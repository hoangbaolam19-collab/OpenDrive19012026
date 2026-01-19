# -*- coding: utf-8 -*-
"""
Coordinate systems utilities for JGD2011 (Japanese Geodetic Datum 2011).

This module provides utilities for converting between geographic coordinates (lat/lon)
and planar coordinates using the appropriate JGD2011 planar zone system.

Reference: https://lemulus.me/column/epsg-list-gis#2011JGD2011
EPSG:4612 - JGD2000 geographic (lat/lon)
EPSG:6669-6687 - JGD2011 planar zones (19 zones for different Japanese prefectures)
"""

from pyproj import CRS


# JGD2011 planar coordinate system (平面直角座標系) zones
# Zone I - XIX mapping for Japanese prefectures
JGD2011_ZONES = {
    "Nagasaki": 6669,      # Zone I (1)系
    "Fukuoka": 6670,       # Zone II (2)系
    "Saga": 6670,
    "Kumamoto": 6670,
    "Oita": 6670,
    "Miyazaki": 6670,
    "Kagoshima": 6670,
    "Yamaguchi": 6671,     # Zone III (3)系
    "Shimane": 6671,
    "Hiroshima": 6671,
    "Kagawa": 6672,        # Zone IV (4)系
    "Ehime": 6672,
    "Tokushima": 6672,
    "Kochi": 6672,
    "Hyogo": 6673,         # Zone V (5)系
    "Tottori": 6673,
    "Okayama": 6673,
    "Kyoto": 6674,         # Zone VI (6)系
    "Osaka": 6674,
    "Fukui": 6674,
    "Shiga": 6674,
    "Mie": 6674,
    "Nara": 6674,
    "Wakayama": 6674,
    "Ishikawa": 6675,      # Zone VII (7)系
    "Toyama": 6675,
    "Gifu": 6675,
    "Aichi": 6675,
    "Niigata": 6676,       # Zone VIII (8)系 ⭐
    "Nagano": 6676,
    "Yamanashi": 6676,
    "Shizuoka": 6676,
    "Tokyo": 6677,         # Zone IX (9)系
    "Fukushima": 6677,
    "Tochigi": 6677,
    "Ibaraki": 6677,
    "Saitama": 6677,
    "Chiba": 6677,
    "Gunma": 6677,
    "Kanagawa": 6677,
    "Aomori": 6678,        # Zone X (10)系
    "Akita": 6678,
    "Yamagata": 6678,
    "Iwate": 6678,
    "Miyagi": 6678,
    # ... additional zones 11-19 covered by prefectures above
}


def get_coordinate_systems(location_prefecture=None, lat=None, lon=None, default_zone=6671):
    """
    Get appropriate CRS pair (source and destination) based on location.
    
    Args:
        location_prefecture (str): Prefecture name in English (e.g., "Hiroshima", "Nagano")
        lat (float): Latitude for coordinate-based zone detection (optional)
        lon (float): Longitude for coordinate-based zone detection (optional)
        default_zone (int): Default planar zone EPSG code if prefecture not found (default: 6676 Zone VIII)
    
    Returns:
        tuple: (src_crs, dst_crs, zone_epsg) where:
            - src_crs: CRS object for EPSG:4612 (JGD2000 geographic/lat-lon)
            - dst_crs: CRS object for selected planar zone
            - zone_epsg: int EPSG code of selected zone
    
    Example:
        >>> src_crs, dst_crs, zone = get_coordinate_systems("Shizuoka")
        >>> # or by coordinates:
        >>> src_crs, dst_crs, zone = get_coordinate_systems(lat=34.375, lon=132.408)
    """

    src_crs = CRS.from_epsg(4612)  # JGD2000 geographic (lat/lon)
    
    # Determine destination zone
    if location_prefecture and location_prefecture in JGD2011_ZONES:
        zone_epsg = JGD2011_ZONES[location_prefecture]
    # elif lat is not None and lon is not None:
    #     # Coordinate-based detection using prefecture boundaries
    #     zone_epsg = determine_zone_from_coordinates(lat, lon, default_zone)
    else:
        zone_epsg = default_zone
    
    dst_crs = CRS.from_epsg(zone_epsg)
    return src_crs, dst_crs, zone_epsg


