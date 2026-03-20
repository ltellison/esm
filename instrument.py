"""Instrument
Module for creating and operating on classes of Earth Science Mission 
instruments.

Author:
	Luke Ellison

Version:
	0.1

History:
	v0.1, 09-Dec-2025, Luke Ellison: Module compiled.

Classes:
	Instrument -- Defines an instrument object on an Earth Science Mission 
		platform.
	WhiskbroomScanner -- Defines a whiskbroom instrument object on an Earth 
		Science Mission platform.
	PushbroomScanner -- Defines a pushbroom instrument object on an Earth 
		Science Mission platform.

Functions:
	get_available_instruments -- Gets the instrument ID of all available 
		instruments for the given platform(s).
	get_standard_instrument_id -- Gets the standardized name (ID) of a specified 
		instrument for the given platform(s).
	get_instrument_class -- Gets the class for the given instrument ID and 
		platform ID.
	load_instrument -- Creates either an object of an instrument-specific class 
		if available, or a generic Instrument object otherwise.
	get_instrument_platform -- Gets the platform IDs of the specified instrument.
"""
# from .config import EARTH_RADIUS

#------------------------------ GLOBAL VARIABLES ------------------------------#

# The modules available for reading ESM RSR data
# RSR_READER_MODULES = ['pyspectral', 'eradiate']


#---------------------------------- CLASSES ----------------------------------#

