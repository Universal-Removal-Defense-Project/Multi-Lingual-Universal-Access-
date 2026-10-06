# I-589 intake wording review

**For:** Blake Koch, reviewer. **From:** Raj Desai, refs Issue #41.

Every label below is quoted verbatim from **Form I-589, Edition 03/01/23** (the editable copy
you supplied). USCIS's current edition is 07/28/26. Per your note that the fields are the same,
please confirm the item numbering still matches 07/28/26 as you go; any renumbering changes the
reference column only, not the code.

**Scope of this review.** Blake's review covers field scope and wording. Attorney review is
still required before the new form route is linked from the site; until then `/intake-form`
is reachable only by direct URL.

**What is in code today.** Each row's label is the field's `verbose_name` in `intake/models.py`,
so the intake form, the dashboard and the admin all show the same string. There is no help text
on any applicant field. Where the form prints an instruction next to a box (for example Part B's
"If 'Yes,' explain in detail: ..."), that instruction is the label of the explanation box, so it
is reviewed as a label. The **Help text** column is a slot for anything you want added; leave it
blank to add nothing.

**Decisions already taken (Christina Wu, 2026-09-10), listed so you can object:**

1. v1 scope is Parts A.I, A.II, B and C. Part A.III (background tables) is a follow-up Issue.
   Parts D to G (signature, preparer, officer, judge) are not intake data.
2. **Social Security Number is not collected** anywhere it appears (A.I Item 2, spouse Item 4,
   child Item 4).
3. Free-text answers get a separate staff-translation field so the applicant's wording is
   never overwritten. That is: A.I Item 7, spouse Item 8, and every explanation box in Parts B
   and C. Identifiers, dates and choices do not.

**Flags for you specifically:**

- **Gender** offers only Male / Female, as the form does. Whether URDP offers anything else is
  a policy call, not made here.
- **"Spouse" / "Child"** appear only to staff (dashboard, admin), never to the applicant. The
  applicant sees the form's own headings "Your spouse" and "Your Children".
- **Not stored** because they are derivable: "I am not married" (= A.I Item 11), "I do not have
  any children" and "Total number of children" (= number of child rows entered).
- **"(mm/dd/yyyy)"** is kept verbatim in date labels. The web form uses a native date control,
  so the hint is redundant; strike it in the Help text column if you want it dropped.
- Four A.II items are worded differently for spouse and child. Both wordings are listed; the
  spouse row shows the spouse wording and the child rows show the child wording.
- Two step headings (steps 2 and 6), the step 1 intro, and the small set of button labels at the
  end are the only strings that are not I-589 text. The intro says the intake *follows* Form
  I-589, not that the applicant is filing one.

Mark decisions in the last column: **OK**, **change to: ...**, or **drop**.

## Step 1: Part A.I, Information About You

Step heading (verbatim Part title): **Information About You**

