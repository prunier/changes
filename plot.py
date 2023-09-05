# debug
from time import strptime
from matplotlib import dates
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict
from log_config import logger

def plot_modifications(session_name:str, data:defaultdict):


    plot_filename = f"{session_name}_modifications.png"
    # Define colors for each group
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

    sum_by_group = defaultdict(int)

    for level, group_data in data.items():
        for group, project_data in group_data.items():
            for project, value in project_data.items():
                count_of_files_modified = int(value['count_files_modified'])
                sum_by_group[group] += count_of_files_modified


    # Extract group names and sum values for plotting
    group_names = list(sum_by_group.keys())
    sum_values = list(sum_by_group.values())

    # Create a bar plot with different colors for each group
    plt.figure(figsize=(10, 6))  # Adjust the figure size as needed
    bars = plt.bar(group_names, sum_values)

    # Assign colors to bars
    for i, bar in enumerate(bars):
        bar.set_color(colors[i % len(colors)])

    plt.xlabel('Gitlab group')
    plt.ylabel('# modified files')
    plt.title('Sum of modified files by Gitlab group')
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability

    # Display the plot
    plt.tight_layout()
    #plt.show()

    # sauvegarder dans un fichier
    plt.savefig(plot_filename)
    logger.info(f"the plot has been stored in {plot_filename}")

    return plot_filename

def plot_tags(session_name:str,dict_of_list):

    plot_filename = f"{session_name}_tags.png"

    # transform text time dta into datetime format
    date_strings = list(dict_of_list.keys())
    #for  date_string in dict_of_list.keys():
    #    date_data = try_parse_date(date_string)
    #    x_values.append(date_data)

    data_values = []
    for x_data_dict in date_strings:
        count_in_dict = len(dict_of_list[x_data_dict])
        data_values.append(count_in_dict)

    # Convert date strings to datetime objects
    dates = [datetime.strptime(date, '%Y-%m-%d') for date in date_strings]

    # Create a line plot
    plt.figure(figsize=(10, 5))  # Adjust figure size as needed
    plt.plot(dates, data_values, marker='o', linestyle='-', label='Time Series Data', color='blue')

    # Customize the plot
    plt.xlabel('Date')
    plt.ylabel('#tags')
    plt.title('Count of tags by month')
    plt.legend()

    # Format the x-axis date labels (optional)
    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))

    # Rotate x-axis labels (optional)
    plt.xticks(rotation=45)

    # Display the plot
    plt.tight_layout()  # Ensures labels are not cut off
    plt.grid(True)  # Add grid lines (optional)
    #plt.show()

    # sauvegarder dans un fichier
    plt.savefig(plot_filename)
    logger.info(f"the plot has been stored in {plot_filename}")
    return plot_filename