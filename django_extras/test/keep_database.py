import sys

from django.conf import settings
from django.core.management import call_command
from django.db.backends.creation import TEST_DATABASE_PREFIX
from django.test.simple import DjangoTestSuiteRunner
try:
    from django.test.simple import dependency_ordered
except ImportError:
    from django_extras.django124.test.simple import dependency_ordered


class KeepDatabaseTestSuiteRunner(DjangoTestSuiteRunner):

    def setup_databases(self, **kwargs):
        '''
        Copied from Django 1.2.4 django.test.simple.DjangoTestSuiteRunner
        '''
        from django.db import connections, DEFAULT_DB_ALIAS

        # First pass -- work out which databases actually need to be created,
        # and which ones are test mirrors or duplicate entries in DATABASES
        mirrored_aliases = {}
        test_databases = {}
        dependencies = {}
        for alias in connections:
            connection = connections[alias]
            if connection.settings_dict['TEST_MIRROR']:
                # If the database is marked as a test mirror, save
                # the alias.
                mirrored_aliases[alias] = connection.settings_dict['TEST_MIRROR']
            else:
                # Store the (engine, name) pair. If we have two aliases
                # with the same pair, we only need to create the test database
                # once.
                test_databases.setdefault((
                        connection.settings_dict['HOST'],
                        connection.settings_dict['PORT'],
                        connection.settings_dict['ENGINE'],
                        connection.settings_dict['NAME'],
                    ), []).append(alias)

                if 'TEST_DEPENDENCIES' in connection.settings_dict:
                    dependencies[alias] = connection.settings_dict['TEST_DEPENDENCIES']
                else:
                    if alias != 'default':
                        dependencies[alias] = connection.settings_dict.get('TEST_DEPENDENCIES', ['default'])

        # Second pass -- actually create the databases.
        old_names = []
        mirrors = []
        for (host, port, engine, db_name), aliases in dependency_ordered(test_databases.items(), dependencies):
            # Actually create the database for the first connection
            connection = connections[aliases[0]]
            old_names.append((connection, db_name, True))
            test_db_name = connection.creation.create_test_db(self.verbosity, autoclobber=not self.interactive)
            for alias in aliases[1:]:
                connection = connections[alias]
                if db_name:
                    old_names.append((connection, db_name, False))
                    connection.settings_dict['NAME'] = test_db_name
                else:
                    # If settings_dict['NAME'] isn't defined, we have a backend where
                    # the name isn't important -- e.g., SQLite, which uses :memory:.
                    # Force create the database instead of assuming it's a duplicate.
                    old_names.append((connection, db_name, True))
                    connection.creation.create_test_db(self.verbosity, autoclobber=not self.interactive)

        for alias, mirror_alias in mirrored_aliases.items():
            mirrors.append((alias, connections[alias].settings_dict['NAME']))
            connections[alias].settings_dict['NAME'] = connections[mirror_alias].settings_dict['NAME']

        return old_names, mirrors

    def teardown_databases(self, old_config, **kwargs):
        '''
        Copied from Django 1.2.4 django.test.simple.DjangoTestSuiteRunner
        '''
        from django.db import connections
        old_names, mirrors = old_config
        # Point all the mirrors back to the originals
        for alias, old_name in mirrors:
            connections[alias].settings_dict['NAME'] = old_name
        # Destroy all the non-mirror databases
        for connection, old_name, destroy in old_names:
            if destroy:
                connection.creation.destroy_test_db(old_name, self.verbosity)
            else:
                connection.settings_dict['NAME'] = old_name

    def create_test_db(self, verbosity=1, autoclobber=False):
        """
        Copied from Django 1.2.4 django.db.backends.creation.BaseDatabaseCreation

        Creates a test database, prompting the user for confirmation if the
        database already exists. Returns the name of the test database created.
        """
        if verbosity >= 1:
            print "Creating test database '%s'..." % self.connection.alias

        test_database_name = self._create_test_db(verbosity, autoclobber)

        self.connection.close()
        self.connection.settings_dict["NAME"] = test_database_name
        can_rollback = self._rollback_works()
        self.connection.settings_dict["SUPPORTS_TRANSACTIONS"] = can_rollback

        call_command('syncdb', verbosity=verbosity, interactive=False, database=self.connection.alias)

        if settings.CACHE_BACKEND.startswith('db://'):
            from django.core.cache import parse_backend_uri, cache
            from django.db import router
            if router.allow_syncdb(self.connection.alias, cache.cache_model_class):
                _, cache_name, _ = parse_backend_uri(settings.CACHE_BACKEND)
                call_command('createcachetable', cache_name, database=self.connection.alias)

        # Get a cursor (even though we don't need one yet). This has
        # the side effect of initializing the test database.
        cursor = self.connection.cursor()

        return test_database_name

    def _create_test_db(self, verbosity, autoclobber):
        """
        Copied from Django 1.2.4 django.db.backends.creation.BaseDatabaseCreation

        Internal implementation - creates the test db tables.
        """
        suffix = self.sql_table_creation_suffix()

        if self.connection.settings_dict['TEST_NAME']:
            test_database_name = self.connection.settings_dict['TEST_NAME']
        else:
            test_database_name = TEST_DATABASE_PREFIX + self.connection.settings_dict['NAME']

        qn = self.connection.ops.quote_name

        # Create the test database and connect to it. We need to autocommit
        # if the database supports it because PostgreSQL doesn't allow
        # CREATE/DROP DATABASE statements within transactions.
        cursor = self.connection.cursor()
        self.set_autocommit()
        try:
            cursor.execute("CREATE DATABASE %s %s" % (qn(test_database_name), suffix))
        except Exception, e:
            sys.stderr.write("Got an error creating the test database: %s\n" % e)
            if not autoclobber:
                confirm = raw_input("Type 'yes' if you would like to try deleting the test database '%s', or 'no' to cancel: " % test_database_name)
            if autoclobber or confirm == 'yes':
                try:
                    if verbosity >= 1:
                        print "Destroying old test database..."
                    cursor.execute("DROP DATABASE %s" % qn(test_database_name))
                    if verbosity >= 1:
                        print "Creating test database..."
                    cursor.execute("CREATE DATABASE %s %s" % (qn(test_database_name), suffix))
                except Exception, e:
                    sys.stderr.write("Got an error recreating the test database: %s\n" % e)
                    sys.exit(2)
            else:
                print "Tests cancelled."
                sys.exit(1)

        return test_database_name
