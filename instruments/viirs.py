"""VIIRS
Module for creating and operating on classes relating to the Visible Infrared 
Imaging Radiometer Suite (VIIRS).

Author:
	Luke Ellison

Version:
	0.1

History:
	v0.1, 25-Nov-2025, Luke Ellison: Module compiled.

Global Variables:
	VIIRS_PRODUCT_FORMATTERS -- Dictionary of VIIRS product filename formatters.
	VIIRS_PRODUCT_REVERSE_FORMATTERS -- Dictionary of VIIRS product filename 
		reverse formatters.
	VIIRS_NPP_PRODUCTS -- Dictionary of available VIIRS-NPP products and their 
		associated metadata.
	VIIRS_NOAA20_PRODUCTS -- Dictionary of available VIIRS-NOAA20 products and 
		their associated metadata.
	VIIRS_NOAA21_PRODUCTS -- Dictionary of available VIIRS-NOAA21 products and 
		their associated metadata.

Classes:
	VIIRS -- Defines a VIIRS object on either Suomi-NPP or one of the NOAA 
		satellites.

External Modules:
	- dateutil -- https://dateutil.readthedocs.io/
"""
from dateutil.relativedelta import relativedelta
from ..instrument import WhiskbroomScanner

# Set default module to use to read data
# DEFAULT_MODULE = ['netcdf4', 'xarray', 'h5py', 'pyhdf'][0]

# VIIRS product formatters
VIIRS_PRODUCT_FORMATTERS = {
	'timestamp': "%Y%j.%H%M",
	'date': "%Y%j",
	'time': "%H%M",
	'version': lambda v: int(v)/10**d if (d:=len(v.lstrip('0'))-1) else int(v),
	'processing_timestamp': "%Y%j%H%M%S"
}
VIIRS_PRODUCT_REVERSE_FORMATTERS = {
	'version': lambda v: str(v).replace('.','').zfill(3)
}

VIIRS_NPP_PRODUCTS = {
	'VNP03MOD': {
		'name': "VIIRS/Suomi-NPP Geolocation M-band",
		'level': '1a',
		'structure': "swath",
		'spatial_resolution': 750,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VNP03MOD)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
		'along_track_dimension_name': ["number_of_lines", "number_of_scans"],
		'across_track_dimension_name': "number_of_pixels",
		'labels': {
			'latitude_name': "geolocation_data/latitude",
			'longitude_name': "geolocation_data/longitude",
			'range_name': "geolocation_data/range",					# check if implemented
			'elevation_name': "geolocation_data/height",				# check if ortho
			'timestamp_name': "scan_line_attributes/ev_mid_time",		# custom conversion using TAI93
			'sensor_azimuth_name': "geolocation_data/sensor_azimuth",
			'sensor_zenith_name': "geolocation_data/sensor_zenith",
			'solar_azimuth_name': "geolocation_data/solar_azimuth",
			'solar_zenith_name': "geolocation_data/solar_zenith",
			# att_quat_ev, orb_pos_ev_mid, orb_vel_ev_mid, 
		},
	},
	'VNP03IMG': {
		'name': "VIIRS/Suomi-NPP Geolocation I-band",
		'level': '1a',
		'structure': "swath",
		'spatial_resolution': 375,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VNP03IMG)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
		'along_track_dimension_name': ["number_of_lines", "number_of_scans"],
		'across_track_dimension_name': "number_of_pixels",
		'labels': {
			'latitude_name': "geolocation_data/latitude",
			'longitude_name': "geolocation_data/longitude",
			'range_name': "geolocation_data/range",					# check if implemented
			'elevation_name': "geolocation_data/height",				# check if ortho
			'timestamp_name': "scan_line_attributes/ev_mid_time",		# custom conversion using TAI93
			'sensor_azimuth_name': "geolocation_data/sensor_azimuth",
			'sensor_zenith_name': "geolocation_data/sensor_zenith",
			'solar_azimuth_name': "geolocation_data/solar_azimuth",
			'solar_zenith_name': "geolocation_data/solar_zenith",
			# att_quat_ev, orb_pos_ev_mid, orb_vel_ev_mid, 
		},
	},
	'VNP14': {
		'name': "VIIRS/Suomi-NPP Thermal Anomalies/Fire M-band",
		'level': '2',
		'structure': "swath",
		'spatial_resolution': 750,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VNP14)\.A(?P<timestamp>(?P<date>\d{7})"
			"\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
	},
	'VNP14IMG': {
		'name': "VIIRS/Suomi-NPP Thermal Anomalies/Fire I-band",
		'level': '2',
		'structure': "swath",
		'spatial_resolution': 375,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VNP14IMG)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
	},
}

