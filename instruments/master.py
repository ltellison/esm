"""MASTER
Module for creating and operating on classes relating to the MODIS/ASTER 
Airborne Simulator (MASTER).

Author:
	Luke Ellison

Version:
	0.1

History:
	v0.1, 21-Nov-2025, Luke Ellison: Module compiled.

Global Variables:
	MASTER_PRODUCT_FORMATTERS -- Dictionary of MASTER product filename 
		formatters.
	MASTER_PRODUCT_REVERSE_FORMATTERS -- Dictionary of MASTER product filename 
		reverse formatters.
	MASTER_ITER_FILTERS -- A MASTER file name attribute name (used in filtering 
		file search results) or list of such names where the attribute value is 
		an iterable after formatting.
	MASTER_PRODUCTS -- Dictionary of available MASTER products and their 
		associated metadata.

Classes:
	MASTER -- Defines a MASTER object on a given aircraft platform.

External Modules:
	- dateutil -- https://dateutil.readthedocs.io/
"""
# import datetime as dt
from dateutil.relativedelta import relativedelta
from ..instrument import WhiskbroomScanner

#------------------------------ GLOBAL VARIABLES ------------------------------#

# MASTER product formatters
MASTER_PRODUCT_FORMATTERS = {
	'flightid': lambda s: (f"{s[:2]}-{s[2:5]}-{s[5:7]}", int(s[-2:])),
	'flightno': lambda n: f"{n[:2]}-{n[2:5]}-{n[5:]}",
	'flightline': int,
	'start_timestamp': "%Y%m%d_%H%M",
	'start_date': "%Y%m%d",
	'start_time': "%H%M",
	'end_time': "%H%M",
	'version': int,
	'subversion': int
}
MASTER_PRODUCT_REVERSE_FORMATTERS = {
	'flightid': lambda n,l: f"{n.replace('-', '')}_{l:02d}",
	'flightno': lambda s: s.replace('-', ''),
	'flightline': '02d',
}
MASTER_ITER_FILTERS = ['flightid']

# MASTER products
MASTER_PRODUCTS = {
	'MASTERL1B': {
		'name': "MODIS/ASTER Airborne Simulator (MASTER) Level-1B Data",
		'level': '1b',
		'structure': "swath",
		'filename_pattern': "(?P<product>MASTERL1B)_(?P<flightid>"
			"(?P<flightno>\d{7})_(?P<flightline>\d{2}))_(?P<start_timestamp>"
			"(?P<start_date>\d{8})_(?P<start_time>\d{4}))_(?P<end_time>\d{4})_"
			"V(?P<version>\d{2})\.hdf",
		'band_dimension_name': "NumberOfChannels",
		'along_track_dimension_name': "NumberOfScanlines",
		'across_track_dimension_name': "NumberOfPixels",
		'labels': {
			'latitude_name': "PixelLatitude",
			'longitude_name': "PixelLongitude",
			'platform_latitude_name': "AircraftLatitude",
			'platform_longitude_name': "AircraftLongitude",
			'altitude_name': "AircraftAltitude",
			'elevation_name': "PixelElevation",
			'heading_name': "AircraftHeading",
			'pitch_name': "AircraftPitch",
			'roll_name': ("AircraftRollCount", lambda r: r*360/65536),
			'timestamp_name': "GreenwichMeanTime",
			'date_name': ("YearMonthDay", lambda d: \
				f"{(s:=str(d))[:4]}-{s[4:6]}-{s[6:]}"),				# `str` works for Python >=3.11
			'time_name': ("ScanlineTime", lambda t: t*3600),
			'sensor_azimuth_name': "SensorAzimuthAngle",
			'sensor_zenith_name': "SensorZenithAngle",
			'solar_azimuth_name': "SolarAzimuthAngle",
			'solar_zenith_name': "SolarZenithAngle",
		},
		'crs': "NAD 83"		# pyproj.crs.CRS.from_user_input(..crs)
	},
	'MASTERL2': {
		'name': "Atmospheric Corrected MASTER Land Surface Temperature, "
			"Emissivity, and QAmap",
		'level': 2,
		'structure': "swath",
		'filename_pattern': "(?P<product>MASTERL2)_(?P<flightid>"
			"(?P<flightno>\d{7})_(?P<flightline>\d{2}))_(?P<start_timestamp>"
			"(?P<start_date>\d{8})_(?P<start_time>\d{4}))_(?P<end_time>\d{4})_"
			"V(?P<version>\d{2})(?:_(?P<platform>(?:[^\W_]|-)+))?"
			"(?:_SV(?P<subversion>\d{2}))?\.hdf5",
		'band_dimension_index': 2,
		'along_track_dimension_index': 0,
		'across_track_dimension_index': 1,
		'labels': {
			'latitude_name': "Lat",
			'longitude_name': "Lon"
		}
	},
}


