# Extract Satellite Data to Local Directory using Google Earth Engine

## Python script to extract Sentinel 2, Landsat 8 or Landsat 9 GeoTIFF data locally for a given ROI

### Usage:
Update the dictionary called `pull_data_info` in the `pull_data.py` script to customize the data extraction, and then run `pull_data.py`.

The keys in `pull_data_info` are:
> `start_date` : Enter the start date for your data extraction (including) \
> `end_date` : Enter the end date for your data extraction (excluding) \
> `boundary_path` : Path to KML or KMZ file of your ROI \
> `selected_bands` : Enter the band names you want to extract. The bands names are avaiable here: [Sentinel 2](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED), [Landsat 8](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2), [Landsat 9](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC09_C02_T1_L2) \
> `satelliteID` : Enter 0 for Sentinel 2, 1 for Landsat 8 and 2 for Landsat 9 \
> `output_dir` : Directory to save the extracted GeoTIFF files (the data will be saved in `output_dir/farm_name/satellite_name`) \
> `plot_images` : [Optional] Enter True if you want to save the RGB images (Default value is False) \
> `scale` : [Optional] Enter the resolution you want in meters (Default value is 10) \
> `farm_name` : [Optional] The name of your ROI field (Default value is the filename of the `boundary_path`)

