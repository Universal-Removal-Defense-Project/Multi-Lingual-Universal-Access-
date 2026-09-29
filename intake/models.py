from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# How near a hearing has to be before the queue flags it. Pending Christina's
# confirmation of the right window for removal defense.
HEARING_SOON_DAYS = 7


class IntakeSubmission(models.Model):
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('es', _('Spanish')),
        ('fr', _('French')),
        ('ar', _('Arabic')),
        ('ht', _('Haitian Creole')),
        ('ru', _('Russian')),
        ('hi', _('Hindi')),
        ('pa', _('Punjabi')),
        ('pt', _('Portuguese')),
        ('zh-hans', _('Chinese (Simplified)')),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('conflict_check', 'Needs Conflict Check'),
        ('translation_review', 'Needs Translation Review'),
        ('legal_review', 'Needs Legal Review'),
        ('accepted', 'Accepted'),
        ('referred', 'Referred'),
        ('closed', 'Closed'),
    ]

    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    country_of_origin = models.CharField(max_length=255)
    preferred_language = models.CharField(max_length=100)
    language_preference = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text=_('Language used while completing the intake form.'),
    )
    phone = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    current_location = models.CharField(max_length=255, blank=True)
    detained = models.BooleanField(default=False)
    immigration_court = models.CharField(max_length=255, blank=True)
    a_number = models.CharField(max_length=50, blank=True)
    next_hearing_date = models.DateField(null=True, blank=True)
    fear_of_return_summary = models.TextField()
    past_harm_summary = models.TextField(blank=True)
    countries_traveled_asylum_summary = models.TextField(blank=True)
    # Staff translations are stored separately so the applicant's wording is preserved.
    fear_of_return_summary_translated = models.TextField(
        blank=True,
        help_text=_('Staff translation only. The original response is preserved separately.'),
    )
    past_harm_summary_translated = models.TextField(
        blank=True,
        help_text=_('Staff translation only. The original response is preserved separately.'),
    )
    countries_traveled_asylum_summary_translated = models.TextField(
        blank=True,
        help_text=_('Staff translation only. The original response is preserved separately.'),
    )
    translated_response_language = models.CharField(
        max_length=10,
        blank=True,
        choices=LANGUAGE_CHOICES,
        help_text=_('Language of any staff-entered translated responses.'),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_intakes',
    )
    family_members_included = models.BooleanField(default=False)
    consent_acknowledged = models.BooleanField(default=False)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    # Attribution for the most recent status change only. Full audit history is a
    # separate Issue; these two answer "who moved this last, and when".
    status_changed_at = models.DateTimeField(null=True, blank=True)
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='status_changed_cases',
    )

    class Meta:
        permissions = [
            ('access_dashboard', 'Can access the case manager dashboard'),
            ('change_case_status', 'Can change case status'),
        ]

    def __str__(self):
        return self.full_name

    @property
    def hearing_is_soon(self) -> bool:
        """True when the next hearing falls within the urgency window."""
        if self.next_hearing_date is None:
            return False
        today = timezone.localdate()
        # Past-due hearings are deliberately unflagged: the flag means "act now",
        # and a date already gone needs a different conversation.
        return today <= self.next_hearing_date <= today + timedelta(days=HEARING_SOON_DAYS)


# --- I-589 intake application (Issue #41) -------------------------------------------------
#
# IntakeApplication and its child rows live alongside IntakeSubmission rather than replacing
# it (Christina, #41). Every applicant-facing label is Form I-589's own wording, quoted
# verbatim from Edition 03/01/23, with its Part and Item in a comment beside it. ModelForms
# inherit these as their labels, so this is the single place the wording lives.
# docs/i589-wording-review.md is the attorney sign-off copy and must match exactly.
# No help_text on applicant fields until the reviewer approves any.

TRANSLATION_HELP_TEXT = _('Staff translation only. The original response is preserved separately.')

GENDER_CHOICES = [
    ('male', _('Male')),
    ('female', _('Female')),
]

