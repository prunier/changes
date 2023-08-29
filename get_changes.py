import argparse
import pprint
import yaml

from tabulate import tabulate
from log_config import logger

from repos import Repos
from wiki import RedmineWikiPages

from wiki import PARENT_WIKI_PAGE
from wiki import REDMINE_PROJECT
from wiki import TOP_PARENT_WIKI_PAGE



def parse_arguments(args):
    arguments = iter(args)
    result = []

    for arg in arguments:
        if arg in ("-p", "--project"):
            item = {"type": "project", "name": next(arguments), "start": None, "end": None}
            result.append(item)
        elif arg in ("-g", "--group"):
            item = {"type": "group", "name": next(arguments), "start": None, "end": None}
            result.append(item)
        elif arg in ("-l", "--level"):
            item = {"type": "level", "name": next(arguments), "start": None, "end": None}
            result.append(item)
        elif arg in ("-s", "--start"):
            item["start"] = next(arguments)
        elif arg in ("-e", "--end"):
            item["end"] = next(arguments)

    return result

def load_SGS_gitlab_groups(input_yaml_file: str) -> dict:
    with open(input_yaml_file, "r") as f:
        SGS_gitlab_groups = yaml.safe_load(f.read())

    # Create a PrettyPrinter
    pp = pprint.PrettyPrinter(indent=2)

    # Use the pretty-printer to format the dictionary
    formatted_dict = pp.pformat(SGS_gitlab_groups)

    # Log the formatted dictionary
    logger.debug("Formatted dictionary:\n%s", formatted_dict)

    return SGS_gitlab_groups


    # loop over the projects belonging to the level specified in the input arguments
def get_gitlab_projects(parsed_arguments,repo, SGS_gitlab_groups):

    gitlab_projects_selected = []

    for item in parsed_arguments:
        if item["type"] == "level":
            level_name = item["name"]
            logger.info(f"Selecting projects for the level '{level_name}'")
            if level_name in SGS_gitlab_groups.keys():
                    element = SGS_gitlab_groups[level_name]
                    level_long_name = element['name']
                    gitlab_groups_of_the_level = element["gitlab_groups"]
                    for gitlab_long_name,gitlab_group in gitlab_groups_of_the_level.items():
                        logger.info(f"Selecting projects for the gitlab group '{gitlab_group}'")
                        # get the gitlab projects in the level
                        gitlab_projects = repo.get_projects_with_path_with_namespace(group=gitlab_group)
                        for gitlab_project in gitlab_projects:
                            dict1 = {'name': gitlab_project,'level':level_name,'group':gitlab_group,'start':item['start'],'end':item['end']}
                            gitlab_projects_selected.append(dict1)

        if item["type"] == "group":
            gitlab_group = item["name"]
            logger.info(f"Selecting projects in the group  '{gitlab_group}'")
            # get the gitlab projects in the group
            gitlab_projects = repo.get_projects_with_path_with_namespace(group=gitlab_group)
            for gitlab_project in gitlab_projects:
                # check if gitlab_project exist in the list of dictionaries gitlab_projects_selected
                if any(d['name'] == gitlab_project for d in gitlab_projects_selected):
                    # delete the dictionary with the same name
                    gitlab_projects_selected = [d for d in gitlab_projects_selected if d.get('name') != gitlab_project]
                    # get the name of the level of the project
                    logger.warning(f"Project '{gitlab_project}' already selected. Deleting it from the list.")
                dict1 = {'name': gitlab_project,'level':None,'group':gitlab_group,'start':item['start'],'end':item['end']}
                gitlab_projects_selected.append(dict1)

        if item["type"] == "project":
            gitlab_project = item["name"]
            gitlab_group = gitlab_project.split("/")[0] # PF-LE1/LE1_VIS" -> group is PF-LE1
            logger.info(f"Selecting project  '{gitlab_project}'")
            # get the gitlab projects in the group
            if repo.check_project_exists(gitlab_project):
                logger.debug(f"Project '{gitlab_project}' exists.")
                # check if gitlab_project exist in the list of dictionaries gitlab_projects_selected
                if any(d['name'] == gitlab_project for d in gitlab_projects_selected):
                    # delete the dictionary with the same name
                    gitlab_projects_selected = [d for d in gitlab_projects_selected if d.get('name') != gitlab_project]
                    logger.warning(f"Project '{gitlab_project}' already selected. Deleting it from the list.")
                dict1 = {'name': gitlab_project,'level':None,'group':gitlab_group,'start':item['start'],'end':item['end']}
                gitlab_projects_selected.append(dict1)

            else:
                logger.error(f"Gitlab project '{gitlab_project}' does not exist.")

    count_of_selected_projects = len(gitlab_projects_selected)
    logger.info(f"{count_of_selected_projects} selected projects")  
    return gitlab_projects_selected