VIIRS_NOAA20_PRODUCTS = {
	'VJ103MOD': {
		'name': "VIIRS/NOAA-20 Geolocation M-band",
		'level': '1a',
		'structure': "swath",
		'spatial_resolution': 750,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VJ103MOD)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
		'along_track_dimension_name': ["number_of_lines", "number_of_scans"],
		'across_track_dimension_name': "number_of_pixels",
		'labels': {
			'latitude_name': "geolocation_data/latitude",
			'longitude_name': "geolocation_data/longitude",
			'range_name': "geolocation_data/range",					# check if implemented
			'elevation_name': "geolocation_data/height",				# check if ortho
			'timestamp_name': "scan_line_attributes/ev_mid_time",		# custom conversion using TAI93
			'sensor_azimuth_name': "geolocation_data/sensor_azimuth",
			'sensor_zenith_name': "geolocation_data/sensor_zenith",
			'solar_azimuth_name': "geolocation_data/solar_azimuth",
			'solar_zenith_name': "geolocation_data/solar_zenith",
			# att_quat_ev, orb_pos_ev_mid, orb_vel_ev_mid, 
		},
	},
	'VJ103IMG': {
		'name': "VIIRS/NOAA-20 Geolocation I_band",
		'level': '1a',
		'structure': "swath",
		'spatial_resolution': 375,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VJ103IMG)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
		'along_track_dimension_name': ["number_of_lines", "number_of_scans"],
		'across_track_dimension_name': "number_of_pixels",
		'labels': {
			'latitude_name': "geolocation_data/latitude",
			'longitude_name': "geolocation_data/longitude",
			'range_name': "geolocation_data/range",					# check if implemented
			'elevation_name': "geolocation_data/height",				# check if ortho
			'timestamp_name': "scan_line_attributes/ev_mid_time",		# custom conversion using TAI93
			'sensor_azimuth_name': "geolocation_data/sensor_azimuth",
			'sensor_zenith_name': "geolocation_data/sensor_zenith",
			'solar_azimuth_name': "geolocation_data/solar_azimuth",
			'solar_zenith_name': "geolocation_data/solar_zenith",
			# att_quat_ev, orb_pos_ev_mid, orb_vel_ev_mid, 
		},
	},
	'VJ114': {
		'name': "VIIRS/NOAA-20 Thermal Anomalies/Fire M-band",
		'level': '2',
		'structure': "swath",
		'spatial_resolution': 750,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VJ114)\.A(?P<timestamp>(?P<date>\d{7})"
			"\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
	},
	'VJ114IMG': {
		'name': "VIIRS/NOAA-20 Thermal Anomalies/Fire I-band",
		'level': '2',
		'structure': "swath",
		'spatial_resolution': 375,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VJ114IMG)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
	},
}

VIIRS_NOAA21_PRODUCTS = {
	'VJ203MOD': {
		'name': "VIIRS/NOAA-21 Geolocation M-band",
		'level': '1a',
		'structure': "swath",
		'spatial_resolution': 750,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VJ203MOD)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
		'along_track_dimension_name': ["number_of_lines", "number_of_scans"],
		'across_track_dimension_name': "number_of_pixels",
		'labels': {
			'latitude_name': "geolocation_data/latitude",
			'longitude_name': "geolocation_data/longitude",
			'range_name': "geolocation_data/range",					# check if implemented
			'elevation_name': "geolocation_data/height",				# check if ortho
			'timestamp_name': "scan_line_attributes/ev_mid_time",		# custom conversion using TAI93
			'sensor_azimuth_name': "geolocation_data/sensor_azimuth",
			'sensor_zenith_name': "geolocation_data/sensor_zenith",
			'solar_azimuth_name': "geolocation_data/solar_azimuth",
			'solar_zenith_name': "geolocation_data/solar_zenith",
			# att_quat_ev, orb_pos_ev_mid, orb_vel_ev_mid, 
		},
	},
	'VJ203IMG': {
		'name': "VIIRS/NOAA-21 Geolocation I-band",
		'level': '1a',
		'structure': "swath",
		'spatial_resolution': 375,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VJ203IMG)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
		'along_track_dimension_name': ["number_of_lines", "number_of_scans"],
		'across_track_dimension_name': "number_of_pixels",
		'labels': {
			'latitude_name': "geolocation_data/latitude",
			'longitude_name': "geolocation_data/longitude",
			'range_name': "geolocation_data/range",					# check if implemented
			'elevation_name': "geolocation_data/height",				# check if ortho
			'timestamp_name': "scan_line_attributes/ev_mid_time",		# custom conversion using TAI93
			'sensor_azimuth_name': "geolocation_data/sensor_azimuth",
			'sensor_zenith_name': "geolocation_data/sensor_zenith",
			'solar_azimuth_name': "geolocation_data/solar_azimuth",
			'solar_zenith_name': "geolocation_data/solar_zenith",
			# att_quat_ev, orb_pos_ev_mid, orb_vel_ev_mid, 
		},
	},
	'VJ214': {
		'name': "VIIRS/NOAA-21 Thermal Anomalies/Fire M-band",
		'level': '2',
		'structure': "swath",
		'spatial_resolution': 750,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VJ214)\.A(?P<timestamp>(?P<date>\d{7})"
			"\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
	},
	'VJ214IMG': {
		'name': "VIIRS/NOAA-21 Thermal Anomalies/Fire I-band",
		'level': '2',
		'structure': "swath",
		'spatial_resolution': 375,				# [m]
		'temporal_resolution': relativedelta(minutes=6),
		'filename_pattern': "(?P<product>VJ214IMG)\.A(?P<timestamp>"
			"(?P<date>\d{7})\.(?P<time>\d{4}))\.(?P<version>\d{3})\."
			"(?P<processing_timestamp>\d{13})\.(?P<ext>nc)",
	},
}


