import gitlab  # pip install python-gitlab
import os
from log_config import logger

BRANCH = "develop"
SINCE_DATE = "2023-06-09 15:00"
UNTIL_DATE = "2023-06-14 14:00"


# class Repos with a constructor that take two parameters : gitlab server and private token
class Repos:
    def __init__(self, gitlab_server=None, private_token=None):
        self.logger = logger

        if gitlab_server is None:
            # read env variable
            # export GITLAB_SERVER=https://gitlab.euclid-sgs.uk
            gitlab_server = os.environ.get("GITLAB_SERVER")
            self.logger.debug("gitlab server: " + gitlab_server)

        if private_token is None:
            # export GITLAB_TOKEN=glpat-2FeEZidzsSatS99zw41d
            private_token = os.environ.get("GITLAB_TOKEN")
            self.logger.debug("private_token: " + private_token)

        self.gitlab_server = gitlab_server
        self.private_token = private_token

        # check the acces gl is False if wrong acces
        self.gl = self.check_acces_token()

    # method that print the object

    def __str__(self):
        return "gitlab_server: " + self.gitlab_server + "\nprivate_token: " + self.private_token

    # function that check the acces of a gitlab server is ok with two parameters : gitlab server and private token only
    # if the acces is ok return the gitlab object else return false

    def check_acces_token(self):
        # try to connect to the gitlab server
        try:
            # connect to the gitlab server
            gl = gitlab.Gitlab(self.gitlab_server, private_token=self.private_token)
            # get the gitlab server version using the gitlab object
            version = gl.version()[0]

            # print the gitlab server version
            self.logger.debug("Gitlab server version: " + version)
            # return the gitlab object
            return gl
        # if the acces is not ok
        except Exception as err:
            self.logger.critical(f"Unexpected {err=}, {type(err)=}")
            # return false
            return False

    # function that get the group repos with two parameters : gitlab object and group name
    def get_groups_with_path_with_namespace(self, group: str):
        groups = []
        # get the group repos
        group_repos = self.gl.groups.get(group).projects.list(all=True)
        # print the group repos
        self.logger.debug("Group repos: ")
        for repo in group_repos:
            self.logger.debug(repo.name)
            groups.append(repo.path_with_namespace)
        # return the group repos
        return groups

    # function that returns the of modifications done on the files in a project withese parameters : gitlab object, project, file path, branch name, since date
    def get_modifications_by_file(
        self, project, branch_name: str = BRANCH, period_list: list = [SINCE_DATE, UNTIL_DATE, False]      
    ):
        modifications_by_file = {}
        # get the file commits
        if project.path == "empty":
            return modifications_by_file

        start = period_list[0]
        end = period_list[1]
        tag = period_list[2] # True or False
                    
        try:
            if not tag:
                # file_commits = project.commits.list(ref_name=branch_name, since=since_date,all=True)
                file_commits = project.commits.list(ref_name=branch_name, since=start, until=end, all=True)

            else:
                for tag_in_list in period_list[0:1]:
                    try:
                        tag_x = project.tags.get(tag_in_list)
                        # Process the tag if found
                    except gitlab.GitlabGetError as e:
                        if e.response_code == 404:
                            self.logger.warning(f"Tag '{tag_in_list}' not found.")
                            return modifications_by_file
                        else:
                            raise  # Re-raise the exception if it's not a 404 error

                tag_1 = project.tags.get(start)
                tag_2 = project.tags.get(end)

                file_commits = project.commits.list(ref_name=branch_name, since=tag_1.commit["created_at"], until=tag_2.commit["created_at"], all=True)

        except Exception as err:
            self.logger.critical(f"Unexpected {err=}, {type(err)=}")
            self.logger.critical(f"project.path={project.path}, branch_name={branch_name}")
            self.logger.critical(f"start={start}, end={end}")
            return modifications_by_file

        # print the file commits
        self.logger.debug(
            "Getting the commits in the "
            + branch_name
            + " branch since "
            + start
            + " until "
            + end
            + "of the project "
            + project.path
        )


        for commit in file_commits:
            # self.logger.info(commit.title)
            diff = commit.diff(all=True)
            for d in diff:
                file_path = d["new_path"]
                # self.logger.info(d["new_path"])
                # self.logger.info(d["diff"])
                if file_path not in modifications_by_file:
                    modifications_by_file[file_path] = []
                    modifications_by_file[file_path].append(
                        [d["diff"], commit.title, commit.author_name, commit.created_at, commit.id]
                    )
                elif d["diff"] not in modifications_by_file[file_path][0]:
                    modifications_by_file[file_path].append(
                        [d["diff"], commit.title, commit.author_name, commit.created_at, commit.id]
                    )

        # return of file commits
        return modifications_by_file

    # function that get all the files of a gitlab project with two parameters : gitlab object and project name
    def list_files_in_subdirectories(self, project, file_path='', branch_name: str = BRANCH):
        table = []
        row_names = ["Path/Name", "Modifications"]
        # List all files in the specified directory
        files = project.repository_tree(path=file_path, ref=branch_name, recursive=True, all=True)

        # Print the name of each file
        for file in files:
            if file['type'] == 'blob':
                # Print the file name and its modification count
                table.append([file['path'], 0])
                # table.append([file_path, modification_count])
        return table, row_names

    def print_project_files(
        self, project: str, branch_name: str = BRANCH, period_list: list = [SINCE_DATE, UNTIL_DATE, False]
    ):
        # Recursively list all files in the subdirectories
        project = self.gl.projects.get(project)

        modifications_by_file = self.get_modifications_by_file(
            project, branch_name=branch_name, period_list=period_list
        )
        # transform modifications_by_file to table
        table = []
        row_names = ["Path/Name", "Modifications"]
        for file_path, modifications in modifications_by_file.items():
            cell_text = "{{collapse(" + str(len(modifications)) + ")"
            # commit.title,commit.author_name,commit.created_at,commit.id])
            for modification in modifications:
                cell_text += "\n+*Title:*+ " + modification[1] + "\n"
                cell_text += "\n+*Author:*+ " + modification[2] + "\n"
                cell_text += "\n+*Creation date:*+ " + str(modification[3]) + "\n"
                cell_text += "\n+*Commit ID:*+ " + str(modification[4]) + "\n"
                cell_text += "\n+*Differences:*+ <pre>" + str(modification[0]) + "</pre>\n\n"

            cell_text = cell_text + "\n}}\n"
            table.append([file_path, cell_text])
            # table.append([file_path, modification_count])

        # table,row_names = self.list_files_in_subdirectories(project, file_path='',branch_name=branch_name)
        return table, row_names
