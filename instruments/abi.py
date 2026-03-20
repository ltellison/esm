"""GOES ABI
Module for creating and operating on classes relating to the Geostationary 
Operational Environmental (GOES) Satellite R-Series Advanced Baseline Imager 
(ABI).

Author:
	Luke Ellison

Version:
	0.1

History:
	v0.1, 05-Dec-2025, Luke Ellison: Module compiled.

Global Variables:
	GOES_ABI_PRODUCT_FORMATTERS -- Dictionary of GOES-ABI product filename 
		formatters.
	GOES_ABI_PRODUCT_REVERSE_FORMATTERS -- Dictionary of GOES-ABI product 
		filename reverse formatters.
	GOES_ABI_PRODUCTS -- Dictionary of available GOES-ABI products and their 
		associated metadata.

Classes:
	ABI -- Defines an ABI object on a GOES satellite.

External Modules:
	- dateutil -- https://dateutil.readthedocs.io/
"""
import datetime as dt
from dateutil.relativedelta import relativedelta
from ..platform import Satellite
from ..instrument import WhiskbroomScanner

# Set default module to use to read data
# DEFAULT_MODULE = ['netcdf4', 'xarray', 'h5py', 'pyhdf'][0]

# GOES ABI product formatters
GOES_ABI_PRODUCT_FORMATTERS = {
	'platform': lambda p: Satellite(f"goes{p}"),
	'start_timestamp': lambda s: dt.datetime.strptime(s[:-1], "%Y%j%H%M%S")+ \
		dt.timedelta(milliseconds=int(s[-1])*100),
	'start_date': "%Y%j",
	'start_time': lambda s: (dt.datetime.strptime(s[:-1], "%H%M%S")+ \
		dt.timedelta(milliseconds=int(s[-1])*100)).time(),
	'end_timestamp': lambda s: dt.datetime.strptime(s[:-1], "%Y%j%H%M%S")+ \
		dt.timedelta(milliseconds=int(s[-1])*100),
	'end_date': "%Y%j",
	'end_time': lambda s: (dt.datetime.strptime(s[:-1], "%H%M%S")+ \
		dt.timedelta(milliseconds=int(s[-1])*100)).time(),
	'processing_timestamp': lambda s: dt.datetime.strptime(s[:-1], \
		"%Y%j%H%M%S")+dt.timedelta(milliseconds=int(s[-1])*100)
}
GOES_ABI_PRODUCT_REVERSE_FORMATTERS = {
	'platform': lambda p: p.id[-2:],
	'start_timestamp': lambda t: t.strftime("%Y%j%H%M%S%f")[:-5],
	'start_time': lambda t: t.strftime("%H%M%S%f")[:-5],
	'end_timestamp': lambda t: t.strftime("%Y%j%H%M%S%f")[:-5],
	'end_time': lambda t: t.strftime("%H%M%S%f")[:-5],
	'processing_timestamp': lambda t: t.strftime("%Y%j%H%M%S%f")[:-5]
}

