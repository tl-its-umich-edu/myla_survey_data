from django import forms

import mysql.connector
from django.conf import settings
from material import Layout, Fieldset

# connect to MySQL Database

cnx = mysql.connector.connect(
    user=settings.DATABASES['qualtrics'].get('USER'),
    password=settings.DATABASES['qualtrics'].get('PASSWORD'),
    host=settings.DATABASES['qualtrics'].get('HOST'),
    port=settings.DATABASES['qualtrics'].get('PORT'),
    database=settings.DATABASES['qualtrics'].get('NAME'))
cursor = cnx.cursor()


class DataForm(forms.Form):
    # more material forms example at http://demo.viewflow.io/materialforms/registration/

    # semester choices
    cursor.execute(
        """SELECT DISTINCT(semester) FROM questions"""
    )
    sems = cursor.fetchall()
    semesters_choices = [(sem[0], sem[0]) for sem in sems]
    semesters = forms.MultipleChoiceField(
        label='',
        required=True,
        choices=semesters_choices,
        widget=forms.CheckboxSelectMultiple(
            attrs={'class': 'custom-checkbox-list'}),
        initial=(semesters_choices[0])
    )

    # question choices
    download_pref_choices = [('all_matches', 'Only questions that match across selected semesters'),
                             ('solo', 'Download one survey on its own')]
    download_pref = forms.ChoiceField(
        required=True,
        label='',
        widget=forms.RadioSelect(
            attrs={'class': 'custom-radio-list', 'required': True}),
        choices=download_pref_choices)

    # include metadata
    include_metadata = forms.ChoiceField(
        required=False,
        label='Yes',
        widget=forms.CheckboxInput()
    )

    layout = Layout(
        Fieldset('Select semester(s):', 'semesters'),
        Fieldset('Select Download Preference:', 'download_pref'),
        Fieldset('Include Student Survey Metadata?', 'include_metadata')
    )
