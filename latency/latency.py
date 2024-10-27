import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch

SENSOR_NAME = "ESP32_8F7400"
sns.set_theme(style="whitegrid")

def _load_data(input_path):
    # Get a list of CSV files in the folder
    csv_files = [f for f in os.listdir(input_path) if f.endswith('.csv') and f.replace('.csv', '').isdigit()]

    # Sort the files based on the number in the file name
    csv_files.sort(key=lambda x: int(x.replace('.csv', '')))

    # Load the data from the CSV files into an array of DataFrames
    node_counts = []
    dataframes = []

    for csv_file in csv_files:
        print(f"Loading data from {csv_file}")
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

def plot_and_save_boxplot(cloud_df, gateway_df, sensor_df, output_path):
    fig, axes = plt.subplots(3, 1, figsize=(12, 18), sharex=True)

    sns.boxplot(linecolor='black', linewidth=1.5, x='node_count', y='inference_latency', data=sensor_df, ax=axes[0], showfliers=False, color='tab:blue')
    axes[0].set_ylabel('Inference Latency (ms)')
    axes[0].set_xlabel('')
    axes[0].grid(True, which='both', linestyle='--', linewidth=0.5)

    sns.boxplot(linecolor='black', linewidth=1.5, x='node_count', y='inference_latency', data=gateway_df, ax=axes[1], showfliers=False, color='tab:orange')
    axes[1].set_ylabel('Inference Latency (ms)')
    axes[1].set_xlabel('')
    axes[1].grid(True, which='both', linestyle='--', linewidth=0.5)

    sns.boxplot(linecolor='black', linewidth=1.5, x='node_count', y='inference_latency', data=cloud_df, ax=axes[2], showfliers=False, color='tab:green')
    axes[2].set_ylabel('Inference Latency (ms)')
    axes[2].set_xlabel('WSN Node Count')
    axes[2].grid(True, which='both', linestyle='--', linewidth=0.5)


    # Add legend at the bottom of the figure
    legend_elements = [
        Patch(facecolor='tab:blue', edgecolor='black', label='Sensor-based Inference'),
        Patch(facecolor='tab:orange', edgecolor='black', label='Gateway-based Inference'),
        Patch(facecolor='tab:green', edgecolor='black', label='Cloud-based Inference')
    ]
    fig.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 0), ncol=3, edgecolor='black')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)  # Adjust bottom to make space for the legend
    plt.savefig(os.path.join(output_path, 'latency_boxplot.png'), bbox_inches='tight')
    plt.show()

def main():
    cloud_path = "cloud/data"
    gateway_path = "gateway/data"
    sensor_path = "sensor/data"
    output_path = 'plots'

    # Create output directory if it does not exist
    os.makedirs(output_path, exist_ok=True)

    _, cloud_dataframes = _load_data(cloud_path)
    _, gateway_dataframes = _load_data(gateway_path)
    _, sensor_dataframes = _load_data(sensor_path)

    # Concatenate dataframes
    cloud_df = pd.concat(cloud_dataframes, ignore_index=True)
    cloud_df['type'] = 'cloud'

    gateway_df = pd.concat(gateway_dataframes, ignore_index=True)
    gateway_df['type'] = 'gateway'

    sensor_df = pd.concat(sensor_dataframes, ignore_index=True)
    sensor_df['type'] = 'sensor'

    # Generate the plot
    plot_and_save_boxplot(cloud_df, gateway_df, sensor_df, output_path)

if __name__ == "__main__":
    main()
