import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import itertools

SENSOR_NAME = "ESP32_AABBCC"
SENSOR_SLEEP_TIME = 10

# Set the Seaborn theme

def _load_data(input_path):
    # Get a list of CSV files in the folder
    csv_files = [f for f in os.listdir(input_path) if f.endswith('.csv') and f.replace('.csv', '').isdigit()]

    # Sort the files based on the number in the file name
    csv_files.sort(key=lambda x: int(x.replace('.csv', '')))

    # Load the data from the CSV files into an array of DataFrames
    node_counts = []
    dataframes = []

    for csv_file in csv_files:
        file_path = os.path.join(input_path, csv_file)
        df = pd.read_csv(file_path)

        node_counts.append(int(csv_file.replace('.csv', '')))

        # Ensure the required columns are present
        if 'sensor_name' not in df.columns or 'inference_latency' not in df.columns or 'registered_at' not in df.columns:
            raise ValueError(f"The input CSV file {csv_file} must contain 'sensor_name', 'inference_latency', and 'registered_at' columns")

        # Filter the DataFrame to only include the sensor of interest
        df = df[df['sensor_name'] == SENSOR_NAME]

        # Convert inference_latency entries from us to ms
        df['inference_latency'] = df['inference_latency'] / 1000

        # Sort by registered_at
        df = df.sort_values(by='registered_at').reset_index(drop=True)

        # Extract the node count from the file name
        node_count = int(csv_file.replace('.csv', ''))

        # Add a column for the node count to use in the plot
        df['node_count'] = node_count

        # Add the DataFrame to the list
        dataframes.append(df)

    return node_counts, dataframes

def plot_and_save_boxplot(dataframes, output_path):
    plt.figure(figsize=(12, 8))
    for df in dataframes:
        sns.boxplot(x='node_count', y='inference_latency', data=df, showfliers=True, linecolor='black', linewidth=1.5)

    # Set the title and labels
    plt.title('Inference Latency by Node Count')
    plt.xlabel('Nodes in the Network')
    plt.ylabel('Inference Latency (ms)')

    # Add grid
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Increase the number of ticks on the y-axis
    plt.gca().yaxis.set_major_locator(plt.MaxNLocator(nbins=12))

    # Save the plot to a file
    plt.savefig(os.path.join(output_path, f'latency_boxplot.png'))

def plot_and_save_lineplot(labels, dataframes, output_path):
    markers = ['o', 's', 'd', 'p', 'h', 'X']  # List of different markers
    colors = itertools.cycle(plt.cm.tab10.colors)  # Use a color cycle

    # Create a 2x3 grid of subplots
    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(22, 6))
    axes = axes.flatten()  # Flatten to easily iterate over subplots

    for i, (label, df) in enumerate(zip(labels, dataframes)):
        # Ensure the dataframe has at least 100 rows
        df = df.head(100)
        
        # Convert index to time in minutes
        df['time'] = pd.to_timedelta(df.index * SENSOR_SLEEP_TIME, unit='s')
        df.set_index('time', inplace=True)
        
        # Get the next color in the cycle
        color = next(colors)
        
        # Plot the line and add markers with black borders and filled color
        ax = axes[i]
        ax.plot(df.index.total_seconds(), df['inference_latency'], 
                marker=markers[i % len(markers)], label=label, linestyle='-',
                color=color, markersize=5, markerfacecolor=color, 
                markeredgewidth=1, markeredgecolor='black')
        
        # Set x-axis and y-axis labels conditionally
        if i // 3 == 1:  # Only for the bottom row
            ax.set_xlabel('Elapsed Time [s]')
        if i % 3 == 0:  # Only for the first column
            ax.set_ylabel('Inference Latency [ms]')
        
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=12))
        ax.legend(loc='upper right')

    plt.tight_layout()
    
    # Save the plot to a file
    plt.savefig(os.path.join(output_path, f'latency_boxplot.png'))

def main(input_path, output_path):
    # Load the data from the CSV files into an array of DataFrames
    node_counts, dataframes = _load_data(input_path)

    # First figure: Boxplot of inference latency by node count
    plot_and_save_boxplot(dataframes, output_path)
    
    # Second figure: Line plots of inference latency over time
    labels = [f'{node_count} Nodes' if node_count != 1 else f'{node_count} Node' for node_count in node_counts]
    plot_and_save_lineplot(labels, dataframes, output_path)

    # Show the plots
    plt.show()

def main(input_path, output_path):
    # Load the data from the CSV files into an array of DataFrames
    node_counts, dataframes = _load_data(input_path)

    # First figure: Boxplot of inference latency by node count
    plot_and_save_boxplot(dataframes, output_path)
    
    # Second figure: Line plots of inference latency over time
    labels = [f'{node_count} Nodes' if node_count != 1 else f'{node_count} Node' for node_count in node_counts]
    plot_and_save_lineplot(labels, dataframes, output_path)

    # Show the plots
    plt.show()
    
if __name__ == "__main__":
    input_path = sys.argv[1]  # Path to the input directory
    output_path = sys.argv[2]  # Path to the output directory
    main(input_path, output_path)