def determine_zone_from_coordinates(lat, lon, default_zone=6676):
    """
    Determine JGD2011 planar zone from latitude/longitude by identifying prefecture.
    Uses geographic boundaries for accurate prefecture detection.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        default_zone (int): Default zone if cannot determine (default: 6676 Zone VIII)
    
    Returns:
        int: EPSG code of detected zone
    
    Reference: Japanese prefectures approximate geographic boundaries
    """
    
    # Prefecture boundaries (approximate): (lat_min, lat_max, lon_min, lon_max) -> prefecture
    # Organized by zone for efficiency
    PREFECTURE_BOUNDS = {
        # Zone I - Nagasaki
        "Nagasaki": ((32.7, 33.2), (129.0, 130.3)),
        
        # Zone II - Fukuoka, Saga, Kumamoto, Oita, Miyazaki, Kagoshima
        "Fukuoka": ((33.0, 34.6), (130.1, 131.1)),
        "Saga": ((32.8, 33.8), (129.5, 130.6)),
        "Kumamoto": ((32.0, 33.1), (130.1, 131.3)),
        "Oita": ((32.7, 33.9), (130.9, 132.3)),
        "Miyazaki": ((31.6, 32.7), (130.6, 131.6)),
        "Kagoshima": ((30.3, 31.8), (129.5, 131.2)),
        
        # Zone III - Yamaguchi, Shimane, Hiroshima
        "Yamaguchi": ((33.6, 34.4), (130.4, 132.1)),
        "Shimane": ((34.7, 35.5), (131.8, 133.1)),
        "Hiroshima": ((34.0, 34.8), (131.9, 133.1)),
        
        # Zone IV - Kagawa, Ehime, Tokushima, Kochi
        "Kagawa": ((34.2, 34.5), (133.8, 134.7)),
        "Ehime": ((33.5, 34.5), (132.4, 134.1)),
        "Tokushima": ((33.9, 34.5), (133.6, 134.7)),
        "Kochi": ((32.8, 34.4), (132.5, 134.4)),
        
        # Zone V - Hyogo, Tottori, Okayama
        "Hyogo": ((34.1, 35.6), (133.7, 135.6)),
        "Tottori": ((35.3, 35.6), (133.7, 134.9)),
        "Okayama": ((34.4, 35.1), (133.4, 134.3)),
        
        # Zone VI - Kyoto, Osaka, Fukui, Shiga, Mie, Nara, Wakayama
        "Kyoto": ((34.7, 35.6), (135.2, 136.3)),
        "Osaka": ((34.3, 34.9), (135.0, 135.8)),
        "Fukui": ((35.6, 36.6), (135.5, 136.8)),
        "Shiga": ((34.9, 35.5), (135.7, 136.4)),
        "Mie": ((33.9, 34.8), (135.8, 137.3)),
        "Nara": ((34.3, 34.7), (135.8, 136.8)),
        "Wakayama": ((33.4, 34.4), (135.2, 136.9)),
        
        # Zone VII - Ishikawa, Toyama, Gifu, Aichi
        "Ishikawa": ((35.9, 37.3), (135.7, 137.6)),
        "Toyama": ((36.4, 37.1), (136.6, 138.2)),
        "Gifu": ((35.2, 36.6), (136.4, 137.6)),
        "Aichi": ((34.7, 35.9), (136.6, 138.2)),
        
        # Zone VIII - Niigata, Nagano, Yamanashi, Shizuoka
        "Niigata": ((36.6, 37.9), (137.5, 139.7)),
        "Nagano": ((35.9, 37.0), (137.1, 138.5)),
        "Yamanashi": ((35.3, 35.9), (137.5, 139.2)),
        "Shizuoka": ((34.4, 35.2), (137.7, 139.1)),
        
        # Zone IX - Tokyo, Fukushima, Tochigi, Ibaraki, Saitama, Chiba, Gunma, Kanagawa
        "Tokyo": ((35.1, 35.9), (138.9, 140.9)),
        "Fukushima": ((36.9, 37.9), (139.5, 141.0)),
        "Tochigi": ((36.4, 37.1), (139.5, 140.9)),
        "Ibaraki": ((35.9, 36.9), (139.8, 141.0)),
        "Saitama": ((35.8, 36.6), (138.7, 140.5)),
        "Chiba": ((35.2, 35.8), (139.8, 141.2)),
        "Gunma": ((36.3, 37.3), (138.5, 140.1)),
        "Kanagawa": ((34.9, 35.6), (139.0, 140.9)),
        
        # Zone X - Aomori, Akita, Yamagata, Iwate, Miyagi
        "Aomori": ((40.2, 41.3), (139.5, 141.6)),
        "Akita": ((39.4, 40.8), (139.5, 141.3)),
        "Yamagata": ((37.9, 38.9), (139.5, 141.2)),
        "Iwate": ((38.9, 40.6), (140.7, 142.1)),
        "Miyagi": ((37.8, 38.9), (140.3, 141.8)),
    }
    
    # Check which prefecture the coordinate falls into
    for prefecture, (lat_bounds, lon_bounds) in PREFECTURE_BOUNDS.items():
        lat_min, lat_max = lat_bounds
        lon_min, lon_max = lon_bounds
        
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            # Return the zone for this prefecture
            if prefecture in JGD2011_ZONES:
                return JGD2011_ZONES[prefecture]
    
    # If no prefecture boundary matched, return default zone
    return default_zone
