from django.shortcuts import render
import mysql.connector
import pandas as pd
from .forms import DataForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib import messages


# connect to MySQL Database

cnx = mysql.connector.connect(
    user=settings.DATABASES['qualtrics'].get('USER'),
    password=settings.DATABASES['qualtrics'].get('PASSWORD'),
    host=settings.DATABASES['qualtrics'].get('HOST'),
    port=settings.DATABASES['qualtrics'].get('PORT'),
    database=settings.DATABASES['qualtrics'].get('NAME'))
cursor = cnx.cursor()


def login(request):
    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            # correct username and password login the user
            auth.login(request, user)
            return get_home_template(request)
        else:
            messages.error(request, 'Error wrong username/password')

    return render(request, 'login.html')


def logout(request):
    auth.logout(request)
    return get_home_template(request)


def get_home_template(request):
    """Query database, render index.html with data."""
    # query database for available semesters
    context = {}
    context['form'] = DataForm()
    return render(request, 'home.html', context)


def generate_csv(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        form = DataForm(request.POST)
        # process data
        semesters = request.POST.getlist('semesters')
        download_pref = request.POST.get('download_pref')
        metadata = request.POST.get('include_metadata')

        return process_data(semesters, download_pref, metadata)

    else:
        form = DataForm()

    return render(request, 'base.html', {'form': form})


def get_dataframe_by_pref(semesters, download_pref):

    # how user wants to go download files
    if download_pref == 'solo':
        df = pd.read_sql("""SELECT q.qid, q.question_text, q.semester, sa.uniqname, sa.answer, s.subject_id 
                            FROM (questions q INNER JOIN survey_answers sa USING(qid) LEFT JOIN students s USING(uniqname))
                            WHERE(q.semester=%s AND sa.semester=%s) """, con=cnx, params=(semesters[0], semesters[0])).dropna()

    elif download_pref == "all_matches":
        if len(semesters) == 1:
            # only one semester selected
            query = """SELECT q.qid, q.question_text, q.semester, sa.uniqname, sa.answer, s.subject_id 
                        FROM (questions q INNER JOIN survey_answers sa 
                        ON(sa.qid=q.qid AND sa.semester=q.semester)
                        LEFT JOIN students s USING(uniqname))
                        WHERE(q.semester='{}' AND sa.semester='{}')""".format(semesters[0], semesters[0])
        else:
            # more than one semesters selected
            query = """SELECT q.qid, q.question_text, q.semester, sa.uniqname, sa.answer, s.subject_id 
                            FROM (questions q INNER JOIN survey_answers sa 
                            ON(sa.qid=q.qid AND sa.semester=q.semester)
                            LEFT JOIN students s USING(uniqname))
                            WHERE(q.semester IN{} AND sa.semester IN{})""".format(tuple(semesters), tuple(semesters))

        # run query
        df = pd.read_sql(query, con=cnx).dropna()

    pivot_df = df.pivot(index=['subject_id', 'semester'], columns=['qid'])
    return pivot_df


def update_dataframe_by_metadata(metadata, download_pref, semesters, pivot_df):
    if metadata:
        # Load second dataframe with survey metadata if specified to merge
        if download_pref == "all_matches":
            if len(semesters) == 1:
                # only one semester selected
                query = """SELECT * FROM survey_respondents sr
                                    LEFT JOIN students s
                                    ON(s.uniqname=sr.uniqname)
                                    WHERE(sr.semester='{}')""".format(semesters[0])
            else:
                # more than one semesters selected
                query = """SELECT * FROM survey_respondents sr
                                        LEFT JOIN students s
                                        ON(s.uniqname=sr.uniqname)
                                        WHERE(sr.semester IN{})""".format(tuple(semesters))
        else:
            query = """SELECT * FROM survey_respondents
                                    LEFT JOIN students
                                    USING(uniqname)
                                    WHERE(survey_respondents.semester='{}')""".format(semesters[0])

        df2 = pd.read_sql(query, con=cnx).set_index(
            ['subject_id', 'semester'])

        # Drop identifying columns
        df2 = df2.drop(['uniqname', 'RecipientLastName', 'RecipientFirstName',
                        'RecipientEmail', 'canvas_id', 'myla_id'], axis=1)

        # Merge answers df with metadata df
        pivot_df = pivot_df.merge(
            df2, how='left', left_index=True, right_index=True)

    return pivot_df


def process_data(semesters, download_pref, metadata_choice):

    metadata = 'on' == metadata_choice

    # get dataframe by download preferance
    # pivot the dataframe to make question numbers columns
    pivot_df = get_dataframe_by_pref(semesters, download_pref)

    # Find questions that are the same across semseters
    consistent_columns = {}
    for q in pivot_df['question_text'].columns:
        un = pivot_df['question_text'][q].dropna().unique()
        if download_pref == "all_matches":
            # Check if question is consistent across semesters and filter out question 39 (asks for student name)
            if len(un) == 1 and q != 39:
                consistent_columns[q] = un[0]
        else:
            if q != 39:
                consistent_columns[q] = un[0]
    # filter out columns found to be different
    pivot_df = pivot_df['answer'][list(consistent_columns.keys())]

    # reset index for appending a column and filtering out subject_id nans
    pivot_df = pivot_df.reset_index()

    # Add in dummy variables of 0 to row of questions so they will appear at the top
    consistent_columns['semester'] = 0
    consistent_columns['subject_id'] = 0
    # append question text to end of the dataframe
    pivot_df = pivot_df.append(consistent_columns, ignore_index=True)
    # drop rows without subject ids (not on rosters, need to find out why that is)
    pivot_df = pivot_df[pivot_df['subject_id'].notnull()]

    # reset index and sort so question text appears at the top
    pivot_df = pivot_df.set_index(
        ['subject_id', 'semester']).sort_index()

    # update the dataframe based on metadata choice
    pivot_df = update_dataframe_by_metadata(
        metadata, download_pref, semesters, pivot_df)

    # output csv file
    # construct download file name
    fname = "{}_survey_responses_ANONYMIZED.csv".format("_".join(semesters))
    fname = f'''metadata_{metadata}_{download_pref}_{fname}'''

    df = pivot_df.reset_index()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'''attachment; filename={fname}'''

    df.to_csv(path_or_buf=response, encoding="utf-8", index=False, sep=",")
    return response
