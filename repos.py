import gitlab  # pip install python-gitlab
import os
from log_config import logger
from datetime import datetime
from gitlab.exceptions import GitlabGetError

BRANCH = "develop"
SINCE_DATE = "2023-06-09 15:00"
UNTIL_DATE = "2023-06-14 14:00"


def is_valid_datetime(input_str):
# Test cases
# date_time_str1 = "2023-08-21 15:30"
# date_time_str2 = "2023-08-21 25:30"  # Invalid hour
# date_time_str3 = "2023-08-21"        # Missing time part
    if not input_str:
        return False
    try:
        datetime.strptime(input_str, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False
    
def is_tag(input_str):
    return not is_valid_datetime(input_str)    

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

    def check_project_exists(self,project_path):
        try:
            project = self.gl.projects.get(project_path)
            return True
        except GitlabGetError:
            return False

    # function that get the group repos with two parameters : gitlab object and group name
    def get_projects_with_path_with_namespace(self, group: str):
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

    def select_modifications(self,modifications: dict,filename_contain:list) -> dict:

        selected_modifications = {}
        for file_path, items in modifications.items():
            short_filename = os.path.basename(file_path)
            # [d["diff"], commit.title, commit.author_name, commit.created_at, commit.id]
            for string in filename_contain:
                if string in file_path:
                    selected_modifications[file_path] = items
                    break


        return selected_modifications



    # function that returns the of modifications done on the files in a project withese parameters : gitlab object, project, file path, branch name, since date
    def get_modifications_by_file(self, gitlab_project_name:str, branch_name: str, period:dict):
        project = self.gl.projects.get(gitlab_project_name)
        modifications_by_file = {}
        
        # get the file commits
        if project.path == "empty":
            return modifications_by_file

        start_date = period['start date']
        end_date = period['end date']
        start_tag = period['start tag']
        end_tag = period['end tag'] 
        use_tag = period['use_tag']

        # return empty dict if no period of time or no tags
        if not use_tag:
            if not start_date or not end_date:
                return modifications_by_file
        else:
            if not start_tag or not end_tag:
                return modifications_by_file
                    
        try:
            if not use_tag:
                # file_commits = project.commits.list(ref_name=branch_name, since=since_date,all=True)
                file_commits = project.commits.list(ref_name=branch_name, since=start_date, until=end_date, all=True)
            else:
                for tag_in_list in [start_tag,end_tag]:
                    try:
                        tag_x = project.tags.get(tag_in_list)
                        # Process the tag if found
                    except gitlab.GitlabGetError as e:
                        if e.response_code == 404:
                            self.logger.warning(f"Tag '{tag_in_list}' not found.")
                            return modifications_by_file
                        else:
                            raise  # Re-raise the exception if it's not a 404 error

                tag_1 = project.tags.get(start_tag)
                tag_2 = project.tags.get(end_tag)

                file_commits = project.commits.list(ref_name=branch_name, since=tag_1.commit["created_at"], until=tag_2.commit["created_at"], all=True)

        except Exception as err:
            self.logger.critical(f"Unexpected {err=}, {type(err)=}")
            self.logger.critical(f"project.path={project.path}, branch_name={branch_name}")
            return modifications_by_file

        # print the file commits

        for commit in file_commits:
            # self.logger.info(commit.title)
            try:
                diff = commit.diff(all=True)
            except Exception as err:
                self.logger.critical(f"Unexpected {err=}, {type(err)=}")
                self.logger.critical(f"project.path={project.path}, branch_name={branch_name}")
                return modifications_by_file
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

    def get_tags(self, gitlab_project_name:str) -> list:

        tag_full_list=[]
        latest_tag = ""
        before_latest_tag = ""

        project = self.gl.projects.get(gitlab_project_name)

        try:
            tags = project.tags.list(get_all=True)
        except Exception as err:
            self.logger.critical(f"Unexpected {err=}, {type(err)=}")
            return [tag_full_list,latest_tag, before_latest_tag]    
        
        logger.debug(f"tags of the project ={tags} in " + project.name)
        for tag in tags:
            commit = tag.commit
            # get the creation date of the tag
            created_at = commit['created_at'] if commit else "N/A"
            author_name = commit['author_name'] if commit else "N/A"

            tag_full_list.append({'name':tag.name,'created_at':created_at,'author_name':author_name})
        tag_full_list.sort(key=lambda x: x['created_at'])
        tag_short_list = [tag['name'] for tag in tag_full_list]

        if tag_full_list:
            latest_tag = tag_full_list[-1]
            latest_tag = latest_tag['name']
            if len(tag_full_list) >= 2:
                before_latest_tag = tag_full_list[-2]
                before_latest_tag = before_latest_tag['name']
            else:
                logger.warning(f"only one tag in " + project.name)
        else:
            logger.warning(f"no tag in " + project.name)

        logger.debug(f"tag_short_list= {tag_short_list}, latest_tag ={latest_tag} and before_latest_tag={before_latest_tag} in " + project.name)
        return [tag_full_list,latest_tag, before_latest_tag]
    

    def get_tags_in_period(self,tag_full_list:list, period:list)-> list :

        tags_in_period = []
        # reminder: prefix the tag name with "> " when the start or end date is after the tag creation
        start_tag = period['start tag'].replace("> ","")
        end_tag = period['end tag'].replace("> ","")

        in_the_period = False
        for tag in tag_full_list:
            if tag['name'] == start_tag:
                in_the_period = True
            if in_the_period:
                tags_in_period.append(tag)
            if tag['name'] == end_tag:
                in_the_period = False

        logger.debug(f"Tags in the period = {tags_in_period}")
        return tags_in_period

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
    

    def complete_the_period_of_the_project(self, project_name:str, project_items:dict,tag_full_list:list,latest_tag:str, before_latest_tag:str) -> dict:
            
        period = {}            
        tag_short_list = [tag['name'] for tag in tag_full_list]

        # check if start and end are dates
        if not is_tag(project_items['start date']):
            period['use_tag'] = False
            period['start date'] = project_items['start date']
            period['end date'] = project_items['end date']
            period['start tag'] = "-"
            period['end tag'] = "-"

            # let's identity the tag names that correspond to the start and end dates
            # WARNING: prefix the tag name with "> " when the start or end date is after the tag creation
            for tag in tag_full_list:
                if tag['created_at'] <= project_items['start date']:
                    period['start tag'] = "> " + tag['name']
                if tag['created_at'] <= project_items['end date']:
                    period['end tag'] = "> " + tag['name']

        else:
            period['use_tag'] = True
            start = project_items['start tag'] 
            end = project_items['end tag'] 

            # start and end are empty or are tag names
            if not start and not end:
                start = before_latest_tag
                end = latest_tag

            if not start and end:
                # look for the tag before the 'end' tag
                start = end
                previous_tag = ""
                for tag in tag_short_list:
                    if tag == end:
                        start = previous_tag
                        break
                    previous_tag = tag
            #check if start is not in the dictionary tag_list and raise an error if it is the case

            if len(tag_short_list) <2:
                start =  ""
                end = ""

            if len(tag_short_list) >= 2 and start not in tag_short_list:
                logger.warning(f"Tag '{start}' does not exist in the project '{project_name}'")
                #raise ValueError(f"Tag '{start}' does not exist in the project '{project_name}'")
                start = ""
            if len(tag_short_list) >= 2 and end not in tag_short_list:
                logger.critical(f"Tag '{end}' does not exist in the project '{project_name}'")
                #raise ValueError(f"Tag '{end}' does not exist in the project '{project_name}'")
                end = ""

            period['start tag'] = start
            period['end tag'] = end
            # let's identity the dates that correspond to the start and end tags
            period['start date'] = "-"
            period['end date'] = "-"
            for tag in tag_full_list:
                if start == tag['name']:                    
                    parsed_date = datetime.strptime(tag['created_at'], "%Y-%m-%dT%H:%M:%S.%f%z")
                    period['start date'] = parsed_date.strftime("%Y-%m-%dT%H:%M:%S")

                if end == tag['name']:
                    parsed_date = datetime.strptime(tag['created_at'], "%Y-%m-%dT%H:%M:%S.%f%z")
                    period['end date'] = parsed_date.strftime("%Y-%m-%dT%H:%M:%S")

        return period 
