from django import forms
from django.utils.translation import gettext_lazy as _

from .models import IntakeApplication, IntakeEntry, IntakeFamilyMember, IntakeSubmission


class IntakeSubmissionForm(forms.ModelForm):
    consent_acknowledged = forms.BooleanField(
        label=_(
            'I understand that submitting this form does not create an '
            'attorney-client relationship.'
        ),
        required=True,
        error_messages={
            'required': _('Please acknowledge this notice before submitting your intake.')
        },
        widget=forms.CheckboxInput(),
    )

    class Meta:
        model = IntakeSubmission
        fields = [
            'full_name',
            'date_of_birth',
            'country_of_origin',
            'preferred_language',
            'phone',
            'email',
            'current_location',
            'detained',
            'immigration_court',
            'a_number',
            'next_hearing_date',
            'fear_of_return_summary',
            'past_harm_summary',
            'countries_traveled_asylum_summary',
            'family_members_included',
            'consent_acknowledged',
        ]
        labels = {
            'full_name': _('Full name'),
            'date_of_birth': _('Date of birth'),
            'country_of_origin': _('Country of origin'),
            'preferred_language': _('Preferred language'),
            'phone': _('Phone number'),
            'email': _('Email address'),
            'current_location': _('Current city or location'),
            'detained': _('Currently detained'),
            'immigration_court': _('Immigration court'),
            'a_number': _('A-number'),
            'next_hearing_date': _('Next hearing date'),
            'fear_of_return_summary': _('Reason for fearing return'),
            'past_harm_summary': _('Past harm or persecution'),
            'countries_traveled_asylum_summary': _(
                'Countries traveled through and asylum applications'
            ),
            'family_members_included': _('Family members included'),
        }
        widgets = {
            'full_name': forms.TextInput(
                attrs={
                    'placeholder': _('Enter your full name'),
                    'autocomplete': 'name',
                }
            ),
            'date_of_birth': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'autocomplete': 'bday',
                },
            ),
            'country_of_origin': forms.TextInput(
                attrs={
                    'placeholder': _('Country where you are from'),
                    'autocomplete': 'country-name',
                }
            ),
            'preferred_language': forms.TextInput(
                attrs={
                    'placeholder': _('Language you prefer for communication'),
                    'autocomplete': 'language',
                }
            ),
            'phone': forms.TextInput(
                attrs={
                    'placeholder': _('Best phone number to reach you'),
                    'autocomplete': 'tel',
                    'inputmode': 'tel',
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'placeholder': _('Email address, if available'),
                    'autocomplete': 'email',
                    'inputmode': 'email',
                }
            ),
            'current_location': forms.TextInput(
                attrs={
                    'placeholder': _('City, state, or detention facility'),
                    'autocomplete': 'address-level2',
                }
            ),
            'detained': forms.CheckboxInput(),
            'immigration_court': forms.TextInput(
                attrs={
                    'placeholder': _('Court name or city, if known'),
                }
            ),
            'a_number': forms.TextInput(
                attrs={
                    'placeholder': _('Example: A123456789'),
                    'autocomplete': 'off',
                }
            ),
            'next_hearing_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'fear_of_return_summary': forms.Textarea(
                attrs={
                    'placeholder': _('Describe why returning would be unsafe for you.'),
                    'rows': 5,
                }
            ),
            'past_harm_summary': forms.Textarea(
                attrs={
                    'placeholder': _('Describe any past harm, threats, or persecution.'),
                    'rows': 5,
                }
            ),
            'countries_traveled_asylum_summary': forms.Textarea(
                attrs={
                    'placeholder': _(
                        'List countries traveled through and whether you applied for asylum.'
                    ),
                    'rows': 5,
                }
            ),
            'family_members_included': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'consent_acknowledged':
                continue
            field.error_messages['required'] = _('This information is required.')


# --- I-589 intake application (Issue #41) -------------------------------------------------
#
# Labels come from the model fields' verbose_name (the I-589's own wording), so these forms
# carry no labels, except the child rows, which the I-589 words differently from the spouse.

YES_NO_CHOICES = [(True, _('Yes')), (False, _('No'))]


