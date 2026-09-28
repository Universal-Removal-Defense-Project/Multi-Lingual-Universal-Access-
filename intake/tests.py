from datetime import date, timedelta

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .dates import parse_date_string
from .models import (
    HEARING_SOON_DAYS,
    IntakeApplication,
    IntakeEntry,
    IntakeFamilyMember,
    IntakeSubmission,
)


def valid_submission(**overrides):
    values = {
        'language': 'es',
        'full_name': 'Maria Example',
        'date_of_birth': '1990-01-01',
        'country_of_origin': 'Venezuela',
        'preferred_language': 'Spanish',
        'phone': '',
        'email': '',
        'current_location': '',
        'immigration_court': '',
        'a_number': '',
        'next_hearing_date': '',
        'fear_of_return_summary': 'Original response in the applicant language.',
        'past_harm_summary': '',
        'countries_traveled_asylum_summary': 'Mexico',
        'consent_acknowledged': 'on',
    }
    values.update(overrides)
    return values


class IntakeLanguageWorkflowTests(TestCase):
    def test_language_change_preserves_draft_values_and_sets_cookie(self):
        response = self.client.post(
            reverse('intake_form'),
            {
                'language': 'ar',
                'form_action': 'change_language',
                'full_name': 'Draft Applicant',
                'fear_of_return_summary': 'Draft narrative',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Draft Applicant"')
        self.assertContains(response, 'dir="rtl"')
        self.assertEqual(response.cookies['urdp_language'].value, 'ar')
        self.assertEqual(IntakeSubmission.objects.count(), 0)

    def test_submission_stores_interface_language_and_original_responses(self):
        response = self.client.post(reverse('intake_form'), valid_submission())

        self.assertRedirects(response, reverse('intake_success'))
        submission = IntakeSubmission.objects.get()
        self.assertEqual(submission.language_preference, 'es')
        self.assertEqual(
            submission.fear_of_return_summary,
            'Original response in the applicant language.',
        )
        self.assertEqual(submission.fear_of_return_summary_translated, '')
        self.assertEqual(response.cookies['urdp_language'].value, 'es')

    def test_invalid_language_falls_back_to_supported_default(self):
        response = self.client.post(
            reverse('intake_form'),
            valid_submission(language='unsupported'),
        )

        self.assertRedirects(response, reverse('intake_success'))
        self.assertEqual(IntakeSubmission.objects.get().language_preference, 'en')


class LegacyDateParsingTests(TestCase):
    """Covers the parse helper the 0011 data migration uses."""

    def test_iso_values_parse(self):
        self.assertEqual(parse_date_string('1990-01-01'), date(1990, 1, 1))

    def test_us_slash_format_parses(self):
        self.assertEqual(parse_date_string('03/04/1990'), date(1990, 3, 4))

    def test_day_first_slash_format_parses_when_day_exceeds_twelve(self):
        self.assertEqual(parse_date_string('25/12/1990'), date(1990, 12, 25))

    def test_surrounding_whitespace_is_tolerated(self):
        self.assertEqual(parse_date_string('  1990-01-01  '), date(1990, 1, 1))

    def test_empty_and_unparseable_values_return_none(self):
        for raw in ('', '   ', None, 'not-a-date', '1990-13-45'):
            self.assertIsNone(parse_date_string(raw), raw)


class IntakeDateFieldTests(TestCase):
    def test_valid_dates_are_stored_as_date_objects(self):
        response = self.client.post(
            reverse('intake_form'),
            valid_submission(next_hearing_date='2026-09-15'),
        )

        self.assertRedirects(response, reverse('intake_success'))
        submission = IntakeSubmission.objects.get()
        self.assertEqual(submission.date_of_birth, date(1990, 1, 1))
        self.assertEqual(submission.next_hearing_date, date(2026, 9, 15))

    def test_blank_hearing_date_is_stored_as_null(self):
        self.client.post(reverse('intake_form'), valid_submission())

        self.assertIsNone(IntakeSubmission.objects.get().next_hearing_date)

    def test_invalid_date_is_rejected_without_creating_a_row(self):
        response = self.client.post(
            reverse('intake_form'),
            valid_submission(language='en', date_of_birth='not-a-date'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid date.')
        self.assertEqual(IntakeSubmission.objects.count(), 0)

    def test_invalid_date_error_is_translated(self):
        # Fails if the .mo catalogs were never compiled.
        response = self.client.post(
            reverse('intake_form'),
            valid_submission(language='ht', date_of_birth='not-a-date'),
        )

        self.assertContains(response, 'Antre yon dat valab.')
        self.assertEqual(IntakeSubmission.objects.count(), 0)


class RootRedirectTests(TestCase):
    def test_root_redirects_to_intake_form(self):
        response = self.client.get('/')
        self.assertRedirects(response, reverse('intake_form'))


class IntakeTranslationRenderingTests(TestCase):
    def test_spanish_locale_renders_translated_form(self):
        # Fails if the .mo catalogs were never compiled — the heading falls back to English.
        response = self.client.get(reverse('intake_form'), headers={'Accept-Language': 'es'})

        self.assertContains(response, 'Información personal')


class IntakeApplicationModelTests(TestCase):
    """The I-589 application models (Issue #41)."""

    def test_str_of_every_model_carries_no_applicant_data(self):
        application = IntakeApplication.objects.create(
            last_name='Ejemplo', first_name='Maria', preferred_language='Spanish'
        )
        entry = IntakeEntry.objects.create(application=application, place='El Paso')
        member = IntakeFamilyMember.objects.create(
            application=application, relationship='child', last_name='Ejemplo'
        )

        expected = {
            application: f'Application {application.pk}',
            entry: f'Entry {entry.pk}',
            member: f'Family member {member.pk}',
        }
        for instance, label in expected.items():
            with self.subTest(model=type(instance).__name__):
                self.assertEqual(str(instance), label)
                # A repr reaches tracebacks and admin logs, so it must never name a person.
                for applicant_value in ('Ejemplo', 'Maria', 'El Paso'):
                    self.assertNotIn(applicant_value, str(instance))

    def test_deleting_an_application_removes_its_child_rows(self):
        application = IntakeApplication.objects.create()
        IntakeEntry.objects.create(application=application)
        IntakeFamilyMember.objects.create(application=application, relationship='spouse')

        application.delete()

        self.assertEqual(IntakeEntry.objects.count(), 0)
        self.assertEqual(IntakeFamilyMember.objects.count(), 0)

    def test_hearing_is_soon_only_inside_the_window(self):
        today = timezone.localdate()
        cases = [
            (None, False),
            (today - timedelta(days=1), False),
            (today, True),
            (today + timedelta(days=HEARING_SOON_DAYS), True),
            (today + timedelta(days=HEARING_SOON_DAYS + 1), False),
        ]

        for hearing_date, expected in cases:
            with self.subTest(next_hearing_date=hearing_date):
                application = IntakeApplication(next_hearing_date=hearing_date)
                self.assertIs(application.hearing_is_soon, expected)

    def test_the_legacy_submission_model_is_untouched(self):
        # Issue #41: the new models live alongside IntakeSubmission, they do not replace it.
        self.assertEqual(IntakeSubmission.objects.count(), 0)
        submission = IntakeSubmission.objects.create(
            full_name='Legacy Applicant',
            country_of_origin='Venezuela',
            preferred_language='Spanish',
            fear_of_return_summary='Unchanged.',
        )
        self.assertEqual(str(submission), 'Legacy Applicant')


# --- Multi-step application form (Issue #41) ----------------------------------------------


def step_url(step):
    return reverse('application_step', kwargs={'step': step})


def management(prefix, total):
    return {f'{prefix}-TOTAL_FORMS': str(total), f'{prefix}-INITIAL_FORMS': '0'}


def valid_step(step, **overrides):
    """The smallest valid POST for each step: every list present but left blank."""
    values = {
        1: {'last_name': 'Ejemplo', 'first_name': 'Maria'},
        2: management('entries', 1),
        3: {**management('spouse', 1), **management('children', 1)},
        4: {},
        5: {},
        6: {'preferred_language': 'Spanish', 'consent_acknowledged': 'on'},
    }[step]
    return {**values, **overrides}


def complete_through(client, last_step, overrides=None):
    """POST steps 1..last_step; returns the redirect target of each."""
    overrides = overrides or {}
    locations = []
    for step in range(1, last_step + 1):
        response = client.post(step_url(step), valid_step(step, **overrides.get(step, {})))
        locations.append(response['Location'])
    return locations


class ApplicationStepAccessTests(TestCase):
    def test_start_redirects_to_step_one(self):
        self.assertRedirects(self.client.get(reverse('application_start')), step_url(1))

    def test_unknown_step_is_404(self):
        for step in (0, 7):
            with self.subTest(step=step):
                self.assertEqual(self.client.get(step_url(step)).status_code, 404)

    def test_skipping_ahead_redirects_to_first_incomplete_step(self):
        complete_through(self.client, 2)

        self.assertRedirects(self.client.get(step_url(5)), step_url(3))

    def test_back_navigation_prefills_stored_step(self):
        complete_through(self.client, 2)

        response = self.client.get(step_url(1))

        self.assertContains(response, 'value="Ejemplo"')


class ApplicationStepValidationTests(TestCase):
    def test_invalid_step_rerenders_with_errors_and_stores_nothing(self):
        response = self.client.post(step_url(1), valid_step(1, last_name=''))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form-error-summary')
        self.assertContains(response, 'This information is required.')
        self.assertNotIn('1', self.client.session.get('intake_application', {}))

    def test_valid_step_stores_answers_and_advances(self):
        response = self.client.post(step_url(1), valid_step(1))

        self.assertRedirects(response, step_url(2))
        stored = self.client.session['intake_application']['1']
        self.assertEqual(stored['last_name'], 'Ejemplo')
        self.assertNotIn('csrfmiddlewaretoken', stored)

    def test_consent_is_required_on_final_step(self):
        complete_through(self.client, 5)

        response = self.client.post(step_url(6), valid_step(6, consent_acknowledged=''))

        self.assertContains(response, 'Please acknowledge this notice before submitting')
        self.assertEqual(IntakeApplication.objects.count(), 0)

    def test_add_row_rerenders_with_one_more_row_and_stores_nothing(self):
        complete_through(self.client, 1)

        response = self.client.post(step_url(2), valid_step(2, add_row='entries'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="entries-1-place"')
        self.assertNotContains(response, 'form-error-summary')
        self.assertNotIn('2', self.client.session['intake_application'])

    def test_spouse_list_accepts_at_most_one(self):
        complete_through(self.client, 2)

        response = self.client.post(
            step_url(3),
            valid_step(
                3,
                **management('spouse', 2),
                **{'spouse-0-last_name': 'Uno', 'spouse-1-last_name': 'Dos'},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('3', self.client.session['intake_application'])


class ApplicationSubmitTests(TestCase):
    def test_full_submit_saves_application_and_every_list_in_order(self):
        locations = complete_through(
            self.client,
            6,
            {
                2: {
                    'immigration_court_proceedings': 'never',
                    'fluent_in_english': 'False',
                    **management('entries', 2),
                    'entries-0-place': 'El Paso',
                    'entries-0-date': '2024-01-15',
                    'entries-1-place': 'Miami',
                },
                3: {
                    'spouse-0-last_name': 'Esposo',
                    **management('children', 3),
                    'children-0-first_name': 'Primera',
                    'children-1-first_name': 'Borrada',
                    'children-1-DELETE': 'on',
                    'children-2-first_name': 'Segunda',
                },
                4: {
                    'experienced_harm': 'True',
                    'experienced_harm_explanation': 'Palabras originales.',
                },
            },
        )

        self.assertEqual(locations[-1], reverse('intake_success'))
        application = IntakeApplication.objects.get()
        self.assertEqual(application.last_name, 'Ejemplo')
        self.assertEqual(application.immigration_court_proceedings, 'never')
        self.assertIs(application.fluent_in_english, False)
        self.assertIs(application.experienced_harm, True)
        # Unanswered Yes/No stays None, distinct from No.
        self.assertIsNone(application.fears_torture)
        self.assertEqual(application.experienced_harm_explanation, 'Palabras originales.')
        self.assertEqual(application.experienced_harm_explanation_translated, '')
        self.assertTrue(application.consent_acknowledged)
        self.assertEqual(application.status, 'new')
        self.assertEqual(
            list(application.entries.values_list('place', 'position')),
            [('El Paso', 0), ('Miami', 1)],
        )
        self.assertEqual(application.entries.first().date, date(2024, 1, 15))
        spouse = application.family_members.get(relationship='spouse')
        self.assertEqual(spouse.last_name, 'Esposo')
        children = application.family_members.filter(relationship='child')
        self.assertEqual(
            list(children.values_list('first_name', 'position')), [('Primera', 0), ('Segunda', 1)]
        )
        self.assertNotIn('intake_application', self.client.session)

    def test_submit_records_interface_language(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'es'

        complete_through(self.client, 6)

        self.assertEqual(IntakeApplication.objects.get().language_preference, 'es')

    def test_blank_lists_save_no_rows(self):
        complete_through(self.client, 6)

        application = IntakeApplication.objects.get()
        self.assertEqual(application.entries.count(), 0)
        self.assertEqual(application.family_members.count(), 0)

    def test_abandoned_flow_creates_no_rows(self):
        complete_through(self.client, 5)

        self.assertEqual(IntakeApplication.objects.count(), 0)

    def test_tampered_session_step_sends_applicant_back_to_it(self):
        complete_through(self.client, 5)
        session = self.client.session
        stored = session['intake_application']
        stored['1']['last_name'] = ''
        session['intake_application'] = stored
        session.save()

        response = self.client.post(step_url(6), valid_step(6))

        self.assertRedirects(response, step_url(1))
        self.assertEqual(IntakeApplication.objects.count(), 0)

    def test_unsubmitted_answers_expire_with_the_session(self):
        complete_through(self.client, 1)
        self.assertEqual(self.client.session.get_expiry_age(), 2 * 60 * 60)

        Session.objects.update(expire_date=timezone.now() - timedelta(minutes=1))
        call_command('clearsessions')

        self.assertEqual(Session.objects.count(), 0)
        self.assertRedirects(self.client.get(step_url(2)), step_url(1))
        self.assertEqual(IntakeApplication.objects.count(), 0)


class ApplicationRenderingTests(TestCase):
    def test_every_supported_language_renders_every_step(self):
        complete_through(self.client, 5)

        for code, _name in settings.LANGUAGES:
            for step in range(1, 7):
                with self.subTest(language=code, step=step):
                    response = self.client.get(step_url(step), headers={'Accept-Language': code})
                    self.assertContains(response, f'lang="{code}"')

    def test_arabic_renders_rtl_with_direction_neutral_inputs(self):
        response = self.client.get(step_url(1), headers={'Accept-Language': 'ar'})

        self.assertContains(response, '<html lang="ar" dir="rtl">')
        self.assertContains(response, 'dir="auto"')

    def test_i589_intro_shows_on_the_first_step_only(self):
        complete_through(self.client, 1)
        intro = 'Form I-589, Application for Asylum and for Withholding of Removal'

        self.assertContains(self.client.get(step_url(1)), intro)
        self.assertNotContains(self.client.get(step_url(2)), intro)

    def test_yes_no_questions_offer_only_yes_and_no(self):
        complete_through(self.client, 3)

        response = self.client.get(step_url(4))

        self.assertContains(response, 'type="radio" name="experienced_harm" value="True"')
        self.assertContains(response, 'type="radio" name="experienced_harm" value="False"')
        self.assertNotContains(response, 'Unknown')

    def test_child_rows_use_the_child_wording(self):
        complete_through(self.client, 2)

        response = self.client.get(step_url(3))

        self.assertContains(response, 'Is this person in the U.S.?')
        self.assertContains(response, 'Is this child in the U.S.?')

    def test_no_applicant_data_appears_in_any_url(self):
        locations = complete_through(self.client, 6)

        for location in locations:
            with self.subTest(location=location):
                self.assertRegex(location, r'^/(intake-form/\d/|intake-success/)$')
                self.assertNotIn('Ejemplo', location)