| Field | Label (verbatim) | I-589 ref | Help text | Decision |
|---|---|---|---|---|
| `apply_withholding_cat` | Check this box if you also want to apply for withholding of removal under the Convention Against Torture. | Page 1 header NOTE | | |
| `a_number` | Alien Registration Number(s) (A-Number) (if any) | A.I 1 | | |
| (not collected) | U.S. Social Security Number (if any) | A.I 2 | | |
| `uscis_online_account_number` | USCIS Online Account Number (if any) | A.I 3 | | |
| `last_name` (required) | Complete Last Name | A.I 4 | | |
| `first_name` (required) | First Name | A.I 5 | | |
| `middle_name` | Middle Name | A.I 6 | | |
| `other_names_used` (+ staff translation) | What other names have you used (include maiden name and aliases)? | A.I 7 | | |
| (group heading) | Residence in the U.S. (where you physically reside) | A.I 8 | | |
| `residence_street` | Street Number and Name | A.I 8 | | |
| `residence_apt_number` | Apt. Number | A.I 8 | | |
| `residence_city` | City | A.I 8 | | |
| `residence_state` | State | A.I 8 | | |
| `residence_zip_code` | Zip Code | A.I 8 | | |
| `residence_telephone_number` | Telephone Number | A.I 8 | | |
| (group heading) | Mailing Address in the U.S. (if different than the address in Item Number 8) | A.I 9 | | |
| `mailing_in_care_of` | In Care Of (if applicable): | A.I 9 | | |
| `mailing_telephone_number` | Telephone Number | A.I 9 | | |
| `mailing_street` | Street Number and Name | A.I 9 | | |
| `mailing_apt_number` | Apt. Number | A.I 9 | | |
| `mailing_city` | City | A.I 9 | | |
| `mailing_state` | State | A.I 9 | | |
| `mailing_zip_code` | Zip Code | A.I 9 | | |
| `gender` | Gender: (Male / Female) | A.I 10 | | |
| `marital_status` | Marital Status: (Single / Married / Divorced / Widowed) | A.I 11 | | |
| `date_of_birth` | Date of Birth (mm/dd/yyyy) | A.I 12 | | |
| `city_and_country_of_birth` | City and Country of Birth | A.I 13 | | |
| `present_nationality` | Present Nationality (Citizenship) | A.I 14 | | |
| `nationality_at_birth` | Nationality at Birth | A.I 15 | | |
| `race_ethnic_or_tribal_group` | Race, Ethnic, or Tribal Group | A.I 16 | | |
| `religion` | Religion | A.I 17 | | |

## Step 2: Part A.I, Items 18 to 25

Step heading (**not I-589 text, authored**): **Immigration History**

| Field | Label (verbatim) | I-589 ref | Help text | Decision |
|---|---|---|---|---|
| `immigration_court_proceedings` | Check the box, a through c, that applies: | A.I 18 | | |
| (choice a) | I have never been in Immigration Court proceedings. | A.I 18.a | | |
| (choice b) | I am now in Immigration Court proceedings. | A.I 18.b | | |
| (choice c) | I am not now in Immigration Court proceedings, but I have been in the past. | A.I 18.c | | |
| `date_last_left_country` | When did you last leave your country? (mm/dd/yyyy) | A.I 19.a | | |
| `current_i94_number` | What is your current I-94 Number, if any? | A.I 19.b | | |
| (group heading, repeatable rows) | List each entry into the U.S. beginning with your most recent entry. List date (mm/dd/yyyy), place, and your status for each entry. (Attach additional sheets as needed.) | A.I 19.c | | |
| `IntakeEntry.date` | Date | A.I 19.c | | |
| `IntakeEntry.place` | Place | A.I 19.c | | |
| `IntakeEntry.status` | Status | A.I 19.c | | |
| `IntakeEntry.date_status_expires` | Date Status Expires | A.I 19.c | | |
| `last_travel_document_country` | What country issued your last passport or travel document? | A.I 20 | | |
| `passport_number` | Passport Number | A.I 21 | | |
| `travel_document_number` | Travel Document Number | A.I 21 | | |
| `travel_document_expiration_date` | Expiration Date (mm/dd/yyyy) | A.I 22 | | |
| `native_language` | What is your native language (include dialect, if applicable)? | A.I 23 | | |
| `fluent_in_english` | Are you fluent in English? (Yes / No) | A.I 24 | | |
| `other_languages_spoken` | What other languages do you speak fluently? | A.I 25 | | |

## Step 3: Part A.II, Information About Your Spouse and Children

Step heading (verbatim Part title): **Information About Your Spouse and Children**

Sub-headings (verbatim): **Your spouse** and **Your Children**. The form's own instruction under
Your Children, "List all of your children, regardless of age, location, or marital status.",
is shown verbatim.

One table covers both, since the rows are the same record type. Column "Spouse / Child" gives
the item number in each block. Where the wording differs, both are quoted.

