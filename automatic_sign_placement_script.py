"""
Integrated Automatic Sign Placement Script
Tích hợp toàn bộ pipeline xử lý biển báo tự động

This module provides a single function to run the complete sign placement pipeline:
1. Convert coordinates (if needed)
2. Extract XY coordinates from XODR
3. Check signal existence and calculate positions
4. Generate OpenDRIVE with signs

Author: Generated from existing pipeline scripts
"""

import os
import sys
import pandas as pd
import numpy as np
import glob
import shutil
from typing import List, Tuple, Optional, Union
import logging
from pathlib import Path
from pyproj import CRS, Transformer
from shapely.geometry import LineString, Point
from automatic_sign_placement.calc_pos_st2 import interpolate_points, func_calc_st
from automatic_sign_placement.signal_pole_input_make import make_format
from automatic_sign_placement.convert_coordinates import convert_coordinates


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def automatic_sign_placement_script(
    xodr_input_path: str,
    meshcode_list: List[str],
    latitude0: float,
    longitude0: float,
    db_folder: str = '2202DB',
    distance_threshold: float = 10.0,
    output_dir: str = 'output',
    skip_coordinate_conversion: bool = False
) -> Tuple[str, bool]:
    """
    Integrated automatic sign placement pipeline
    
    Args:
        xodr_input_path: Path to input OpenDRIVE file (.xodr)
        meshcode_list: List of mesh codes to process (e.g., ['Z513243'])
        latitude0: Origin latitude for projection
        longitude0: Origin longitude for projection
        db_folder: Database folder name (default: '2202DB')
        distance_threshold: Distance threshold for sign placement (meters)
        output_dir: Output directory for final XODR file
        skip_coordinate_conversion: Skip coordinate conversion if processed files exist
        
    Returns:
        Tuple[output_path, success]: Path to output XODR file and success status
    """
    
    logger.info(" Starting Automatic Sign Placement Pipeline")
    logger.info(f"Input XODR: {xodr_input_path}")
    logger.info(f"Mesh codes: {meshcode_list}")
    logger.info(f"Origin: ({latitude0}, {longitude0})")
    logger.info(f"Distance threshold: {distance_threshold}m")
    
    try:
        # Setup paths
        base_dir = Path(__file__).parent / 'automatic_sign_placement'
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(exist_ok=True)
        
        # Generate output filename
        input_name = Path(xodr_input_path).stem
        output_filename = f"{input_name}_with_signs.xodr"
        final_output_path = output_dir_path / output_filename
        
        # Step 1: Coordinate conversion (if needed)
        logger.info(" Step 1: Coordinate conversion")
        if not skip_coordinate_conversion:
            success = _run_coordinate_conversion(
                base_dir, meshcode_list, latitude0, longitude0, db_folder
            )
            if not success:
                logger.error("Coordinate conversion failed")
                return str(final_output_path), False
        else:
            logger.info("Skipping coordinate conversion")
        
        # Step 2: Extract XY coordinates from XODR
        logger.info("Step 2: Extract XY coordinates from XODR")
        coords_dir = base_dir / 'coordinates'
        success = _extract_xy_from_xodr(xodr_input_path, coords_dir)
        if not success:
            logger.error("XY extraction failed")
            return str(final_output_path), False
        
        # Step 3: Check signal existence and calculate positions
        logger.info("Step 3: Check signal existence and calculate positions")
        success = _check_signals_and_calculate_positions(
            base_dir, db_folder, meshcode_list, latitude0, longitude0, distance_threshold
        )
        if not success:
            logger.error("Signal position calculation failed")
            return str(final_output_path), False
        
        # Step 4: Generate OpenDRIVE with signs
        logger.info("Step 4: Generate OpenDRIVE with signs")
        success = _generate_opendrive_with_signs(base_dir, xodr_input_path, final_output_path)
        if not success:
            logger.error("OpenDRIVE generation failed")
            return str(final_output_path), False
        
        logger.info(f" Pipeline completed successfully!")
        logger.info(f"Output file: {final_output_path}")
        
        return str(final_output_path), True
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return str(final_output_path), False


