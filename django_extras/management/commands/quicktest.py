import sys
from optparse import make_option

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--failfast', action='store_true', dest='failfast', default=False,
            help='Tells Django to stop running the test suite after first failed test.'),
        make_option('--reuse_db', action='store_true', dest='reuse_db', default=False,
            help=('Tells Django to reuse the existing test database if it exists and not'
                  'to destroy it. Implies --noinput.')),
    )
    help = 'Runs the test suite for the specified applications, or the entire site if no apps are specified.'
    args = '[appname ...]'

    requires_model_validation = False

    def handle(self, *test_labels, **options):
        from django.conf import settings
        from django.test.utils import get_runner

        verbosity = int(options.get('verbosity', 1))
        interactive = options.get('interactive', True)
        failfast = options.get('failfast', False)
        reuse_db = options.get('reuse_db', False)

        settings.TEST_RUNNER = 'django_extras.test.keep_database.KeepDatabaseTestSuiteRunner'

        TestRunner = get_runner(settings)

        test_runner = TestRunner(verbosity=verbosity, interactive=interactive, failfast=failfast, reuse_db=reuse_db)
        failures = test_runner.run_tests(test_labels)

        if failures:
            sys.exit(bool(failures))
