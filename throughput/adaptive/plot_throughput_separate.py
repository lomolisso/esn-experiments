import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def compute_throughput(input_path, bin_size=1):
    # Load the CSV data
    df = pd.read_csv(input_path)

    # Compute the maximum time from the dataset
    max_time = df['elapsed_time'].max()

    # Create bins for the time intervals
    bins = np.arange(0, max_time + bin_size, bin_size)

    # Bin the data based on the elapsed_time column
    df['time_bin'] = pd.cut(df['elapsed_time'], bins=bins, right=False)

    # Calculate the throughput for each bin
    throughput = df.groupby('time_bin', observed=True)['length'].sum() * 8 / bin_size / 1024  # Convert to Kbps (bits to Kbits)

    # Handle missing intervals by reindexing with all bins and filling NaNs with 0
    throughput = throughput.reindex(pd.IntervalIndex.from_breaks(bins, closed='left'), fill_value=0)

    # Prepare data for plotting
    time_intervals = [interval.left for interval in throughput.index]
    throughput_values = throughput.values

    return time_intervals, throughput_values

def pad_data_centered(time1, values1, time2, values2):
    # Handle the case where one of the datasets is missing (all zero)
    if len(time1) == 0:
        time1, values1 = [0], [0]  # Default to zero if no data
    if len(time2) == 0:
        time2, values2 = [0], [0]  # Default to zero if no data

    # Find the length difference between the two sets
    len1, len2 = len(time1), len(time2)
    diff = abs(len1 - len2)

    if len1 < len2:
        # Data 1 is shorter; pad it
        pad_left = diff // 2
        pad_right = diff - pad_left
        padded_time1 = np.pad(time1, (pad_left, pad_right), 'constant', constant_values=(0, 0))
        padded_values1 = np.pad(values1, (pad_left, pad_right), 'constant', constant_values=(0, 0))
        padded_time2 = time2
        padded_values2 = values2
    else:
        # Data 2 is shorter; pad it
        pad_left = diff // 2
        pad_right = diff - pad_left
        padded_time2 = np.pad(time2, (pad_left, pad_right), 'constant', constant_values=(0, 0))
        padded_values2 = np.pad(values2, (pad_left, pad_right), 'constant', constant_values=(0, 0))
        padded_time1 = time1
        padded_values1 = values1

    # Ensure both time arrays are the same length and align them
    unified_time = np.arange(min(padded_time1[0], padded_time2[0]), max(padded_time1[-1], padded_time2[-1]) + 1)

    return unified_time, padded_values1, padded_values2

# File combinations for the plots, adjusted to exclude zero data files
file_combinations = [
    (25, 'gateway', None, 'cloud'),  # None indicates no data for 'cloud'
    (20, 'gateway', 5, 'cloud'),
    (15, 'gateway', 10, 'cloud'),
    (10, 'gateway', 15, 'cloud'),
    (5, 'gateway', 20, 'cloud'),
    (None, 'gateway', 25, 'cloud')  # None indicates no data for 'gateway'
]

# Create a figure with subplots
fig, axes = plt.subplots(2, 3, figsize=(18, 12), sharey=True)  # Changed to 2 rows, 3 columns

# Define colors with transparency
cloud_color = plt.cm.tab10.colors[0]
gateway_color = plt.cm.tab10.colors[1]

# Flatten axes array for easier iteration
axes = axes.flatten()

# Loop through each file combination and plot
for i, (gateway_num, gateway_source, cloud_num, cloud_source) in enumerate(file_combinations):
    # Check if the files exist and compute data if they do
    if gateway_num is not None:
        gateway_path = f'./gateway/data/{gateway_num}_{gateway_source}.csv'
        time_gateway, throughput_gateway = compute_throughput(gateway_path)
    else:
        time_gateway, throughput_gateway = [], []

    if cloud_num is not None:
        cloud_path = f'./cloud/data/{cloud_num}_{cloud_source}.csv'
        time_cloud, throughput_cloud = compute_throughput(cloud_path)
    else:
        time_cloud, throughput_cloud = [], []

    # Pad data to have equal lengths and be centered
    unified_time, padded_throughput_cloud, padded_throughput_gateway = pad_data_centered(
        time_cloud, throughput_cloud, time_gateway, throughput_gateway
    )

    # Plot the stacked histograms with stepfilled style
    axes[i].hist(
        [unified_time, unified_time], bins=len(unified_time), 
        weights=[padded_throughput_cloud, padded_throughput_gateway],
        label=['Cloud-based Inference', 'Gateway-based Inference'], 
        color=[cloud_color, gateway_color], stacked=True, 
        edgecolor='black', alpha=0.75, histtype='stepfilled', zorder=3
    )
    
    # Overlay with ustep style
    axes[i].hist(
        [unified_time, unified_time], bins=len(unified_time), 
        weights=[padded_throughput_cloud, padded_throughput_gateway],
        color=['black', "black"], stacked=True, histtype='step', linewidth=1.5, zorder=4
    )

    # Annotate the areas with text inside a box
    area_cloud = np.sum(padded_throughput_cloud)
    area_gateway = np.sum(padded_throughput_gateway)
    total_area = area_cloud + area_gateway

    # Adding a bounding box to the text
    bbox_props = dict(edgecolor='black', facecolor='white')
    
    # Annotate the areas with text inside a box
    axes[i].text(0.95, 0.95, f'Cloud: ~{area_cloud:.2f} Kb\nGateway: ~{area_gateway:.2f} Kb\nTotal: ~{total_area:.2f} Kb', 
        transform=axes[i].transAxes, fontsize=10, verticalalignment='top', horizontalalignment='right', bbox=bbox_props)

    axes[i].set_yticks(np.arange(0, max(axes[i].get_ylim()), 100))

    # Set axis labels and grid
    axes[i].set_xlabel('Time (seconds)')
    axes[i].grid(axis='y')
    if i % 3 == 0:  # Set y-label for the first column only
        axes[i].set_ylabel('Throughput (Kbps)')

# Add a legend with black border and color patch borders
legend_patches = [
    Patch(facecolor=cloud_color, edgecolor='black', label='Cloud-based Inference', linewidth=1.5, alpha=0.75),
    Patch(facecolor=gateway_color, edgecolor='black', label='Gateway-based Inference', linewidth=1.5, alpha=0.75)
]
fig.legend(handles=legend_patches, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2, edgecolor='black')

# Save the combined figure
plt.tight_layout()
plt.savefig('throughput_over_time_stacked_histograms.png')
plt.show()