class _ApplicantModelForm(forms.ModelForm):
    # (heading, note, [field names]) per group; None renders every field as one group.
    groups = None
    autocomplete = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'consent_acknowledged':
                field.error_messages['required'] = _('This information is required.')
            if isinstance(field, forms.NullBooleanField):
                # The I-589 asks Yes / No. Unanswered stays None, distinct from No.
                field.widget = forms.RadioSelect(choices=YES_NO_CHOICES)
            elif isinstance(field, forms.TypedChoiceField):
                field.widget = forms.RadioSelect(choices=[c for c in field.choices if c[0]])
            elif isinstance(field, forms.DateField):
                field.widget = forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})
            elif isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.Textarea)):
                # Applicants type in their own script, whatever the interface language.
                field.widget.attrs['dir'] = 'auto'
                if isinstance(field.widget, forms.Textarea):
                    field.widget.attrs['rows'] = 4
            if name in self.autocomplete:
                field.widget.attrs['autocomplete'] = self.autocomplete[name]

    def grouped_fields(self):
        if self.groups is None:
            return [(None, None, self.visible_fields())]
        return [
            (heading, note, [self[name] for name in names]) for heading, note, names in self.groups
        ]


class ApplicationAboutYouForm(_ApplicantModelForm):
    groups = [
        (
            None,
            None,
            [
                'apply_withholding_cat',
                'a_number',
                'uscis_online_account_number',
                'last_name',
                'first_name',
                'middle_name',
                'other_names_used',
            ],
        ),
        # I-589 Part A.I, Item 8
        (
            _('Residence in the U.S. (where you physically reside)'),
            None,
            [
                'residence_street',
                'residence_apt_number',
                'residence_city',
                'residence_state',
                'residence_zip_code',
                'residence_telephone_number',
            ],
        ),
        # I-589 Part A.I, Item 9
        (
            _('Mailing Address in the U.S. (if different than the address in Item Number 8)'),
            None,
            [
                'mailing_in_care_of',
                'mailing_telephone_number',
                'mailing_street',
                'mailing_apt_number',
                'mailing_city',
                'mailing_state',
                'mailing_zip_code',
            ],
        ),
        (
            None,
            None,
            [
                'gender',
                'marital_status',
                'date_of_birth',
                'city_and_country_of_birth',
                'present_nationality',
                'nationality_at_birth',
                'race_ethnic_or_tribal_group',
                'religion',
            ],
        ),
    ]
    autocomplete = {
        'a_number': 'off',
        'uscis_online_account_number': 'off',
        'last_name': 'family-name',
        'first_name': 'given-name',
        'middle_name': 'additional-name',
        'residence_street': 'address-line1',
        'residence_apt_number': 'address-line2',
        'residence_city': 'address-level2',
        'residence_state': 'address-level1',
        'residence_zip_code': 'postal-code',
        'residence_telephone_number': 'tel',
        'date_of_birth': 'bday',
    }

    class Meta:
        model = IntakeApplication
        fields = [
            'apply_withholding_cat',
            'a_number',
            'uscis_online_account_number',
            'last_name',
            'first_name',
            'middle_name',
            'other_names_used',
            'residence_street',
            'residence_apt_number',
            'residence_city',
            'residence_state',
            'residence_zip_code',
            'residence_telephone_number',
            'mailing_in_care_of',
            'mailing_telephone_number',
            'mailing_street',
            'mailing_apt_number',
            'mailing_city',
            'mailing_state',
            'mailing_zip_code',
            'gender',
            'marital_status',
            'date_of_birth',
            'city_and_country_of_birth',
            'present_nationality',
            'nationality_at_birth',
            'race_ethnic_or_tribal_group',
            'religion',
        ]


class ApplicationImmigrationHistoryForm(_ApplicantModelForm):
    """I-589 Part A.I, Items 18 to 19.b. The Item 19.c entry list follows as a formset."""

    class Meta:
        model = IntakeApplication
        fields = ['immigration_court_proceedings', 'date_last_left_country', 'current_i94_number']


class ApplicationTravelLanguageForm(_ApplicantModelForm):
    """I-589 Part A.I, Items 20 to 25, after the Item 19.c entry list."""

    autocomplete = {'passport_number': 'off', 'travel_document_number': 'off'}

    class Meta:
        model = IntakeApplication
        fields = [
            'last_travel_document_country',
            'passport_number',
            'travel_document_number',
            'travel_document_expiration_date',
            'native_language',
            'fluent_in_english',
            'other_languages_spoken',
        ]