| Field | Label (verbatim) | Spouse / Child | Help text | Decision |
|---|---|---|---|---|
| `a_number` | Alien Registration Number (A-Number) (if any) | 1 / 1 | | |
| `passport_id_card_number` | Passport/ID Card Number (if any) | 2 / 2 | | |
| `date_of_birth` | Date of Birth (mm/dd/yyyy) | 3 / 8 | | |
| (not collected) | U.S. Social Security Number (if any) | 4 / 4 | | |
| `last_name` | Complete Last Name | 5 / 5 | | |
| `first_name` | First Name | 6 / 6 | | |
| `middle_name` | Middle Name | 7 / 7 | | |
| `other_names_used` (+ staff translation), spouse only | Other names used (include maiden name and aliases) | 8 / - | | |
| `date_of_marriage`, spouse only | Date of Marriage (mm/dd/yyyy) | 9 / - | | |
| `place_of_marriage`, spouse only | Place of Marriage | 10 / - | | |
| `marital_status`, child only | Marital Status (Married, Single, Divorced, Widowed) | - / 3 | | |
| `city_and_country_of_birth` | City and Country of Birth | 11 / 9 | | |
| `nationality` | Nationality (Citizenship) | 12 / 10 | | |
| `race_ethnic_or_tribal_group` | Race, Ethnic, or Tribal Group | 13 / 11 | | |
| `gender` | Gender (Male / Female) | 14 / 12 | | |
| `in_united_states` | Spouse: Is this person in the U.S.? / Child: Is this child in the U.S.? (Yes / No) | 15 / 13 | | |
| `location_if_not_in_us` | No (Specify location): (shown as "Specify location") | 15 / 13 | | |
| `place_of_last_entry` | Place of last entry into the U.S. | 16 / 14 | | |
| `date_of_last_entry` | Date of last entry into the U.S. (mm/dd/yyyy) | 17 / 15 | | |
| `i94_number` | I-94 Number (if any) | 18 / 16 | | |
| `status_when_last_admitted` | Status when last admitted (Visa type, if any) | 19 / 17 | | |
| `current_status` | Spouse: What is your spouse's current status? / Child: What is your child's current status? | 20 / 18 | | |
| `authorized_stay_expiration_date` | What is the expiration date of his/her authorized stay, if any? (mm/dd/yyyy) | 21 / 19 | | |
| `in_immigration_court_proceedings` | Spouse: Is your spouse in Immigration Court proceedings? / Child: Is your child in Immigration Court proceedings? (Yes / No) | 22 / 20 | | |
| `date_of_previous_arrival`, spouse only | If previously in the U.S., date of previous arrival (mm/dd/yyyy) | 23 / - | | |
| `include_in_application` | Spouse: If in the U.S., is your spouse to be included in this application? (Check the appropriate box.) / Child: If in the U.S., is this child to be included in this application? (Check the appropriate box.) (Yes / No) | 24 / 21 | | |

## Step 4: Part B, Information About Your Application

Step heading (verbatim Part title): **Information About Your Application**