GOES_ABI_PRODUCTS = {
	'FDCC': {
		'name': "ABI/GOES Fire/Hot Spot Characterization CONUS",
		'level': '2',
		'structure': "ABI grid",
		'spatial_resolution': 2000,				# [m]
		'temporal_resolution': relativedelta(minutes=5),
		'filename_pattern': "(?P<environment>[A-Z]{2})_"
			"(?P<full_product>ABI-L2-(?P<product>FDCC)-M\d)_G(?P<platform>\d{2})_"
			"s(?P<start_timestamp>(?P<start_date>\d{7})(?P<start_time>\d{7}))_"
			"e(?P<end_timestamp>(?P<end_date>\d{7})(?P<end_time>\d{7}))_"
			"c(?P<processing_timestamp>\d{14})\.(?P<ext>nc)",
		'horizontal_dimension_name': "x",
		'vertical_dimension_name': "y",
		'labels': {
			'x_name': "x",
			'y_name': "y",
			'platform_latitude_name': "nominal_satellite_subpoint_lat",
			'platform_longitude_name': "nominal_satellite_subpoint_lon",
			'altitude_name': "nominal_satellite_height",
			# time_bounds, t, y_image, x_image
		},
		'scan_width': 332,					# Kalluri et al. 2018, Table 1
		'swath_width': 3952,				# .. Table 2
		'pixel_scale': 56e-6,				# [rad] (from Schmit et al. 2017)
		'ifov': (47.7e-6, 51.5e-6),			# [rad] (along-track/vertical, across-track/horizontal)
	},
	'FDCM': {
		'name': "ABI/GOES Fire/Hot Spot Characterization Mesoscale",
		'level': '2',
		'structure': "ABI grid",
		'spatial_resolution': 2000,				# [m]
		'temporal_resolution': relativedelta(seconds=30),
		'filename_pattern': "(?P<environment>[A-Z]{2})_"
			"(?P<full_product>ABI-L2-(?P<product>FDCM)-M\d)_G(?P<platform>\d{2})_"
			"s(?P<start_timestamp>(?P<start_date>\d{7})(?P<start_time>\d{7}))_"
			"e(?P<end_timestamp>(?P<end_date>\d{7})(?P<end_time>\d{7}))_"
			"c(?P<processing_timestamp>\d{14})\.(?P<ext>nc)",
		'horizontal_dimension_name': "x",
		'vertical_dimension_name': "y",
		'labels': {
			'x_name': "x",
			'y_name': "y",
			'platform_latitude_name': "nominal_satellite_subpoint_lat",
			'platform_longitude_name': "nominal_satellite_subpoint_lon",
			'altitude_name': "nominal_satellite_height",
			# time_bounds, t, y_image, x_image
		},
		'scan_width': 332,
		'swath_width': 1408,
		'pixel_scale': 56e-6,				# [rad]
		'ifov': (47.7e-6, 51.5e-6),			# [rad] (along-track/vertical, across-track/horizontal)
	},
}


#---------------------------------- CLASSES ----------------------------------#

