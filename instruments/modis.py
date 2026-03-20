"""MODIS
Module for creating and operating on classes relating to the Moderate Resolution 
Imaging Spectroradiometer (MODIS).

Author:
	Luke Ellison

Version:
	0.1

History:
	v0.1, 26-Nov-2025, Luke Ellison: Module compiled.

Global Variables:
	MODIS_PRODUCT_FORMATTERS -- Dictionary of MODIS product filename formatters.
	MODIS_PRODUCT_REVERSE_FORMATTERS -- Dictionary of MODIS product filename 
		reverse formatters.
	MODIS_TERRA_PRODUCTS -- Dictionary of available MODIS-Terra products and 
		their associated metadata.
	MODIS_AQUA_PRODUCTS -- Dictionary of available MODIS-Aqua products and their 
		associated metadata.
	MODIS_COMBINED_PRODUCTS -- Dictionary of available combined 
		MODIS-Terra/-Aqua products and their associated metadata.
	MODIS_ANCILLARY_PRODUCTS -- Dictionary of available MODIS ancillary products 
		and their associated metadata.

Classes:
	MODIS -- Defines a MODIS object on either Terra or Aqua.

External Modules:
	- dateutil -- https://dateutil.readthedocs.io/
"""
# import os
# import datetime as dt
from dateutil.relativedelta import relativedelta
from ..instrument import WhiskbroomScanner

#------------------------------ GLOBAL VARIABLES ------------------------------#

# Set default module to use to read data
# DEFAULT_MODULE = ['netcdf4', 'xarray', 'h5py', 'pyhdf'][0]

# MODIS product formatters
MODIS_PRODUCT_FORMATTERS = {
	'timestamp': "%Y%j.%H%M",
	'date': "%Y%j",
	'time': "%H%M",
	'version': lambda v: int(v)/10**d if (d:=len(v.lstrip('0'))-1) else int(v),
	'processing_timestamp': "%Y%j%H%M%S"
}
MODIS_PRODUCT_REVERSE_FORMATTERS = {
	'version': lambda v: str(v).replace('.','').zfill(3)
}

