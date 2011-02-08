quicktest / KeepDatabaseTestSuiteRunner

KeepDatabaseTestSuiteRunner is a test runner that optionally reuses the test
database instead of destroying and recreating it.

quicktest is a Django management command to use KeepDatabaseTestSuiteRunner

Install:

    pip install https://github.com/saltycrane/django-extras/tarball/master

Edit settings.py:

    INSTALLED_APPS += (
        'django_extras',
    )

Usage:

    python manage.py quicktest --reuse_db [app_label]

Compatibility:

 - Based on Django 1.2.4
 - Tested with Django 1.2.3
 - Does not work with Django 1.3

Original quicktest.py and keep_database.py by Eric Holscher: <https://github.com/ericholscher/django-test-utils>

Differences from django-test-utils:

 - Support for multiple databases
 - This method sucks more (it is less maintainable) than the method used by django-test-utils