################################## Instrument ##################################
class Instrument:
	"""Defines an instrument object on an Earth Science Mission platform.
	
	Functions:
		__init__ -- Initializes an instrument object on an Earth Science Mission 
			platform.
		set_datadir -- Sets the data directory for this instrument.
		search_products -- Filters list of products by searching their 
			attributes.
		load_product -- Initializes a product of the instrument.
	
	Returns:
		- An object defining an instrument on an Earth Science Mission platform, 
		including metadata such available products.
	"""

	# Constructor method
	def __init__(self, /, id, platform=None, meta=None, formatters=None, 
	  reverse_formatters=None, iter_filters=None, directory=None, 
	  load_product=None, available_products=None, geo_product=None, 
	  geo_product_key=None, swath_width=None, swath_width_key=None, 
	  swath_length=None, swath_length_key=None, pixel_offset=None, 
	  pixel_offset_key=None, pixel_scale=None, pixel_scale_key=None, ifov=None, 
	  ifov_key=None, gsd=None, gsd_key=None, prf=None, prf_key=None, **kwargs):
		"""Initializes an instrument object on an Earth Science Mission platform.
	
		Parameters:
			id: type=str
				- The standardized name (ID) of the instrument or one of its 
				alternative IDs or names.  If not found, will still create an 
				Instrument object with no geometry, meta information, products, 
				or platform.
			platform: type=Platform|str|bool, default=None
				- The platform on which the instrument is located.  If a 
				Platform object, will use its ID.  If a string, will use the 
				standardized platform ID to create a new Platform object.  If 
				`False`, will ensure that no platform is set (even if the 
				instrument ID is found).  If `None`, will search for the 
				instrument ID among all available platforms and create a new 
				Platform object if one and only one platform is found with the 
				instrument ID.
			meta: type=dict, default=None
				- Information that will be added to the default information for 
				the given instrument (duplicate keys in the default information 
				are overwritten).
			formatters: type=dict, default=None
				- A dictionary of standard product field formatters.  Accepted 
				fields are stored in the `PRODUCT_FIELDS` global variable in the 
				`product` module.
			reverse_formatters: type=dict, default=None
				- A dictionary of standard product field reverse formatters.  
				Accepted fields are stored in the `PRODUCT_FIELDS` global 
				variable in the `product` module.  If any necessary formatters 
				are not included, then if it exists in the `formatters` argument, 
				the `datetime` function `strftime` will be used; otherwise, if 
				the pattern in the given file name includes only digits, then 
				the digits of the string version of the value is fit to those 
				number of digits; otherwise, `str` will be used as the reverse 
				formatter.
			iter_filters: type=list|str, default=None
				- A file name attribute name (used in filtering file search 
				results) or list of such names where the attribute value is an 
				iterable after formatting.
			directory: type=str|pathlib.Path, default=None
				- The directory of the instrument's data.  Set to `False` to 
				ensure no data directory attribute is set.
			load_product: type=str|list|bool, default=None
				- The standardized name (ID) or list of IDs of the instrument 
				product.  If `True`, will initialize all products for the 
				instrument.
			available_products: type=dict, default=None
				- A dictionary of available product IDs and metadata for the 
				instrument that will be made available as the object attribute 
				`products` and used for loading Product objects.
			geo_product: type=str|dict, default=None
				- The geolocation product of this instrument.  If multiple 
				values are possible due to different product/variable 
				configurations, enter a dictionary with keys corresponding to 
				different possible configuration values (e.g. platforms) and 
				set `geo_product_key` to the attribute name/location of this 
				configuration parameter.
			geo_product_key: type=str, default=None
				- The attribute name/location of the key values in the 
				`geo_product` dictionary.  For instance, if the configuration 
				values that comprise the `geo_product` keys represent the 
				platform ID, `geo_product_key` should be set to `platform.id` if 
				a given object has such an attribute.  If the object does not 
				have such an attribute saved in its metadata, parent objects 
				will be searched recursively all the way up to the Platform 
				object until it is located.  Periods may be used to specify more 
				targeted information (e.g. using `product.id` instead of simply 
				`id`.)
			swath_width: type=int|dict, default=None
				- The side-to-side width in pixels of the granule.  If multiple 
				values are possible due to different product/variable 
				configurations, enter a dictionary with keys corresponding to 
				different possible configuration values (e.g. spatial 
				resolutions) and set `swath_width_key` to the attribute 
				name/location of this configuration parameter.
			swath_width_key: type=str, default=None
				- The attribute name/location of the key values in the 
				`swath_width` dictionary.  For instance, if the configuration 
				values that comprise the `swath_width` keys represent the 
				spatial resolution, `swath_width_key` should be set to 
				`spatial_resolution` if a given object has such an attribute.  
				If the object does not have such an attribute saved in its 
				metadata, parent objects will be searched recursively all the 
				way up to the Platform object until it is located.  Periods may 
				be used to specify more targeted information (e.g. using 
				`product.id` instead of simply `id`.)
			swath_length: type=int|dict, default=None
				- The end-to-end length in pixels of the granule.  If multiple 
				values are possible due to different product/variable 
				configurations, enter a dictionary with keys corresponding to 
				different possible configuration values (e.g. spatial 
				resolutions) and set `swath_length_key` to the attribute 
				name/location of this configuration parameter.
			swath_length_key: type=str, default=None
				- The attribute name/location of the key values in the 
				`swath_length` dictionary.  (See the `swath_width_key` 
				description.)
			pixel_offset: type=float|tuple|dict, default=None
				- The pixel fraction that the granule grid is offset by.  If one 
				number, is assumed to be the offset only in the across-track 
				dimension.  If a two-element tuple, will be the (along-track, 
				across-track) offsets.  If multiple values are possible due to 
				different product/variable configurations, enter a dictionary 
				with keys corresponding to different possible configuration 
				values (e.g. spatial resolutions) and set `pixel_offset_key` to 
				the attribute name/location of this configuration parameter.
			pixel_offset_key: type=str, default=None
				- The attribute name/location of the key values in the 
				`pixel_offset` dictionary.  (See the `swath_width_key` 
				description.)
			pixel_scale: type=float|tuple|dict, default=None
				- The pixel scale (actual pixel dimensions on a grid) in radians. 
				If the system is oversampled, this will be smaller than `ifov`; 
				if it is undersampled, it will be larger, and equal if 
				critically sampled. If one number, is assumed to be the pixel 
				scale in both along-track and across-track dimensions.  If a 
				two-element tuple, will be the (along-track, across-track) IFOV 
				values.  If multiple values are possible due to different 
				product/variable configurations, enter a dictionary with keys 
				corresponding to different possible configuration values (e.g. 
				spatial resolutions) and set `pixel_scale_key` to the attribute 
				name/location of this configuration parameter.
			pixel_scale_key: type=str, default=None
				- The attribute name/location of the key values in the 
				`pixel_scale` dictionary.  (See the `swath_width_key` 
				description.)
			ifov: type=float|tuple|dict, default=None
				- The instantaneous field of view in radians. If one number, is 
				assumed to be the IFOV in both along-track and across-track 
				dimensions.  If a two-element tuple, will be the (along-track, 
				across-track) IFOV values.  If multiple values are possible due 
				to different product/variable configurations, enter a dictionary 
				with keys corresponding to different possible configuration 
				values (e.g. spatial resolutions) and set `ifov_key` to the 
				attribute name/location of this configuration parameter.
			ifov_key: type=str, default=None
				- The attribute name/location of the key values in the `ifov` 
				dictionary.  (See the `swath_width_key` description.)
			gsd: type=float|tuple|dict, default=None
				- The ground sample distance (pixel resolution) at nadir at the 
				geoid. If one number, is assumed to be the GSD in both 
				along-track and across-track dimensions.  If a two-element tuple, 
				will be the (along-track, across-track) GSD values.  If multiple 
				values are possible due to different product/variable 
				configurations, enter a dictionary with keys corresponding to 
				different possible configuration values (e.g. spatial 
				resolutions) and set `gsd_key` to the attribute name/location of 
				this configuration parameter.
			gsd_key: type=str, default=None
				- The attribute name/location of the key values in the `gsd` 
				dictionary.  (See the `swath_width_key` description.)
			prf: type=function, default=None
				- The pixel response function of the optical system. The function 
				should take two arguments, the first being the along-track 
				coordinate and the second the across-track coordinate, which may 
				range from -1 to 2. The range 0 to 1 represents the edges of a 
				pixel, while -1 to 0 represents the neighboring pixel one one 
				side and 1 to 2 represents the neighboring pixel on the other 
				side. The output of the function should yield a value between 0 
				and 1, where 1 is full contribution of the signal and 0 is no 
				contribution.  If multiple functions are possible due to 
				different product/variable configurations, enter a dictionary 
				with keys corresponding to different possible configuration 
				values (e.g. spatial resolutions) and set `prf_key` to the 
				attribute name/location of this configuration parameter.
			prf_key: type=str, default=None
				- The attribute name/location of the key values in the `prf` 
				dictionary.  (See the `swath_width_key` description.)

		External Modules:
			- numpy -- https://numpy.org/
		"""
		from types import NoneType
		from pathlib import Path
		import numpy as np
		from .config import AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS, \
			AVAILABLE_SATELLITE_INSTRUMENTS, AVAILABLE_AIRCRAFT_PLATFORMS, \
			AVAILABLE_AIRCRAFT_INSTRUMENTS
		from .platform import Platform, Satellite, Aircraft, \
			get_standard_platform_id
		from .product import PRODUCT_FIELDS
		from .ancillary import iterable, assert_iterable, findattr #, set_attr_by_key #, getattr_recursive

		# Check input formats
		assert isinstance(id, str)
		assert isinstance(platform, (NoneType, Platform, str, bool))
		assert isinstance(meta, (NoneType, dict))
		assert isinstance(formatters, (NoneType, dict))
		assert isinstance(reverse_formatters, (NoneType, dict))
		assert_iterable(iter_filters, (list, tuple, set, dict, np.ndarray), str)
		assert isinstance(directory, (NoneType, str, Path))
		assert isinstance(load_product, (NoneType, str, list, tuple, bool, \
			np.ndarray))
		assert isinstance(available_products, (NoneType, dict))
		assert isinstance(geo_product, (NoneType, str, dict))
		assert isinstance(geo_product_key, (NoneType, str))
		# for param,param_key,t in [(geo_product, geo_product_key, str), \
		#   (swath_width, swath_width_key, int), (swath_length, \
		#   swath_length_key, int)]:
		for param,param_key,t in [(swath_width, swath_width_key, int), \
		  (swath_length, swath_length_key, int)]:
			assert_iterable(param, dict, t)
			if param is not None and t is not str:
				assert all(p > 0 for p in param.values()) if \
					isinstance(param, dict) else param > 0
			if isinstance(param, dict):
				assert isinstance(param_key, str)
		for param,pos in [(pixel_offset, False), (pixel_scale, True), \
		  (ifov, True), (gsd, True)]:
			test = (lambda x: x > 0) if pos else None
			if isinstance(param, dict):
				assert_iterable(param, dict, (float, int, list, tuple, \
					np.ndarray), require_iterable=True)
				for v in param.values():
					assert_iterable(v, (list, tuple, np.ndarray), (float, int), \
						item_test=test, size=2)
				assert isinstance(f"{param}_key", str)
			else:
				assert_iterable(param, (list, tuple, np.ndarray), (float, int), \
					item_test=test, size=2)
		assert_iterable(prf, dict, item_test=lambda f: callable(f) and \
			0 <= f(0.5, 0.5) <= 1)
		if isinstance(prf, dict):
			assert isinstance(prf_key, str)
		
		# Get standard instrument ID and platform ID
		if isinstance(platform, Platform):
			platform_id = platform.id
		elif isinstance(platform, str):
			platform_id = get_standard_platform_id(platform) or \
				platform.strip().lower()
		else:
			platform_id = None
		instrument_id = None if platform is False else \
			get_standard_instrument_id(id, platform=platform_id)
		if instrument_id and not platform_id:
			platform_id = get_instrument_platform(instrument_id)

		# Check against multiple instruments and save instrument ID
		if isinstance(instrument_id, list):
			raise ValueError(f"Multiple instruments found with ID '{id}' - "
				"specify an exact instrument with the 'platform' parameter.")
		elif isinstance(platform_id, list):
			raise ValueError("Multiple platforms found belonging to instrument "
				f"ID '{id}' - specify an exact platform with the 'platform' "
				"parameter.")
		self.id = instrument_id or id.lower().strip()
		
		# Create new platform if identified but doesn't exist
		if isinstance(platform, str):
			if platform_id in AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS:
				platform = Satellite(platform_id)
			elif platform_id in AVAILABLE_AIRCRAFT_PLATFORMS:
				platform = Aircraft(platform_id)
			else:
				platform_meta = dict(instruments={instrument_id: self})
				platform = Platform(platform_id, meta=platform_meta)

		# Save this new Instrument object to Platform object
		instrument_meta = dict()
		if platform:
			if isinstance(platform, Aircraft) and self.id in \
			  AVAILABLE_AIRCRAFT_INSTRUMENTS:
				instrument_meta.update(AVAILABLE_AIRCRAFT_INSTRUMENTS[self.id])
			if not hasattr(platform, 'instruments'):
				setattr(platform, 'instruments', dict())
			elif self.id not in platform.instruments:
				pass
			elif isinstance(platform.instruments[self.id], dict):
				instrument_meta.update(platform.instruments[self.id])
			else:
				instrument_meta.update(vars(platform.instruments[self.id]))
			platform.instruments.update({self.id: self})
			self.platform = platform
		elif self.id in AVAILABLE_SATELLITE_INSTRUMENTS:
			instrument_meta.update(AVAILABLE_SATELLITE_INSTRUMENTS[self.id])
		elif self.id in AVAILABLE_AIRCRAFT_INSTRUMENTS:
			instrument_meta.update(AVAILABLE_AIRCRAFT_INSTRUMENTS[self.id])

		# Update instrument info
		if meta:
			instrument_meta.update(meta)
		for k,v in instrument_meta.items():
			setattr(self, k, v)

		# Save geolocation product
		if geo_product is None:
			geo_product = findattr(self, 'geo_product', None)
		if isinstance(geo_product, dict):
			geo_product = {k:v for k,v in geo_product.items() if v in ([] if \
				available_products is None else available_products)}
			if not geo_product:
				raise ValueError("None of the geolocation products found in "
					"'available_products'")
			if geo_product_key is None:
				geo_product_key = findattr(self, 'geo_product_key', None)
			if geo_product_key is None:
				self.geo_product = geo_product
			else:
				geo_product_key_value = findattr(self, geo_product_key, None)
				if geo_product_key_value is None:
					self.geo_product = geo_product
					self.geo_product_key = geo_product_key
				elif geo_product_key_value in geo_product:
					self.geo_product = geo_product[geo_product_key_value]
				else:
					raise ValueError("The geolocation product at "
						f"{geo_product_key_value} {geo_product_key} not found "
						"in 'available_products'")
		elif geo_product is not None:
			if available_products is None or geo_product not in \
			  available_products:
				raise ValueError(f"{geo_product} not found in "
					"'available_products'")
			self.geo_product = geo_product
		# if geo_product is not None:
		# 	if available_products is None or geo_product not in \
		# 	  available_products:
		# 		raise ValueError("'geo_product' must be in 'available_products'")
		# 	self.geo_product = geo_product
		# # if geo_product is None:
		# # 	geo_product = getattr(self, 'geo_product', None)
		# # if geo_product is not None:
		# # 	msg = "'geo_product' must be in 'available_products'"
		# # 	if not available_products:
		# # 		raise ValueError(msg)
		# # 	self.geo_product = geo_product
		# # 	if isinstance(geo_product, dict):
		# # 		if not any(p in available_products for p in geo_product.values()):
		# # 			raise ValueError(msg)
		# # 		if geo_product_key is not None:
		# # 			self.geo_product_key = geo_product_key
		# # 		set_attr_by_key(self, 'geo_product', change=True, value=False, \
		# # 			silent=True)
		# # 	elif geo_product not in available_products:
		# # 		raise ValueError(msg)
		
		# Function to save attribute from specifications list
		def _set_spec_attr(name, value, key=None, itype=tuple):
			if value is None and hasattr(self, "specifications"):
				value = self.specifications.get(name)
			if value is not None:
				if itype is not None:
					if isinstance(value, dict):
						value = {k: itype(v) if iterable(v) else v for k,v \
							in value.items()}
					elif iterable(value):
						value = itype(value)
				setattr(self, name, value)
				if isinstance(value, dict):
					if key is None:
						key = self.specifications[f"{name}_key"]
					setattr(self, f"{name}_key", key)

		# Save specification values and keys
		_set_spec_attr('swath_width', swath_width, swath_width_key)
		_set_spec_attr('swath_length', swath_length, swath_length_key)
		_set_spec_attr('pixel_offset', pixel_offset, pixel_offset_key)
		_set_spec_attr('pixel_scale', pixel_scale, pixel_scale_key)
		_set_spec_attr('ifov', ifov, ifov_key)
		_set_spec_attr('gsd', gsd, gsd_key)
		_set_spec_attr('prf', prf, prf_key)

		# Set the data directory of the instrument
		if directory is not False:
			self.set_datadir(directory, default=None, warn=False)

		# Set the formatters
		if formatters is not None:
			self.formatters = {k.lower():v for k,v in dict(formatters).items() \
				if k.lower() in PRODUCT_FIELDS}

		# Set the formatters
		if reverse_formatters is not None:
			self.reverse_formatters = {k.lower():v for k,v in \
				dict(reverse_formatters).items() if k.lower() in PRODUCT_FIELDS}

		# Set the iterable filters
		if iter_filters is not None:
			iter_filters = [j for i in (iter_filters if iterable(iter_filters) \
				else [iter_filters]) if (j:=i.lower().strip()) in PRODUCT_FIELDS]
			if iter_filters:
				self.iter_filters = sorted(iter_filters)

		# Initialize all products on the instrument
		if isinstance(available_products, dict):
			self.products = available_products
			if load_product is not None:
				_ = self.load_product(load_product, **kwargs)
		
		# Set state of platform
		# try:
		# 	self.set_state(**kwargs)
		# except:
		# 	pass

	# Magic method for representation output
	def __repr__(self):
		class_path = '.'.join([self.__module__, self.__class__.__qualname__])
		plat_str = ":"+self.platform.id if hasattr(self, 'platform') else ""
		return f"<{class_path}({self.id}{plat_str})>"
	
	# Magic method for string output
	def __str__(self):
		class_name = self.__class__.__name__
		name = getattr(self, 'name', self.id)
		plat_str = ", "+getattr(self.platform, 'name', self.platform.id) if \
			hasattr(self, 'platform') else ""
		return f"{class_name}({name}{plat_str})"

	# Method to check for related objects to instrument instance
	def related_object(self, /, platform=None, product=None, dataset=None, \
	  granule=None, grid=None):
		"""Checks if given object(s) are related to this instrument instance.
		
		Parameters:
			platform: type=Platform, default=None
				- A Platform object to test if parent of instrument.
			product: type=Product, default=None
				- A Product object to test if child of instrument.
			dataset: type=Dataset, default=None
				- A Dataset object to test if child of instrument.
			granule: type=Granule, default=None
				- A Granule object to test if child of instrument.
			grid: type=Grid, default=None
				- A Grid object to test if child of instrument.
		
		Returns:
			- True if all given objects are related objects of this instrument 
			instance.
		"""
		from types import NoneType
		from .platform import Platform
		from .product import Product
		from .data import Dataset, Granule, Grid

		# Check for correct input types
		assert isinstance(platform, (NoneType, Platform))
		assert isinstance(product, (NoneType, Product))
		assert isinstance(dataset, (NoneType, Dataset))
		assert isinstance(granule, (NoneType, Granule))
		assert isinstance(grid, (NoneType, Grid))

		# Check if given platform is related to instrument
		if platform is not None and (not hasattr(self, 'platform') or \
		  self.platform is not self):
			return False

		# Check if given children objects are related to instrument
		for object in [product, dataset, granule, grid]:
			if object is not None and (not hasattr(object, 'instrument') or \
			  object.instrument is not self):
				return False
		
		# Return passed tests
		return True

	# Method to retrieve the relative spectral response function
	def rsr(self, /, band=True, detector=False, combine=None, 
	  dependent='wavelength', reader=None, **kwargs):
		"""Retrieves the relative spectral response function for the instrument.
		
		Parameters:
			band: type=int|str|list|bool, default=True
				- The 1-based index or name/ID (or list of either) of the band 
				or bands to retrieve the RSR functions for.  If True, will 
				retrieve all bands for the instrument.
			detector: type=int|str|list|bool, default=False
				- The 1-based index or name/ID (or list of either) of the 
				detector or detectors of the given band(s) to retrieve the RSR 
				functions for.  If True, will retrieve all detectors for the 
				given band(s); if False, will retrieve all detectors for the 
				given band(s) and average them for each band (effectively giving 
				`combine` a value of True.)
			combine: type=bool, default=None
				- If True, will combine multiple detector RSR functions into an 
				averaged one.
			dependent: type=str, default='wavelength'
				- The dependent variable of the resulting function(s) - either 
				'wavelength' for wavelengths in meters, or 'wavenumber' for 
				wavenumbers in units of meters^(-1).
			reader: type=str, default=None
				- A string representation of the module to use to get the 
				relative spectral response function.  If None, will first search 
				for a RSR_VALUES global variable that is a dictionary of RSR 
				data based on platform, band (and detector if availble); if it 
				is not found, then data files in the 'rsr' directory will be 
				searched for under the platform, band (and detector if availale) 
				subdirectories, before finally progressing through modules 
				listed in the RSR_READER_MODULES variable.
		
		Returns:
			- A scipy BSpline function object with wavelength (or wavenumber) in 
			meters (or 1/m) as the input variable and the relative spectral 
			response as the output value.  For multiple bands or detectors, each 
			spline will be inside a dictionary with values corresponding to the 
			input values for `band` and `detector`.
		"""

		pass

	# Method to set the data directory for instrument
	def set_datadir(self, /, directory=None, default=".", warn=True):
		"""Sets the data directory for this instrument.

		Parameters:
			directory: type=str|pathlib.Path, default=None
				- The data directory for this instrument.  If not given, will 
				look for the environment variable "XPATH" where "X" is replaced 
				with the instrument ID in upper case with only alphanumeric 
				characters.  If this is not found, will use the current working 
				directory.
			default: type=str|pathlib.Path, default="."
				- The default directory to use if `directory` is `None` and no 
				environment variable for the data directory was found.  If 
				`None`, will not set any data directory attribute at this point.
			warn: type=bool, default=True
				- If `True`, will give a warning if `directory` is `None` and no 
				environment variable for the data directory was found.
		"""
		import warnings
		from pathlib import Path
		import os
		import re

		# Get directory from environment variable or current working directory
		if directory is None:
			env = f"{re.sub(r'[^a-zA-Z0-9]', '', self.id).upper()}PATH"
			if env not in os.environ:
				if default is None:
					if warn:
						warnings.warn("\033[38;5;208mEnvironment variable "
							f"({env}) not found.\033[0m", stacklevel=2)
					return
				if warn:
					warnings.warn(f"\033[38;5;208mEnvironment variable ({env}) "
						"not found; using current working directory.\033[0m", \
						stacklevel=2)
			directory = os.getenv(env, default)
		
		# Convert pathlib.Path object to str
		if not isinstance(directory, str):
			directory = str(directory)

		# Resolve path name
		directory = os.path.normpath(os.path.expandvars(os.path.expanduser( \
			directory)))
		
		# Check for existing path
		if not os.path.exists(directory):
			raise ValueError(f"Directory does not exist: {directory}")
		
		# Set data directory attribute
		self.datadir = Path(directory)

	# Method to search for a particular product
	def search_products(self, /, id=None, name=None, level=None, structure=None, 
	  spatial_resolution=None, temporal_resolution=None, inclusive=True, 
	  **kwargs):
		"""Filters list of products by searching their attributes.

		Parameters:
			id: type=str|re|def, default=None
				- A term to search within products' IDs.  Terms separated with a 
				space will each be tested, and if any of them are found, it will 
				be considered a match.
			name: type=str|re|def, default=None
				- A term to search within products' names.  Terms separated with 
				a space will each be tested, and all of them must be found in 
				order for it to be considered a match.
			level: type=int|str|re|def, default=None
				- The product level to match products' levels.  If this argument 
				is an integer and the saved level for a product is a string, 
				will compare the number against the first full number in the 
				string.  An array of possible values can be given.
			structure: type=str|re|def, default=None
				- A term to search within products' structure designations.  
				Terms separated with a space will each be tested, and all of 
				them must be found in order for it to be considered a match.
			spatial_resolution: type=int|float|str|re|def, default=None
				- A numerical or string value to match products' spatial 
				resolutions, which is generally given in meters (e.g. for 
				swaths) or degrees (e.g. for CMG grids).  An array of possible 
				values can be given.
			temporal_resolution: type=dateutil.relativedelta.relativedelta|re|
			  function, default=None
				- A dateutil.relativedelta.relativedelta object to match 
				products' temporal resolutions.  Must match exactly.
			inclusive: type=bool, default=True
				- If True, will include products that do not have an attribute 
				specified that is being searched.  Set to False to remove such 
				products from the output.

		External modules:
			- dateutil -- https://dateutil.readthedocs.io/
			- numpy -- https://numpy.org/

		Returns:
			- A dictionary of product IDs and metadata for each product that 
			matches the search query.  Note that for each of the parameters 
			listed, a regex pattern (re.Pattern object) or a function with 
			boolean output may alternatively be given.
		"""
		import re
		from dateutil.relativedelta import relativedelta
		import numpy as np
		from .ancillary import iterable

		# Function to search for a match depending on input type
		def _search(search_value, values, key=None, operator=any):
			if search_value is None:
				return True
			if isinstance(values, dict):
				value = values.get(key, None)
				if value is None:
					return bool(inclusive)
			else:
				value = values
			if isinstance(search_value, str) and len(search_value.split()) > 1:
				search_value = search_value.split()
			if iterable(search_value):
				return operator(_search(s, value) for s in search_value)
			if isinstance(search_value, str):
				return search_value.lower() in str(value).lower()
			elif isinstance(search_value, relativedelta):
				return search_value == value
			elif np.isscalar(search_value):
				return any(np.isclose(search_value, float(re.search(r'\d+', \
					v).group(0)) if isinstance(v, str) else v, rtol=1e-2) for v \
					in (value if iterable(value) else [value]))
			elif isinstance(search_value, re.Pattern):
				return search_value.search(str(value), flags=re.I)
			else:
				return search_value(value.lower() if isinstance(value, str) \
					else value)

		# Get all products
		products = getattr(self, 'products', dict())

		# Select matching key and values
		products = {k:v for k,v in products.items() if \
			_search(id, k) and \
			_search(name, v, 'name', all) and \
			_search(level, v, 'level') and \
			_search(structure, v, 'structure', all) and \
			_search(spatial_resolution, v, 'spatial_resolution') and \
			_search(temporal_resolution, v, 'temporal_resolution')}

		# Return search results
		return products

	# Method to initialize a product of the instrument
	def load_product(self, /, product_id, reload=False, **kwargs):
		"""Initializes a Product isntance of the Instrument object.
	
		Parameters:
			product_id: type=str|list|bool
				- The standardized name (ID) or list of IDs of the product.  If 
				True, will initialize all products on the instrument.
			reload: type=bool, default=False
				- If `False`, will recreate/reload the product only if not yet 
				created/loaded; if `True`, will always recreate/reload the 
				product even if it already exists.
		
		Returns:
			- An instance or list of instances of the product class that were 
			loaded.
		"""
		from .product import get_product_class
		from .ancillary import iterable, getattr_recursive

		# Initialize products attribute if not set
		if not hasattr(self, 'products'):
			self.products = dict()
		
		# Check if multiple products requested
		isiterable = product_id is True or iterable(product_id)
		
		# Get list of product IDs to initialize
		if product_id is True:
			product_ids = [*self.products]
		elif isiterable:
			product_ids = list(product_id)
		else:
			product_ids = [product_id]
		
		# Create instance of product
		products = []
		for i,product_id in enumerate(product_ids):
			if product_id in product_ids[:i]:
				products.append(products[product_ids.index(product_id)])
			elif not reload and product_id in self.loaded_products():
				products.append(self.products[product_id])
			else:
				platform_id = getattr_recursive(self, 'platform.id', False)
				ProductClass = get_product_class(product_id, \
					instrument=self.id, platform=platform_id)
				products.append(ProductClass(product_id, instrument=self, \
					**kwargs))

		# Return product instance(s)
		return products if isiterable else products[0]

	# Method to return a dictionary of all loaded products
	def loaded_products(self):
		"""Filters the available products for those that have been loaded.
	
		Returns:
			- A dictionary of loaded products with the product names as the keys.
		"""
		from .product import Product
		
		# Return dictionary of loaded products
		return {name:prod for name,prod in self.products.items() if \
			isinstance(prod, Product)}
	
	# # Method to get the latitude and longitude of the instrument's geolocation 
	# # product
	# def get_latlon(self, /, **kwargs):
	# 	"""Retrieves the latitude and longitude arrays from the instrument's 
	# 	geolocation product.

	# 	Parameters:
	# 		**kwargs:
	# 			- Keyword arguments that will be passed to the geolocation 
	# 			product's `get_latlon` method.
	# 			- If the instrument does not have a `geo_product` attribute, or 
	# 			it is not loaded, this method will raise an error.

	# 	Returns:
	# 		- A tuple of two numpy ndarrays (latitudes, longitudes) with shape 
	# 		(...), where ... represents the dimensions of the geolocation grid.
	# 	"""

	# 	# Get geolocation product
	# 	geo_product = getattr(self, 'geo_product', None)
	# 	if geo_product is None:
	# 		raise ValueError("Instrument does not have a 'geo_product' "
	# 			"attribute set.")
	# 	if isinstance(geo_product, dict):
	# 		geo_product_key = getattr(self, 'geo_product_key', None)
	# 		if geo_product_key is None:
	# 			raise ValueError("Instrument has multiple possible "
	# 				"'geo_product' values; set 'geo_product_key' to the "
	# 				"attribute name/location of the key value to use.")
	# 		geo_product = geo_product.get(geo_product_key, None)
	# 		if geo_product is None:
	# 			raise ValueError(f"Could not find key '{geo_product_key}' in "
	# 				"'geo_product' dictionary with a valid value.")
	# 	product = self.load_product(geo_product)

	# 	# 

	# Method to set platform state information (position, velocity, time)
	def set_state(self, /, dataset=None, line=None, strict=False, **kwargs):
		"""Sets the platform's state information (position, velocity, and time).
	
		Parameters:
			dataset: type=Dataset, default=None
				- The dataset for which to set the platform state information.  
				If `None`, the geolocation dataset will be searched (if one was 
				specified in the instrument initialization) using the extra 
				keyword arguments to identify the file of interest (these will 
				be passed to the `product.find_files` method).
			line: type=int, default=None
				- The along-track index for which to set the platform state 
				information.  If `None`, will instead set the state for the center of the  
				scan/frame.
			strict: type=bool, default=False
				- If `True`, will raise an error if any of the standardized 
				variables specified in the metadata are not found in the dataset.
			**kwargs:
				- 

		External modules:
			- numpy -- https://numpy.org/
		"""
		from types import NoneType
		import datetime as dt
		from datetime import timezone as tz
		import numpy as np
		# from .platform import lla2xyz, uvw2enu
		from .data import Dataset, sort_dims  #, broadcast_prep
		from .ancillary import iterable, findattr  #, lon_convert

		# Check inputs
		assert isinstance(dataset, (NoneType, Dataset))
		assert isinstance(line, (NoneType, int, np.integer))

		# Settings
		standardized_variables = [			# angles in degrees
			'latitude',						# 2D
			'longitude',
			'platform_latitude',			# 1D (can differ if pointing off-nadir)
			'platform_longitude',
			'x',
			'y',
			'platform_x',
			'platform_y',
			'undulation',					# geoid height
			'altitude',						# ellipsoidal/geodetic
			'orthometric_altitude',
			'elevation',					# ellipsoidal/geodetic
			'orthometric_elevation',
			'height',						# AGL
			'range',
			'velocity',
			'course',
			'heading',
			'pitch',
			'roll',
			'sensor_azimuth',
			'sensor_zenith',
			'solar_azimuth',
			'solar_zenith',
			'datetime',						# ISO format or seconds since Unix epoch or datetime.datetime object or numpy.datetime64 object
			'date',							# ISO format or ordinal days (day 1 = Jan. 1, 1 A.D.) or datetime.date object or numpy.datetime64 object
			'time',							# ISO format or seconds since midnight or datetime.time object
		]

		""" ####################################################
		Still to do:
		- Automate course calculation if not provided, from lat/lon values
		- Reference either sensor azimth/zenith or pitch/roll to pick the 
		correct nadir point of the scene (right now it is just the middle pixel)
		#################################################### """

		# Check for linked platform
		if not hasattr(self, 'platform'):
			raise ValueError("The instrument has not linked platform in order "
				"to set its state.")

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
		
		# Get label names for standardized variables
		labels = {var:label for var in standardized_variables if \
			(label:=findattr(dataset, name:=f'{var}_name', None, group=[None, \
			'labels'])) is not None}
		
		# Get slice for center of scene for the given line
		def _get_center_slice(var, mean=True, nmin=None, vect=False):
			# Identify dimensions of variable
			dims = sort_dims(dataset.read(var=var, dim=True))
			ids = [d['id'] if 'id' in d else None for d in dims]
			ialong_track = ids.index('along_track') if 'along_track' in ids \
				else None
			if line is not None:
				raise ValueError("Could not find along-track dimension.")
			iacross_track = ids.index('across_track') if 'across_track' in ids \
				else None
			if len(dims) > (3 if vect else 2):
				raise ValueError(f"Variable {var} has too many dimensions.")
			extra_dims = sorted([d for i,d in enumerate(dims) if i not in \
				[ialong_track, iacross_track]], key=lambda d: d['size'])
			ivect = dims.index(extra_dims[0]) if vect and extra_dims else None
			if ivect is not None and dims[ivect]['size'] > 3:
				if ialong_track is None or iacross_track is None:
					ivect = None
				else:
					raise ValueError(f"Variable {var} has too many vector "
						"components.")

			# Get slice for center of scene or for given line
			shape = tuple(d['size'] for d in dims)
			s = ()
			for i,size in enumerate(shape):
				if i == ivect:
					s += (slice(),)
				elif line is not None and i == ialong_track:
					if nmin is not None:
						s += (slice(max(0, line-nmin), line+nmin+1),)
					if mean:
						s += (slice(line, line+1),)
					else:
						s += (slice(max(0, line-1), line+2, 2-(line == 0 or \
							line >= size-1)),)
				else:
					if nmin is not None:
						s += (slice((size-nmin)//2, (size+nmin+1)//2),)
					elif mean:
						s += (slice((size-1)//2, (size+2)//2),)
					else:
						s += (slice((size-2)//2, (size+3)//2, 1+(size % 2)),)

			# Return slice
			return s
			
		# Function to format variable data scalar or array with given function
		def _format_var_data(data, func):
			assert callable(func)
			if not iterable(data):
				data = func(data)
			else:
				isma = np.ma.isMA(data)
				try:
					data = np.ma.masked_invalid(data)
				except TypeError:
					data = np.ma.array(data)
				try:
					idata = func(data)
					if iterable(idata):
						data = idata
					else:
						raise ValueError
				except:
					try:
						data = np.ma.masked_invalid(a:=[np.ma.masked if \
							np.ma.is_masked(d) else func(d) for d in \
							data.flat]).reshape(data.shape)
					except TypeError:
						data = np.ma.array(a).reshape(data.shape)
				if not isma and not np.ma.is_masked(data):
					data = np.ma.getdata(data)
			return data
		
		# Function to extract and format a variable slice
		def _extract_format_var_slice(var, mean=True, nmin=None, otype=False, 
		  func=None, vect=False):
			# Get the custom label and converter if provided
			label = labels[var]
			if iterable(label):
				label,converter = label
			else:
				converter = None
			
			# Check that variable exists in the dataset
			if label not in dataset.variables:
				if strict:
					raise ValueError(f"Variable '{label}' not found in dataset.")
				else:
					return None
			
			# Extract data slice and apply converter
			s = _get_center_slice(label, mean=mean, nmin=nmin, vect=vect)
			data = dataset.extract(label, s)
			if converter is not None:
				data = _format_var_data(data, converter)
			
			# Apply additional converter function if necessary
			try:
				example = np.ma.masked_invalid(data).compressed()[0].item()
			except TypeError:
				example = np.ma.array(data).compressed()[0].item()
			if otype is True or otype is not False and not isinstance(example, \
			  otype):
				data = _format_var_data(data, func)
			
			# Return mean of data if requested, else the formatted data
			if mean:
				try:
					return np.ma.masked_invalid(data).mean()
				except TypeError:
					try:
						return np.ma.array(data).mean()
					except:
						dmin = np.ma.getdata(data).min()
						return (np.ma.array(data)-dmin).mean()+dmin
			else:
				return data

		# Get location data
		state_kwargs = dict()
		if 'platform_latitude' in labels and 'platform_longitude' in labels:
			lat = _extract_format_var_slice('platform_latitude', \
				otype=(int, float, np.number), func=float)
			lon = _extract_format_var_slice('platform_longitude', \
				otype=(int, float, np.number), func=float)
			# lat = dataset.extract(labels['platform_latitude'], s_pt).mean()
			# lon = dataset.extract(labels['platform_longitude'], s_pt).mean()
			if lat is not None and lon is not None:
				state_kwargs.update(lat=lat, lon=lon)
			lats = _extract_format_var_slice('platform_latitude', mean=False, \
				otype=(int, float, np.number), func=float)
			lons = _extract_format_var_slice('platform_longitude', mean=False, \
				otype=(int, float, np.number), func=float)
			# lats = dataset.extract(labels['platform_latitude'], s_ray)
			# lons = dataset.extract(labels['platform_longitude'], s_ray)
		elif 'platform_x' in labels and 'platform_y' in labels:
			x = _extract_format_var_slice('platform_x', \
				otype=(int, float, np.number), func=float)
			y = _extract_format_var_slice('platform_y', \
				otype=(int, float, np.number), func=float)
			if x is not None and y is not None:
				state_kwargs.update(lat=y, lon=x)
			lons = _extract_format_var_slice('platform_x', mean=False, \
				otype=(int, float, np.number), func=float)
			lats = _extract_format_var_slice('platform_y', mean=False, \
				otype=(int, float, np.number), func=float)
		elif 'latitude' in labels and 'longitude' in labels:
			lat = _extract_format_var_slice('latitude', \
				otype=(int, float, np.number), func=float)
			lon = _extract_format_var_slice('longitude', \
				otype=(int, float, np.number), func=float)
			if lat is not None and lon is not None:
				state_kwargs.update(lat=lat, lon=lon)
			lats = _extract_format_var_slice('latitude', mean=False, \
				otype=(int, float, np.number), func=float)
			lons = _extract_format_var_slice('longitude', mean=False, \
				otype=(int, float, np.number), func=float)
		elif 'x' in labels and 'y' in labels:
			x = _extract_format_var_slice('x', otype=(int, float, np.number), \
				func=float)
			y = _extract_format_var_slice('y', otype=(int, float, np.number), \
				func=float)
			if x is not None and y is not None:
				state_kwargs.update(lat=y, lon=x)
			lons = _extract_format_var_slice('x', mean=False, \
				otype=(int, float, np.number), func=float)
			lats = _extract_format_var_slice('y', mean=False, \
				otype=(int, float, np.number), func=float)
		
		# Get distance data
		if 'undulation' in labels:
			und = _extract_format_var_slice('undulation', \
				otype=(int, float, np.number), func=float)
			if und is not None:
				state_kwargs.update(und=und)
		if 'altitude' in labels:
			alt = _extract_format_var_slice('altitude', \
				otype=(int, float, np.number), func=float)
			if alt is not None:
				state_kwargs.update(alt=alt)
		if 'orthometric_altitude' in labels:
			ortho_alt = _extract_format_var_slice('orthometric_altitude', \
				otype=(int, float, np.number), func=float)
			if ortho_alt is not None:
				state_kwargs.update(ortho_alt=ortho_alt)
		if 'elevation' in labels:
			elev = _extract_format_var_slice('elevation', \
				otype=(int, float, np.number), func=float)
			if elev is not None:
				state_kwargs.update(elev=elev)
		if 'orthometric_elevation' in labels:
			ortho_elev = _extract_format_var_slice('orthometric_elevation', \
				otype=(int, float, np.number), func=float)
			if ortho_elev is not None:
				state_kwargs.update(ortho_elev=ortho_elev)
		if 'height' in labels:
			h = _extract_format_var_slice('height', \
				otype=(int, float, np.number), func=float)
			if h is not None:
				state_kwargs.update(h=h)
		if 'range' in labels:
			r = _extract_format_var_slice('range', \
				otype=(int, float, np.number), func=float)
			if r is not None:
				state_kwargs.update(r=r)

		# Get velocity/directional data
		if 'velocity' in labels:
			vel = _extract_format_var_slice('velocity', \
				otype=(int, float, np.number), func=float, vect=True)
			if vel is not None:
				state_kwargs.update(vel=vel)
		if 'course' in labels:
			course = _extract_format_var_slice('course', \
				otype=(int, float, np.number), func=float)
			if course is not None:
				state_kwargs.update(course=course)
		if 'heading' in labels:
			head = _extract_format_var_slice('heading', \
				otype=(int, float, np.number), func=float)
			if head is not None:
				state_kwargs.update(head=head)
		if 'pitch' in labels:
			pitch = _extract_format_var_slice('pitch', \
				otype=(int, float, np.number), func=float)
			if pitch is not None:
				state_kwargs.update(pitch=pitch)
		if 'roll' in labels:
			roll = _extract_format_var_slice('roll', \
				otype=(int, float, np.number), func=float)
			if roll is not None:
				state_kwargs.update(roll=roll)
		if 'sensor_azimuth' in labels:
			senazi = _extract_format_var_slice('sensor_azimuth', \
				otype=(int, float, np.number), func=float)
			if senazi is not None:
				state_kwargs.update(solazi=senazi)
		if 'sensor_zenith' in labels:
			senzen = _extract_format_var_slice('sensor_zenith', \
				otype=(int, float, np.number), func=float)
			if senzen is not None:
				state_kwargs.update(solzen=senzen)
		if 'solar_azimuth' in labels:
			solazi = _extract_format_var_slice('solar_azimuth', \
				otype=(int, float, np.number), func=float)
			if solazi is not None:
				state_kwargs.update(solazi=solazi)
		if 'solar_zenith' in labels:
			solzen = _extract_format_var_slice('solar_zenith', \
				otype=(int, float, np.number), func=float)
			if solzen is not None:
				state_kwargs.update(solzen=solzen)

		# Get time data
		if 'timestamp' in labels:
			def func(t):
				if isinstance(t, dt.date):
					return dt.datetime.combine(t, dt.time())
				elif isinstance(t, np.datetime64):
					return t.astype(dt.datetime)
				elif isinstance(t, str):
					return dt.datetime.fromisoformat(t)
				else:
					return dt.datetime.fromtimestamp(t, tz=tz.utc)
			timestamp = _extract_format_var_slice('timestamp', \
				otype=dt.datetime, func=func)
			if timestamp is not None:
				state_kwargs.update(time=timestamp)
		elif 'date' in labels and 'time' in labels:
			def func(d):
				if isinstance(d, dt.datetime):
					return d.date()
				elif isinstance(d, dt.date):
					return d
				elif isinstance(d, np.datetime64):
					return d.astype(dt.datetime).date()
				elif isinstance(d, str):
					return dt.date.fromisoformat(d)
				else:
					return dt.date.fromordinal(d)
			date = _extract_format_var_slice('date', mean=False, nmin=1, \
				otype=True, func=func)
			def func(t):
				if isinstance(t, str):
					return dt.time.fromisoformat(t)
				else:
					return (dt.datetime(1,1,1)+dt.timedelta(seconds= \
						float(t))).time()
			time = _extract_format_var_slice('time', mean=False, nmin=1, \
				otype=dt.time, func=func)
			if not iterable(date) and not iterable(time):
				try:
					timestamp = dt.datetime.combine(date, time)
				except:
					timestamp = None
			elif not iterable(date):
				try:
					timestamp = _format_var_data(time, lambda t: \
						dt.datetime.combine(date, t))
				except:
					timestamp = None
			elif not iterable(time):
				try:
					timestamp = _format_var_data(date, lambda d: \
						dt.datetime.combine(d, time))
				except:
					timestamp = None
			else:
				try:
					isma = np.ma.isMA(date) or np.ma.isMA(time)
					try:
						date = np.ma.masked_invalid(date)
					except:
						date = np.ma.array(date)
					try:
						time = np.ma.masked_invalid(time)
					except:
						time = np.ma.array(time)
					b = np.broadcast(date, time)
					timestamp = np.ma.masked_all(b.shape, dt.datetime)
					timestamp.flat = [np.ma.masked if np.ma.is_masked(d) or \
						np.ma.is_masked(t) else dt.datetime.combine(d,t) for \
						d,t in b]
					if not isma and not np.ma.is_masked(timestamp):
						timestamp = np.ma.getdata(timestamp)
				except:
					timestamp = None
				if iterable(timestamp):
					tmin = np.ma.getdata(timestamp).min()
					timestamp = (np.ma.array(timestamp)-tmin).mean()+tmin
				if timestamp is not None:
					state_kwargs.update(time=timestamp)

		# Get CRS
		crs = findattr(dataset, 'crs', None)
		if crs is not None:
			state_kwargs.update(crs=crs)
		
		# Set platform state
		self.platform.set_state(**state_kwargs)

	# Method to get the geolocation corner coordinates of a swath dataset
	def corners(self, /, dataset=None, extend=False, coordinate_order=None, 
	  **kwargs):
		"""Gets the corner geolocation coordinates of a given dataset.
	
		Parameters:
			dataset: type=Dataset, default=None
				- The dataset from which to get the geolocation data (either 
				latitude/longitude data or x/y data).  If `None`, the 
				geolocation dataset will be searched (if one was specified in 
				the instrument initialization) using the extra keyword arguments 
				to identify the file of interest (these will be passed to the 
				`product.find_files` method).
			extend: type=bool, default=False
				- If `True`, will extend the returned corner data coordinates to 
				the outer edges of the outer pixels instead of the pixel centers.
			coordinate_order: type=bool, default=None
				- Set to "ji" to order y-axis data first, then x-axis data; and 
				set to "ij" for the reverse.  If `None`, will select it 
				automatically depending on if latitude/longitude values are used 
				(ji) or x/y values are used (ij).  The result will be saved to 
				the 'coordinate_order' attribute in the resulting dataset.
			**kwargs:
				- 

		External modules:
			- numpy -- https://numpy.org/

		Returns:
			- A numpy ndarray of shape (4, 2) with the corner coordinates as 
			either (latitude, longitude) or (x,y) pairs, depending on the 
			available variables in the dataset.
		"""
		import numpy as np
		from .ancillary import findattr
		
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
			raise RuntimeError("This routine applies only to datasets with a "
				"swath structure.")
		
		# Settings
		standardized_variables = [
			'latitude',
			'longitude',
			'x',
			'y',
		]

		# Check for extend argument
		if extend:
			raise NotImplementedError("Extend option not yet implemented.")
		
		# Get label names for standardized variables
		labels = {var:label for var in standardized_variables if \
			(label:=findattr(dataset, name:=f'{var}_name', None, group=[None, \
			'labels'])) is not None}
		
		# Function to get the array corners
		def _get_var_corners(var):
			# Construct corners data for variable
			data = dataset.extract(var, np.s_[0,:1])
			isma = np.ma.is_masked(data)
			for s in [np.s_[:1,-1], np.s_[-1,-1:], np.s_[-1:,0]]:
				side = dataset.extract(var, s)
				isma |= np.ma.is_masked(side)
				concat = np.ma.concatenate if isma else np.concatenate
				data = concat((data, side))

			# Return corners data
			return data
		
		# Set coordinate order
		if coordinate_order is not None:
			dataset.coordinate_order = coordinate_order
		
		# Return corner coordinates as list of (lat, lon) or (x, y)
		if 'latitude' in labels and 'longitude' in labels:
			lats = _get_var_corners(labels['latitude'])
			lons = _get_var_corners(labels['longitude'])
			if dataset.coordinate_order is None:
				dataset.coordinate_order = 'ji'
			cstack = np.ma.column_stack if np.ma.isMA(lats) or \
				np.ma.isMA(lons) else np.column_stack
			if dataset.coordinate_order == 'ij':
				return cstack((lons, lats))
			else:
				return cstack((lats, lons))
		elif 'x' in labels and 'y' in labels:
			xs = _get_var_corners(labels['x'])
			ys = _get_var_corners(labels['y'])
			if dataset.coordinate_order is None:
				dataset.coordinate_order = 'ij'
			cstack = np.ma.column_stack if np.ma.isMA(xs) or np.ma.isMA(ys) \
				else np.column_stack
			if dataset.coordinate_order == 'ij':
				return cstack((xs, ys))
			else:
				return cstack((ys, xs))
		else:
			raise ValueError("Could not find latitude/longitude or x/y "
				"variables in the dataset to get corner coordinates.")
	
	# Method to get the geolocation boundaries of a swath dataset
	def border(self, /, dataset=None, extend=False, coordinate_order=None, 
	  **kwargs):
		"""Gets the border geolocation coordinates of a given dataset.
	
		Parameters:
			dataset: type=Dataset, default=None
				- The dataset from which to get the geolocation data (either 
				latitude/longitude data or x/y data).  If `None`, the 
				geolocation dataset will be searched (if one was specified in 
				the instrument initialization) using the extra keyword arguments 
				to identify the file of interest (these will be passed to the 
				`product.find_files` method).
			extend: type=bool, default=False
				- If `True`, will extend the returned border data coordinates to 
				the outer edges of the outer pixels instead of the pixel centers.
			coordinate_order: type=bool, default=None
				- Set to "ji" to order y-axis data first, then x-axis data; and 
				set to "ij" for the reverse.  If `None`, will select it 
				automatically depending on if latitude/longitude values are used 
				(ji) or x/y values are used (ij).  The result will be saved to 
				the 'coordinate_order' attribute in the resulting dataset.
			**kwargs:
				- 

		External modules:
			- numpy -- https://numpy.org/
			- shapely -- https://shapely.readthedocs.io/

		Returns:
			- A Shapely Polygon object representing the border coordinates as 
			either (latitude, longitude) or (x,y) pairs, depending on the 
			available variables in the dataset.
		"""
		import numpy as np
		from shapely.geometry import Polygon
		from .ancillary import findattr
		
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
			raise RuntimeError("This routine applies only to datasets with a "
				"swath structure.")
		
		# Settings
		standardized_variables = [
			'latitude',
			'longitude',
			'x',
			'y',
		]

		# Check for extend argument
		if extend:
			raise NotImplementedError("Extend option not yet implemented.")
		
		# Get label names for standardized variables
		labels = {var:label for var in standardized_variables if \
			(label:=findattr(dataset, name:=f'{var}_name', None, group=[None, \
			'labels'])) is not None}
		
		# Function to get the array borders
		def _get_var_border(var):
			# Construct border data for variable
			data = dataset.extract(var, np.s_[0,:-1])
			isma = np.ma.isMA(data)
			for s in [np.s_[:-1,-1], np.s_[-1,:0:-1], np.s_[:0:-1,0]]:
				side = dataset.extract(var, s)
				isma |= np.ma.isMA(side)
				concat = np.ma.concatenate if isma else np.concatenate
				data = concat((data, side))

			# Return border data
			return data
		
		# Set coordinate order
		if coordinate_order is not None:
			dataset.coordinate_order = coordinate_order
		
		# Get border coordinates as list of (lat, lon) or (x, y)
		if 'latitude' in labels and 'longitude' in labels:
			lats = _get_var_border(labels['latitude'])
			lons = _get_var_border(labels['longitude'])
			if dataset.coordinate_order is None:
				dataset.coordinate_order = 'ji'
			if dataset.coordinate_order == 'ij':
				points = np.ma.column_stack((lons, lats))
			else:
				points = np.ma.column_stack((lats, lons))
		elif 'x' in labels and 'y' in labels:
			xs = _get_var_border(labels['x'])
			ys = _get_var_border(labels['y'])
			if dataset.coordinate_order is None:
				dataset.coordinate_order = 'ij'
			if dataset.coordinate_order == 'ij':
				points = np.ma.column_stack((xs, ys))
			else:
				points = np.ma.column_stack((ys, xs))
		else:
			raise ValueError("Could not find latitude/longitude or x/y "
				"variables in the dataset to get border coordinates.")
		
		# Return valid border coordinates as polygon object
		return Polygon(points[~points.mask.any(axis=1),:])
	
	# Method to construct pixel outlines for simulated scan
	def simulated_pixel_outlines(self, /, **kwargs):
		"""Constructs pixel outlines for a simulated scan or frame of the 
		instrument based on its specifications and platform position and 
		attitude.

		Parameters:
			**kwargs:
				- Keyword arguments that will be used in place of attributes of 
				the instrument or its platform, or to specify keys to use for 
				attributes that are dictionaries.
				- For instance, if the instrument's `ifov` attribute is a 
				dictionary with keys corresponding to different spatial 
				resolutions, and the keyword argument 'spatial_resolution' is 
				given, its value will be used to look up the appropriate `ifov` 
				value in the `ifov` dictionary.
				- Use the platform's `set_state` method to set the required 
				platform attributes (`latitude`, `longitude`, `altitude` and 
				`heading`) if not already set and not provided here.
				- The following instrument attributes are required:
					- Either `scan_width` (for whiskbroom scanners) or 
					`frame_width` (for pushbroom scanners)
					- `swath_width`
					- Either `ifov` or `pixel_scale` or both - if one is 
					missing, it is assumed to be equal to the other
					- `pixel_offset` (optional; assumed to be 0 if not given)

		Returns:
			- A tuple of two numpy ndarrays (latitudes, longitudes) with shape 
			(..., 4), where the last new dimension represents the four corners 
			of each pixel.
		"""
		import numpy as np
		from pyproj import CRS
		from .platform import lla2xyz, xyz2lla, uvw2ecef
		from .ancillary import iterable, getattr_recursive, findattr

		# Function to get attribute value, searching recursively and extracting 
		# value from dictionary if necessary
		def _getattr(attr, default=None):
			data = kwargs[attr] if attr in kwargs else getattr_recursive(self, \
				attr, None)
			if not isinstance(data, dict):
				return data
			key_name = findattr(self, f"{attr.split('.')[-1]}_key", None)
			if key_name is None or key_name not in kwargs:
				return default
			return data.get(kwargs[key_name], default)

		# Get necessary platform attributes
		lat0 = _getattr('platform.latitude')
		lon0 = _getattr('platform.longitude')
		alt0 = _getattr('platform.altitude')
		head = _getattr('platform.heading')
		if lat0 is None or lon0 is None or alt0 is None or head is None:
			raise ValueError("Platform latitude, longitude, altitude, and "
				"heading must be set to simulate pixel outlines.")

		# Get necessary instrument attributes
		if isinstance(self, WhiskbroomScanner):
			swath_length = _getattr('scan_width')
		elif isinstance(self, PushbroomScanner):
			swath_length = _getattr('frame_width')
		else:
			swath_length = _getattr('scan_width', _getattr('frame_width'))
		swath_width = _getattr('swath_width')
		ifov = _getattr('ifov')
		pixel_scale = _getattr('pixel_scale', ifov)
		if ifov is None:
			ifov = pixel_scale
		pixel_offset = _getattr('pixel_offset', 0)
		if swath_length is None or swath_width is None or ifov is None or \
		  pixel_scale is None or pixel_offset is None:
			first_word = "Scan" if isinstance(self, WhiskbroomScanner) else \
				"Frame" if isinstance(self, PushbroomScanner) else "Scan/frame"
			raise ValueError(f"{first_word} dimensions, and IFOV and/or pixel "
				"scale must be set to simulate pixel outlines.")
		if not iterable(ifov):
			ifov = (ifov,)*2
		if not iterable(pixel_scale):
			pixel_scale = (pixel_scale,)*2
		if not iterable(pixel_offset):
			pixel_offset = (pixel_offset,)*2

		# Get angles of pixel centers in along-track (i) and across-track (j) 
		# directions
		swath_dims = np.array([swath_length, swath_width])
		first_pix_dist = (pixel_scale*(swath_dims-1))/2
		i0,j0 = np.meshgrid(*[np.linspace(-first_pix_dist[i], \
			first_pix_dist[i], swath_dims[i])+pixel_offset[i]*pixel_scale[i] \
			for i in range(2)], indexing='ij')
		
		# Get angles of pixel corners
		for ni,nj in [(-1,-1), (1,-1), (1,1), (-1,1)]:
			i = i0+ni*ifov[0]/2
			j = j0+nj*ifov[1]/2
			try:
				ipixels = np.concatenate((ipixels, i[...,None]), axis=-1)
				jpixels = np.concatenate((jpixels, j[...,None]), axis=-1)
			except:
				ipixels = i[...,None]
				jpixels = j[...,None]

		# Get ENU unit vectors in direction of each pixel corner (UVW=ENU) by 
		# rotating scan angles by heading and flipping z-axis
		heading = np.radians(head)
		alpha = np.pi-ipixels
		beta = np.pi-jpixels
		sa = np.sin(alpha)
		sb = np.sin(beta)
		upixels = np.sin(heading)*sa - np.cos(heading)*sb
		vpixels = np.cos(heading)*sa + np.sin(heading)*sb
		wpixels = -np.cos(alpha)*np.cos(beta)
		
		# Convert LLA position and ENU view angles to ECEF coordinates
		x0,y0,z0 = lla2xyz(lon0, lat0, alt0)
		upixels,vpixels,wpixels = uvw2ecef(upixels, vpixels, wpixels, lat0, lon0)

		# Intersect the ray for each pixel corner with the WGS84 ellipsoid
		wgs84 = CRS("EPSG:4326")
		ellipsoid = wgs84.ellipsoid
		a = ellipsoid.semi_major_metre
		b = ellipsoid.semi_minor_metre
		c0 = (upixels/a)**2 + (vpixels/a)**2 + (wpixels/b)**2
		c1 = 2*(x0*upixels/a**2 + y0*vpixels/a**2 + z0*wpixels/b**2)
		c2 = (x0/a)**2 + (y0/a)**2 + (z0/b)**2 - 1
		coef1 = -c1/(coef2:=2*c0)
		coef2 = np.ma.sqrt(c1**2-4*c0*c2)/coef2
		d = np.minimum(np.ma.masked_less_equal(coef1 + coef2, 0), \
			np.ma.masked_less_equal(coef1 - coef2, 0))
		if not np.ma.is_masked(d):
			d = np.ma.getdata(d)
		xpixels = x0+d*upixels
		ypixels = y0+d*vpixels
		zpixels = z0+d*wpixels

		# Convert pixel corner coordinates from ECEF to LLA
		lons,lats,alts = xyz2lla(xpixels, ypixels, zpixels)

		# Return latitudes and longitudes of pixel corners
		return (lats, lons)
################################## Instrument ##################################

############################## WhiskbroomScanner ##############################
class WhiskbroomScanner(Instrument):
	"""Defines a whiskbroom instrument object on an Earth Science Mission 
	platform.
	
	Functions:
		__init__ -- Initializes a whiskbroom instrument object on an Earth 
			Science Mission platform.
	
	Returns:
		- An object defining a whiskbroom instrument on an Earth Science Mission 
		platform, including metadata such available products.
	"""
	
	# Constructor method
	def __init__(self, /, id, *, scan_width=None, scan_width_key=None, **kwargs):
		"""Defines an object simulating an orbiting whiskbrook scanning 
		spaceborne instrument.
	
		Parameters:
			id: type=str
				- The standardized name (ID) of the instrument or one of its 
				alternative IDs or names.  If not found, will still create an 
				Instrument object with no geometry, meta information, products, 
				or platform.
			scan_width: type=int|dict, default=None
				- The width in pixels/detectors of the instrument's scan.  If 
				multiple values are possible due to different product/variable 
				configurations, enter a dictionary with keys corresponding to 
				different possible configuration values (e.g. spatial 
				resolutions) and set 'scan_width_key' to the attribute 
				name/location of this configuration parameter.
			scan_width_key: type=str, default=None
				- The attribute name/location of the key values in the 
				'scan_width' dictionary.  For instance, if the configuration 
				values that comprise the 'scan_width' keys represent the spatial 
				resolution, 'scan_width_key' should be set to 
				'spatial_resolution' if a given object has such an attribute.  
				If the object does not have such an attribute saved in its 
				metadata, parent objects will be searched recursively all the 
				way up to the Platform object until it is located.  If a 
				recursive search is not desired, prepend the class name to the 
				attribute name (e.g. 'product.spatial_resolution' for the 
				spatial resolution given in the Product object.)
		"""
		from .ancillary import iterable, assert_iterable

		# Check input formats
		assert_iterable(scan_width, dict, int)
		if scan_width is not None:
			assert all(w > 0 for w in scan_width.values()) if \
				isinstance(scan_width, dict) else scan_width > 0
		if isinstance(scan_width, dict):
			assert isinstance(scan_width_key, str)
		
		# Call parent constructor
		super().__init__(id, **kwargs)

		# Function to save attribute from specifications list
		def _set_spec_attr(name, value, key=None, itype=tuple):
			if value is None and hasattr(self, "specifications"):
				value = self.specifications.get(name)
			if value is not None:
				if itype is not None:
					if isinstance(value, dict):
						value = {k: itype(v) if iterable(v) else v for k,v \
							in value.items()}
					elif iterable(value):
						value = tuple(value)
				setattr(self, name, value)
				if isinstance(value, dict):
					if key is None:
						key = self.specifications[f"{name}_key"]
					setattr(self, f"{name}_key", key)

		# Save scan width
		_set_spec_attr('scan_width', scan_width, scan_width_key)
		# self.scan_width = scan_width
		# if isinstance(scan_width, dict):
		# 	self.scan_width_key = scan_width_key
############################## WhiskbroomScanner ##############################

############################### PushbroomScanner ###############################
class PushbroomScanner(Instrument):
	"""Defines a pushbroom instrument object on an Earth Science Mission 
	platform.
	
	Functions:
		__init__ -- Initializes a pushbroom instrument object on an Earth 
			Science Mission platform.
	
	Returns:
		- An object defining a pushbroom instrument on an Earth Science Mission 
		platform, including metadata such available products.
	"""

	# Constructor method
	def __init__(self, /, id, *, frame_width=None, frame_width_key=None, **kwargs):
		"""Defines an object simulating an orbiting whiskbrook scanning 
		spaceborne instrument.
	
		Parameters:
			id: type=str
				- The standardized name (ID) of the instrument or one of its 
				alternative IDs or names.  If not found, will still create an 
				Instrument object with no geometry, meta information, products, 
				or platform.
			frame_width: type=int|dict, default=None
				- The along-track width in pixels/detectors of a single frame.  
				If multiple values are possible due to different 
				product/variable configurations, enter a dictionary with keys 
				corresponding to different possible configuration values (e.g. 
				spatial resolutions) and set `frame_width_key` to the attribute 
				name/location of this configuration parameter.
			frame_width_key: type=str, default=None
				- The attribute name/location of the key values in the 
				`frame_width` dictionary.  For instance, if the configuration 
				values that comprise the `frame_width` keys represent the 
				spatial resolution, `frame_width_key` should be set to 
				'spatial_resolution' if a given object has such an attribute.  
				If the object does not have such an attribute saved in its 
				metadata, parent objects will be searched recursively all the 
				way up to the Platform object until it is located.  If a 
				recursive search is not desired, prepend the class name to the 
				attribute name (e.g. 'product.spatial_resolution' for the 
				spatial resolution given in the Product object.)
		"""
		pass
############################### PushbroomScanner ###############################


#--------------------------------- FUNCTIONS ---------------------------------#

###################### (LOCAL) get_available_instruments ######################
def _get_available_instruments(available_platform_instruments, platforms=False):
	"""Gets the instrument ID of all available instruments from a dictionary of 
	available platforms and instruments.

	Parameters:
		available_platform_instruments: type=dict
			- A dictionary of available platforms and instruments.
		platforms: type=bool, default=False
			- If `True`, will include the platform(s) that the instrument is on.
	
	Returns:
		- A list of standardized instrument IDs of available instruments, or if 
		`platforms` is `True`, a list of two-element tuples where the first item 
		is the instrument ID and the second item is the platform(s) that the 
		instrument is on.
	"""

	# Get unique list of instruments (using website as a unique identifier)
	results = []
	results_platform = []
	for platform_id,platform_data in available_platform_instruments.items():
		if 'instruments' not in platform_data:
			continue
		for instrument_id,instrument_data in \
		  platform_data['instruments'].items():
			website = instrument_data.get('website', None)
			result = (instrument_id, website)
			if result not in results or not website:
				results.append(result)
				results_platform.append(platform_id)
			elif result in results and website:
				i = results.index(result)
				if isinstance(results_platform[i], str):
					results_platform[i] = [results_platform[i], platform_id]
				else:
					results_platform[i].append(platform_id)
	
	# Extract and sort instrument IDs and platforms
	instruments = list(zip(*results))[0] if results else []
	if platforms:
		instruments = zip(instruments, results_platform)
	instruments = sorted(instruments)

	# Return instruments (and platforms if requested)
	return instruments
###################### (LOCAL) get_available_instruments ######################

########################## get_available_instruments ##########################
def get_available_instruments(platforms=False, satellites=False, aircraft=False):
	"""Gets the instrument ID of all available instruments for the given 
	platform(s).

	Parameters:
		platforms: type=bool, default=False
			- If `True`, will include the platform(s) that the instrument is on.
		satellites: type=bool, default=False
			- Set to `True` to only include instruments on satellites.
		aircraft: type=bool, default=False
			- Set to `True` to only include instruments on aircraft.
	
	Returns:
		- A list of standardized instrument IDs of available instruments, or if 
		`platforms` is `True`, a list of two-element tuples where the first item 
		is the instrument ID and the second item is the platform(s) that the 
		instrument is on.
	"""
	from .config import AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS, \
		AVAILABLE_AIRCRAFT_INSTRUMENTS

	# Check input arguments
	if not satellites and not aircraft:
		satellites = True
		aircraft = True
	
	# Return list of instrument IDs from satellite and/or aircraft platforms
	sat = _get_available_instruments(AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS, \
		platforms=platforms) if satellites else []
	air = sorted(AVAILABLE_AIRCRAFT_INSTRUMENTS.keys()) if aircraft else []
	if platforms:
		air = [(inst, None) for inst in air]
	return sorted(sat+air)
########################## get_available_instruments ##########################

###################### (LOCAL) get_standard_instrument_id ######################
def _get_standard_instrument_id(instrument, available_platform_instruments=dict(), 
  platform=None):
	"""Gets the standardized name (ID) of the specified instrument from a 
	dictionary of available platforms and instruments.

	Parameters:
		instrument: type=str
			- The ID or name of the instrument.
		available_platform_instruments: type=dict, default={}
			- A dictionary of available platforms and instruments within which 
			to search for the ID of the instrument.  Not used if `platform` is a 
			Platform object.
		platform: type=str|Platform, default=None
			- The Platform object, or ID or name of the platform on which the 
			instrument is located.  If `None`, will search all platforms in 
			`available_platform_instruments`.
	
	Returns:
		- The standardized name (ID) of the instrument, or a list of IDs if 
		multiple found, or `None` if not found.
	"""
	from .platform import Platform, _get_standard_platform_id

	# Format instrument for comparison
	instrument = instrument.strip().lower()

	# Get platform ID or list of possible platforms
	if isinstance(platform, Platform):
		platforms = {platform.id: vars(platform)}
	elif isinstance(platform, str):
		platforms = {p: available_platform_instruments[p]} if \
			(p:=_get_standard_platform_id(platform, \
			available_platform_instruments)) else dict()
	else:
		platforms = available_platform_instruments
	
	# Get list of IDs and names that match input
	ids = []
	names = []
	for platform_id,platform_data in platforms.items():
		if 'instruments' not in platform_data:
			continue
		for instrument_id,instrument_data in platform_data['instruments'].items():
			instrument_ids = [instrument_id]
			if not isinstance(instrument_data, dict):
				instrument_data = vars(instrument_data)
			if 'alternative_ids' in instrument_data:
				instrument_ids.extend(instrument_data['alternative_ids'])
			if instrument in instrument_ids:
				ids.append(instrument_id)
			instrument_names = [instrument_data.get('name', "").lower()]
			if 'alternative_names' in instrument_data:
				instrument_names.extend([name.lower() for name in \
					instrument_data['alternative_names']])
			if instrument in instrument_names:
				names.append(instrument_id)
	ids = sorted(set(ids)) if ids else sorted(set(names))

	# Return standard instrument ID (or list if multiple)
	return ids if len(ids) > 1 else ids[0] if ids else None
###################### (LOCAL) get_standard_instrument_id ######################

########################## get_standard_instrument_id ##########################
def get_standard_instrument_id(instrument, platform=None, satellite=False, 
  aircraft=False):
	"""Gets the standardized name (ID) of a specified instrument for the given 
	platform(s).

	Parameters:
		instrument: type=str
			- The ID or name of the instrument.
		platform: type=str, default=None
			- The ID or name of the platform on which the instrument is located.  
			If `None`, will search all platforms.
		satellite: type=bool, default=False
			- Set to `True` to specify that the `platform` is a satellite.
		aircraft: type=bool, default=False
			- Set to `True` to specify that the `platform` is an aircraft.
	
	Returns:
		- The standardized name (ID) of the instrument, or a list of IDs if 
		multiple found, or `None` if not found.
	"""
	from .config import AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS, \
		AVAILABLE_AIRCRAFT_PLATFORMS, AVAILABLE_AIRCRAFT_INSTRUMENTS
	
	# Check input arguments
	if not satellite and not aircraft:
		satellite = True
		aircraft = True
	
	# Get standard instrument IDs from satellite and aircraft platforms
	if satellite:
		sat = _get_standard_instrument_id(instrument, \
			AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS, platform=platform)
	if aircraft:
		if platform is not None and platform.strip().lower() not in \
		  AVAILABLE_AIRCRAFT_PLATFORMS:
			air = None
		else:
			air = _get_standard_instrument_id(instrument, {None: {'instruments': \
				AVAILABLE_AIRCRAFT_INSTRUMENTS}})

	# Return standard IDs from satellite and/or aircraft platforms
	sat = [] if not satellite or not sat else sat if isinstance(sat[0], list) \
		else [sat]
	air = [] if not aircraft or not air else air if isinstance(air[0], list) \
		else [air]
	ids = sorted(set(sat+air))
	return ids if len(ids) > 1 else ids[0] if ids else None
########################## get_standard_instrument_id ##########################

############################# get_instrument_class #############################
def get_instrument_class(instrument, platform=None):
	"""Gets the instrument class for the given instrument ID and platform ID.

	Parameters:
		instrument: type=str
			- The ID or name of the instrument.
		platform: type=str|bool, default=None
			- The ID or name of the platform on which the instrument is located.  
			If `False`, will ensure that a Platform object is not created.
	
	Returns:
		- The class of the given instrument and platform, or the base Instrument 
		class if not found.
	"""
	# from pathlib import Path
	# import pkgutil
	import sys
	import importlib
	import inspect
	
	# Get standard instrument ID
	instrument_id = platform is not False and get_standard_instrument_id( \
		instrument, platform=platform) or instrument.strip().lower()
	
	# Find and import the instrument-specific module
	# path = Path(__file__).resolve().parent / "instruments"
	# modules = [mod.name for mod in pkgutil.iter_modules([str(path)])]
	if instrument_id in sys.modules and \
	  sys.modules[instrument_id].__package__ == 'esm.instruments':
		mod = sys.modules[instrument_id]
	else:
		try:
			mod = importlib.import_module("."+instrument_id, "esm.instruments")
		except:
			return Instrument

	# Find the instrument-specific class
	classes = {k.lower():v for k,v in inspect.getmembers(mod, inspect.isclass)}
	cls = classes.get(instrument_id, Instrument)

	# Check for instrument-specific class that requires a platform argument
	if cls is not Instrument and platform is False:
		signature = inspect.signature(cls.__init__)
		if 'platform' in signature.parameters and \
		  signature.parameters['platform'].default is inspect.Parameter.empty:
			return Instrument
	
	# Return the instrument class
	return cls
############################# get_instrument_class #############################

############################### load_instrument ###############################
def load_instrument(id, platform=None, **kwargs):
	"""Create either an object of an instrument-specific class if available, or 
	a generic Instrument object otherwise.

	Parameters:
		id: type=str
			- The ID or name of the instrument.  Will check for satellites first 
			and then for aircraft before defaulting to a Platform object.
		platform: type=str
			- The ID or name of the platform.  If None, will search all 
			platforms.  If `False`, will ensure that a Platform object is not 
			created.

	Returns:
		- Either an Instrument object or an instrument-specific class object if 
		available.
	"""

	# Get the instrument class
	InstrumentClass = get_instrument_class(id, platform=platform)

	# Return the instrument object
	if InstrumentClass is Instrument:
		return Instrument(id, platform=platform, **kwargs)
	else:
		return InstrumentClass(platform=platform, **kwargs)
############################### load_instrument ###############################

########################### get_instrument_platform ###########################
def get_instrument_platform(instrument):
	"""Gets the satellite IDs of the specified instrument.

	Parameters:
		instrument: type=str
			- The ID or name of the instrument.
	
	Returns:
		- The standardized name (ID) of the satellite, or a list of IDs if 
		multiple found, or `None` if not found.
	"""
	from .config import AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS

	# Get list of platforms and websites for instrument
	results = []
	for platform_id,platform_data in \
	  AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS.items():
		if 'instruments' not in platform_data:
			continue
		for instrument_id,instrument_data in platform_data['instruments'].items():
			instrument_ids = [instrument_id]
			if 'alternative_ids' in instrument_data:
				instrument_ids.extend(instrument_data['alternative_ids'])
			if instrument not in instrument_ids:
				continue
			website = instrument_data.get('website', None)
			results.append((platform_id, website))
	if not results:
		return None
	
	# Group platforms by website and sort
	websites = sorted({w for p,w in results})
	if len(websites) > 1:
		platforms = [[]]*len(websites)
		for platform_id,website in results:
			platforms[websites.index(website)].append(platform_id)
		for p in platforms:
			p.sort()
		platforms.sort(key=lambda p: (-len(p), p))
	else:
		platforms = sorted(list(zip(*results))[0])
	
	# Return standardized platform IDs
	return platforms if len(platforms) > 1 else platforms[0]
########################### get_instrument_platform ###########################

########################### (LOCAL) set_attr_by_key ###########################
# def _set_attr_by_key(obj, attr_name, change=False, value=False, 
#   empty=False, silent=False):
# 	"""Sets selected attributes from parent attribute with selected keys.

# 	Parameters:
# 	obj: type=object
# 		The object to which the selected attribute(s) will be saved.
# 	attr_name: type=str
# 		The attribute name that will be searched for in parent objects.
# 	change: type=bool, default=False
# 		If True, will not save any attributes that are not a subset of the 
# 		original attribute found in a parent object.
# 	value: type=bool, default=False
# 		If True, will only save final values, i.e. no dictionaries with multiple 
# 		possible values.
# 	empty: type=bool, default=False
# 		If True and 'change' is False, will set any subset of attributes that 
# 		result in an empty dictionary to None in the given object.
# 	silent: type=bool, default=False
# 		If True, will supress any exceptions raised, such as when an attribute 
# 		is not found.
# 	"""
# 	from .ancillary import iterable, getattr_recursive, findattr

# 	# Get attribute value and parent object of attribute
# 	try:
# 		attr_val,attr_parent = findattr(obj, attr_name, parent=True)
# 	except:
# 		if silent:
# 			return
# 		else:
# 			raise

# 	# Check if attribute value is a dictionary
# 	if isinstance(attr_val, dict):
# 		# Get associate attribute key name
# 		attr_key_name = f"{attr_name}_key"
# 		try:
# 			attr_key = getattr(attr_parent, attr_key_name)
# 		except:
# 			if silent:
# 				return
# 			else:
# 				raise
		
# 		# Get attribute key value(s)
# 		if '.' in attr_key:
# 			i = attr_key.index('.')
# 			attr_key = (attr_key[:i], attr_key[i+1:])
# 		else:
# 			attr_key = (attr_key, None)
# 		try:
# 			attr_key_val = findattr(obj, attr_key[0])
# 			if attr_key[1] is not None:
# 				attr_key_val = getattr_recursive(attr_key_val, attr_key[1])
# 		except:
# 			if silent:
# 				return
# 			else:
# 				raise
		
# 		# Check if iterable attribute keys
# 		if iterable(attr_key_val):
# 			# Check if no change in dictionary items
# 			if change and len(attr_val) > 1 and all(k in attr_key_val for k in \
# 			  attr_val):
# 				return
			
# 			# Save selected attribute value(s)
# 			iattr_val = {k:v for k,v in attr_val.items() if k in \
# 				attr_key_val}
# 			if not value and len(iattr_val) >= 2:
# 				setattr(obj, attr_name, iattr_val)
# 				setattr(obj, attr_key_name, attr_key)
# 			elif len(iattr_val) == 1:
# 				setattr(obj, attr_name, list(iattr_val.values())[0])
# 			elif empty and not iattr_val:
# 				setattr(obj, attr_name, None)
		
# 		# Save selected attribute value
# 		elif attr_key_val in attr_val:
# 			setattr(obj, attr_name, attr_val[attr_key_val])
		
# 		# Save empty attribute
# 		elif empty:
# 			setattr(obj, attr_name, None)

# 	# Save attribute to current object
# 	elif not change:
# 		setattr(obj, attr_name, attr_val)
########################### (LOCAL) set_attr_by_key ###########################
