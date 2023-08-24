# import functions in repos.py
from repos import Repos
from repos import BRANCH
from repos import SINCE_DATE

from wiki import RedmineWikiPages
from wiki import PARENT_WIKI_PAGE
from wiki import REDMINE_PROJECT

from log_config import logger


# function using construct parser that read input user arguments: project name, branch name, since date, gitlab group, level name
def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Get the changes in a project since a date"
    )
    parser.add_argument(
        "-p",
        "--gitlab_project",
        type=str,
        nargs='+',  
        help="gitlab project name",
        default=["PF-VIS/VIS_Helper_scripts"], # eg ["PF-VIS/VIS_IAL_Pipelines"]
    )
    parser.add_argument(
        "-b", "--branch", type=str, help="branch name", default=BRANCH
    )
    parser.add_argument(
        "-s",
        "--since",
        type=str,
        help="since date",
        default=SINCE_DATE,
    )
    parser.add_argument(
        "-g",
        "--group",
        type=str,
        nargs='+',  
        help="gitlab group",
        default=["PF-VIS"] # eg ["PF-VIS","PF-LE3-WL","PF-LE3-GC"] 
    )
    parser.add_argument(
        "-l",
        "--pf_level",
        type=str,
        nargs='+',  
        help="level name",
        default=[], # eg ["LE2"]
    )

    parser.add_argument(
        "-a",
        "--admin",
        type=str,
        nargs='+',  
        help="admin",
        default=[], # eg ["rm"] or ["list"]
    )

    args = parser.parse_args()
    return args


# function that print the changes in a project with three parameters : project name, branch name and since date
# if the wiki page is created return true else return false 

def load_SGS_gitlab_groups(input_yaml_file:str):
    import yaml
    with open(input_yaml_file, 'r') as f:
        SGS_gitlab_groups = yaml.safe_load(f.read())
    return SGS_gitlab_groups


def get_project_changes(repo: Repos, wiki: RedmineWikiPages, project: str, branch_name: str = BRANCH, since_date: str = SINCE_DATE):
    # get the project changes

    wiki_page_name = PARENT_WIKI_PAGE + "_" +project.replace("/",'_')

    table, row_names = repo.print_project_files(project=project, branch_name=branch_name, since_date=since_date)
    count_of_changes = len(table)

    if count_of_changes == 0:
        logger.info(f"No changes in {project} since {since_date}: wiki page {wiki_page_name} deleted if exists")
        wiki.check_wiki_page_exist(delete_if_exists=True, wiki_page_name=wiki_page_name)
    else:

        logger.debug(f"print the data in redmine...")

        #data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        #row_names = ["Row 1", "Row 2", "Row 3"]
        wiki_page_header = f"\n\nh2. {project} \n\n\nList of files with modifications in the {branch_name} branch since {since_date}\n\n\n"

        wiki.print_table_in_wiki_page(wiki_page_name, wiki_page_header, table, row_names)
    return count_of_changes

def process_gitlab_group(repo: Repos, wiki: RedmineWikiPages, gitlab_group: str, branch_name: str = BRANCH, since_date: str = SINCE_DATE,restrict_to_projects=[] ):
# get the gitlab project 
    gitlab_projects = repo.get_groups_with_path_with_namespace(group=gitlab_group)

    row_names = ["Gitlab project", "Count of files modified"]
    table = []
    count_of_changes_in_the_group = 0

    for gitlab_project_name in gitlab_projects:
        # eg "PF-VIS/VIS_IAL_Pipelines"

        # process if the gitlab project is in the list of PF levels to be processed (if not empty)
        if restrict_to_projects and gitlab_project_name not in restrict_to_projects:
            continue

        logger.info(f"Project {gitlab_project_name} to be processed")
        count_of_changes = get_project_changes(repo, wiki, project=gitlab_project_name, branch_name=branch_name, since_date=since_date)
        if count_of_changes > 0:
            wiki_page_name = PARENT_WIKI_PAGE + "_" +gitlab_project_name.replace("/",'_')
            cell_text = "[["+wiki.project_name+":"+wiki_page_name+"|"+str(count_of_changes)+"]]"
        else:
            cell_text = str(count_of_changes)
        table.append([gitlab_project_name, cell_text])
        count_of_changes_in_the_group += int(count_of_changes)


    if count_of_changes_in_the_group > 0:
        wiki_page_header = f"\n\nh2. Gitlab group {gitlab_group} \n\n\nCount of files modified in the {branch_name} branch since {since_date}\n\n\n"
        wiki.print_table_in_wiki_page("changes_"+gitlab_group, wiki_page_header, table, row_names)

    return count_of_changes_in_the_group



