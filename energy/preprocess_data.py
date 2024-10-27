"""
This module receives as input a .csv file with 
a dataset that details the raw current consumption of
an ESP32 microcontroller over the active phase of
its duty cycle.

The dataset is formatted as follows:
Timestamp(ms),Current(uA),D0-D7

This module loads the .csv as a pandas dataframe and 
applies a series of transformations to the data in order.
Each function takes the df as input and returns the modified df.

The preprocessing steps are as follows:
1. Remove the last column (D0-D7)
2. Shift the timestamp column to start at 0
3. Convert the current to miliamperes
4. Convert the timestamp to seconds
5. Apply a rolling average to the current column for smoothing.
6. Save the preprocessed data to /data/preprocessed/<filename>.csv
"""

import pandas as pd
import sys
import os

INPUT_DIR = 'data/raw'
OUTPUT_DIR = 'data/preprocessed'

def preprocess_data(file_name):
    # Check if the file exists
    file_path = os.path.join(INPUT_DIR, file_name)
    if not os.path.exists(file_path):
        print(f'File {file_path} does not exist.')
        sys.exit(1)
    
    # Load CSV file into a pandas dataframe
    df = pd.read_csv(file_path)
    
    # 1. Remove the last column (D0-D7)
    df = df.iloc[:, :-1]
    
    # 2. Shift the timestamp column to start at 0
    df['Timestamp(ms)'] = df['Timestamp(ms)'] - df['Timestamp(ms)'].min()
    
    # 3. Convert the current to miliamperes
    df['Current(mA)'] = df['Current(uA)'] / 1000
    df.drop(columns=['Current(uA)'], inplace=True)
    
    # 4. Convert the timestamp to seconds
    df['Timestamp(s)'] = df['Timestamp(ms)'] / 1000
    df.drop(columns=['Timestamp(ms)'], inplace=True)
    
    # 5. Apply a rolling average to the current column for smoothing
    df['Current(mA)'] = df['Current(mA)'].rolling(window=10, min_periods=1).mean()
    
    # 6. Save the preprocessed data to /data/preprocessed/<filename>.csv
    df.to_csv(os.path.join(OUTPUT_DIR, file_name), index=False)
    
    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python preprocess_data.py <file_path>')
        sys.exit(1)
    
    file_path = sys.argv[1]
    preprocess_data(file_path)
    print('Data preprocessing complete.')