def _run_coordinate_conversion(
    base_dir: Path,
    meshcode_list: List[str],
    latitude0: float,
    longitude0: float,
    db_folder: str
) -> bool:
    """Run coordinate conversion step"""
    try:
        
        result = convert_coordinates(
            meshcode_list=meshcode_list,
            latitude0=latitude0,
            longitude0=longitude0,
            db_folder=db_folder
        )
        
        if result is not None:
            logger.info(" Coordinate conversion completed")
            return True
        else:
            logger.warning("No processed files generated in coordinate conversion")
            return False
            
    except Exception as e:
        logger.error(f"Coordinate conversion error: {e}")
        return False


def _extract_xy_from_xodr(xodr_input_path: str, coords_dir: Path) -> bool:
    """Extract XY coordinates from XODR file"""
    try:
        coords_dir.mkdir(exist_ok=True)

        for item in coords_dir.iterdir():
            item.unlink() 
        
        with open(xodr_input_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        road_id = None
        coordinates = []
        files_created = 0
        
        for line in lines:
            # Find road id= lines
            if 'road id=' in line:
                # Save previous data if exists
                if road_id is not None and coordinates:
                    filename = coords_dir / f"coordinates{road_id}.csv"
                    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                        import csv
                        writer = csv.writer(csvfile)
                        writer.writerow(['X', 'Y'])  # Header
                        writer.writerows(coordinates)
                    files_created += 1
                    logger.debug(f"Created: {filename}")
                
                # Get new road_id
                road_id = line.split('road id=')[1].split('"')[1]
                coordinates = []
            
            # Extract coordinates from x=, y= lines
            elif 'x=' in line and 'y=' in line:
                try:
                    x = line.split('x=')[1].split('"')[1]
                    y = line.split('y=')[1].split('"')[1]
                    coordinates.append([x, y])
                except IndexError:
                    pass  # Skip malformed lines
        
        # Save last road_id data
        if road_id is not None and coordinates:
            filename = coords_dir / f"coordinates{road_id}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                import csv
                writer = csv.writer(csvfile)
                writer.writerow(['X', 'Y'])
                writer.writerows(coordinates)
            files_created += 1
            logger.debug(f"Created: {filename}")
        
        logger.info(f" Extracted coordinates for {files_created} roads")
        return files_created > 0
        
    except Exception as e:
        logger.error(f"XY extraction error: {e}")
        return False


def _check_signals_and_calculate_positions(
    base_dir: Path,
    db_folder: Path,
    meshcode_list: List[str],
    latitude0: float,
    longitude0: float,
    distance_threshold: float
) -> bool:
    """Check signal existence and calculate positions"""
    try:
        
        # Setup paths
        sign_output_dir = os.path.join(db_folder, 'CSV')
        processed_sign_file = os.path.join(sign_output_dir, 'ALL_TOLLMS_SIGN_processed.csv')
        
        # Check if processed sign file exists
        if not os.path.exists(processed_sign_file):
            logger.error(f"Processed sign file not found: {processed_sign_file}")
            logger.info("Please run coordinate conversion first")
            return False
        
        # Read sign data
        df_check = pd.read_csv(processed_sign_file)
        if df_check.empty:
            logger.warning("No sign data found")
            return False
        
        logger.info(f"Found {len(df_check)} signs to process")
        
        # Setup projection using EPSG codes (JGD2011)
        src_srs = CRS.from_epsg(4612)  # JGD2000 geographic
        dst_srs = CRS.from_epsg(6676)   # JGD2011 planar zone VI
        transformer = Transformer.from_crs(src_srs, dst_srs, always_xy=False)

        # Precompute origin's planar coordinates with swap
        origin_xy = transformer.transform(latitude0, longitude0)  # Input: (lat, lon)
        origin_x_swapped = origin_xy[1]  # Swap x and y as per LinkData.py
        origin_y_swapped = origin_xy[0]

        # Ensure X1, Y1 coordinates exist
        if 'X1' not in df_check.columns or 'Y1' not in df_check.columns:
            logger.info("Converting coordinates to X1, Y1")
            def convert_row(row):
                # Transform current point to planar coordinates
                target_xy = transformer.transform(row['Latitude'], row['Longitude'])  # (lat, lon)
                target_x_swapped = target_xy[1]  # Swap x and y
                target_y_swapped = target_xy[0]
                # Compute local coordinates relative to origin
                x_local = target_x_swapped - origin_x_swapped
                y_local = target_y_swapped - origin_y_swapped
                return pd.Series({'X1': x_local, 'Y1': y_local})
            df_check[['X1', 'Y1']] = df_check.apply(convert_row, axis=1)
            df_check.to_csv(processed_sign_file, index=False)
        
        check_coords = df_check[['X1', 'Y1']].values
        
        # Find coordinate files
        coord_glob_pattern = str(base_dir / 'coordinates' / 'coordinates*.csv')
        coord_files = glob.glob(coord_glob_pattern)
        
        if not coord_files:
            logger.error("No coordinate files found. Run XY extraction first.")
            return False
        
        logger.info(f" Found {len(coord_files)} coordinate files")
        
        # Calculate distance matrix
        distance_df = pd.DataFrame(check_coords, columns=['x', 'y'])
        
        for coord_file in coord_files:
            # Read coordinate file
            df_coords = pd.read_csv(coord_file)
            
            # Skip files with insufficient data
            if len(df_coords) <= 1:
                logger.debug(f"Skipping {coord_file} (insufficient points)")
                continue
            
            # Create road line with interpolation
            try:
                recreate_points = interpolate_points(df_coords[['X', 'Y']].values, step=1.0)
                road_line = LineString(recreate_points)
                
                # Calculate distances
                distances = [Point(p).distance(road_line) for p in check_coords]
                
                # Extract file ID
                file_id = os.path.basename(coord_file).split('coordinates')[-1].split('.')[0]
                distance_df[f"polyline_{file_id}"] = distances
                
            except Exception as e:
                logger.warning(f"Error processing {coord_file}: {e}")
                file_id = os.path.basename(coord_file).split('coordinates')[-1].split('.')[0]
                distance_df[f"polyline_{file_id}"] = np.nan
        
        # Find closest polylines
        distance_cols = [col for col in distance_df.columns if col.startswith('polyline_')]
        
        if not distance_cols:
            logger.error("No valid distance calculations")
            return False
        
        distance_df['closest_polyline'] = distance_df[distance_cols].idxmin(axis=1)
        distance_df['closest_polyline'] = distance_df['closest_polyline'].str.extract(r'(\d+)$').astype(int)
        distance_df['min_distance'] = distance_df[distance_cols].min(axis=1)
        
        # Merge with sign data
        distance_df = pd.merge(
            distance_df,
            df_check[['X1', 'Y1', 'maxspeed', 'orflg']],
            left_on=['x', 'y'],
            right_on=['X1', 'Y1'],
            how='left'
        )
        distance_df.drop(columns=['X1', 'Y1'], inplace=True)
        
        # Filter by distance threshold
        filtered_df = distance_df[distance_df['min_distance'] <= distance_threshold]
        
        if filtered_df.empty:
            logger.warning(f"No signs within {distance_threshold}m threshold")
            return False
        
        logger.info(f"Found {len(filtered_df)} signs within {distance_threshold}m threshold")

        target_df = filtered_df.copy()
        
        logger.info(f"Processing {len(target_df)} signs for placement")
        
        # Process each target point
        processed_count = 0
        for _, target_row in target_df.iterrows():
            polyline_id = int(target_row['closest_polyline'])
            target_point = [target_row['x'], target_row['y']]
            maxspeed = int(target_row['maxspeed']) if pd.notnull(target_row['maxspeed']) else 50
            orflg = target_row['orflg'] if pd.notnull(target_row['orflg']) else [0]
            
            # Find corresponding coordinate file
            coord_file = base_dir / 'coordinates' / f'coordinates{polyline_id}.csv'
            if not coord_file.exists():
                logger.warning(f"Coordinate file not found: {coord_file}")
                continue
            
            # Read coordinates and calculate s,t
            df_coords = pd.read_csv(coord_file)
            current_points = df_coords[['X', 'Y']].values
            
            try:
                recreate_points = interpolate_points(current_points, step=1.0)
                nearest_point, s, t = func_calc_st(recreate_points, target_point)
                
                logger.debug(f" ID: {polyline_id}, Point: {target_point}, s: {s:.3f}, t: {t:.3f}")
                
                # Generate format using make_format
                make_format(s, t, polyline_id, maxspeed, [orflg])
                processed_count += 1
                
            except Exception as e:
                logger.warning(f"Error processing point for road {polyline_id}: {e}")
                continue
        
        logger.info(f" Processed {processed_count} sign positions")
        return processed_count > 0
        
    except Exception as e:
        logger.error(f"Signal position calculation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def _generate_opendrive_with_signs(base_dir: Path, xodr_input_path: str, output_path: Path) -> bool:
    """Generate OpenDRIVE file with signs"""
    try:
        import xml.etree.ElementTree as ET
        import uuid
        import re
        
        # Input files
        signal_input_file = base_dir / 'signal_input_new.csv'
        pole_input_file = base_dir / 'pole_input_new.csv'
        
        # Check if input files exist
        missing = []
        for p, label in [
            (xodr_input_path, 'OpenDRIVE input (.xodr)'),
            (signal_input_file, 'signal_input_new.csv'),
            (pole_input_file, 'pole_input_new.csv'),
        ]:
            if not os.path.exists(p):
                missing.append(f"{label}: {p}")
        
        if missing:
            logger.error("Missing input files:")
            for m in missing:
                logger.error(f"   - {m}")
            return False
        
        # Read CSV data
        signal_df = pd.read_csv(signal_input_file)
        pole_df = pd.read_csv(pole_input_file)
        
        # Remove duplicates
        signal_df = signal_df.drop_duplicates(subset=['linkno','s','t','name'], keep='first')
        pole_df = pole_df.drop_duplicates(subset=['linkno','s','t','name'], keep='first')
        
        logger.info(f"Adding {len(signal_df)} signals and {len(pole_df)} poles")
        
        # Read original file to preserve CDATA
        with open(xodr_input_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Parse OpenDRIVE
        tree = ET.parse(xodr_input_path)
        root = tree.getroot()
        
        def get_or_create_sub_element(parent, tag):
            child = parent.find(tag)
            if child is None:
                child = ET.SubElement(parent, tag)
            return child
        
        # Process each road
        roads_processed = 0
        for road in root.findall('road'):
            road_id = int(road.get('id'))
            
            # Get corresponding data
            signal_rows = signal_df[signal_df['linkno'] == road_id]
            pole_rows = pole_df[pole_df['linkno'] == road_id]
            
            if signal_rows.empty and pole_rows.empty:
                continue
            
            # Add objects (poles) first
            if not pole_rows.empty:
                objects_elem = get_or_create_sub_element(road, 'objects')
                for _, row in pole_rows.iterrows():
                    if "Sign_Post" in row['name']:
                        obj = ET.SubElement(objects_elem, 'object')
                        obj.set('id', str(row['id']))
                        obj.set('name', row['name'])
                        obj.set('s', f"{row['s']:.16e}")
                        obj.set('t', f"{row['t']:.1f}")
                        obj.set('zOffset', f"{row['zOffset']:.16e}")
                        obj.set('hdg', f"{row['hOffset']:.16e}")
                        obj.set('roll', f"{row['roll']:.16e}")
                        obj.set('pitch', f"{row['pitch']:.16e}")
                        obj.set('orientation', row['orientation'])
                        obj.set('type', "none")
                        obj.set('height', f"{row['height']:.16e}")
                        obj.set('width', f"{row['width']:.16e}")
                        obj.set('length', "7.5000009536743156e-02")
                        obj.set('validLength', "0.0000000000000000e+00")
                        obj.set('dynamic', row['dynamic'])
            
            # Add signals
            if not signal_rows.empty:
                signals_elem = get_or_create_sub_element(road, 'signals')
                for _, row in signal_rows.iterrows():
                    signal = ET.SubElement(signals_elem, 'signal')
                    signal.set('name', f"{row['name']}")
                    signal.set('id', str(row['id']))
                    signal.set('s', f"{row['s']:.16e}")
                    signal.set('t', f"{row['t']:.1f}")
                    signal.set('zOffset', f"{row['zOffset']:.16e}")
                    signal.set('hOffset', f"{row['hOffset']:.16e}")
                    signal.set('roll', f"{row['roll']:.16e}")
                    signal.set('pitch', f"{row['pitch']:.16e}")
                    signal.set('orientation', row['orientation'])
                    signal.set('dynamic', row['dynamic'])
                    signal.set('type', str(row['type']))
                    signal.set('subtype', str(row['subtype']))
                    signal.set('height', f"{row['height']:.16e}")
                    signal.set('width', f"{row['width']:.16e}")
                    
                    validity = ET.SubElement(signal, 'validity')
                    validity.set('fromLane', '0')
                    validity.set('toLane', '0')
                    
                    user_data = ET.SubElement(signal, 'userData')
                    user_data.set('code', 'vectorSignal')
                    
                    vector_signal = ET.SubElement(user_data, 'vectorSignal')
                    generated_signal_id = str(uuid.uuid4())
                    vector_signal.set('signalId', f'{{{generated_signal_id}}}')
            
            roads_processed += 1
        
        # Format XML with tabs
        def indent_with_tabs(elem, level=0):
            i = "\n" + level * "\t"
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "\t"
                for e in elem:
                    indent_with_tabs(e, level + 1)
                if not e.tail or not e.tail.strip():
                    e.tail = i
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
        
        indent_with_tabs(root)
        
        # Save output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(str(output_path), encoding='utf-8', xml_declaration=True)
        
        # Restore CDATA in geoReference
        with open(output_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
        
        # Extract geoReference content from original
        geo_match = re.search(r'<geoReference><!\[CDATA\[(.*?)\]\]></geoReference>', original_content, re.DOTALL)
        if geo_match:
            cdata_content = geo_match.group(1)
            # Replace in new file with CDATA preserved
            new_content = re.sub(
                r'<geoReference>(.*?)</geoReference>',
                f'<geoReference><![CDATA[{cdata_content}]]></geoReference>',
                new_content,
                flags=re.DOTALL
            )
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info("CDATA in geoReference preserved")
        
        logger.info(f"Generated OpenDRIVE with signs for {roads_processed} roads")
        logger.info(f"Output saved to: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"OpenDRIVE generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


# Example usage and testing
if __name__ == "__main__":
    # Example parameters for HIROSHIMA
    # xodr_input = "output/openDRIVE_data_34.375228_132.408491_34.35542_132.517107_route.xodr"
    # meshcode_list = ['Z513243', 'Z513244']
    # latitude0 = 34.375228
    # longitude0 = 132.408491

    xodr_input = "output/openDRIVE_data_new_34.38450787998186_132.49864639503264_34.35689848650365_132.48759687223688_new.xodr"
    meshcode_list = ['Z513243']
    latitude0 = 34.38450787998186
    longitude0 = 132.49864639503264
    
    output_path, success = automatic_sign_placement_script(
        xodr_input_path=xodr_input,
        meshcode_list=meshcode_list,
        latitude0=latitude0,
        longitude0=longitude0,
        db_folder='2202DB/HIROSHIMA',
        distance_threshold=10.0,
        output_dir="output",
        skip_coordinate_conversion=False
    )
    
    if success:
        print(f"SUCCESS! Output file: {output_path}")
    else:
        print(f"FAILED! Check logs for details.")
        sys.exit(1)
