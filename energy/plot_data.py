"""
This module receives as input a .csv file with 
a dataset that details the preprocessed current consumption of
an ESP32 microcontroller over the active phase of
its duty cycle.

The dataset is formatted as follows:
Current(mA),Timestamp(s) 

This module loads the .csv as a pandas dataframe and
creates a plot of the current consumption over time.
"""

from matplotlib.patches import Patch
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import os

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

INPUT_DIR = 'data/preprocessed'
OUTPUT_DIR = 'fig'

# Voltage is a global variable
VOLTAGE = 3.7

# Function to calculate energy (mJ) from the area under the curve
def calculate_energy(df, start_time, end_time):
    # Filter the dataframe within the specified time interval
    sub_df = df[(df['Timestamp(s)'] >= start_time) & (df['Timestamp(s)'] <= end_time)]
    # Use trapezoidal rule to calculate the area under the curve (Current * Voltage)
    energy = np.trapz(sub_df['Current(mA)'] * 1e-3 * VOLTAGE, sub_df['Timestamp(s)']) * 1e3  # mJ
    return energy

def plot_figure(file_name, insets, ax, color='tab:blue'):
    """
    Plots the current consumption over time with insets on the provided axes.

    Parameters:
    - file_name (str): Name of the CSV file to plot.
    - insets (dict): Dictionary containing inset configurations for the file.
    - ax (matplotlib.axes.Axes): The axes on which to plot.
    """
    # 0. Check if the file exists
    file_path = os.path.join(INPUT_DIR, file_name)
    if not os.path.exists(file_path):
        print(f'File {file_path} does not exist.')
        sys.exit(1)

    # 1. Load CSV file into a pandas dataframe
    df = pd.read_csv(file_path)

    # 2. Plot the current consumption over time on the given axes
    ax.plot(df['Timestamp(s)'], df['Current(mA)'], label="Current Consumption", zorder=2, color=color)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Current (mA)')
    # ax.grid(axis='y', zorder=1)

    # 3. Create insets from the provided dictionary
    for inset_key, inset_info in insets.items():
        # Extract inset details
        inset_start = inset_info['inset_start']
        inset_end = inset_info['inset_end']
        inset_pos = inset_info['position']
        inset_zorder = inset_info['zorder']
        highlight_start = inset_info['highlight_start']
        highlight_end = inset_info['highlight_end']
        mark_inset_params = inset_info['mark_inset_params']

        # Create an inset axis using axes coordinates
        ax_inset = ax.inset_axes(
            [inset_pos[0], inset_pos[1], 0.25, 0.3],
            transform=ax.transAxes,
            zorder=inset_zorder,
        )
        ax_inset.set_title(inset_key, fontsize=10)

        # Plot the zoomed region on the inset
        ax_inset.plot(df['Timestamp(s)'], df['Current(mA)'], label=f'Inset {inset_key}', zorder=inset_zorder-1, color=color)
        ax_inset.set_xlim(inset_start, inset_end)

        # **Set y-limits based on the inset data with padding**
        sub_df_inset = df[(df['Timestamp(s)'] >= inset_start) & (df['Timestamp(s)'] <= inset_end)]
        y_min, y_max = sub_df_inset['Current(mA)'].min(), sub_df_inset['Current(mA)'].max()

        # Add padding to y-axis limits for better visualization
        y_padding = (y_max - y_min) * 0.1 if y_max != y_min else 1  # Avoid zero padding if y_min == y_max
        ax_inset.set_ylim(
            y_min - y_padding if y_max < 100 else .85 * y_min,
            y_max + y_padding if y_max < 150 else 1.05 * y_max
        )
        ax_inset.set_xticks([])
        ax_inset.set_yticks([])

        # Highlight the sub-interval inside the inset
        sub_df_highlight = df[(df['Timestamp(s)'] >= highlight_start) & (df['Timestamp(s)'] <= highlight_end)]
        ax_inset.fill_between(sub_df_highlight['Timestamp(s)'], sub_df_highlight['Current(mA)'], color=color, alpha=0.5, zorder=inset_zorder-1)

        # Highlight the sub-interval in the main plot
        ax.fill_between(sub_df_highlight['Timestamp(s)'], sub_df_highlight['Current(mA)'], color=color, alpha=0.5, zorder=1)

        # Calculate and display the energy (mJ)
        energy = calculate_energy(df, highlight_start, highlight_end)
        energy_text = (f'{energy:.2f} mJ | {(highlight_end - highlight_start) * 1e3:.2f} ms'
                       if energy < 1000
                       else f'{energy/1000:.2f} J | {(highlight_end - highlight_start):.2f} s')
        ax_inset.text(
            0.5, -0.1, energy_text,
            transform=ax_inset.transAxes,
            ha='center',
            va='top',
            fontsize=10,
            color='black',
            bbox=dict(facecolor='white', zorder=inset_zorder+1)
        )

        # Mark the inset with zoom lines
        mark_inset(ax, ax_inset, fc="none", ec="0", zorder=2, linewidth=0.65, **mark_inset_params)

    # 4. Adjust the main plot's limits
    ax.set_xlim(df['Timestamp(s)'].min(), df['Timestamp(s)'].max())
    ax.set_ylim(df['Current(mA)'].min(), 2 * df['Current(mA)'].max())

