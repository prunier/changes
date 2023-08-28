# import functions in repos.py
from repos import Repos
from repos import BRANCH
from repos import SINCE_DATE
from repos import UNTIL_DATE

from wiki import RedmineWikiPages
from wiki import PARENT_WIKI_PAGE
from wiki import REDMINE_PROJECT
from wiki import TOP_PARENT_WIKI_PAGE

from log_config import logger


# function using construct parser that read input user arguments: project name, branch name, since date, gitlab group, level name
def get_args():
    import argparse

    parser = argparse.ArgumentParser(description="Get the changes in a project since a date")
    parser.add_argument(
        "-p",
        "--gitlab_project",
        type=str,
        nargs="+",
        help="gitlab project name",
        default=[],  # eg ["PF-VIS/VIS_IAL_Pipelines"]
    )
    parser.add_argument("-b", "--branch", type=str, help="branch name", default=BRANCH)
    parser.add_argument(
        "-s",
        "--since",
        type=str,
        help="since date",
        default="0.9.0", #SINCE_DATE 2023-06-09 09:00
    )

    parser.add_argument(
        "-t",
        "--tag",
        action="store_true",
        help="use tag instead of date",
        default=False,
    )


    parser.add_argument(
        "-u",
        "--until",
        type=str,
        help="until date",
        default="0.9.1", #UNTIL_DATE  2023-06-14 15:00
    )

    parser.add_argument(
        "-g",
        "--group",
        type=str,
        nargs="+",
        help="gitlab group",
        default=[],  # eg ["PF-VIS","PF-LE3-WL","PF-LE3-GC"]
    )
    parser.add_argument(
        "-l",
        "--pf_level",
        type=str,
        nargs="+",
        help="level name",
        default=[],  # eg ["LE2"]
    )

    parser.add_argument(
        "--rm",
        type=str,
        help="remove wiki pages starting with a string",
        default="",  # eg ["Changes_2023-08-03_15"] or ["list"]
    )
    parser.add_argument(
        "--list",
        type=str,
        help="list wiki pages starting with a string",
        default="",  # eg ["Changes_2023-08-03_15"] or ["list"]
    )

    args = parser.parse_args()
    return args


# function that print the changes in a project with three parameters : project name, branch name and since date
# if the wiki page is created return true else return false


def load_SGS_gitlab_groups(input_yaml_file: str):
    """_summary_

    Arguments:
        input_yaml_file -- _description_

    Returns:
        _description_
    """
    import yaml

    with open(input_yaml_file, "r") as f:
        SGS_gitlab_groups = yaml.safe_load(f.read())
    return SGS_gitlab_groups


def set_wiki_name(group_or_project_name: str, period_list: list = [SINCE_DATE, UNTIL_DATE, False]) -> str:

    since_date = period_list[0].replace(" ", "_").replace(":", "_").replace(".","_")  #  format "YYYY-MM-DD HH:MM". or tag ("3.1")
    until_date = period_list[1].replace(" ", "_").replace(":", "_").replace(".","_") 
    project_name = group_or_project_name.replace("/", "_")  # "PF-VIS/VIS_IAL_Pipelines"

    wiki_page_name = PARENT_WIKI_PAGE + "_" + since_date + "_" + until_date + "_" + project_name
    return wiki_page_name


def get_project_changes(       
    repo: Repos,
    wiki: RedmineWikiPages,
    project: str,
    branch_name: str = BRANCH,
    period_list: list = [SINCE_DATE, UNTIL_DATE, False],
    parent_wiki_page=PARENT_WIKI_PAGE,
):
    # get the project changes

    since_date = period_list[0]
    until_date = period_list[1]
    wiki_page_name = set_wiki_name(project, period_list)

    table, row_names = repo.print_project_files(project=project, branch_name=branch_name, period_list=period_list)
    count_of_changes = len(table)

    if count_of_changes == 0:
        logger.debug(
            f"No changes in {project} since {since_date} until {until_date}, wiki page {wiki_page_name} deleted if exists"
        )
        wiki.check_wiki_page_exist(delete_if_exists=True, wiki_page_name=wiki_page_name)
    else:
        logger.info(f"Project  {project} have {count_of_changes} changes")
        logger.debug(f"print the data in redmine...")

        # data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        # row_names = ["Row 1", "Row 2", "Row 3"]
        wiki_page_header = f"\n\nh2. {project} \n\n\nList of files with modifications in the {branch_name} branch since {since_date} until {until_date}\n\n\n"

        wiki.create_table_in_a_new_wiki_page(wiki_page_name, parent_wiki_page, wiki_page_header, table, row_names)
    return count_of_changes


