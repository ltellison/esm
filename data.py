"""Data
Module for creating and operating on classes of Earth Science Mission data 
files.

Author:
	Luke Ellison

Version:
	0.1

History:
	v0.1, 09-Dec-2025, Luke Ellison: Module compiled.

Global Variables:
	RASTER_PRODUCT_READER_MODULES -- List of modules used for reading raster 
		files.
	TABLE_PRODUCT_READER_MODULES -- List of modules used for reading tabular 
		files.
	PRODUCT_READER_MODULES -- List of modules used for reading data files 
		(combined RASTER_PRODUCT_READER_MODULES and 
		TABLE_PRODUCT_READER_MODULES).

Classes:
	Dataset -- Defines a dataset object for an Earth Science Mission product.
	Granule -- Defines a granule object for an Earth Science Mission dataset.
	Grid -- Defines a grid object for an Earth Science Mission dataset.

Functions:
	decompress -- Decompresses files with common compression formats (zip, gzip, 
		xz).
	get_path_name -- Extracts the name for a given dataset object's path.
	sort_dims -- Orders a dictionary of dimensions for a variable into a list 
		sorted by index.
	broadcast_prep -- Prepares an array to be broadcasted to a given shape, 
		aligned at a given axis.
	full_slice -- Fills in a partial slice object with slices for unspecified 
		dimensions.
	slice_to_array -- Converts a slice object to a set of arrays.
	ma_pad -- Pads an array (adds masked array functionality to numpy's pad 
		function.)
	grid_interp -- Interpolating or extrapolating structured data in multiple 
		dimensions at regular or irregular locations.
	planck -- Computes the blackbody radiance for a given wavelength and 
		temperature, or radiance or wavelength if given the other two parameters.
"""

#------------------------------ GLOBAL VARIABLES ------------------------------#

# The modules available for reading ESM data files
RASTER_PRODUCT_READER_MODULES = ['rioxarray', 'xarray', 'netcdf4', 'gdal', \
	'h5py', 'h5netcdf', 'pyhdf', 'pygrib']
TABLE_PRODUCT_READER_MODULES = ['geopandas', 'pandas', 'polars']
PRODUCT_READER_MODULES = RASTER_PRODUCT_READER_MODULES + \
	TABLE_PRODUCT_READER_MODULES


#---------------------------------- CLASSES ----------------------------------#

