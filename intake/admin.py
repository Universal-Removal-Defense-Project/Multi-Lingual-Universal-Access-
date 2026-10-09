from django.contrib import admin, messages
from django.db.models import Value
from django.db.models.functions import Replace, Upper
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.views.decorators.http import require_POST

from .forms import (
    ApplicationAboutYouForm,
    ApplicationAdditionalInfoForm,
    ApplicationBasisForm,
    ApplicationContactConsentForm,
    ApplicationImmigrationHistoryForm,
    ApplicationTravelLanguageForm,
    SpouseForm,
)
from .models import IntakeApplication, IntakeEntry, IntakeFamilyMember, IntakeSubmission

TRANSLATION_NOTE = 'Enter translations here without replacing the applicant original wording.'


# Stripped from both sides before comparing, so 'A-123 456 789' matches '123456789'.
A_NUMBER_NOISE = ('-', ' ', 'A')


def _normalized_a_number(expression):
    """Database-side version of the A-number normalization (field is upper-cased first)."""
    for character in A_NUMBER_NOISE:
        expression = Replace(expression, Value(character), Value(''))
    return expression


class ANumberLookupMixin:
    """A private "Find by A-number" box on the changelist.

    Admin's own search puts the query in the URL (?q=...), where it reaches browser history,
    server logs and anything the link is pasted into. An A-number leads straight to someone's
    immigration case, so it is looked up by POST instead, and the redirect names records by
    primary key only.
    """

    change_list_template = 'admin/intake/a_number_lookup_change_list.html'

    def get_urls(self):
        opts = self.model._meta
        lookup = path(
            'find-by-a-number/',
            self.admin_site.admin_view(require_POST(self.find_by_a_number)),
            name=f'{opts.app_label}_{opts.model_name}_find_by_a_number',
        )
        return [lookup, *super().get_urls()]

    def find_by_a_number(self, request):
        opts = self.model._meta
        changelist = reverse(f'admin:{opts.app_label}_{opts.model_name}_changelist')
        if not self.has_view_permission(request):
            return HttpResponseRedirect(reverse('admin:index'))
        typed = request.POST.get('a_number', '').upper()
        wanted = ''.join(c for c in typed if c not in A_NUMBER_NOISE)
        if not wanted:
            return HttpResponseRedirect(changelist)
        pks = list(
            self.get_queryset(request)
            .annotate(normalized_a_number=_normalized_a_number(Upper('a_number')))
            .filter(normalized_a_number=wanted)
            .values_list('pk', flat=True)
        )
        if len(pks) == 1:
            return HttpResponseRedirect(
                reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[pks[0]])
            )
        if pks:
            return HttpResponseRedirect(f'{changelist}?id__in={",".join(map(str, pks))}')
        self.message_user(request, 'No record found for that A-number.', messages.WARNING)
        return HttpResponseRedirect(changelist)


@admin.register(IntakeSubmission)
class IntakeSubmissionAdmin(ANumberLookupMixin, admin.ModelAdmin):
    list_display = (
        'full_name',
        'language_preference',
        'preferred_language',
        'country_of_origin',
        'detained',
        'status',
        'assigned_to',
        'created_at',
    )
    list_filter = ('language_preference', 'preferred_language', 'detained', 'status', 'created_at')
    # Names only: these go in the URL. A-numbers use the POST lookup (ANumberLookupMixin).
    search_fields = ('full_name', 'country_of_origin')
    fieldsets = (
        (
            'Submission',
            {
                'fields': (
                    'full_name',
                    'date_of_birth',
                    'country_of_origin',
                    'preferred_language',
                    'language_preference',
                    'phone',
                    'email',
                    'current_location',
                    'detained',
                    'immigration_court',
                    'a_number',
                    'next_hearing_date',
                    'family_members_included',
                    'consent_acknowledged',
                    'status',
                    'assigned_to',
                )
            },
        ),
        (
            'Original narrative responses',
            {
                'fields': (
                    'fear_of_return_summary',
                    'past_harm_summary',
                    'countries_traveled_asylum_summary',
                )
            },
        ),
        (
            'Staff translations',
            {
                'fields': (
                    'translated_response_language',
                    'fear_of_return_summary_translated',
                    'past_harm_summary_translated',
                    'countries_traveled_asylum_summary_translated',
                ),
                'description': TRANSLATION_NOTE,
            },
        ),
    )


# --- I-589 intake application (Issue #44) -------------------------------------------------
#
# Field lists come from the applicant step forms, so the admin shows the same items in the
# same order and there is one list to maintain. Staff translations sit in their own section,
# apart from the applicant's original wording, as for IntakeSubmission above.

TRANSLATED_FIELDS = tuple(
    field.name for field in IntakeApplication._meta.fields if field.name.endswith('_translated')
)


class IntakeEntryInline(admin.TabularInline):
    model = IntakeEntry
    fields = ('position', 'date', 'place', 'status', 'date_status_expires')
    extra = 0


class IntakeFamilyMemberInline(admin.StackedInline):
    model = IntakeFamilyMember
    extra = 0
    fieldsets = (
        (None, {'fields': ('relationship', 'position', *SpouseForm.Meta.fields, 'marital_status')}),
        ('Staff translation', {'fields': ('other_names_used_translated',)}),
    )


@admin.register(IntakeApplication)
class IntakeApplicationAdmin(ANumberLookupMixin, admin.ModelAdmin):
    list_display = (
        '__str__',
        'last_name',
        'first_name',
        'language_preference',
        'detained',
        'status',
        'assigned_to',
        'created_at',
    )
    list_filter = ('language_preference', 'detained', 'status', 'created_at')
    # Names only: these go in the URL. A-numbers use the POST lookup (ANumberLookupMixin).
    search_fields = ('last_name', 'first_name')
    readonly_fields = ('created_at',)
    inlines = (IntakeEntryInline, IntakeFamilyMemberInline)
    fieldsets = (
        ('Case', {'fields': ('status', 'assigned_to', 'language_preference', 'created_at')}),
        (
            'Part A.I: Information About You',
            {
                'fields': (
                    *ApplicationAboutYouForm.Meta.fields,
                    *ApplicationImmigrationHistoryForm.Meta.fields,
                    *ApplicationTravelLanguageForm.Meta.fields,
                )
            },
        ),
        (
            'Part B: Information About Your Application',
            {'fields': ApplicationBasisForm.Meta.fields},
        ),
        (
            'Part C: Additional Information About Your Application',
            {'fields': ApplicationAdditionalInfoForm.Meta.fields},
        ),
        ('Contact and consent', {'fields': ApplicationContactConsentForm.Meta.fields}),
        (
            'Staff translations',
            {
                'fields': ('translated_response_language', *TRANSLATED_FIELDS),
                'description': TRANSLATION_NOTE,
            },
        ),
    )
