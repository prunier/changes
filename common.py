from datetime import datetime, timedelta
import os
import pytz
from tabulate import tabulate




def try_parse_date(date_string):
    # List of potential formats to try
    potential_formats = [
        '%Y-%m-%dT%H:%M:%S.%f%z',  # ISO 8601 format with timezone
        '%Y-%m-%dT%H:%M:%S.%f',    # ISO 8601 format without timezone
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d'
    ]

    for format in potential_formats:
        try:
            return datetime.strptime(date_string, format)
        except ValueError:
            pass
    return None

def get_the_tags_in_the_period_at_SGS_level(gitlab_projects_selected):

    start_tag_date = ""
    end_tag_date = ""
    gitlab_server = os.environ.get("GITLAB_SERVER")

    headers = ['Group','Project Name', 'tag', 'Creation date','Author']


    if len(gitlab_projects_selected) == 0:
        return start_tag_date,end_tag_date
    level_data = {}

    for level_name, gitlab in gitlab_projects_selected.items():
        level_data[level_name] = []
        for gitlab_group_name, project in gitlab.items():

            gn = '"' + gitlab_group_name + '":' + gitlab_server + "/" + gitlab_group_name    
            #gn = gitlab_group_name
            for gitlab_project_name, item in project.items():

                pn = '"' + gitlab_project_name + '":' + gitlab_server + "/" + gitlab_project_name
                #pn = gitlab_project_name

                for tag_item in item['tags_in_period']:
                    cr = tag_item['created_at']
                    level_data[level_name].append((gn, pn, tag_item['name'], cr, tag_item['author_name']))
                    if not start_tag_date or cr < start_tag_date:
                        start_tag_date = cr
                    if not end_tag_date or cr > end_tag_date:
                        end_tag_date = cr

        table_data = level_data[level_name]
        table_str = tabulate(table_data, headers, tablefmt='simple')
        print(table_str)


    return start_tag_date,end_tag_date,level_data

def get_the_tags_by_period(data:dict,start_tag_date:str,end_tag_date:str,periodicity_in_days:int= 30)->dict:

    # split the period 
    periodicity = timedelta(days=periodicity_in_days)
    # Initialize an empty list to store the dates
    date_list = []
    tags_by_period = {}
    if len(data) == 0 or start_tag_date == "" or end_tag_date == "":
        return tags_by_period   

    start_date = try_parse_date(start_tag_date)
    end_date = try_parse_date(end_tag_date)

    paris_timezone = pytz.timezone('Europe/Paris')
    current_date = datetime(start_date.year, start_date.month, 1,tzinfo=paris_timezone)

    # Generate the list of dates
    while current_date <= end_date:
        date_list.append(current_date)
        # Move to the beginning of the next month
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1,tzinfo=paris_timezone)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1,tzinfo=paris_timezone)

    for level_name, gitlab in data.items():
        for gitlab_group_name, project in gitlab.items():
            for gitlab_project_name, item in project.items():
                for tag_item in item['tags_in_period']:
                    created_at = try_parse_date(tag_item['created_at'])

                    # loop  the tange  of dates
                    for date in date_list:
                        key_date = date.strftime('%Y-%m-%d')
                        if not key_date in tags_by_period:
                            tags_by_period[key_date] = []

                        next_date = date + timedelta(days=periodicity_in_days)
                        if created_at >= date and created_at < next_date:
                            tags_by_period[key_date].append(tag_item)

    return tags_by_period