################################### Dataset ###################################
class Dataset:
	"""Defines a dataset object for an Earth Science Mission product.
	
	Functions:
		__init__ -- Initializes a dataset object of an Earth Science Mission 
			product.
		__repr__ -- Returns the official string represenation of the dataset.
		__str__ -- Returns the string represenation of the dataset.
		__enter__ -- The context manager's opening method of a `with` block.
		__exit__ -- The context manager's opening method of a `with` block.
		__contains__ -- Tests if a variable or attribute or dimension is 
			contained within the dataset.
		cousin_dataset -- Finds a cousin dataset to the current one under the 
			same instrument.
		download -- Downloads the `earthaccess` granule associated with this 
			dataset.
		set_reader -- Sets the reader module explicitly without checking file 
			type.
		open -- Opens the file using a designated module.
		close -- Closes the file and deletes the handle.
		variables -- Gets a list of all variable names in dataset.
		get_filename_attr -- Gets the formatted results from a file name match.
		read -- Reads a variable, attribute or dimension from a data file.
		get_shape -- Gets the data shape of the specified variable of this 
			dataset.
		dim_index -- Finds the dimension index from a dimension name or ID.
		extract -- Extracts data from file or file dataset object, allowing for 
			custom 
		masking and scaling functions.
		set_geo -- Retrieves the geolocation data from the instrument's 
			geolocation product and saves it as attributes to this dataset.
		set_state -- Sets the platform's state information (position, velocity, 
			and time).
		coordinate_order -- Sets the order of coordinates to either 'ij' or 'ji'.
		corners -- Gets the corner geolocation coordinates of a given dataset.
		border -- Gets the border geolocation coordinates for this dataset.
		coincident -- Finds coincident datasets from other instruments within a 
			given time.
		overlapping_pixels -- Identifies overlapping pixels between scans/frames 
			of swath.
	
	Returns:
		- An object defining a dataset for an Earth Science Mission product.
	"""

	# Constructor method
	def __init__(self, /, file, product=None, instrument=None, platform=None, 
	  download=None, **kwargs):
		"""Initializes a dataset object of an Earth Science Mission product.
		
		Parameters:
			file: type=str|pathlib.Path|earthaccess.DataGranule
				- The dataset file to read.
			product: type=Product|str|bool, default=None
				- The product associated with the datasets.  If a `Product` 
				object, will use its ID.  If a string, will use the standardized 
				product ID to create a new `Instrument` object.  If `False`, 
				will ensure that no product is set.  If `None`, will search for 
				the product ID among all available products and create a new 
				`Product` object if one and only one product is found.
			instrument: type=Instrument|str|bool, default=None
				- The instrument associated with the datasets' product.  If an 
				`Instrument` object, will use its ID.  If a string, will use the 
				standardized instrument ID to create a new `Instrument` object.  
				If `False`, will ensure that no instrument is set (even if the 
				product ID is found).  If `None`, will search for the instrument 
				ID among all available instruments and create a new `Instrument` 
				object if one and only one instrument is found with the product 
				ID.
			platform: type=Platform|str|bool, default=None
				- The platform on which the dataset's product's instrument is 
				located.  If a `Platform` object, will use its ID.  If a string, 
				will use the standardized platform ID to create a new `Platform` 
				object.  If `False`, will ensure that no platform is set (even 
				if the instrument ID is found).  If `None`, will search for the 
				instrument ID among all available platforms and create a new 
				`Platform` object if one and only one platform is found with the 
				instrument ID.
			download: type=bool, default=None
				- A boolean determining if a given `earthaccess.DataGranule` 
				object will be downloaded before processing, versus only reading 
				it into memory.  If given, this overrides the related product's 
				`download` attribute.
			**kwargs:
				- 
		"""
		from types import NoneType
		import os
		import re
		from pathlib import Path
		import datetime as dt
		import earthaccess as ea
		from .platform import Platform, get_standard_platform_id
		from .instrument import Instrument, get_available_instruments, \
			get_instrument_class
		from .product import Product, query_filename
		from .ancillary import iterable, breadth_first_search, findattr, \
			set_attr_by_key, set_nadir_point

		# Validate parameters
		assert isinstance(file, (str, Path, ea.DataGranule))
		assert isinstance(product, (NoneType, Product, str, bool))
		assert isinstance(instrument, (NoneType, Instrument, str, bool))
		assert isinstance(platform, (NoneType, Platform, str, bool))
		assert isinstance(download, (NoneType, bool))

		# Save file name
		if isinstance(file, ea.DataGranule):
			self.file = query_filename(file)
		else:
			file = Path(os.path.normpath(os.path.expandvars(os.path.expanduser( \
				str(file)))))
			self.file = file.name

		# Search for matching product filename to get product object
		if product is None:
			# Function to get product object or ID from filename match
			def _match_filename(instrument):
				for p,v in getattr(instrument, 'products', dict()).items():
					loaded = not isinstance(v, dict)
					filename_pattern = v.filename_pattern if loaded else \
						v['filename_pattern']
					if re.fullmatch(filename_pattern, self.file):
						return v if loaded else p
				return None
			
			# Search for matching product when instrument is given
			if instrument not in [None, False]:
				if not isinstance(instrument, Instrument):
					InstrumentClass = get_instrument_class(instrument, \
						platform=platform)
					instrument = InstrumentClass(platform=platform, **kwargs)
				product = _match_filename(instrument)

			# Search for matching product when instrument not given
			else:
				if platform:
					platform_ids = get_standard_platform_id(platform)
				for i,ps in get_available_instruments(platforms=True):
					if platform and ps not in platform_ids:
						continue
					InstrumentClass = get_instrument_class(i, platform=ps if \
						isinstance(ps, str) or ps is None else ps[0])
					if InstrumentClass is Instrument:
						continue
					for p in ([ps] if isinstance(ps, str) else ps):
						i = InstrumentClass(platform=p, **kwargs)
						product = _match_filename(i)
						if product:
							if instrument:
								raise ValueError("Multiple products with ID "
									f"{id} found - either specify the "
									"'instrument' argument (and 'platform' if "
									"necessary) or set it to False.")
							instrument = i
		
		# Get product object from inputs
		if product not in [None, False]:
			# Save the product 
			if not isinstance(product, Product):
				product = Product(product, instrument=instrument, \
					platform=platform, **kwargs)
			self.product = product
			if hasattr(product, 'instrument'):
				self.instrument = self.product.instrument
				if hasattr(self.instrument, 'platform'):
					self.platform = self.instrument.platform

			# Get formatted file name attributes and save to dataset object
			attrs = self.product.get_filename_attrs(self.file)
			if attrs is None:
				raise ValueError("File does not match file name template for product.")
			for k,v in attrs.items():
				if not hasattr(self, k):
					setattr(self, k, v)
			
			# Save time range to dataset object if applicable
			res = getattr(self.product, 'temporal_resolution', None)
			for tvar in ('timestamp', 'date', 'time'):
				tmin = attrs.get(f"start_{tvar}", attrs.get(tvar, None))
				tmax = attrs.get(f"end_{tvar}", None)
				if tvar == 'timestamp':
					if tmax is None and tmin is not None and 'end_time' in attrs:
						tmax = dt.datetime.combine(tmin.date(), attrs['end_time'])
						if tmax < tmin:
							tmax += dt.timedelta(days=1)
					elif tmin is None and tmax is not None and 'start_time' in \
					  attrs:
						tmin = dt.datetime.combine(tmax.date(), \
							attrs['start_time'])
						if tmax < tmin:
							tmin -= dt.timedelta(days=1)
				if tmin is not None and tmax is not None:
					setattr(self, f"{tvar}_range", dict(min=tmin, max=tmax, \
						incl=True))
				elif res is not None:
					if tmin is not None:
						if tvar == 'time':
							if (dt.datetime(1,1,1)+res) < dt.datetime(1,1,2):
								tmax = (dt.datetime.combine(dt.date(1,1,1), \
									tmin) + res).time()
						else:
							tmax = tmin+res
							if tvar == 'date' and isinstance(tmax, dt.datetime):
								tmax = None
						if tmax is not None:
							setattr(self, f"{tvar}_range", dict(min=tmin, \
								max=tmax, incl='[)'))
					elif tmax is not None:
						if tvar == 'time':
							if (dt.datetime(1,1,1)+res) < dt.datetime(1,1,2):
								tmin = (dt.datetime.combine(dt.date(1,1,1), \
									tmax) - res).time()
						else:
							tmin = tmax-res
							if tvar == 'date' and isinstance(tmin, dt.datetime):
								tmin = None
						if tmin is not None:
							setattr(self, f"{tvar}_range", dict(min=tmin, \
								max=tmax, incl='(]'))

			# Initialize datasets attribute if not set
			if not hasattr(self.product, 'datasets'):
				self.product.datasets = dict()
			if not hasattr(self.product, 'dataset_keys'):
				self.product.dataset_keys = []
		
			# Save datasets to dynamic dictionary using filters
			ordered_filters = ['version', 'subversion', ['flightid', \
				'flightno', 'flightline'], ['location', ('lat','lon'), \
				('x','y')], ['tile', ('h','v')], ['timestamp', \
				'start_timestamp', 'date', 'start_date', 'time', 'start_time', \
				'end_timestamp', 'end_date', 'end_time']]
			def _get_first_dict_tree_value(d):
				for d2 in d.values():
					if isinstance(d2, dict) and d2:
						d3 = _get_first_dict_tree_value(d2)
						if d3 is not None:
							return d3
					else:
						return d2
				# return _get_first_dict_tree_value(d[list(d.keys())[0]]) if \
				# 	isinstance(d, dict) else d
			def _iter_dict_levels(d, level):
				ds = [d]
				for _ in range(level):
					for _ in range(len(ds)):
						ds.extend(ds.pop(0).values())
				return ds
			level = self.product.datasets
			parent = None
			ilevel = 0
			for i,filt in enumerate(ordered_filters):
				# Check for filter in file name
				filts = filt if iterable(filt) else [filt]
				for filt in filts:
					if isinstance(filt, tuple) and set(filt).issubset(attrs) \
					  or filt in attrs:
						break
					filt = None
				if not filt:
					continue

				# Skip to last filter if no datasets saved yet
				if not self.product.dataset_keys and i < len(ordered_filters)-1:
					continue

				# Save first dataset with the last category
				elif not self.product.dataset_keys:
					parent = level
					self.product.dataset_keys.append(filt)
				
				# Progress level for created filter category (i.e. multiple values)	
				elif filt in self.product.dataset_keys:
					parent = level
					attr = tuple(attrs[f] for f in filt) if isinstance(filt, \
						tuple) else attrs[filt]
					if attr not in level:
						level[attr] = dict()
					level = level[attr]
					ilevel += 1
					continue

				# Alter categories if new info found
				else:
					ds0 = _get_first_dict_tree_value( \
						self.product.datasets)
					attr0 = tuple(getattr(ds0, f) for f in filt) if \
						isinstance(filt, tuple) else getattr(ds0, filt)
					attr = tuple(attrs[f] for f in filt) if isinstance(filt, \
						tuple) else attrs[filt]
					if attr0 != attr:
						self.product.dataset_keys = \
							self.product.dataset_keys[:ilevel] + [filt] + \
							self.product.dataset_keys[ilevel:]
						if not ilevel:
							self.product.datasets = {attr0: \
								self.product.datasets}
							level = self.product.datasets
						else:
							for d in _iter_dict_levels(self.product.datasets, \
							  ilevel-1):
								for k,v in d.items():
									d[k] = {attr0: v}
							ifilt = self.product.dataset_keys[ilevel-1]
							iattr = tuple(attrs[f] for f in ifilt) if \
								isinstance(ifilt, tuple) else attrs[ifilt]
							level = parent[iattr]
						parent = level
						level[attr] = dict()
						level = level[attr]
						ilevel += 1
			
			# Set value of filter
			parent[attrs[filt]] = self

		# Get file path
		ispath = not isinstance(file, ea.DataGranule)
		if ispath:
			if not file.is_absolute():
				datadir = getattr(self.product, 'datadir', None) if \
					hasattr(self, 'product') else None
				if datadir:
					file = breadth_first_search(file, datadir, timeout=200) or \
						file
			assert file.exists()
		self.path = file
		if isinstance(file, ea.DataGranule):
			if download is None and hasattr(self, 'product'):
				download = self.product.download
			if download:
				self.path = file = self.download(**kwargs)

		# Open file
		self.open(**kwargs)

		# Set geolocation product
		set_attr_by_key(self, 'geo_product', change=True, value=False, \
			silent=True)

		# Set special dimensions list
		if 'swath' in (structure:=findattr(self, 'structure', "").lower()):
			self.SPECIAL_DIMENSIONS = Granule.GRANULE_SPECIAL_DIMENSIONS
		elif 'grid' in structure:
			self.SPECIAL_DIMENSIONS = Grid.GRID_SPECIAL_DIMENSIONS

		# Set platform state
		if hasattr(self, 'platform') and getattr(self.product, 'structure', \
		  None) == 'swath':
			self.set_state(**kwargs)

		# Set nadir point in terms of pixel indices
		set_nadir_point(self)

	# Magic method for representation output
	def __repr__(self):
		"""Returns the official string represenation of the dataset.

		Returns:
			- The official string represenation of the dataset.
		"""
		class_path = '.'.join([self.__module__, self.__class__.__qualname__])
		return f"<{class_path}({self.path})>"
	
	# Magic method for string output
	def __str__(self):
		"""Returns the string represenation of the dataset.

		Returns:
			- The string represenation of the dataset.
		"""
		class_name = self.__class__.__name__
		return f"{class_name}({self.file})"

	# Magic method for context manager protocol (enter a with block)
	def __enter__(self):
		"""The context manager's opening method of a `with` block.

		Returns:
			- The file handle of the Dataset object.
		"""
		return getattr(self, 'handle', self.open(getattr(self, 'reader', None)))

	# Magic method for context manager protocol (exit a with block)
	def __exit__(self, /, etype, eval, etb):
		"""The context manager's closing method of a `with` block.
		"""
		self.close()

	# Magic method for the 'in' command
	def __contains__(self, /, item):
		"""Tests if a variable or attribute or dimension is contained within the 
		dataset.

		Parameters:
			item: type=str
				- A variable, attribute or dimension name or path.
		
		Returns:
			- A boolean value representing if the item is found in the dataset 
			as either a variable, an attribute or a dimension.
		"""
		return item in self.variables or \
			item in get_path_name(self.variables) or \
			item in (attrs:=self.read(attr=True)) or \
			item in get_path_name(attrs) or \
			any([item in (attrs:=self.read(var=v, attr=True)) or item in \
				get_path_name(attrs) for v in self.variables]) or \
			item in self.read(dim=True)
	
	# Method to get a cousin dataset to this dataset for a given product
	def cousin_dataset(self, /, product, **kwargs):
		"""Finds a cousin dataset to the current one under the same instrument.

		Parameters:
			product: type=Product|str
				- The Product object or product ID for which to find the cousin 
				dataset.
		
		Returns:
			- A reference to the loaded cousin dataset of the specified product 
			under the same instrument as the current dataset.
		"""
		from .product import Product

		# Get cousin product
		if not hasattr(self, 'product'):
			raise AttributeError("No product class has been associated with "
				"this dataset instance, so no cousin product can be found.")
		if isinstance(product, Product):
			if product.id == self.product.id:
				raise ValueError("Product is the same as this dataset's product.")
			cousin_prod = product
		else:
			if product.upper() == self.product.id.upper():
				raise ValueError("Product is the same as this dataset's product.")
			if not hasattr(self, 'instrument'):
				raise AttributeError("No instrument class has been associated "
					"with this dataset's product instance, so no cousin "
					"product can be found.")
			cousin_prod = self.instrument.load_product(product, **kwargs)
		
		# Match file to file name format and get groups
		mdict = self.product.get_filename_attrs(self.file)
		if mdict is None:
			raise RuntimeError("Could not match this dataset's file name to its "
				"product's file name format specification.")

		# Find cousin product's file
		if 'product' in mdict:
			del mdict['product']
		if 'processing_timestamp' in mdict:
			del mdict['processing_timestamp']
		if 'ext' in mdict:
			del mdict['ext']
		kwargs_cousin = mdict | kwargs
		for loop in range(4):
			try:
				if loop == 0:
					cousin_file,_ = next(cousin_prod.find_files(**kwargs_cousin))
					break
				elif loop == 1 and cousin_prod.query:
					cousin_file = next(cousin_prod.query_data(**kwargs_cousin))
					break
				elif loop == 2:
					del kwargs_cousin['version']
					cousin_file,_ = next(cousin_prod.find_files(**kwargs_cousin))
					break
				elif loop == 3 and cousin_prod.query:
					cousin_file = next(cousin_prod.query_data(**kwargs_cousin))
					break
			except:
				pass
		else:
			return None

		# Load the cousin dataset and return it
		return cousin_prod.load_dataset(cousin_file, **kwargs)
	
	# Method to download Earthdata granule
	def download(self, /, path=None, **kwargs):
		"""Downloads the `earthaccess` granule associated with this dataset.
		
		Parameters:
			path: type=str|pathlib.Path, default=None
				- The path where the granule file will be downloaded to.
			**kwargs:
				- Additional keyword arguments for the following functions:
					- esm.product.download_granule: path, overwrite
					- earthaccess.download: provider, threads, show_progress, 
					credentials_endpoint, pqdm_kwargs
		
		External Modules:
			- earthaccess -- https://earthaccess.readthedocs.io/
		
		Returns:
			- A list of downloaded granule paths.
		"""
		from pathlib import Path
		import earthaccess as ea

		# Validate inputs
		if not isinstance(self.path, ea.DataGranule):
			raise TypeError("The 'path' attribute must be of type " \
				"`earthaccess.DataGranule`.")
		elif path is None and not hasattr(self, 'product'):
			raise ValueError("'path' must be included if no associated product " \
				"exists.")
		if path is not None:
			path = Path(path)

		# Download granule from product object
		if hasattr(self, 'product'):
			return self.product.download_granule(self.path, path=path, **kwargs)
		
		# Download granule using static path variable
		else:
			path = path.absolute()
			ea.download(self.path, local_path=path, **kwargs)
			return path

	# Method to set the reader module
	def set_reader(self, /, reader, **kwargs):
		"""Sets the reader module explicitly without checking file type.  If the 
		currently set reader is different from the given reader and a file 
		handler already exists, the file will be closed, and the file will be 
		reopened with the new reader resulting in a new handle object.
		
		Parameters:
			reader: type=str, default=None
				- A string representation of the module to use to open the file.
		"""

		# Format reader and check if supported or already set
		reader = str(reader).lower().strip()
		assert reader in PRODUCT_READER_MODULES
		if reader == getattr(self, 'reader', None):
			return

		# Delete the 'handle' attribute by closing the file
		opened = hasattr(self, "handle")
		if opened:
			self.close()
		
		# Save reader module
		self.reader = reader

		# Reopen file with new reader if previously opened
		if opened:
			self.open()

	# Method to open the file using a designated module
	def open(self, /, reader=None, **kwargs):
		"""Opens the file using a designated module.  Sets the 'reader' and 
		'handle' attributes, unless a module that is unable to load a file 
		object in which case it only sets the 'reader' attribute.
		
		Parameters:
			reader: type=str, default=None
				- A string representation of the module to use to open the file.  
				If it fails, will progress through modules listed in the 
				`PRODUCT_READER_MODULES` variable in an order that is contingent 
				on the file extension of the 'file' attribute.  If `None`, 
				reader will be set to the 'reader' attribute only if it exists; 
				otherwise, it will iterate through all options.
		
		Returns:
			- A file handler for the opened file, or `None` if the reader is 
			incapable of creating a file object.
		"""
		from pathlib import Path
		import earthaccess as ea

		# Settings
		reader_abbr_map = {
			'rxr': 'rioxarray',
			'xr': 'xarray',
			'nc': 'netcdf4',
			'h5nc': 'h5netcdf',
			'pg': 'pygrib',
			'gpd': 'geopandas',
			'pd': 'pandas',
			'pl': 'polars'
		}
		
		# Get standard name of reader
		if reader is not None:
			reader = str(reader).lower().strip()
			reader = reader_abbr_map.get(reader, reader)
			assert reader in PRODUCT_READER_MODULES

		# Decompress files into byte stream if compressed
		if isinstance(self.path, ea.DataGranule):
			source = ea.open([self.path])[0]
		else:
			source = decompress(self.path) or self.path

		# Get file extensions
		ext = [ext] if isinstance(ext:=Path(self.file).suffixes, str) else ext

		# Set preferred readers first
		mods = [reader] if reader else []
		if reader in TABLE_PRODUCT_READER_MODULES:
			mods += TABLE_PRODUCT_READER_MODULES
		elif reader:
			mods += ['rioxarray', 'xarray']
			if {'nc','nc4'}.intersection(ext):
				mods += ['netcdf4', 'h5netcdf', 'h5py', 'gdal', 'pyhdf']
			elif {'h5','hdf5','he5'}.intersection(ext):
				mods += ['netcdf4', 'h5py', 'h5netcdf', 'gdal']
			elif {'hdf','h4','hdf4','he2','he4','hdfeos'}.intersection(ext):
				mods += ['pyhdf', 'netcdf4', 'gdal']
			elif {'grib','grb','gb','grib2','grb2','gb2'}.intersection(ext):
				mods += ['pygrib', 'gdal']
			mods += [r for r in PRODUCT_READER_MODULES if r not in \
				['geopandas', 'pandas', 'polars']]
		elif not hasattr(self, 'reader'):
			mods += PRODUCT_READER_MODULES

		# Eliminate duplicate items
		mods = [r for i,r in enumerate(mods) if r not in mods[:i]]

		# Loop thru modules
		for i,mod in enumerate(mods):
			# Import module and open file
			try:
				if mod == 'rioxarray':
					try:	# Error can occur if netCDF4 not imported before xarray
						import netCDF4
					except ImportError:
						pass
					import rioxarray as rxr
					f = rxr.open_rasterio(source, **kwargs)
				elif mod == 'xarray':
					try:	# Error can occur if netCDF4 not imported before xarray
						import netCDF4
					except ImportError:
						pass
					import xarray as xr
					f = xr.open_datatree(source, **kwargs)
				elif mod == 'netcdf4':
					import netCDF4 as nc
					f = nc.Dataset(source, 'r', **kwargs)
				elif mod == 'gdal':
					from osgeo import gdal
					gdal.UseExceptions()
					f = gdal.OpenEx(source, gdal.OF_READONLY | \
						gdal.OF_MULTIDIM_RASTER, **kwargs)
					if f is None:
						raise IOError("Could not read file with gdal.")
				elif mod == 'h5py':
					import h5py
					f = h5py.File(source, 'r', **kwargs)
				elif mod == 'h5netcdf':
					import h5netcdf as h5nc
					f = h5nc.File(source, 'r', **kwargs)
				elif mod == 'pyhdf':
					from pyhdf.SD import SD, SDC
					f = SD(source, SDC.READ, **kwargs)
				elif mod == 'pygrib':
					import pygrib as pg
					f = pg.open(source, **kwargs)
				elif mod == 'geopandas':
					import geopandas
					f = open(source, 'r', **kwargs)
				elif mod == 'pandas':
					import pandas
					f = open(source, 'r', **kwargs)
				elif mod == 'polars':
					import polars
					f = open(source, 'r', **kwargs)
				break
			except Exception as e:
				if not i:
					e0 = e
				elif i >= len(mods)-1:
					if isinstance(e, ImportError):
						ImportError("Could not import any module for reading "
							"the file.")
					else:
						raise e0
				else:
					continue

		# if set(mods+[abbr for abbr,m in reader_abbr_map.items() if \
		# 	m in mods]).intersection(locals()):
		# 	raise
		# else:
		# 	raise ImportError("Could not import any module for "
		# 		"reading the file.")
		
		# Save reader module
		self.reader = mod

		# Set and return file handle
		if f:
			self.handle = f
		return f

	# Method to close file
	def close(self):
		"""Closes the file and deletes the handle.
		"""
		import warnings

		# Check for existence of attributes
		if not hasattr(self, 'handle'):
			warnings.warn("\033[38;5;208mFile already closed or never opened."
				"\033[0m", stacklevel=2)
			raise SyntaxError("File never opened.")
		elif not hasattr(self, 'reader'):
			raise AttributeError("File handle exists without a saved reader.")

		# Close file
		if self.reader == 'rioxarray':
			self.handle.close()
		elif self.reader == 'xarray':
			self.handle.close()
		elif self.reader == 'netcdf4':
			self.handle.close()
		elif self.reader == 'gdal':
			if hasattr(self.handle, 'Close'):
				self.handle.Close()
			else:
				self.handle = None
		elif self.reader == 'h5py':
			self.handle.close()
		elif self.reader == 'h5netcdf':
			self.handle.close()
		elif self.reader == 'pyhdf':
			self.handle.end()
		elif self.reader == 'pygrib':
			self.handle.close()
		elif self.reader == 'geopandas':
			self.handle.close()
		elif self.reader == 'pandas':
			self.handle.close()
		elif self.reader == 'polars':
			self.handle.close()
		
		# Delete handle
		delattr(self, "handle")

	# Getter method to return the variable names
	@property
	def variables(self):
		"""Gets a list of all variable names in dataset.
		
		Returns:
			- A list of variable names in the whole dataset, including the path 
			if applicable.
		"""
		# Test for existing attribute
		if hasattr(self, '_variables'):
			pass
		
		# Get all rioxarray/Xarray variable objects
		elif self.reader in ['rioxarray','xarray']:
			self._variables = []
			for path,group in self.handle.subtree_with_keys:
				self._variables.extend([f"{path}/{name}" for name in \
					group.data_vars])
		
		# Get all NetCDF4 variable objects
		elif self.reader == 'netcdf4':
			def _recursive_vars(group):
				path = group.path.lstrip('/')
				self._variables.extend([f"{path}/{name}".lstrip('/') for name \
					in group.variables])
				for subgroup in group.groups.values():
					_recursive_vars(subgroup)
			self._variables = []
			_recursive_vars(self.handle)
		
		# Get all GDAL variable objects
		elif self.reader == 'gdal':
			root = self.handle.GetRootGroup()
			self._variables = root.GetMDArrayFullNamesRecursive()
		
		# Get all h5py variable objects
		elif self.reader == 'h5py':
			import h5py
			self._variables = []
			self.handle.visititems(lambda k,v: self._variables.append(k) if \
				isinstance(v, h5py.Dataset) else None)
		
		# Get all h5netcdf variable objects
		elif self.reader == 'h5netcdf':
			self._variables = []
			def _recursive_vars(group):
				for v in group.variables.values():
					self._variables.append(v.name.lstrip('/'))
				for subgroup in group.groups.values():
					_recursive_vars(subgroup)
		
		# Get all PyHDF variable objects
		elif self.reader == 'pyhdf':
			# from pyhdf.HDF import HDF, HC
			# from pyhdf.V import V
			# from pyhdf.error import HDF4Error
			# self._variables = []
			# out = []
			# h = HDF(self.path, HC.READ)
			# v  = h.vgstart()
			# def _recursive_vars(vg, path):
			# 	for t,r in vg.tagrefs():
			# 		if t == HC.DFTAG_NDG:
			# 			# sds = self.handle.select(self.handle.reftoindex(r))
			# 			sds = f.select(f.reftoindex(r))
			# 			name,_,_,_,_ = sds.info()
			# 			# self._variables.append(f"{path}/name")
			# 			out.append(f"{path}/{name}")
			# 			sds.endaccess()
			# 		elif t == HC.DFTAG_VG:
			# 			subgroup = v.attach(r)
			# 			_recursive_vars(subgroup, f"{path}/{subgroup._name}")
			# 			subgroup.detach()
			
			# ref = -1
			# while True:
			# 	try:
			# 		ref = v.getid(ref)
			# 		print(f"ref={ref}")
			# 	except HDF4Error:
			# 		break
			# 	vg = v.attach(ref)
			# 	_recursive_vars(vg, vg._name)
			# [print(o) for o in out]
			
			# 	for t,r in vg.tagrefs():
			# 		if t == HC.DFTAG_NDG:
			# 			# sds = self.handle.select(self.handle.reftoindex(r))
			# 			sds = f.select(f.reftoindex(r))
			# 			name,_,_,_,_ = sds.info()
			# 			print(f"SDS: {name}")
			# 			sds.endaccess()
			# 		elif t == HC.DFTAG_VG:
			# 			vg2 = v.attach(r)
			# 			print(f"Group: {vg2._name}")
			# 			vg2.detach()

			# return [name for name in self.handle.datasets().keys() if not \
			# 	self.handle.select(name).iscoordvar()]
			self._variables = list(self.handle.datasets().keys())
		
		# Get all pygrib message objects for each variable
		elif self.reader == 'pygrib':
			self._variables = []
			for g in self.handle:
				if g.shortName not in vars:
					self._variables.append(g.shortName)

		# Return variables
		return self._variables
	
	# Method to get the formatted results from a file name match
	def get_filename_attrs(self, **kwargs):
		"""Gets the formatted results from a file name match.

		Returns:
			- A dictionary of filename match groups.
		"""
		
		# Check for associated product
		if not hasattr(self, 'product'):
			raise ValueError("A product is not associated with this dataset, "
				"which is required for performing the file name match.")

		# Return the file name attributes for this dataset
		return self.product.get_filename_attrs(self.file, **kwargs)
	
	# Method to read a variable, attribute or dimension
	def read(self, /, var=None, attr=None, dim=None):
		"""Reads a variable, attribute or dimension from a data file.
		
		Parameters:
			var: type=str|bool, default=None
				- Name of the variable from which to read either the data, an 
				attribute or its dimensions.  Set to `True` to return dictionary 
				of all variables.  Note that variables will only be loaded 
				lazily, so the file needs to remain open in order to continue 
				reading from the array or else e.g. the `extract` method needs 
				to be used to load the data into memory.
			attr: type=str|bool, default=None
				- The name of the variable's or dataset's attribute.  If `var` 
				is `None`, will return the dataset's attribute; otherwise, will 
				return the variable's attribute.  Set to `True` to return a 
				dictionary with all attributes.
			dim: type=str|int|bool, default=None
				- A dictionary with the following dimension elements for the 
				variable, or dataset (if `var` is `None`), dimension given by 
				`dim` (which should be a string, but can also be a number if 
				`var` is set and applicable for the data format):
					-index: index of dimension (only given if `var` is set)
					-size: the length of the dimension (current length is given 
					for unlimited dimensions)
					-coords: the coordinate values of the dimension if available
					If `dim` is set to `True`, will return a dictionary of these 
					dictionaries for all dimensions, where the keys will be the 
					dimension name.
		
		External Modules:
			- numpy -- https://numpy.org/
		
		Returns:
			- The data or value of the variable, attribute or dimension as 
			specified.  If `var` is set in conjunction with `attr` or `dim`, 
			will return values associated with that variable.  If both `attr` 
			and `dim` are set, will return the dimension of the attribute if an 
			array.  If `var`, `attr` and `dim` are all set or all unset, or if 
			`var` is `True` but `attr` or `dim are set, an error will occur.
		"""
		import numpy as np
		from .instrument import Instrument
		from .ancillary import iterable, findattr

		# Check for well-defined inputs
		assert any([var, attr, dim]) and not all([var, attr, dim])
		assert var is not True or attr is None and dim is None
		assert getattr(self, 'reader', None) in RASTER_PRODUCT_READER_MODULES

		# Save original var input
		var0 = var

		# Define dimension-related functions
		if dim is not None:
			# Define dimension renaming function
			if not hasattr(self, 'product') or not (_rename_dimension:= \
			  findattr(self.product, '_rename_dimension', None, \
			  top_level=Instrument)):
				_rename_dimension = lambda dim_name: dim_name
			if callable(_rename_dimension):
				_rename_dim = _rename_dimension
			elif isinstance(_rename_dimension, dict):
				def _rename_dim(dim_name):
					return _rename_dimension.get(dim_name, dim_name)
			else:
				raise ValueError("'_rename_dimension' must either be a "
					"function or a dictionary.")
			def _rename_dims(dim_names):
				if isinstance(dim_names, str):
					return _rename_dim(dim_names)
				elif isinstance(dim_names, dict):
					return {(knew:=_rename_dim(k)): v if not isinstance(v, \
						dict) or knew == k else dict(original_name=k) | v for \
						k,v in dim_names.items()}
				elif iterable(dim_names):
					dtype = type(dim_names)
					return dtype([_rename_dim(dim_name) for dim_name in \
						dim_names])
				else:
					raise ValueError("'dim_names' must be a string, dictionary "
						"or an iterable.")
				
			# Define standardize dimension ID setting function
			standardized_dim_map = dict()
			for dim_var in getattr(self, 'SPECIAL_DIMENSIONS', tuple()):
				if (dim_name:=findattr(self, f"{dim_var}_dimension_name", None, \
				  group=[None, 'labels'])):
					for d in (dim_name if iterable(dim_name) else [dim_name]):
						standardized_dim_map[d] = dim_var
			# standardized_dim_map = {dname:d for d in ['band', 'level', \
			# 	'along_track', 'across_track'] if (dname:=findattr(self, \
			# 	f"{d}_dimension_name", None))}
			def _standardize_dim_id(dims):
				if isinstance(dims, str):
					return standardized_dim_map.get(dims, None)
				elif isinstance(dims, dict):
					for dim_name,d in dims.items():
						if dim_name in standardized_dim_map:
							d['id'] = standardized_dim_map[dim_name]
				elif iterable(dims):
					return [standardized_dim_map.get(d, None) for d in dims]
				else:
					raise ValueError("'dims' must be a string, dictionary or "
						"an iterable.")
		
		# Return all variable objects in a dictionary
		if var is True:
			# Get variable paths and names
			vars = get_path_name(self.variables)
			use_path = len(set(vars)) < len(self.variables)
			if use_path:
				vars = self.variables

			# Return all rioxarray/Xarray variable objects
			if self.reader in ['rioxarray','xarray']:
				return {vars[i]: self.handle[self.variables[i]] for i in \
					range(len(vars))}
			
			# Return all NetCDF4 variable objects
			elif self.reader == 'netcdf4':
				vars = dict()
				for i,ivar in enumerate(vars):
					try:
						vars[ivar] = self.handle[self.variables[i]]
					except:
						vars[ivar] = self.handle.variables[self.variables[i]]
				return vars
			
			# Return all GDAL variable objects
			elif self.reader == 'gdal':
				root = self.handle.GetRootGroup()
				return {vars[i]: root.OpenMDArrayFromFullname(self.variables[i]) \
					for i in range(len(vars))}
			
			# Return all h5py variable objects
			elif self.reader == 'h5py':
				import h5py
				data = dict()
				self.handle.visititems(lambda k,v: data.update({k:v}) if \
					isinstance(v, h5py.Dataset) else None)
				return data
			
			# Return all h5netcdf variable objects
			elif self.reader == 'h5netcdf':
				return {vars[i]: self.handle[self.variables[i]] for i in \
					range(len(vars))}
			
			# Return all PyHDF variable objects
			elif self.reader == 'pyhdf':
				# from pyhdf.HDF import HDF, HC
				# from pyhdf.V import V
				# from pyhdf.error import HDF4Error
				# data = dict()
				# h = HDF(self.path, HC.READ)
				# v = V(h.id)
				# sds_info = self.handle.datasets()
				# for name,sds_obj_info in sds_info.items():
				# 	# sds_id = sds_obj_info[0]
				# 	sds = self.handle.select(name)
				# 	data[name] = sds
				# for ref in v.getvgroups():
				# 	vg = v.attach(ref)
				# 	members = vg.tagrefs()
				# 	for tag,member_ref in members:
				# 		if tag == HC.DFTAG_NDG:  # Check if the member is a dataset
				# 			try:
				# 				sds = self.handle.select(self.handle.inqref( \
				# 					member_ref)[0])
				# 				data[sds.name()] = sds
				# 			except HDF4Error:
				# 				pass
				# 	vg.detach()
				# v.end()
				# h.close()
				# return data
				return {v: self.handle.select(v) for v in vars}
			
			# Return all pygrib message objects for each variable
			elif self.reader == 'pygrib':
				return {name: self.handle.select(shortName=name) for name in \
					self.variables}
		
		# Get variable object and return if requested
		elif var is not None:
			try:
				if self.reader in ['rioxarray', 'xarray']:
					var = self.handle[var]
				elif self.reader == 'netcdf4':
					try:
						var = self.handle[var]
					except:
						var = self.handle.variables[var]
				elif self.reader == 'gdal':
					root = self.handle.GetRootGroup()
					var = root.OpenMDArrayFromFullname(var)
				elif self.reader == 'h5py':
					var = self.handle[var]
				elif self.reader == 'h5netcdf':
					var = self.handle.variables[var]
				elif self.reader == 'pyhdf':
					var = self.handle.select(var)
				elif self.reader == 'pygrib':
					if isinstance(var, str):
						var = self.handle.select(shortName=var)
					else:
						var = self.handle.select(paramId=var)
			except:
				var = self.read(var=True)[var]
			if attr is None and dim is None:
				return var
		
		# Determine if base is dataset or variable
		var_isbase = var is not None
		base = var if var_isbase else self.handle
		
		# Return all attributes of dataset/variable
		if attr is True:
			if self.reader in ['rioxarray', 'xarray']:
				return base.attrs
			elif self.reader == 'netcdf4':
				return {attr:base.getncattr(attr) for attr in base.ncattrs()}
			elif self.reader == 'gdal':
				if var_isbase:
					attrs = var.GetAttributes()
				else:
					attrs = self.handle.GetRootGroup().GetAttributes()
				return {a.GetName():a for a in attrs}
			elif self.reader == 'h5py':
				return base.attrs
			elif self.reader == 'h5netcdf':
				return base.attrs
			elif self.reader == 'pyhdf':
				return base.attributes()
			elif self.reader == 'pygrib':
				return [{k:g[k] for k in g.keys() if g.valid_key(k) and k \
					not in ['values']} for g in base]
		
		# Return attribute of dataset/variable
		elif attr is not None:
			if self.reader in ['rioxarray', 'xarray']:
				return base.attrs[attr]
			elif self.reader == 'netcdf4':
				return base.getncattr(attr)
			elif self.reader == 'gdal':
				if var_isbase:
					return var.GetAttribute(attr)
				else:
					return self.handle.GetRootGroup().GetAttribute(attr)
			elif self.reader == 'h5py':
				return base.attrs[attr]
			elif self.reader == 'h5netcdf':
				return base.attrs[attr]
			elif self.reader == 'pyhdf':
				return getattr(base, attr)
			elif self.reader == 'pygrib':
				return [g[attr] for g in base]
		
		# Return all dimensions of dataset/variable
		elif dim is True:
			# Return all dimensions of rioxarray/Xarray dataset/variable object
			if self.reader in ['rioxarray', 'xarray']:
				if var_isbase:
					dims = {name: dict(index=i, size=size) for i,(name,size) \
						in enumerate(var.sizes.items())}
				else:
					dims = {name: dict(size=size) for name,size in \
						self.handle.sizes.items()}
				for k,v in dims.items():
					coords = base.coords.get(dim)
					if coords:
						v['coords'] = coords
				dims = _rename_dims(dims)
				_standardize_dim_id(dims)
				return dims
			
			# Return all dimensions of NetCDF4 dataset/variable object
			elif self.reader == 'netcdf4':
				if var_isbase:
					dims = {d.name: dict(index=i, size=d.size) for i,d in \
						enumerate(var.get_dims())}
				else:
					dims = {name: dict(size=d.size) for name,d in \
						self.handle.dimensions.items()}
				for k,v in dims.items():
					if k in self.handle.variables:
						v['coords'] = self.handle.variables[k][:]
				dims = _rename_dims(dims)
				_standardize_dim_id(dims)
				return dims
			
			# Return all dimensions of GDAL dataset/variable object
			elif self.reader == 'gdal':
				if var_isbase:
					ds = var.GetDimensions()
				else:
					ds = self.handle.GetRootGroup().GetDimensions()
				dims = dict()
				for i,d in enumerate(ds):
					if var_isbase:
						dims[d.GetName()] = dict(index=i, size=d.GetSize())
					else:
						dims[d.GetName()] = dict(size=d.GetSize())
					coords = d.GetIndexingVariable()
					if coords:
						dims[d.GetName()]['coords'] = coords.ReadAsArray()
				dims = _rename_dims(dims)
				_standardize_dim_id(dims)
				return dims
			
			# Return all dimensions of h5py dataset/variable object
			elif self.reader == 'h5py':
				dims = dict()
				vars = [var] if var_isbase else self.read(var=True).values()
				for ivar in vars:
					for i,d in enumerate(ivar.dims):
						if var_isbase:
							v = dict(index=i, size=ivar.shape[i])
						else:
							v = dict(size=ivar.shape[i])
						if d.keys():
							v['coords'] = d[d.keys()[0]]
						name = d.label or d.keys()[0]
						if name not in dims:
							dims[name] = v
				dims = _rename_dims(dims)
				_standardize_dim_id(dims)
				return dims
			
			# Return all dimensions of h5netcdf dataset/variable object
			elif self.reader == 'h5netcdf':
				if var_isbase:
					dims = {name:dict(index=i, \
						size=self.handle.dimensions.get(name).size) for i,name \
						in enumerate(var.dimensions)}
				else:
					dims = {name:dict(size=d.size) for name,d in \
						self.handle.dimensions.items()}
				for k,v in dims.items():
					try:
						v['coords'] = self.read(var=k)[:]
					except:
						pass
				dims = _rename_dims(dims)
				_standardize_dim_id(dims)
				return dims
			
			# Return all dimensions of PyHDF dataset/variable object
			elif self.reader == 'pyhdf':
				dims = dict()
				vars = [var] if var_isbase else self.read(var=True).values()
				for ivar in vars:
					for name,(size,i,_,scale_type,_) in \
					  ivar.dimensions(full=True).items():
						if var_isbase:
							dims[name] = dict(index=i, size=size)
						elif name in dims:
							continue
						else:
							dims[name] = dict(size=size)
						if scale_type != 0:
							dims[name]['coords'] = base.dim(i).getscale()
				dims = _rename_dims(dims)
				_standardize_dim_id(dims)
				return dims
			
			# Return all dimensions of pygrib dataset/variable object
			elif self.reader == 'pygrib':
				timestamps = []
				levels = []
				latitudes = []
				longitudes = []
				ni = []
				nj = []
				for g in base:
					timestamps.append(g.validDate)
					levels.append(g.level)
					try:
						latitudes.append(np.linspace( \
							g.latitudeOfFirstGridPointInDegrees, \
							g.latitudeOfLastGridPointInDegrees, g.Nj))
						if g.longitudeOfFirstGridPointInDegrees < \
							g.longitudeOfLastGridPointInDegrees:
							longitudes.append(np.linspace( \
								g.longitudeOfFirstGridPointInDegrees, \
								g.longitudeOfLastGridPointInDegrees, g.Ni))
						elif g.longitudeOfFirstGridPointInDegrees >= 0 and \
							g.longitudeOfLastGridPointInDegrees >= 0:
							longitudes.append(np.concatenate(np.linspace( \
								g.longitudeOfFirstGridPointInDegrees, 360, \
								g.Ni), np.linspace( \
								g.longitudeOfFirstGridPointInDegrees, 0, \
								-g.Ni)[::-1]))
						else:
							longitudes.append(np.concatenate(np.linspace( \
								g.longitudeOfFirstGridPointInDegrees, 180, \
								g.Ni), np.linspace( \
								g.longitudeOfFirstGridPointInDegrees, -180, \
								-g.Ni)[::-1]))
						ni.append(g.Ni)
						nj.append(g.Nj)
					except:
						lats,lons = g.latlons()
						ni.append(lons.shape[1])
						nj.append(lats.shape[0])
						if not np.any(lons[:,1:]-lons[:,[0]]) and not \
							np.any(lats[1:,:]-lats[0,:]):
							lats = lats[0,:]
							lons = lons[:,0]
						latitudes.append(lats)
						longitudes.append(lons)
				timestamps_size = len(set(timestamps))
				levels_size = len(set(levels))
				if len(set(ni)) > 1 or len(set(nj)) > 1:
					raise ValueError("Inconsistent grid dimensions.")
				lats_size = nj[0]
				lons_size = ni[0]
				timestamps_dim = 0 if timestamps_size > 1 else None
				levels_dim = 0 if timestamps_dim is None or levels_size > 1 \
					else None
				try:
					levelists = [g.levelist for g in base]
				except:
					levelists = None
				dims = {
					'validDate': dict(
						index = timestamps_dim, 
						size = timestamps_size,
						coords = timestamps
					),
					'level' if levelists is None else 'levelist': dict(
						index = levels_dim,
						size = levels_size,
						coords = levels if levelists is None else levelists
					),
					'latitude': dict(
						index = 1,
						size = lats_size,
						coords = latitudes
					),
					'longitude': dict(
						index = 2,
						size = lons_size,
						coords = longitudes
					)
				}
				dims = _rename_dims(dims)
				_standardize_dim_id(dims)
				return dims
		
		# Return dimension of dataset/variable 
		elif dim is not None:
			# Return dimension of rioxarray/Xarray dataset/variable object
			if self.reader in ['rioxarray', 'xarray']:
				if var_isbase:
					if isinstance(dim, str):
						i = _rename_dims(var.dims).index(dim)
					else:
						i = dim
						dim = _rename_dims(var.dims)[i]
					v = dict(index=i, size=_rename_dims(var.sizes)[dim])
				else:
					v = dict(size=_rename_dims(self.handle.sizes)[dim])
				coords = _rename_dims(base.coords).get(dim)
				if coords:
					v['coords'] = coords
				if (dim_id:=_standardize_dim_id(dim)):
					v['id'] = dim_id
				return v
			
			# Return dimension of NetCDF4 dataset/variable object
			elif self.reader == 'netcdf4':
				if var_isbase:
					if isinstance(dim, str):
						i = _rename_dims(var.dimensions).index(dim)
					else:
						i = dim
						dim = _rename_dims(var.dimensions)[i]
					size = var.get_dims()[i].size
					v = dict(index=i, size=size)
				else:
					v = dict(size=_rename_dims(self.handle.dimensions)[dim].size)
				if dim in self.handle.variables:
					v['coords'] = self.handle.variables[dim][:]
				if (dim_id:=_standardize_dim_id(dim)):
					v['id'] = dim_id
				return v
			
			# Return dimension of GDAL dataset/variable object
			elif self.reader == 'gdal':
				v = self.read(var=var0, dim=True)[dim]
				if 'original_name' in v:
					del v['original_name']
				if (dim_id:=_standardize_dim_id(dim)):
					v['id'] = dim_id
				return v
			
			# Return dimension of h5py dataset/variable object
			elif self.reader == 'h5py':
				if var_isbase:
					if isinstance(dim, str):
						try:
							i = _rename_dims([d.label for d in \
								var.dims]).index(dim)
						except:
							i = [dim in _rename_dims(d.keys()) for d in \
								var.dims].index(True)
						d = var.dims[i]
					else:
						i = dim
						d = var.dims[i]
						dim = _rename_dims(d.label or d.keys()[0])
					v = dict(index=i, size=var.shape[i])
				else:
					d2 = [None]*2
					size2 = [None]*2
					for ivar in self.read(var=True).values():
						for i,d in enumerate(ivar.dims):
							if dim == _rename_dims(d.label):
								d2[0] = d
								size2[0] = ivar.shape[i]
								break
							if dim in _rename_dims(d.keys()) and d2[1] is None:
								d2[1] = d
								size2[1] = ivar.shape[i]
						if d2[0]:
							break
					d = d2[0] or d2[1]
					size = size2[0] or size2[1]
					v = dict(size=size)
				if d.keys():
					v['coords'] = d[d.keys()[0]]
				if (dim_id:=_standardize_dim_id(dim)):
					v['id'] = dim_id
				return v
			
			# Return dimension of h5netcdf dataset/variable object
			elif self.reader == 'h5netcdf':
				if var_isbase:
					if isinstance(dim, str):
						i = _rename_dims(var.dimensions).index(dim)
					else:
						i = dim
						dim = _rename_dims(var.dimensions)[i]
					d = _rename_dims(self.handle.dimensions)[dim]
					v = dict(index=i, size=d.size)
				else:
					d = _rename_dims(self.handle.dimensions)[dim]
					v = dict(size=d.size)
				try:
					v['coords'] = self.read(var=dim)[:]
				except:
					pass
				if (dim_id:=_standardize_dim_id(dim)):
					v['id'] = dim_id
				return v
			
			# Return dimension of PyHDF dataset/variable object
			elif self.reader == 'pyhdf':
				if var_isbase:
					if isinstance(dim, str):
						i = _rename_dims(list(var.dimensions())).index(dim)
					else:
						i = dim
						dim = _rename_dims(list(var.dimensions()))[i]
					d = var.dim(i)
					v = dict(index=i, size=d.length())
				else:
					for v,(names,shape,_,_) in self.handle.datasets().items():
						names = _rename_dims(names)
						if dim in names:
							d = self.handle.select(v).dim(names.index(dim))
							break
					else:
						d = None
					v = dict(size=d.length())
				if d.info()[2] != 0:
					v['coords'] = d.getscale()
				if (dim_id:=_standardize_dim_id(dim)):
					v['id'] = dim_id
				return v
			
			# Return dimension of pygrib dataset/variable object
			elif self.reader == 'pygrib':
				timestamps = [g.validDate for g in base]
				timestamps_size = len(set(timestamps))
				timestamps_dim = 0 if timestamps_size > 1 else None
				if dim == _rename_dims('validDate'):
					return dict(
						index = timestamps_dim, 
						size = timestamps_size,
						coords = timestamps)
				levels = [g.level for g in base]
				levels_size = len(set(levels))
				levels_dim = 0 if timestamps_dim is None or levels_size > 1 \
					else None
				if dim == _rename_dims('level'):
					try:
						levelists = [g.levelist for g in base]
					except:
						levelists = None
					return dict(
						index = levels_dim,
						size = levels_size,
						coords = levels if levelists is None else levelists)
				coords = []
				n = []
				for g in base:
					try:
						if dim == _rename_dims('latitude'):
							coords.append(np.linspace( \
								g.latitudeOfFirstGridPointInDegrees, \
								g.latitudeOfLastGridPointInDegrees, g.Nj))
							n.append(g.Nj)
						elif dim == _rename_dims('longitude'):
							if g.longitudeOfFirstGridPointInDegrees < \
								g.longitudeOfLastGridPointInDegrees:
								coords.append(np.linspace( \
									g.longitudeOfFirstGridPointInDegrees, \
									g.longitudeOfLastGridPointInDegrees, \
									g.Ni))
							elif g.longitudeOfFirstGridPointInDegrees >= 0 \
								and g.longitudeOfLastGridPointInDegrees >= 0:
								coords.append(np.concatenate(np.linspace( \
									g.longitudeOfFirstGridPointInDegrees, \
									360, g.Ni), np.linspace( \
									g.longitudeOfFirstGridPointInDegrees, \
									0, -g.Ni)[::-1]))
							else:
								coords.append(np.concatenate(np.linspace( \
									g.longitudeOfFirstGridPointInDegrees, \
									180, g.Ni), np.linspace( \
									g.longitudeOfFirstGridPointInDegrees, \
									-180, -g.Ni)[::-1]))
							n.append(g.Ni)
					except:
						lats,lons = g.latlons()
						n.append(lats.shape[0] if dim == \
							_rename_dims('latitude') else lons.shape[1])
						if not np.any(lons[:,1:]-lons[:,[0]]) and not \
							np.any(lats[1:,:]-lats[0,:]):
							lats = lats[0,:]
							lons = lons[:,0]
						coords.append(lats if dim == _rename_dims('latitude') \
							else lons)
					if len(set(n)) > 1:
						raise ValueError("Inconsistent grid dimensions.")
				v = dict(
					index = 1+int(dim==_rename_dims('longitude')),
					size = n[0],
					coords = coords)
				if (dim_id:=_standardize_dim_id(dim)):
					v['id'] = dim_id
				return v
	
	# Method to get the data shape for a given variable
	def get_shape(self, /, var):
		"""Gets the data shape of the specified variable of this dataset.
		
		Parameters:
			var: type=str
				- Name of the variable from which to read its dimensions for 
				determining its shape.
		
		Returns:
			- The data shape of the given variable.
		"""

		# Get the dimensions of the variable
		dims = self.read(var=var, dim=True)

		# Return the data shape for the given variable
		return tuple(d['size'] for d in sort_dims(dims))

	# Method to locate special dimension
	def dim_index(self, /, name, var, **kwargs):
		"""Finds the dimension index from a dimension name or ID.
		
		Parameters:
			name: type=str
				- The dimension name, or one of a select special IDs.
			var: type=str
				- Name of the variable from which to read its dimensions.
		
		Returns:
			- The index of the dimension in the given variable.
		"""
		import re
		from .ancillary import iterable, findattr

		# Determine if name is a special dimension name
		special = name.strip().lower() in getattr(self, 'SPECIAL_DIMENSIONS', \
			tuple()) or name.endswith("_dimension_name")
		if special:
			name = re.sub("_dimension_name$", "", name.strip().lower())

		# Return the dimension index
		if special:
			dim_name = findattr(self, f"{name}_dimension_name", None, \
				group=[None, 'labels'])
			if dim_name is None:
				g = Granule(var, dataset=self, dims=True, **kwargs)
				for d in g.dimensions.values():
					if d.get('id') == name:
						return d['index']
			elif iterable(dim_name):
				dims = self.read(var=var, dim=True)
				dim_name = set(dim_name).intersection(dims).pop()
				return dims[dim_name]['index']
			else:
				return self.read(var=var, dim=dim_name)['index']
			return None
		else:
			return self.read(var=var, dim=name)['index']
			
	# Method to extract data wtih given slice and with the options of masking 
	# and scaling/offsetting
	def extract(self, /, var, s=slice(None), mask=True, fill_value=None, 
	  valid_min=None, valid_max=None, valid_range=None, actual_range=None, 
	  scale=True, scale_factor=None, offset=None, conversion="*+", **kwargs):
		"""Extracts data from file or file dataset object, allowing for custom 
		masking and scaling functions.
	
		Parameters:
		var: type=str|numpy.ndarray
			The variable name for which to extract the data from this dataset 
			object, or the actual file dataset object (e.g. obtained with the 
			'read' method).
		s: type=slice|int|tuple, default=slice(None)
			A slice to apply to the data.
		mask: type=bool, default=True
			If False, will turn off masking.
		fill_value: type=str|int|float, default=None
			The fill value to mask the data with.  If a string, will search this 
			object's attributes for this value (or 'fill_value' if this argument 
			is None), and if found, will search the file data's attributes for 
			that name, and if found, will use that value.
		valid_min: type=str|int|float, default=None
			The minimum value of the valid range to mask the data with 
			(pre-scaling).  If a string, will search this object's attributes 
			for this value (or 'valid_min' if this argument is None), and if 
			found, will search the file data's attributes for that name, and if 
			found, will use that value.
		valid_max: type=str|int|float, default=None
			The maximum value of the valid range to mask the data with 
			(pre-scaling).  If a string, will search this object's attributes 
			for this value (or 'valid_max' if this argument is None), and if 
			found, will search the file data's attributes for that name, and if 
			found, will use that value.
		valid_range: type=str|tuple|list, default=None
			The two-element tuple of the valid range to mask the data with 
			(pre-scaling).  Will be ignored if 'valid_min' or 'valid_max' are 
			given.  If a string, will search this object's attributes for this 
			value (or 'valid_range' if this argument is None), and if found, 
			will search the file data's attributes for that name, and if found, 
			will use that value.
		actual_range: type=str|tuple|list, default=None
			The two-element tuple of the valid range to mask the data with 
			(post-scaling).  If a string, will search this object's attributes 
			for this value (or 'actual_range' if this argument is None), and if 
			found, will search the file data's attributes for that name, and if 
			found, will use that value.
		scale: type=bool, default=True
			If False, will turn off scaling.
		scale_factor: type=str|int|float, default=None
			The scale factor to scale the data with.  If a string, will search 
			this object's attributes for this value (or 'scale_factor' if this 
			argument is None), and if found, will search the file data's 
			attributes for that name, and if found, will use that value.  If no 
			value can be found but 'offset' is set, will use 1.
		offset: type=str|int|float, default=None
			The offset to scale the data with.  If a string, will search this 
			object's attributes for this value (or 'offset' if this argument is 
			None), and if found, will search the file data's attributes for that 
			name, and if found, will use that value.  If no value can be found 
			but 'offset' is set, will use 0.
		conversion: type=str, default="*+"
			The conversion operators and order to use when using custom scaling.  
			The data can be scaled by 'scale_factor' using either multiplication 
			('*') or division ('/'), and it can be positioned with 'offset' 
			using either addition ('+') or subtraction ('-').  If '*' or '/' are 
			listed first in the two-element string, it will be the first 
			operation with the scale factor, and the second operation would be 
			with the offset.  If '+' or '-' are listed first, then the offset is 
			applied first before the scale factor.

		External modules:
			numpy -- https://numpy.org/

		Returns:
		Data extracted and sliced for the given variable or dataset with masking 
		and scaling applied according to the given arguments.
		"""
		import numpy as np
		from .ancillary import iterable, getattr_recursive

		# Read data
		if isinstance(var, str):
			var_name = var
			var = self.read(var=var)
		else:
			var_name = None

		# Get full slice object
		shape = var.info()[2] if self.reader=='pyhdf' else (len(var),) if \
			self.reader=='pygrib' else var.shape
		s = full_slice(s, shape)

		# Function to get the proper value for an argument
		def _get_arg_val(arg, name):
			if arg is None:
				arg = getattr_recursive(self, name, None)
				if isinstance(arg, dict):
					if var_name and var_name in arg:
						return arg[var_name]
				return None
			elif arg is False:
				return None
			else:
				return arg
		
		# Get mask and scale labels for custom data masking and scaling
		if mask:
			fill_value = _get_arg_val(fill_value, 'fill_value')
			valid_min = _get_arg_val(valid_min, 'valid_min')
			valid_max = _get_arg_val(valid_max, 'valid_max')
			valid_range = _get_arg_val(valid_range, 'valid_range')
			actual_range = _get_arg_val(actual_range, 'actual_range')
			auto_mask = all(val is None for val in [fill_value, valid_min, \
				valid_max, valid_range, actual_range])
		if scale:
			scale_factor = _get_arg_val(scale_factor, 'scale_factor')
			offset = _get_arg_val(offset, 'offset')
			conversion = _get_arg_val(conversion, 'conversion')
			auto_scale = all(val is None for val in [scale_factor, offset])
		# if mask is not True or fill_value is not None:
		# 	if isinstance(mask, str):
		# 		fill_value = mask
		# 		mask = None
		# 	else:
		# 		mask = False
		# if scale is not True:
		# 	scale_factor = 1 if scale is False else scale
		# 	scale = False

		# Define function to calibrate data
		math = {'+': np.add, '-': np.subtract, '*': np.multiply, '/': np.divide}
		def _calibrate(operations, data, m, b):
			funcs = (math[operations[0]], math[operations[1]])
			operators = (m,b) if operations[0] in "*/" else (b,m)
			return funcs[1](funcs[0](data, operators[0]), operators[1])

		# Extract data
		if self.reader == 'rioxarray':
			import rioxarray as rxr
			pass
		elif self.reader == 'xarray':
			import xarray as xr
			pass
		elif self.reader == 'netcdf4':
			# import netCDF4 as nc
			var.set_auto_mask(mask and auto_mask)
			var.set_auto_scale(scale and auto_scale)
			data = var[s]
			def _get_arg_attr(attr_name):
				if not isinstance(attr_name, str):
					return attr_name
				elif attr_name in var.ncattrs():
					return var.getncattr(attr_name)
				elif hasattr(data, 'dtype') and np.issubdtype(data.dtype, \
				  np.flexible):
					return attr_name
				raise ValueError(f"Could not find the {attr_name} attribute.")
			if mask and not auto_mask:
				fill_value = _get_arg_attr(fill_value)
				valid_min = _get_arg_attr(valid_min)
				valid_max = _get_arg_attr(valid_max)
				valid_range = _get_arg_attr(valid_range)
				actual_range = _get_arg_attr(actual_range)
			if scale and not auto_scale:
				scale_factor = _get_arg_attr(scale_factor)
				offset = _get_arg_attr(offset)
			# if not mask:
			# 	if mask is None:
			# 		fill_value = var.getncattr(fill_value)
			# 	if fill_value is not None:
			# 		data = np.ma.masked_equal(data, fill_value)
			# if not scale:
			# 	if isinstance(scale_factor, str):
			# 		scale_factor = var.getncattr(scale_factor)
			# 	if isinstance(offset, str):
			# 		offset = var.getncattr(offset)
			# 	data = _calibrate(conversion, data, scale_factor, offset)
		elif self.reader == 'gdal':
			from osgeo import gdal
			pass
		elif self.reader == 'h5py':
			import h5py
			pass
		elif self.reader == 'h5netcdf':
			import h5netcdf as h5nc
			pass
		elif self.reader == 'pyhdf':
			from pyhdf.SD import SD, SDC
			pass
		elif self.reader == 'pygrib':
			import pygrib as pg
			pass
		elif self.reader == 'geopandas':
			import geopandas as gpd
			pass
		elif self.reader == 'pandas':
			import pandas as pd
			pass
		elif self.reader == 'polars':
			import polars as pl
			pass
		
		# # Function to return native Python number or array set for broadcasting
		# def _convert_num_broadcast(val, idim=None):
		# 	if not iterable(val):
		# 		return val.item() if hasattr(val, 'item') else val
		# 	else:
		# 		if not isinstance(val, np.ndarray):
		# 			val = np.array(val)
		# 		ndim = len(tuple(shape))
		# 		i = (...,)+(None,)*(ndim-idim-1)
		# 		return val[i]

		# Function to select values from iterable attribute
		def _select_attr_vals(attr):
			# Return if not an iterable
			if not iterable(attr):
				return broadcast_prep(attr, shape)
			
			# Return sliced array if single matching dimension size
			n = len(attr)
			if sum([size == n for size in shape]) == 1:
				idim = tuple(shape).index(n)
				return broadcast_prep(attr[s[idim]], shape, idim)
			
			# Quick search for band dimension and return sliced array
			dims = self.read(var=var_name, dim=True)
			for d in dims.values():
				if d.get('id') == 'band':
					idim = d['index']
					return broadcast_prep(attr[s[idim]], shape, idim)
			
			# Long search for band dimension and return sliced array
			g = Granule(var_name, dataset=self, dims=True)
			for d in g.dimensions.values():
				if d.get('id') == 'band':
					idim = d['index']
					return broadcast_prep(attr[s[idim]], shape, idim)
			
			# Throw error
			raise ValueError("Could not find band dimension index.")

		# Perform manual masking and scaling
		if mask and not auto_mask:
			if fill_value is not None:
				fill_value = _select_attr_vals(fill_value)
				data = np.ma.masked_equal(data, fill_value)
			if valid_min is not None or valid_max is not None:
				if valid_max is None:
					valid_min = _select_attr_vals(valid_min)
					data = np.ma.masked_less(data, valid_min)
				elif valid_min is None:
					valid_max = _select_attr_vals(valid_max)
					data = np.ma.masked_greater(data, valid_max)
				else:
					valid_min = _select_attr_vals(valid_min)
					valid_max = _select_attr_vals(valid_max)
					data = np.ma.masked_outside(data, valid_min, valid_max)
			elif valid_range is not None:
				data = np.ma.masked_outside(data, *valid_range)
		if scale and not auto_scale:
			if scale_factor is None:
				scale_factor = 1
			if offset is None:
				offset = 0
			data = _calibrate(conversion, data, _select_attr_vals(scale_factor), \
				_select_attr_vals(offset))
		if mask and not auto_mask:
			if actual_range is not None:
				data = np.ma.masked_outside(data, *actual_range)

		# Return data
		return data

	
		
		# if self.reader == 'rioxarray':
		# 	import rioxarray as rxr
			
		# elif self.reader == 'xarray':
		# 	import xarray as xr
			
		# elif self.reader == 'netcdf4':
		# 	import netCDF4 as nc
			
		# elif self.reader == 'gdal':
		# 	from osgeo import gdal
			
		# elif self.reader == 'h5py':
		# 	import h5py
			
		# elif self.reader == 'h5netcdf':
		# 	import h5netcdf as h5nc
			
		# elif self.reader == 'pyhdf':
		# 	from pyhdf.SD import SD, SDC
			
		# elif self.reader == 'pygrib':
		# 	import pygrib as pg
			
		# elif self.reader == 'geopandas':
		# 	import geopandas as gpd
			
		# elif self.reader == 'pandas':
		# 	import pandas as pd
			
		# elif self.reader == 'polars':
		# 	import polars as pl

	# Method to set geolocation data for the dataset using the geolocation 
	# product corresponding to this dataset
	def set_geo(self, /, reload=False, **kwargs):
		"""Retrieves the geolocation data from the instrument's geolocation 
		product and saves it as attributes to this dataset.

		Parameters:
			reload: type=bool, default=False
				- If `False`, will first check if geolcoation data already 
				loaded; if `True`, will overwrite any saved geolocation data.
			**kwargs:
				- Keyword arguments that will be used to specify geolocation 
				variable names ('lat', 'lon', 'x', or 'y'), or extra keyword 
				arguments to be passed to the `cousin_dataset` or `extract` 
				methods of the dataset object.
				- If these values are not provided as keyword arguments, will 
				search for variable names as attributes ('latitude_name', 
				'longitude_name', 'x_name', 'y_name').
				- If no geolocation product is found or multiple are found, an 
				exception will be raised.
		
		Returns:
			- The dimensions dictionary of the geolocation arrays.
		"""
		from .ancillary import findattr

		# Call parent `set_geo` function if it exists
		if self.__class__ is Dataset and hasattr(self, 'product'):
			set_geo_init = findattr(self.product, 'set_geo', None)
			if set_geo_init is not None:
				try:
					return set_geo_init(dataset=self, **(kwargs | {'reload': \
						reload}))
				except:
					pass

		# Check if geolocation data already loaded
		load = reload or not (hasattr(self, 'latitude') and hasattr(self, \
			'longitude') or hasattr(self, 'x') and hasattr(self, 'y'))

		# Get geolocation product name
		geo_product = findattr(self, "geo_product", None)
		if geo_product is None:
			raise ValueError("No geolocation product found.")
		if isinstance(geo_product, dict):
			geo_product_key = findattr(self, 'geo_product_key', None)
			if geo_product_key is None:
				raise ValueError("Multiple possible 'geo_product' values; set "
					"'geo_product_key' to the attribute name/location of the "
					"key value to use.")
			geo_product = geo_product.get(geo_product_key, None)
			if geo_product is None:
				raise ValueError(f"Could not find key '{geo_product_key}' in "
					"'geo_product' dictionary with a valid value.")
		
		# Load the geolocation product
		if hasattr(self, 'product') and self.product.id == geo_product:
			geo_ds = self
		else:
			geo_ds = self.cousin_dataset(geo_product, **kwargs)

		# Loop thru geolocation parameters
		dims = None
		loc_vars = [
			('lat', 'latitude', ['latitudes', 'latitude', 'Latitudes', 
				'Latitude', 'LATITUDES', 'LATITUDE', 'lats', 'lat']), 
			('lon', 'longitude', ['longitudes', 'Longitude', 'Longitudes', 
				'Longitude', 'LONGITUDES', 'LONGITUDE', 'lons', 'lon']),
			('x', 'x', ['x', 'X']),
			('y', 'y', ['y', 'Y']),
		]
		for var_name,attr_name,search_names in loc_vars:
			# Get search name(s) for variable
			var_value = kwargs.get(var_name, findattr(geo_ds, f"{attr_name}_name", \
				None, group=[None, 'labels']))
			if var_value is None:
				var_value = search_names
			elif not isinstance(var_value, str):
				raise ValueError(f"'{var_name}' must be a string or None.")
			else:
				search_names = [var_value.strip()]
			
			# Search each possible variable name and set dataset attribute if 
			# found
			for search_name in search_names:
				if search_name in geo_ds.variables:
					if load:
						setattr(self, attr_name, geo_ds.extract(var= \
							search_name, **kwargs))
					if dims is None:
						dims = geo_ds.read(var=search_name, dim=True, **kwargs)
					break
			
		# Return the dimensions of the geolocation arrays
		return dims

	# Method to set platform state information (position, velocity, time)
	def set_state(self, /, *args, **kwargs):
		"""Sets the platform's state information (position, velocity, and time).
	
		Parameters:
			*args:
				-
			**kwargs:
				- 
		"""

		# Check for associated instrument object
		if not hasattr(self, 'instrument'):
			raise ValueError("This dataset does not have an associated "
				"instrument to set the platform state information.")
		
		# Set the platform state from the instrument object using this dataset 
		# information
		self.instrument.set_state(*args, dataset=self, **kwargs)

	# Property for the order of coordinates
	@property
	def coordinate_order(self):
		"""Gets the order of coordinates.
	
		Returns:
			- A string representing the order of coordinates ("ij" or "ji").
		"""
		return self._coordinate_order if hasattr(self, '_coordinate_order') \
			else None
	@coordinate_order.deleter
	def coordinate_order(self):
		"""Deletes the order of coordinates."""
		if hasattr(self, '_coordinate_order'):
			del self._coordinate_order
		if hasattr(self, '_corners'):
			del self._corners
		if hasattr(self, '_border'):
			del self._border
	@coordinate_order.setter
	def coordinate_order(self, /, order):
		"""Sets the order of coordinates to either 'ij' or 'ji'.
	
		Parameters:
			order: type=str
				- Either "ij" for the horizontal axis first, or "ji" for the 
				vertical axis first.

		External modules:
			- numpy -- https://numpy.org/
			- shapely -- https://shapely.readthedocs.io/
		"""
		import numpy as np
		from shapely.ops import transform

		# Validate input
		order = order.strip().lower()
		if order not in ['ij','ji']:
			raise ValueError("'order' must be either 'ij' or 'ji'.")
		
		# Set coordinate order, and update saved data with coordinate data
		if not hasattr(self, '_coordinate_order'):
			setattr(self, '_coordinate_order', order)
		elif self._coordinate_order != order:
			if hasattr(self, '_corners'):
				self._corners = np.fliplr(self._corners)
			if hasattr(self, '_border'):
				self._border = transform(lambda i,j: (j,i), self._border)

	# Method to get the geolocation corners of a swath dataset
	def corners(self, /, *args, coordinate_order=None, **kwargs):
		"""Gets the corner geolocation coordinates of a given dataset.
	
		Parameters:
			*args:
				- 
			coordinate_order: type=bool, default=None
				- Set to "ji" to order y-axis data first, then x-axis data; and 
				set to "ij" for the reverse.  If `None`, will select it 
				automatically depending on if latitude/longitude values are used 
				(ji) or x/y values are used (ij).  The result will be saved to 
				the 'coordinate_order' attribute in the resulting dataset.
			**kwargs:
				- 

		Returns:
			- A numpy ndarray of shape (4, 2) with the corner coordinates as 
			either (latitude, longitude) or (x,y) pairs, depending on the 
			available variables in the dataset.
		"""
		from .ancillary import findattr

		# Check for already-processed corners
		if hasattr(self, '_corners'):
			if coordinate_order is not None:
				self.coordinate_order = coordinate_order
			return self._corners

		# Check for associated instrument object
		if not hasattr(self, 'instrument'):
			raise ValueError("This dataset must be associated with an "
				"instrument in order to use this routine.")
		
		# Check for swath structure
		if self.product.structure != "swath":
			raise RuntimeError("This routine applies only to datasets with a "
				"swath structure.")
		
		# Set the geolocation corners for this dataset from the instrument 
		# object and return the result
		try:
			self._corners = self.instrument.corners(*args, dataset=self, \
				**kwargs)
			return self._corners
		except:
			geo_prod_id = findattr(self, 'geo_product', None)
			if self.id == geo_prod_id:
				raise RuntimeError("Could not locate geolocation data in this " \
					"dataset.")
			elif geo_prod_id is None:
				raise RuntimeError("Could not locate geolocation data in this " \
					"dataset or in its associated geolocation product dataset.")
			geo_ds = self.cousin_dataset(geo_prod_id, **kwargs)
			if geo_ds is None:
				raise RuntimeError("Could not find associated geolocation " \
					"dataset to this dataset.")
			return self.instrument.corners(*args, dataset=geo_ds, **kwargs)

	# Method to get the geolocation boundaries of a swath dataset
	def border(self, /, *args, coordinate_order=None, **kwargs):
		"""Gets the border geolocation coordinates for this dataset.  If 
		unsuccesful, will return the coordinates for the cousin geolocation 
		dataset if found.
	
		Parameters:
			*args:
				- 
			coordinate_order: type=bool, default=None
				- Set to "ji" to order y-axis data first, then x-axis data; and 
				set to "ij" for the reverse.  If `None`, will select it 
				automatically depending on if latitude/longitude values are used 
				(ji) or x/y values are used (ij).  The result will be saved to 
				the 'coordinate_order' attribute in the resulting dataset.
			**kwargs:
				- 

		Returns:
			- A Shapely Polygon object representing the border coordinates as 
			either (latitude, longitude) or (x,y) pairs, depending on the 
			available variables in the dataset.
		"""
		from .ancillary import findattr

		# Check for already-processed border
		if hasattr(self, '_border'):
			if coordinate_order is not None:
				self.coordinate_order = coordinate_order
			return self._border

		# Check for associated instrument object
		if not hasattr(self, 'instrument'):
			raise ValueError("This dataset must be associated with an "
				"instrument in order to use this routine.")
		
		# Check for swath structure
		if self.product.structure != "swath":
			raise RuntimeError("This routine applies only to datasets with a "
				"swath structure.")
		
		# Set the geolocation boundaries for this dataset from the instrument 
		# object and return the result
		try:
			self._border = self.instrument.border(*args, dataset=self, \
				coordinate_order=coordinate_order, **kwargs)
			return self._border
		except:
			geo_prod_id = findattr(self, 'geo_product', None)
			if self.product.id == geo_prod_id:
				raise RuntimeError("Could not locate geolocation data in this " \
					"dataset.")
			elif geo_prod_id is None:
				raise RuntimeError("Could not locate geolocation data in this " \
					"dataset or in its associated geolocation product dataset.")
			geo_ds = self.cousin_dataset(geo_prod_id, **kwargs)
			if geo_ds is None:
				raise RuntimeError("Could not find associated geolocation " \
					"dataset to this dataset.")
			return geo_ds.border(*args, coordinate_order=coordinate_order, \
				**kwargs)
	
	# Method to find coincident datasets from other instruments
	def coincident(self, /, products, timedelta, **kwargs): 
		"""Finds coincident datasets from other instruments within a given time.

		Parameters:
			products: type=Product|str|list
				- A product or list of products from other instruments to search 
				for coincident datasets.
			timedelta: type=datetime.timedelta|dateutil.relativedelta.relativedelta|int
				- The time difference within which to search for coincident 
				datasets.  If an integer, will be assumed to be the number of 
				minutes.
			**kwargs:
				- 
		
		External Modules:
			- dateutil -- https://dateutil.readthedocs.io/
			- numpy -- https://numpy.org/

		Returns:
			- A list of `Dataset` objects (or file paths if `create` is `False`) 
			that are coincident within `timedelta` of this dataset.
		"""
		import datetime as dt
		from dateutil.relativedelta import relativedelta
		import numpy as np
		from .product import Product, load_product
		from .ancillary import iterable

		# Process products argument
		if not iterable(products):
			products = [products]
		products = [p if isinstance(p, Product) else load_product(p, **kwargs) \
			for p in products]
		for p in products:
			if not hasattr(p, 'instrument'):
				raise ValueError("All products must be associated with an "
					"instrument to search for coincident datasets.")
			if p.instrument == self.instrument:
				raise ValueError("Cannot search for coincident datasets from "
					"the same instrument.")
		
		# Process timedelta argument
		if isinstance(timedelta, int):
			timedelta = dt.timedelta(minutes=timedelta)
		elif not isinstance(timedelta, (dt.timedelta, relativedelta)):
			raise ValueError("'timedelta' must be an integer number of minutes, "
				"or a datetime.timedelta or dateutil.relativedelta.relativedelta "
				"object.")
		
		# Get start time of this dataset
		attrs = self.get_filename_attrs()
		if 'start_timestamp' in attrs:
			start_time = attrs['start_timestamp']
		elif ('start_date' in attrs or 'date' in attrs) and 'start_time' in \
		  attrs:
			start_time = dt.datetime.combine(attrs.get('start_date', \
				attrs['date']), attrs['start_time'])
		elif 'timestamp' in attrs:
			start_time = attrs['timestamp']
		elif 'start_time' in attrs:
			start_time = attrs['start_time']
		else:
			raise ValueError("Could not determine the start time of this dataset.")
		
		# Get end time of this dataset
		if 'end_timestamp' in attrs:
			end_time = attrs['end_timestamp']
		elif 'end_time' in attrs:
			if 'end_date' in attrs:
				end_time = dt.datetime.combine(attrs['end_date'], \
					attrs['end_time'])
			elif isinstance(start_time, dt.time):
				end_time = attrs['end_time']
			else:
				end_time = attrs['end_time']
				if end_time < start_time.time():
					end_time = dt.datetime.combine(start_time.date()+ \
						dt.timedelta(days=1), end_time)
				else:
					end_time = dt.datetime.combine(start_time.date(), end_time)
		elif hasattr(self.product, 'temporal_resolution'):
			end_time = start_time + self.product.temporal_resolution
		else:
			raise ValueError("Could not determine the end time of this dataset.")

		# Expand time range to search for coincident datasets
		start_time -= timedelta
		end_time += timedelta

		# Get border of this dataset
		border = self.border(**kwargs)
		if self.coordinate_order == 'ij':
			border_ij = np.asarray(border.exterior.coords)
			ccw = border.exterior.is_ccw
		else:
			border_ij = np.fliplr(border.exterior.coords)
			ccw = not border.exterior.is_ccw
		if not ccw:
			border_ij = border_ij[::-1]
		border_ij = [tuple(row) for row in border_ij]

		# Get datasets whose swath borders intersect this dataset
		results = []
		results_filenames = []
		for p in products:
			for file,_ in p.find_files(timestamp=dict(min=start_time, \
			  max=end_time, incl=True), polygon=border_ij, **kwargs):
				ds = p.load_dataset(file, **kwargs)
				if ds.border(**kwargs).intersects(border):
					results.append(ds)
					results_filenames.append(ds.file)
		
		# Return intersecting borders
		return results
	
	# Method to identify overlapping pixels between scans/frames of swath
	def overlapping_pixels(self, /, select='both', fraction=0, neighbors=80, \
	  **kwargs):
		"""Identifies overlapping pixels between scans/frames of swath.
		**NOT FINISHED - only select='front' is programmed; nothing returned.**

		Parameters:
			select: type=str, default='both'
				- The side of each frame to keep; one of 'front', 'back', or 
				'both'.
			fraction: type=int, default=0
				- The fraction of pixel overlap before triggering an exclusion.
			neighbors: type=, default=80
				- If specified, the value of the interpolant at each evaluation 
				point will be computed using only this many nearest data points. 
				All the data points are used by default.
			**kwargs:
				- scipy.interpolate.RBFInterpolator: smoothing, kernel, epsilon, 
				degree
		
		External Modules:
			- numpy -- https://numpy.org/
			- shapely -- https://shapely.readthedocs.io/

		Returns:
			- 
		"""
		import numpy as np
		from shapely import Point, MultiPoint, LineString, MultiLineString, \
			GeometryCollection
		from .instrument import WhiskbroomScanner, PushbroomScanner
		from .ancillary import iterable, findattr

		# Check for associated product
		if not hasattr(self, 'product'):
			raise ValueError("A product is not associated with this dataset, "
				"which is required for this method.")

		# Check for swath structure
		if not getattr(self.product, 'structure', None) != 'swath':
			raise ValueError("Overlapping pixels can only be identified for "
				"swath datasets.")
		
		# Sanitize the select input
		select = select.strip().lower()
		if select not in ['front', 'back', 'both']:
			raise ValueError("'select' must be one of 'front', 'back', or 'both'")
		
		# Get the scan/frame width
		width_vars = ['scan_width', 'frame_width']
		if hasattr(self, 'instrument'):
			if isinstance(self.instrument, WhiskbroomScanner):
				width_vars = ['scan_width']
			elif isinstance(self.instrument, PushbroomScanner):
				width_vars = ['frame_width']
		for width_var in width_vars:
			width = findattr(self, width_var, None)
			if width is not None:
				break
		if width is None:
			width_vars_str = ' or '.join([f"'{v}'" for v in width_vars])
			raise ValueError(f"Could not find the {width_vars_str} variable.")
		
		# Set the latitude and longitude values
		dims = self.set_geo()
		ialong_track,nalong_track = [(d['index'],d['size']) for d in \
			dims.values() if d.get('id') == 'along_track'][0]
		swath_width = [d['size'] for d in dims.values() if d.get('id') == \
			'across_track'][0]
		cross_track_ind = np.arange(-1, swath_width+2)		# extend by one pixel on each end
		
		# Get the cross-track nadir point in terms of pixels	
		nadir_point = getattr(self, 'scan_nadir_point', getattr(self, \
			'frame_nadir_point', getattr(self, 'swath_nadir_point', None)))
		if nadir_point is None:
			geo_product = findattr(self, 'geo_product', None)
			if geo_product is not None and not isinstance(geo_product, dict):
				geo_ds = self.cousin_dataset(geo_product)
				if geo_ds is not None:
					ilatname = findattr(geo_ds, 'latitude_name', group=[None, \
						'labels'])
					if ilatname is not None:
						ilats = geo_ds.extract(ilatname)
						nadir_point = getattr(ilats, 'scan_nadir_point', \
							getattr(ilats, 'frame_nadir_point', \
							getattr(ilats, 'swath_nadir_point', None)))
		if nadir_point is None:
			raise ValueError("Could not find the nadir point")
		nadir_point = nadir_point[1]

		# Function to get the array borders
		def _get_line_edges(frame, lines=None, **kwargs):
			# Set lines to all pixel edges along-track as default
			if lines is None:
				lines = np.arange(width+1)
			iterable_lines = iterable(lines)
			lines = np.atleast_1d(lines)

			# Get latitudes and longitudes of frame at given along-track locations
			if ialong_track == 0:
				i = lines
				j = cross_track_ind
			else:
				i = cross_track_ind
				j = lines
			s = np.s_[frame*width:(frame+1)*width]
			lats = grid_interp(self.latitude[s], i, j, **kwargs)
			lons = grid_interp(self.longitude[s], i, j, **kwargs)
			
			# Build list of LineString objects at each along-track line
			linestrings = []
			for i in range(lines.size):
				s = (i, slice(None))[::-1 if ialong_track else 1]
				linestrings.append(LineString(zip(lats[s], lons[s])))

			# Return LineString objects
			return linestrings if iterable_lines else linestrings[0]

		# Function to build list of points from Shapely objections
		def _extract_geoms(geom, pts=[]):
			if isinstance(geom, Point):
				pts.append(geom)
			elif isinstance(geom, MultiPoint):
				pts.extend(list(geom.geoms))
			elif isinstance(geom, LineString):
				pts.extend(list(geom.boundary))
			elif isinstance(geom, MultiLineString):
				for g in geom.geoms:
					pts.extend(list(g.boundary))
			elif isinstance(geom, GeometryCollection):
				for g in geom.geoms:
					_ = _extract_geoms(g, pts=pts)
			elif not geom.is_empty:
				raise TypeError(f"Could not discern the geom type ({type(geom)})")
			return pts

		# Identify overlapping pixels
		nframes = nalong_track // width
		for frame1 in range(nframes-1):
			frame2 = frame1 + 1
			if select == 'front':
				tested_edges = _get_line_edges(frame1, np.arange(1-fraction, \
					width+1-fraction, 1), neighbors=neighbors, **kwargs)
				test_edge = _get_line_edges(frame2, 0, neighbors=neighbors, \
					**kwargs)
				overlap_indices = []
				for tested_edge in tested_edges:
					overlap_indices.append([None, None])
					intersection = test_edge.intersection(tested_edge)
					pts = _extract_geoms(intersection)
					if not pts:
						overlap_indices[-1] = [0, swath_width-1]
					for i,(p1,p2) in enumerate(zip(tested_edge.coords[:-1], \
					  tested_edge.coords[1:])):
						segment = LineString([p1, p2])
						if test_edge.intersects(segment) and 0 < i < \
						  (swath_width-1):
							if (i-1) < nadir_point and overlap_indices[-1][0] \
							  is None or (i-1) > overlap_indices[-1][0]:
								overlap_indices[-1][0] = i-1
							elif (i-1) > nadir_point and overlap_indices[-1][1] \
							  is None or (i-1) < overlap_indices[-1][1]:
								overlap_indices[-1][1] = i-1
							elif (i-1) == nadir_point:
								overlap_indices[-1][:] = None
								break


