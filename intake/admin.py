from django.contrib import admin

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


@admin.register(IntakeSubmission)
class IntakeSubmissionAdmin(admin.ModelAdmin):
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
    search_fields = ('full_name', 'country_of_origin', 'a_number', 'email', 'phone')
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
class IntakeApplicationAdmin(admin.ModelAdmin):
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
    search_fields = ('last_name', 'first_name', 'a_number', 'email')
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
