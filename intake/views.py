from django.conf import settings
from django.db import transaction
from django.forms import CheckboxInput
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import translation

from .forms import APPLICATION_STEPS, IntakeSubmissionForm
from .models import IntakeApplication

SUPPORTED_LANGUAGE_CODES = {code for code, _name in settings.LANGUAGES}

APPLICATION_SESSION_KEY = 'intake_application'
# Unsubmitted answers live in the session store until final submit. Each completed step
# saves the session and restarts this clock, so a stalled draft is gone two hours after the
# last completed step (once `clearsessions` runs). It applies to the whole browser session:
# a case manager who walks the form in their dashboard browser gets a two-hour login too.
APPLICATION_SESSION_TTL = 2 * 60 * 60


def _valid_language(code: str | None) -> str:
    if code in SUPPORTED_LANGUAGE_CODES and translation.check_for_language(code):
        return code
    current_language = translation.get_language() or settings.LANGUAGE_CODE
    if current_language in SUPPORTED_LANGUAGE_CODES:
        return current_language
    return settings.LANGUAGE_CODE


def _remember_language(response: HttpResponse, language_code: str) -> HttpResponse:
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language_code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    return response


def _preserved_form_values(request: HttpRequest) -> dict[str, object]:
    # Switching display language must not force an applicant to re-enter draft answers.
    initial = {}
    for name, field in IntakeSubmissionForm.base_fields.items():
        if isinstance(field.widget, CheckboxInput):
            initial[name] = name in request.POST
        else:
            initial[name] = request.POST.get(name, '')
    return initial


def intake_form(request: HttpRequest) -> HttpResponse:
    requested_language = request.POST.get('language') if request.method == 'POST' else None
    language_code = _valid_language(requested_language)
    translation.activate(language_code)

    if request.method == 'POST' and request.POST.get('form_action') == 'change_language':
        form = IntakeSubmissionForm(initial=_preserved_form_values(request))
        response = render(
            request,
            'intake/intake_form.html',
            {'form': form, 'selected_language': language_code},
        )
        return _remember_language(response, language_code)

    if request.method == 'POST':
        form = IntakeSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.language_preference = language_code
            submission.save()
            return _remember_language(redirect('intake_success'), language_code)
    else:
        form = IntakeSubmissionForm()

    response = render(
        request,
        'intake/intake_form.html',
        {'form': form, 'selected_language': language_code},
    )
    if request.method == 'POST':
        return _remember_language(response, language_code)
    return response


def intake_success(request: HttpRequest) -> HttpResponse:
    return render(request, 'intake/intake_success.html')


def _bind_step(step: int, data, application: IntakeApplication | None = None) -> list:
    """The step's forms and formsets, bound to data, or unbound when data is None.

    Scalar forms share `application`, so re-binding every step fills one instance.
    """
    bound = []
    for form_class in APPLICATION_STEPS[step - 1][1]:
        if getattr(form_class, 'is_formset', False):
            bound.append(form_class(data))
        else:
            bound.append(form_class(data, instance=application))
    return bound


def _error_summary(forms: list) -> list[tuple[str, str, str]]:
    """(field id, label, message) for every error on the step, formset rows included."""
    summary = []
    for part in forms:
        if getattr(part, 'is_formset', False):
            summary.extend(('', '', error) for error in part.non_form_errors())
            rows = part.forms
        else:
            rows = [part]
        for form in rows:
            summary.extend(('', '', error) for error in form.non_field_errors())
            for field in form:
                summary.extend((field.auto_id, field.label, error) for error in field.errors)
    return summary


def application_start(request: HttpRequest) -> HttpResponse:
    return redirect('application_step', step=1)


def application_step(request: HttpRequest, step: int) -> HttpResponse:
    step_count = len(APPLICATION_STEPS)
    if not 1 <= step <= step_count:
        raise Http404
    stored = request.session.get(APPLICATION_SESSION_KEY, {})
    for earlier in range(1, step):
        if str(earlier) not in stored:
            return redirect('application_step', step=earlier)
    if step == 1 and not stored:
        request.session.set_expiry(APPLICATION_SESSION_TTL)

    errors = []
    if request.method == 'POST':
        add_row = request.POST.get('add_row')
        if add_row:
            # "Add another" re-renders with one more blank row and stores nothing.
            data = request.POST.copy()
            total_key = f'{add_row}-TOTAL_FORMS'
            if data.get(total_key, '').isdigit():
                data[total_key] = str(int(data[total_key]) + 1)
            forms = _bind_step(step, data)
        else:
            forms = _bind_step(step, request.POST)
            if all(form.is_valid() for form in forms):
                stored[str(step)] = {
                    key: value
                    for key, value in request.POST.items()
                    if key != 'csrfmiddlewaretoken'
                }
                request.session[APPLICATION_SESSION_KEY] = stored
                if step < step_count:
                    return redirect('application_step', step=step + 1)
                return _save_application(request, stored)
            errors = _error_summary(forms)
    else:
        forms = _bind_step(step, stored.get(str(step)))

    return render(
        request,
        'intake/application_step.html',
        {
            'step': step,
            'step_count': step_count,
            'heading': APPLICATION_STEPS[step - 1][0],
            'forms': forms,
            'errors': errors,
            'selected_language': translation.get_language(),
        },
    )


def _save_application(request: HttpRequest, stored: dict) -> HttpResponse:
    application = IntakeApplication()
    formsets = []
    for step in range(1, len(APPLICATION_STEPS) + 1):
        forms = _bind_step(step, stored[str(step)], application)
        # Every step validated when it was stored; this catches a tampered session.
        if not all(form.is_valid() for form in forms):
            return redirect('application_step', step=step)
        formsets.extend(form for form in forms if getattr(form, 'is_formset', False))

    with transaction.atomic():
        application.language_preference = _valid_language(translation.get_language())
        application.save()
        for formset in formsets:
            for position, row in enumerate(formset.save(commit=False)):
                row.application = application
                row.position = position
                if formset.relationship:
                    row.relationship = formset.relationship
                row.save()
    del request.session[APPLICATION_SESSION_KEY]
    return redirect('intake_success')