################################### Dataset ###################################

################################### Granule ###################################
class Granule:
	"""Defines a granule object for an Earth Science Mission dataset.
	
	Class Variables:
		GRANULE_SPECIAL_DIMENSIONS -- List of special dimension designations.
	
	Functions:
		__init__ -- Initializes a granule object of an Earth Science Mission 
			product variable.
		__repr__ -- Returns the official string represenation of the granule.
		__str__ -- Returns the string represenation of the granule.
		__getitem__ -- Gets item from Granule object.
	
	Returns:
		- An object defining a granule for an Earth Science Mission dataset.
	"""

	# Class variables
	GRANULE_SPECIAL_DIMENSIONS = ('band', 'level', 'along_track', \
		'across_track')
	
	# Constructor method
	def __init__(self, /, var, long_name=None, description=None, dataset=None, 
	  s=slice(None), s0=slice(None), meta=None, attrs=None, dims=None, 
	  dim_map=None, dim_order=None, lats=None, lons=None, x=None, y=None, 
	  scan_width=None, swath_width=None, swath_length=None, pixel_offset=None, 
	  pixel_scale=None, ifov=None, gsd=None, prf=None, **kwargs):
		"""Initializes a granule object of an Earth Science Mission product 
		variable.
		
		Parameters:
			var: type=str|tuple|list|np.ndarray
				- Either a string representing the variable name (provided 
				'dataset' is provided), or a >=2D data array, or a two-element 
				tuple of the variable name and the data.
			long_name: type=str, default=None
				- The long name of the variable, to be saved as an attribute.
			description: type=str, default=None
				- The description of the variable, to be saved as an attribute.
			dataset: type=Dataset, default=None
				- The Dataset object associated with this variable's data.  It 
				will be included as an attribute, but can also be used to get 
				the data using the variable name, or to get attributes or 
				dimensions or dimension name mapping of the variable.
			s: type=slice|tuple, default=slice(None)
				- A slice object to be applied to the data.  A resulting slice 
				object will be saved as an attribute, which will also 
				incorporate 's0' if given.
			s0: type=slice|tuple, default=slice(None)
				- A slice object that has already been applied to the input 
				data, if given.  If a slice has been applied to the input data
				but this argument is not supplied, will result in the incorrect 
				slice object being saved as an attribute, and possibly the 
				wrong dimensions attribute as well.
			meta: type=dict, default=None
				- Information that will be added as attributes to this object.  
				This can be useful if e.g. 'ifov' and 'gsd' attributes in a 
				parent object are both dependent on 'spatial_resolution', but 
				the listed spatial resolution for the dataset/product has 
				mutiple options.  In this case, instead of specifying both 
				values explicitly, a 'spatial_resolution' key/value pair can be 
				included here, which will then determine which value of IFOV 
				and GSD is the correct one for this granule and set it 
				automatically.  Cannot include keys that match parameter names 
				from this method.
			attrs: type=dict|bool, default=None
				- Set to a dictionary of a set of attributes to save to the 
				Granule object, or True if 'var' and 'dataset' are supplied to 
				get all the attributes from the dataset.
			dims: type=dict|bool, default=None
				- Set to a dictionary of a set of dimensions to save to the 
				Granule object, or True if 'var' and 'dataset' are supplied to 
				get all the dimensions from the dataset.  The resulting 
				dimensions attribute will be altered according to the 's' 
				and/or 's0' arguments, and any dimensions that are eliminated 
				from splicing will have its index set to None.  If set to None 
				and 'var' name or 'dataset' is also None, will attempt to guess 
				which dimension is one of the standard dimensions listed under 
				the 'dim_map' description, and will rename the rest of the 
				available dimensions to "dim0", "dim1", etc.
			dim_map: type=dict, default=None
				- A dictionary to map the following standard dimension names to 
				those given in the dataset:
					band: the band/channel dimension
					level: the vertical level dimension
					along_track: the along-track dimension
					across_track: the across-track dimension
				- If these mappings aren't given, the program will search the 
				`dataset` object for attributes named "band_dimension_name", 
				"level_dimension_name", etc.  For each standard dimension that 
				is found and is present in the data, the name will be saved 
				both as an attribute of the Granuale object and under the 'id' 
				key for the given dimension in the 'dimensions' attribute.
			dim_order: type=bool|list|tuple|np.ndarray, default=None
				- A list of ordered dimension names or ID's to rearrange the 
				data to.  For remaining dimension names not included in the 
				list but included in the data, will place these remaining 
				dimensions where any given Ellipsis object is provided in the 
				list or else at the beginning of the list if no Ellipsis is 
				included.  The reordering of dimensions will be done after 
				slicing, and will be reflected in the saved 'dimensions' and 
				'slice' attributes.
			scan_width: type=int, default=None
				- The width in pixels of the instrument's scan.  If the 
				instrument is not a whiskbroom scanner, set to `None`.  Program 
				will throw an error if this argument is provided but any 
				associated instrument is not a WhiskbroomScanner object.  If 
				`None` and a product object is associated with the `dataset` 
				argument with an integer `scan_width` attribute, will use that 
				information to determine the granule's scan width for the given 
				variable.
			swath_width: type=int, default=None
				- The side-to-side width in pixels of the granule.  If `None` 
				and a product object is associated with the `dataset` argument 
				with an integer `swath_width` attribute, will use that 
				information to determine the granule's swath width for the 
				given variable.  Otherwise, if None and across-track dimension 
				name known and its dimension unchanged through slicing, will 
				set the swath width to the size of that dimension.
			swath_length: type=int, default=None
				The end-to-end length in pixels of the granule.  If None and a 
				product object is associated with the 'dataset' argument with an 
				integer 'swath_length' attribute, will use that information to 
				determine the granule's swath width for the given variable.  
				Otherwise, if None and along-track dimension name known and its 
				dimension unchanged through slicing, will set the swath length to 
				the size of that dimension.
			pixel_offset: type=float, default=None
				The pixel fraction that the granule grid is offset by.  If one 
				number, is assumed to be the offset only in the across-track 
				dimension.  If a two-element tuple, will be the (along-track, 
				across-track) offsets.  If None and a product object is associated 
				with the 'dataset' argument with a 'pixel_offset' attribute, will 
				use that information to determine the granule's pixel offset for the 
				given variable.
			pixel_scale: type=float, default=None
				The pixel scale (actual pixel dimensions on a grid) in radians. A 
				scalar will be broadcasted into a two-element vector of the form 
				[along-track, across-track].  If None and a product object is 
				associated with the 'dataset' argument with an 'pixel_scale' 
				attribute, will use that information to determine the granule's 
				pixel scale for the given variable.  If None and 'gsd' is set and 
				the geoid height is set on the platform, the pixel scale will be 
				calculated and set.  If both 'pixel_scale' and 'gsd' are set, the 
				platform state will be adjusted with the resulting geoid height.
			ifov: type=float, default=None
				The instantaneous field of view in radians. A scalar will be 
				broadcasted into a two-element vector of the form [along-track, 
				across-track].  If None and a product object is associated with the 
				'dataset' argument with an 'ifov' attribute, will use that 
				information to determine the granule's IFOV for the given variable.  
				If 'pixel_scale' is not set and both 'ifov' and 'gsd' are set, the 
				platform state will be adjusted with the resulting geoid height.
			gsd: type=float, default=None
				The ground sample distance (pixel resolution) at nadir at the geoid. 
				A scalar will be broadcasted into a two-element vector of the form 
				[along-track,across-track].  If None and a product object is 
				associated with the 'dataset' argument with a 'gsd' attribute, will 
				use that information to determine the granule's GSD for the given 
				variable.  If both 'pixel_scale' (or 'ifov' if 'pixel_scale' is not 
				set) and 'gsd' are set, the platform state will be adjusted with the 
				resulting geoid height.  If None and 'pixel_scale' is set and the 
				geoid height is set on the platform, the GSD will be calculated and 
				set.  If both 'pixel_scale' and 'gsd' are set, the platform state 
				will be adjusted with the resulting geoid height.
			prf: type=function, default=None
				The pixel response function of the optical system. The function 
				should take two arguments, the first being the along-track 
				coordinate and the second the across-track coordinate, which may 
				range from -1 to 2. The range 0 to 1 represents the edges of a 
				pixel, while -1 to 0 represents the neighboring pixel one one side 
				and 1 to 2 represents the neighboring pixel on the other side. The 
				output of the function should yield a value between 0 and 1, where 1 
				is full contribution of the signal and 0 is no contribution.  If 
				None and a product object is associated with the 'dataset' argument 
				with a 'prf' attribute, will use that information to determine the 
				granule's PRF for the given variable.
			lats: type=list|tuple|np.ndarray, default=None
				A 2D array of latitude values.  It's dimension order must match the 
				order of the along-track and across-track dimensions of the data 
				after any dimension reordering.  Must be None if 'y' argument is 
				provided.
			lons: type=list|tuple|np.ndarray, default=None
				A 2D array of longitude values.  It's dimension order must match the 
				order of the along-track and across-track dimensions of the data 
				after any dimension reordering.  Must be None if 'x' argument is 
				provided.
			x: type=list|tuple|np.ndarray, default=None
				A 2D array of X-dimension values.  It's dimension order must match 
				the order of the along-track and across-track dimensions of the data 
				after any dimension reordering.  Must be None if 'lons' argument is 
				provided.
			y: type=list|tuple|np.ndarray, default=None
				A 2D array of Y-dimension values.  It's dimension order must match 
				the order of the along-track and across-track dimensions of the data 
				after any dimension reordering.  Must be None if 'lats' argument is 
				provided.

		External modules:
			- numpy -- https://numpy.org/
		"""
		from types import NoneType
		import warnings
		import inspect
		import numpy as np
		from .config import SELECTABLE_SPECIFICATIONS
		from .instrument import WhiskbroomScanner
		from .ancillary import iterable, assert_iterable, assert_slice, \
			findattr, set_attr_by_key, set_nadir_point

		# Check input formats
		assert isinstance(var, str) or iterable(var) and \
			((isinstance(var[0], str) and iterable(var[1]) and \
			len(np.array(var[1]).shape) >= 2) if (isinstance(var, tuple) and \
			len(var) == 2) else len(np.array(var).shape) >= 2)
		assert isinstance(long_name, (NoneType, str))
		assert isinstance(description, (NoneType, str))
		assert isinstance(dataset, (NoneType, Dataset))
		s = assert_slice(s)
		s0 = assert_slice(s0)
		assert isinstance(meta, (NoneType, dict))
		assert isinstance(attrs, (NoneType, dict, bool))
		assert isinstance(dims, (NoneType, dict, bool))
		assert isinstance(dim_map, (NoneType, dict))
		assert isinstance(dim_order, (NoneType, bool, list, tuple, np.ndarray))
		assert isinstance(lats, (NoneType, str, bool)) or isinstance(lats, \
			(list, tuple, np.ndarray)) and len(np.array(lats).shape) == 2
		assert isinstance(lons, (NoneType, str, bool)) or isinstance(lons, \
			(list, tuple, np.ndarray)) and len(np.array(lons).shape) == 2
		assert isinstance(x, (NoneType, str, bool)) or isinstance(x, \
			(list, tuple, np.ndarray)) and len(np.array(x).shape) == 2
		assert isinstance(y, (NoneType, str, bool)) or isinstance(y, \
			(list, tuple, np.ndarray)) and len(np.array(y).shape) == 2
		assert not (lats is not None and y is not None)
		assert not (lons is not None and x is not None)
		assert scan_width is None or isinstance(scan_width, (int, np.integer)) \
			and scan_width > 0
		assert swath_width is None or isinstance(swath_width, (int, np.integer)) \
			and swath_width > 0
		assert swath_length is None or isinstance(swath_length, \
			(int, np.integer)) and swath_length > 0
		assert_iterable(pixel_offset, (list, tuple, np.ndarray), (float, int), \
			size=2)
		assert_iterable(pixel_scale, (list, tuple, np.ndarray), (float, int), \
			item_test=lambda x: x > 0, size=2)
		assert_iterable(ifov, (list, tuple, np.ndarray), (float, int), \
			item_test=lambda x: x > 0, size=2)
		assert_iterable(gsd, (list, tuple, np.ndarray), (float, int), \
			item_test=lambda x: x > 0, size=2)
		assert prf is None or callable(prf) and 0 <= prf(0.5, 0.5) <= 1
		
		# Set variable, long name, description, and get data
		if isinstance(var, tuple) and len(var) == 2:
			self.id,data = var
		elif isinstance(var, str):
			self.id = var
			data = dataset.read(var=var)
			if s0 not in [None, slice(None)]:
				raise ValueError("Cannot include 's0' when reading the "
					"original data from the dataset.")
		else:
			self.id = None
			data = var
		self.id = self.id.strip()
		if long_name:
			self.long_name = long_name.strip()
		elif dataset is not None:
			try:
				self.long_name = dataset.read(var=var, attr='long_name')
			except:
				pass
		if description:
			self.description = description.strip()
		elif dataset is not None:
			try:
				self.description = dataset.read(var=var, attr='description')
			except:
				pass
		data = np.atleast_2d(data)

		# Set dataset object
		if dataset is not None:
			self.dataset = dataset
			if hasattr(dataset, 'product'):
				self.product = dataset.product
				if hasattr(self.product, 'instrument'):
					self.instrument = self.product.instrument
					if hasattr(self.instrument, 'platform'):
						self.platform = self.instrument.platform

		# Check for swath structure in product
		if hasattr(self, 'product') and hasattr(self.product, 'structure'):
			if self.product.structure != 'swath':
				raise ValueError("The associated product has a non-swath "
					"structure which is incompatible with the Granule class.")

		# Update instrument info
		if meta:
			params = [param.name for param in \
				inspect.signature(Granule.__init__).parameters.values()]
			for k,v in meta.items():
				if k not in params:
					setattr(self, k, v)

		# Set attributes
		if attrs is None:
			attrs = bool(self.id is not None and dataset is not None)
		if attrs is True:
			if self.id is None:
				raise ValueError("Need to include 'var' name if 'attrs' is set to True.")
			if dataset is None:
				raise ValueError("Need to include 'dataset' if 'attrs' is set to True.")
			attrs = dataset.read(var=self.id, attr=True)
		if attrs:
			self.attributes = attrs

		# Set dimensions
		if dims is True or dims is None and self.id is not None and dataset is \
		  not None:
			if self.id is None:
				raise ValueError("Need to include 'var' name if 'dims' is set "
					"to True.")
			if dataset is None:
				raise ValueError("Need to include 'dataset' if 'dims' is set "
					"to True.")
			dims = dataset.read(var=self.id, dim=True)
		elif dims is None:
			if s0 not in [None, slice(None)]:
				raise ValueError("Cannot include 's0' without 'dims' or access "
					"to dimensions through the dataset.")
			ndims = len(data.shape)
			ndims_extra = max(0, ndims-4)
			iband = None
			ilevel = None
			if ndims >= 4:
				iband,ilevel = np.argsort(data.shape[-4:])[:2]+ndims_extra
			elif ndims >= 3:
				iband = np.argmin(data.shape[-3:])+ndims_extra
			itrack,iscan = [i for i in range(ndims_extra, ndims) if i not in \
				[iband,ilevel]]
			dims = dict()
			for i in range(ndims):
				dim_id = "band" if i == iband else "level" if i == ilevel else \
					"along_track" if i == itrack else "across_track" if i == \
					iscan else f"dim{i}"
				dims[dim_id] = dict(index=i, size=data.shape[i])
			dim_map = {k:k for k in self.GRANULE_SPECIAL_DIMENSIONS}
		
		# Function to position dimensions of sliced array
		def _get_new_dims(ind):
			# dims_new = [i for i in range(len(ind)) if isinstance(ind[i], \
			# 	np.ndarray)]
			dims_new = [j for j,i in enumerate(ind) if iterable(i) or \
				isinstance(i, slice) or i is None]
			return {idim: dims_new.index(idim) if idim in dims_new else None \
				for idim in range(len(ind))}
		
		# Function to change dimensions for sliced array
		def _change_dims(ind):
			dims_new = _get_new_dims(ind)
			for d in dims.values():
				size_new = ind[d['index']].size
				if size_new < d['size']:
					if 'original_size' not in d:
						d['original_size'] = d['size']
					d['size'] = size_new
					if 'coord' in d:
						d['coords'] = d['coords'][ind[d['index']]]
				index_new = dims_new[d['index']]
				if index_new != d['index']:
					if 'original_index' not in d:
						d['original_index'] = d['index']
					d['index'] = index_new

		# Reorganize dimensions according to pre-slicing of the input data
		if s0 not in [None, slice(None)]:
			if dims is None:
				raise ValueError("Cannot include 's0' without 'dims' or access "
					"to dimensions through the dataset.")
			shape0 = tuple(d['size'] for d in sort_dims(dims))
			s0 = full_slice(s0, shape0)
			si0 = slice_to_array(s0, shape0)
			_change_dims(si0)
		else:
			si0 = None

		# Slice data and reorganize dimensions
		if s not in [None, slice(None)]:
			shape = data.shape
			data = data[s]
			s = full_slice(s, shape)
			si = slice_to_array(s, shape)
			_change_dims(si)
			if si0 is None:
				self.slice = s
			else:
				s2 = tuple(s0)
				dims_new = _get_new_dims(si0)
				for i0,i in dims_new:
					if i0 is None:
						continue
					elif i is None:
						s2[i0] = si0[i0][si[i]]
					else:
						s0_step = 1 if s0.step is None else s0.step
						s_step = 1 if s.step is None else s.step
						s2[i0] = slice(si0[i0][si[i][0]], \
							si0[i0][si[i][-1]]+s0_step, s0_step*s_step)
		else:
			si = None
			if si0 is not None:
				self.slice = s0
			else:
				self.slice = full_slice(slice(None), data.shape)

		# Set dimension names
		dims_set = set(dims)
		for dim_var in self.GRANULE_SPECIAL_DIMENSIONS:
			dim_name = None
			if dim_map:
				if dim_var in dim_map:
					dim_name = dim_map[dim_var]
			else:
				dim_name = findattr(self, f"{dim_var}_dimension_name", None, \
					group=[None, 'labels'])
			if dim_name:
				dim_name = dims_set & (set(dim_name) if iterable(dim_name) \
					else {dim_name})
				if len(dim_name) == 1:
					dim_name = dim_name.pop()
					setattr(self, f'{dim_var}_dimension_name', dim_name)
					dims[dim_name]['id'] = dim_var
		
		# Rearrange dimensions
		if dim_order is True:
			dim_order = [name for name in self.GRANULE_SPECIAL_DIMENSIONS if \
				hasattr(self, f"{name}_dimension_name")]
		if dim_order is not None:
			dim_order = list(dim_order)
			iellipsis = dim_order.index(Ellipsis) if Ellipsis in dim_order\
				else None
			dims_sorted = sort_dims(dims)
			dims_extra = [dims_sorted[i]['name'] for i in range(len(dims)) if \
				dims_sorted[i]['name'] not in dim_order and \
				dims_sorted[i].get('id', None) not in dim_order]
			if iellipsis is not None:
				dim_order[iellipsis:iellipsis+1] = dims_extra
			else:
				dim_order = dims_extra + dim_order
			dim_order = [name if name in dims else getattr(self, \
				f"{name}_dimension_name", name) if name in \
				self.GRANULE_SPECIAL_DIMENSIONS else None for name in dim_order]
			dim_order = [name for name in dim_order if name is not None and \
				dims[name]['index'] is not None]
			dim_order = [dims[name]['index'] for name in dim_order]
			if set(dim_order) != set(range(len(data.shape))):
				raise ValueError("'dim_order' must have the same or less "
					"number of unique elements than the resulting data array")
			data = data.transpose(dim_order)
			self.slice = tuple(np.array(self.slice)[dim_order])
			for d in dims:
				if d['index'] is not None:
					d['index'] = dim_order.index(d['index'])

		# Set data and dimensions
		self.data = data
		self.shape = data.shape
		if dims:
			self.dimensions = dims

		# Set geolocation product if single product not previously selected
		set_attr_by_key(self, 'geo_product', change=True, value=True, \
			empty=False, silent=True)

		# Set selected product attributes
		for attr_name in SELECTABLE_SPECIFICATIONS:
			set_attr_by_key(self, attr_name, change=False, value=True, \
				empty=False, silent=True)
		
		# Save scan width
		if scan_width is not None:
			if hasattr(self, 'instrument') and not isinstance(self.instrument, \
			  WhiskbroomScanner):
				raise ValueError("Only a WhiskbroomScanner object can have a "
					"scan width.")
			self.scan_width = int(scan_width)						# [pixels]

		# Save swath width
		if swath_width is not None:
			self.swath_width = int(swath_width)						# [pixels]
		elif not hasattr(self, 'swath_width') and hasattr(self, \
		  'across_track_dimension_name') and hasattr(self, 'slice'):
			dims_new = {v:k for k,v in _get_new_dims(self.slice).items() if v \
				is not None}
			i0 = dims_new[dims[self.across_track_dimension_name]['index']]
			if self.slice[i0] in [slice(None), None]:
				d = dims[self.across_track_dimension_name]
				k = 'original_size' if 'original_size' in d else 'size'
				self.swath_width = d[k]
			elif var is not None and dataset is not None:
				dims0 = dataset.read(var=var, dim=True)
				self.swath_width = dims0[self.across_track_dimension_name]['size']

		# Save swath length
		if swath_length is not None:
			self.swath_length = int(swath_length)					# [pixels]
		elif not hasattr(self, 'swath_length') and hasattr(self, \
		  'along_track_dimension_name') and hasattr(self, 'slice'):
			dims_new = {v:k for k,v in _get_new_dims(self.slice).items() if v \
				is not None}
			i0 = dims_new[dims[self.along_track_dimension_name]['index']]
			if self.slice[i0] in [slice(None), None]:
				d = dims[self.along_track_dimension_name]
				k = 'original_size' if 'original_size' in d else 'size'
				self.swath_length = d[k]
			elif var is not None and dataset is not None:
				dims0 = dataset.read(var=var, dim=True)
				self.swath_length = dims0[self.along_track_dimension_name]['size']

		# Save number of scans
		if hasattr(self, 'swath_length') and hasattr(self, 'scan_width'):
			self.scans = self.swath_length//self.scan_width + \
				int(bool(self.swath_length % self.scan_width))

		# Save the pixel offset
		if pixel_offset is not None:
			self.pixel_offset = tuple(pixel_offset) if iterable(pixel_offset) \
				else pixel_offset

		# Save pixel scale, IFOV, ground sample distance (GSD), and elevation
		if pixel_scale is not None:
			self.pixel_scale = tuple(pixel_scale) if iterable(pixel_scale) \
				else pixel_scale
		if ifov is not None:
			self.ifov = tuple(ifov) if iterable(ifov) else ifov
		if gsd is not None:
			self.gsd = tuple(gsd) if iterable(gsd) else gsd
		platform = getattr(self, 'platform', None)
		elev = platform and getattr(platform, 'elevation', None)
		if platform and hasattr(self, 'pixel_scale') and hasattr(self, 'gsd'):
			if elev is not None:
				warnings.warn("\033[38;5;208mPlatform elevation is being " \
					"recalculated based on the provided 'pixel_scale' and "
					"'gsd' values.\033[0m", stacklevel=2)
			if iterable(self.pixel_scale) or iterable(self.gsd):
				elev = np.array(self.gsd)/np.array(self.pixel_scale)
				if not np.isclose(*elev):
					raise ValueError("'pixel_scale' and 'gsd' in 2D must "
						"result in the same altitude calculation in both "
						"dimensions.")
				elev = elev.mean().item()
			else:
				elev = self.gsd/self.pixel_scale
			platform.set_state(elev=elev, reset=False)
		elif elev is not None and hasattr(self, 'pixel_scale'):
			self.gsd = (elev*np.array(self.pixel_scale)).tolist() if \
				iterable(self.pixel_scale) else elev*self.pixel_scale
		elif elev is not None and hasattr(self, 'gsd'):
			self.pixel_scale = (np.array(self.gsd)/elev).tolist() if \
				iterable(self.gsd) else self.gsd/elev

		# Save the pixel response function (PRF)
		if prf is not None:
			self.prf = prf

		# Save latitude and longitude arrays
		if lats is not None or lons is not None:
			if not hasattr(self, 'dimensions'):
				raise ValueError("In order to include geolocation data, the "
					"granule dimensions need to be positively identified. Use "
					"the 'dims' argument to provide this information.")
			if not hasattr(self, 'along_track_dimension_name') or not \
			  hasattr(self, 'across_track_dimension_name'):
				raise ValueError("In order to include geolocation data, the "
					"along-track and across-track dimensions need to be "
					"positively identified. Use the 'dim_map' argument to "
					"provide this information.")
			along_track_dim = dims[self.along_track_dimension_name]
			across_track_dim = dims[self.across_track_dimension_name]
			k0 = 'original_size' if 'original_size' in along_track_dim else \
				'size'
			k1 = 'original_size' if 'original_size' in across_track_dim else \
				'size'
			var_geo_dims0 = (along_track_dim[k0], across_track_dim[k1])[::1 if \
				along_track_dim['index'] < across_track_dim['index'] else -1]
			var_geo_dims = (along_track_dim['size'], across_track_dim['size']) \
				[::1 if along_track_dim['index'] < across_track_dim['index'] \
				else -1]
		def _check_geo_dims(g):
			if not hasattr(g, 'dimensions') or len(g.dimensions) != 2 or \
			  not hasattr(g, 'along_track_dimension_name') or not hasattr(g, \
			  'across_track_dimension_name'):
				return None
			geo_dims = (g.dimensions[g.along_track_dimension_name]['size'], \
				g.dimensions[g.across_track_dimension_name]['size'])[::1 if \
				g.dimensions[g.along_track_dimension_name]['index'] < \
				g.dimensions[g.across_track_dimension_name]['index'] else -1]
			return geo_dims == var_geo_dims0
		def _get_geo_var(ds, var_name):
			try:
				# geo_dims = ds.read(var=var_name, dim=True)
				g = Granule(var_name, dataset=ds, dim_map=dim_map, **kwargs)
			except:
				return None
			if _check_geo_dims(g):
				s = [slice(None)]*2
				s[g.dimensions[g.along_track_dimension_name]['index']] = \
					self.slice[self.dimensions[self.along_track_dimension_name] \
					['index']]
				s[g.dimensions[g.across_track_dimension_name]['index']] = \
					self.slice[self.dimensions \
					[self.across_track_dimension_name]['index']]
				geo_data = np.atleast_2d(ds.extract(var_name, tuple(s)))
				if np.sign(g.dimensions[g.along_track_dimension_name]['index'] - \
				  g.dimensions[g.across_track_dimension_name]['index']) != \
				  np.sign(self.dimensions[self.along_track_dimension_name]['index'] - \
				  self.dimensions[self.across_track_dimension_name]['index']):
					geo_data = geo_data.T
				return geo_data
			return None
		loc_vars = [
			('lats', lats, 'latitude', ['latitudes', 'latitude', 'Latitudes', 
				'Latitude', 'LATITUDES', 'LATITUDE', 'lats', 'lat']), 
			('lons', lons, 'longitude', ['longitudes', 'Longitude', 'Longitudes', 
				'Longitude', 'LONGITUDES', 'LONGITUDE', 'lons', 'lon']),
			('x', x, 'x', ['x', 'X']),
			('y', y, 'y', ['y', 'Y']),
		]
		for var_name,var_value,attr_name,search_names in loc_vars:
			if isinstance(var_value, str) or var_value is True:
				for iloop in range(2):
					try:
						geo_product = findattr(self, 'geo_product')
						ds = dataset.cousin_dataset(geo_product, **kwargs) if \
							iloop else dataset
					except:
						continue
					if isinstance(var_value, str):
						if ds is None:
							raise ValueError("'dataset' must be provided if "
								f"'{var_name}' is a string.")
						# setattr(self, attr_name, np.atleast_2d(dataset.extract( \
						# 	var_value.strip(), self.slice)))
						# var_value = np.atleast_2d(ds.extract(var_value.strip(), \
						# 	self.slice))
						var_value = _get_geo_var(ds, var_value.strip())
					elif var_value is True:
						if ds is None:
							raise ValueError("'dataset' must be provided if '"
								f"{var_name}' is True.")
						for search_name in search_names:
							if search_name in ds:
								# setattr(self, attr_name, np.atleast_2d(dataset.extract( \
								# 	search_name, self.slice)))
								# search_var_dims = dataset.read(var=search_name, dim=True)
								# if _check_geo_dims(search_var_dims):
								# 	var_value = np.atleast_2d(dataset.extract( \
								# 		search_name, self.slice))
								var_value = _get_geo_var(ds, search_name)
								if var_value is None:
									var_value = True
								break
						else:
							if iloop:
								warnings.warn("\033[38;5;208mCould not find "
									f"{attr_name} data.\033[0m", stacklevel=2)
					if var_value is not None and var_value is not True:
						break
				if isinstance(var_value, str) or var_value is True:
					var_value = None
			elif var_value is not None:
				s = [slice(None)]*2
				i = self.dimensions[self.along_track_dimension_name]['index']
				j = self.dimensions[self.across_track_dimension_name]['index']
				if i > j:
					i,j = j,i
				s2 = (self.slice[i], self.slice[j])
				var_value = np.atleast_2d(var_value[s2])
			if var_value is not None:
				if var_value.shape != var_geo_dims:
					raise ValueError(f"'{var_name}' does not have the shape "
						f"{var_geo_dims}")
				setattr(self, attr_name, var_value)

		# Set nadir point in terms of pixel indices
		set_nadir_point(self)
	
	# Magic method for representation output
	def __repr__(self):
		"""Returns the official string represenation of the granule.

		Returns:
			- The official string represenation of the granule.
		"""
		class_path = '.'.join([self.__module__, self.__class__.__qualname__])
		ds_str = ":"+self.dataset.path if hasattr(self, 'dataset') else ""
		return f"<{class_path}({self.id}{ds_str})>"
	
	# Magic method for string output
	def __str__(self):
		"""Returns the string represenation of the granule.

		Returns:
			- The string represenation of the granule.
		"""
		class_name = self.__class__.__name__
		ds_str = ", "+self.dataset.file if hasattr(self, 'dataset') else ""
		return f"{class_name}({getattr(self, 'long_name', self.id)}{ds_str})"

	# Magic method to index the granule object
	def __getitem__(self, /, index):
		"""Get item from Granule object.
		
		Parameters:
			index: type=slice|int|tuple|list
				- A scalar or series of slice or index objects for indexing the 
				Granule data.
		
		Returns:
			The Granule data indexed by the given `index`.
		"""
		from .ancillary import assert_slice

		# Return the indexed data
		index = assert_slice(index)
		return self.data[index]
	
	# Method to get the corners of the loaded data
	"""
	def data_corners():
		pass
	"""
