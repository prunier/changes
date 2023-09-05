# import the redmine library
# pip install python-redmine
from redminelib import Redmine
from log_config import logger
import os
import common

REDMINE_PROJECT = "maturity-assessment"
PARENT_WIKI_PAGE = "Changes"
TOP_PARENT_WIKI_PAGE = "Files_modified_in_projects"


# class taht manage redmine wiki pages
class Wiki_pages_with_Redmine:
    def __init__(self, redmine_server=None, private_token=None, project_name=REDMINE_PROJECT):
        self.logger = logger

        if redmine_server is None:
            # export REDMINE_SERVER=https://euclid.roe.ac.uk
            redmine_server = os.environ.get("REDMINE_SERVER")
            self.logger.debug("redmine server: " + redmine_server)
        if private_token is None:
            # export REDMINE_TOKEN=c37b998606c4baa6f4aa6e93336ebe1bca12b052
            private_token = os.environ.get("REDMINE_TOKEN")
            self.logger.debug("private_token: " + private_token)

        self.redmine_server = redmine_server
        self.private_token = private_token
        self.project_name = project_name

        # check the acces gl is False if wrong acces
        self.redmine = self.check_acces_token()

    # method that print the object

    def __str__(self):
        return (
            "redmine_server: "
            + self.redmine_server
            + "\nprivate_token: "
            + self.private_token
            + "\nproject_name: "
            + self.project_name
        )

    # function that check the acces of a redmine server with the parameters redmine server address, private token
    # if the acces is ok return the redmine object else return false
    def check_acces_token(self):
        # try connect to the redmine server
        try:
            # Create a Redmine object using the provided URL and API key
            redmine = Redmine(self.redmine_server, key=self.private_token)

            # return the redmine object
            return redmine
        except Exception as err:
            self.logger.critical(f"Unexpected {err=}, {type(err)=}")
            # return false
            return False

    # function that get the project wiki pages with two parameters : redmine object and project name
    def get_project_wiki_pages(self):
        # Get the project by its identifier or name
        project = self.redmine.project.get(self.project_name)
        # redmine.project.get('project_identifier')

        # Get the list of all wiki pages for the project
        wiki_pages = project.wiki_pages

        # Print the titles of the wiki pages
        for wiki_page in wiki_pages:
            self.logger.debug(wiki_page.title)

    # function that check id a redmine wiki page exist with three parameters : redmine object, project name and wiki page name
    # if the wiki page exist return true else return false
    def check_wiki_page_exist(self, delete_if_exists: bool, wiki_page_name: str):
        # Get the project by its identifier or name
        project = self.redmine.project.get(self.project_name)  # redmine.project.get('project_identifier')

        # Get the list of all wiki pages for the project
        wiki_pages = project.wiki_pages

        # Print the titles of the wiki pages
        for wiki_page in wiki_pages:
            # self.logger.info(wiki_page.title)

            if wiki_page_name.lower() == wiki_page.title.lower():
                # delete the wiki page
                # return true if the wiki page exist else return false

                if delete_if_exists:
                    wiki_page.delete()
                    return False

                else:
                    return wiki_page

        return False

    def create_wiki_page(
        self,
        wiki_page_name: str,
        wiki_page_content: str,
        wiki_page_parent: str,
        wiki_page_comments: str,
        wiki_page_notify: bool,
    ):
        # Get the project by its identifier or name
        project = self.redmine.project.get(self.project_name)  # redmine.project.get('project_identifier')

        # Create a new wiki page
        try:
            wiki_page = self.redmine.wiki_page.create(
                project_id=project.id,
                title=wiki_page_name,
                text=wiki_page_content,
                parent_title=wiki_page_parent,
                comments=wiki_page_comments,
                notify=wiki_page_notify,
            )
        except Exception as err:
            self.logger.critical(f"Unexpected {err=}, {type(err)=}")
            return False        

        return wiki_page

    # function that print a table in a wiki page with four parameters : redmine object, project name, wiki page name and table name
    # if the wiki page is created return true else return false

    # function that print a list of data with these parameters : list of data and row names
    def print_data_table(self, data_list, row_names,flag_add_line=True):
        # Print header
        text = "\n{background:gold}. |_. " + " |_. ".join(row_names) + "|\n" if row_names else ""
        width_table = str(len(row_names))

        # Print data rows
        previous_cell_col1 = ""
        for i, row in enumerate(data_list):
            if flag_add_line and i > 0 and row[0] != previous_cell_col1:
                text += "|\\" + width_table + "{background:lightgrey}. |\n"
            previous_cell_col1 = row[0]
            text += f"| " + " |".join(str(cell) for cell in row) + "|\n"

        return text

    def create_table_in_a_new_wiki_page(
        self, wiki_page_name: str, parent_wiki_page: str, wiki_page_header: str, data: list, row_names: list,flag_add_line=True):
        # Example data and row names
        # data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        # row_names = ["Row 1", "Row 2", "Row 3"]

        # Call the function to print the data table
        wiki_page_content = wiki_page_header + self.print_data_table(data, row_names,flag_add_line)

        # check if the wiki page exist and delete it if exist
        wiki_page_exist = self.check_wiki_page_exist(
            delete_if_exists=True,
            wiki_page_name=wiki_page_name,
        )

        if not wiki_page_exist:
            self.logger.debug(f"wiki page {wiki_page_name} will be created")
            wiki_page = self.create_wiki_page(
                wiki_page_name,
                wiki_page_content,
                wiki_page_parent=parent_wiki_page,
                wiki_page_comments="script",
                wiki_page_notify=False,
            )
            self.logger.info(f"wiki page {wiki_page_name} created")

        # if the acces is not ok
        else:
            self.logger.critical("Acces not ok")

        # return true if the wiki page is created else return false
        return wiki_page
    
    def add_file_in_wiki_page_object(self,wiki_page_object,file_paths:list,header_line="{{>toc}}",width_image="width:800px"):

       if wiki_page_object:
            self.logger.debug(f"wiki page {wiki_page_object.title} will be updated")
            try:
                paths = []
                info_image = ""
                for file_path in file_paths:
                    filename = os.path.basename(file_path)
                    paths.append({'path': file_path, 'filename': filename})
                    if ".png" in filename:
                        info_image +="\n!{"+ width_image + "}" + f"{filename}!"
                wiki_page_object.uploads = paths
                previous_contents = wiki_page_object.text
                previous_contents = previous_contents.replace(header_line,f"{header_line}\n\n{info_image}\n\n")
                wiki_page_object.text = previous_contents + "\n\nupdated on " + str(common.CURRENT_DATE) + "\n"

                wiki_page_object.save()
            except Exception as err:
                self.logger.critical(f"Unexpected {err=}, {type(err)=}")
                return False
            
            self.logger.info("Wiki page " + wiki_page_object.title + " updated")
    
    

    # function that print a list of data with these parameters : list of data and row names


    def add_table_in_wiki_page(self, wiki_page_object, wiki_page_header: str, data: list, row_names: list,flag_add_line=True):
        wiki_page_content = wiki_page_header + self.print_data_table(data, row_names,flag_add_line)

        # update the existing wiki page and add the table inside
        if wiki_page_object:
            self.logger.debug(f"wiki page {wiki_page_object.title} will be updated")
            wiki_page_object.text += wiki_page_content
            try:
                wiki_page_object.save()
            except Exception as err:
                self.logger.critical(f"Unexpected {err=}, {type(err)=}")
                return False
            
            self.logger.info("Wiki page " + wiki_page_object.title + " updated")

        # if the acces is not ok
        else:
            self.logger.critical("Acces not ok")

        # return true if the wiki page is created else return false
        return wiki_page_object

    def delete_wiki_pages(
        self,
        wiki_project_name: str,
        wiki_page_name_with_string: str,
        delete: bool = False,
    ):
        # Get the project by its identifier or name
        project = self.redmine.project.get(self.project_name)  # redmine.project.get('project_identifier')

        # Get the list of all wiki pages for the project
        wiki_pages = project.wiki_pages
        for wiki_page in wiki_pages:
            if wiki_page.title.lower().startswith(wiki_page_name_with_string.lower()):
                if delete:
                    # delete the wiki page
                    wiki_page.delete()
                    self.logger.info(f"Wiki page {wiki_page.title} deleted")
                else:
                    self.logger.info(f"Wiki page {wiki_page.title} exists")
