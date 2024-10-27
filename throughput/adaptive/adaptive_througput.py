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
    (25, 'gateway', None, 'cloud'),  # n_g=25, n_c=0
    (20, 'gateway', 5, 'cloud'),     # n_g=20, n_c=5
    (15, 'gateway', 10, 'cloud'),    # n_g=15, n_c=10
    (10, 'gateway', 15, 'cloud'),    # n_g=10, n_c=15
    (5, 'gateway', 20, 'cloud'),     # n_g=5, n_c=20
    (None, 'gateway', 25, 'cloud')   # n_g=0, n_c=25
]

# Create a figure with subplots
fig, axes = plt.subplots(2, 3, figsize=(18, 12), sharey=False)  # Changed sharey to False

# Get tab colors from matplotlib
tab_colors = plt.cm.tab10.colors
num_plots = len(file_combinations)
if num_plots > len(tab_colors):
    # If more plots than available tab colors, extend the color list
    tab_colors = tab_colors * ((num_plots // len(tab_colors)) + 1)
    
# Flatten axes array for easier iteration
axes = axes.flatten()

# Prepare legend labels
legend_labels = []
for gateway_num, _, cloud_num, _ in file_combinations:
    n_g = gateway_num if gateway_num is not None else 0
    n_c = cloud_num if cloud_num is not None else 0
    legend_labels.append(f"$n_{{g}}={n_g}, \, n_{{c}}={n_c}$")

# Initialize list to keep track of plot colors for the legend
plot_colors = []

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

    # Sum the throughput values
    total_throughput = padded_throughput_cloud + padded_throughput_gateway

    # Choose a color for this subplot
    plot_color = tab_colors[i]
    plot_colors.append(plot_color)

    # Plot the single histogram
    axes[i].hist(
        unified_time, bins=len(unified_time), 
        weights=total_throughput,
        color=plot_color, edgecolor='black', alpha=0.75, histtype='stepfilled', zorder=3
    )
    
    # Overlay with step style for better edge visibility
    axes[i].hist(
        unified_time, bins=len(unified_time), 
        weights=total_throughput,
        color='black', histtype='step', linewidth=1.5, zorder=4
    )

    # Annotate the areas with text inside a box
    D_c = np.sum(padded_throughput_cloud)
    D_g = np.sum(padded_throughput_gateway)
    D_total = D_c + D_g

    # Adding a bounding box to the text
    bbox_props = dict(edgecolor='black', facecolor='white')

    # Annotate the areas with text inside a box
    axes[i].text(0.95, 0.95, f'$D_{{c}} = {D_c:.2f}$ Kb\n$D_{{g}} = {D_g:.2f}$ Kb\n$D_{{total}} = {D_total:.2f}$ Kb', 
        transform=axes[i].transAxes, fontsize=10, verticalalignment='top', horizontalalignment='right', bbox=bbox_props)

    # Set axis labels and grid
    if i >= 3:
        axes[i].set_xlabel('Time (seconds)')
    axes[i].grid(axis='y')
    
    # Set y-label for the first column only
    if i % 3 == 0:  
        axes[i].set_ylabel('Throughput (Kbps)')
    
    # Adjust y-axis limits to add padding
    y_max = axes[i].get_ylim()[1]
    axes[i].set_ylim(0, y_max * 1.3)  # Add 10% padding on top

# Add a legend with patches corresponding to each subplot
legend_patches = [Patch(facecolor=plot_colors[i], alpha=0.75, edgecolor='black', label=legend_labels[i]) for i in range(num_plots)]
fig.legend(handles=legend_patches, loc='lower center', bbox_to_anchor=(0.5, 0.02), ncol=6)  # Changed ncol to 6 for a single row

# Adjust layout to make room for the legend
plt.tight_layout(rect=[0, 0.05, 1, 1])  # Adjusted rect to provide more space for the legend

# Save the combined figure
plt.savefig('throughput_over_time_sum_histograms.png')
plt.show()
