import sys
import pandas as pd


def main(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Find the minimum elapsed_time
    min_time = df['elapsed_time'].min()

    # Shift the elapsed_time so it starts from 0
    df['elapsed_time'] = df['elapsed_time'] - min_time

    # Save the updated DataFrame to a new CSV file
    df.to_csv(file_path, index=False)

    print(f"Elapsed time has been shifted and saved to {file_path}")


if __name__ == "__main__":
    main(sys.argv[1])