# MODIS/Terra products
MODIS_TERRA_PRODUCTS = {
	'MOD00F': {
		'name': "MODIS/Terra Raw Instrument Packets",
		'level': 0,
		'structure': "swath",
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD00F)\.A(?P<timestamp>(?P<date>\d{7})"
			"\.(?P<time>\d{4}))\.(?P<processing_timestamp>\d{13})\."
			"(?P<sequence>\d{3})\.PDS"
	},
	'MOD02QKM': {
		'name': "MODIS/Terra Calibrated Radiances 250m",
		'level': '1b',
		'structure': "swath",
		'spatial_resolution': 250,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD02QKM)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)",
		'band_dimension_name': "Band_250M",
		'along_track_dimension_name': ["40*nscans", "10*nscans"],
		'across_track_dimension_name': ["4*Max_EV_frames", "Max_EV_frames"]
	},
	'MOD02HKM': {
		'name': "MODIS/Terra Calibrated Radiances 500m",
		'level': '1b',
		'structure': "swath",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD02HKM)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)",
		'band_dimension_name': ["Band_250M", "Band_500M"],
		'along_track_dimension_name': ["20*nscans", "10*nscans"],
		'across_track_dimension_name': ["2*Max_EV_frames", "Max_EV_frames"]
	},
	'MOD021KM': {
		'name': "MODIS/Terra Calibrated Radiances 1km",
		'level': '1b',
		'structure': "swath",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD021KM)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)",
		'band_dimension_name': ["Band_250M", "Band_500M", "Band_1KM_RefSB", \
			"Band_1KM_Emissive"],
		'along_track_dimension_name': ["10*nscans", "2*nscans"],
		'across_track_dimension_name': ["Max_EV_frames", "1KM_geo_dim"]
	},
	'MOD02OBC': {
		'name': "MODIS/Terra Onboard Calibrator/Engineering Data",
		'level': '1b',
		'structure': "swath",
		'spatial_resolution': [250, 500, 1000],	# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD02OBC)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD03': {
		'name': "MODIS/Terra Geolocation",
		'level': '1a',
		'structure': "swath",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD03)\.A(?P<timestamp>(?P<date>\d{7})"
			"\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)",
		'band_dimension_name': "numbands",
		'along_track_dimension_name': ["nscans*10", "nscans*20", "nscans"],
		'across_track_dimension_name': ["mframes", "mframes*2"],
		'labels': {
			'latitude_name': "Latitude",
			'longitude_name': "Longitude",
			'range_name': "Range",					# check if implemented
			'elevation_name': "Height",				# check if ortho
			'timestamp_name': "EV_center_time",		# check if works
			'solar_azimuth_name': "SolarAzimuth",
			'solar_zenith_name': "SolarZenith",
			# attitude_angles, orb_pos, orb_vel, 
		},
	},
	'MOD04_L2': {
		'name': "MODIS/Terra Aerosol 10km",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': 10000,			# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD04_L2)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)",
		'band_dimension_name': ["Num_By_Products", "MODIS_Band_Land", \
			"MODIS_Band_Ocean", "MODIS_Band_AND_NPP_Extra", \
			"Num_DeepBlue_Wavelengths", "Solution_1_Land", "Solution_2_Land", \
			"Solution_3_Land", "Solution_4_Land"],
		'along_track_dimension_name': ["Cell_Along_Swath", \
			"Cell_Along_Swath_500"],
		'across_track_dimension_name': ["Cell_Across_Swath", \
			"Cell_Across_Swath_500"]
	},
	'MOD04_3K': {
		'name': "MODIS/Terra Aerosol 3km",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': 3000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD04_3K)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)",
		'band_dimension_name': ["Num_By_Products", "MODIS_Band_Land", \
			"MODIS_Band_Ocean", "Solution_1_Land", "Solution_2_Land", \
			"Solution_3_Land", "Solution_4_Land"],
		'along_track_dimension_name': "Cell_Along_Swath",
		'across_track_dimension_name': "Cell_Across_Swath"
	},
	'MOD05_L2': {
		'name': "MODIS/Terra Total Precipitable Water Vapor",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': [1000, 5000],		# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD05_L2)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD06_L2': {
		'name': "MODIS/Terra Clouds",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': [1000, 5000],		# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD06_L2)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD07_L2': {
		'name': "MODIS/Terra Temperature and Water Vapor Profiles",
		'level': 3,
		'structure': "swath",
		'spatial_resolution': 5000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD07_L2)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD08_D3': {
		'name': "MODIS/Terra Aerosol Cloud Water Vapor Ozone Daily",
		'level': 3,
		'structure': "CMG grid",
		'spatial_resolution': 1,				# [deg]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD08_D3)\.A(?P<date>\d{7})\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD08_E3': {
		'name': "MODIS/Terra Aerosol Cloud Water Vapor Ozone 8-Day",
		'level': 3,
		'structure': "CMG grid",
		'spatial_resolution': 1,				# [deg]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD08_E3)\.A(?P<date>\d{7})\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD08_M3': {
		'name': "MODIS/Terra Aerosol Cloud Water Vapor Ozone Monthly",
		'level': 3,
		'structure': "CMG grid",
		'spatial_resolution': 1,				# [deg]
		'temporal_resolution': relativedelta(months=1),
		'filename_pattern': "(?P<product>MOD08_M3)\.A(?P<date>\d{7})\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD08_TL': {
		'name': "MODIS/Terra Atmosphere Daily Zonal Tiling",
		'level': 3,
		'structure': "CMG grid",
		'spatial_resolution': 1,				# [deg]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD08_TL)\.A(?P<date>\d{7})\.Z"
			"(?P<zone>\d{2})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD09': {
		'name': "MODIS/Terra Atmospherically Corrected Surface Reflectance",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': [250,500,1000],	# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD09)\.A(?P<timestamp>(?P<date>\d{7})"
			"\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD09GQ': {
		'name': "MODIS/Terra Surface Reflectance Daily SIN 250m",
		'level': 2,
		'structure': "SIN grid",
		'spatial_resolution': 250,				# [m]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD09GQ)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD09GA': {
		'name': "MODIS/Terra Surface Reflectance Daily SIN 500m & 1km",
		'level': 2,
		'structure': "SIN grid",
		'spatial_resolution': [500, 1000],		# [m]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD09GA)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD09Q1': {
		'name': "MODIS/Terra Surface Reflectance 8-Day",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 250,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD09Q1)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD09A1': {
		'name': "MODIS/Terra Surface Reflectance Monthly",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(months=1),
		'filename_pattern': "(?P<product>MOD09A1)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD09CMA': {
		'name': "MODIS/Terra Aerosol Optical Thickness",
		'level': 3,
		'structure': "CMG grid",
		'spatial_resolution': 0.05,				# [deg]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD09CMA)\.A(?P<date>\d{7})\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD11_L2': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD11_L2)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD11A1': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity Daily 1km",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD11A1)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD11A2': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity 8-Day 1km",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD11A2)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD11B1': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity Daily 6km",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 6000,				# [m]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD11B1)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD11B2': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity 8-Day 6km",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 6000,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD11B2)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD11B3': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity Monthly 6km",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 6000,				# [m]
		'temporal_resolution': relativedelta(months=1),
		'filename_pattern': "(?P<product>MOD11B3)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD11C1': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity Daily CMG",
		'level': 3,
		'structure': "CMG grid",
		'spatial_resolution': 0.05,				# [deg]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD11C1)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD11C2': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity 8-Day CMG",
		'level': 3,
		'structure': "CMG grid",
		'spatial_resolution': 0.05,				# [deg]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD11C2)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD11C3': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity Monthly CMG",
		'level': 3,
		'structure': "CMG grid",
		'spatial_resolution': 0.05,				# [deg]
		'temporal_resolution': relativedelta(months=1),
		'filename_pattern': "(?P<product>MOD11C3)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD13Q1': {
		'name': "MODIS/Terra Vegetation Indices 16-Day 250m",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 250,				# [m]
		'temporal_resolution': relativedelta(days=16),
		'filename_pattern': "(?P<product>MOD13Q1)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD13A1': {
		'name': "MODIS/Terra Vegetation Indices 16-Day 500m",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(days=16),
		'filename_pattern': "(?P<product>MOD13A1)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD13A2': {
		'name': "MODIS/Terra Vegetation Indices 16-Day 1km",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(days=16),
		'filename_pattern': "(?P<product>MOD13A2)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD13A3': {
		'name': "MODIS/Terra Vegetation Indices Monthly 1km",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(months=1),
		'filename_pattern': "(?P<product>MOD13A3)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD13C1': {
		'name': "MODIS/Terra Vegetation Indices 16-Day CMG",
		'level': 3,
		'structure': "CMG grid",
		'spatial_resolution': 0.05,				# [deg]
		'temporal_resolution': relativedelta(days=16),
		'filename_pattern': "(?P<product>MOD13C1)\.A(?P<date>\d{7})\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD13C2': {
		'name': "MODIS/Terra Vegetation Indices Monthly CMG",
		'level': 3,
		'structure': "CMG grid",
		'spatial_resolution': 0.05,				# [deg]
		'temporal_resolution': relativedelta(months=1),
		'filename_pattern': "(?P<product>MOD13C2)\.A(?P<date>\d{7})\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD14': {
		'name': "MODIS/Terra Thermal Anomalies/Fire",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD14)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)",
		'along_track_dimension_name': "number_of_scan_lines",
		'across_track_dimension_name': "pixels_per_scan_line"
	},
	'MOD14CRS': {
		'name': "MODIS/Terra Coarse Thermal Anomalies/Fire",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD14CRS)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\.NRT\.(?P<ext>hdf)"
	},
	'MOD14A1': {
		'name': "MODIS/Terra Thermal Anomalies/Fire Daily",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD14A1)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD14A2': {
		'name': "MODIS/Terra Thermal Anomalies/Fire 8-Day",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD14A2)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD15A2H': {
		'name': "MODIS/Terra Leaf Area Index/FPAR",
		'level': 4,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD15A2H)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD15A2HGF': {
		'name': "MODIS/Terra Year-End Gap-Filled Leaf Area Index/FPAR",
		'level': 4,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD15A2HGF)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD16A2': {
		'name': "MODIS/Terra Net Evapotranspiration",
		'level': 4,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD16A2)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD16A2GF': {
		'name': "MODIS/Terra Year-End Gap-Filled Net Evapotranspiration",
		'level': 4,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD16A2GF)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD16A3': {
		'name': "MODIS/Terra Evapotranspiration/Latent Heat Flux",
		'level': 4,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(years=1),
		'filename_pattern': "(?P<product>MOD16A3)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD16A3GF': {
		'name': "MODIS/Terra Gap-Filled Evapotranspiration/Latent Heat Flux",
		'level': 4,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(years=1),
		'filename_pattern': "(?P<product>MOD16A3GF)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD17A2H': {
		'name': "MODIS/Terra Gross Primary Productivity",
		'level': 4,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD17A2H)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD17A2HGF': {
		'name': "MODIS/Terra Gap-Filled Gross Primary Productivity",
		'level': 4,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD17A2HGF)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD17A3H': {
		'name': "MODIS/Terra Net Primary Production",
		'level': 4,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(years=1),
		'filename_pattern': "(?P<product>MOD17A3H)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD17A3HGF': {
		'name': "MODIS/Terra Gap-Filled Net Primary Production",
		'level': 4,
		'structure': "SIN grid",
		'spatial_resolution': 500,				# [m]
		'temporal_resolution': relativedelta(years=1),
		'filename_pattern': "(?P<product>MOD17A3HGF)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD21': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD21)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)",
		'along_track_dimension_name': ["swath_lines_1km", "swath_lines_5km"],
		'across_track_dimension_name': ["swath_pixels_1km", "swath_pixels_5km"]
	},
	'MOD21A1D': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity Daily Day",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD21A1D)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD21A1N': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity Daily Night",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(days=1),
		'filename_pattern': "(?P<product>MOD21A1N)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD21A2': {
		'name': "MODIS/Terra Land Surface Temperature/Emissivity 8-Day",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD21A2)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD28C2': {
		'name': "MODIS/Terra Water Reservoir 8-Day",
		'level': 3,
		'structure': "table",
		'temporal_resolution': relativedelta(days=8),
		'filename_pattern': "(?P<product>MOD28C2)\.A(?P<date>\d{7})\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD28C3': {
		'name': "MODIS/Terra Water Reservoir Monthly",
		'level': 3,
		'structure': "table",
		'temporal_resolution': relativedelta(months=1),
		'filename_pattern': "(?P<product>MOD28C3)\.A(?P<date>\d{7})\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD35_L2': {
		'name': "MODIS/Terra Cloud Mask and Spectral Test Results",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': [250, 1000],		# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MOD35_L2)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD44B': {
		'name': "MODIS/Terra Vegetation Continuous Fields",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 250,				# [m]
		'temporal_resolution': relativedelta(years=1),
		'filename_pattern': "(?P<product>MOD44B)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MOD44W': {
		'name': "MODIS/Terra Global Land Water Mask Derived from MODIS and SRTM",
		'level': 3,
		'structure': "SIN grid",
		'spatial_resolution': 250,				# [m]
		'temporal_resolution': relativedelta(years=1),
		'filename_pattern': "(?P<product>MOD44W)\.A(?P<date>\d{7})\."
			"(?P<tile>h(?P<h>\d{2})v(?P<v>\d{2}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MODATML2': {
		'name': "MODIS/Terra Aerosol, Cloud and Water Vapor Subset",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': [5000, 10000],	# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MODATML2)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MODCSR_G': {
		'name': "MODIS/Terra Clear Radiance Statistics Indexed to Global Grid",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': 10000,			# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MODCSR_G)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	# 'MODCSR_D': {
	# 	'name': "MODIS/Terra Clear Sky Radiance Statistics",
	# 	'level': 3,
	# 	'structure': "??",
	# 	'spatial_resolution': 25000,			# [m]
	# 	'temporal_resolution': relativedelta(days=1),
	# 	'filename_pattern': "(?P<product>MODCSR_D)\.A(?P<date>\d{7})\."
	# 		"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	# },
	# 'MODCSR_8': {
	# 	'name': "MODIS/Terra Clear Sky Radiance 8-Day Composite",
	# 	'level': 3,
	# 	'structure': "??",
	# 	'spatial_resolution': 25000,			# [m]
	# 	'temporal_resolution': relativedelta(days=1),
	# 	'filename_pattern': "(?P<product>MODCSR_8)\.A(?P<date>\d{7})\."
	# 		"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	# },
	# 'MODCSR_B': {
	# 	'name': "MODIS/Terra 8-Day Clear Sky Radiance Bias",
	# 	'level': 3,
	# 	'structure': "??",
	# 	'spatial_resolution': 1,				# [deg]
	# 	'temporal_resolution': relativedelta(days=1),
	# 	'filename_pattern': "(?P<product>MODCSR_8)\.A(?P<date>\d{7})\."
	# 		"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	# },
}

MODIS_AQUA_PRODUCTS = {
	'MYD03': {
		'name': "MODIS/Aqua Geolocation",
		'level': '1a',
		'structure': "swath",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MYD03)\.A(?P<timestamp>(?P<date>\d{7})"
			"\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)",
		'band_dimension_name': "numbands",
		'along_track_dimension_name': ["nscans*10", "nscans*20", "nscans"],
		'across_track_dimension_name': ["mframes", "mframes*2"],
		'labels': {
			'latitude_name': "Latitude",
			'longitude_name': "Longitude",
			'range_name': "Range",					# check if implemented
			'elevation_name': "Height",				# check if ortho
			'timestamp_name': "EV_center_time",		# check if works
			'solar_azimuth_name': "SolarAzimuth",
			'solar_zenith_name': "SolarZenith",
			# attitude_angles, orb_pos, orb_vel, 
		},
	},
	'MYD14': {
		'name': "MODIS/Aqua Thermal Anomalies/Fire",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': 1000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MYD14)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)",
		'along_track_dimension_name': "number_of_scan_lines",
		'across_track_dimension_name': "pixels_per_scan_line"
	},
}

MODIS_COMBINED_PRODUCTS = {}

MODIS_ANCILLARY_PRODUCTS = {
	'MODARNSS': {
		'name': "Atmosphere Aeronet Subset",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': [250, 500, 1000],	# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MODARNSS)\.(?P<location>\w+)\."
			"A(?P<timestamp>(?P<date>\d{7})\.(?P<time>\d{4}))\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MODBMSS': {
		'name': "Atmosphere BELMANIP Subset",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': [250, 500, 1000],	# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MODBMSS)\.(?P<location>\w+)\."
			"A(?P<timestamp>(?P<date>\d{7})\.(?P<time>\d{4}))\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
	'MODFNSS': {
		'name': "Atmosphere FluxNet Subset",
		'level': 2,
		'structure': "swath",
		'spatial_resolution': [250, 500, 1000],	# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<product>MODFNSS)\.(?P<location>\w+)\."
			"A(?P<timestamp>(?P<date>\d{7})\.(?P<time>\d{4}))\."
			"(?P<version>\d{3})\.(?P<processing_timestamp>\d{13})\.(?P<ext>hdf)"
	},
}


#---------------------------------- CLASSES ----------------------------------#

#################################### MODIS ####################################
class MODIS(WhiskbroomScanner):
	"""Defines a MODIS object on either Terra or Aqua.
	
	Functions:
		__init__ -- Initializes a MODIS instrument object for either the Terra 
			or Aqua platforms.
		parse_meta -- Parses MODIS metadata.
		set_state -- Sets the platform's state information (position and 
			velocity).
		corners -- Gets the corner geolocation coordinates of a given MODIS 
			dataset.
		get_radiance -- Gets the radiance or reflectance data (and associated 
			uncertainty data) from a MODIS Level 1B data file for a given band 
			or set of bands.
	
	Returns:
		- An object defining a MODIS instrument for the Terra or Aqua platform.
	"""

	# Constructor method
	def __init__(self, /, platform, **kwargs):
		"""Initializes a MODIS instrument object for either the Terra or Aqua 
		platforms.
		
		Parameters:
			platform: type=Platform|str
				- The platform (Terra or Aqua) on which this MODIS instance is 
				located.
		
		External Modules:
			- numpy -- https://numpy.org/
		"""
		from numpy import pi
		from ..config import AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS
		from ..platform import Platform, _get_standard_platform_id
		from ..ancillary import set_sigfigs
		
		# Get standard platform ID
		if isinstance(platform, Platform):
			platform_id = platform.id.lower()
		elif isinstance(platform, str):
			available_platform_instruments = {k:v for k,v in \
				AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS.items() if k in \
				['terra','aqua']}
			platform_id = _get_standard_platform_id(platform, \
				available_platform_instruments)
		else:
			platform_id = platform

		# Get products for platform
		if platform_id == 'terra':
			products = MODIS_TERRA_PRODUCTS | MODIS_COMBINED_PRODUCTS | \
				MODIS_ANCILLARY_PRODUCTS
		elif platform_id == 'aqua':
			products = MODIS_AQUA_PRODUCTS | MODIS_COMBINED_PRODUCTS | \
				MODIS_ANCILLARY_PRODUCTS
		elif platform_id is None:
			products = MODIS_TERRA_PRODUCTS | MODIS_AQUA_PRODUCTS | \
				MODIS_COMBINED_PRODUCTS | MODIS_ANCILLARY_PRODUCTS
		else:
			raise ValueError("Instance of MODIS instrument not recognized.")
		
		# Update products with 'available_products' argument if provided
		if 'available_products' in kwargs and \
		  isinstance(kwargs['available_products'], dict):
			products.update(kwargs['available_products'])
		
		# Set the geolocation product ID by platform
		# geo_product_key = 'platform.id'
		# geo_product = {'terra': "MOD03", 'aqua': "MYD03"}
		
		# Set scan widths, swath widths, and pixel offsets by spatial resolution
		scan_width = {250: 40, 500: 20, 1000: 10}
		swath_width = {250: 5416, 500: 2708, 1000: 1354}
		pixel_offset = {250: (0,-3/2), 500: (0,-1/2), 1000: 0}
		scan_width_key = swath_width_key = pixel_offset_key = \
			'spatial_resolution'
		
		# Set IFOV and pixel scale by spatial resolution
		rpm = 20.3092					# [rot. per min] rotation rate
		sample_time_1km = 333.333e-6	# [μs] sample time for 1km detector
		# sample_frame = 2				# fraction of pixel area spent sampling
		# ifov_1km = 2*pi*(sample_time_1km/sample_frame)/(60/rpm)*4		# unclear why off by factor of 4
		ifov_1km = 2*pi*sample_time_1km/(60/rpm)*2		# unclear why off by factor of 2
		sigfigs = 6
		ang250 = set_sigfigs(ifov_1km/4, sigfigs)
		ang500 = set_sigfigs(ifov_1km/2, sigfigs)
		ang1000 = set_sigfigs(ifov_1km, sigfigs)
		ang2000 = set_sigfigs(2*ifov_1km, sigfigs)
		pixel_scale = {250: ang250, 500: ang500, 1000: ang1000}
		ifov = {250: (ang250, ang500), 500: (ang500, ang1000), \
			1000: (ang1000, ang2000)}
		pixel_scale_key = ifov_key = 'spatial_resolution'

		# Set pixel response function
		prf = lambda i,j: max(0, 1-abs(j-1/2))

		# Initialize MODIS object
		# super().__init__('modis', platform=platform, \
		# 	formatters=MODIS_PRODUCT_FORMATTERS, available_products=products, \
		# 	geo_product=geo_product, geo_product_key=geo_product_key, \
		# 	scan_width=scan_width, scan_width_key=scan_width_key, \
		# 	swath_width=swath_width, swath_width_key=swath_width_key, \
		# 	pixel_offset=pixel_offset, pixel_offset_key=pixel_offset_key, \
		# 	ifov=ifov, ifov_key=ifov_key, pixel_scale=pixel_scale, \
		# 	pixel_scale_key=pixel_scale_key, prf=prf, **kwargs)
		super().__init__('modis', platform=platform, \
			formatters=MODIS_PRODUCT_FORMATTERS, \
			reverse_formatters=MODIS_PRODUCT_REVERSE_FORMATTERS, \
			available_products=products, scan_width=scan_width, \
			scan_width_key=scan_width_key, swath_width=swath_width, \
			swath_width_key=swath_width_key, pixel_offset=pixel_offset, \
			pixel_offset_key=pixel_offset_key, ifov=ifov, ifov_key=ifov_key, \
			pixel_scale=pixel_scale, pixel_scale_key=pixel_scale_key, prf=prf, \
			**kwargs)
		
		# Set dimension renaming function
		def _rename_dimension(dim_name):
			return dim_name[:dim_name.index(':')] if ':' in dim_name else \
				dim_name
		self._rename_dimension = _rename_dimension
	
	# Static method to parse MODIS metadata
	@staticmethod
	def parse_meta(metadata, format='xml'):
		"""Parses MODIS metadata.
	
		Parameters:
			metadata: type=str
				- The MODIS dataset for which to set the platform state 
				information.
			format: type=str, default='xml'
				- The output format type; one of 'xml' for XML or 'dict' for a 
				dictionary.

		Returns:
			- Either an xml object or a dict object with the parsed metadata 
			information.
		"""
		import re
		if format == 'xml':
			from xml.etree import ElementTree as ET

		# Check format input
		assert format in ['xml', 'dict']
		isxml = format == 'xml'

		# Convert string to integer or float
		def _tonum(text):
			try:
				return int(text)
			except:
				try:
					return float(text)
				except:
					return text

		# Build search patterns
		pattern = re.compile(r"^(?P<indent>\s*)(?P<key>\w+)\s*=\s*(?P<text>\"?(?P<value>.*?)(?P<string>\"?))\s*$")
		list_pattern = re.compile(r"^\s*\((.+?)\)\s*$")

		# Initialize XML or dictionary object
		root = ET.Element("MODISMETADATA") if isxml else dict()
		current_tree = [root]

		# Loop thru lines of metadata
		for iline,line in enumerate(metadata.splitlines()):
			# Continue if empty line or break if end of document
			if not line.strip():
				continue
			elif line.strip() == "END":
				break

			# Match line to pattern
			m = re.fullmatch(pattern, line)
			if not m:
				raise IOError(f"Cannot parse line {iline}.")
			
			# Create new element
			if m.group('key') in ["GROUP", "OBJECT"]:
				key = m.group('value')
				if isxml:
					current_tree.append(ET.SubElement(current_tree[-1], key))
				else:
					current_tree[-1][key] = dict()
					current_tree.append(current_tree[-1][key])
			
			# Close element
			elif m.group('key') in ["END_GROUP", "END_OBJECT"]:
				current_tree.pop()
			
			# Save attributes, converting to tuple, ints and floats as needed
			else:
				key = m.group('key')
				if isxml:
					value = m.group('text')
					current_tree[-1].set(key, value)
				else:
					value = m.group('value')
					if not m.group('string'):
						if current_tree[-1].get('NUM_VAL', 1) > 1:
							value = tuple(m2.group(1) if \
								(m2:=re.match(r"\"(.*)\"", v.strip())) else \
								_tonum(v) for v in re.fullmatch(list_pattern, \
								value).group(1).split(','))
						else:
							value = _tonum(value)
					current_tree[-1][key] = value
		
		# Delete temporary root folder if only one child
		# if isxml and len(root) == 1:
		# 	root = root[0]

		# Return XML or dictionary object
		return root
	
	# Method to set Terra/Aqua state information (position, velocity)
	def set_state(self, /, dataset, line=None, **kwargs):
		"""Sets the platform's state information (position and velocity).
	
		Parameters:
			dataset: type=Dataset
				- The MODIS dataset for which to set the platform state 
				information.
			line: type=int, default=None
				- The scan line index for which to set the platform state 
				information.  If `None`, will set the state for the whole 
				dataset instead of its scan.

		External Modules:
			- numpy -- https://numpy.org/
		"""
		import numpy as np
		from ..platform import xyz2lla, uvw2enu
		from ..data import sort_dims
		from ..ancillary import lon_convert

		# Check for link between dataset and instrument object
		if not self.related_object(dataset=dataset):
			raise ValueError("The given dataset is either not linked to an "
				"instrument object or it belongs to a different instrument.")

		# Check for linked platform
		if not hasattr(self, 'platform'):
			raise ValueError("The instrument has no linked platform in order "
				"to set its state.")

		# Check for swath structure
		if dataset.product.structure != "swath":
			raise RuntimeError("The platform state can only be set for datasets "
				"with a swath structure. To override, call 'set_state' from the "
				"platform directly.")
		
		# Get state from associated MOD03/MYD03 product
		# m3p = dataset.product.id[:3]+'03'
		m3p = self.geo_product
		m3ds = m3p != dataset.product.id
		if m3ds:
			m3ds = dataset.cousin_dataset(m3p)
			if m3ds:
				# Get ECEF coordinates
				nscans = m3ds.read(attr='Number of Scans')
				s = slice((nscans-1)//2, (nscans+2)//2) if line is None else \
					slice(line//10, line//10+1)
				x,y,z = m3ds.extract('orb_pos', s).mean(axis=0)			# [m]
				u,v,w = m3ds.extract('orb_vel', s).mean(axis=0)			# [m/s]

				# Convert to WGS84 geodetic
				lon,lat,alt = xyz2lla(x, y, z)
				enu = uvw2enu(u, v, w, lat, lon)

				# Update results
				kwargs.update(dict(lat=lat, lon=lon, alt=alt, vel=enu))

		# Get state from given dataset
		if not m3ds:
			# Update lat/lon information
			if 'Latitude' in dataset and 'Longitude' in dataset:
				dims = sort_dims(dataset.read(var='Latitude', dim=True))
				shape = tuple(d['size'] for d in dims)
				s = tuple(slice((size-1)//2, (size+2)//2) for size in shape)
				lat = dataset.extract('Latitude', s).mean()
				lon = dataset.extract('Longitude', s).mean()
				kwargs.update(lat=lat, lon=lon)
			elif 'CoreMetadata.0' in dataset:
				metadata = dataset.read(attr="CoreMetadata.0")
				metadata = self.parse_meta(metadata, format='dict')
				group = metadata["INVENTORYMETADATA"]["SPATIALDOMAINCONTAINER"] \
					["HORIZONTALSPATIALDOMAINCONTAINER"]["GPOLYGON"] \
					["GPOLYGONCONTAINER"]["GRINGPOINT"]
				gring_lats = group["GRINGPOINTLATITUDE"]["VALUE"]
				gring_lons = group["GRINGPOINTLONGITUDE"]["VALUE"]
				lat = np.mean(gring_lats)
				lon = lon_convert(np.mean(lon_convert(gring_lons, gring_lons[0])))
				kwargs.update(lat=lat, lon=lon)
			
			# Update altitude
			if 'Range' in dataset and 'Height' in dataset:
				dims = sort_dims(dataset.read(var='Range', dim=True))
				shape = tuple(d['size'] for d in dims)
				s = tuple(slice((size-1)//2, (size+2)//2) for size in shape)
				r = dataset.extract('Range', s)
				h = dataset.extract('Height', s)
				alt = round(np.mean(r+h))
				kwargs.update(alt=alt)

		# Set platform state
		if hasattr(self, 'platform'):
			self.platform.set_state(**kwargs)
	
	# Method to get the corners of a MODIS granule
	def corners(self, /, dataset=None, extend=False, **kwargs):
		"""Gets the corner geolocation coordinates of a given MODIS dataset.
	
		Parameters:
			dataset: type=Dataset, default=None
				- The dataset from which to get the geolocation data (latitude/
				longitude).  If `None`, the geolocation dataset will be searched 
				using the extra keyword arguments to identify the file of 
				interest (these will be passed to the `product.find_files` 
				method).
			extend: type=bool, default=False
				- If `True`, will extend the returned corner data coordinates to 
				the outer edges of the outer pixels instead of the pixel centers.
			**kwargs:
				- 

		External modules:
			- numpy -- https://numpy.org/

		Returns:
			- A numpy ndarray of shape (4, 2) with the corner coordinates as 
			(latitude, longitude) pairs.
		"""
		import numpy as np
		from ..ancillary import findattr

		# Use parent class method if extending corners to edge of pixels
		if extend:
			return super().corners(dataset=dataset, extend=extend, **kwargs)
		
		# Load geolocation dataset if needed
		if dataset is None:
			geo_product_id = findattr(self, 'geo_product')
			geo_product = self.load_product(geo_product_id)
			for i,(geo_file,geo_file_attr) in \
			  enumerate(geo_product.find_files(**kwargs)):
				if i > 0:
					raise ValueError(f"Multiple files found for {geo_product_id} "
						"and given keyword arguments - try adding more arguments "
						"that collectively identifies only one file.")
			dataset = geo_product.load_dataset(geo_file)

		# Check for link between dataset and instrument object
		elif not self.related_object(dataset=dataset):
			raise ValueError("The given dataset is either not linked to an "
				"instrument object or it belongs to a different instrument.")

		# Check for swath structure
		if dataset.product.structure != "swath":
			raise RuntimeError("The platform state can only be set for datasets "
				"with a swath structure. To override, call 'set_state' from the "
				"platform directly.")
		
		# Return corners using MODIS attributes, with fallback to parent class
		if 'CoreMetadata.0' in dataset:
			metadata = dataset.read(attr="CoreMetadata.0")
			metadata = self.parse_meta(metadata, format='dict')
			group = metadata["INVENTORYMETADATA"]["SPATIALDOMAINCONTAINER"] \
				["HORIZONTALSPATIALDOMAINCONTAINER"]["GPOLYGON"] \
				["GPOLYGONCONTAINER"]["GRINGPOINT"]
			lats = group["GRINGPOINTLATITUDE"]["VALUE"]
			lons = group["GRINGPOINTLONGITUDE"]["VALUE"]
			cstack = np.ma.column_stack if np.ma.isMA(lats) or \
				np.ma.isMA(lons) else np.column_stack
			return cstack((lats, lons))
		else:
			return super().corners(dataset=dataset, extend=extend, **kwargs)
	
	# Method to get the radiance, reflectance or brightness temperatures from 
	# the Level 1B data files
	def get_radiance(self, /, measurement='radiance', file=None, band=True, 
	  s=slice(None), resolution=None, uncertainty=False, output='array', 
	  **kwargs):
		"""Gets the radiance or reflectance data (and associated uncertainty 
		data) from a MODIS Level 1B data file for a given band or set of bands.
	
		Parameters:
			measurement: type=str, default='radiance'
				- The measurement ('radiance'/'rad' or 'reflectance'/'ref') of 
				data to output.
			file: type=pathlib.Path|str, default=None
				- The file path of the file to open.  If `None`, will use the 
				additional keyword arguments to locate a file.
			band: type=int|str|list|bool, default=True
				- The band (as an integer or string) or list of bands for which 
				to get the data.  If True, will output all bands if 
				`measurement` is 'radiance', or all reflectance bands if 
				`measurement` is 'reflectance'.  Dual gain bands (13 and 14) 
				will be combined if 'lo' or 'hi' are not appended to the band 
				number.
			s: type=slice|int|tuple, default=slice(None)
				- A slice to apply to the data.  Note that if the band 
				dimension is sliced such that requested bands are eliminated, 
				the program will throw an error.
			resolution: type=int, default=None
				- The maximum output resolution to use.  For instance, if a 
				quarter-kilometer resolution band is requested but `resolution` 
				is set to 500, the half-kilometer product is used instead.
			uncertainty: type=bool, default=False
				- If `True`, will also calculate and output the uncertainty.
			output: type=str, default='array'
				- The output format: 'array' for a single ndarray, 'list' for a 
				list of ndarrays, or 'dict' for a dictionary of ndarrays 
				referenced by the band ID.  Note that if bands with multiple 
				resolutions are requested and `output` is 'array', then the 
				down-sampled data for the higher-resolution bands will be used.
			**kwargs:
				- Additional keyword arguments for the following functions:
					- esm.product.find_files: timestamp, date, time, version, 
					processingtimestamp, ext, directory
				- If more than one file is found with these specifications, an 
				error will be raised.

		External Modules:
			- numpy -- https://numpy.org/

		Returns:
			- The radiance or reflectance data for the first file found with 
			the `kwargs` dictionary as either an ndarray, list or dictionary, 
			or a tuple where the second item is the uncertainty data as a 
			fraction (between 0-1).  Radiance units are W/m^2/sr/μm.
		"""
		import numpy as np
		from ..data import broadcast_prep, full_slice, slice_to_array
		from ..ancillary import iterable, assert_slice

		# Test input data types
		s = assert_slice(s)

		# Format output argument
		# output = "array" if output is None else output.strip().lower()
		output = output.strip().lower()
		# output_list = 'list' in output
		# output_array = 'array' in output
		# output_dict = 'dict' in output
		# output_granule = 'granule' in output or 'scene' in output
		# output_data = 'data' in output or not output_granule
		# assert sum(map(int, [output_list, output_array, output_dict])) == 1
		# assert sum(map(int, [output_data, output_granule])) == 1
		# assert not (output_array and output_granule)
		# output_array = output == 'array'

		# Set dataset names dictionary
		dataset_ref = {
			'EV_250_RefSB': (250, "QKM", 40, [1,2], {500: \
				"EV_250_Aggr500_RefSB", 1000: "EV_250_Aggr1km_RefSB"}), 
			'EV_500_RefSB': (500, "HKM", 20, [3,4,5,6,7], {1000: \
				"EV_500_Aggr1km_RefSB"}),
			'EV_1KM_RefSB': (1000, "1KM", 10, [8,9,10,11,12,'13lo','13hi', 
				'14lo','14hi',15,16,17,18,19,26], dict()),
			'EV_1KM_Emissive': (1000, "1KM", 10, list(range(20, 26))+ \
				list(range(27,37)), dict())
		}

		# Get the value to measure
		measurement = measurement.strip().lower()
		if measurement not in ['radiance', 'rad', 'reflectance', 'ref']:
			raise ValueError("'measurement' must be either 'radiance' or "
				"'reflectance'")
		if measurement == 'rad':
			measurement = 'radiance'
		elif measurement == 'ref':
			measurement = 'reflectance'

		# Format band input
		if band is True:
			if measurement == 'radiance':
				band = list(range(1,37))
				# vars = list(dataset_ref)
			else:
				band = list(range(1,20))+[26]
				# vars = list(d for d in dataset_ref if 'Emissive' not in d)
			single_band = False
			band_dict = {b:b for b in band}
			# dualband13 = dualband14 = True
			# band[(i:=band.index(13)):i+1] = ['13lo', '13hi']
			# band[(i:=band.index(14)):i+1] = ['14lo', '14hi']
			# resolution = 1000

			# prod = "1KM"
			# product_id = f"{self.data_tag}02{prod}"
			# product = self.load_product(product_id, **kwargs)
			# try:
			# 	file,reg = next(product.find_files(**kwargs))
			# except:
			# 	raise ValueError(f"Could not find a {product} file "
			# 		"with given specifications.")
			# ds = product.load_dataset(file)
		else:
			# Format input band(s) for comparison
			single_band = not iterable(band)
			if single_band:
				band = [band]
			# dualband13 = dualband14 = False
			band_dict = dict()
			for i,iband in enumerate(band):
				# if str(iband) == '13':
					# dualband13 = True
					# band[i:i+1] = ['13lo', '13hi']
				# elif str(iband) == '14':
					# dualband14 = True
					# band[i:i+1] = ['14lo', '14hi']
				# else:
					try:
						band_id = int(iband)
						band_dict[band_id] = iband
						band[i] = band_id
					except:
						band_id = iband.strip().lower()
						band_dict[band_id] = iband
						band[i] = band_id
			# band = [b for i,b in enumerate(band) if b not in band[:i]]

		# Initialize dictionary of band data
		data_dict = {b:None for i,b in enumerate(band) if b not in band[:i]}
		if uncertainty:
			udata_dict = data_dict.copy()
		if 13 in band:
			data_dict.update({b:None for b in ['13lo', '13hi']})
			if uncertainty:
				udata_dict.update({b:None for b in ['13lo', '13hi']})
		if 14 in band:
			data_dict.update({b:None for b in ['14lo', '14hi']})
			if uncertainty:
				udata_dict.update({b:None for b in ['14lo', '14hi']})
		
		# Find spatial resolution and dataset variable that encompasses all 
		# requested bands/data
		all_bands = set()
		vars = []
		for var,(res,prod,det,bands,agg_names) in dataset_ref.items():
			# Update info for loop
			# bands_ext = {int(re.match(r'\d+', b).group(0)) if \
			# 	isinstance(b, str) else b for b in bands}
			# bands_ext.update([str(b) for b in bands])
			if set(bands).intersection(data_dict):
				if 'Emissive' in var and measurement == 'reflectance':
					raise ValueError("Cannot convert emissive bands to reflectance.")
				vars.append(var)
			
			# Check for completed list of bands
			all_bands.update(bands)
			if '13lo' in bands:
				all_bands.update([13])
			if '14lo' in bands:
				all_bands.update([14])
			if not all_bands.issuperset(band):
				continue

			# Check for correct resolution
			if resolution is not None and res > resolution:
				raise ValueError("Given resolution requirement is too high "
					"for given band(s) or available data.")
			elif resolution is not None and res < resolution:
			# elif output_array and resolution is not None and res < resolution:
				continue
			
			# Get the product object
			product_id = f"{self.data_tag}02{prod}"
			product = self.load_product(product_id, **kwargs)

			# Get the file and file name attributes
			if file is None:
				files = product.find_files(**kwargs)
				for i in range(2):
					try:
						file,attrdict = next(files)
					except:
						if not i:
							if var == list(dataset_ref)[-1]:
								raise ValueError(f"Could not find a {product.id} "
									"file with given specifications.")
						break
				else:
					raise ValueError(f"Multiple files found for {product.id} "
						"product with given specifications.")
			# else:
			# 	attrdict = product.get_filename_attrs(file)
			if file is None:
				continue
			ds = product.load_dataset(file)
			break

			# Get the dataset of the first identified file
			# try:
			# 	file,reg = next(product.find_files(**kwargs))
			# except:
			# 	if var == list(dataset_ref)[-1]:
			# 		raise ValueError(f"Could not find a {product} file "
			# 			"with given specifications.")
			# 	continue
			# ds = product.load_dataset(file)
			# break

		# Function to convert reflectance channel data accurately
		def _ref_rad_convert(reflectance, bands, band_idim, s, shape):
			# Determine if multiple bands are given
			single_band = not iterable(bands)
			if single_band:
				bands = [bands]

			# Get detector indices for given bands
			idet0 = 0
			for _,_,det0,bands0,_ in dataset_ref.values():
				if bands[0] in bands0:
					break
				idet0 += det0*len(bands0)
				# else:
				# 	idet0 += idet*len(ibands[:ibands.index(band)])
			ibands = np.atleast_1d(s[band_idim])
			idet = idet0+np.array([list(range(i*det0,(i+1)*det0)) for i in \
				ibands])
			
			# Get attributes for converting reflectance to radiance
			es_dist = ds.read(attr="Earth-Sun Distance")
			irrad_pi = ds.read(attr="Solar Irradiance on RSB Detectors over pi")\
				[idet.flat]
			if det0 > det:
				irrad_pi = irrad_pi.reshape(-1, det0//det).mean(axis=1)
			irrad_pi = irrad_pi.reshape(-1, det)
			track_idim = ds.dim_index('along_track', var)
			nscans = shape[track_idim]//det + int(bool(shape[track_idim] % det))
			irrad_pi = np.tile(irrad_pi, nscans)[(..., s[track_idim])]

			# Return radiance for reflectance bands
			radiance = reflectance * broadcast_prep(irrad_pi/es_dist**2, \
				shape, max(band_idim,track_idim))
			return radiance[0] if single_band and radiance.shape[0] == 1 else \
				radiance
		
		# Loop thru the dataset variables
		# data = None
		for var in vars:
			# Get the variable name for the spatial resolution
			var_info = dataset_ref[var]
			if var_info[0] != res:
				var = var_info[4][res]

			# Get the scale and offset labels to use
			ref_rad_convert = measurement == 'radiance' and 'Emissive' not in var
			if measurement == 'reflectance' or ref_rad_convert:
				scale_factor = "reflectance_scales"
				offset = "reflectance_offsets"
			else:
				scale_factor = "radiance_scales"
				offset = "radiance_offsets"
			
			# 
			# kwargs2 = {k:v for k,v in kwargs.items() if k != 'dims'}
			# g = Granule(var, dataset=ds, s=s, dims=True, **kwargs2)

			# Get the index for the dimension of bands
			idim = ds.dim_index('band', var)
			# band_dim = findattr(ds, 'band_dimension_name', None)
			# if band_dim is None:
			# 	idim = None
			# 	g = Granule(var, dataset=ds, dims=True, **kwargs)
			# 	for i,d in enumerate(g.dimensions.values()):
			# 		if d.get('id', None) == 'band':
			# 			idim = i
			# 			break
			# elif iterable(band_dim):
			# 	dims = ds.read(var=var, dim=True)
			# 	band_dim = set(band_dim).intersection(dims).pop()
			# 	idim = dims[band_dim]['index']
			# else:
			# 	idim = ds.read(var=var, dim=band_dim)['index']
			if idim is None:
				raise ValueError("Could not find the band dimension.")
			
			# Get the indicies of the requested bands within the band dimension
			# ibands,bands = map(list, zip(*[(i,b) for i,b in \
			# 	enumerate(var_info[3]) if b in data_dict]))
			
			# Get the slice object for extracting data for the requested bands
			shape = ds.get_shape(var)
			s2 = list(full_slice(s, shape))
			is2 = slice_to_array(s2[idim], (shape[idim],))
			if not iterable(is2):
				is2 = [is2]
			# if not set(is2).issuperset(ibands):
			# 	raise ValueError(f"The band dimension (index {idim}) in "
			# 		"the 's' slice object eliminated necessary bands prior "
			# 		"to extraction.")
			# s2[idim] = ibands
			# s2 = tuple(s2)

			# Check slice and get data for each requested band
			for i,b in enumerate(var_info[3]):
				# Set slice for band
				if b not in data_dict:
					continue
				if i not in is2:
					raise ValueError(f"The band dimension (index {idim}) in "
						"the 's' slice object eliminated necessary bands prior "
						"to extraction.")
				s2[idim] = i

				# Get data for band
				# if output_granule:
				# 	data_dict[b] = Granule(var, dataset=ds, s=s2, \
				# 		scale_factor=scale_factor, offset=offset, **kwargs)
				# 	if ref_rad_convert:
				# 		data_dict[b].data = _ref_rad_convert(data_dict[b].data, \
				# 			[b], idim, s2, shape)
				# else:
				data_dict[b] = ds.extract(var, s=tuple(s2), \
					scale_factor=scale_factor, offset=offset)
				if ref_rad_convert:
					data_dict[b] = _ref_rad_convert(data_dict[b], b, \
						idim, tuple(s2), shape)
				
				# Get uncertainty data for band
				if uncertainty:
					uvar = f"{var}_Uncert_Indexes"
					udata_dict[b] = ds.extract(uvar, s=tuple(s2), \
						scale_factor='scaling_factor', conversion="/+")
					isma = np.ma.isMA(udata_dict[b])
					spec_uncert = ds.read(var=uvar, \
						attr='specified_uncertainty')[i]
					udata_dict[b] = spec_uncert*np.ma.exp(udata_dict[b])/100
					if not np.ma.is_masked(udata_dict[b]) and not isma:
						udata_dict[b] = np.ma.getdata(udata_dict[b])
			
			# Get combined channels for dual gain 13 and 14 bands
			if var == 'EV_1KM_RefSB':
				for b in [13, 14]:
					if b in data_dict:
						# if output_granule:
						# else:
							data_dict[b] = np.ma.where(data_dict[f"{b}hi"].mask, \
								data_dict[f"{b}lo"], data_dict[f"{b}hi"])
							if uncertainty:
								udata_dict[b] = np.ma.where( \
									data_dict[f"{b}hi"].mask, \
									udata_dict[f"{b}lo"], udata_dict[f"{b}hi"])

			# Check for completed data extraction
			if not any(v is None for v in data_dict.values()):
				break

			# Get the data and join to previously extracted data
			# idata = ds.extract(var, s=s2, scale_factor=scale_factor, \
			# 	offset=offset)
			# if ref_rad_convert:
			# 	idata = _ref_rad_convert(idata, bands, idim, s2, shape)
		
		# 
		# for b,idata in data_dict.items():
		# 	s0 = tuple(s2)
		# 	data_dict[b] = Granule((str(b), idata), dataset=ds, attrs=attrs, )

		# Return radiance/reflectance data and uncertainty data as dictionary
		if output == 'dict':
			data = {band_dict[k]:data_dict[k] for i,k in enumerate(band) if k \
				not in band[:i]}
			if uncertainty:
				udata = {band_dict[k]:udata_dict[k] for i,k in enumerate(band) \
					if k not in band[:i]}
				return (data, udata)
			return data
		
		# Return radiance/reflectance data and uncertainty data as list
		elif output == 'list':
			data = [data_dict[b] for b in band]
			if uncertainty:
				udata = [udata_dict[b] for b in band]
				return (data, udata)
			return data
		
		# Return radiance/reflectance data and uncertainty data as ndarray
		elif output == 'array':
			# Compile data into single array
			for b in band:
				try:
					concatenate = np.ma.concatenate if np.ma.isMA(data) or \
						np.ma.isMA(data_dict[b]) else np.concatenate
					data = concatenate((data, data_dict[b][None]))  #, axis=idim)
				except:
					data = data_dict[b][None]
				if uncertainty:
					try:
						concatenate = np.ma.concatenate if np.ma.isMA(udata) \
							or np.ma.isMA(udata_dict[b]) else np.concatenate
						udata = concatenate((udata, udata_dict[b][None]))
					except:
						udata = udata_dict[b][None]
			
			# Position band dimension
			idim = sum([not isinstance(size, (int, np.integer)) for size in \
				s2[:idim]])
			if single_band and data.shape[0] == 1:
				data = data[0]
				if uncertainty:
					udata = udata[0]
			elif idim:
				data = np.moveaxis(data, 0, idim)
				if uncertainty:
					udata = np.moveaxis(udata, 0, idim)
			
			# Return data
			return (data, udata) if uncertainty else data
		
		# Throw error if 'output' invalid
		else:
			raise ValueError("'output' must be one of 'dict', 'list' or 'array'")
#################################### MODIS ####################################





		
# 		# VIIRS presets
# 		elif instrument == 'VIIRS':
# 			self.h = 833.		# 833km=design altitude, actual range: 828-856km
# 			if p:
# 				i = np.abs(np.array([.371,.742])-np.atleast_1d(p)[0]).argmin()
# 				self.p = (np.array([.371,.1293])*(i+1)).tolist()
# 			else:
# 				self.p = [.371,.1293]
# 			self.N = int(round(6304*0.742/self.p[0]))		# 6304 pixels at 0.742km resolution
# 			self.offset = 0.
# 			self.width = int(round(32*.371/self.p[0]))
		
# 		# Throw error if instrument not found
# 		else:
# 			raise ValueError(f"Preset orbital parameters for {instrument} " + \
# 				"not yet set internally")
		
	






# #--------------------------------- FUNCTIONS ---------------------------------#



# ############################## extractMASTERdata ##############################
# def extractMASTERdata(dataset, ds_slice=slice(None), mask=True, scale=True):
# 	"""Slices, scales and masks a MASTER dataset.
	
# 	Parameters:
# 	dataset: type=netCDF4.Variable|pyhdf.SD.SDS
# 		Dataset object handler.
# 	ds_slice: type=tuple|slice, default=slice(None)
# 		The slice (or tuple of slices for each dimension) to apply to the 
# 		dataset object when extracting the data. If `ds_slice` does not match 
# 		the number of dimensions of the dataset, the missing dimensions will be 
# 		filled in with `slice(None)`.
# 	mask: type=bool, default=True
# 		Set to False to keep invalid data in the output from being masked.
# 	scale: type=bool, default=True
# 		Set to False to keep the output data from having scaling applied to it.
	
# 	External modules:
# 	numpy -- https://numpy.org/
	
# 	Returns:
# 	The data for the `dataset` where scaling and offsets and masking has been 
# 	applied automatically, and where the dataset has been sliced appropriately 
# 	according to `ds_slice`.
# 	"""
# 	import numpy as np

# 	# Get file handler module
# 	mod = _getfilemodule(dataset).lower()

# 	# Validate dataset slice object
# 	if isinstance(ds_slice, slice):
# 		ds_slice = (ds_slice,)
# 	shape = dataset.shape if mod == 'netcdf4' else dataset[:].shape
# 	ds_slice = tuple(ds_slice) + (slice(None),) * max(0, \
# 		len(shape)-len(ds_slice))

# 	# Extract data from netCDF4 dataset
# 	if mod == 'netcdf4':
# 		# Set dataset settings to not automatically scale, and to not 
# 		# automatically fill if different fill scheme used
# 		dataset.set_auto_mask(mask and dataset.mask and "fill_value" not in \
# 			dataset.ncattrs())
# 		dataset.set_auto_scale(False)		# MASTER files store scale factors incorrectly
		
# 		# Get masked data
# 		data = dataset[ds_slice]
# 		if mask and not dataset.mask:
# 			fill_value = getattr(dataset, "fill_value", getattr(dataset, \
# 				"_FillValue", None))
# 			if fill_value is not None:
# 				data = np.ma.masked_equal(data, fill_value)
	
# 	# Extract data from pyhdf dataset
# 	elif mod == 'pyhdf':
# 		# Get masked data
# 		try:
# 			data = dataset[ds_slice]
# 		except:
# 			data = dataset[:][ds_slice]
# 		if mask:
# 			attrs = dataset.attributes()
# 			try:
# 				fill_value = attrs["fill_value"] if "fill_value" in attrs else \
# 					dataset.getfillvalue()
# 				data = np.ma.masked_equal(data, fill_value)
# 			except:
# 				pass
	
# 	# Delete mask if no fill values
# 	if np.ma.isMA(data) and not np.ma.is_masked(data):
# 		data = data.data
		
# 	# Scale data
# 	if scale:
# 		scale_factors = getattr(dataset, "scale_factor", getattr(dataset, \
# 			"scale", 1))
# 		if scale_factors is False:
# 			scale_factors = 1
# 		offsets = getattr(dataset, "add_offset", getattr(dataset, "offset", 0))
# 		if isinstance(scale_factors, list):
# 			scale_factors = np.array(scale_factors)
# 		if isinstance(offsets, list):
# 			offsets = np.array(offsets)
# 		n = scale_factors.size if not np.isscalar(scale_factors) else \
# 			(offsets.size if not np.isscalar(offsets) else 0)
# 		axis = shape.index(n) if n else -1
# 		axis_slice = ds_slice[axis]
# 		if not isinstance(axis_slice, slice) or axis_slice != slice(None):
# 			if not np.isscalar(scale_factors):
# 				scale_factors = scale_factors[axis_slice]
# 			if not np.isscalar(offsets):
# 				offsets = offsets[axis_slice]
# 			if np.isscalar(scale_factors) and np.isscalar(offsets):
# 				axis = -1
# 		swapaxes = np.ma.swapaxes if np.ma.isMA(data) else np.swapaxes
# 		data = swapaxes(swapaxes(data, axis, -1) * scale_factors + offsets, \
# 			-1, axis) if len(data.shape) > 1 else (data * scale_factors + \
# 			offsets)
	
# 	# Return data
# 	return data
# ############################## extractMASTERdata ##############################


# ################################ getMASTERdims ################################
# def getMASTERdims(f, dataset, mod=DEFAULT_MODULE):
# 	"""Returns an ordered dictionary of dimensions for a given dataset.
	
# 	Parameters:
# 	f: type=str|netCDF4.Dataset|pyhdf.SD.SD
# 		File handler (using either netCDF4 or pyhdf modules) or file path string.
# 	dataset: type=str
# 		Name of the dataset for which to get the dimensions.
# 	mod: type=str, default=DEFAULT_MODULE
# 		A string representation (either 'netcdf4' or 'pyhdf') of the module to 
# 		use to open the file if a file path is given for `f`.
	
# 	Returns:
# 	An ordered dictionary object (collections.OrderedDict) with any of the 
# 	following keys: 'lines' (along-track), 'samples' (along-scan), and 'bands' 
# 	(channels) whose values are the number of elements for those dimensions. 
# 	The order of the dimensions matches that of the dataset.
# 	"""
# 	from collections import OrderedDict

# 	# Settings
# 	dim_name_convert = dict(lines="scanline", samples="pixel", bands="channel")

# 	# Open new file
# 	newfile = isinstance(f, str)
# 	if newfile:
# 		f = openMASTERfile(f, mod)
# 	mod = _getfilemodule(f).lower()

# 	# Initialize ordered dimensions list
# 	dims = OrderedDict()

# 	# Get dimension names and values using netCDF4 module
# 	if mod == 'netcdf4':
# 		ds = readMASTERdataset(f, dataset)
# 		names,nums = zip(*[(d.name, d.size) for d in ds.get_dims()])
	
# 	# Get dimension names and values using pyhdf module
# 	elif mod == 'pyhdf':
# 		names = f.datasets()[dataset][0]
# 		nums = f.datasets()[dataset][1]
	
# 	# Construct ordered dictionary of dimensions
# 	for i,(name,n) in enumerate(zip(names, nums)):
# 		for short,search in dim_name_convert.items():
# 			if search in name.lower():
# 				dims.update([(short,n)])
# 		if len(dims) <= i:
# 			dims.update([(name,n)])
	
# 	# Close file
# 	if newfile:
# 		closeMASTERfile(f)
	
# 	# Return dimensions
# 	return dims
# ################################ getMASTERdims ################################


# ########################### centerMASTERwavelengths ###########################
# def centerMASTERwavelengths(f, effective=True, mod=DEFAULT_MODULE):
# 	"""Gets center wavelengths of MASTER bands.
	
# 	Parameters:
# 	f: type=str|netCDF4.Dataset|pyhdf.SD.SD
# 		File handler (using either netCDF4 or pyhdf modules) or file path string.
# 	effective: type=bool, default=True
# 		If set to True, will fill in center wavelengths of the IR bands with the 
# 		effective center wavelengths.
# 	mod: type=str, default=DEFAULT_MODULE
# 		A string representation (either 'netcdf4' or 'pyhdf') of the module to 
# 		use to open the file if a file path is given for `f`.
	
# 	External modules:
# 	numpy -- https://numpy.org/
	
# 	Returns:
# 	A list of center wavelengths for each MASTER band.
# 	"""
# 	import numpy as np

# 	# Open new file
# 	newfile = isinstance(f, str)
# 	if newfile:
# 		f = openMASTERfile(f, mod)

# 	# Get center wavelength bands
# 	bands = extractMASTERdata(readMASTERdataset(f, \
# 		"Central100%ResponseWavelength"))
	
# 	# Insert effective IR bands
# 	if effective:
# 		effective_ir_bands = extractMASTERdata(readMASTERdataset(f, 
# 			"EffectiveCentralWavelength_IR_bands"))
# 		bands = np.ma.where(effective_ir_bands.mask, bands, effective_ir_bands)
	
# 	# Remove mask if no fill value
# 	if np.ma.isMA(bands) and not np.ma.is_masked(bands):
# 		bands = bands.data

# 	# Close file
# 	if newfile:
# 		closeMASTERfile(f)
	
# 	# Return center wavelengths
# 	return bands
# ########################### centerMASTERwavelengths ###########################


# ############################## getMASTERwavebands ##############################
# def estimateMASTERsrf(f, wavelength=None, i=0, confidence=0.7609681, 
#   mod=DEFAULT_MODULE):
# 	"""Estimates the spectral response function (SRF) of MASTER bands for a 
# 	given confidence level assuming a normal distribution around the center.
	
# 	Parameters:
# 	f: type=str|netCDF4.Dataset|pyhdf.SD.SD
# 		File handler (using either netCDF4 or pyhdf modules) or file path string.
# 	wavelength: type=float, default=None
# 		The wavelength of the band for which to estimate the SRF.
# 	i: type=int, default=0
# 		The relative index of the band to choose for all MASTER bands that have 
# 		the same wavelength and match the given `wavelength` parameter.
# 	confidence: type=float, default=0.7609681
# 		The confidence level to use for selecting the width of the SRF. The 
# 		default confidence level represents what would be the full-width at 
# 		half-max (FWHM) range for a normal distribution.
# 	mod: type=str, default=DEFAULT_MODULE
# 		A string representation (either 'netcdf4' or 'pyhdf') of the module to 
# 		use to open the file if a file path is given for `f`.
	
# 	External modules:
# 	numpy -- https://numpy.org/
# 	scipy -- https://scipy.org/
	
# 	Returns:
# 	The confidence interval beginning and ending points as a two-element tuple 
# 	for the given `wavelength` and `confidence` level, assuming a normal 
# 	distribution about the center wavelength.
# 	"""
# 	import numpy as np
# 	from scipy.optimize import curve_fit
# 	from scipy.stats import skewnorm

# 	# Open new file
# 	newfile = isinstance(f, str)
# 	if newfile:
# 		f = openMASTERfile(f, mod)

# 	# Get center wavelength and FWHM wavelengths for each band
# 	left50_bands = extractMASTERdata(readMASTERdataset(f, \
# 		"Left50%ResponseWavelength"))
# 	right50_bands = extractMASTERdata(readMASTERdataset(f, \
# 		"Right50%ResponseWavelength"))
# 	center_bands = centerMASTERwavelengths(f, effective=True)

# 	# Select location of given wavelength in list of bands
# 	if wavelength is not None:
# 		nonzero = np.ma.nonzero if np.ma.isMA(center_bands) else np.nonzero
# 		i = nonzero((abs(wavelength-center_bands) == \
# 			min(abs(wavelength-center_bands))) & \
# 			(abs(wavelength/center_bands-1) < 0.15))[0][i]
	
# 	# Prepare data for curve fitting to CDF of response function
# 	mu = center_bands[i]
# 	x = [left50_bands[i], mu, right50_bands[i]]
# 	y = [(1-confidence)/2, .5, .5+confidence/2]
	
# 	# Peform curve fit using CDF with fixed center to get skew and scale
# 	popt,pcov = curve_fit(lambda x,a,s: skewnorm.cdf(x, a, mu, s), x, y, p0=[0,1])
# 	a,s = popt

# 	# Close file
# 	if newfile:
# 		closeMASTERfile(f)
	
# 	# Return interval estimatation of band's response function for given confidence
# 	return skewnorm.interval(confidence, a=a, loc=mu, scale=s)
# ############################## getMASTERwavebands ##############################


# ############################### getMASTERcaldata ###############################
# def getMASTERcaldata(f, wavelength, bt=False, getsaturation=False, 
#   getblooming=False, mod=DEFAULT_MODULE):
# 	"""Gets calibrated radiance or brightness temperature data for given band.
	
# 	Parameters:
# 	f: type=str|netCDF4.Dataset|pyhdf.SD.SD
# 		File handler (using either netCDF4 or pyhdf modules) or file path string.
# 	wavelength: type=float, default=None
# 		The wavelength of the band for which to extract the calibrated radiance 
# 		data.
# 	bt: type=bool, default=False
# 		If set to True, will convert the output from radiances to brightness 
# 		temperatures.
# 	getsaturation: type=bool, default=False
# 		If set to True, will return a boolean array of saturation flags.
# 	getblooming: type=bool, default=False
# 		If set to True and `getsaturation` is True, will return a boolean array
# 		of pixels whose values have bloomed.
# 	mod: type=str, default=DEFAULT_MODULE
# 		A string representation (either 'netcdf4' or 'pyhdf') of the module to 
# 		use to open the file if a file path is given for `f`.
	
# 	External modules:
# 	numpy -- https://numpy.org/
# 	remote_sensing -- https://feer.gsfc.nasa.gov/
	
# 	Returns:
# 	The scaled calibrated radiance data in units of W m^-2 sr^-1 μm^-1. If the 
# 	`bt` argument is given, the output will be brightness temperatures in units 
# 	of Kelvin. If the `getsaturation` argument is given, the output is a tuple 
# 	where the first item is the data and the second is the saturation array.
# 	"""
# 	import numpy as np
# 	from remote_sensing import extract_data
	
# 	# Open new file
# 	newfile = isinstance(f, str)
# 	if newfile:
# 		f = openMASTERfile(f, mod)

# 	# Get calibrated radiance dataset
# 	ds = readMASTERdataset(f, "CalibratedData")

# 	# Get wavelength bands and indicies of given wavelength
# 	bands = centerMASTERwavelengths(f)
# 	ibands = np.nonzero((abs(wavelength-bands) == min(abs(wavelength-bands))) & \
# 		(abs(wavelength/bands-1) < 0.15))[0]
# 	bands = bands[ibands]

# 	# Get scaled and masked radiances for bands (accounting for dual gain)
# 	banddim = list(getMASTERdims(f, "CalibratedData")).index('bands')
# 	i = np.roll(np.array(np.s_[:,:,ibands], dtype=object), banddim+1)
# 	data = extractMASTERdata(ds, i)		# (no axes eliminated b/c ibands is always an array)
	
# 	# Get calibrated radiance or brightness temperature data with saturation, 
# 	# combining dual gain channels
# 	scandim = list(getMASTERdims(f, "CalibratedData")).index('samples')
# 	if bt:
# 		bt_scale_factors = extractMASTERdata(readMASTERdataset(f, \
# 			"TemperatureCorrectionSlope"), (ibands,))
# 		bt_offsets = extractMASTERdata(readMASTERdataset(f, \
# 			"TemperatureCorrectionIntercept"), (ibands,))
# 		data = extract_data(wavelength, bands, data, banddim=banddim, \
# 			bt=True, bt_scale_factors=bt_scale_factors, bt_offsets=bt_offsets, \
# 			getsaturation=getsaturation, scandim=scandim, \
# 			getblooming=getblooming)
# 	else:
# 		data = extract_data(wavelength, bands, data, banddim=banddim, \
# 			getsaturation=getsaturation, scandim=scandim, \
# 			getblooming=getblooming)

# 	# Close file
# 	if newfile:
# 		closeMASTERfile(f)
	
# 	# Return radiance or brightness temperature data, and saturation if desired
# 	return data
# ############################### getMASTERcaldata ###############################


# ############################# getMASTERpixelareas #############################
# def getMASTERpixelareas(f, mod=DEFAULT_MODULE):
# 	"""Gets pixel earth surface areas of a MASTER granule.
	
# 	Parameters:
# 	f: type=str|netCDF4.Dataset|pyhdf.SD.SD
# 		File handler (using either netCDF4 or pyhdf modules) or file path string.
# 	mod: type=str, default=DEFAULT_MODULE
# 		A string representation (either 'netcdf4' or 'pyhdf') of the module to 
# 		use to open the file if a file path is given for `f`.
	
# 	External modules:
# 	mapping -- https://feer.gsfc.nasa.gov/
	
# 	Returns:
# 	An array of pixel areas in units of m^2.
# 	"""
# 	from mapping import irreg_grid_area

# 	# Open new file
# 	newfile = isinstance(f, str)
# 	if newfile:
# 		f = openMASTERfile(f, mod)

# 	# Get latitude and longitude data
# 	lats = extractMASTERdata(readMASTERdataset(f, "PixelLatitude"))
# 	lons = extractMASTERdata(readMASTERdataset(f, "PixelLongitude"))

# 	# Get pixel areas
# 	areas = irreg_grid_area(lats, lons)			# [m^2]

# 	# Close file
# 	if newfile:
# 		closeMASTERfile(f)
	
# 	# Return areas
# 	return areas
# ############################# getMASTERpixelareas #############################


# ############################### createMASTERrgb ###############################
# def createMASTERrgb(f, wavelengths={'r':.65, 'g':.56, 'b':.47}, fout=None, 
#   mod=DEFAULT_MODULE, **kwargs):
# 	"""Creates an RGB image of a MASTER scene.
	
# 	Parameters:
# 	f: type=str|netCDF4.Dataset|pyhdf.SD.SD
# 		File handler (using either netCDF4 or pyhdf modules) or file path string.
# 	wavelengths: type=dict, default={'r':.65, 'g':.56, 'b':.47}
# 		Dictionary of wavelengths for the RGB channels. Keys need to be 'r', 'g' 
# 		and 'b'.
# 	fout: type=str, default=None
# 		Path of the output image file.
# 	mod: type=str, default=DEFAULT_MODULE
# 		A string representation (either 'netcdf4' or 'pyhdf') of the module to 
# 		use to open the file if a file path is given for `f`.
# 	Accepts additional keyword arguments for the following function:
# 		remote_sensing.create_rgb: alpha, beta, gamma
	
# 	External modules:
# 	matplotlib (optional) -- https://matplotlib.org/
# 	remote_sensing -- https://feer.gsfc.nasa.gov/
	
# 	Returns:
# 	A 3D RGB image array. If the `fout` argument is given, nothing is returned 
# 	and the image is saved to the `fout` path instead.
# 	"""
# 	import numpy as np
# 	if fout is not None:
# 		import matplotlib.pyplot as plt
# 	from remote_sensing import create_rgb

# 	# Open new file
# 	newfile = isinstance(f, str)
# 	if newfile:
# 		f = openMASTERfile(f, mod)

# 	# Get radiance data for RGB channels
# 	r = getMASTERcaldata(f, wavelengths['r'])
# 	g = getMASTERcaldata(f, wavelengths['g'])
# 	b = getMASTERcaldata(f, wavelengths['b'])

# 	# Convert radiance to reflectance (assumed method; ATBD not found)
# 	wavelengthsMASTER = centerMASTERwavelengths(f)
# 	ir = np.argmin(np.abs(wavelengthsMASTER-wavelengths['r']))
# 	ig = np.argmin(np.abs(wavelengthsMASTER-wavelengths['g']))
# 	ib = np.argmin(np.abs(wavelengthsMASTER-wavelengths['b']))
# 	solar_irrad = readMASTERdataset(f, 'SolarSpectralIrradiance')
# 	csz = np.cos(np.radians(readMASTERdataset(f, 'SolarZenithAngle')))
# 	r /= solar_irrad[ir]*csz
# 	g /= solar_irrad[ig]*csz
# 	b /= solar_irrad[ib]*csz

# 	# Close file
# 	if newfile:
# 		closeMASTERfile(f)
	
# 	# Get RGB image
# 	img = create_rgb(r, g, b, **kwargs)
	
# 	# Return image, or save image if output filename given
# 	if fout is None:
# 		return img
# 	else:
# 		plt.imsave(fout, img)
# ############################### createMASTERrgb ###############################