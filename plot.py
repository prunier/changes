# debug
import matplotlib.pyplot as plt
from collections import defaultdict

# # Créer un tableau en 3 dimensions basé sur defaultdict
# data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

# # Ajouter des valeurs au tableau (exemple)
# data[1][1][1] = 10
# data[1][1][2] = 20
# data[1][2][1] = 30
# data[2][1][1] = 40

# Calculer la somme des z par x et par y

def plot_my_3d_data(session_name:str, data:defaultdict):


    plot_filename = f"{session_name}.png"
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
    plt.show()

    # sauvegarder dans un fichier
    plt.savefig(plot_filename)