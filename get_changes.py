import argparse
import pprint
from log_config import logger

from repos import Repos


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
    """_summary_

    Arguments:
        input_yaml_file -- _description_

    Returns:
        _description_
    """
    import yaml

    with open(input_yaml_file, "r") as f:
        SGS_gitlab_groups = yaml.safe_load(f.read())

    # Create a PrettyPrinter
    pp = pprint.PrettyPrinter(indent=2)

    # Use the pretty-printer to format the dictionary
    formatted_dict = pp.pformat(SGS_gitlab_groups)

    # Log the formatted dictionary
    logger.debug("Formatted dictionary:\n%s", formatted_dict)

    return SGS_gitlab_groups



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

    gitlab_projects_selected = []

    # loop over the projects belonging to the level specified in the input arguments

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
                            dict1 = {'name': gitlab_project,'start':item['start'],'end':item['end']}
                            gitlab_projects_selected.append(dict1)

        if item["type"] == "group":
            group_name = item["name"]
            logger.info(f"Selecting projects in the group  '{group_name}'")
            # get the gitlab projects in the group
            gitlab_projects = repo.get_projects_with_path_with_namespace(group=group_name)
            for gitlab_project in gitlab_projects:
                # check if gitlab_project exist in the list of dictionaries gitlab_projects_selected
                if any(d['name'] == gitlab_project for d in gitlab_projects_selected):
                    # delete the dictionary with the same name
                    gitlab_projects_selected = [d for d in gitlab_projects_selected if d.get('name') != gitlab_project]
                    logger.warning(f"Project '{gitlab_project}' already selected. Deleting it from the list.")
                dict1 = {'name': gitlab_project,'start':item['start'],'end':item['end']}
                gitlab_projects_selected.append(dict1)

        if item["type"] == "project":
            gitlab_project = item["name"]
            logger.info(f"Selecting project  '{gitlab_project}'")
            # get the gitlab projects in the group
            if repo.check_project_exists(gitlab_project):
                logger.debug(f"Project '{gitlab_project}' exists.")
                # check if gitlab_project exist in the list of dictionaries gitlab_projects_selected
                if any(d['name'] == gitlab_project for d in gitlab_projects_selected):
                    # delete the dictionary with the same name
                    gitlab_projects_selected = [d for d in gitlab_projects_selected if d.get('name') != gitlab_project]
                    logger.warning(f"Project '{gitlab_project}' already selected. Deleting it from the list.")
                dict1 = {'name': gitlab_project,'start':item['start'],'end':item['end']}
                gitlab_projects_selected.append(dict1)

            else:
                logger.error(f"Gitlab project '{gitlab_project}' does not exist.")

    count_of_selected_projects = len(gitlab_projects_selected)
    logger.info(f"{count_of_selected_projects} selected projects")

    branch_name = "develop"

    for item in gitlab_projects_selected:
        logger.info(f"Project '{item['name']}': Start: {item['start']}, End: {item['end']}  ")

        gitlab_project_name= item['name']
        # Recursively list all files in the subdirectories
        project = repo.gl.projects.get(gitlab_project_name)
        period_list = [item['start'], item['end'], False]
        modifications_by_file = repo.get_modifications_by_file(project, branch_name=branch_name, period_list=period_list)
        logger.info("Modifications by file:" + str(len(modifications_by_file)))  # Print the dictionary
    
        


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
