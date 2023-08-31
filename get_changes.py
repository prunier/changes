import argparse
import pprint
import yaml

from tabulate import tabulate
from log_config import logger
from collections import defaultdict


from repos import Repos,is_tag
from wiki import REDMINE_PROJECT, Wiki_pages_with_Redmine
import write_wiki_pages as wwp


def parse_arguments(args):

    arguments = iter(args)
    result = []

    session_name = "current"
    list_string = ""
    rm_string = ""

    if args[0] in ("--session"):
        session_name = args[1]
        args.pop(0)
        args.pop(0)

    if args[0] in ("--list"):
        list_string = args[1]
        args.pop(0)
        args.pop(0)
        return session_name,result,list_string,rm_string


    if args[0] in ("--rm"):
        rm_string = args[1]
        args.pop(0)
        args.pop(0)
        return session_name,result,list_string,rm_string



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

    return session_name,result,list_string,rm_string

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

def is_level_name(SGS_gitlab_groups,level_name_to_find):

    if level_name_to_find not in SGS_gitlab_groups.keys():
        logger.critical(f"The level name'{level_name_to_find}' does not exist in the input configuration file'")
        raise ValueError(f"The level name '{level_name_to_find}' does not exist in the input configuration file'")
    return True

def get_level_name(SGS_gitlab_groups,gitlab_group_name_to_find):

    level_name = "unknown_level"
    for level_name in SGS_gitlab_groups.keys():
        element = SGS_gitlab_groups[level_name]
        level_long_name = element['name']
        gitlab_groups_of_the_level = element["gitlab_groups"]
        for gitlab_long_name,gitlab_group in gitlab_groups_of_the_level.items():
            if gitlab_group == gitlab_group_name_to_find:
                return level_name

    logger.critical(f"The gitlab group '{gitlab_group_name_to_find}' does not exist in the input configuration file'")
    raise ValueError(f"The gitlab group '{gitlab_group_name_to_find}' does not exist in the input configuration file'")


def dictionalry_3d_empty(three_dimensional_dict,i,j,k):
    # Check if the cell is not empty in the three-dimensional dictionary
    if i in three_dimensional_dict and j in three_dimensional_dict[i] and k in three_dimensional_dict[i][j]:
        cell_value = three_dimensional_dict[i][j][k]
        if cell_value is not None and cell_value != '':
            #print(f"The cell ({i}, {j}, {k}) is not empty. Value: {cell_value}")
            return False
        else:
            # print(f"The cell ({i}, {j}, {k}) is empty.")
            return True
    else:
        #print(f"The cell ({i}, {j}, {k}) does not exist in the three-dimensional dictionary.")
        return True




