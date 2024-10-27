import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def plot_throughput_vs_time(input_path, label, ax, color='blue', limits=[]):
    # Load the CSV data
    df = pd.read_csv(input_path)

    # Define the bin size (in seconds)
    bin_size = 1

    # Compute the maximum time from the dataset
    max_time = df['elapsed_time'].max()

    # Create bins for the time intervals
    bins = np.arange(0, max_time + bin_size, bin_size)

    # Bin the data based on the elapsed_time column
    df['time_bin'] = pd.cut(df['elapsed_time'], bins=bins, right=False)

    # Calculate the throughput for each bin
    throughput = df.groupby('time_bin')['length'].sum() * 8 / bin_size / 1024  # Convert to Kbps (bits to Kbits)

    # Handle missing intervals by reindexing with all bins and filling NaNs with 0
    throughput = throughput.reindex(pd.IntervalIndex.from_breaks(bins, closed='left'), fill_value=0)

    # Reset index for a cleaner output
    throughput = throughput.reset_index()
    throughput.columns = ['Time Interval', 'Throughput (Kbps)']

    # Prepare data for plotting
    time_intervals = [interval.left for interval in throughput['Time Interval']]
    throughput_values = throughput['Throughput (Kbps)']

    # Plot the throughput over time on the provided axis with the specified color
    ax.hist(time_intervals, bins=bins, weights=throughput_values, color=color, alpha=0.75, histtype='stepfilled', zorder=3)
    ax.hist(time_intervals, bins=bins, weights=throughput_values, color="black", histtype='step', zorder=4, linewidth=1)
    
    # x-label only on the last subplot
    if ax == axs[1]:
        ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('Throughput (Kbps)')
    ax.grid(axis='y')

    # For each pair (x_0, x_1) in limits, put vertical lines on the plot
    for (x_0, x_1) in limits:
        ax.axvline(x=x_0, color='gray', linestyle='--', linewidth=1.5, zorder=5)
        ax.axvline(x=x_1, color='gray', linestyle='--', linewidth=1.5, zorder=5)

    # For each pair (x_0, x_1) in limits, compute the area under the histogram between x_0 and x_1
    for (x_0, x_1) in limits:
        # Find the indices of the bins that fall within the range [x_0, x_1)
        relevant_bins = throughput[(throughput['Time Interval'].apply(lambda x: x.left >= x_0 and x.right <= x_1))]
        
        # Compute the area (sum of throughput values in the specified range)
        area = relevant_bins['Throughput (Kbps)'].sum()
        
        # Compute the middle of the interval to place the text
        mid_point = ((x_0 + x_1) / 2)
        
        # Annotate the area on the plot
        ax.text(mid_point, ax.get_ylim()[1] * 0.25, f'~{area:.0f} Kb', ha='center', va='center', fontsize=10, color='black')

    ax.legend()


# Paths to the CSV files
cloud_path = './cloud/data/cloud.csv'
gateway_path = './gateway/data/gateway.csv'

# Create a figure with 2 subplots in the left column and 3 subplots in the right column
fig, axs = plt.subplots(2, 1, figsize=(12, 9))

# Plot each CSV file on a separate pair of subplots with specified colors
color_blue = plt.cm.tab10.colors[0]
color_orange = plt.cm.tab10.colors[1]
color_green = plt.cm.tab10.colors[2]

labels = ['Cloud-based Inference', 'Gateway-based Inference']
limits = [(0, 15), (29, 46), (60, 76)]
plot_throughput_vs_time(cloud_path, labels[0], axs[0], color=color_blue, limits=limits)
plot_throughput_vs_time(gateway_path, labels[1], axs[1], color=color_orange, limits=limits)

legend_patches = [
    Patch(facecolor=color, edgecolor='black', label=label, linewidth=1.5, alpha=0.75)
    for color, label in zip([color_blue, color_orange, color_green], labels)
]


# Create a single legend for all subplots closer to the third row
legend = fig.legend(legend_patches, labels, loc='upper center', ncol=3, bbox_to_anchor=(0.5, 0.1),
                    frameon=True, fancybox=False, edgecolor='black')
                    
# Adjust layout to make the plot more compact
plt.tight_layout(rect=[0, 0.12, 1, 1])  # Adjust rect to leave space for the legend

# Save the combined figure
plt.savefig('throughput_over_time.png', bbox_inches='tight')
plt.show()