################################### Granule ###################################

##################################### Grid #####################################
class Grid():
	# Class variables
	GRID_SPECIAL_DIMENSIONS = ('level', 'horizontal', 'vertical') #'longitude', 'latitude'


	# Magic method for representation output
	# def __repr__(self):
	# 	class_path = '.'.join([self.__module__, self.__class__.__qualname__])
	# 	ds_str = ", "+self.dataset.path if hasattr(self, 'dataset') else ""
	# 	return f"<{class_path}({self.id}{ds_str})>"
	
	# Magic method for string output
	# def __str__(self):
	# 	class_name = self.__class__.__name__
	# 	ds_str = ", "+self.dataset.file if hasattr(self, 'dataset') else ""
	# 	return f"{class_name}({getattr(self, 'long_name', self.id)}{ds_str})"

##################################### Grid #####################################


#--------------------------------- FUNCTIONS ---------------------------------#

################################## decompress ##################################
def decompress(path):
	"""Decompresses files with common compression formats (zip, gzip, xz).
	
	Parameters:
		path: type=str|pathlib.Path
			- The path of the file to decompress.
	
	Returns:
		A buffer stream of the uncompressed file.
	"""
	from pathlib import Path
	import io

	# Get path and file name
	path = Path(path)
	file = path.name

	# Get last file extension and decompressed file name
	ext = ext if isinstance(ext:=path.suffixes, str) else ext[-1]
	decompressed_file = file.rstrip(f".{ext}")
	ext = ext.lower()
	if ext not in ['zip', 'gzip', 'xz', '7z']:
		return None

	# Open compressed file
	with open(path, 'rb') as f:
		# Read contents of compressed file
		compressed = f.read()

		# Decompress contents with appropriate tool
		if ext == 'zip':
			import zipfile
			with zipfile.ZipFile(path, 'r') as zf:
				decompressed = zf.read(decompressed_file)
		elif ext == 'gzip':
			import gzip
			decompressed = gzip.decompress(compressed)
		elif ext == 'xz':
			import lmza
			decompressed = lzma.decompress(compressed)
		# elif ext == '7z':
		# 	import py7zr
		# 	from py7zr.io import BytesIOFactory		#, Py7zBytesIO
		# 	with py7zr.SevenZipFile(path, mode='r') as zf:
		# 		with zf.extract(decompressed_file, factory=BytesIOFactory) as zf2:
		# 			decompressed = zf2.read()
	
	# Get binary/buffer stream and return
	binary_io = io.BytesIO(decompressed)
	buffer_io = io.BufferedReader(binary_io)
	return buffer_io