##################################### ABI #####################################
class ABI(WhiskbroomScanner):
	"""Defines an ABI object on a GOES satellite.
	
	Functions:
		__init__ -- Initializes an ABI instrument object for a GOES platform.
		set_proj -- Sets the projection for the given GOES ABI dataset.
		set_geo -- Sets the geolocation information for a given GOES ABI dataset.
	
	Returns:
		- An object defining an ABI instrument for the GOES platforms.
	"""

	# Constructor method
	def __init__(self, /, platform, **kwargs):
		"""Initializes an ABI instrument object for a GOES platform.
		
		Parameters:
			platform: type=Platform|str
				- The GOES platform on which this ABI instance is located.
		
		External Modules:
			- pyproj -- https://pyproj4.github.io/pyproj/
		"""
		import re
		from pyproj import CRS, Transformer
		from ..config import AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS
		from ..platform import _get_standard_platform_id
		
		# Get standard platform ID
		if isinstance(platform, str):
			available_platform_instruments = {k:v for k,v in \
				AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS.items() if \
				re.fullmatch("goes-\d{2}", k)}
			platform = _get_standard_platform_id(platform, \
				available_platform_instruments)

		# Update products with 'available_products' argument if provided
		products = GOES_ABI_PRODUCTS.copy()
		if 'available_products' in kwargs and \
		  isinstance(kwargs['available_products'], dict):
			products.update(kwargs['available_products'])
		
		# Set scan widths, swath widths, and pixel offsets by spatial resolution
		# pixel_offset = 0		# check!!

		# Set IFOV and pixel scale by spatial resolution
		# rps = 0.02443					# [rad/s] rotation rate

		# Set pixel response function
		# prf = lambda i,j: max(0, 1-abs(j-1/2))

		# Initialize ABI object
		super().__init__('abi', platform=platform, \
			formatters=GOES_ABI_PRODUCT_FORMATTERS, \
			reverse_formatters=GOES_ABI_PRODUCT_REVERSE_FORMATTERS, \
			available_products=products, **kwargs)
	
	# Method to set projection
	def set_proj(self, /, dataset, **kwargs):
		"""Sets the projection for the given GOES ABI dataset.
		
		Parameters:
			dataset: type=Dataset
				- The GOES ABI dataset for which to set the projection.
		
		External Modules:
			- pyproj -- https://pyproj4.github.io/pyproj/
		"""
		from pyproj import CRS

		# Save projection information to dataset object
		proj_info = dataset.read(var='goes_imager_projection', attr=True)
		dataset.crs = CRS.from_cf(proj_info)
	
	# Method to set the latitude and longitude for the given dataset
	def set_geo(self, /, dataset, crs_to="epsg:4326", reload=False, **kwargs):
		"""Sets the geolocation information for a given GOES ABI dataset.
		
		Parameters:
			dataset: type=Dataset
				- The GOES ABI dataset for which to save the geolocation 
				information.
			crs_to: type=str, default="epsg:4326"
				- The CRS to transform the geolocation data to.
			reload: type=bool, default=False
				- 
			**kwargs:
				- 
		
		External Modules:
			- numpy -- https://numpy.org/
			- pyproj -- https://pyproj4.github.io/pyproj/
		
		Returns:
			- The dimensions dictionary of the geolocation arrays.
		"""
		import numpy as np
		from pyproj import Transformer

		# Check if geolocation data already loaded
		load = reload or not (hasattr(dataset, 'latitude') and \
			hasattr(dataset, 'longitude'))
		if not load:
			return dataset.read(var='x', dim=True, **kwargs)
		
		# Set the projection if not already completed
		if not hasattr(dataset, 'crs'):
			self.set_proj(dataset)
		
		# Set x and y values in meters
		proj_info = dataset.read(var='goes_imager_projection', attr=True)
		h = proj_info['perspective_point_height'] + proj_info['semi_major_axis']
		x,y = np.meshgrid(dataset.extract('x'), dataset.extract('y'))
		dataset.x = x*h			# [m]
		dataset.y = y*h			# [m]
		
		# Set latitudes and longitudes
		# transformer = Transformer.from_crs(dataset.crs, crs_to, always_xy=True)
		# lon,lat = transformer.transform(dataset.x, dataset.y)
		# dataset.latitude = lat
		# dataset.longitude = lon

		# Official method since above doesn't work
		# https://www.star.nesdis.noaa.gov/atmospheric-composition-training/python_abi_lat_lon.php
		lon0 = np.radians(proj_info['longitude_of_projection_origin'])
		a = proj_info['semi_major_axis']
		b = proj_info['semi_minor_axis']
		a_var = np.ma.sin(x)**2 + np.ma.cos(x)**2 * (np.ma.cos(y)**2 + \
			a**2/b**2*np.ma.sin(y)**2)
		b_var = -2*h*np.ma.cos(x)*np.ma.cos(y)
		c_var = h**2 - a**2
		r_s = (-b_var - np.ma.sqrt(b_var**2-4*a_var*c_var)) / (2*a_var)
		s_x = r_s*np.ma.cos(x)*np.ma.cos(y)
		s_y = -r_s*np.ma.sin(x)
		s_z = r_s*np.ma.cos(x)*np.ma.sin(y)
		lat = np.degrees(np.ma.arctan(a**2 / b**2 * s_z / \
			np.ma.sqrt((h-s_x)*(h-s_x)+s_y*s_y)))
		lon = np.degrees(lon0 - np.ma.arctan(s_y/(h-s_x)))
		dataset.latitude = lat if np.ma.is_masked(lat) else np.ma.getdata(lat)
		dataset.longitude = lon if np.ma.is_masked(lon) else np.ma.getdata(lon)

		# Return dimensions dictionary of geolocation arrays
		return dataset.read(var='x', dim=True, **kwargs)