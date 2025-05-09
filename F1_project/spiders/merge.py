import pandas as pd
import os
import glob # To easily find all CSV files

# --- Configuration ---
# Directory where the individual CSV files (e.g., f1_2024-2024_race.csv) are stored
INPUT_DIR = "f1_results_by_type_simple"

# Name for the final merged CSV file
OUTPUT_FILENAME = "f1_data.csv"
# --- End Configuration ---

def merge_csv_files(input_directory, output_file):
    """
    Finds all CSV files in the input directory, merges them,
    and saves the combined data to the output file.
    """
    # Create the pattern to find all CSV files in the input directory
    csv_pattern = os.path.join(input_directory, "*.csv")
    csv_files = glob.glob(csv_pattern) # Get a list of all matching file paths

    if not csv_files:
        print(f"No CSV files found in directory: {input_directory}")
        return

    print(f"Found {len(csv_files)} CSV files to merge:")
    # for f in csv_files: # Optional: print filenames being merged
    #     print(f"- {os.path.basename(f)}")

    # List to hold DataFrames from each file
    all_dataframes = []

    # Read each CSV file into a pandas DataFrame
    for filename in csv_files:
        try:
            # Check if file is empty before reading
            if os.path.getsize(filename) > 0:
                 print(f"Reading: {os.path.basename(filename)}...")
                 df = pd.read_csv(filename, low_memory=False) # low_memory=False can help with mixed types
                 all_dataframes.append(df)
            else:
                 print(f"Skipping empty file: {os.path.basename(filename)}")
        except pd.errors.EmptyDataError:
             print(f"Skipping empty file (pandas read error): {os.path.basename(filename)}")
        except Exception as e:
            print(f"Error reading {os.path.basename(filename)}: {e}")

    if not all_dataframes:
        print("No dataframes were successfully read. Merged file not created.")
        return

    # Concatenate all DataFrames into one
    print("\nConcatenating dataframes...")
    # ignore_index=True creates a new index for the combined DataFrame
    # sort=False attempts to keep original column order where possible
    merged_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
    print(f"Total rows in merged data: {len(merged_df)}")

    # Save the merged DataFrame to a new CSV file
    try:
        print(f"Saving merged data to: {output_file}...")
        merged_df.to_csv(output_file, index=False, encoding='utf-8') # index=False prevents writing pandas index
        print("Successfully saved merged file.")
    except Exception as e:
        print(f"Error saving merged file {output_file}: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    print("--- Starting CSV Merge Script ---")
    # Check if input directory exists
    if not os.path.isdir(INPUT_DIR):
        print(f"ERROR: Input directory '{INPUT_DIR}' not found.")
        print("Please ensure the directory exists and contains the CSV files from the scraper.")
    else:
        merge_csv_files(INPUT_DIR, OUTPUT_FILENAME)
    print("--- CSV Merge Script Finished ---")