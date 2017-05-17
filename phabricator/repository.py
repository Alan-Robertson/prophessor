import os
import subprocess
from .api import api_call
from database import db

repository_policy_update_sql = """UPDATE default_repository.repository
    SET viewPolicy = %s,editPolicy = %s,pushPolicy = %s
    WHERE callsign = %s"""

repository_hosted_select_sql = """SELECT details
    FROM default_repository.repository
    WHERE callsign = %s"""

repository_hosted_update_sql = """UPDATE default_repository.repository
    SET details = %s
    WHERE callsign = %s"""

class Repository():
    def create(self, name, callsign, uri, vcs="git"):
        """
        Creates a Phab Repository with the given name and callsign.
        :param name: The name of the repository.
        :param callsign: The callsign of the repository (unique).
        :return: The result from the api call.
        """
        result = api_call.template("create_repository", (name, callsign, uri, vcs))

        # Complete creation of the repository (API does not handle this part).
        # Move the repository files to the appropriate location.
        repo_dir = os.path.join("/var/repo/", callsign)
        example_repo = os.path.join(os.getcwd(), "example_files/example_repo/")
        p1 = subprocess.Popen("cp -r %s %s" % (example_repo, repo_dir,), shell=True)
        p1.wait()

        # Include the repo's callsign in the repository files.
        file_to_change = os.path.join(repo_dir, "hooks/pre-receive")
        p2 = subprocess.Popen("sed -i 's/CALLSIGN/%s/' %s" % (callsign, file_to_change,), shell=True)
        p2.wait()

        return result

    def set_repository_policy(self, callsign, view_policy, edit_policy, push_policy):
        connection = db.connect()

        with connection.cursor() as cursor:
            cursor.execute(repository_policy_update_sql, (view_policy, edit_policy, push_policy, callsign))

        db.commit(connection)
        db.disconnect(connection)

    def get_repository_phab_hosted(self, callsign):
        connection = db.connect()

        with connection.cursor() as cursor:
            cursor.execute(repository_hosted_select_sql, (callsign,))

            # Should only return one row.
            result = []
            for row in cursor:
                result = row['details']

        db.disconnect(connection)

        return result

    def set_repository_phab_hosted(self, details, callsign):
        connection = db.connect()

        with connection.cursor() as cursor:
            cursor.execute(repository_hosted_update_sql, (details, callsign))

        db.commit(connection)
        db.disconnect(connection)

    def clone_base_repo(self, base_repo, name, email):
        """
        Clones the given base repository, makes an initial commit, and add a
        sample 'origin' remote.
        :param base_repo: URL to the base repository.
        :param name: The desired name to appear in the initial commit.
        :param email: The desired email to appear in the initial commit.
        :return: None.
        """

        commands = ['git clone %s base_repo' % (base_repo,),
                    'cd base_repo',
                    'rm -rf .git/',
                    'git init',
                    'git add *',
                    'git config user.name "%s"' % (name,),
                    'git config user.email "%s"' % (email,),
                    'git commit -m "Initial Commit."',
                    'git remote add origin https://sample_remote',
                    'git config --global credential.helper cache']

        p1 = subprocess.Popen(' && ',join(commands), shell=True)
        p1.wait()


    def push_to_repo(self, uri):
        """
        Pushes the base repository to the given uri repository.
        :param uri: The uri of the group repository.
        :return: None.
        """

        commands = ['git remote set-url origin %s' % (uri,),
                    'git push --quiet origin master']

        p1 = subprocess.Popen(' && '.join(commands), shell=True)
        p1.wait()


repository = Repository()