def get_gitlab_projects(parsed_arguments,repo, SGS_gitlab_groups):

    gitlab_projects_selected = defaultdict(lambda: defaultdict(dict))

    #if parsed_arguments

    for item in parsed_arguments:
        if item["type"] == "level":
            level_name = item["name"]
            is_level_name(SGS_gitlab_groups,level_name)
            logger.info(f"Selecting projects for the level '{level_name}'")

            element = SGS_gitlab_groups[level_name]
            level_long_name = element['name']
            gitlab_groups_of_the_level = element["gitlab_groups"]
            for gitlab_long_name,gitlab_group in gitlab_groups_of_the_level.items():
                logger.info(f"Selecting projects for the gitlab group '{gitlab_group}'")
                # get the gitlab projects in the level
                gitlab_projects = repo.get_projects_with_path_with_namespace(group=gitlab_group)
                for gitlab_project in gitlab_projects:
                    if is_tag(item['start']):
                        dict1 = {'start date':'','end date':'','start tag':item['start'],'end tag':item['end']}
                    else:
                        dict1 = {'start date':item['start'],'end date':item['end'],'start tag':'','end tag':''}
                    gitlab_projects_selected[level_name][gitlab_group][gitlab_project] = dict1

        if item["type"] == "group":
            gitlab_group = item["name"]
            logger.info(f"Selecting projects in the group  '{gitlab_group}'")
            level_name = get_level_name(SGS_gitlab_groups,gitlab_group)
            # get the gitlab projects in the group
            gitlab_projects = repo.get_projects_with_path_with_namespace(group=gitlab_group)
            for gitlab_project in gitlab_projects:
                # check if gitlab_project exist in the list of dictionaries gitlab_projects_selected
                if not dictionalry_3d_empty (gitlab_projects_selected,level_name,gitlab_group,gitlab_project):
                    # delete the dictionary with the same name
                    logger.warning(f"Project '{gitlab_project}' already selected. Deleting it from the list.")

                if is_tag(item['start']):
                    dict1 = {'start date':'','end date':'','start tag':item['start'],'end tag':item['end']}
                else:
                    dict1 = {'start date':item['start'],'end date':item['end'],'start tag':'','end tag':''}
                gitlab_projects_selected[level_name][gitlab_group][gitlab_project] = dict1

        if item["type"] == "project":
            gitlab_project = item["name"]
            gitlab_group = gitlab_project.split("/")[0] # PF-LE1/LE1_VIS" -> group is PF-LE1
            short_gitlab_project = gitlab_project.split("/")[1] # PF-LE1/LE1_VIS" -> short_gitlab_project is LE1_VIS
            level_name = get_level_name(SGS_gitlab_groups,gitlab_group)

            logger.info(f"Selecting project  '{gitlab_project}'")
            # get the gitlab projects in the group
            if repo.check_project_exists(gitlab_project):
                logger.debug(f"Project '{gitlab_project}' exists.")

                if not dictionalry_3d_empty (gitlab_projects_selected,level_name,gitlab_group,gitlab_project):
                    # delete the dictionary with the same name
                    logger.warning(f"Project '{gitlab_project}' already selected. Deleting it from the list.")
                if is_tag(item['start']):
                    dict1 = {'start date':'','end date':'','start tag':item['start'],'end tag':item['end']}
                else:
                    dict1 = {'start date':item['start'],'end date':item['end'],'start tag':'','end tag':''}
                gitlab_projects_selected[level_name][gitlab_group][gitlab_project] = dict1
            else:
                logger.error(f"Gitlab project '{gitlab_project}' does not exist.")

    count_of_selected_projects = len(gitlab_projects_selected)
    logger.info(f"{count_of_selected_projects} selected projects")  
    return gitlab_projects_selected

def print_in_console_the_gitlab_projects_selected(gitlab_projects_selected):

    if len(gitlab_projects_selected) == 0:
        return

    # pretty print of the list of projects gitlab_projects_selected
    headers = ['Level','Group','Project Name', 'Start date', 'End date', 'Start tag', 'End tag']

# Converting the three-dimensional dictionary to a list of tuples
    table_data = []
    count_files_modified_flag = False

    for level_name, gitlab in gitlab_projects_selected.items():
        for gitlab_group_name, project in gitlab.items():
            for gitlab_project_name, item in project.items():
                if 'count_files_modified' in item:
                    table_data.append((level_name, gitlab_group_name, gitlab_project_name, item['start date'], item['end date'], item['start tag'], item['end tag'],item['count_files_modified']))
                    count_files_modified_flag = True
                else:
                    # value is a dictionary with the keys 'start', 'end', 'is_tag'
                    table_data.append((level_name, gitlab_group_name, gitlab_project_name, item['start date'], item['end date'], item['start tag'], item['end tag']))

    if count_files_modified_flag:
        headers.append('count of modifications')

    table_str = tabulate(table_data, headers, tablefmt='simple') # grid, simple, plain, pipe, orgtbl, rst, mediawiki, html, latex, latex_raw, latex_booktabs, tsv

    print(table_str)

def print_in_console_the_modifications_in_the_selected_gitlab_projects(gitlab_projects_selected):

    # pretty print of the list of projects gitlab_projects_selected
    headers = ['File','Author name','Created_= at']

