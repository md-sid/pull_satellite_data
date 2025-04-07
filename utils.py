"""
Title       : utils.py
Description : Helper function for the script pull_data.py
Author      : Siddat Nesar (siddatnesar@montana.edu)
Date        : 2025-04-06
Version     : 1.0.0
License     : BSD 3-Clause
"""

import os
import sys
import ee
import json
import zipfile
import numpy as np
import rasterio
import requests
import geopandas as gpd
from matplotlib import pyplot as plt


class SatelliteData:
    def __init__(self, info):
        self.start_date = info['start_date']
        self.end_date = info['end_date']
        self.boundary = info['boundary_path']
        self.bands = info['selected_bands']
        self.output_dir = info['output_dir']
        self.scale = info.get('scale', 10)
        self.plot_images = info.get('plot_images', False)
        if not isinstance(self.plot_images, bool):
            raise ValueError('Invalid value for plot_images. Expected a boolean (True or False)')
        self.farm_name = info.get('farm_name', os.path.basename(self.boundary[:-4]))
        if info['satelliteID'] == 0:
            self.satellite_name = 'Sentinel2'
            self.dataset = 'COPERNICUS/S2_SR_HARMONIZED'
        elif info['satelliteID'] == 1:
            self.satellite_name = 'Landsat8'
            self.dataset = 'LANDSAT/LC08/C02/T1_L2'
        elif info['satelliteID'] == 2:
            self.satellite_name = 'Landsat9'
            self.dataset = 'LANDSAT/LC09/C02/T1_L2'
        else:
            raise ValueError('Invalid Satellite ID!\nPlease enter either 0, 1, or 2')


    def kmz_to_kml(self):
        """Extract KML from KMZ"""
        with zipfile.ZipFile(self.boundary, 'r') as z:
            for filename in z.namelist():
                if filename.endswith('.kml'):
                    os.rename(z.extract(filename, path='.'), './temp.kml')
                    return './temp.kml'
        return None


    def get_geometry(self):
        """Convert KML to GeoJSON and extract the formatted polygon geometry for earth engine"""
        if self.boundary.endswith('.kmz'):
            kml = self.kmz_to_kml()
            if not kml:
                raise ValueError(f"No KML file found in the KMZ archive: {self.boundary}")
        elif self.boundary.endswith('.kml'):
            kml = self.boundary
        else:
            raise ValueError("Input file must be a KML or KMZ file.")

        gdf = gpd.read_file(kml, driver='KML')
        if os.path.exists('./temp.kml'):
            os.remove('./temp.kml')
        geojson = json.loads(gdf.to_json())

        # ensure the KML has at least one feature
        if not geojson['features']:
            raise ValueError('No features found in the KML file')

        geometry = geojson['features'][0]['geometry']

        # validate it is a polygon or multipolygon
        if geometry['type'] == 'Polygon':
            coordinates = geometry['coordinates']
        elif geometry['type'] == 'MultiPolygon':
            coordinates = geometry['coordinates'][0]
            print('Extracting Data for the First Polygon')
        else:
            raise ValueError(f"Expected 'Polygon' or 'MultiPolygon', but got '{geometry['type']}'")

        # remove altitude (third value) for each coordinate
        cleaned_coordinates = [[[lon, lat] for lon, lat, *_ in ring] for ring in coordinates]

        # ensure polygon is created
        if cleaned_coordinates[0][0] != cleaned_coordinates[0][-1]:
            cleaned_coordinates[0].append(cleaned_coordinates[0][0])

        return cleaned_coordinates


    def plot_rgb(self, path):
        if self.satellite_name == 'Sentinel2':
            rgb_bands = ['B4', 'B3', 'B2']
        elif self.satellite_name in ('Landsat8' or 'Landsat9'):
            rgb_bands = ['SR_B4', 'SR_B3', 'SR_B2']
        else:
            self.plot_images = False
            return

        idx = [self.bands.index(band) for band in rgb_bands if band in self.bands]
        if len(idx) != 3:
            print('Not saving the images as all RGB bands are not found')
            self.plot_images = False
            return

        with rasterio.open(path) as d:
            bands_count = d.count
            bands = [d.read(i) for i in range(1, bands_count + 1)]
        rgb = np.stack([bands[idx[0]], bands[idx[1]], bands[idx[2]]], axis=-1)
        rgb = np.clip(rgb / np.max(rgb), 0, 1)
        plt.imsave(path[:-3] + 'png', rgb)


    def export_images(self):
        region = ee.Geometry.Polygon(self.get_geometry())

        # Load image collection
        collection = (ee.ImageCollection(self.dataset)
                      .filterBounds(region)
                      .filterDate(self.start_date, self.end_date)
                      .select(self.bands))

        # Get the unique days if repeats
        date_list = collection.aggregate_array('system:time_start') \
            .map(lambda t: ee.Date(t).format('YYYY-MM-dd')) \
            .distinct()

        # Group images by date to get the best data on the day
        def mosaic_day(mapped_date):
            date = ee.Date(mapped_date)
            daily = collection.filterDate(date, date.advance(1, 'day'))
            return daily.mosaic().set('system:time_start', date.millis())

        # Refine the image collection
        collection = ee.ImageCollection(date_list.map(mosaic_day))

        # Get list of images
        images = collection.toList(collection.size())
        try:
            num_images = images.size().getInfo()
            print(f"Found {num_images} images in {self.satellite_name} from {self.start_date} to {self.end_date}")
        except Exception as e:
            print(f'Check start and end date: {e}')
            sys.exit(1)

        # check if output directory exists
        save_dir = os.path.join(self.output_dir, self.farm_name, self.satellite_name)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        for i in range(num_images):
            image = ee.Image(images.get(i))
            date_str = image.date().format("YYYY-MM-dd").getInfo()

            # Generate download URL for multi-band image
            url = image.getDownloadURL({
                'scale': self.scale,
                'region': region,
                'format': 'GeoTIFF'
            })

            # Save file locally
            file_path = os.path.join(str(save_dir), str(date_str) + '.tif')
            print(f"Saving: {file_path}")

            response = requests.get(url)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                # Add metadata (add band names to a multi-band GeoTIFF)
                with rasterio.open(file_path, "r+") as d:
                    d.descriptions = tuple(self.bands)

                if self.plot_images:
                    # call the function to plot image
                    self.plot_rgb(file_path)

            else:
                print(f"Failed: {date_str}")
