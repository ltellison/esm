"""Config
Module of high-level configuration variables for the Earth Science Mission 
Python package.

Author:
	Luke Ellison

Version:
	0.1

History:
	v0.1, 08-Dec-2025, Luke Ellison: Module compiled.

Global Variables:
	DIRECTORY_ORDER -- List representing hierarchical order of data directories.
	AUTH -- `earthaccess` authentication object.
	QUERY -- The default switch for querying online data.
	DOWNLOAD -- The default switch for downloading online data.
	SELECTABLE_SPECIFICATIONS -- List of instrument-related specification 
		variables for defining an instrument's native output.
	AVAILABLE_SATELLITE_INSTRUMENTS -- Dictionary of available spaceborne 
		instruments and their associated metadata.
	AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS -- Dictionary of available 
		satellites and their associated metadata and onboard instruments.
	AVAILABLE_AIRCRAFT_INSTRUMENTS -- Dictionary of available airborne 
		instruments and their associated metadata.
	AVAILABLE_AIRCRAFT_PLATFORMS -- Dictionary of available aircraft and their 
		associated metadata.
"""
import os
import datetime as dt
from numpy import pi

#------------------------------ GLOBAL VARIABLES ------------------------------#

# Variables for file system
DIRECTORY_ORDER = os.getenv('ESM_DIRECTORY_ORDER', \
	('instrument', 'platform', 'product'))

# Variables for earthaccess
AUTH = None										# earthaccess authentication object
QUERY = os.getenv('ESM_QUERY', False)			# default switch for querying online data
DOWNLOAD = os.getenv('ESM_DOWNLOAD', False)		# default switch for downloading online data

# Variables for specifications
SELECTABLE_SPECIFICATIONS = [
	# 'geo_product',		# geolocation product ID
	'scan_width',		# whiskbroom scan width (along-track) in pixels
	'frame_width',		# pushbroom frame width (along-track) in pixels
	'swath_length',		# swath length (along-track) in pixels
	'swath_width',		# swath width (across-track) in pixels
	'pixel_offset',		# pixel offset (2D) in pixel fraction (along-track, 
						# 	across-track)
	'pixel_scale',		# pixel scale (2D) in radians (along-track, across-track)
	'ifov',				# instantaneous field of view (2D) in radians 
						# 	(along-track, across-track)
	'gsd',				# ground sample distance (2D) at nadir in e.g. meters 
						# 	(along-track, across-track)
	'prf',				# pixel response function as function with two inputs 
						#   (i,j) corresponding to pixel fraction (w.r.t. pixel 
						#   scale not IFOV) along-track and across-track, 
						#   respectively, and returning a value between 0-1
	'reversed_cross_track'	# a boolean dictating if the cross-track indices are 
							#   reversed from the right-handed rule
]

# Variables for satellites
AVAILABLE_SATELLITE_INSTRUMENTS = {
	'abi': {
		'name': "ABI",
		'full_name': "Advanced Baseline Imager",
		'website': "https://www.goes-r.gov/spacesegment/abi.html"
	},
	'modis': {
		'name': "MODIS",
		'full_name': "Moderate Resolution Imaging Spectroradiometer",
		'website': "https://modis.gsfc.nasa.gov/",
		# 'labels': {
		# 	'latitude_name': "Latitude",
		# 	'longitude_name': "Longitude",
		# 	'range_name': "Range",
		# 	'elevation_name': "Height"
		# },
		# 'specifications': {
		# 	'scan_width': {250: 40, 500: 20, 1000: 10},
		# 	'scan_width_key': "spatial_resolution",
		# 	'swath_width': {250: 5416, 500: 2708, 1000: 1354},
		# 	'swath_width_key': "spatial_resolution",
		# 	'pixel_offset': {250: (0,-3/2), 500: (0,-1/2), 1000: 0},
		# 	'pixel_offset_key': "spatial_resolution",
		# 	'prf': lambda i,j: max(0, 1-abs(j-1/2))
		# }
	},
	'omi': {
		'name': "OMI",
		'full_name': "Ozone Monitoring Instrument",
		'website': "https://aura.gsfc.nasa.gov/omi.html",
		'start_date': dt.date(2004, 8, 9)
	},
	'viirs': {
		'name': "VIIRS",
		'full_name': "Visible Infrared Imaging Radiometer Suite",
		'website': "https://www.nesdis.noaa.gov/our-satellites/"
			"currently-flying/joint-polar-satellite-system/"
			"visible-infrared-imaging-radiometer-suite-viirs"
	}
}

