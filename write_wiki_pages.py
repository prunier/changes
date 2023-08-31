from datetime import datetime, timedelta
from log_config import logger


PREFIX_WIKI_PAGE = "Changes"
TOP_PARENT_WIKI_PAGE = "Files_modified_in_projects"

SINCE_DATE = "2023-06-09 15:00"
UNTIL_DATE = "2023-06-14 14:00"



def try_parse_date(date_string):
    # List of potential formats to try
    potential_formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M'
    ]

    for format in potential_formats:
        try:
            return datetime.strptime(date_string, format)
        except ValueError:
            pass
    return None


def print_the_modifications_at_project_level(gitlab_projects_selected,level_name,gitlab_group_name,gitlab_project,selection_modifications=False):
    
    headers = ["Path/Name", "Modifications"]
    table = []

    if not selection_modifications:
        field_count = 'count_files_modified'
        field_modifs = 'modifications_by_file'
    else:
        field_count = 'count_selected_modifications'
        field_modifs = 'selected_modifications'

    item = gitlab_projects_selected[level_name][gitlab_group_name][gitlab_project]   

    if field_count in item and item[field_count] != '0':
        modifications_by_file = item[field_modifs]

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

    return headers,table


def print_the_modifications_at_SGS_level(wiki,session_name:str,gitlab_server:str,gitlab_projects_selected,filter_modifications_list):

    if len(gitlab_projects_selected) == 0:
        return

    output_wiki_page_name = PREFIX_WIKI_PAGE + "_" + session_name
    wiki_page_header = f"\n\nh2. Count of modifications in files" + "\n\n\n"
    wiki_page_header += """
{background:lightgrey}. |_. Color |_. Tag created before...|
|{background:red}. Red| this week |
|{background:orange}. Orange| this month | 
|{background:yellow}. Yellow | the last three months |
|{background:lightgrey}. Grey | this year|


{background:lightgrey}. |_. Color |_. Description|
|{background:lightgreen}. Green| Specific files modified (see below) |


*Selected modifications*: count of modifications done on the files which name contains one of the following strings: *"""
    wiki_page_header += ", ".join(filter_modifications_list) + "*\n\n\n"

    output_wki_object = wiki.create_table_in_a_new_wiki_page(output_wiki_page_name, TOP_PARENT_WIKI_PAGE, wiki_page_header, [], [])

    # pretty print of the list of projects gitlab_projects_selected
    headers = ['Group','Project Name', 'Start date', 'End date','Start tag','End tag','# modifications','# selected modifications']

    current_date = datetime.now()
    last_week_date = current_date - timedelta(days=7)
    last_month_date = current_date - timedelta(days=30)
    last_year_date = current_date - timedelta(days=365)
    last_3months_date = current_date - timedelta(days=92)

    count_files_modified_flag = False

    for level_name, gitlab in gitlab_projects_selected.items():

        table_data = []

        for gitlab_group_name, project in gitlab.items():

            # create the wiki page for the group with all the modifications done in the group
            wiki_page_gitlab_name = PREFIX_WIKI_PAGE + "_" + session_name + "_" + gitlab_group_name.replace("/", "_") + "_files"
            wiki_page_header = f"\n\nh2. {gitlab_group_name} \n\n\nList of files with modifications\n\n\n"


            output_wki_gitlab_object = wiki.create_table_in_a_new_wiki_page(wiki_page_gitlab_name, output_wiki_page_name, wiki_page_header, [], [])
               
            for gitlab_project_name, item in project.items():
                # build the sub page showing the gitlab products modified and their files
                project_headers, project_table = print_the_modifications_at_project_level(gitlab_projects_selected,level_name,gitlab_group_name,gitlab_project_name)

                count_of_changes = int(item['count_files_modified'])
                if count_of_changes > 0:

                    wiki_page_header = f"\n\nh3. {gitlab_project_name}\n\n"
                    wiki_page_header += f"\n\n*All the modifications*;\n\n\n"
                    wiki.add_table_in_wiki_page(output_wki_gitlab_object, wiki_page_header, project_table, project_headers,flag_add_line=False)

                    count_of_changes = "[[" + wiki_page_gitlab_name + "#"+ gitlab_project_name + "|" + str(item['count_files_modified']) + "]]"

                    project_headers_s, project_table_s = print_the_modifications_at_project_level(gitlab_projects_selected,level_name,gitlab_group_name,gitlab_project_name,selection_modifications=True)
                    count_of_selected_changes = int(item['count_selected_modifications'])

                    if count_of_selected_changes > 0:
                        wiki_page_header = f"\n\n*Selected modifications*: count of modifications done on the files which name contains one of the following strings:*{filter_modifications_list}*\n\n\n"   
                        wiki.add_table_in_wiki_page(output_wki_gitlab_object, wiki_page_header, project_table_s, project_headers_s,flag_add_line=False)             

                        count_of_selected_changes = "{background:lightgreen}. "  + "[[" + wiki_page_gitlab_name + "#"+ gitlab_project_name + "|" + str(item['count_selected_modifications']) + "]]"

                    gn = '"' + gitlab_group_name + '":' + gitlab_server + "/" + gitlab_group_name    
                    pn = '"' + gitlab_project_name + '":' + gitlab_server + "/" + gitlab_project_name
                    # compare dates if the start tag does not contain ">" so start_date matches exactly with a tag
                    et = item['end tag'] 
                    if ">" not in item['end tag']:
                        edt = try_parse_date(item['end date'])
                        if not edt:
                            logger.error(f"Unable to parse the value 'end_date' '{item['end date']}' with any of the formats")
                        else:
                            if edt > last_year_date:
                                et = "{background:lightgrey}. " + item['end tag']
                            if edt > last_3months_date:
                                et = "{background:yellow}. " + item['end tag']
                            if edt > last_month_date:
                                et = "{background:orange}. " + item['end tag']
                            if edt > last_week_date:
                                et = "{background:red}. " + item['end tag']                  

                    table_data.append((gn, pn, item['start date'], item['end date'], item['start tag'], et,str(count_of_changes),str(count_of_selected_changes)))

        wiki_page_header = (f"\n\nh2. {level_name} \n\n\nCount of modifications in files\n\n\n")
        output_wki_object = wiki.add_table_in_wiki_page(output_wki_object, wiki_page_header, table_data, headers)

