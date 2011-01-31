quicktest / KeepDatabaseTestSuiteRunner

KeepDatabaseTestSuiteRunner is a test runner that optionally reuses the test
database instead of destroying and recreating it.

quicktest is a Django management command to use KeepDatabaseTestSuiteRunner

Usage:

    python manage.py quicktest --reuse_db [app_label]

Based on Django 1.2.4
Tested with Django 1.2.3

Original quicktest.py and keep_database.py by Eric Holscher: https://github.com/ericholscher/django-test-utils