#---------------------------------- CLASSES ----------------------------------#

#################################### MODIS ####################################
class VIIRS(WhiskbroomScanner):
	"""Defines a VIIRS object on either Suomi-NPP or one of the NOAA satellites.
	
	Functions:
		__init__ -- Initializes a VIIRS instrument object for either the 
			Suomi-NPP or one of the NOAA platforms.
	
	Returns:
		- An object defining a VIIRS instrument on either the Suomi-NPP or one 
		of the NOAA platforms.
	"""

	# Constructor method
	def __init__(self, /, platform, **kwargs):
		"""Initializes a VIIRS instrument object for either the Suomi-NPP or one 
		of the NOAA platforms.
		
		Parameters:
			platform: type=Platform|str
				- The platform (Suomi-NPP, NOAA-20 or NOAA-21) on which this 
				VIIRS instance is located.
		
		External Modules:
			- numpy -- https://numpy.org/
		"""
		# from numpy import pi
		from ..config import AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS
		from ..platform import Platform, _get_standard_platform_id
		# from ..ancillary import set_sigfigs
		
		# Get standard platform ID
		if isinstance(platform, Platform):
			platform_id = platform.id.lower()
		elif isinstance(platform, str):
			available_platform_instruments = {k:v for k,v in \
				AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS.items() if k in \
				['suomi-npp','noaa-20','noaa-21']}
			platform_id = _get_standard_platform_id(platform, \
				available_platform_instruments)
		else:
			platform_id = platform

		# Get products for platform
		if platform_id == 'suomi-npp':
			products = VIIRS_NPP_PRODUCTS
		elif platform_id == 'noaa-20':
			products = VIIRS_NOAA20_PRODUCTS
		elif platform_id == 'noaa-21':
			products = VIIRS_NOAA21_PRODUCTS
		elif platform_id is None:
			products = VIIRS_NPP_PRODUCTS | VIIRS_NOAA20_PRODUCTS | \
				VIIRS_NOAA21_PRODUCTS
		else:
			raise ValueError("Instance of VIIRS instrument not recognized.")
		
		# Update products with 'available_products' argument if provided
		if 'available_products' in kwargs and \
		  isinstance(kwargs['available_products'], dict):
			products.update(kwargs['available_products'])
		
		# Set scan widths, swath widths, and pixel offsets by spatial resolution
		scan_width_key = swath_width_key = pixel_offset_key = 'spatial_resolution'
		scan_width = 32
		swath_width = 6400		# check!!
		pixel_offset = 0		# check!!

		# Set IFOV and pixel scale by spatial resolution
		# rpm = 20.3092					# [rot. per min] rotation rate
		# sample_time_1km = 333.333e-6	# [μs] sample time for 1km detector
		# # sample_frame = 2				# fraction of pixel area spent sampling
		# # ifov_1km = 2*pi*(sample_time_1km/sample_frame)/(60/rpm)*4		# unclear why off by factor of 4
		# ifov_1km = 2*pi*sample_time_1km/(60/rpm)*2		# unclear why off by factor of 2
		# sigfigs = 6
		# ang250 = set_sigfigs(ifov_1km/4, sigfigs)
		# ang500 = set_sigfigs(ifov_1km/2, sigfigs)
		# ang1000 = set_sigfigs(ifov_1km, sigfigs)
		# ang2000 = set_sigfigs(2*ifov_1km, sigfigs)
		# pixel_scale = {250: ang250, 500: ang500, 1000: ang1000}
		# ifov = {250: (ang250, ang500), 500: (ang500, ang1000), \
		# 	1000: (ang1000, ang2000)}
		# pixel_scale_key = ifov_key = 'spatial_resolution'

		# Set pixel response function
		# prf = lambda i,j: max(0, 1-abs(j-1/2))

		# Initialize VIIRS object
		super().__init__('viirs', platform=platform, \
			formatters=VIIRS_PRODUCT_FORMATTERS, \
			reverse_formatters=VIIRS_PRODUCT_REVERSE_FORMATTERS, \
			available_products=products, scan_width=scan_width, \
			scan_width_key=scan_width_key, swath_width=swath_width, \
			swath_width_key=swath_width_key, pixel_offset=pixel_offset, \
			pixel_offset_key=pixel_offset_key, ifov=None, ifov_key=None, \
			pixel_scale=None, pixel_scale_key=None, prf=None, \
			**kwargs)		# check!!
		
		# Set dimension renaming function
		# def _rename_dimension(dim_name):
		# 	return dim_name[:dim_name.index(':')] if ':' in dim_name else \
		# 		dim_name
		# self._rename_dimension = _rename_dimension
	