# Converting the three-dimensional dictionary to a list of tuples
    table_data = []
    count_files_modified_flag = False

    for level_name, gitlab in gitlab_projects_selected.items():
        for gitlab_group_name, project in gitlab.items():
            for gitlab_project_name, item in project.items():

                print("=" * 100)
                print("Level = "+level_name+" Group = " + gitlab_group_name + " Project = " + gitlab_project_name+ " Start = " + item['start'] + " End = "+ item['end'])
                print()
                table = []
                if 'count_files_modified' in item and item['count_files_modified'] != '0':
                    modifications_by_file = item['modifications_by_file']
                    for file,modifications in modifications_by_file.items():
                        for m in modifications:
                            table.append([file,m[2],m[3]]) # m[4] = Id, m[1] = Title
                
                    table_str = tabulate(table, headers, tablefmt='simple')
                    print(table_str)


def main(args):
    parser = argparse.ArgumentParser(description="Get the changes in the gitlab projects")

    session_name,parsed_arguments,list_string,rm_string = parse_arguments(args)

    logger.debug("Connecting to the redmine server")
    wiki = Wiki_pages_with_Redmine(project_name=REDMINE_PROJECT)
    logger.debug(wiki) 

    if list_string != "":
        wiki.delete_wiki_pages(wiki.project_name, list_string, delete=False)
        return
    if rm_string != "":
        wiki.delete_wiki_pages(wiki.project_name, rm_string, delete=False)
        # ask the user if he is sure to delete the wiki pages above
        if input("Are you sure to delete the wiki pages above (Y/N)? ") == "Y":
            wiki.delete_wiki_pages(wiki.project_name, rm_string, delete=True)
        return

    # Get the logger specified in the file

    logger.debug("Starting the main program")
    logger.info("Starting changes")

    logger.debug("Loading the SGS gitlab groups")
    SGS_gitlab_groups = load_SGS_gitlab_groups("SGS_gitlab_groups.yaml")

    for item in parsed_arguments:
        if item["type"] == "project":
            logger.debug(f"Setting times or tags for project '{item['name']}': Start: {item['start']}, End: {item['end']}")
        elif item["type"] == "group":
            logger.debug(f"Setting times or tags for group '{item['name']}': Start: {item['start']}, End: {item['end']}")
        elif item["type"] == "level":
            logger.debug(f"Setting times or tags for level '{item['name']}': Start: {item['start']}, End: {item['end']}")

    # if the first argument for the level is "SGS", then add all the levels to the list of arguments
    if parsed_arguments[0]['name'] == 'SGS':
        for level in SGS_gitlab_groups.keys():
            added_item = {}
            added_item['type'] = 'level'
            added_item['name'] = level
            added_item['start'] = item['start']
            added_item['end'] = item['end']
            parsed_arguments.append(added_item)
        parsed_arguments.pop(0) # delete the first level "SGS" !


    logger.debug("Connecting to the gitlab server")
    repo = Repos()
    logger.debug(repo)

    gitlab_projects_selected =  get_gitlab_projects(parsed_arguments,repo, SGS_gitlab_groups)
    print_in_console_the_gitlab_projects_selected(gitlab_projects_selected)


    branch_name = "develop"
    filter_modifications_list = ["PkgDef_"]

    logger.info(f"----------------------------------------------------")
    logger.info(f"Looking for the modifications by selected project...")
    logger.info(f"----------------------------------------------------")

    for level_name, gitlab_group_name in gitlab_projects_selected.items():
        for gitlab_group_name, project in gitlab_group_name.items():
            for gitlab_project_name, item in project.items():
                period = repo.complete_the_period_of_the_project(gitlab_project_name, item)
                item['start date'] = period['start date']  
                item['end date'] = period['end date']    
                item['start tag'] = period['start tag']
                item['end tag'] = period['end tag']

                all_modifications = repo.get_modifications_by_file(gitlab_project_name, branch_name=branch_name, period=period)
                selected_modifications = repo.select_modifications(all_modifications,filter_modifications_list)            

                item['count_files_modified'] = str(len(all_modifications))
                item['modifications_by_file'] = all_modifications
                item['selected_modifications'] = selected_modifications
                item['count_selected_modifications'] = str(len(selected_modifications))

        
    print_in_console_the_gitlab_projects_selected(gitlab_projects_selected)
    #print_in_console_the_modifications_in_the_selected_gitlab_projects(gitlab_projects_selected)


    wwp.print_the_modifications_at_SGS_level(wiki,session_name,repo.gitlab_server,gitlab_projects_selected,filter_modifications_list)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