class ApplicationBasisForm(_ApplicantModelForm):
    groups = [
        # I-589 Part B, Item 1
        (
            _(
                'Why are you applying for asylum or withholding of removal under section '
                '241(b)(3) of the INA, or for withholding of removal under the Convention '
                'Against Torture? Check the appropriate box(es) below and then provide '
                'detailed answers to questions A and B below.'
            ),
            _('I am seeking asylum or withholding of removal based on:'),
            [
                'basis_race',
                'basis_religion',
                'basis_nationality',
                'basis_political_opinion',
                'basis_particular_social_group',
                'basis_torture_convention',
            ],
        ),
        (
            None,
            None,
            [
                'experienced_harm',
                'experienced_harm_explanation',
                'fears_harm_on_return',
                'fears_harm_explanation',
                'arrested_or_detained_abroad',
                'arrested_explanation',
                'belonged_to_organization',
                'organization_explanation',
                'continues_participation',
                'continued_participation_explanation',
                'fears_torture',
                'torture_explanation',
            ],
        ),
    ]

    class Meta:
        model = IntakeApplication
        fields = [
            'basis_race',
            'basis_religion',
            'basis_nationality',
            'basis_political_opinion',
            'basis_particular_social_group',
            'basis_torture_convention',
            'experienced_harm',
            'experienced_harm_explanation',
            'fears_harm_on_return',
            'fears_harm_explanation',
            'arrested_or_detained_abroad',
            'arrested_explanation',
            'belonged_to_organization',
            'organization_explanation',
            'continues_participation',
            'continued_participation_explanation',
            'fears_torture',
            'torture_explanation',
        ]


class ApplicationAdditionalInfoForm(_ApplicantModelForm):
    class Meta:
        model = IntakeApplication
        fields = [
            'family_applied_for_protection',
            'protection_application_explanation',
            'traveled_through_other_country',
            'applied_for_status_elsewhere',
            'other_country_explanation',
            'caused_harm_to_others',
            'caused_harm_explanation',
            'returned_to_country',
            'return_explanation',
            'filing_after_one_year',
            'late_filing_explanation',
            'crimes_in_united_states',
            'us_crimes_explanation',
        ]


class ApplicationContactConsentForm(_ApplicantModelForm):
    # Declared exactly as on IntakeSubmissionForm, so the msgids are already translated.
    consent_acknowledged = forms.BooleanField(
        label=_(
            'I understand that submitting this form does not create an '
            'attorney-client relationship.'
        ),
        required=True,
        error_messages={
            'required': _('Please acknowledge this notice before submitting your intake.')
        },
        widget=forms.CheckboxInput(),
    )
    autocomplete = {
        'email': 'email',
        'preferred_language': 'language',
        'current_location': 'address-level2',
    }

    class Meta:
        model = IntakeApplication
        fields = [
            'email',
            'preferred_language',
            'current_location',
            'detained',
            'immigration_court',
            'next_hearing_date',
            'consent_acknowledged',
        ]
        # Placeholders reuse IntakeSubmissionForm's msgids, already translated.
        widgets = {
            'email': forms.EmailInput(
                attrs={'placeholder': _('Email address, if available'), 'inputmode': 'email'}
            ),
            'preferred_language': forms.TextInput(
                attrs={'placeholder': _('Language you prefer for communication')}
            ),
            'current_location': forms.TextInput(
                attrs={'placeholder': _('City, state, or detention facility')}
            ),
            'immigration_court': forms.TextInput(
                attrs={'placeholder': _('Court name or city, if known')}
            ),
        }


class EntryForm(_ApplicantModelForm):
    class Meta:
        model = IntakeEntry
        fields = ['date', 'place', 'status', 'date_status_expires']


FAMILY_MEMBER_AUTOCOMPLETE = {'a_number': 'off', 'passport_id_card_number': 'off'}