# main
def main():
# Get the logger specified in the file

    logger.debug('Starting the main program')
    logger.info("Starting changes")


    logger.debug("Connecting to the gitlab server")
    repo = Repos()
    logger.debug(repo)

    logger.debug("Connecting to the redmine server")
    wiki = RedmineWikiPages(project_name=REDMINE_PROJECT)
    logger.debug(wiki)

    logger.debug("Loading the SGS gitlab groups")
    SGS_gitlab_groups = load_SGS_gitlab_groups ("SGS_gitlab_groups.yaml")
    logger.debug(SGS_gitlab_groups)

    # get the arguments
    args = get_args()
    logger.info(args)

    #  admin tasks  
    if args.admin:
        # delete the wiki pages if their names contain the string "changes"
        if "list" in args.admin:
            wiki.delete_wiki_pages(wiki.project_name,PARENT_WIKI_PAGE+"_",delete=False)
        if "rm" in args.admin:
            wiki.delete_wiki_pages(wiki.project_name,PARENT_WIKI_PAGE+"_",delete=True)
        return

    branch_name = args.branch
    since_date = args.since
    gitlab_groups_selected = args.group # if not empty, process only these gitlab groups
    PF_levels_selected = args.pf_level  # if not empty, process only these PF levels
    gitlab_projects_selected = args.gitlab_project  # if not empty, process only these gitlab projects (full pathname)
    

    wiki_page_header = f"\nh2. Count of files modified in the {branch_name} branch since {since_date}\n\n\n"

    if PF_levels_selected:
        wiki_page_header += f"\n*PF levels selected*: " + ' '.join(PF_levels_selected)
    if gitlab_groups_selected:
        wiki_page_header += f"\nG*itlab groups selected*: " + ' '.join(gitlab_groups_selected)
    if gitlab_projects_selected:
        wiki_page_header += f"\n*Gitlab projects selected*: " + ' '.join(gitlab_projects_selected)

    
    output_wki_page = wiki.print_table_in_wiki_page(PARENT_WIKI_PAGE, wiki_page_header, [], [])


    for PF_level in SGS_gitlab_groups:


        # process if the PF level is in the list of PF levels to be processed (if not empty)
        if PF_levels_selected and PF_level not in PF_levels_selected:
            continue

        PF_level_name = SGS_gitlab_groups[PF_level]['name']
        gitlab_groups = SGS_gitlab_groups[PF_level]['gitlab_groups']

        row_names = ["Gitlab group", "Count of files modified"]  
        table = []
        count_of_changes_in_the_level = 0


        for group_name,gitlab_group in gitlab_groups.items():

            # process if the PF level is in the list of PF levels to be processed (if not empty)
            if gitlab_groups_selected and gitlab_group not in gitlab_groups_selected:
                continue

            logger.info(f"Group {gitlab_group} to be processed")
            count_of_changes_in_the_group = process_gitlab_group(repo, wiki, gitlab_group, branch_name, since_date,restrict_to_projects=gitlab_projects_selected)
            if count_of_changes_in_the_group > 0:
                wiki_page_name = PARENT_WIKI_PAGE+"_"+gitlab_group
                cell_text = "[["+wiki.project_name+":"+wiki_page_name+"|"+str(count_of_changes_in_the_group)+"]]"
            else:
                cell_text = str(count_of_changes_in_the_group)
            count_of_changes_in_the_level += count_of_changes_in_the_group

            table.append([gitlab_group, cell_text])
        if count_of_changes_in_the_level > 0:
            wiki_page_header = f"\n\nh2. {PF_level_name} \n\n\nCount of files modified in the {branch_name} branch since {since_date}\n\n\n"
            #created_wki_page = wiki.print_table_in_wiki_page("changes_"+PF_level, wiki_page_header, table, row_names)
            output_wki_page = wiki.add_table_in_wiki_page(output_wki_page, wiki_page_header, table, row_names)


# call the main function
if __name__ == "__main__":
    main()