# Variables for spaceborne instruments and their platforms
AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS = {
	'aqua': {
		'name': "Aqua",
		'organization': "NASA",
		'program': "Earth Observing System (EOS)",
		'launch_date': dt.date(2002, 5, 4),
		'website': "https://aqua.nasa.gov/",
		'instruments': {
			'modis': AVAILABLE_SATELLITE_INSTRUMENTS['modis'] | {
				'first_light': dt.date(2002, 6, 24),
				'data_tag': "MYD",
				'geo_product': "MYD03"
			}
		}
	},
	'aura': {
		'name': "Aura",
		'organization': "NASA",
		'program': "Earth Observing System (EOS)",
		'launch_date': dt.date(2004, 7, 15),
		'website': "https://science.nasa.gov/mission/aura/",
		'instruments': {
			'omi': AVAILABLE_SATELLITE_INSTRUMENTS['omi'],
		}
	},
	'goes-16': {
		'alternative_ids': ['goes16', 'goes-r'],
		'name': "GOES-16",
		'alternative_names': ["GOES 16", "GOES-R", "GOES R", "GOES East", \
			"GOES-East"],
		'full_name': "Geostationary Operational Environmental Satellite 16 - R "
			"Series",
		'organization': ["NOAA", "NASA"],
		'launch_date': dt.date(2016, 11, 19),
		'website': "https://www.goes-r.gov/",
		'instruments': {
			'abi': AVAILABLE_SATELLITE_INSTRUMENTS['abi'] | {
				'first_light': dt.date(2017, 1, 15),
				'start_date': dt.date(2017, 12, 18),
				'end_date': dt.date(2025, 4, 7),
				'data_tag': "G16"
			}
		}
	},
	'goes-17': {
		'alternative_ids': ['goes17', 'goes-s'],
		'name': "GOES-17",
		'alternative_names': ["GOES 17", "GOES-S", "GOES S", "GOES West", \
			"GOES-West"],
		'full_name': "Geostationary Operational Environmental Satellite 17 - R "
			"Series",
		'organization': ["NOAA", "NASA"],
		'launch_date': dt.date(2018, 3, 1),
		'website': "https://www.goes-r.gov/",
		'instruments': {
			'abi': AVAILABLE_SATELLITE_INSTRUMENTS['abi'] | {
				'first_light': dt.date(2018, 5, 20),
				'start_date': dt.date(2019, 2, 12),
				'end_date': dt.date(2023, 1, 4),
				'data_tag': "G17"
			}
		}
	},
	'goes-18': {
		'alternative_ids': ['goes18', 'goes-t'],
		'name': "GOES-18",
		'alternative_names': ["GOES 18", "GOES-T", "GOES T" "GOES West", \
			"GOES-West"],
		'full_name': "Geostationary Operational Environmental Satellite 18 - R "
			"Series",
		'organization': ["NOAA", "NASA"],
		'launch_date': dt.date(2022, 3, 1),
		'website': "https://www.goes-r.gov/",
		'instruments': {
			'abi': AVAILABLE_SATELLITE_INSTRUMENTS['abi'] | {
				'first_light': dt.date(2022, 5, 5),
				'start_date': dt.date(2023, 1, 4),
				'data_tag': "G18"
			}
		}
	},
	'goes-19': {
		'alternative_ids': ['goes19', 'goes-u'],
		'name': "GOES-19",
		'alternative_names': ["GOES 19", "GOES-U", "GOES U", "GOES East", \
			"GOES-East"],
		'full_name': "Geostationary Operational Environmental Satellite 19 - R "
			"Series",
		'organization': ["NOAA", "NASA"],
		'launch_date': dt.date(2024, 6, 25),
		'website': "https://www.goes-r.gov/",
		'instruments': {
			'abi': AVAILABLE_SATELLITE_INSTRUMENTS['abi'] | {
				'first_light': dt.date(2024, 8, 30),
				'start_date': dt.date(2025, 4, 7),
				'data_tag': "G19"
			}
		}
	},
	'noaa-20': {
		'alternative_ids': ['noaa20', 'jpss-1', 'jpss1'],
		'name': "NOAA-20",
		'alternative_names': ["NOAA 20", "JPSS-1", "JPSS 1"],
		'full_name': "National Oceanic and Atmospheric Administration 20",
		'organization': ["NOAA", "NASA"],
		'launch_date': dt.date(2017, 11, 18),
		'website': "https://www.nesdis.noaa.gov/jpss/",
		'instruments': {
			'viirs': AVAILABLE_SATELLITE_INSTRUMENTS['viirs'] | {
				'first_light': dt.date(2017, 12, 13),
				'data_tag': "VJ1",
				'geo_product': {750: "VJ103MOD", 375: "VJ103IMG"},
				'geo_product_key': "spatial_resolution"
			}
		}
	},
	'noaa-21': {
		'alternative_ids': ['noaa21', 'jpss-2', 'jpss2'],
		'name': "NOAA-21",
		'alternative_names': ["NOAA 21", "JPSS-2", "JPSS 2"],
		'full_name': "National Oceanic and Atmospheric Administration 21",
		'organization': ["NOAA", "NASA"],
		'launch_date': dt.date(2022, 11, 10),
		'website': "https://www.nesdis.noaa.gov/jpss/",
		'instruments': {
			'viirs': AVAILABLE_SATELLITE_INSTRUMENTS['viirs'] | {
				'first_light': dt.date(2023, 2, 9),
				'data_tag': "VJ2",
				'geo_product': {750: "VJ203MOD", 375: "VJ203IMG"},
				'geo_product_key': "spatial_resolution"
			}
		}
	},
	'suomi-npp': {
		'alternative_ids': ['npp', 'snpp'],
		'name': "Suomi NPP",
		'alternative_names': ["NPP", "Suomi-NPP"],
		'full_name': "Suomi National Polar-orbiting Partnership",
		'organization': ["NOAA", "NASA"],
		'launch_date': dt.date(2011, 10, 28),
		'website': "https://science.nasa.gov/mission/suomi-npp/",
		'instruments': {
			'viirs': AVAILABLE_SATELLITE_INSTRUMENTS['viirs'] | {
				'first_light': dt.date(2011, 11, 21),
				'data_tag': "VNP",
				'geo_product': {750: "VNP03MOD", 375: "VNP03IMG"},
				'geo_product_key': "spatial_resolution"
			}
		}
	},
	'terra': {
		'name': "Terra",
		'organization': "NASA",
		'program': "Earth Observing System (EOS)",
		'launch_date': dt.date(1999, 12, 18),
		'website': "https://terra.nasa.gov/",
		'instruments': {
			'modis': AVAILABLE_SATELLITE_INSTRUMENTS['modis'] | {
				'first_light': dt.date(2000, 2, 24),
				'data_tag': "MOD",
				'geo_product': "MOD03"
			}
		}
	}
}