class SpouseForm(_ApplicantModelForm):
    autocomplete = FAMILY_MEMBER_AUTOCOMPLETE

    class Meta:
        model = IntakeFamilyMember
        # I-589 Part A.II spouse item order.
        fields = [
            'a_number',
            'passport_id_card_number',
            'date_of_birth',
            'last_name',
            'first_name',
            'middle_name',
            'other_names_used',
            'date_of_marriage',
            'place_of_marriage',
            'city_and_country_of_birth',
            'nationality',
            'race_ethnic_or_tribal_group',
            'gender',
            'in_united_states',
            'location_if_not_in_us',
            'place_of_last_entry',
            'date_of_last_entry',
            'i94_number',
            'status_when_last_admitted',
            'current_status',
            'authorized_stay_expiration_date',
            'in_immigration_court_proceedings',
            'date_of_previous_arrival',
            'include_in_application',
        ]


class ChildForm(_ApplicantModelForm):
    autocomplete = FAMILY_MEMBER_AUTOCOMPLETE

    class Meta:
        model = IntakeFamilyMember
        # I-589 Part A.II child item order.
        fields = [
            'a_number',
            'passport_id_card_number',
            'marital_status',
            'last_name',
            'first_name',
            'middle_name',
            'date_of_birth',
            'city_and_country_of_birth',
            'nationality',
            'race_ethnic_or_tribal_group',
            'gender',
            'in_united_states',
            'location_if_not_in_us',
            'place_of_last_entry',
            'date_of_last_entry',
            'i94_number',
            'status_when_last_admitted',
            'current_status',
            'authorized_stay_expiration_date',
            'in_immigration_court_proceedings',
            'include_in_application',
        ]
        # The model's verbose_name is the spouse wording; these are the child block's.
        labels = {
            # I-589 Part A.II, child Item 13
            'in_united_states': _('Is this child in the U.S.?'),
            # I-589 Part A.II, child Item 18
            'current_status': _("What is your child's current status?"),
            # I-589 Part A.II, child Item 20
            'in_immigration_court_proceedings': _(
                'Is your child in Immigration Court proceedings?'
            ),
            # I-589 Part A.II, child Item 21
            'include_in_application': _(
                'If in the U.S., is this child to be included in this application? (Check '
                'the appropriate box.)'
            ),
        }


class _ApplicantFormSet(forms.BaseModelFormSet):
    """A repeatable I-589 list, held in the session until submit, never loaded from the DB."""

    is_formset = True
    default_prefix = ''
    heading = None
    note = None
    add_label = None
    # Set on IntakeFamilyMember rows at save; None for other lists.
    relationship = None

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('queryset', self.model.objects.none())
        super().__init__(*args, **kwargs)

    @classmethod
    def get_default_prefix(cls):
        return cls.default_prefix

    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields['DELETE'].label = _('Remove')


def _applicant_formset(form, **kwargs):
    return forms.modelformset_factory(
        form.Meta.model, form=form, formset=_ApplicantFormSet, extra=1, can_delete=True, **kwargs
    )


class EntryFormSet(_applicant_formset(EntryForm)):
    default_prefix = 'entries'
    # I-589 Part A.I, Item 19.c
    heading = _(
        'List each entry into the U.S. beginning with your most recent entry. List date '
        '(mm/dd/yyyy), place, and your status for each entry. (Attach additional sheets as '
        'needed.)'
    )
    add_label = _('Add another entry')


class SpouseFormSet(_applicant_formset(SpouseForm, max_num=1, validate_max=True)):
    default_prefix = 'spouse'
    heading = _('Your spouse')
    relationship = 'spouse'


class ChildFormSet(_applicant_formset(ChildForm)):
    default_prefix = 'children'
    heading = _('Your Children')
    note = _('List all of your children, regardless of age, location, or marital status.')
    add_label = _('Add another child')
    relationship = 'child'


# (heading, [form and formset classes]) per step, in order. Headings are the I-589 Part
# titles verbatim, except steps 2 and 6 (authored; flagged in docs/i589-wording-review.md).
APPLICATION_STEPS = [
    (_('Information About You'), [ApplicationAboutYouForm]),
    (
        _('Immigration History'),
        [ApplicationImmigrationHistoryForm, EntryFormSet, ApplicationTravelLanguageForm],
    ),
    (_('Information About Your Spouse and Children'), [SpouseFormSet, ChildFormSet]),
    (_('Information About Your Application'), [ApplicationBasisForm]),
    (_('Additional Information About Your Application'), [ApplicationAdditionalInfoForm]),
    (_('Contact and Consent'), [ApplicationContactConsentForm]),
]