################################## decompress ##################################

################################ get_path_name ################################
def get_path_name(path):
	"""Extracts the name for a given dataset object's path.
	
	Parameters:
		path: type=str
			- The path for a given dataset object.
	
	Returns:
		- The name of the dataset object's path.
	"""
	from pathlib import PurePosixPath
	from .ancillary import iterable

	# Return path name(s)
	if iterable(path):
		return [PurePosixPath(p).name for p in path]
	else:
		return PurePosixPath(path).name
################################ get_path_name ################################

################################## sort_dims ##################################
def sort_dims(dims):
	"""Orders a dictionary of dimensions for a variable into a list sorted by 
	index.
	
	Parameters:
		dims: type=dict
			- A dictionary of all dimension dictionary objects for a given 
			variable with dimension IDs as the keys and 'index' included as a 
			key in each dimension's dictionary.
	
	Returns:
		- A list of sorted dimension dictionary objects in order of their 
		indices.
	"""

	# Sort dimensions into list by index
	dims_list = [{**dict(name=k), **v} for k,v in dims.items() if v['index'] \
		is not None]
	dims_list = sorted(dims_list, key=lambda d: d['index'])

	# Delete index from data
	for d in dims_list:
		del d['index']

	# Return sorted list of dimensions
	return dims_list
