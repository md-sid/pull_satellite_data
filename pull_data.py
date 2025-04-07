"""
Title       : pull_data.py
Description : Pulls the data for Sentinel2. Landsat8 or Landsat9 using Google Earth Engine
Author      : Siddat Nesar (siddatnesar@montana.edu)
Date        : 2025-04-06
Version     : 1.0.0
License     : BSD 3-Clause
Usage       : python pull_data.py   [Update the dictionary "pull_data_info" below before running the script]
"""

import ee
from utils import SatelliteData

pull_data_info = {
    'start_date' : '2024-05-01',        # Enter the start date
    'end_date' : '2024-05-31',          # Enter the end date
    'farm_name' : 'hospital_area',      # Enter the name of the field
    'boundary_path' : './data/hospital_area.kmz',   # Enter a KML or KMZ file
    'selected_bands' : ["B1", "B2", "B3", "B4"],    # Enter the band names you want corresponding to 'satelliteID'
    'satelliteID' : 0,                  # Enter 0 for Sentinel 2, 1 for Landsat 8 and 2 for Landsat 9
    'output_dir' : './ExtractedSatelliteData',      # Enter the directory to save the data
    # 'plot_images' : True                # True or False (Default value is False if not specified)
}


# Initialize Earth Engine
ee.Initialize()

s1 = SatelliteData(pull_data_info)
s1.export_images()
