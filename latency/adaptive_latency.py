import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch
import os

SENSOR_NAME = "ESP32_8F7400"
SENSOR_SLEEP_TIME = 10
NODE_COUNT_TO_PLOT = 25  # The node count to plot

# Set the Seaborn theme
sns.set_theme(style="whitegrid")

def _load_data(input_path):
    df = pd.read_csv(input_path)

    # Ensure the required columns are present
    if 'sensor_name' not in df.columns or 'inference_latency' not in df.columns or 'registered_at' not in df.columns:
        raise ValueError(f"The input CSV file must contain 'sensor_name', 'inference_latency', and 'registered_at' columns")

    # Filter the DataFrame to only include the sensor of interest
    df = df[df['sensor_name'] == SENSOR_NAME]

    # Convert inference_latency entries from us to ms
    # Sort by registered_at
    df = df.sort_values(by='registered_at').reset_index(drop=True)

    return df

def plot_single_line(df, output_path):
    # Convert index to time in seconds
    df['time'] = pd.to_timedelta(df.index * SENSOR_SLEEP_TIME, unit='s')
    df.set_index('time', inplace=True)

    # Create the figure and axis only once
    plt.figure(figsize=(10, 6))

    # Define a function to plot line segments for each contiguous interval
    def plot_segments(df, layer_colors):
        start_idx = 0
        for i in range(1, len(df)):
            if df['inference_layer'].iloc[i] != df['inference_layer'].iloc[start_idx]:
                segment_df = df.iloc[start_idx:i]
                layer = df['inference_layer'].iloc[start_idx]
                color = layer_colors[layer]
                plt.plot(segment_df.index.total_seconds(), segment_df['inference_latency'], 
                         color=color, linewidth=2, zorder=3)
                start_idx = i
        # Plot the last segment
        segment_df = df.iloc[start_idx:]
        layer = df['inference_layer'].iloc[start_idx]
        color = layer_colors[layer]
        plt.plot(segment_df.index.total_seconds(), segment_df['inference_latency'], 
                 color=color, linewidth=2, zorder=3)

    # Define colors for each inference layer
    inference_layers = {"InferenceLayer.SENSOR": "Sensor", "InferenceLayer.GATEWAY": "Gateway", "InferenceLayer.CLOUD": "Cloud"}
    layer_colors = dict(zip(inference_layers.keys(), sns.color_palette("tab10", len(inference_layers))))

    # Plot the main line for reference
    plt.plot(df.index.total_seconds(), df['inference_latency'], color='black', linewidth=1, zorder=2, linestyle='--', alpha=0.8)

    # Plot line segments for each interval where an inference layer is selected
    plot_segments(df, layer_colors)
    
    layer_colors_list = ["tab:blue", "tab:orange", "tab:green"]

    # Plot average latency line for each inference layer
    for layer, color in zip(df['inference_layer'].unique(), layer_colors_list):
        layer_df = df[df['inference_layer'] == layer]
        mean_latency = layer_df['inference_latency'].mean()
        plt.axhline(y=mean_latency, color=color, linestyle='--', linewidth=1.5, alpha=0.7)
        plt.text(x=0.01, y=mean_latency+15, s=f'{mean_latency:.2f} ms', 
                 color=color, fontsize=12, va='bottom', ha='left',
                 transform=plt.gca().get_yaxis_transform(), zorder=15)
    
    # Set labels
    plt.xlabel('Elapsed Time (s)')
    plt.ylabel('Inference Latency (ms)')
    plt.grid(axis="x")

    # Define legend patches
    legend_elements = [
        Patch(facecolor='tab:blue', edgecolor='black', label='Sensor-based Inference'),
        Patch(facecolor='tab:orange', edgecolor='black', label='Gateway-based Inference'),
        Patch(facecolor='tab:green', edgecolor='black', label='Cloud-based Inference')
    ]

    # Add legend at the bottom of the figure
    plt.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=3, edgecolor='black')
    
    # Adjust layout to make room for the legend
    plt.tight_layout()

    # Save the plot to a file
    plt.savefig(output_path, bbox_inches='tight')
    plt.show()

def main():
    input_path = os.path.join("adaptive", "data", "latencies.csv")
    output_path = os.path.join("plots", "adaptive_inference.png")

    # Create the plots directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Load the data for the specified node count
    df = _load_data(input_path)

    # Plot and save the single line chart for the specified node count
    plot_single_line(df, output_path)

if __name__ == "__main__":
    main()