################################## sort_dims ##################################

################################ broadcast_prep ################################
# Function to prepare data for broadcasting by adding new axes to align to axis
def broadcast_prep(data, shape, axis=-1, full=False):
	"""Prepares an array to be broadcasted to a given shape, aligned at a given 
	axis.
	
	Parameters:
		data: type=list|tuple|np.ndarray|int|float
			- An array (scalar's allowed) to be adjusted for broadcasting 
			against another array with `shape`.
		shape: type=tuple|int
			- The shape of the array that `data` will be broadcasted to.  If an 
			integer, will be taken as the number of dimensions (i.e. 
			`len(shape)`).
		axis: type=int, default=-1
			- The dimension index of 'shape' that the last dimension of `data` 
			corresponds to.
		full: type=bool, default=False
			- If True, will add dimensions to the front of `data` to match the 
			dimensions of `shape`.
	
	External Modules:
		- numpy -- https://numpy.org/
	
	Returns:
		- The `data` argument with dimensions added to prepare for broadcasting 
		to an array with `shape`.
	"""
	import numpy as np
	from .ancillary import iterable

	# Return scalar if not iterable
	if not iterable(data):
		return data.item() if hasattr(data, 'item') else data
	
	# Add new axes to align to axis and return
	else:
		if not isinstance(data, np.ndarray):
			data = np.array(data)
		ndim = len(tuple(shape)) if iterable(shape) else int(shape)
		if axis < 0:
			axis = ndim+axis
		i = (...,)+(None,)*(ndim-axis-1)
		if full:
			n = len(i)
			i = (None,)*(ndim-n)+i
		return data[i]