MARITAL_STATUS_CHOICES = [
    ('single', _('Single')),
    ('married', _('Married')),
    ('divorced', _('Divorced')),
    ('widowed', _('Widowed')),
]

# I-589 Part A.I, Item 18
COURT_PROCEEDINGS_CHOICES = [
    ('never', _('I have never been in Immigration Court proceedings.')),
    ('now', _('I am now in Immigration Court proceedings.')),
    (
        'past',
        _('I am not now in Immigration Court proceedings, but I have been in the past.'),
    ),
]

# Not I-589 wording. The applicant never picks this: the spouse and children formsets set
# it. The form's own headings are "Your spouse" and "Your Children".
FAMILY_RELATIONSHIP_CHOICES = [
    ('spouse', _('Spouse')),
    ('child', _('Child')),
]


class IntakeApplication(models.Model):
    # Header NOTE, page 1
    apply_withholding_cat = models.BooleanField(
        default=False,
        verbose_name=_(
            'Check this box if you also want to apply for withholding of removal under the '
            'Convention Against Torture.'
        ),
    )

    # I-589 Part A.I, Item 1
    a_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Alien Registration Number(s) (A-Number) (if any)'),
    )
    # I-589 Part A.I, Item 2 is the U.S. Social Security Number. Not collected (Christina).
    # I-589 Part A.I, Item 3
    uscis_online_account_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('USCIS Online Account Number (if any)'),
    )
    # I-589 Part A.I, Item 4
    last_name = models.CharField(max_length=255, verbose_name=_('Complete Last Name'))
    # I-589 Part A.I, Item 5
    first_name = models.CharField(max_length=255, verbose_name=_('First Name'))
    # I-589 Part A.I, Item 6
    middle_name = models.CharField(max_length=255, blank=True, verbose_name=_('Middle Name'))
    # I-589 Part A.I, Item 7
    other_names_used = models.TextField(
        blank=True,
        verbose_name=_('What other names have you used (include maiden name and aliases)?'),
    )
    other_names_used_translated = models.TextField(blank=True, help_text=TRANSLATION_HELP_TEXT)
    # I-589 Part A.I, Item 8: "Residence in the U.S. (where you physically reside)"
    residence_street = models.CharField(
        max_length=255, blank=True, verbose_name=_('Street Number and Name')
    )
    residence_apt_number = models.CharField(
        max_length=50, blank=True, verbose_name=_('Apt. Number')
    )
    residence_city = models.CharField(max_length=255, blank=True, verbose_name=_('City'))
    residence_state = models.CharField(max_length=100, blank=True, verbose_name=_('State'))
    residence_zip_code = models.CharField(max_length=20, blank=True, verbose_name=_('Zip Code'))
    residence_telephone_number = models.CharField(
        max_length=100, blank=True, verbose_name=_('Telephone Number')
    )
    # I-589 Part A.I, Item 9: "Mailing Address in the U.S. (if different than the address in
    # Item Number 8)"
    mailing_in_care_of = models.CharField(
        max_length=255, blank=True, verbose_name=_('In Care Of (if applicable):')
    )
    mailing_telephone_number = models.CharField(
        max_length=100, blank=True, verbose_name=_('Telephone Number')
    )
    mailing_street = models.CharField(
        max_length=255, blank=True, verbose_name=_('Street Number and Name')
    )
    mailing_apt_number = models.CharField(max_length=50, blank=True, verbose_name=_('Apt. Number'))
    mailing_city = models.CharField(max_length=255, blank=True, verbose_name=_('City'))
    mailing_state = models.CharField(max_length=100, blank=True, verbose_name=_('State'))
    mailing_zip_code = models.CharField(max_length=20, blank=True, verbose_name=_('Zip Code'))
    # I-589 Part A.I, Item 10
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, blank=True, verbose_name=_('Gender:')
    )
    # I-589 Part A.I, Item 11
    marital_status = models.CharField(
        max_length=10,
        choices=MARITAL_STATUS_CHOICES,
        blank=True,
        verbose_name=_('Marital Status:'),
    )
    # I-589 Part A.I, Item 12
    date_of_birth = models.DateField(
        null=True, blank=True, verbose_name=_('Date of Birth (mm/dd/yyyy)')
    )
    # I-589 Part A.I, Item 13
    city_and_country_of_birth = models.CharField(
        max_length=255, blank=True, verbose_name=_('City and Country of Birth')
    )
    # I-589 Part A.I, Item 14
    present_nationality = models.CharField(
        max_length=255, blank=True, verbose_name=_('Present Nationality (Citizenship)')
    )
    # I-589 Part A.I, Item 15
    nationality_at_birth = models.CharField(
        max_length=255, blank=True, verbose_name=_('Nationality at Birth')
    )
    # I-589 Part A.I, Item 16
    race_ethnic_or_tribal_group = models.CharField(
        max_length=255, blank=True, verbose_name=_('Race, Ethnic, or Tribal Group')
    )
    # I-589 Part A.I, Item 17
    religion = models.CharField(max_length=255, blank=True, verbose_name=_('Religion'))
    # I-589 Part A.I, Item 18
    immigration_court_proceedings = models.CharField(
        max_length=10,
        choices=COURT_PROCEEDINGS_CHOICES,
        blank=True,
        verbose_name=_('Check the box, a through c, that applies:'),
    )
    # I-589 Part A.I, Item 19.a
    date_last_left_country = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('When did you last leave your country? (mm/dd/yyyy)'),
    )
    # I-589 Part A.I, Item 19.b
    current_i94_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('What is your current I-94 Number, if any?'),
    )
    # I-589 Part A.I, Item 19.c is the repeatable entry list: see IntakeEntry.
    # I-589 Part A.I, Item 20
    last_travel_document_country = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('What country issued your last passport or travel document?'),
    )
    # I-589 Part A.I, Item 21
    passport_number = models.CharField(
        max_length=100, blank=True, verbose_name=_('Passport Number')
    )
    travel_document_number = models.CharField(
        max_length=100, blank=True, verbose_name=_('Travel Document Number')
    )
    # I-589 Part A.I, Item 22
    travel_document_expiration_date = models.DateField(
        null=True, blank=True, verbose_name=_('Expiration Date (mm/dd/yyyy)')
    )
    # I-589 Part A.I, Item 23
    native_language = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('What is your native language (include dialect, if applicable)?'),
    )
    # I-589 Part A.I, Item 24
    fluent_in_english = models.BooleanField(
        null=True, blank=True, verbose_name=_('Are you fluent in English?')
    )
    # I-589 Part A.I, Item 25
    other_languages_spoken = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('What other languages do you speak fluently?'),
    )

    # I-589 Part B, Item 1: "I am seeking asylum or withholding of removal based on:"
    basis_race = models.BooleanField(default=False, verbose_name=_('Race'))
    basis_religion = models.BooleanField(default=False, verbose_name=_('Religion'))
    basis_nationality = models.BooleanField(default=False, verbose_name=_('Nationality'))
    basis_political_opinion = models.BooleanField(
        default=False, verbose_name=_('Political opinion')
    )
    basis_particular_social_group = models.BooleanField(
        default=False, verbose_name=_('Membership in a particular social group')
    )
    basis_torture_convention = models.BooleanField(
        default=False, verbose_name=_('Torture Convention')
    )
    # I-589 Part B, Item 1.A
    experienced_harm = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'Have you, your family, or close friends or colleagues ever experienced harm or '
            'mistreatment or threats in the past by anyone?'
        ),
    )
    experienced_harm_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes," explain in detail: 1. What happened; 2. When the harm or mistreatment '
            'or threats occurred; 3. Who caused the harm or mistreatment or threats; and '
            '4. Why you believe the harm or mistreatment or threats occurred.'
        ),
    )
    experienced_harm_explanation_translated = models.TextField(
        blank=True, help_text=TRANSLATION_HELP_TEXT
    )
    # I-589 Part B, Item 1.B
    fears_harm_on_return = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_('Do you fear harm or mistreatment if you return to your home country?'),
    )
    fears_harm_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes," explain in detail: 1. What harm or mistreatment you fear; 2. Who you '
            'believe would harm or mistreat you; and 3. Why you believe you would or could be '
            'harmed or mistreated.'
        ),
    )
    fears_harm_explanation_translated = models.TextField(
        blank=True, help_text=TRANSLATION_HELP_TEXT
    )
    # I-589 Part B, Item 2
    arrested_or_detained_abroad = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'Have you or your family members ever been accused, charged, arrested, detained, '
            'interrogated, convicted and sentenced, or imprisoned in any country other than '
            'the United States (including for an immigration law violation)?'
        ),
    )
    arrested_explanation = models.TextField(
        blank=True,
        verbose_name=_('If "Yes," explain the circumstances and reasons for the action.'),
    )
    arrested_explanation_translated = models.TextField(blank=True, help_text=TRANSLATION_HELP_TEXT)
    # I-589 Part B, Item 3.A
    belonged_to_organization = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'Have you or your family members ever belonged to or been associated with any '
            'organizations or groups in your home country, such as, but not limited to, a '
            'political party, student group, labor union, religious organization, military '
            'or paramilitary group, civil patrol, guerrilla organization, ethnic group, human '
            'rights group, or the press or media?'
        ),
    )
    organization_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes," describe for each person the level of participation, any leadership '
            'or other positions held, and the length of time you or your family members were '
            'involved in each organization or activity.'
        ),
    )
    organization_explanation_translated = models.TextField(
        blank=True, help_text=TRANSLATION_HELP_TEXT
    )
    # I-589 Part B, Item 3.B
    continues_participation = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'Do you or your family members continue to participate in any way in these '
            'organizations or groups?'
        ),
    )
    continued_participation_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes," describe for each person your or your family members\' current level '
            'of participation, any leadership or other positions currently held, and the '
            'length of time you or your family members have been involved in each '
            'organization or group.'
        ),
    )
    continued_participation_explanation_translated = models.TextField(
        blank=True, help_text=TRANSLATION_HELP_TEXT
    )
    # I-589 Part B, Item 4
    fears_torture = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'Are you afraid of being subjected to torture in your home country or any other '
            'country to which you may be returned?'
        ),
    )
    torture_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes," explain why you are afraid and describe the nature of torture you '
            'fear, by whom, and why it would be inflicted.'
        ),
    )
    torture_explanation_translated = models.TextField(blank=True, help_text=TRANSLATION_HELP_TEXT)

    # I-589 Part C, Item 1
    family_applied_for_protection = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'Have you, your spouse, your child(ren), your parents or your siblings ever '
            'applied to the U.S. Government for refugee status, asylum, or withholding of '
            'removal?'
        ),
    )
    protection_application_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes," explain the decision and what happened to any status you, your '
            'spouse, your child(ren), your parents, or your siblings received as a result '
            'of that decision. Indicate whether or not you were included in a parent or '
            "spouse's application. If so, include your parent or spouse's A-number in your "
            'response. If you have been denied asylum by an immigration judge or the Board '
            'of Immigration Appeals, describe any change(s) in conditions in your country or '
            'your own personal circumstances since the date of the denial that may affect '
            'your eligibility for asylum.'
        ),
    )
    protection_application_explanation_translated = models.TextField(
        blank=True, help_text=TRANSLATION_HELP_TEXT
    )
    # I-589 Part C, Item 2.A
    traveled_through_other_country = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'After leaving the country from which you are claiming asylum, did you or your '
            'spouse or child(ren) who are now in the United States travel through or reside '
            'in any other country before entering the United States?'
        ),
    )
    # I-589 Part C, Item 2.B
    applied_for_status_elsewhere = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'Have you, your spouse, your child(ren), or other family members, such as your '
            'parents or siblings, ever applied for or received any lawful status in any '
            'country other than the one from which you are now claiming asylum?'
        ),
    )
    # I-589 Part C, Item 2 (one explanation covers 2.A and 2.B)
    other_country_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes" to either or both questions (2A and/or 2B), provide for each person '
            'the following: the name of each country and the length of stay, the '
            "person's status while there, the reasons for leaving, whether or not the "
            'person is entitled to return for lawful residence purposes, and whether the '
            'person applied for refugee status or for asylum while there, and if not, why '
            'he or she did not do so.'
        ),
    )
    other_country_explanation_translated = models.TextField(
        blank=True, help_text=TRANSLATION_HELP_TEXT
    )
    # I-589 Part C, Item 3
    caused_harm_to_others = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'Have you, your spouse or your child(ren) ever ordered, incited, assisted or '
            'otherwise participated in causing harm or suffering to any person because of '
            'his or her race, religion, nationality, membership in a particular social '
            'group or belief in a particular political opinion?'
        ),
    )
    caused_harm_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes," describe in detail each such incident and your own, your '
            "spouse's, or your child(ren)'s involvement."
        ),
    )
    caused_harm_explanation_translated = models.TextField(
        blank=True, help_text=TRANSLATION_HELP_TEXT
    )
    # I-589 Part C, Item 4
    returned_to_country = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'After you left the country where you were harmed or fear harm, did you return '
            'to that country?'
        ),
    )
    return_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes," describe in detail the circumstances of your visit(s) (for example, '
            'the date(s) of the trip(s), the purpose(s) of the trip(s), and the length of '
            'time you remained in that country for the visit(s).)'
        ),
    )
    return_explanation_translated = models.TextField(blank=True, help_text=TRANSLATION_HELP_TEXT)
    # I-589 Part C, Item 5
    filing_after_one_year = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'Are you filing this application more than 1 year after your last arrival in '
            'the United States?'
        ),
    )
    late_filing_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes," explain why you did not file within the first year after you '
            'arrived. You must be prepared to explain at your interview or hearing why you '
            'did not file your asylum application within the first year after you arrived. '
            'For guidance in answering this question, see Instructions, Part 1: Filing '
            'Instructions, Section V. "Completing the Form," Part C.'
        ),
    )
    late_filing_explanation_translated = models.TextField(
        blank=True, help_text=TRANSLATION_HELP_TEXT
    )
    # I-589 Part C, Item 6
    crimes_in_united_states = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'Have you or any member of your family included in the application ever '
            'committed any crime and/or been arrested, charged, convicted, or sentenced for '
            'any crimes in the United States (including for an immigration law violation)?'
        ),
    )
    us_crimes_explanation = models.TextField(
        blank=True,
        verbose_name=_(
            'If "Yes," for each instance, specify in your response: what occurred and the '
            'circumstances, dates, length of sentence received, location, the duration of '
            'the detention or imprisonment, reason(s) for the detention or conviction, any '
            'formal charges that were lodged against you or your relatives included in your '
            'application, and the reason(s) for release. Attach documents referring to '
            'these incidents, if they are available, or an explanation of why documents are '
            'not available.'
        ),
    )
    us_crimes_explanation_translated = models.TextField(blank=True, help_text=TRANSLATION_HELP_TEXT)

    # URDP intake fields carried over from IntakeSubmission (not on the I-589). Labels reuse
    # the existing form's msgids, already translated in every catalog.
    email = models.EmailField(blank=True, verbose_name=_('Email address'))
    preferred_language = models.CharField(max_length=100, verbose_name=_('Preferred language'))
    # "Current city or location" is the applicant's present whereabouts, including a
    # detention facility; it is not the residence address in Part A.I, Item 8.
    current_location = models.CharField(
        max_length=255, blank=True, verbose_name=_('Current city or location')
    )
    detained = models.BooleanField(default=False, verbose_name=_('Currently detained'))
    immigration_court = models.CharField(
        max_length=255, blank=True, verbose_name=_('Immigration court')
    )
    next_hearing_date = models.DateField(null=True, blank=True, verbose_name=_('Next hearing date'))
    consent_acknowledged = models.BooleanField(default=False)

    # Set by code, never by the applicant.
    language_preference = models.CharField(
        max_length=10,
        choices=IntakeSubmission.LANGUAGE_CHOICES,
        default='en',
        help_text=_('Language used while completing the intake form.'),
    )
    translated_response_language = models.CharField(
        max_length=10,
        blank=True,
        choices=IntakeSubmission.LANGUAGE_CHOICES,
        help_text=_('Language of any staff-entered translated responses.'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # Case-management columns mirror IntakeSubmission so the dashboard can treat both the
    # same way (Christina, 2026-09-10). Plain duplication: IntakeSubmission is slated for
    # retirement, so no shared base class.
    status = models.CharField(max_length=50, choices=IntakeSubmission.STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_applications',
    )
    status_changed_at = models.DateTimeField(null=True, blank=True)
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='status_changed_applications',
    )

    def __str__(self):
        # pk only: a repr must never carry applicant data into a log or traceback.
        return f'Application {self.pk}'

    @property
    def hearing_is_soon(self) -> bool:
        """True when the next hearing falls within the urgency window."""
        if self.next_hearing_date is None:
            return False
        today = timezone.localdate()
        return today <= self.next_hearing_date <= today + timedelta(days=HEARING_SOON_DAYS)


class IntakeEntry(models.Model):
    """One row of I-589 Part A.I, Item 19.c: an entry into the U.S., most recent first."""

    application = models.ForeignKey(
        IntakeApplication, on_delete=models.CASCADE, related_name='entries'
    )
    position = models.PositiveIntegerField(default=0)
    date = models.DateField(null=True, blank=True, verbose_name=_('Date'))
    place = models.CharField(max_length=255, blank=True, verbose_name=_('Place'))
    status = models.CharField(max_length=255, blank=True, verbose_name=_('Status'))
    date_status_expires = models.DateField(
        null=True, blank=True, verbose_name=_('Date Status Expires')
    )

    class Meta:
        ordering = ['position', 'pk']
        verbose_name_plural = 'intake entries'

    def __str__(self):
        return f'Entry {self.pk}'


class IntakeFamilyMember(models.Model):
    """One row of I-589 Part A.II: the spouse or one child.

    Spouse-only and child-only items stay blank for the other relationship. Where the spouse
    and child blocks word the same item differently, the spouse wording is the verbose_name
    and the child formset overrides the label with the child wording.
    """

    application = models.ForeignKey(
        IntakeApplication, on_delete=models.CASCADE, related_name='family_members'
    )
    relationship = models.CharField(max_length=10, choices=FAMILY_RELATIONSHIP_CHOICES)
    position = models.PositiveIntegerField(default=0)

    # I-589 Part A.II, spouse Item 1 / child Item 1
    a_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Alien Registration Number (A-Number) (if any)'),
    )
    # I-589 Part A.II, spouse Item 2 / child Item 2
    passport_id_card_number = models.CharField(
        max_length=100, blank=True, verbose_name=_('Passport/ID Card Number (if any)')
    )
    # I-589 Part A.II, spouse Item 4 / child Item 4 is the U.S. Social Security Number.
    # Not collected (Christina).
    # I-589 Part A.II, spouse Item 5 / child Item 5
    last_name = models.CharField(max_length=255, blank=True, verbose_name=_('Complete Last Name'))
    # I-589 Part A.II, spouse Item 6 / child Item 6
    first_name = models.CharField(max_length=255, blank=True, verbose_name=_('First Name'))
    # I-589 Part A.II, spouse Item 7 / child Item 7
    middle_name = models.CharField(max_length=255, blank=True, verbose_name=_('Middle Name'))
    # I-589 Part A.II, spouse Item 3 / child Item 8
    date_of_birth = models.DateField(
        null=True, blank=True, verbose_name=_('Date of Birth (mm/dd/yyyy)')
    )
    # I-589 Part A.II, spouse Item 11 / child Item 9
    city_and_country_of_birth = models.CharField(
        max_length=255, blank=True, verbose_name=_('City and Country of Birth')
    )
    # I-589 Part A.II, spouse Item 12 / child Item 10
    nationality = models.CharField(
        max_length=255, blank=True, verbose_name=_('Nationality (Citizenship)')
    )
    # I-589 Part A.II, spouse Item 13 / child Item 11
    race_ethnic_or_tribal_group = models.CharField(
        max_length=255, blank=True, verbose_name=_('Race, Ethnic, or Tribal Group')
    )
    # I-589 Part A.II, spouse Item 14 / child Item 12
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, blank=True, verbose_name=_('Gender')
    )
    # I-589 Part A.II, spouse Item 15 / child Item 13 ("Is this child in the U.S.?")
    in_united_states = models.BooleanField(
        null=True, blank=True, verbose_name=_('Is this person in the U.S.?')
    )
    # Same item, the "No (Specify location):" blank.
    location_if_not_in_us = models.CharField(
        max_length=255, blank=True, verbose_name=_('Specify location')
    )
    # I-589 Part A.II, spouse Item 16 / child Item 14
    place_of_last_entry = models.CharField(
        max_length=255, blank=True, verbose_name=_('Place of last entry into the U.S.')
    )
    # I-589 Part A.II, spouse Item 17 / child Item 15
    date_of_last_entry = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Date of last entry into the U.S. (mm/dd/yyyy)'),
    )
    # I-589 Part A.II, spouse Item 18 / child Item 16
    i94_number = models.CharField(max_length=50, blank=True, verbose_name=_('I-94 Number (if any)'))
    # I-589 Part A.II, spouse Item 19 / child Item 17
    status_when_last_admitted = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Status when last admitted (Visa type, if any)'),
    )
    # I-589 Part A.II, spouse Item 20 / child Item 18 ("What is your child's current status?")
    current_status = models.CharField(
        max_length=255, blank=True, verbose_name=_("What is your spouse's current status?")
    )
    # I-589 Part A.II, spouse Item 21 / child Item 19
    authorized_stay_expiration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_(
            'What is the expiration date of his/her authorized stay, if any? (mm/dd/yyyy)'
        ),
    )
    # I-589 Part A.II, spouse Item 22 / child Item 20 ("Is your child in Immigration Court
    # proceedings?")
    in_immigration_court_proceedings = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_('Is your spouse in Immigration Court proceedings?'),
    )
    # I-589 Part A.II, spouse Item 24 / child Item 21 ("If in the U.S., is this child to be
    # included in this application? (Check the appropriate box.)")
    include_in_application = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=_(
            'If in the U.S., is your spouse to be included in this application? (Check the '
            'appropriate box.)'
        ),
    )

    # Spouse only.
    # I-589 Part A.II, spouse Item 8
    other_names_used = models.TextField(
        blank=True, verbose_name=_('Other names used (include maiden name and aliases)')
    )
    other_names_used_translated = models.TextField(blank=True, help_text=TRANSLATION_HELP_TEXT)
    # I-589 Part A.II, spouse Item 9
    date_of_marriage = models.DateField(
        null=True, blank=True, verbose_name=_('Date of Marriage (mm/dd/yyyy)')
    )
    # I-589 Part A.II, spouse Item 10
    place_of_marriage = models.CharField(
        max_length=255, blank=True, verbose_name=_('Place of Marriage')
    )
    # I-589 Part A.II, spouse Item 23
    date_of_previous_arrival = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('If previously in the U.S., date of previous arrival (mm/dd/yyyy)'),
    )

    # Child only.
    # I-589 Part A.II, child Item 3
    marital_status = models.CharField(
        max_length=10,
        choices=MARITAL_STATUS_CHOICES,
        blank=True,
        verbose_name=_('Marital Status (Married, Single, Divorced, Widowed)'),
    )

    class Meta:
        ordering = ['position', 'pk']

    def __str__(self):
        return f'Family member {self.pk}'