def process_gitlab_group(
    repo: Repos,
    wiki: RedmineWikiPages,
    gitlab_group: str,
    branch_name: str = BRANCH,
    period_list=[SINCE_DATE, UNTIL_DATE, False],
    restrict_to_projects=[],
    parent_wiki_page=PARENT_WIKI_PAGE,
):
    # get the gitlab project
    gitlab_projects = repo.get_groups_with_path_with_namespace(group=gitlab_group)

    since_date = period_list[0]
    until_date = period_list[1]

    row_names = ["Gitlab project", "Count of files modified"]
    table = []
    count_of_changes_in_the_group = 0

    for gitlab_project_name in gitlab_projects:
        # eg "PF-VIS/VIS_IAL_Pipelines"

        # process if the gitlab project is in the list of PF levels to be processed (if not empty)
        if restrict_to_projects and gitlab_project_name not in restrict_to_projects:
            continue

        logger.info(f"Project {gitlab_project_name}")
        count_of_changes = get_project_changes(
            repo,
            wiki,
            project=gitlab_project_name,
            branch_name=branch_name,
            period_list=period_list,
            parent_wiki_page=parent_wiki_page,
        )
        if count_of_changes > 0:
            wiki_page_name = set_wiki_name(gitlab_project_name, period_list)
            cell_text = "[[" + wiki.project_name + ":" + wiki_page_name + "|" + str(count_of_changes) + "]]"
        else:
            cell_text = str(count_of_changes)
        table.append([gitlab_project_name, cell_text])
        count_of_changes_in_the_group += int(count_of_changes)

    if count_of_changes_in_the_group > 0:
        logger.info(f"Group {gitlab_group} have {count_of_changes_in_the_group} changes")
        wiki_page_name = set_wiki_name(gitlab_group, period_list)

        wiki_page_header = f"\n\nh2. Gitlab group {gitlab_group} \n\n\nCount of files modified in the {branch_name} branch since {since_date} until {until_date}\n\n\n"
        wiki.create_table_in_a_new_wiki_page(wiki_page_name, parent_wiki_page, wiki_page_header, table, row_names)

    return count_of_changes_in_the_group


# main
def main():
    # Get the logger specified in the file

    logger.debug("Starting the main program")
    logger.info("Starting changes")

    logger.debug("Connecting to the gitlab server")
    repo = Repos()
    logger.debug(repo)

    logger.debug("Connecting to the redmine server")
    wiki = RedmineWikiPages(project_name=REDMINE_PROJECT)
    logger.debug(wiki)

    logger.debug("Loading the SGS gitlab groups")
    SGS_gitlab_groups = load_SGS_gitlab_groups("SGS_gitlab_groups.yaml")
    logger.debug(SGS_gitlab_groups)

    # get the arguments
    args = get_args()
    logger.info(args)

    #  admin tasks
    if args.list:
        wiki.delete_wiki_pages(wiki.project_name, args.list, delete=False)
        return
    if args.rm:
        wiki.delete_wiki_pages(wiki.project_name, args.rm, delete=False)
        # ask the user if he is sure to delete the wiki pages above
        if input("Are you sure to delete the wiki pages above (Y/N)? ") == "Y":
            wiki.delete_wiki_pages(wiki.project_name, args.rm, delete=True)
        return

    branch_name = args.branch
    since_date = args.since
    until_date = args.until
    use_tags = args.tag

    period_str = f" since {since_date} until {until_date}"
    period_list = [since_date, until_date, use_tags]

    gitlab_groups_selected = args.group  # if not empty, process only these gitlab groups
    PF_levels_selected = args.pf_level  # if not empty, process only these PF levels
    gitlab_projects_selected = args.gitlab_project  # if not empty, process only these gitlab projects (full pathname)

    wiki_page_header = f"\n\nh2. Count of files modified in the {branch_name} branch" + period_str + "\n\n\n"

    if PF_levels_selected:
        wiki_page_header += f"\n*PF levels selected*: " + " ".join(PF_levels_selected)
    if gitlab_groups_selected:
        wiki_page_header += f"\n*Gitlab groups selected*: " + " ".join(gitlab_groups_selected)
    if gitlab_projects_selected:
        wiki_page_header += f"\n*Gitlab projects selected*: " + " ".join(gitlab_projects_selected)

    output_wiki_page_name = set_wiki_name(group_or_project_name="SGS", period_list=period_list)
    output_wki_object = wiki.create_table_in_a_new_wiki_page(
        output_wiki_page_name, TOP_PARENT_WIKI_PAGE, wiki_page_header, [], []
    )

    for PF_level in SGS_gitlab_groups:
        # process if the PF level is in the list of PF levels to be processed (if not empty)
        if PF_levels_selected and PF_level not in PF_levels_selected:
            continue

        PF_level_name = SGS_gitlab_groups[PF_level]["name"]
        gitlab_groups = SGS_gitlab_groups[PF_level]["gitlab_groups"]

        row_names = ["Gitlab group", "Count of files modified"]
        table = []
        count_of_changes_in_the_level = 0

        for group_name, gitlab_group in gitlab_groups.items():
            # process if the PF level is in the list of PF levels to be processed (if not empty)
            if gitlab_groups_selected and gitlab_group not in gitlab_groups_selected:
                continue

            logger.info(f"Group {gitlab_group}")
            count_of_changes_in_the_group = process_gitlab_group(
                repo,
                wiki,
                gitlab_group,
                branch_name,
                period_list,
                restrict_to_projects=gitlab_projects_selected,
                parent_wiki_page=output_wiki_page_name,
            )
            if count_of_changes_in_the_group > 0:
                wiki_page_name = set_wiki_name(gitlab_group, period_list)
                cell_text = (
                    "[[" + wiki.project_name + ":" + wiki_page_name + "|" + str(count_of_changes_in_the_group) + "]]"
                )
            else:
                cell_text = str(count_of_changes_in_the_group)
            count_of_changes_in_the_level += count_of_changes_in_the_group

            table.append([gitlab_group, cell_text])
        if count_of_changes_in_the_level > 0:
            logger.info(f"Level {PF_level} have {count_of_changes_in_the_level} changes")
            wiki_page_header = (
                f"\n\nh2. {PF_level_name} \n\n\nCount of files modified in the {branch_name} branch"
                + period_str
                + "\n\n\n"
            )
            # created_wki_page = wiki.print_table_in_wiki_page("changes_"+PF_level, wiki_page_header, table, row_names)
            output_wki_object = wiki.add_table_in_wiki_page(output_wki_object, wiki_page_header, table, row_names)


# call the main function
if __name__ == "__main__":
    main()