################################ broadcast_prep ################################

################################## full_slice ##################################
def full_slice(s, shape):
	"""Fills in a partial slice object with slices for unspecified dimensions.
	
	Parameters:
		s: type=slice|int|tuple|list
			- A slice object.
		shape: type=tuple
			- The shape of the data to which the slice is applied.
	
	Returns:
		- A tuple of slices for each dimension of the data shape.
	"""
	from types import EllipsisType
	from .ancillary import assert_slice

	# Check for valid input types and dimensions
	s = assert_slice(s)
	# if not isinstance(s, (slice, int, tuple)) or isinstance(s, tuple) and not \
	#   all(isinstance(i, (slice, int, EllipsisType)) for i in s):
	# 	raise TypeError("Slice must be a slice object or tuple of slice objects.")
	if not isinstance(shape, tuple):
		raise TypeError("Shape must be a tuple representing the shape of the " \
			"data.")
	if (len(s) if isinstance(s, tuple) else 1) > len(shape):
		raise ValueError("The slice object must not have more dimensions than " \
			"the data.")

	# Convert non-tuple to tuple if single element
	if not isinstance(s, tuple):
		s = (s,)
	
	# Convert non-list iterables to list type
	# for i in range(len(s)):
	# 	if iterable(s[i]) and not isinstance(s[i], list):
	# 		s[i] = list(s[i])

	# Fill in missing dimensions
	if EllipsisType in s:
		i = s.index(EllipsisType)
		s = s[:i] + (slice(None),)*(len(shape)-len(s)+1) + s[i+1:]
	else:
		s += (slice(None),) * (len(shape)-len(s))

	# Return the full slice tuple
	return s