#---------------------------------- CLASSES ----------------------------------#

#################################### MASTER ####################################
class MASTER(WhiskbroomScanner):
	"""Defines a MASTER object on a given aircraft platform.
	
	Functions:
		__init__ -- Initializes a MASTER instrument object.
		set_state -- Sets the platform's state information (position and 
			velocity).
		corners -- Gets the corner geolocation coordinates of a given MASTER 
			dataset.
		get_radiance -- Gets the radiance or brightness temperature data from a 
			MASTER Level 1B data file for a given band or set of bands.
	
	Returns:
		- An object defining a MASTER instrument.
	"""

	# Constructor method
	def __init__(self, /, platform=None, **kwargs):
		"""Initializes a MASTER instrument object.
		
		Parameters:
			platform: type=Platform|str, default=None
				- The airborne platform on which this MASTER instance is located.
		"""
		from copy import deepcopy
		from ..platform import Platform, Aircraft
		
		# Get standard platform ID
		if isinstance(platform, str):
			platform = Aircraft(platform)
		elif not isinstance(platform, Platform):
			platform = None

		# Get available products
		products = deepcopy(MASTER_PRODUCTS)
		if 'available_products' in kwargs and \
		  isinstance(kwargs['available_products'], dict):
			products.update(kwargs['available_products'])
		
		# Initialize instrument object
		super().__init__('master', platform=platform, \
			formatters=MASTER_PRODUCT_FORMATTERS, \
			reverse_formatters=MASTER_PRODUCT_REVERSE_FORMATTERS, \
			iter_filters=MASTER_ITER_FILTERS, available_products=products, \
			**kwargs)		# geo_product="MASTERL1B", 
		
		# Set dimension renaming function
		# def _rename_dimension(dim_name):
		# 	return dim_name[:dim_name.index(':')] if ':' in dim_name else \
		# 		dim_name
		# self._rename_dimension = _rename_dimension
	
	# Method to set MASTER state information (position, velocity)
	def set_state(self, /, dataset=None, line=None, strict=False, **kwargs):
		"""Sets the platform's state information (position and velocity).
	
		Parameters:
			dataset: type=Dataset, default=None
				- The MASTER dataset for which to set the platform state 
				information.  If `None`, the geolocation dataset will be 
				searched (if one was specified in the instrument initialization) 
				using the extra keyword arguments to identify the file of 
				interest (these will be passed to the `product.find_files` 
				method).
			line: type=int, default=None
				- The scan line index for which to set the platform state 
				information.  If `None`, will set the state for the whole 
				dataset instead of its scan.
			strict: type=bool, default=False
				- If `True`, will raise an error if any of the standardized 
				variables specified in the metadata are not found in the dataset.
			**kwargs:
				- 

		# External modules:
		# 	- numpy -- https://numpy.org/
		"""
		# import numpy as np
		# from ..platform import lla2xyz, uvw2enu
		# from ..data import sort_dims
		# from ..ancillary import iterable, findattr, lon_convert

		# Set platform state via parent class' method
		super().set_state(dataset=dataset, line=line, strict=strict, **kwargs)

		# # Get state from associated geolocation product
		# geo_product_id = findattr(self, 'geo_product')
		# if geo_product_id == dataset.product.id:
		# 	geo_ds = dataset
		# else:
		# 	geo_ds = dataset.cousin_dataset(geo_product_id)

		# 
		# if geo_ds:
		# 	# 
		# 	if line is None:
		# 		# dim_name = findattr(geo_ds, 'along_track_dimension_name', True)
		# 		nlines = geo_ds.dim_index('along_track', 'AircraftLatitude').size
		# 		s = slice((nlines-1)//2, (nlines+2)//2)
		# 	elif iterable(line):
		# 		raise ValueError("'line' must be a scalar value")
		# 	else:
		# 		s = slice(nlines, nlines+1)

			# Get point data at nadir
			# lat = (lats:=geo_ds.extract('AircraftLatitude', s)).mean()
			# lon = (lons:=geo_ds.extract('AircraftLongitude', s)).mean()
			# alt = (alts:=geo_ds.extract('AircraftAltitude', s)).mean()
			# head = geo_ds.extract('AircraftHeading', s).mean()
			# # pitch = np.radians(geo_ds.extract('AircraftPitch', s).mean())
			# # roll = geo_ds.extract('AircraftRollCount', s).mean()*2*np.pi/65536

			# Get vector data at nadir
			# if lats.size == 1:
			# 	s = slice(max(0, s.start-1), s.stop+1)
			# 	lats =  (v:=geo_ds.extract('AircraftLatitude', s))[[0,-1]]
			# 	lons =  geo_ds.extract('AircraftLongitude', s)[[0,-1]]
			# 	times = geo_ds.extract('ScanlineTime', s)[[0,-1]]		# [hrs]
			# 	# steps = len(v)-1
			# else:
			# 	times = geo_ds.extract('ScanlineTime', s)				# [hrs]
			# 	# steps = 1
			
			# # Get unit displacement in ECEF
			# pt1,pt2 = np.array(list(zip(*lla2xyz(lons, lats, alts))))
			# disp = pt2-pt1
			# dist = np.linalg.norm(disp)
			# u,v,w = disp/dist

			# # Convert to ENU geodetic coordinates and calculate course
			# e,n,u = uvw2enu(u, v, w, lat, lon)
			# course = lon_convert(np.arctan2(e, n), np.pi, radians=True)

			# # Calculate the velocity vector
			# time = np.diff(times).item()*3600							# [s]
			# vel = disp/time
			
			# Update results
			# kwargs.update(dict(lat=lat, lon=lon, alt=alt, vel=vel, head=head, 
			# 	course=course))
	
	# Method to get the corners of a MASTER granule
	def corners(self, /, dataset=None, extend=False, **kwargs):
		"""Gets the corner geolocation coordinates of a given MASTER dataset.
	
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
		
		# Return corners using MASTER attributes, with fallback to parent class
		attrs = [("lat_UL", "lon_UL"), ("lat_UR", "lon_UR"), \
			("lat_LL", "lon_LL"), ("lat_LR", "lon_LR")]
		try:
			return np.array([[dataset.read(attr=attr) for attr in pair] for \
				pair in attrs])
		except:
			return super().corners(dataset=dataset, extend=extend, **kwargs)
	
	# Method to get the radiance or brightness temperature data from the MASTER 
	# Level 1B data file
	def get_radiance(self, /, measurement='radiance', file=None, band=True, 
	  s=slice(None), dual_gain=True, output='array', **kwargs):
		"""Gets the radiance or brightness temperature data from a MASTER Level 
		1B data file for a given band or set of bands.
		
		Parameters:
			measurement: type=str, default='radiance'
				- The measurement ('radiance'/'rad' or 'brightness temperature'/
				'bt') of data to output.
			file: type=pathlib.Path|str, default=None
				- The file path of the file to open.  If `None`, will use the 
				additional keyword arguments to locate a file.
			band: type=int|str|list|bool, default=True
				- The band (as an integer or string) or list of bands for which 
				to get the data.  If `True`, will output all bands if 
				`measurement` is 'radiance' or 'brightness temperature', or all 
				reflectance bands if `measurement` is 'reflectance'.
			s: type=slice|int|tuple, default=slice(None)
				- A slice to apply to the data.  Note that if the band 
				dimension is sliced such that requested bands are eliminated, 
				the program will throw an error.
			dual_gain: type=bool, default=True
				- If `True`, will combine dual gain bands (26/32) into a single 
				band if either are requested and the timestamp of the data file 
				is after the alteration to band 26.
			output: type=str, default='array'
				- The output format: 'array' for a single ndarray, 'list' for a 
				list of ndarrays, or 'dict' for a dictionary of ndarrays 
				referenced by the band ID.
			**kwargs:
				- Additional keyword arguments for the following functions:
					- esm.product.find_files: flightid, flightno, flightline, 
	  				timestamp, date, time, version, ext, directory
				- If more than one file is found with these specifications, an 
				error will be raised.

		External Modules:
			- numpy -- https://numpy.org/

		Returns:
			- The radiance or brightness temperature data for the first file 
			found with the `kwargs` dictionary as either an ndarray, list or 
			dictionary.  Radiance units are W/m^2/sr/μm.
		"""
		import datetime as dt
		import numpy as np
		from ..data import full_slice, slice_to_array, planck
		from ..ancillary import iterable, assert_slice

		# Test input data types
		s = assert_slice(s)

		# Settings
		var = "CalibratedData"
		band26_change_date = dt.date(2011, 1, 1)		# Band 26 change date

		# Get the value to measure
		measurement = measurement.strip().lower().replace('_', ' ')
		if measurement not in ['radiance', 'rad', 'brightness temperature', \
		  'bt']:
			raise ValueError("'measurement' must be either 'radiance' or "
				"'brightness temperature'")
		if measurement == 'rad':
			measurement = 'radiance'
		elif measurement == 'bt':
			measurement = 'brightness temperature'

		# Format band input
		if band is True:
			band = list(range(1,51))
			single_band = False
		else:
			single_band = not iterable(band)
			if single_band:
				band = [int(band)]
			else:
				band = list(map(int, band))

		# Initialize dictionary of band data
		data_dict = {b:None for i,b in enumerate(band) if b not in band[:i]}
		
		# Get the product object
		product_id = f"{self.data_tag}L1B"
		product = self.load_product(product_id, **kwargs)

		# Get the file and file name attributes
		if file is None:
			files = product.find_files(**kwargs)
			for i in range(2):
				try:
					file,attrdict = next(files)
				except:
					if not i:
						raise ValueError(f"Could not find a {product.id} file "
							"with given specifications.")
					break
			else:
				raise ValueError(f"Multiple files found for {product.id} "
					"product with given specifications.")
		else:
			attrdict = product.get_filename_attrs(file)
		ds = product.load_dataset(file)
		date = attrdict['start_date']

		# Get variables for brightness temperature conversion
		if measurement == 'brightness temperature':
			wavelengths = ds.extract(var="EffectiveCentralWavelength_IR_bands", \
				fill_value="fill_value")
			wavelengths = 1e-6 * np.where(wavelengths.mask, \
				ds.extract(var="Central100%ResponseWavelength"), wavelengths)
			btcorr_m = ds.extract(var="TemperatureCorrectionSlope")
			btcorr_b = ds.extract(var="TemperatureCorrectionIntercept")

		# Get the index for the dimension of bands
		idim = ds.dim_index('band', var)
		if idim is None:
			raise ValueError("Could not find the band dimension.")
		
		# Get the slice object for extracting data for the requested bands
		shape = ds.get_shape(var)
		s2 = list(full_slice(s, shape))
		is2 = slice_to_array(s2[idim], (shape[idim],))
		if not iterable(is2):
			is2 = [is2]

		# Check slice and get data for each requested band
		if not set(is2).issuperset([b-1 for b in band]):
			raise ValueError(f"The band dimension (index {idim}) in the 's' "
				"slice object eliminated necessary bands prior to extraction.")
		dual = dual_gain and {26,32}.intersection(band) and date > \
			band26_change_date
		band_set = set(band+[26,32]) if dual else set(band)
		for b in band_set:
			i = b-1
			s2[idim] = i
			scale_factor = ds.read(var=var, attr='scale_factor')[i]
			data_dict[b] = ds.extract(var, s=tuple(s2), scale_factor= \
				scale_factor)								# [W/m2/sr/μm]
			if measurement == 'brightness temperature':
				data_dict[b] = (planck(wavelengths[i], radiance=data_dict[b]* \
					1e6)-btcorr_b[i])/btcorr_m[i]			# [K]
		
		# Get combined channels for dual gain 26/32 band
		if dual:
			if 32 in band and np.ma.isMA(data_dict[32]):
				data_dict[32][data_dict[32].mask] = \
					data_dict[26][data_dict[32].mask]
			if 26 in band and np.ma.isMA(data_dict[26]):
				data_dict[26][data_dict[26].mask] = \
					data_dict[32][data_dict[26].mask]

		# Return radiance/BT data as a dictionary
		output = output.strip().lower()
		if output == 'dict':
			return {b:data_dict[b] for i,b in enumerate(band) if b not in \
				band[:i]}
		
		# Return radiance/BT data as a list
		elif output == 'list':
			return [data_dict[b] for b in band]
		
		# Return radiance/BT data as an ndarray
		elif output == 'array':
			# Compile data into single array
			for b in band:
				try:
					concatenate = np.ma.concatenate if np.ma.isMA(data) or \
						np.ma.isMA(data_dict[b]) else np.concatenate
					data = concatenate((data, data_dict[b][None]))
				except:
					data = data_dict[b][None]
			
			# Position band dimension
			idim = sum([not isinstance(size, (int, np.integer)) for size in \
				s2[:idim]])
			if single_band and data.shape[0] == 1:
				data = data[0]
			elif idim:
				data = np.moveaxis(data, 0, idim)
			
			# Return data
			return data
		
		# Throw error if 'output' invalid
		else:
			raise ValueError("'output' must be one of 'dict', 'list' or 'array'")
#################################### MASTER ####################################
