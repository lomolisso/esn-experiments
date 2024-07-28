import pandas as pd
import numpy as np
import json
import os
from config import SEQ_LENGTH, PATH_TO_DATASET, LABELS

# --- Accelerometer Constants ---
G_MS2 = 9.80665
MAX_INT_VALUE_SENSOR = 32768.0
ACC_RAW_TO_MS2 = (G_MS2 / MAX_INT_VALUE_SENSOR)
SENSOR_ACC_RANGE = 2 # 8g

# --- Gyroscope Constants ---
SENSOR_GYR_RANGE = 250.0
PI = 3.14159265359
GYR_RAW_TO_RADS = (PI / 180.0) / MAX_INT_VALUE_SENSOR

# --- Converters ---
convert_raw_acc_to_ms2 = lambda raw: (pow(2, SENSOR_ACC_RANGE + 1) * ACC_RAW_TO_MS2) * raw
convert_raw_gyr_to_rads = lambda raw: SENSOR_GYR_RANGE * GYR_RAW_TO_RADS * raw


class MeasurementHandler:
    def _init_sequences_and_labels(self):
        with open(PATH_TO_DATASET + 'column_names.json') as f:
            column_names = json.load(f)

        labeled_data_frames = {l: [] for l in LABELS.values()}
        for filename in os.listdir(PATH_TO_DATASET):
            for label in LABELS.values():
                if filename.startswith(str(label)) and filename.endswith('.csv'):
                    df = pd.read_csv(PATH_TO_DATASET + filename, names=column_names, sep=';')
                    
                    # Convert the timestamp column to a datetime object
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    # Create a mask for rows where acc_x, acc_y, and acc_z are all 0
                    mask_acc_zero = (df['acc_x'] == 0) & (df['acc_y'] == 0) & (df['acc_z'] == 0)

                    # Create a mask for rows where gyro_x, gyro_y, and gyro_z are all 0
                    mask_gyro_zero = (df['gyro_x'] == 0) & (df['gyro_y'] == 0) & (df['gyro_z'] == 0)

                    # Combine the masks to identify rows where either condition is true
                    mask_either_zero = mask_acc_zero | mask_gyro_zero

                    # Filter out the rows from the DataFrame
                    df = df[~mask_either_zero]

                    # Convert the raw accelerometer data to m/s^2
                    df['acc_x'] = df['acc_x'].apply(convert_raw_acc_to_ms2).astype("float32")
                    df['acc_y'] = df['acc_y'].apply(convert_raw_acc_to_ms2).astype("float32")
                    df['acc_z'] = df['acc_z'].apply(convert_raw_acc_to_ms2).astype("float32")

                    # Convert the raw gyroscope data to rad/s
                    df['gyro_x'] = df['gyro_x'].apply(convert_raw_gyr_to_rads).astype("float32")
                    df['gyro_y'] = df['gyro_y'].apply(convert_raw_gyr_to_rads).astype("float32")
                    df['gyro_z'] = df['gyro_z'].apply(convert_raw_gyr_to_rads).astype("float32")
                    
                    labeled_data_frames[label].append(df)

        dataframes = {label: pd.concat(data_frames) for label, data_frames in labeled_data_frames.items()}

        # crop dataframes to a number of rows that is a multiple of SEQ_LENGTH
        for label, data in dataframes.items():
            dataframes[label] = data.iloc[:len(data) - len(data) % SEQ_LENGTH]

        sequences = []
        labels = []
        # Create sequences and labels
        for label, data in dataframes.items():
            for i in range(0, len(data), SEQ_LENGTH):
                seq = data.iloc[i:i + SEQ_LENGTH]
                sequences.append(seq[['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z']].values)
                labels.append(label)
        
        self.sequences, self.labels = np.array(sequences), np.array(labels)

        # shuffle sequences and labels the same way
        _zip_sequences_labels = list(zip(self.sequences, self.labels))
        np.random.shuffle(_zip_sequences_labels)
        _sequences, _labels = zip(*_zip_sequences_labels)

        self.sequences, self.labels = np.array(_sequences), np.array(_labels)

    def __init__(self) -> None:
        self.counter = 0
        self._init_sequences_and_labels()

    def sequence(self):
        if self.counter >= len(self.sequences):
            self.counter = 0

        seq = self.sequences[self.counter]
        label = self.labels[self.counter]
        self.counter += 1

        return label, seq