################################## full_slice ##################################

################################ slice_to_array ################################
def slice_to_array(s, shape):
	"""Converts a slice object to a set of arrays.
	
	Parameters:
		s: type=slice|int|tuple|list
			- A slice object.
		shape: type=tuple
			- The shape of the data to which the slice is applied.
	
	External Modules:
		- numpy -- https://numpy.org/
		
	Returns:
		- An array or set of arrays with the indices of the slice.
	"""
	import numpy as np

	# Fill in missing dimensions
	is_slice = not isinstance(s, tuple)
	s = full_slice(s, shape)

	# Return a tuple of arrays with the indices of the slice
	a = [np.arange(isize)[s[i]] for i,isize in enumerate(shape)]
	for i in range(len(a)):
		if a[i].size == 1:
			a[i] = a[i].item()
	a = tuple(a)
	return a[0] if is_slice else a
################################ slice_to_array ################################

#################################### ma_pad ####################################
def ma_pad(array, pad_width, *args, **kwargs):
	"""Pads an array (adds masked array functionality to numpy's pad function) - 
	can add this function to an imported numpy instance using the following:
		`import numpy as np`
		`from esm.data import ma_pad`
		`np.ma.pad = ma_pad`
	
	Parameters:
		array: type=array_like
			- The array to pad.
		pad_width: type=sequence|array_like|int
			- Number of values padded to the edges of each axis. ((before_1, 
			after_1), ... (before_N, after_N)) unique pad widths for each axis. 
			(before, after) or ((before, after),) yields same before and after 
			pad for each axis. (pad,) or int is a shortcut for before = after = 
			pad width for all axes.
		*args:
			- Accepts additional arguments for the following functions:
				- numpy.pad: mode
		**kwargs:
			- Accepts additional keyword arguments for the following functions:
				- numpy.pad: mode, stat_length, constant_values, end_values, 
				reflect_type
	
	External Modules:
		- numpy -- https://numpy.org/
	
	Returns:
		- Padded masked array of rank equal to `array` with shape increased 
		according to `pad_width`.
	"""
	import numpy as np

	# Save keyword arguments for numpy.pad function defining the mask
	pad_kwargs = kwargs.copy()
	if args:
		pad_kwargs['mode'] = args[0]
	if 'constant_values' in pad_kwargs:
		pad_kwargs['constant_values'] = False
	if 'mode' in pad_kwargs:
		if pad_kwargs['mode'] == 'linear_ramp':
			pad_kwargs['mode'] = 'edge'
		elif pad_kwargs['mode'] in ['maximum', 'mean', 'median', 'minimum']:
			pad_kwargs['mode'] = 'constant'
		elif pad_kwargs['mode'] == 'empty':
			pad_kwargs['mode'] = 'constant'
			pad_kwargs['constant_values'] = True
		elif pad_kwargs['mode'] in ['reflect', 'symmetric'] and \
		  'reflect_type' in pad_kwargs and pad_kwargs['reflect_type'] == 'odd':
			def ma_pad_func(vector, pad_width, iaxis, kwargs):
				vector[:pad_width[0]] = vector[0] | vector[1:pad_width[0]+ \
					int(kwargs['mode'] == 'reflect')]
				vector[-pad_width[1]:] = vector[-1] | vector[-pad_width[1]- \
					int(kwargs['mode'] == 'reflect'):-1]
			pad_kwargs['mode'] = ma_pad_func
	
	# Return padded masked array
	return np.ma.masked_where(np.pad(np.ma.getmaskarray(array), pad_width, \
		**pad_kwargs), np.pad(array, pad_width, **kwargs))
#################################### ma_pad ####################################

################################# grid_interp #################################
def grid_interp(data, *indices, grid=True, **kwargs):
	"""Interpolating or extrapolating structured data in multiple dimensions at 
	regular or irregular locations.
	
	Parameters:
		data: type=float|int
			- The reference data array.
		*indices: type=int|float
			- Arrays of indices, where the number of arrays corresponds to the 
			number of dimensions of `data`.  The values of indices corresponds 
			to the location in the `data` array for the given axis.  These 
			arrays can be either 1D, which will then be broadcasted to the 
			number of dimensions of `data`, or greater than 1D in which case it 
			must match the shape of the resulting output array exactly.
		grid: type=bool, default=True
			- If `True`, will assume any 1D indices arrays will be for the given 
			axes and broadcast it across all dimensions; if `False`, will assume 
			any 1D indices arrays will be for single points in an irregular 
			grid.
		**kwargs:
			- Accepts additional keyword arguments for the following functions:
				- scipy.interpolate.RBFInterpolator: neighbors, smoothing, 
				kernel, epsilon, degree
	
	External Modules:
		- numpy -- https://numpy.org/
		- scipy -- https://scipy.org/
	
	Returns:
		- Interpolated or extrapolated values for a given `data` array at the 
		given `indices`.
	"""
	import numpy as np
	from scipy.interpolate import RBFInterpolator

	# Format inputs and check for agreement in number of dimensions
	data = np.ma.masked_invalid(data)
	indices = [np.array(i) for i in indices]
	ndims = len(data.shape)
	if ndims != len(indices):
		raise ValueError(f"The number of dimensions of the input data ({ndims}) "
			f"does not match the number of 'indices' arrays ({len(indices)})")
	
	# Check for consistent shapes of indices arrays
	dim_ndims = [len(i.shape) for i in indices]
	if max(dim_ndims) > 1:
		if grid:
			raise ValueError("When 'grid' is True, the 'indices' arrays must be 1D.")
		dim_ind = max(dim_ndims)
	elif grid:
		dim_ind = tuple(i.size for i in indices)
	else:
		dim_ind = (indices[0].size,)
	if not all(ind.shape == dim_ind if len(ind.shape) > 1 else ind.size == \
	  dim_ind[i if grid else 0] for i,ind in enumerate(indices)):
		raise ValueError("The 'indices' arrays do not have matching shapes.")

	# Get full set of indices of output data
	if ndims == 1:
		indices = indices[0]
	elif not grid:
		pass
	elif max(dim_ndims) == 1:
		indices = np.meshgrid(*indices)
	elif 1 in dim_ndims:
		ones = np.ones(dim_ind, dtype=int)
		for i,ind in enumerate(indices):
			if dim_ndims[i] == 1:
				indices[i] = ones*broadcast_prep(ind, dim_ind, i)
	if ndims > 1:
		indices = list(zip(i.ravel() for i in indices))
	
	# Return interpolated/extrapolated values at given indices
	rbfi = RBFInterpolator(list(zip(*np.where(~data.mask))), data.compressed(), \
		**kwargs)
	return rbfi(indices).reshape(dim_ind)
################################# grid_interp #################################

################################ pixel_outlines ################################
"""
def pixel_outlines(data, ifov=None, pixel_scale=None, **kwargs):
	import numpy as np
	# from scipy.interpolate import RBFInterpolator
	from .ancillary import iterable

	# def pad_with(vector, iaxis_pad_width, iaxis, kwargs):
	# 	pass
	# lats = ma_pad(lats, 1, 'empty')
	# lons = ma_pad(lons, 1, 'empty')

	# 
	ifov = np.array(ifov) if iterable(ifov) else np.array([ifov]*2)
	pixel_scale = np.array(pixel_scale) if iterable(pixel_scale) else np.array([pixel_scale]*2)
	scale = ifov / pixel_scale
	i0 = np.arange(.5)
	data = grid_interp(data, )
"""
################################ pixel_outlines ################################

#################################### planck ####################################
def planck(wavelength=None, temperature=None, radiance=None, \
  energy_density=False, variable='wavelength', angular=False, rtol=1e-10, \
  atol=0):
	"""Computes the blackbody radiance for a given wavelength and temperature, 
	or radiance or wavelength if given the other two parameters. Spectral energy 
	density can be substituted for radiance, and frequency and wavenumber can be 
	substituted for wavelength.  Angular values can also be used.
	
	Parameters:
		wavelength: type=float, default=None
			- The wavelength in meters if `variable` is 'wavelength'; otherwise 
			in Hz if 'frequency' or 1/m if 'wavenumber'.
		temperature: type=float, default=None
			- The blackbody temperature in Kelvin.
		radiance: type=float, default=None
			- The spectral radiance in W/m^2/sr/m if `variable` is 'wavelength'; 
			otherwise W/m^2/sr/Hz if 'frequency' or W/m^2/sr*m if 'wavenumber'. 
			Ignored if `wavelength` and `temperature` are given.
		energy_density: type=bool, default=False
			- If `True`, `radiance` parameter will be taken as spectral energy 
			density instead of radiance, or if `radiance` is `None`, will output 
			spectral energy density.
		variable: type=str, default='wavelength'
			- Set to the variable used to parameterize Planck's Law (effecting 
			both `wavelength` and `radiance` input parameters); one of: 
			'wavelength', 'frequency' or 'wavenumber'.
		angular: type=bool, default=False
			- If `True`, signifies that Planck's Law has been parameterized with 
			angular values, i.e. angular wavelength, angular frequency or 
			angular wavenumber.
		rtol: type=float, default=1e-10
			- The relative tolerance parameter in the following test for 
			equivalency between the target radiance and peak radiance for the 
			given temperature:
				abs(peak_radiance - radiance) <= atol + rtol * peak_radiance
			- This parameter is used when `temperature` and `radiance` are 
			given.
		atol: type=float, default=0
			- The absolute tolerance parameter. See equation given in `rtol` 
			description.
	
	External modules:
		- numpy -- https://numpy.org/
		- scipy -- https://scipy.org/
	
	Returns:
		- The spectral radiance (in units of W/m^2/sr/m) of the blackbody 
		defined by inputs `wavelength` and `temperature`.  If `radiance` is 
		given, either `wavelength` (in meters) or `temperature` (in Kelvin) must 
		also be given and the other will be solved for and returned.  If 
		`wavelength` is `None`, `temperature` and `radiance` must be scalars 
		since there can be two solutions for `wavelength`.  If `variable` is set 
		to 'frequency', then the output will be in units of W/m^2/sr/Hz, or Hz 
		if `temperature` and `radiance` are given.  If `variable` is set to 
		'wavenumber', then the output will be in units of W/m^2/sr*m, or 1/m if 
		`temperature` and `radiance` are given.  If `angular` is set to `True`, 
		then units will be in m/rad and W/m^2/sr/m*rad for `variable`=
		'wavelength', or rad/s and W/m^2/sr/Hz/rad for `variable`='frequency', 
		or rad/m and W/m^2/sr*m/rad for `variable`='wavenumber'.  If 
		`energy_density` is set to `True`, the output will be spectral energy 
		density instead of radiance, whose radiance units will be multiplied by 
		rad/(m.Hz).
	"""
	import numpy as np
	from scipy.constants import c, h, hbar, k		# c [m/s], h [J*s], k [J/K]
	
	# Validate `variable` argument
	assert isinstance(variable, str)
	variable = variable.lower().strip()
	assert variable in ['frequency', 'wavelength', 'wavenumber']

	# Return temperature from inverse Planck function
	if temperature is None:
		# Format inputs
		wavelength = np.ma.array(wavelength)
		radiance = np.ma.array(radiance)

		# Convert from spectral energy density to radiance
		if energy_density:
			radiance *= c/(4*np.pi)

		# Convert inputs to non-angular wavelength and radiance
		if variable == 'frequency':
			frequency = wavelength
			if angular:
				frequency /= 2*np.pi							# [Hz]
				radiance *= 2*np.pi
			wavelength = c/frequency							# [m]
			radiance *= c/wavelength**2							# [W/m^2/sr/m]
		elif variable == 'wavelength':
			if angular:
				wavelength *= 2*np.pi							# [m]
				radiance /= 2*np.pi								# [W/m^2/sr/m]
		elif variable == 'wavenumber':
			wavenumber = wavelength
			if angular:
				wavenumber /= 2*np.pi							# [1/m]
				radiance *= 2*np.pi
			wavelength = 1/wavenumber							# [m]
			radiance *= 1/wavelength**2							# [W/m^2/sr/m]

		# Calculate temperature
		temperature = h*c/(wavelength*k*np.ma.log(2*h*c**2/ \
			(wavelength**5*radiance)+1))						# [K]
		
		# Format temperature for output and return
		if not np.iterable(temperature):
			temperature = float(temperature)
		elif not np.ma.is_masked(temperature):
			temperature = np.ma.getdata(temperature)
		return temperature
	
	# Return wavelength from Planck function curve fit
	elif wavelength is None:
		# Import additional necessary function
		from scipy.optimize import root_scalar
		
		# Check that temperature and radiance are scalars and positive
		assert np.isscalar(temperature) and temperature > 0
		assert np.isscalar(radiance) and radiance > 0

		# Build dictionary of parameters for multiple function calls
		kwargs = dict(energy_density=energy_density, variable=variable, \
			angular=angular)

		# Get appropriate parameterization of Wien's displacement constant and 
		# calculate wavelength (or frequency or wavenumber) at peak
		if variable == 'wavelength':
			from scipy.constants import Wien as b				# [m.K]
			wlpeak = b/temperature								# [m]
			if angular:
				wlpeak /= 2*np.pi								# [m/rad]
		else:
			from scipy import constants
			b = constants.physical_constants[ \
				'Wien frequency displacement law constant'][0]	# [Hz/K]
			if variable == 'wavenumber':
				b /= c											# [1/(m.K)]
			wlpeak = b*temperature								# freq: [Hz], waveno: [1/m]
			if angular:
				wlpeak *= 2*np.pi								# freq: [rad/s], waveno: [rad/m]
		
		# Return peak wavelength (or frequency or wavenumber) if given radiance 
		# within tolerance
		radpeak = planck(wlpeak, temperature, **kwargs)
		if np.isclose(radiance, radpeak, rtol=rtol, atol=atol):
			return [wlpeak]
		elif radiance > radpeak:
			raise Exception("No solution found")
		
		# Get range of possible wavelengths (or frequencies or wavenumbers)
		wlmin = wlpeak/2
		wlmax = wlpeak*2
		while planck(wlmin, temperature, **kwargs) >= radiance:
			wlmin /= 2
		while planck(wlmax, temperature, **kwargs) >= radiance:
			wlmax *= 2
		
		# Define difference function between Planck function and given radiance 
		# for given wavelength (or frequency or wavenumber)
		def f(wl):
			return planck(wl, temperature, **kwargs) - radiance
		
		# Solve for wavelengths (or frequencies or wavenumbers)
		wl1 = root_scalar(f, bracket=[wlmin, wlpeak])
		wl2 = root_scalar(f, bracket=[wlpeak, wlmax])
		wavelengths = [wl1.root if wl1.converged else np.nan, \
			wl2.root if wl2.converged else np.nan]
		
		# Return wavelengths (or frequencies or wavenumbers; angular or non-angular)
		return wavelengths
	
	# Return radiance from Planck function
	else:
		# Format inputs
		wavelength = np.ma.array(wavelength)
		temperature = np.ma.array(temperature)

		# Calculate radiance
		if variable == 'frequency':
			frequency = wavelength
			if angular:
				radiance = hbar*frequency**3/(4*np.pi**3*c**2)/ \
					(np.exp(hbar*frequency/(k*temperature))-1)		# [W/m^2/sr/Hz/rad]
			else:
				radiance = 2*h*frequency**3/c**2/(np.exp(h*frequency/ \
					(k*temperature))-1)								# [W/m^2/sr/Hz]
		elif variable == 'wavelength':
			if angular:
				radiance = hbar*c**2/(4*np.pi**3*wavelength**5)/ \
					(np.exp(hbar*c/(wavelength*k*temperature))-1)	# [W/m^2/sr/m*rad]
			else:
				radiance = 2*h*c**2/wavelength**5/(np.exp(h*c/ \
					(wavelength*k*temperature))-1)					# [W/m^2/sr/m]
		elif variable == 'wavenumber':
			wavenumber = wavelength
			if angular:
				radiance = hbar*c**2*wavenumber**3/(4*np.pi**3)/ \
					(np.exp(hbar*c*wavenumber/(k*temperature))-1)	# [W/m^2/sr*m/rad]
			else:
				radiance = 2*h*c**2*wavenumber**3/(np.exp(h*c*wavenumber/ \
					(k*temperature))-1)								# [W/m^2/sr*m]

		# Convert to spectral energy density
		if energy_density:
			radiance *= 4*np.pi/c

		# Format radiance / energy density for output and return
		if not np.iterable(radiance):
			radiance = float(radiance)
		elif not np.ma.is_masked(radiance):
			radiance = np.ma.getdata(radiance)
		return radiance
#################################### planck ####################################