def main():
    # Example insets dictionary
    insets = {
        'inference_cycle.csv': {
            'Read Sample from BMI270 (I2C)': {
                'inset_start': 12.015,
                'inset_end': 12.075,
                'position': [0.15, 0.6],  # Relative position in figure coordinates
                'zorder': 3,
                'highlight_start': 12.035,
                'highlight_end': 12.055,
                'mark_inset_params': {'loc1': 3, 'loc2': 1},
            },
            'On-device Inference (TFLM)': {
                'inset_start': 21.31 - 0.05,
                'inset_end': 21.335 + 0.05,
                'position': [0.55, 0.6],  # Relative position in figure coordinates
                'zorder': 3,
                'highlight_start': 21.3152,
                'highlight_end': 21.3292,
                'mark_inset_params': {'loc1': 3, 'loc2': 1},
            },
            
        },
        'offload_cycle.csv': {
            'Read Sample from BMI270 (I2C)': {
                'inset_start': 12.018,
                'inset_end': 12.08,
                'position': [0.05, 0.6],  # Relative position in figure coordinates
                'zorder': 3,
                'highlight_start': 12.039,
                'highlight_end': 12.059,
                'mark_inset_params': {'loc1': 3, 'loc2': 1},
            },
            'Signal Compression (Zlib)': {
                'inset_start': 21.21,
                'inset_end': 21.47,
                'position': [0.375, 0.6],
                'zorder': 3,
                'highlight_start': 21.315,
                'highlight_end': 21.365,
                'mark_inset_params': {'loc1': 3, 'loc2': 1},
            },
            'Turn On Radio + Transmit': {
                'inset_start': 26.3,
                'inset_end': 31,
                'position': [0.7, 0.6],
                'zorder': 3,
                'highlight_start': 26.3,
                'highlight_end': 31,
                'mark_inset_params': {'loc1': 3, 'loc2': 1},
            }
        }
    }

    # List of files to plot
    files_to_plot = ['inference_cycle.csv', 'offload_cycle.csv']

    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Create a figure with two subplots arranged vertically
    fig, axs = plt.subplots(nrows=2, ncols=1, figsize=(9, 9), sharex=False)

    # Iterate over each file and its corresponding subplot
    colors = ['tab:blue', 'tab:orange']
    for ax, file_name, color in zip(axs, files_to_plot, colors):
        # Retrieve insets for the current file
        file_insets = insets.get(file_name, {})
        # Plot the figure on the current subplot
        plot_figure(file_name, file_insets, ax, color)
    
    # Remove x-axis label for the top subplot
    axs[0].set_xlabel('') 
    labels = ['Onboard Inference Cycle', 'Offboard Inference Cycle']
    legend_patches = [
        Patch(facecolor=color, edgecolor='black', label=label, linewidth=1.5, alpha=0.75)
        for color, label in zip(colors, labels)
    ]

    # Create a single legend for all subplots closer to the third row
    plt.legend(legend_patches, labels, loc='upper center', ncol=3, bbox_to_anchor=(0.5, -0.15),
            frameon=True, fancybox=False, edgecolor='black')

    # Adjust layout for better spacing
    plt.tight_layout()

    # Save the combined figure
    output_file = 'combined_plot.png'
    plt.savefig(os.path.join(OUTPUT_DIR, output_file))
    print(f'Combined plot saved to {os.path.join(OUTPUT_DIR, output_file)}')

if __name__ == '__main__':
    main()

