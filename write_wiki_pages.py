from log_config import logger
from repos import is_tag


PREFIX_WIKI_PAGE = "Changes"
SINCE_DATE = "2023-06-09 15:00"
UNTIL_DATE = "2023-06-14 14:00"

def set_wiki_name(group_or_project_name: str, period_list: list = [SINCE_DATE, UNTIL_DATE, False]) -> str:

    since_date = period_list[0].replace(" ", "_").replace(":", "_").replace(".","_")  #  format "YYYY-MM-DD HH:MM". or tag ("3.1")
    until_date = period_list[1].replace(" ", "_").replace(":", "_").replace(".","_") 
    project_name = group_or_project_name.replace("/", "_")  # "PF-VIS/VIS_IAL_Pipelines"

    wiki_page_name = PREFIX_WIKI_PAGE + "_" + since_date + "_" + until_date + "_" + project_name
    return wiki_page_name



def print_the_modifications_in_the_selected_gitlab_group(wiki,gitlab_projects_selected):

    logger.info(f"--------------------print in wiki page--------------------------------")

    for item in gitlab_projects_selected:
        print("=" * 100)
        print("Level = "+str(item['level'])+" Group = " + str(item['group']) + " Project = " + item['name'] + " Start = " + item['start'] + " End = "+ item['end'])
        print()

        gitlab_group = item['group']
        if not gitlab_group:
            continue

        wiki_page_name = set_wiki_name(gitlab_group,[item['start'],item['end'],is_tag(item['start'])])
        