def print_in_console_the_gitlab_projects_selected(gitlab_projects_selected):

    if len(gitlab_projects_selected) == 0:
        return

    # pretty print of the list of projects gitlab_projects_selected
    table = []
    headers = ['Level','Group','Project Name', 'Start Date', 'End Date']

    for item in gitlab_projects_selected:
        if 'count_files_modified' in item:
            #modifications_by_file = item['modifications_by_file']
            #for file in modifications_by_file:
            #    table.append(['', '', file['file_path'], file['start'], file['end']])
            table.append([item['level'],item['group'], item['name'], item['start'], item['end'],item['count_files_modified']])
        else:
            table.append([item['level'],item['group'], item['name'], item['start'], item['end']])



    if 'count_files_modified' in gitlab_projects_selected[0]:
        headers.append('count of files modified')

    table_str = tabulate(table, headers, tablefmt='simple') # grid, simple, plain, pipe, orgtbl, rst, mediawiki, html, latex, latex_raw, latex_booktabs, tsv

    print(table_str)

def print_in_console_the_modifications_in_the_selected_gitlab_projects(gitlab_projects_selected):

    # pretty print of the list of projects gitlab_projects_selected
    headers = ['file','Author name','Created_= at']

    for item in gitlab_projects_selected:
        print("=" * 100)
        print("Level = "+str(item['level'])+" Group = " + str(item['group']) + " Project = " + item['name'] + " Start = " + item['start'] + " End = "+ item['end'])
        print()
        table = []

        if 'count_files_modified' in item and item['count_files_modified'] != '0':
            modifications_by_file = item['modifications_by_file']
            for file,modifications in modifications_by_file.items():
                for m in modifications:
                    table.append([file,m[2],m[3]]) # m[4] = Id, m[1] = Title
        
            table_str = tabulate(table, headers, tablefmt='simple')
            print(table_str)

def print_the_modifications_in_the_selected_gitlab_group(wiki,gitlab_projects_selected):

    logger.info(f"--------------------print in wiki page--------------------------------")

    for item in gitlab_projects_selected:
        print("=" * 100)
        print("Level = "+str(item['level'])+" Group = " + str(item['group']) + " Project = " + item['name'] + " Start = " + item['start'] + " End = "+ item['end'])
        print()


def main(args):
    parser = argparse.ArgumentParser(description="Example script with subarguments")

    parsed_arguments = parse_arguments(args)

    for item in parsed_arguments:
        if item["type"] == "project":
            logger.debug(f"Setting times or tags for project '{item['name']}': Start: {item['start']}, End: {item['end']}")
        elif item["type"] == "group":
            logger.debug(f"Setting times or tags for group '{item['name']}': Start: {item['start']}, End: {item['end']}")
        elif item["type"] == "level":
            logger.debug(f"Setting times or tags for level '{item['name']}': Start: {item['start']}, End: {item['end']}")


    # Get the logger specified in the file

    logger.debug("Starting the main program")
    logger.info("Starting changes")

    logger.debug("Loading the SGS gitlab groups")
    SGS_gitlab_groups = load_SGS_gitlab_groups("SGS_gitlab_groups.yaml")

    logger.debug("Connecting to the gitlab server")
    repo = Repos()
    logger.debug(repo)

    gitlab_projects_selected =  get_gitlab_projects(parsed_arguments,repo, SGS_gitlab_groups)
    print_in_console_the_gitlab_projects_selected(gitlab_projects_selected)

    branch_name = "develop"

    logger.info(f"----------------------------------------------------")
    logger.info(f"Looking for the modifications by selected project...")
    logger.info(f"----------------------------------------------------")

    for item in gitlab_projects_selected:
        logger.info(f"Project '{item['name']}': Start: {item['start']}, End: {item['end']}  ")

        gitlab_project_name= item['name']
        # Recursively list all files in the subdirectories
        period_list = repo.set_the_period_of_the_project(gitlab_project_name, item['start'], item['end'])
        modifications_by_file = repo.get_modifications_by_file(gitlab_project_name, branch_name=branch_name, period_list=period_list)
        #modifications_by_file = []
        item['count_files_modified'] = str(len(modifications_by_file))
        item['modifications_by_file'] = modifications_by_file
    print_in_console_the_gitlab_projects_selected(gitlab_projects_selected)
    print_in_console_the_modifications_in_the_selected_gitlab_projects(gitlab_projects_selected)

    logger.debug("Connecting to the redmine server")
    wiki = RedmineWikiPages(project_name=REDMINE_PROJECT)
    logger.debug(wiki) 
    print_the_modifications_in_the_selected_gitlab_group(wiki,gitlab_projects_selected)

    
        


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