# Variables for airborne instruments
AVAILABLE_AIRCRAFT_INSTRUMENTS = {
	'master': {
		'name': "MASTER",
		'full_name': "MODIS/ASTER Airborne Simulator",
		'geo_product': "MASTERL1B",
		'data_tag': "MASTER",
		'start_date': dt.date(1998, 12, 2),
		'website': "https://masterprojects.jpl.nasa.gov",
		'specifications': {
			'scan_width': 1,					# pixels
			'swath_width': 716,					# pixels
			'pixel_offset': 0,					# pixels
			# 'scan_rate': [6.25, 12.5, 25],		# rps
			'ifov': 2.5e-3,						# rad
			'pixel_scale': 2*pi/3000,			# rad
			'bit_depth': 12,					# bits
			'digitization': 16					# bits
		}
	}
}

# Variables for aircraft
AVAILABLE_AIRCRAFT_PLATFORMS = {
	'nasa-afrc-er-2': {
		'name': "Earth Resources 2",
		'organization': "NASA",
		'program': "Airborne Science Program",
		'operator': "NASA Armstrong Flight Research Center",
		'website': "https://airbornescience.nasa.gov/aircraft/ER-2_-_AFRC",
		'specifications': {
			'duration': "8 hrs",
			'range': "5000 Nmi",
			'maximum_altitude': "70000 ft",
			'air_speed': "410 knots",
			'useful_payload': "2900 lbs",
			'gross_take_off_weight': "40000 lbs",
			'onboard_operators': 1
		}
	},
	'nasa-jsc-wb-57': {
		'name': "Weather Martin B-57 Canberra",
		'organization': "NASA",
		'program': "Airborne Science Program",
		'operator': "NASA Johnson Space Center",
		'website': "https://airbornescience.nasa.gov/aircraft/WB-57_-_JSC",
		'specifications': {
			'duration': "6.5 hrs",
			'range': "2500 Nmi",
			'maximum_altitude': "60000 ft",
			'air_speed': "410 knots",
			'useful_payload': "8800 lbs",
			'gross_take_off_weight': "72000 lbs",
			'onboard_operators': 2
		}
	},
	'nasa-larc-b200': {
		'name': "Beechcraft King Air 200",
		'organization': "NASA",
		'program': "Airborne Science Program",
		'operator': "NASA Langley Research Center",
		'website': "https://airbornescience.nasa.gov/aircraft/B200_-_LARC",
		'specifications': {
			'duration': "6.2 hrs",
			'range': "1250 Nmi",
			'maximum_altitude': "35000 ft",
			'air_speed': "260 knots",
			'useful_payload': "4100 lbs",
			'gross_take_off_weight': "13500 lbs",
			'onboard_operators': 4
		}
	}
}
