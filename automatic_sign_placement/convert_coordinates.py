import pandas as pd
import os
import glob
import geopandas as gpd
from pyproj import CRS, Transformer


def convert_coordinates(meshcode_list: list, latitude0: float, longitude0: float, db_folder: str):
    # Configure directories based on db_folder
    db_base = db_folder
    sign_input_dir = os.path.join(db_base, 'SHAPE', '25K')
    os.makedirs(sign_input_dir, exist_ok=True)
    sign_output_dir = os.path.join(db_base, 'CSV')
    os.makedirs(sign_output_dir, exist_ok=True)

    # Set projection using EPSG (replace Proj)
    from pyproj import CRS, Transformer  # Add import if not already at the top
    src_srs = CRS.from_epsg(4612)  # JGD2000 geographic
    dst_srs = CRS.from_epsg(6676)  # JGD2011 planar zone VI (default)
    transformer = Transformer.from_crs(src_srs, dst_srs, always_xy=False)  # Always use (lat, lon)

    # Calculate planar coordinates of the origin (latitude0, longitude0) once
    origin_xy = transformer.transform(latitude0, longitude0)  # Input: (lat, lon)
    origin_x_swapped = origin_xy[1]  # Swap according to LinkData.py: (x_planar, y_planar) → (y, x)
    origin_y_swapped = origin_xy[0]

    processed_dfs = []

    for meshcode in meshcode_list:
        # File paths based on meshcode
        os.makedirs(os.path.join(sign_output_dir, meshcode), exist_ok=True)
        dbf_file = os.path.join(sign_input_dir, meshcode, f'{meshcode}_TOLLMS_SIGN.dbf')
        csv_file = os.path.join(sign_output_dir, meshcode, f'{meshcode}_TOLLMS_SIGN.csv')
        output_file = os.path.join(sign_output_dir, meshcode, f'{meshcode}_TOLLMS_SIGN_processed.csv')

        # Step 1: Convert .dbf to .csv if necessary
        if not os.path.exists(csv_file) and os.path.exists(dbf_file):
            print(f"Converting .dbf to .csv: {dbf_file}")
            try:
                data = gpd.read_file(dbf_file)
                data.to_csv(csv_file, index=False)
                print(f"Successfully converted .dbf to .csv: {csv_file}")
            except Exception as e:
                print(f"Error converting .dbf to .csv: {e}")
                continue

        # Step 2: Read CSV
        print(f"Reading file: {csv_file}")
        if not os.path.exists(csv_file):
            print(f"CSV file not found: {csv_file}")
            continue

        df = pd.read_csv(csv_file)

        # Convert keido/ido → Longitude/Latitude
        if 'signkeido' in df.columns and 'signido' in df.columns:
            df['Longitude'] = df['signkeido'] / 3600000.0
            df['Latitude'] = df['signido'] / 3600000.0
        else:
            print("signkeido/signido not found; expecting Longitude/Latitude to exist.")

        # Add X1, Y1 (local planar coordinates)
        if 'Longitude' in df.columns and 'Latitude' in df.columns:
            def latlon_to_xy(row):
                # Convert current point to planar coordinates
                target_xy = transformer.transform(row['Latitude'], row['Longitude'])  # (lat, lon)
                target_x_swapped = target_xy[1]  # Swap
                target_y_swapped = target_xy[0]
                # Calculate local coordinates relative to origin
                x_local = target_x_swapped - origin_x_swapped
                y_local = target_y_swapped - origin_y_swapped
                return pd.Series({'X1': x_local, 'Y1': y_local})
            
            xy_df = df.apply(latlon_to_xy, axis=1)
            df['X1'] = xy_df['X1']
            df['Y1'] = xy_df['Y1']
        else:
            print("Longitude/Latitude not found; skip XY projection.")

        # Save output per meshcode
        df.to_csv(output_file, index=False)
        print(f"Converted file saved as: {output_file}")

        # Store for merging
        df_with_mesh = df.copy()
        df_with_mesh['meshcode'] = meshcode
        processed_dfs.append(df_with_mesh)

    # Merge all results into one file
    if processed_dfs:
        merged_df = pd.concat(processed_dfs, ignore_index=True)
        merged_output = os.path.join(sign_output_dir, 'ALL_TOLLMS_SIGN_processed.csv')
        merged_df.to_csv(merged_output, index=False)
        print(f"Merged output saved as: {merged_output}")
        return merged_df

    print("No processed files generated.")
    return None


if __name__ == "__main__":
    # Example: pass meshcode list, projection origin, and DB folder
    convert_coordinates(
        meshcode_list=['Z513243', 'Z513244'],
        latitude0=34.38450787998186,
        longitude0=132.49864639503264,
        db_folder='2202DB'
    )