The Part B preamble ("When answering the following questions ... you must provide a detailed and
specific account ...") and the "Refer to Instructions ..." paragraph are **not shown**. They
address the paper filing, not intake. Say if you want either shown.

| Field | Label (verbatim) | I-589 ref | Help text | Decision |
|---|---|---|---|---|
| (group heading) | Why are you applying for asylum or withholding of removal under section 241(b)(3) of the INA, or for withholding of removal under the Convention Against Torture? Check the appropriate box(es) below and then provide detailed answers to questions A and B below. | B 1 | | |
| (sub-heading) | I am seeking asylum or withholding of removal based on: | B 1 | | |
| `basis_race` | Race | B 1 | | |
| `basis_religion` | Religion | B 1 | | |
| `basis_nationality` | Nationality | B 1 | | |
| `basis_political_opinion` | Political opinion | B 1 | | |
| `basis_particular_social_group` | Membership in a particular social group | B 1 | | |
| `basis_torture_convention` | Torture Convention | B 1 | | |
| `experienced_harm` | Have you, your family, or close friends or colleagues ever experienced harm or mistreatment or threats in the past by anyone? (Yes / No) | B 1.A | | |
| `experienced_harm_explanation` (+ staff translation) | If "Yes," explain in detail: 1. What happened; 2. When the harm or mistreatment or threats occurred; 3. Who caused the harm or mistreatment or threats; and 4. Why you believe the harm or mistreatment or threats occurred. | B 1.A | | |
| `fears_harm_on_return` | Do you fear harm or mistreatment if you return to your home country? (Yes / No) | B 1.B | | |
| `fears_harm_explanation` (+ staff translation) | If "Yes," explain in detail: 1. What harm or mistreatment you fear; 2. Who you believe would harm or mistreat you; and 3. Why you believe you would or could be harmed or mistreated. | B 1.B | | |
| `arrested_or_detained_abroad` | Have you or your family members ever been accused, charged, arrested, detained, interrogated, convicted and sentenced, or imprisoned in any country other than the United States (including for an immigration law violation)? (Yes / No) | B 2 | | |
| `arrested_explanation` (+ staff translation) | If "Yes," explain the circumstances and reasons for the action. | B 2 | | |
| `belonged_to_organization` | Have you or your family members ever belonged to or been associated with any organizations or groups in your home country, such as, but not limited to, a political party, student group, labor union, religious organization, military or paramilitary group, civil patrol, guerrilla organization, ethnic group, human rights group, or the press or media? (Yes / No) | B 3.A | | |
| `organization_explanation` (+ staff translation) | If "Yes," describe for each person the level of participation, any leadership or other positions held, and the length of time you or your family members were involved in each organization or activity. | B 3.A | | |
| `continues_participation` | Do you or your family members continue to participate in any way in these organizations or groups? (Yes / No) | B 3.B | | |
| `continued_participation_explanation` (+ staff translation) | If "Yes," describe for each person your or your family members' current level of participation, any leadership or other positions currently held, and the length of time you or your family members have been involved in each organization or group. | B 3.B | | |
| `fears_torture` | Are you afraid of being subjected to torture in your home country or any other country to which you may be returned? (Yes / No) | B 4 | | |
| `torture_explanation` (+ staff translation) | If "Yes," explain why you are afraid and describe the nature of torture you fear, by whom, and why it would be inflicted. | B 4 | | |

## Step 5: Part C, Additional Information About Your Application

Step heading (verbatim Part title): **Additional Information About Your Application**

| Field | Label (verbatim) | I-589 ref | Help text | Decision |
|---|---|---|---|---|
| `family_applied_for_protection` | Have you, your spouse, your child(ren), your parents or your siblings ever applied to the U.S. Government for refugee status, asylum, or withholding of removal? (Yes / No) | C 1 | | |
| `protection_application_explanation` (+ staff translation) | If "Yes," explain the decision and what happened to any status you, your spouse, your child(ren), your parents, or your siblings received as a result of that decision. Indicate whether or not you were included in a parent or spouse's application. If so, include your parent or spouse's A-number in your response. If you have been denied asylum by an immigration judge or the Board of Immigration Appeals, describe any change(s) in conditions in your country or your own personal circumstances since the date of the denial that may affect your eligibility for asylum. | C 1 | | |
| `traveled_through_other_country` | After leaving the country from which you are claiming asylum, did you or your spouse or child(ren) who are now in the United States travel through or reside in any other country before entering the United States? (Yes / No) | C 2.A | | |
| `applied_for_status_elsewhere` | Have you, your spouse, your child(ren), or other family members, such as your parents or siblings, ever applied for or received any lawful status in any country other than the one from which you are now claiming asylum? (Yes / No) | C 2.B | | |
| `other_country_explanation` (+ staff translation) | If "Yes" to either or both questions (2A and/or 2B), provide for each person the following: the name of each country and the length of stay, the person's status while there, the reasons for leaving, whether or not the person is entitled to return for lawful residence purposes, and whether the person applied for refugee status or for asylum while there, and if not, why he or she did not do so. | C 2 | | |
| `caused_harm_to_others` | Have you, your spouse or your child(ren) ever ordered, incited, assisted or otherwise participated in causing harm or suffering to any person because of his or her race, religion, nationality, membership in a particular social group or belief in a particular political opinion? (Yes / No) | C 3 | | |
| `caused_harm_explanation` (+ staff translation) | If "Yes," describe in detail each such incident and your own, your spouse's, or your child(ren)'s involvement. | C 3 | | |
| `returned_to_country` | After you left the country where you were harmed or fear harm, did you return to that country? (Yes / No) | C 4 | | |
| `return_explanation` (+ staff translation) | If "Yes," describe in detail the circumstances of your visit(s) (for example, the date(s) of the trip(s), the purpose(s) of the trip(s), and the length of time you remained in that country for the visit(s).) | C 4 | | |
| `filing_after_one_year` | Are you filing this application more than 1 year after your last arrival in the United States? (Yes / No) | C 5 | | |
| `late_filing_explanation` (+ staff translation) | If "Yes," explain why you did not file within the first year after you arrived. You must be prepared to explain at your interview or hearing why you did not file your asylum application within the first year after you arrived. For guidance in answering this question, see Instructions, Part 1: Filing Instructions, Section V. "Completing the Form," Part C. | C 5 | | |
| `crimes_in_united_states` | Have you or any member of your family included in the application ever committed any crime and/or been arrested, charged, convicted, or sentenced for any crimes in the United States (including for an immigration law violation)? (Yes / No) | C 6 | | |
| `us_crimes_explanation` (+ staff translation) | If "Yes," for each instance, specify in your response: what occurred and the circumstances, dates, length of sentence received, location, the duration of the detention or imprisonment, reason(s) for the detention or conviction, any formal charges that were lodged against you or your relatives included in your application, and the reason(s) for release. Attach documents referring to these incidents, if they are available, or an explanation of why documents are not available. | C 6 | | |

## Step 6: URDP contact, case status and consent (not on the I-589)

Step heading (**not I-589 text, authored**): **Contact and Consent**

These labels are carried over unchanged from the current intake form and are already translated
in all nine languages. Listed for completeness; they were not written for this review.

| Field | Label (existing form) | Source | Help text | Decision |
|---|---|---|---|---|
| `email` | Email address | current form | | |
| `preferred_language` (required) | Preferred language | current form | | |
| `current_location` | Current city or location | current form (placeholder: City, state, or detention facility) | | |
| `detained` | Currently detained | current form (Are you currently detained? / Yes, I am detained) | | |
| `immigration_court` | Immigration court | current form | | |
| `next_hearing_date` | Next hearing date | current form | | |
| `consent_acknowledged` (required) | I understand that submitting this form does not create an attorney-client relationship. | current form, unchanged | | |
| (notice, top of every step) | Submitting this form does not create an attorney-client relationship. URDP must review your intake, complete conflict screening, and provide written acceptance before representation begins. | current form, unchanged | | |

## UI strings that are not I-589 wording

Small, authored, applicant-visible. Listed so nothing applicant-facing escapes review.

| Where | String |
|---|---|
| Intro title, step 1 only (the form's official name) | Form I-589, Application for Asylum and for Withholding of Removal |
| Intro text, step 1 only | This intake follows Form I-589, the U.S. government form used to apply for asylum and for withholding of removal. It asks about you, your family, how you came to the United States, and why you fear returning to your home country. URDP uses your answers to review your case and prepare your application. Answer what you can. You may leave a question blank if you do not know the answer. |
| Progress line | Step N of 6 |
| Privacy line, under the progress line | For your privacy, your answers are cleared after 20 minutes without activity or when you close your browser. |
| Button, every step | Start over and clear my answers |
| Buttons | Back, Continue, Submit Intake Securely (existing), Add another entry, Add another child, Remove |
| Field badges | Required, Optional (existing) |
| Yes / No controls | Yes, No |

## Deferred, for the record

Part A.III (last address before the U.S., residences past 5 years, education, employment,
parents and siblings) is a follow-up Issue. Parts D to G are not intake data.
