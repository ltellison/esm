"""Product
Module for creating and operating on classes of Earth Science Mission products.

Author:
	Luke Ellison

Version:
	0.1

History:
	v0.1, 26-Jan-2026, Luke Ellison: Module compiled.

Global Variables:
	PRODUCT_FIELDS -- List of valid field names for product file name formatters.

Classes:
	Product -- Defines a product object on an Earth Science Mission instrument.

Functions:
	get_product_class -- Gets the product class for the given product ID, 
		instrument ID and platform ID.
	load_product -- Creates either an object of an product-specific class if 
		available, or a generic Product object otherwise.
	query_filename -- Gets the file name of a given `earthaccess.DataGranule` 
		object.
	check_file_hash -- Validates a file using a hash.
"""

#------------------------------ GLOBAL VARIABLES ------------------------------#

PRODUCT_FIELDS = [
	'product',					# product ID
	'flightid',					# flight ID
	'flightno',					# flight number
	'flightline',				# flight line
	'location',					# name location or lat/lon location
	'lat',						# latitude (usually within location field)
	'lon',						# lontigude (usually within location field)
	'x',						# X-coordinate (usually within location field)
	'y',						# Y-coordinate (usually within location field)
	'tile',						# SIN grid tile (usually "hHHvVV" format)
	'h',						# SIN grid horizontal index ("HH" in above)
	'v',						# SIN grid vertical index ("VV" in above)
	'timestamp',				# date/time
	'start_timestamp',			# start date/time
	'end_timestamp',			# end date/time
	'date',						# date (within timestamp field for convenience)
	'start_date',				# start date
	'end_date',					# end date
	'time',						# time (within timestamp field for convenience)
	'start_time',				# start time
	'end_time',					# end time
	'version',					# version or collection number or string
	'processing_timestamp',		# processing date/time
	'ext'						# file name extension
]


#---------------------------------- CLASSES ----------------------------------#

################################### Product ###################################
class Product:
	"""Defines a product object on an Earth Science Mission instrument.
	
	Functions:
		__init__ -- Initializes a product object on an Earth Science Mission 
			instrument.
		set_datadir -- Sets the data directory for this product.
		get_filename_attrs -- Gets the formatted results from a file name match.
		find_files -- Finds product files that match given filters.
		load_dataset -- Initializes a dataset of the Product object from a file.
		loaded_datasets -- Organizes the loaded datasets into a flattened 
			dictionary with the file name as the keys.
	
	Returns:
		- An object defining a product on an Earth Science Mission instrument.
	"""

	# Constructor method
	def __init__(self, /, id, instrument=None, platform=None, meta=None, 
	  formatters=None, reverse_formatters=None, iter_filters=None, 
	  directory=None, query=None, download=None, available_products=dict(), 
	  **kwargs):
		"""Initializes a product object of an Earth Science Mission instrument.
		
		Parameters:
			id: type=str
				- The standardized name (ID) of the product.  If not found, will 
				still create a `Product` object with no associated `instrument` 
				or `platform`.
			instrument: type=Instrument|str|bool, default=None
				- The instrument associated with the product.  If an 
				`Instrument` object, will use its ID.  If a string, will use the 
				standardized instrument ID to create a new `Instrument` object.  
				If `False`, will ensure that no `instrument` is set (even if the 
				product ID is found).  If `None`, will search for the instrument 
				ID among all available instruments and create a new `Instrument` 
				object if one and only one instrument is found with the product 
				ID.
			platform: type=Platform|str|bool, default=None
				- The platform on which the product's instrument is located.  If 
				a `Platform` object, will use its ID.  If a string, will use the 
				standardized platform ID to create a new `Platform` object.  If 
				`False`, will ensure that no platform is set (even if the 
				instrument ID is found).  If `None`, will search for the 
				instrument ID among all available platforms and create a new 
				`Platform` object if one and only one platform is found with the 
				instrument ID.
			meta: type=dict, default=None
				- Information that will be added to the default information for 
				the given product (duplicate keys in the default information are 
				overwritten).
			formatters: type=dict, default=None
				- A dictionary of standard product field formatters.  Accepted 
				fields are stored in the `PRODUCT_FIELDS` global variable.  
				These will overwrite any formatters saved at the instrument 
				level.
			reverse_formatters: type=dict, default=None
				- A dictionary of standard product field reverse formatters.  
				Accepted fields are stored in the `PRODUCT_FIELDS` global 
				variable.  These will overwrite any formatters saved at the 
				instrument level.  If any necessary formatters are not included, 
				then if it exists in the `formatters` argument, the `datetime` 
				function `strftime` will be used; otherwise, if the pattern in 
				the given file name includes only digits, then the digits of the 
				string version of the value is fit to those number of digits; 
				otherwise, `str` will be used as the reverse formatter.
			iter_filters: type=list|str, default=None
				- A file name attribute name (used in filtering search results) 
				or list of such names where the attribute value is an iterable 
				after formatting.  This value will overwrite any value saved at 
				the instrument level.
			directory: type=str|pathlib.Path, default=None
				- The directory of the product's data.  Set to `False` to ensure 
				no data directory attribute is set.
			query: type=bool, default=None
				- A switch to turn querying online data on or off.  If `None`, 
				will use the global `QUERY` value.
			download: type=bool, default=None
				- A switch to turn downloading online data on or off.  If 
				`None`, will use the global `DOWNLOAD` value.
			available_products: type=dict, default=dict()
				- A dictionary of available product IDs and metadata used for 
				loading the object.
		"""
		import re
		from functools import partial
		import datetime as dt
		from .config import QUERY, DOWNLOAD, SELECTABLE_SPECIFICATIONS
		# from .instrument import _set_attr_by_key
		from .ancillary import set_attr_by_key, iterable, findattr
		
		# Format ID
		id = id.strip()

		# Get instrument object from inputs
		instrument = _find_product_instrument(id, instrument=instrument, \
			platform=platform, **kwargs)
		
		# Get available products from instrument
		if instrument and hasattr(instrument, 'products'):
			available_products = instrument.products | available_products

		# Get standardized platform ID and save
		self.id = _get_standard_product_id(id, available_products)
		if self.id is None:
			self.id = id

		# Save this new Product object to Instrument object
		product_meta = dict()
		if instrument:
			if not hasattr(instrument, 'products'):
				setattr(instrument, 'products', dict())
			elif self.id not in instrument.products:
				pass
			elif isinstance(instrument.products[self.id], dict):
				product_meta.update(instrument.products[self.id])
			else:
				product_meta.update(vars(instrument.products[self.id]))
			instrument.products.update({self.id: self})
			self.instrument = instrument
			if hasattr(instrument, 'platform'):
				self.platform = self.instrument.platform
		
		# Update product info
		if meta:
			product_meta.update(meta)
		for k,v in product_meta.items():
			setattr(self, k, v)
		
		# Set the formatters
		self.formatters = dict(lat=float, lon=float, x=float, y=float, h=int, \
			v=int)
		if hasattr(self, 'instrument'):
			self.formatters |= getattr(self.instrument, 'formatters', dict())
		if formatters is not None:
			self.formatters |= {k.lower():v for k,v in dict(formatters).items() \
				if k.lower() in PRODUCT_FIELDS}
		
		# Convert string formatter inputs to functions
		time_vars = set("fpzHIMSXZ")
		def _str2dt_formatter(string, formatter):
			value_vars = set(re.sub("[^a-zA-Z]", "", formatter))
			t = dt.datetime.strptime(string, formatter)
			if not value_vars-time_vars:
				t = t.time()
			elif not value_vars.intersection(time_vars):
				t = t.date()
			return t
		datetime_formatters = dict()
		for k,v in self.formatters.items():
			if isinstance(v, str):
				self.formatters[k] = partial(_str2dt_formatter, formatter=v)
				datetime_formatters.update({k:v})

		# Set the reverse formatters
		self_reverse_formatters = dict()
		if hasattr(self, 'instrument'):
			self_reverse_formatters |= getattr(self.instrument, \
				'reverse_formatters', dict())
		if reverse_formatters is not None:
			self_reverse_formatters |= {k.lower():v for k,v in \
				dict(reverse_formatters).items() if k.lower() in PRODUCT_FIELDS}
		for k,v in self_reverse_formatters.items():
			if isinstance(v, str):
				if "%" in v:
					self_reverse_formatters[k] = lambda t,v=v: t.strftime(v)
				else:
					self_reverse_formatters[k] = lambda n,v=v: f"{n:{v}}"
		for formatter in set(self.formatters)-set(self_reverse_formatters):
			if formatter in datetime_formatters:
				self_reverse_formatters[formatter] = lambda t,formatter= \
					datetime_formatters[formatter]: t.strftime(formatter)
			# else:
			# 	self_reverse_formatters[formatter] = str
		if self_reverse_formatters:
			self.reverse_formatters = self_reverse_formatters
		
		# Set the iterable filters
		if iter_filters is None:
			if hasattr(self, 'instrument'):
				self.iter_filters = getattr(self.instrument, 'iter_filters', [])
		else:
			self.iter_filters = set([j for i in (iter_filters if \
				iterable(iter_filters) else [iter_filters]) if \
				(j:=i.lower().strip()) in PRODUCT_FIELDS])

		# Set the data directory of the product
		if directory is not False:
			self.set_datadir(directory, default=None)

		# Set the query switch
		self.query = QUERY if query is None else query
		self.download = DOWNLOAD if download is None else download
		
		# Set geolocation product specific to platform from the instrument object
		set_attr_by_key(self, 'geo_product', change=True, value=False, \
			silent=True)
		# geo_product = findattr(self, 'geo_product', None)
		# if isinstance(geo_product, dict):
		# 	geo_product_key = findattr(self, 'geo_product_key', None)
		# 	if geo_product_key is not None:
		# 		geo_product_key_value = findattr(self, geo_product_key, None)
		# 		if geo_product_key_value is not None and \
		# 		  geo_product_key_value in geo_product:
		# 			self.geo_product = geo_product[geo_product_key_value]
		# # if hasattr(self, 'instrument') and hasattr(self.instrument, \
		# #   'geo_product'):
		# # 	if isinstance(self.instrument.geo_product, dict):
		# # 		if hasattr(self, 'platform') and self.platform.id in \
		# # 		  self.instrument.geo_product:
		# # 			self.geo_product = self.instrument.geo_product[ \
		# # 				self.platform.id]
		# # 	else:
		# # 		self.geo_product = self.instrument.geo_product

		# Set selected product attributes
		for attr_name in SELECTABLE_SPECIFICATIONS:
			set_attr_by_key(self, attr_name, change=True, value=False, \
				silent=True)
		# Set product attributes specific to spatial resolution from instrument
		# if hasattr(self, 'instrument') and hasattr(self, 'spatial_resolution'):
		# 	for attr_name in ('scan_width', 'swath_width', 'ifov', 'gsd', \
		# 	  'prf', 'pixel_offset'):
		# 		if hasattr(self.instrument, attr_name):
		# 			attr_val = getattr(self.instrument, attr_name)
		# 			if isinstance(attr_val, dict):
		# 				if iterable(self.spatial_resolution):
		# 					iattr_val = {k:v for k,v in attr_val.items() if k \
		# 						in self.spatial_resolution}
		# 					if len(iattr_val) >= 2:
		# 						setattr(self, attr_name, iattr_val)
		# 					elif iattr_val:
		# 						setattr(self, attr_name, \
		# 							list(iattr_val.values())[0])
		# 				elif self.spatial_resolution in attr_val:
		# 					setattr(self, attr_name, \
		# 						attr_val[self.spatial_resolution])
		# 			else:
		# 				setattr(self, attr_name, attr_val)
	
	# Magic method for representation output
	def __repr__(self):
		class_path = '.'.join([self.__module__, self.__class__.__qualname__])
		return f"<{class_path}({self.id})>"
	
	# Magic method for string output
	def __str__(self):
		class_name = self.__class__.__name__
		return f"{class_name}({getattr(self, 'name', self.id)})"

	# Method to set the data directory for product
	def set_datadir(self, /, directory=None, default=".", max_level=None, 
	  timeout=10):
		"""Sets the data directory for this product.

		Parameters:
			directory: type=str|pathlib.Path, default=None
				- The data directory for this instrument, which is determined by 
				the first resolvable method in this ordered list:
					- 1. An absolute path given by the `directory` argument.
					- 2. A relative path given by the `directory` argument whose 
					base directory is found within `max_level` directory levels 
					from the corresponding instrument's data directory (given by 
					the `instrument.datadir` attribute) if it exists.
					- 3. A relative path given by the `directory` argument whose 
					base directory is found within `max_level` directory levels 
					from the current working directory.
					- 4. The environment variable "XPATH" where "X" is replaced 
					with the product ID in upper case with only alphanumeric 
					characters, which can be an absolute path or relative to the 
					corresponding instrument's data directory (given by the 
					`instrument.datadir` attribute) if it exists.
					- 5. A search for a directory named with the product ID 
					within `max_level` directory levels from the corresponding 
					instrument's data directory (given by the 
					`instrument.datadir` attribute) if it exists.
					- 6. The default path given by the `default` argument.
			default: type=str|pathlib.Path, default="."
				- The default directory to use if `directory` is `None` and no 
				environment variable for the data directory was found.  If 
				`None`, will not set any data directory attribute at this point.
			max_level: type=int, default=None
				- The maximum number of levels to traverse in the directory 
				system when searching for a subdirectory.  If `None`, will use 
				the defaults for each search (1 for methods #2 and #3 if a path 
				separator is included in the path and infinity otherwise, and 
				infinity for methods #5 and #6).
			timeout: type=int|float, default=10
				- The number of seconds of runtime before the routine aborts the 
				search.
		"""
		# import warnings
		from pathlib import Path
		import os
		import re
		from .ancillary import breadth_first_search

		# Function to walk through directories only at one level at a time
		# def _search_by_level(relpath, root_dir, max_level, results):
		# 	# Initialization
		# 	search_list = [root_dir]
		# 	level = 0

		# 	# Loop while unsearched directories exist
		# 	while search_list:
		# 		# Check for max level
		# 		level += 1
		# 		if max_level is not None and level > max_level:
		# 			# return None
		# 			results.append(None)
		# 			return
				
		# 		# Search for match
		# 		for _ in range(len(search_list)):
		# 			for item in os.scandir(root:=search_list.pop(0)):
		# 				if item.is_dir():
		# 					if relpath.startswith(item.name) and \
		# 					os.path.exists(path:=os.path.join(root, relpath)):
		# 						# return path
		# 						results.append(path)
		# 						return
		# 					else:
		# 						search_list.append(item.path)
		# 		search_list.sort(reverse=True)
			
		# 	# Return None if no more directories to search
		# 	# return None
		# 	results.append(None)
		
		# Get directory from environment variable or current working directory
		has_inst_dir = hasattr(self, 'instrument') and \
			hasattr(self.instrument, 'datadir')
		if directory is None:
			env = f"{re.sub(r'[^a-zA-Z0-9]', '', self.id).upper()}PATH"
			datadir = os.getenv(env, self.id if has_inst_dir else default)
		
		# Convert pathlib.Path object to str if needed
		else:
			datadir = str(directory)

		# Resolve path name
		datadir = os.path.normpath(os.path.expandvars(os.path.expanduser( \
			datadir)))

		# Search for directory in self.instrument.datadir or '.' if 
		# `directory` is not an absolute path
		if not os.path.isabs(datadir):
			level = (1 if os.sep in datadir else None) if max_level is None \
				else max_level
			basedir = self.instrument.datadir if has_inst_dir else "." if \
				directory else None
			if basedir is not None:
				datadir = breadth_first_search(datadir, basedir, \
					max_level=level, timeout=timeout)
				if datadir is not None:
					datadir = os.path.normpath(str(datadir))
				# results = []
				# thread = threading.Thread(target=_search_by_level, \
				# 	args=(datadir, basedir, level, results), daemon=True)
				# thread.start()
				# thread.join(timeout)
				# if thread.is_alive():
				# 	warnings.warn("\033[38;5;208mTimeout occurred when searching "
				# 		f"for data directory '{datadir}' in '{basedir}'.\033[0m", \
				# 		stacklevel=2)
				# 	datadir = None
				# else:
				# 	datadir = results[0]

		# Set data directory to default if needed and it exists
		if (datadir is None or not os.path.exists(datadir)) and default is not \
		  None:
			datadir = os.path.normpath(os.path.expandvars(os.path.expanduser( \
				str(default))))
		
		# Check for existing path
		if not os.path.exists(datadir):
			raise ValueError(f"Directory does not exist: {datadir}")
		
		# Set data directory attribute
		self.datadir = Path(datadir)
	
	# Method to check if a given file belongs to this product
	def is_product_file(self, /, file):
		"""Checks that the given file name belongs to this product.

		Parameters:
			file: type=str|pathlib.Path
				- The file name or path.

		Returns:
			- `True` if the given file belongs to this product, and `False` 
			otherwise.
		"""
		import os
		import re

		# Return if the given file belongs to this product
		return re.fullmatch(self.filename_pattern, os.path.basename(str(file)))

	# Method to get the formatted results from a file name match
	def get_filename_attrs(self, /, file, format=True, **kwargs):
		"""Gets the formatted results from a file name match.

		Parameters:
			file: type=str|pathlib.Path
				- The file name or path.
			format: type=bool, default=True
				- If `True`, will use the file formatters to format the 
				extracted attribute values from the file name; if `False`, will 
				return unformatted file name attributes.
			**kwargs:
				- 

		Returns:
			- A dictionary of file name match groups.
		"""
		import warnings
		import os
		import re
		# import datetime as dt

		# Match file to file name format
		if not (m:=re.fullmatch(self.filename_pattern, \
		  os.path.basename(str(file)))):
			return None
		mdict = m.groupdict()

		# Return unformatted filename attributes
		if not format:
			return mdict

		# Format all fields
		# time_vars = set("fpzHIMSXZ")
		for k,v in mdict.items():
			# Find formatter
			if k not in self.formatters:
				continue
			formatter = self.formatters[k]

			# String formatters are assumed to be date/time formats
			# if isinstance(formatter, str):
			# 	v = dt.datetime.strptime(v, formatter)
			# 	value_vars = set(re.sub("[^a-zA-Z]", "", formatter))
			# 	if not value_vars-time_vars:
			# 		v = v.time()
			# 	elif not value_vars.intersection(time_vars):
			# 		v = v.date()
			# 	mdict[k] = v
			
			# Use formatter as a function
			# else:
			try:
				mdict[k] = formatter(v)
			except:
				warnings.warn(f"\033[38;5;208mCould not format {k} "
					"- treating as string. Consider a new formatter "
					"for this field.\033[0m", stacklevel=2)
		
		# Return filename match groups dictionary
		return mdict

	# Method to reverse format filename attributes back to strings
	def filename_attrs_unformat(self, /, ignore=(dict,), **kwargs):
		"""Reverse formats (back to a string) file name attributes.

		Parameters:
			ignore: type=tuple, default=(dict,)
				- A tuple of types that will be ignored during conversion.  The 
				resulting entry will be set to `None` in the returned dictionary.
			**kwargs:
				-

		Returns:
			- A dictionary of reversed formatted file name attributes.  Input 
			keyword arguments without a matching reverse formatter are ignored.
		"""

		# Return a dictionary of reversed formatted filename attributes
		reverse_formatters = getattr(self, 'reverse_formatters', {})
		return {k:(None if isinstance(v, ignore) else reverse_formatters[k](v)) \
			for k,v in kwargs.items() if k in reverse_formatters}

	# Method to reverse the filename format with given attributes
	def filename_unformat(self, /, **kwargs):
		"""Reverses the product's 'filename_format' attribute.
	
		Parameters:
			**kwargs:
				- 
		
		Returns:
			- The original file name using the given formatted file name 
			attributes.  Uses * and ? wildcards where keyword not given or 
			ambiguous.
		"""
		import re

		# Set product data tag keyword
		kwargs['product'] = self.id

		# Function to find the last match position of a regex search
		def _last_match_pos(pattern, string, flags=0):
			imatch = None
			istring = 0
			while m:=re.search(pattern, string, flags=flags):
				imatch = istring+m.start()
				istring += m.end()
				string = string[m.end():]
			return imatch if imatch is None else (imatch,istring)

		# Function to account for nested brackets in regex searches
		def _search_for_groups(pattern, string, flags=0, dtype=tuple, unit=None):
			assert dtype in (tuple, list, dict)
			opensym,closesym = [rf"(?<!\\)\{s}" for s in list(str(dtype()))]
			if unit is None:
				if dtype is tuple:
					unit = r"\(\?P<\w+>.*?(\(\?<\\\\\))?\)"
				else:
					unit = rf"\\\{closesym[-1]}"
			count = (0,0)
			i = None
			while True:
				m = re.search(pattern, string, flags=flags)
				if not m:
					return m
				nopen = len(re.findall(opensym, m[0]))
				nclose = len(re.findall(closesym, m[0]))
				if nopen == nclose:
					break
				elif nopen < nclose or count == (nopen, nclose):
					return None
				count = (nopen, nclose)
				if i is None:
					_,i = _last_match_pos(unit, pattern)
				pattern = pattern[:i-1] + f"{closesym}.*?"*(nopen-nclose) + \
					pattern[i-1:]
			return m
		
		# Function to account for nested brackets in regex substitutions
		def _sub_for_groups(pattern, repl, string, count=0, flags=0, \
		  dtype=tuple):
			m = _search_for_groups(pattern, string, flags=flags, dtype=dtype)
			if not m:
				return string
			return re.sub(m.re, repl, string, count=count, flags=flags)

		# Replace components (1st round)
		subs = [
			(r"(?<!\\)\(\?#.*?(?<!\\)\)", ""),			# comments
		]
		filename_pattern = self.filename_pattern
		for pattern,repl in subs:
			filename_pattern = _sub_for_groups(pattern, repl, filename_pattern)

		# Convert file name pattern to an f-string
		attr_pattern = r"(?<!\\)\(\?P<(?P<attrname>\w*)>(?P<attrpttn>.*?)(?<!\\)\)"
		attr_formats = {}
		def _pattern2formatter(s):
			s = ["", s]
			while s[1]:
				m = _search_for_groups(attr_pattern, s[1])
				if not m:
					s[0] += s[1]
					break
				s[0] += s[1][:m.start()]
				if m['attrname'] not in kwargs and \
				  _search_for_groups(attr_pattern, m['attrpttn']):
					s[0] += _pattern2formatter(m['attrpttn'])
				else:
					s[0] += f"{{{m['attrname']}}}"
					attr_formats[m['attrname']] = m['attrpttn']
				s[1] = s[1][m.end():]
			return s[0]
		filename_format = _pattern2formatter(filename_pattern)

		# Check file name format for irreversible formatting
		invalid = [
			r"(?<!\.|\\)\*",						# * character
			r"(?<!\\)\+",							# + character
			r"(?<!\\)\?",							# ? character
			r"(?<!\\)\|",							# | character
			r"[^\\](\^|\\A)",						# start of string
			r"(?<!\\)(\$|\\[zZ]).",					# end of string
			r"(?<!\\)\[[^\\]*?\]",					# brackets
			r"(?<!\\)\{\d+(,\d+)?\}",				# multiplier
			r"(?<!\\)\(\?P=\w+\)",					# backreference
			r"(?<!\\)\\\d{1,2}",					# group number
			r"(?<!\\)\\[bBdDsSwW]",					# special sequences
			r"(?<!\\)\\[abfnNrtuUvx]",				# escape sequences
		]
		for seq in invalid:
			if re.search(seq, filename_format):
				raise ValueError("The file name format attribute for this " \
					"product has an irreversible formatting sequence.")

		# Check file name format for irreversible formatting of groups
		invalid = [
			r"(?<!\\)\(\?<?[=!].*?(?<!\\)\)",				# assertions
			r"(?<!\\)\(\?\(\w*\).*(?<!\\)\|.*(?<!\\)\)",	# if-then
		]
		for seq in invalid:
			if _search_for_groups(seq, filename_format):
				raise ValueError("The file name format attribute for this " \
					"product has an irreversible formatting sequence.")

		# Replace components (2nd round)
		subs = [
			(r"(?<!\\)\(\?[aiLmsux]+\)", r"\1"),			# flags
			(r"(?<!\\)\(\?[aiLmsux]+(?:-[imsx]+)?:.*?(?<!\\)\)", r"\1"),	# flags
			(r"(?<!\\)\(\?>(.*?)(?<!\\)\)", r"\1"),			# atomic group
			(r"(?<!\\)\((?:\?:)?(.*?)(?<!\\)\)", r"\1"),	# group
		]
		for pattern,repl in subs:
			filename_format = _sub_for_groups(pattern, repl, filename_format)

		# Replace components (3rd round)
		subs = [
			(r"^(\^|\\A)", ""),						# start of string
			(r"(\$|\\[zZ])$", ""),					# end of string
			(r"(?<!\\)\.\*", "*"),					# dot-asterisk -> asterisk
			(r"(?<!\\)\.", "?"),					# dot -> question mark
			(r"(?<!\\)\\([.^$*+?|\\(){}[\]])", r"\1"),	# escape characters
		]
		for pattern,repl in subs:
			filename_format = re.sub(pattern, repl, filename_format)
		
		# Format filename with reverse formatters and return
		if not attr_formats:
			return filename_format
		reverse_formatters = getattr(self, 'reverse_formatters', {})
		attrs = self.filename_attrs_unformat(**kwargs)
		for attrname,attrpttn in attr_formats.items():
			if attrname not in kwargs or attrname in attrs and attrs[attrname] \
			  is None:
				attrs[attrname] = "*"
			elif attrname in reverse_formatters:
				pass
				# attrs[attrname] = reverse_formatters[attrname](kwargs[attrname])
			elif isinstance(kwargs[attrname], str):
				attrs[attrname] = kwargs[attrname]
			elif attrname not in reverse_formatters and \
			  re.fullmatch(r"(\\d(\{\d+\})?)+", attrpttn):
				count = 0
				while (m:=re.match(r"\\d(?:\{(\d+)\})?", attrpttn)):
					count += int(m[1]) if m[1] else 1
					attrpttn = attrpttn[m.end():]
				digits = ''.join([s for s in str(kwargs[attrname]) if \
					s.isdigit()])
				if len(digits) > count and set(digits[count:]) != {'0'}:
					attrs[attrname] = str(kwargs[attrname])
				else:
					attrs[attrname] = digits[:count].zfill(count)
			else:
				attrs[attrname] = str(kwargs[attrname])
		return filename_format.format(**attrs)

	# Property to set if querying online data is on or off
	@property
	def query(self):
		"""Returns a boolean value representing if querying online data is 
		allowed.
		"""
		return self._query
	@query.setter
	def query(self, /, switch):
		"""Sets the switch governing if querying online data is allowed.
	
		Parameters:
			switch: type=bool
				- Set to `True` to allow querying online data.
		"""
		self._query = bool(switch)
	
	# Property to set if downloading online data is on or off
	@property
	def download(self):
		"""Returns a boolean value representing if downloading online data is 
		allowed.
		"""
		return self._download
	@download.setter
	def download(self, /, switch):
		"""Sets the switch governing if downloading online data is allowed.
	
		Parameters:
			switch: type=bool
				- Set to `True` to allow downloading online data.
		"""
		self._download = bool(switch)
	
	# Method to query NASA Earth Data using the NASA CMR
	def query_data(self, /, **kwargs):
		"""Queries NASA Earth Data for matching granules using NASA's CMR.

		Parameters:
			**kwargs:
				- Accepts additional keyword arguments for the following 
				functions:
					- earthaccess.search_datasets: count, keyword, short_name, 
					doi, daac, data_center, provider, has_granules, temporal, 
					bounding_box, polygon, point, line, circle, cloud_hosted, 
					concept_id, instrument, project, fields, revision_date, 
					debug
					- earthaccess.search_data: count, short_name, version, daac, 
					data_center, provider, cloud_hosted, downloadable, 
					online_only, orbit_number, granule_name, instrument, 
					platform, cloud_cover, day_night_flag, temporal, 
					bounding_box, polygon, point, line, circle
				- Accepts additional keyword arguments that are file name 
				attributes as extracted from the `get_filename_attrs` method.  
				These will be used to construct the `granule_name` parameter for 
				`earthaccess.search_data`.

		External Modules:
			- earthaccess -- https://earthaccess.readthedocs.io/
		
		Returns:
			- A list of `earthaccess.DataGranule` objects that match the given 
			parameters.
		"""
		import re
		import datetime as dt
		import earthaccess as ea
		from .platform import Aircraft

		# Convert timestamp information to 'temporal' argument for earthaccess
		if 'temporal' not in kwargs and {'timestamp', 'date'}.intersection(kwargs):
			if 'timestamp' in kwargs:
				t = kwargs['timestamp']
				if isinstance(t, dict):
					kwargs['temporal'] = (t['min'], t['max'])
				elif isinstance(t, (dt.date, str)):
					kwargs['temporal'] = (t, t)
			else:
				t = kwargs['date']
				if isinstance(t, dict):
					t = (t['min'], t['max'])
				else:
					t = (t, t)
				if 'time' in kwargs:
					d = t
					t = kwargs['time']
					t = (t['min'], t['max']) if isinstance(t, dict) else (t, t)
					if any([isinstance(i, str) for i in [*d, *t]]) and \
					  any([not isinstance(i, str) for i in [*d, *t]]):
						d = tuple(i if isinstance(i, str) else i.isoformat() \
							for i in d)
						t = tuple(i if isinstance(i, str) else i.isoformat() \
							for i in d)
					if isinstance(d[0], str):
						t = (f"{d[0]}T{t[0]}", f"{d[1]}T{t[1]}")
					else:
						t = tuple(dt.datetime.combine(i,j) for i,j in zip(d,t))
				kwargs['temporal'] = t

		# Condense number of points for lines and polygons if too many
		if 'polygon' in kwargs:
			n = len(kwargs['polygon'])
			if n > 150:
				kwargs['polygon'] = kwargs['polygon'][::n//150] + \
					[kwargs['polygon'][0]]
		if 'line' in kwargs:
			n = len(kwargs['line'])
			if n > 150:
				kwargs['line'] = kwargs['line'][::n//150]

		# Get function-specific keyword parameters (use explicit lists because 
		# these are hidden inside **kwargs)
		ds_params = ['count', 'keyword', 'short_name', 'doi', 'daac', \
			'data_center', 'provider', 'has_granules', 'temporal', \
			'bounding_box', 'polygon', 'point', 'line', 'circle', \
			'cloud_hosted', 'concept_id', 'instrument', 'project', 'fields', \
			'revision_date', 'debug']
		data_params = ['count', 'short_name', 'version', 'daac', 'data_center', \
			'provider', 'cloud_hosted', 'downloadable', 'online_only', \
			'orbit_number', 'granule_name', 'instrument', 'platform', \
			'cloud_cover', 'day_night_flag', 'temporal', 'bounding_box', \
			'polygon', 'point', 'line', 'circle']
		ds_kwargs = {k:v for k,v in kwargs.items() if k in ds_params and v is \
			not None}
		data_kwargs = {k:v for k,v in kwargs.items() if (k in data_params or k \
			in ds_params) and v is not None}
		
		# Get associated instrument and platform objects
		instrument = getattr(self, 'instrument', None)
		platform = getattr(self, 'platform', None)

		# Get the earthaccess product object
		isproductset = 'concept_id' in data_kwargs or 'doi' in data_kwargs
		if not isproductset:
			# Get matching products
			ds_kwargs['short_name'] = data_kwargs['short_name'] = self.id
			keyword0 = ds_kwargs.get('keyword', '')
			ea_prod = ea.search_datasets(**ds_kwargs)
			if not ea_prod:
				del ds_kwargs['short_name']
				del data_kwargs['short_name']
				ds_kwargs['keyword'] = f"{self.id} {keyword0}"
				ea_prod = ea.search_datasets(**ds_kwargs)
				if not ea_prod and instrument:
					ds_kwargs['keyword'] = getattr(instrument, 'name', \
						instrument.id) + f" {keyword0}"
					ea_prod = ea.search_datasets(**ds_kwargs)
			
			# Get single product (unless its platform is an aircraft, because 
			# products are given per mission)
			if len(ea_prod) > 1 and not isinstance(platform, Aircraft):
				# if len(ea_prod) > 1 and instrument and 'instrument' not in \
				#   ds_kwargs:
				# 	ds_kwargs['instrument'] = getattr(instrument, 'name', \
				# 		instrument.id)
				# 	ea_prod2 = ea.search_datasets(**ds_kwargs)
				# 	if ea_prod2 and len(ea_prod2) < len(ea_prod):
				# 		ea_prod = ea_prod2
				# 		data_kwargs['instrument'] = ds_kwargs['instrument']
				# if len(ea_prod) > 1 and not re.search( \
				#   '(?<![a-z0-9])nrt(?![a-z0-9])', self.id, re.I) and 'nrt' not \
				#   in getattr(self, 'name', '').lower().split() and 'nrt' not in \
				#   ds_kwargs.get('keyword', '').lower().split():
				# 	ds_kwargs2 = {k:v for k,v in ds_kwargs.items()}
				# 	ds_kwargs2['keyword'] = "NRT " + ds_kwargs.get('keyword', '')
				# 	ea_prod2 = ea.search_datasets(**ds_kwargs2)
				# 	ea_prod = [p for p in ea_prod if p not in ea_prod2]
				# if len(ea_prod) > 1:
				# 	raise ValueError("Could not specify which online product "
				# 		f"corresponds to '{self.id}' (received {len(ea_prod)} "
				# 		"matches.)")
				ea_prod_vers = [p['umm']['Version'] for p in ea_prod]
				ea_prod_nrt = ['NRT' in v.upper() for v in ea_prod_vers]
				if any(ea_prod_nrt) and not \
				  re.search('(?<![a-z0-9])nrt(?![a-z0-9])', self.id, re.I) and \
				  'nrt' not in getattr(self, 'name', '').lower().split() and \
				  'nrt' not in ds_kwargs.get('keyword', '').lower().split():
					ea_prod = [p for i,p in enumerate(ea_prod) if not \
						ea_prod_nrt[i]]
					ea_prod_vers = [v for i,v in enumerate(ea_prod_vers) if not \
						ea_prod_nrt[i]]
				if len(ea_prod) > 1 and len(set(ea_prod_vers)) > 1 and \
				  'version' in getattr(self, 'formatters', {}):
					ea_prod_vers = [self.formatters['version'](v) for v in \
						ea_prod_vers]
					latest = max(ea_prod_vers)
					ea_prod = [p for i,p in enumerate(ea_prod) if \
						ea_prod_vers[i] == latest]
				if len(ea_prod) > 1 and instrument and 'instrument' not in \
				  ds_kwargs:
					ds_kwargs['instrument'] = getattr(instrument, 'name', \
						instrument.id)
					ea_prod2 = ea.search_datasets(**ds_kwargs)
					if ea_prod2 and len(ea_prod2) < len(ea_prod):
						ea_prod = ea_prod2
						data_kwargs['instrument'] = ds_kwargs['instrument']
				if len(ea_prod) > 1:
					raise ValueError("Could not specify which online product "
						f"corresponds to '{self.id}' (received {len(ea_prod)} "
						"matches.)")
			if not len(ea_prod):
				raise ValueError("Could not identify any online product "
					f"'{self.id}'.")
		
		# Construct granule name and add to query if not given
		# 
		# (adding an 
		# asterisk wildcard to the front of the granule name due to a bug with 
		# `earthaccess.search_data`)
		if 'granule_name' not in data_kwargs:
			gkwargs = {k:v for k,v in kwargs.items() if k != 'ext'}
			granule_name = self.filename_unformat(**gkwargs)
			if hasattr(granule_name, 'removesuffix'):
				granule_name = granule_name.removesuffix(".*")
			elif granule_name[-1] != '.':
				granule_name = granule_name.rsplit('.',1)[0]
			data_kwargs['granule_name'] = f"{granule_name}"
		
		# Order products by filename of first available file in each product
		if not isproductset and len(ea_prod) > 1:
			examples = []
			data_kwargs2 = data_kwargs | {'count': 1}
			for p in ea_prod:
				data_kwargs2['concept_id'] = p['meta']['concept-id']
				try:
					examples.append(query_filename(ea.search_data( \
						**data_kwargs2)[0]))
				except:
					examples.append("")
			ea_prod = [p for f,p in sorted(zip(examples, ea_prod), \
				key=lambda z: z[0]) if f]
		
		# Return granules the meet search criteria
		if isproductset:
			for g in self.filter_files(ea.search_data(**data_kwargs), **kwargs):
				yield g
		else:
			for p in ea_prod:
				data_kwargs['concept_id'] = p['meta']['concept-id']
				for g in self.filter_files(ea.search_data(**data_kwargs), \
				  **kwargs):
					yield g
	
	# Method to check if a file name matches the expected file pattern
	def filter_files(self, /, files, attrs=False, iter_filters=None, 
	  flightid=None, flightno=None, flightline=None, location=None, bounds=None, 
	  lat=None, lon=None, x=None, y=None, tile=None, h=None, v=None, 
	  timestamp=None, date=None, time=None, version=None, subversion=None, 
	  processingtimestamp=None, ext=None, **kwargs):
		"""Filters given file names that match given filters.  The filters may 
		be a single value or a list of values, of which at least one must be 
		found in the file name.  The values may be a dictionary that defines a 
		range between the two values, where key 'min' represents the minimum 
		value, 'max' represents the maximum value, and 'incl' gives either a 
		boolean value indicating whether the min and max are inclusive or not, 
		or a two-element string (e.g. '[)') where '[' and ']' represent the 
		endpoints are inclusive, and '(' and ')' represent the endpoints are 
		exclusive.  If any array-like value is given, it must be enclosed within 
		a list or be specified in `iter_filters`, or else it will be interpreted 
		as individual values.  Values extracted from the file name are first 
		converted with any formatters defined by the `Instrument` or `Product` 
		class, before being tested with these filters.  For the individual 
		(non-range) filter values, they may even be of `re.Pattern` type.
		
		Parameters:
			files: type=list|str|pathlib.Path|earthaccess.DataGranule
				- A scalar or list of file path objects.
			attrs: type=bool, default=False
				- If `True`, will return a tuple of the form (file, attribute 
				dictionary) for each successful test instead of just the file.
			iter_filters: type=list|str, default=None
				- A filter name or list of filter names where the base item is 
				an iterable object (excluding dictionaries which are reserved 
				for defining ranges.)
			flightid: type=object, default=None
				- The flight ID (usually composed of `flightno` and `flightline`).
			flightno: type=object, default=None
				- The flight number.
			flightline: type=object, default=None
				- The flight line.
			location: type=object, default=None
				- The location, which may be a name or be composed of `lat` and 
				`lon` or `x` and `y`.
			bounds: type=object, default=None
				- A bounding box or list of bounding boxes using either `lat` 
				and `lon` or `x` and `y`, in the format [xmin, ymin, xmax, ymax].
			lat: type=object, default=None
				- The latitude. (The default formatter is `float`.)
			lon: type=object, default=None
				- The longitude. (The default formatter is `float`.)
			x: type=object, default=None
				- The X-coordinate physical system. (The default formatter is 
				`float`.)
			y: type=object, default=None
				- The Y-coordinate physical system. (The default formatter is 
				`float`.)
			tile: type=object, default=None
				- The tile designation, which may be composed of `h` and `v`.
			h: type=object, default=None
				- The horizontal tile index. (The default formatter is `int`.)
			v: type=object, default=None
				- The vertical tile index. (The default formatter is `int`.)
			timestamp: type=object, default=None
				- The date/time timestamp (usually a `datetime.datetime` 
				object).  The 'timestamp', 'start_timestamp' and 'end_timestamp' 
				file attributes will all be referenced if included.
			date: type=object, default=None
				- The date (usually a `datetime.date` object).  The 'date', 
				'start_date' and 'end_date' file attributes will all be 
				referenced if included.
			time: type=object, default=None
				- The time (usually a `datetime.time` object).  The 'time', 
				'start_time' and 'end_time' file attributes will all be 
				referenced if included.
			version: type=object, default=None
				- The data version or collection.
			subversion: type=object, default=None
				- The data sub-version or sub-collection.
			processingtimestamp: type=object, default=None
				- The processing date/time timestamp (usually a 
				`datetime.datetime` object).
			ext: type=object, default=None
				- The file extension.
			**kwargs:
				- 
		
		External Modules:
			- earthaccess -- https://earthaccess.readthedocs.io/
		
		Returns:
			- A list of given files whose file names passed all given filters.
		"""
		from types import GeneratorType
		from pathlib import Path
		import re
		from operator import lt, gt, le, ge
		import datetime as dt
		import earthaccess as ea
		from .ancillary import iterable

		# Get file names of files
		if not iterable(files):
			files = [files]
		filenames = []
		for file in files:
			if isinstance(file, str):
				filename = Path(file).name
			elif isinstance(file, Path):
				filename = file.name
			elif isinstance(file, ea.DataGranule):
				filename = query_filename(file)
			filenames.append(filename)
		
		# Get iterable filters
		if iter_filters is None:
			iter_filters = getattr(self, 'iter_filters', [])
		elif isinstance(iter_filters, str):
			iter_filters = [iter_filters]
		iter_filters = [j for i in iter_filters if (j:=i.lower().strip()) in \
			PRODUCT_FIELDS]

		# Function to get the range endpoints and operators from range dictionary
		def _get_range_params(range_dict):
			minval = range_dict.get('min', None)
			maxval = range_dict.get('max', None)
			incl = range_dict.get('incl', True)
			if isinstance(incl, bool):
				minincl = maxincl = incl
			else:
				minincl = {'[': True, '(': False}[incl[0]]
				maxincl = {']': True, ')': False}[incl[1]]
			minop = ge if minincl else gt
			maxop = le if maxincl else lt
			return (minval, minop, maxval, maxop)

		# Function to apply a set of filters to a formatted value
		def _apply_filters(value, filters, iter_item=False):
			if value is None or filters is None:
				return True
			if isinstance(value, dict):
				vmin,vminop,vmax,vmaxop = _get_range_params(value)
			if isinstance(filters, GeneratorType):
				filters = list(filters)
			if not iterable(filters) or isinstance(filters, dict) or iter_item \
			  and (not iterable(filters[0]) or isinstance(filters[0], dict)):
				filters = [filters]
			for f in filters:
				if isinstance(f, dict):
					fmin,fminop,fmax,fmaxop = _get_range_params(f)
				if isinstance(f, re.Pattern) and f.fullmatch(value):
					return True
				elif not isinstance(value, dict) and isinstance(f, dict):
					if fmaxop(value, fmax) if fmin is None else fminop(value, \
					  fmin) if fmax is None else fminop(value, fmin) and \
					  fmaxop(value, fmax):
						return True
				elif isinstance(value, dict) and not isinstance(f, dict):
					if vmaxop(f, vmax) if vmin is None else vminop(f, vmin) if \
					  vmax is None else vminop(f, vmin) and vmaxop(f, vmax):
						return True
				elif isinstance(value, dict) and isinstance(f, dict):
					if vmaxop(fmin, vmax) and fminop(vmax, fmin) if vmin is \
					  None or fmax is None else vminop(fmax, vmin) and \
					  fmaxop(vmin, fmax) if vmax is None or fmin is None else \
					  vminop(fmax, vmin) and fminop(vmax, fmin) and \
					  vmaxop(fmin, vmax) and fmaxop(vmin, fmax):
						return True
				elif value == f:
					return True
				elif not isinstance(f, type(value)) and value == type(value)(f):
					return True
			return False

		# Loop thru file names
		passed = []
		for file,filename in zip(files, filenames):
			# Match file to file name format and get groups
			attrdict = self.get_filename_attrs(filename)
			if attrdict is None:
				continue

			# Match product ID
			if not _apply_filters(attrdict.get('product'), self.id, \
			  iter_item='product' in iter_filters):
				continue
			
			# Match flight information
			if not _apply_filters(attrdict.get('flightid'), flightid, \
			  iter_item='flightid' in iter_filters):
				continue
			if not _apply_filters(attrdict.get('flightno'), flightno, \
			  iter_item='flightno' in iter_filters):
				continue
			if not _apply_filters(attrdict.get('flightline'), flightline, \
			  iter_item='flightline' in iter_filters):
				continue

			# Match location information
			if not _apply_filters(attrdict.get('location'), location, \
			  iter_item='location' in iter_filters):
				continue
			if bounds is not None:
				if (y:=attrdict.get('lat')) is None or (x:=attrdict.get('lon')) is \
				  None:
					if (x:=attrdict.get('x')) is None or (y:=attrdict.get('y')) is \
					  None:
						raise ValueError("Could not determine coordinates "
							"for bounds filter.")
				if not iterable(bounds[0]):
					bounds = [bounds]
				passed = False
				for x1,y1,x2,y2 in bounds:
					if x1 <= x <= x2 and y1 <= y <= y2:
						passed = True
						break
				if not passed:
					continue
			if not _apply_filters(attrdict.get('lat'), lat, iter_item='lat' in \
			  iter_filters):
				continue
			if not _apply_filters(attrdict.get('lon'), lon, iter_item='lon' in \
			  iter_filters):
				continue
			if not _apply_filters(attrdict.get('x'), x, iter_item='x' in \
			  iter_filters):
				continue
			if not _apply_filters(attrdict.get('y'), y, iter_item='y' in \
			  iter_filters):
				continue

			# Match grid information
			if not _apply_filters(attrdict.get('tile'), tile, iter_item='tile' \
			  in iter_filters):
				continue
			if not _apply_filters(attrdict.get('h'), h, iter_item='h' in \
			  iter_filters):
				continue
			if not _apply_filters(attrdict.get('v'), v, iter_item='v' in \
			  iter_filters):
				continue

			# Match timestamp information
			if timestamp is not None:
				timestamp_file = []
				if 'timestamp' in attrdict or 'date' in attrdict and 'time' in \
				  attrdict:
					t = attrdict.get('timestamp', dt.datetime.combine( \
						attrdict.get('date'), attrdict.get('time')))
					if hasattr(self, 'temporal_resolution'):
						timestamp_file.append(dict(min=t, \
							max=t+self.temporal_resolution, incl='[)'))
					else:
						timestamp_file.append(t)
				if 'start_timestamp' in attrdict or 'start_date' in attrdict \
				  and 'start_time' in attrdict:
					t = attrdict.get('start_timestamp', dt.datetime.combine( \
						attrdict.get('start_date'), attrdict.get('start_time')))
					if 'end_timestamp' in attrdict:
						timestamp_file.append(dict(min=t, \
							max=attrdict.get('end_timestamp'), incl=True))
					elif 'end_time' in attrdict:
						timestamp_file.append(dict(min=t, \
							max=dt.datetime.combine(attrdict.get('end_date', \
							t.date()), attrdict.get('end_time')), incl=True))
					elif hasattr(self, 'temporal_resolution'):
						timestamp_file.append(dict(min=t, \
							max=t+self.temporal_resolution, incl='[)'))
					else:
						timestamp_file.append(t)
				elif 'end_timestamp' in attrdict or 'end_date' in attrdict and \
				  'end_time' in attrdict:
					t = attrdict.get('end_timestamp', dt.datetime.combine( \
						attrdict.get('end_date'), attrdict.get('end_time')))
					if hasattr(self, 'temporal_resolution'):
						timestamp_file.append(dict(min=t- \
							self.temporal_resolution, max=t, incl='(]'))
					else:
						timestamp_file.append(t)
				for tf in timestamp_file:
					if _apply_filters(tf, timestamp, iter_item='timestamp' in \
					  iter_filters):
						break
				else:
					continue

			# Match date information
			if date is not None:
				date_file = []
				if 'date' in attrdict:
					t = attrdict.get('date')
					if hasattr(self, 'temporal_resolution'):
						t2 = (dt.datetime.combine(t, dt.time())+ \
							self.temporal_resolution).date()
						if t2 != t:
							date_file.append(dict(min=t, max=t2, incl='[)'))
						else:
							date_file.append(t)
					else:
						date_file.append(t)
				if 'start_date' in attrdict:
					t = attrdict.get('start_date')
					if 'end_date' in attrdict:
						date_file.append(dict(min=t, max=attrdict.get('end_date'), \
							incl=True))
					elif hasattr(self, 'temporal_resolution'):
						t2 = (dt.datetime.combine(t, dt.time())+ \
							self.temporal_resolution).date()
						if t2 != t:
							date_file.append(dict(min=t, max=t2, incl='[)'))
						else:
							date_file.append(t)
					else:
						date_file.append(t)
				elif 'end_date' in attrdict:
					t = attrdict.get('end_date')
					if hasattr(self, 'temporal_resolution'):
						t0 = (dt.datetime.combine(t, dt.time())- \
							self.temporal_resolution).date()
						if t0 != t:
							date_file.append(dict(min=t0, max=t, incl='(]'))
						else:
							date_file.append(t)
					else:
						date_file.append(t)
				for df in date_file:
					if _apply_filters(df, date, iter_item='date' in \
					  iter_filters):
						break
				else:
					continue

			# Match time information
			if time is not None:
				time_file = []
				if 'time' in attrdict:
					t = attrdict.get('time')
					if hasattr(self, 'temporal_resolution'):
						xday = dt.date.today()
						t2 = (dt.datetime.combine(xday, t)+ \
							self.temporal_resolution)
						if t2.date() == xday:
							time_file.append(dict(min=t, max=t2.time(), \
								incl='[)'))
						else:
							time_file.append(dict(min=t, max=None, \
								incl=True))
					else:
						time_file.append(t)
				if 'start_time' in attrdict:
					t = attrdict.get('start_time')
					if 'end_time' in attrdict:
						time_file.append(dict(min=t, \
							max=attrdict.get('end_time'), incl=True))
					elif hasattr(self, 'temporal_resolution'):
						xday = dt.date.today()
						t2 = (dt.datetime.combine(xday, t)+ \
							self.temporal_resolution)
						if t2.date() == xday:
							time_file.append(dict(min=t, max=t2.time(), \
								incl='[)'))
						else:
							time_file.append(dict(min=t, max=None, \
								incl=True))
					else:
						time_file.append(t)
				elif 'end_time' in attrdict:
					t = attrdict.get('end_time')
					if hasattr(self, 'temporal_resolution'):
						xday = dt.date.today()
						t0 = (dt.datetime.combine(xday, t)- \
							self.temporal_resolution)
						if t0.date() == xday:
							time_file.append(dict(min=t0.time(), max=t, \
								incl='(]'))
						else:
							time_file.append(dict(min=None, max=t, incl=True))
					else:
						time_file.append(t)
				for tf in time_file:
					if _apply_filters(tf, time, iter_item='time' in \
					  iter_filters):
						break
				else:
					continue

			# Match version information
			if not _apply_filters(attrdict.get('version'), version, \
			  iter_item='version' in iter_filters):
				continue
			if not _apply_filters(attrdict.get('subversion'), subversion, \
			  iter_item='subversion' in iter_filters):
				continue

			# Match processing information
			if not _apply_filters(attrdict.get('processingtimestamp'), \
			  processingtimestamp, iter_item='processingtimestamp' in \
			  iter_filters):
				continue

			# Match file extension information
			if not _apply_filters(attrdict.get('ext'), ext, iter_item='ext' in \
			  iter_filters):
				continue
			
			# Update results with passed file
			if attrs and kwargs:
				attrdict = self.get_filename_attrs(filename, **kwargs)
			passed.append((file, attrdict) if attrs else file)
		
		# Return passed files
		return passed

	# Method to find files that match given filters
	def find_files(self, /, directory=None, query=None, iterate=True, **kwargs):
		"""Finds product files that match given filters.  The filters may be a 
		single value or a list of values, of which at least one must be found in 
		the file name.  The values may be a dictionary, that defines a range 
		between the two values, where key 'min' represents the minimum value, 
		'max' represents the maximum value, and 'incl' gives either a boolean 
		value indicating whether the min and max are inclusive or not, or a two-
		element string (e.g. '[)') where '[' and ']' represent the endpoints are 
		inclusive, and '(' and ')' represent the endpoints are exclusive.  If 
		any array-like value is given, it must be enclosed within a list or else 
		it will be interpreted as individual values.  Values extracted from the 
		file name are first converted with any formatters defined by the 
		`Instrument` or `Product` class, before being tested with these filters.  
		For the individual (non-range) filter values, they may even be of 
		`re.Pattern` type.
		
		Parameters:
			directory: type=str|pathlib.Path, default=None
				- The path to the data.  If not set, will use the 'datadir' 
				attribute of the `Product` object or `Instrument` object if one 
				exists.  Otherwise, will use the current working directory.
			query: type=bool, default=None
				- A boolean determining if the search will include online files
				or not in the results, overriding this product's `query` 
				attribute.
			iterate: type=bool, default=True
				- By default, the returned object will be a generator, iterating 
				through the file system.  However, when querying is on, the 
				results can include duplicate granules if the local files are 
				out of order due to the way subdirectories are named.  A list 
				can be returned instead (still as a generator object) without 
				these duplicate values all at once by setting this argument to 
				`False`.
			**kwargs:
				- 
		
		External Modules:
			- earthaccess -- https://earthaccess.readthedocs.io/
		
		Returns:
			- A generator object iterating through product files that meet the 
			search conditions. The generator item yields a tuple where the first 
			item is the file path (or `earthaccess.DataGranule` object if the 
			query switch is on) and the second item is a dictionary of the named 
			fields from the regex match with formatted values.
		"""
		import os
		from pathlib import Path
		import earthaccess as ea

		# Get data granules from online query
		if query is None:
			query = self.query
		if query:
			granules = self.query_data(**kwargs)

		# Get data directory
		if directory is False:
			datadir = "."
		elif directory is not None:
			datadir = str(directory)
		elif hasattr(self, 'datadir'):
			datadir = str(getattr(self, 'datadir'))
		elif hasattr(self, 'instrument'):
			datadir = str(getattr(self.instrument, 'datadir', "."))
		else:
			datadir = "."
		assert os.path.exists(datadir) and os.path.isdir(datadir)

		# Traverse directory tree
		passed = []
		passed_filenames = []
		file = None
		g = None
		for root,dirs,files in os.walk(datadir):
			# Ensure the directories are visited in order
			dirs.sort()

			# Loop thru files
			for file,attrdict in self.filter_files(sorted(files), attrs=True, \
			  **kwargs):
				# Yield online granule if it preceeds local file
				if query and iterate:
					while True:
						while g is None:
							try:
								g = next(granules)
							except:
								g = False
								break
							gfn = query_filename(g)
						if not g:
							break
						if gfn <= file:
							if gfn < file:
								if f:=self.filter_files(gfn, attrs=True, \
								  **kwargs):
									yield (g, f[0][1])
							g = None
							continue
						else:
							break

				# Yield file path and regex dictionary for matching file
				result = (Path(os.path.join(root, file)), attrdict)
				if iterate:
					yield result
				else:
					passed.append(result)
					passed_filenames.append(file)

		# Yield remaining online granules
		if query and g is not False:
			while True:
				if g is None:
					try:
						g = next(granules)
					except:
						break
				gfn = query_filename(g)
				if f:=self.filter_files(gfn, attrs=True, **kwargs):
					result = (g, f[0][1])
					if iterate:
						yield result
					else:
						passed.append(result)
						passed_filenames.append(gfn)
				g = None

		# Return ordered list if iterate off
		if not iterate:
			passed_zip = sorted(zip(passed_filenames, passed), key=lambda z: \
				(z[0], isinstance(z, ea.DataGranule)))
			old = None
			for filename,result in passed_zip:
				if filename != old:
					yield result
				old = filename

	# Method to set the product's sub-data directory
	def set_subdatadir(path=None):
		pass

	# Method to download online granule data
	def download_granule(self, /, granule, path=None, overwrite=False, **kwargs):
		"""Downloads `earthaccess` granules.
		
		Parameters:
			granule: type=earthaccess.DataGranule
				- An `earthaccess.DataGranule` object, or list of such objects.
			path: type=str|pathlib.Path, default=None
				- The path where the granule file will be downloaded to.
			overwrite: type=bool, default=False
				- If `True`, will overwrite any existing matching file at the 
				given `path`.
			**kwargs:
				- Additional keyword arguments for the following functions:
					- earthaccess.download: provider, threads, show_progress, 
					credentials_endpoint, pqdm_kwargs
		
		External Modules:
			- earthaccess -- https://earthaccess.readthedocs.io/
		
		Returns:
			- A list of downloaded granule paths.
		"""
		# import os
		import re
		from pathlib import Path
		import datetime as dt
		import numpy as np
		import earthaccess as ea
		from dateutil.relativedelta import relativedelta
		from .ancillary import iterable, validate_parameters, login

		# Log in to Earthdata
		auth = login()
		if not auth.authenticated:
			raise RuntimeError("Could not authenticate with Earthdata.")

		# Get data directory pattern automatically
		if path is None:
			# Get data directory
			filename = None
			datadir = self.datadir

			# Append sub-data directory if specified in product
			if hasattr(self, 'subdatadir'):
				datadir = datadir.joinpath(*(self.subdatadir if \
					iterable(self.subdatadir) else [self.subdatadir]))
			
			# Get sub-data directory automatically
			else:
				# Find example product file (try 25 times to find file name with 
				# unique date/time quantifiers, providing for hourly data sets)
				indices = [0,1,24,25]
				inc = np.diff([-1]+indices)
				try:
					examples = self.find_files(query=False, format=False)
					for i in inc:
						for _ in range(i):
							example,attrs_str = next(examples)
						if len(set(attrs_str.values())) == len(attrs_str):
							attrs_rev = {v:k for k,v in attrs_str.items()}
							attrs = self.get_filename_attrs(example)
							break
						else:
							example = None
				except:
					example = None
				
				# Get sub-data directory pattern from example product file
				subdatadir = []
				if example:
					subdatadir0 = list(example.parent.relative_to(datadir).parts)
					for val in subdatadir0:
						if val in attrs_rev:
							subdatadir.append(f"{{{attrs_rev[val]}}}")
						else:
							# try:
							# 	val = int(val)
							# except:
							# 	pass
							timestamps = {k:v for k,v in attrs.items() if \
								isinstance(v, (dt.date, dt.time))}
							# dt_formats = {'hour': ["%H", "%I%p"], 'day': "%d", \
							# 	'month': ["%m", "%B", "%b"], 'year': ["%Y", "%y"]}
							dt_formats = {'time': ["%H", "%I%p"], 'date': \
								["%d", "%j", "%m", "%B", "%b", "%Y", "%y"]}
							dt_formats['datetime'] = dt_formats['time'] + \
								dt_formats['date']
							subdatadir.append(None)
							# for attr,t in timestamps.items():
							# 	for dt_unit,dt_fmts in dt_formats.items():
							# 		for dt_fmt in dt_fmts if iterable(dt_fmts) \
							# 		  else [dt_fmts]:
							# 			if getattr(t, dt_unit, None) == val:
							# 				subdatadir[-1] = f"{{{attr}:{dt_fmt}}}"
							# 				break
							# 		if subdatadir[-1] is not None:
							# 			break
							# 	if subdatadir[-1] is not None:
							# 		break
							for attr,t in timestamps.items():
								if isinstance(t, dt.datetime):
									dt_fmts = dt_formats['datetime']
								elif isinstance(t, dt.date):
									dt_fmts = dt_formats['date']
								elif isinstance(t, dt.time):
									dt_fmts = dt_formats['time']
								else:
									continue
								for dt_fmt in dt_fmts:
									if f"{t:{dt_fmt}}" == val:
										subdatadir[-1] = f"{{{attr}:{dt_fmt}}}"
										break
								if subdatadir[-1] is not None:
									break
							if subdatadir[-1] is None:
								subdatadir = subdatadir[:-1]

				# Get sub-data directory pattern from opened datasets and file 
				# name attributes
				else:
					# Get dataset keys for open datasets, and product temporal 
					# resolution
					dataset_keys = getattr(self, 'dataset_keys', [])
					res = getattr(self, 'temporal_resolution', None)
					if not isinstance(res, relativedelta):
						res = relativedelta(days=res.days, \
							hours=res.seconds//3600, \
							minutes=(res.seconds % 3600)//60, \
							seconds=res.seconds % 60, \
							microseconds=res.microseconds)
					
					# Search for time-related attribute if no file loaded
					if not dataset_keys and res is not None:
						groups = re.findall(r"(?<!\\)\(\?P<(.*?)>.*?(?<!\\)\)", \
							self.filename_pattern)
						dt_terms = ['timestamp', 'start_timestamp', (['date', \
							'start_date'], ['time', 'start_time'])]
						def _find_dt_term(dt_terms):
							for dt_term in dt_terms if iterable(dt_terms) else \
							  [dt_terms]:
								if isinstance(dt_term, str):
									if dt_term in groups:
										return [dt_term]
								elif isinstance(dt_term, tuple):
									results = [_find_dt_term(dt_term) for \
										dt_term in dt_term]
									if all(results):
										return results
							return None
						dataset_keys = [term for term in _find_dt_term(dt_terms) \
							if term is not None]

					# Set new sub-data directory for product when none set
					if dataset_keys:
						for k in dataset_keys:
							if 'time' not in k and 'date' not in k:
								subdatadir.append(f"{{{k}}}")
							else:
								day = dt.datetime(1,1,1)
								if day+res < day+relativedelta(hours=1):
									subdatadir.extend([f"{{{k}:%Y}}", \
										f"{{{k}:%m}}", f"{{{k}:%d}}", \
										f"{{{k}:%H}}"])
								elif day+res < day+relativedelta(days=1):
									subdatadir.extend([f"{{{k}:%Y}}", \
										f"{{{k}:%m}}", f"{{{k}:%d}}"])
								elif day+res < day+relativedelta(months=1):
									subdatadir.extend([f"{{{k}:%Y}}", \
										f"{{{k}:%m}}"])
								elif day+res < day+relativedelta(years=1):
									subdatadir.append(f"{{{k}:%Y}}")
				
				# Add sub-data directory to data directory
				if subdatadir:
					self.subdatadir = subdatadir[0] if len(subdatadir) == 1 \
						else subdatadir
					datadir = datadir.joinpath(*subdatadir)
		
		# Get data directory and file name patterns from 'path' argument
		else:
			path = Path(path)
			if path.is_absolute():
				datadir = path if path.is_dir() else path.parent
			else:
				datadir = self.datadir
			filename = path.name if path.name else None

		# Loop thru granules and download
		gpaths = []
		for g in granule if iterable(granule) else [granule]:
			# Get path with formatters
			gfn = query_filename(g)
			# if filename is None:
			# 	path = datadir / gfn
			# else:
			# 	path = datadir
			
			# Get file name attributes
			attrs = self.get_filename_attrs(gfn)
			attrs_str = self.get_filename_attrs(gfn, format=False)

			# Get output file path
			gpath_items = [str(datadir), filename]
			for i,item in enumerate(gpath_items):
				if item is None:
					continue
				iattrs = {k:v for k,v in attrs.items()}
				groups = re.findall(r"(?<![{\\])\{(.*?)(:.*?)?(?<![}\\])\}", \
					str(item))
				for name,frmt in groups:
					if name not in iattrs and name in kwargs:
						iattrs[name] = kwargs[name]
					elif frmt is None and name in attrs_str:
						iattrs[name] = attrs_str[name]
				# gpath = Path(str(path).format(**attrs))
				gpath_items[i] = item.format(**iattrs)
			gdir = Path(gpath_items[0])
			gfile = gpath_items[1]
			gpath = gdir / (gfile or gfn)

			# Download granule
			if gpath.exists() and not overwrite:
				continue
			# gdir.mkdir(parents=True, exist_ok=True)
			download_kwargs = validate_parameters(ea.download, kwargs)
			downloaded_paths = ea.download(g, local_path=gdir, **download_kwargs)
			if filename is not None:
				for downloaded_path in downloaded_paths:
					downloaded_path = Path(downloaded_path)
					oldname = downloaded_path.name
					newname = oldname.replace(gfn, gfile)
					if oldname != newname:
						downloaded_path.rename(downloaded_path.parent / newname)
			gpaths.append(gpath)
		
		# Return list of downloaded granule paths
		return gpaths if iterable(granule) else gpaths[0]
	
	# Method to load datasets
	def load_dataset(self, /, file, reload=False, **kwargs):
		"""Initializes a dataset of the Product object from a file.
	
		Parameters:
			file: type=str|pathlib.Path
				- The file path of the dataset.
			reload: type=bool, default=False
				- If `False`, will recreate/reload the dataset only if not yet 
				created/loaded; if `True`, will always recreate/reload the 
				dataset even if it already exists.
		"""
		import os
		from .data import Dataset

		# Return previously loaded cousin dataset
		if not reload:
			filename = os.path.basename(str(file))
			loaded_datasets = self.loaded_datasets()
			if filename in loaded_datasets:
				return loaded_datasets[filename]

		# Create instance of dataset
		dataset = Dataset(file, product=self, **kwargs)

		# Return the dataset
		return dataset
	
	# Method to return a flattened dictionary of all loaded datasets
	def loaded_datasets(self):
		"""Organizes the loaded datasets into a flattened dictionary with the 
		file name as the keys.
	
		Returns:
			- A dictionary of loaded datasets with the file names as the keys.
		"""

		# Initializes dictionary
		datasets = dict()

		# Collect datasets
		if hasattr(self, 'datasets'):
			def _loop_datasets(ds_dict):
				for v in ds_dict.values():
					if isinstance(v, dict):
						_loop_datasets(v)
					else:
						datasets[v.file] = v
			_loop_datasets(self.datasets)
		
		# Return flattened dictionary of loaded datasets
		return datasets
	
	# # Method to construct pixel outlines for simulated scan
	# def simulated_pixel_outlines(self, /, **kwargs):
	# 	"""Constructs pixel outlines for a simulated scan or frame of the 
	# 	instrument based on its specifications and platform position and 
	# 	attitude.

	# 	Parameters:
	# 		**kwargs:
	# 			- Keyword argumets that will be used in place of attributes of 
	# 			the instrument or its platform, or to specify keys to use for 
	# 			attributes that are dictionaries.
	# 			- For instance, if the instrument's `ifov` attribute is a 
	# 			dictionary with keys corresponding to different spatial 
	# 			resolutions, and the keyword argument 'spatial_resolution' is 
	# 			given, its value will be used to look up the appropriate `ifov` 
	# 			value in the `ifov` dictionary.
	# 			- Use the platform's `set_state` method to set the required 
	# 			platform attributes (`latitude`, `longitude`, `altitude` and 
	# 			`heading`) if not already set and not provided here.
	# 			- The following instrument attributes are required:
	# 				- Either `scan_width` (for whiskbroom scanners) or 
	# 				`frame_width` (for pushbroom scanners)
	# 				- `swath_width`
	# 				- Either `ifov` or `pixel_scale` or both - if one is 
	# 				missing, it is assumed to be equal to the other
	# 				- `pixel_offset` (optional; assumed to be 0 if not given)

	# 	Returns:
	# 		- A tuple of two numpy ndarrays (latitudes, longitudes) with shape 
	# 		(..., 4), where the last new dimension represents the four corners 
	# 		of each pixel.
	# 	"""
	# 	import numpy as np
	# 	from pyproj import CRS
	# 	from .platform import lla2xyz, xyz2lla, uvw2ecef
	# 	from .instrument import WhiskbroomScanner, PushbroomScanner
	# 	from .ancillary import iterable, getattr_recursive, findattr

	# 	# Check for swath structure
	# 	if not getattr(self, 'structure', None) != 'swath':
	# 		raise ValueError("Simulated pixel outlines can only be created for "
	# 			"swath products.")

	# 	# Function to get attribute value, searching recursively and extracting 
	# 	# value from dictionary if necessary
	# 	def _getattr(attr, default=None):
	# 		data = kwargs[attr] if attr in kwargs else getattr_recursive(self, \
	# 			attr, None) if '.' in attr else findattr(self, attr, None)
	# 		if not isinstance(data, dict):
	# 			return data
	# 		key_name = findattr(self, f"{attr.split('.')[-1]}_key", None)
	# 		if key_name is None or key_name not in kwargs:
	# 			return default
	# 		return data.get(kwargs[key_name], default)

	# 	# Get necessary platform attributes
	# 	lat0 = _getattr('platform.latitude')
	# 	lon0 = _getattr('platform.longitude')
	# 	alt0 = _getattr('platform.altitude')
	# 	head = _getattr('platform.heading')
	# 	if lat0 is None or lon0 is None or alt0 is None or head is None:
	# 		raise ValueError("Platform latitude, longitude, altitude, and "
	# 			"heading must be set to simulate pixel outlines.")

	# 	# Get necessary instrument attributes
	# 	inst = getattr(self, 'instrument', None)
	# 	if isinstance(inst, WhiskbroomScanner):
	# 		swath_length = _getattr('scan_width')
	# 	elif isinstance(inst, PushbroomScanner):
	# 		swath_length = _getattr('frame_width')
	# 	else:
	# 		swath_length = _getattr('scan_width', _getattr('frame_width'))
	# 	swath_width = _getattr('swath_width')
	# 	ifov = _getattr('ifov')
	# 	pixel_scale = _getattr('pixel_scale', ifov)
	# 	if ifov is None:
	# 		ifov = pixel_scale
	# 	pixel_offset = _getattr('pixel_offset', 0)
	# 	if swath_length is None or swath_width is None or ifov is None or \
	# 	  pixel_scale is None or pixel_offset is None:
	# 		first_word = "Scan" if isinstance(inst, WhiskbroomScanner) else \
	# 			"Frame" if isinstance(inst, PushbroomScanner) else "Scan/frame"
	# 		raise ValueError(f"{first_word} dimensions, and IFOV and/or pixel "
	# 			"scale must be set to simulate pixel outlines.")
	# 	if not iterable(ifov):
	# 		ifov = (ifov,)*2
	# 	if not iterable(pixel_scale):
	# 		pixel_scale = (pixel_scale,)*2
	# 	if not iterable(pixel_offset):
	# 		pixel_offset = (pixel_offset,)*2

	# 	# Get angles of pixel centers in along-track (i) and across-track (j) 
	# 	# directions
	# 	swath_dims = np.array([swath_length, swath_width])
	# 	first_pix_dist = (pixel_scale*(swath_dims-1))/2
	# 	i0,j0 = np.meshgrid(*[np.linspace(-first_pix_dist[i], \
	# 		first_pix_dist[i], swath_dims[i])+pixel_offset[i]*pixel_scale[i] \
	# 		for i in range(2)], indexing='ij')
		
	# 	# Get angles of pixel corners
	# 	for ni,nj in [(-1,-1), (1,-1), (1,1), (-1,1)]:
	# 		i = i0+ni*ifov[0]/2
	# 		j = j0+nj*ifov[1]/2
	# 		try:
	# 			ipixels = np.concatenate((ipixels, i[...,None]), axis=-1)
	# 			jpixels = np.concatenate((jpixels, j[...,None]), axis=-1)
	# 		except:
	# 			ipixels = i[...,None]
	# 			jpixels = j[...,None]

	# 	# Get ENU unit vectors in direction of each pixel corner (UVW=ENU) by 
	# 	# rotating scan angles by heading and flipping z-axis
	# 	heading = np.radians(head)
	# 	alpha = np.pi-ipixels
	# 	beta = np.pi-jpixels
	# 	sa = np.sin(alpha)
	# 	sb = np.sin(beta)
	# 	upixels = np.sin(heading)*sa - np.cos(heading)*sb
	# 	vpixels = np.cos(heading)*sa + np.sin(heading)*sb
	# 	wpixels = -np.cos(alpha)*np.cos(beta)
		
	# 	# Convert LLA position and ENU view angles to ECEF coordinates
	# 	x0,y0,z0 = lla2xyz(lon0, lat0, alt0)
	# 	upixels,vpixels,wpixels = uvw2ecef(upixels, vpixels, wpixels, lat0, lon0)

	# 	# Intersect the ray for each pixel corner with the WGS84 ellipsoid
	# 	wgs84 = CRS("EPSG:4326")
	# 	ellipsoid = wgs84.ellipsoid
	# 	a = ellipsoid.semi_major_metre
	# 	b = ellipsoid.semi_minor_metre
	# 	c0 = (upixels/a)**2 + (vpixels/a)**2 + (wpixels/b)**2
	# 	c1 = 2*(x0*upixels/a**2 + y0*vpixels/a**2 + z0*wpixels/b**2)
	# 	c2 = (x0/a)**2 + (y0/a)**2 + (z0/b)**2 - 1
	# 	coef1 = -c1/(coef2:=2*c0)
	# 	coef2 = np.ma.sqrt(c1**2-4*c0*c2)/coef2
	# 	d = np.minimum(np.ma.masked_less_equal(coef1 + coef2, 0), \
	# 		np.ma.masked_less_equal(coef1 - coef2, 0))
	# 	if not np.ma.is_masked(d):
	# 		d = np.ma.getdata(d)
	# 	xpixels = x0+d*upixels
	# 	ypixels = y0+d*vpixels
	# 	zpixels = z0+d*wpixels

	# 	# Convert pixel corner coordinates from ECEF to LLA
	# 	lons,lats,alts = xyz2lla(xpixels, ypixels, zpixels)

	# 	# Return latitudes and longitudes of pixel corners
	# 	return (lats, lons)
################################### Product ###################################


#--------------------------------- FUNCTIONS ---------------------------------#

####################### (LOCAL) get_standard_product_id #######################
def _get_standard_product_id(product, available_products):
	"""Gets the standardized name (ID) of selected product from a dictionary of 
	available products.

	Parameters:
		product: type=str
			- The ID or name of the product.
		available_products: type=dict
			- A dictionary of available products within which to search for the 
			ID of the product.
	
	Returns:
		- The standardized name (ID) of the product, or `None` if not found.
	"""

	# Format input
	product = product.upper().strip()

	# Loop thru available products
	reserve_id = None
	for product_id,product_data in available_products.items():
		# Check if product in IDs and return if found
		if product == product_id.upper():
			return product_id
		
		# Check if product in name descriptions
		if reserve_id is None and ('name' in product_data if \
		  isinstance(product_data, dict) else hasattr(product_data, 'name')):
			if product == (product_data['name'] if isinstance(product_data, \
			  dict) else getattr(product_data, 'name')).upper():
				reserve_id = product_id
	
	# Return the ID for the name match if ID not matched earlier
	return reserve_id
####################### (LOCAL) get_standard_product_id #######################

############################## get_product_class ##############################
def get_product_class(product, instrument=None, platform=None):
	"""Gets the product class for the given product ID, instrument ID and 
	platform ID.

	Parameters:
		product: type=str
			The ID or name of the product.
		instrument: type=str
			The ID or name of the product's instrument.
		platform: type=str|bool, default=None
			The ID or name of the platform on which the instrument is located.  
			If `False`, will ensure that the `platform` argument of the 
			instrument class is optional.
	
	Returns:
		- The class of the given `product`, `instrument` and `platform`, or the 
		base Product class if not found.
	"""
	import sys
	import inspect
	from .instrument import Instrument, get_instrument_class
	
	# Get the instrument-specific class
	InstrumentClass = get_instrument_class(instrument, platform=platform)
	if not InstrumentClass or InstrumentClass is Instrument:
		return Product
	
	# Get the instrument-specific module
	mod = sys.modules[InstrumentClass.__module__]

	# Find and return the product-specific class
	classes = {k.upper():v for k,v in inspect.getmembers(mod, inspect.isclass)}
	return classes.get(product.upper(), Product)
############################# get_instrument_class #############################

####################### (LOCAL) find_product_instrument #######################
def _find_product_instrument(product, instrument=None, platform=None, **kwargs):
	"""Searches given (or all) Earth Science Mission instrument(s) for a 
	specified product and returns the instrument object.
	
	Parameters:
		product: type=str
			- The standardized name (ID) of the product for which to search.
		instrument: type=Instrument|str, default=None
			- The instrument associated with the product.  If `None`, will 
			search all instruments for the product.
		platform: type=Platform|str, default=None
			- The platform on which the product's instrument is located.  If 
			`None`, will search for the instrument among all available platforms.

	Returns:
		- An instance of the product's instrument if found, or `None` otherwise.
	"""
	from .platform import get_standard_platform_id
	from .instrument import Instrument, get_available_instruments, \
		get_instrument_class
	from .ancillary import iterable
	
	# Format product ID
	product = product.strip()
	
	# Get instrument object from inputs
	if instrument is not None:
		if not isinstance(instrument, Instrument):
			InstrumentClass = get_instrument_class(instrument, \
				platform=platform)
			instrument = InstrumentClass(platform=platform, **kwargs)
	
	# Search for matching product to get instrument object
	else:
		if platform:
			platform_id = get_standard_platform_id(platform)
		for i,ps in get_available_instruments(platforms=True):
			if not iterable(ps):
				ps = [ps]
			if platform and (not platform_id or platform_id not in ps):
				continue
			InstrumentClass = get_instrument_class(i, platform=ps[0])
			if InstrumentClass is Instrument:
				continue
			for p in ps:
				i = InstrumentClass(platform=p, **kwargs)
				if product.upper() in [s.upper() for s in getattr(i, \
				  'products', dict())]:
					if instrument:
						raise ValueError(f"Multiple products with ID {product} "
							"found - specify the 'instrument' argument (and "
							"'platform' if necessary).")
					instrument = i
	
	# Check for product in instrument's list of products and return
	return instrument if instrument and product.upper() in [s.upper() for s in \
		getattr(instrument, 'products', dict())] else None
####################### (LOCAL) find_product_instrument #######################

################################# load_product #################################
def load_product(product, instrument=None, platform=None, **kwargs):
	"""Create either an object of an product-specific class if available, or 
	a generic Product object otherwise.
	
	Parameters:
		product: type=str
			- The ID or name of the product.
		instrument: type=str|bool, default=None
			- The instrument associated with the product.  If `None`, will 
			search all instruments for the product.  If `False`, will ensure 
			that an Instrument object is not created, but will also create an 
			empty Product instance.
		platform: type=str|bool, default=None
			- The platform on which the product's instrument is located.  If 
			`None`, will search for the instrument among all available 
			platforms.  If `False`, will ensure that a Platform object is not 
			created.

	Returns:
		- An instance of the product.
	"""
	from types import NoneType

	# Check input types
	assert isinstance(instrument, (str, bool, NoneType))
	assert isinstance(platform, (str, bool, NoneType))

	# Get instrument with product
	instrument = _find_product_instrument(product, instrument=instrument, \
		platform=platform, **kwargs)
	
	# Load and return product instance
	return instrument.load_product(product, **kwargs) if instrument else \
		Product(product, instrument=False, **kwargs)
################################# load_product #################################

################################ query_filename ################################
def query_filename(data_granule):
	"""Gets the file name of a given `earthaccess.DataGranule` object.
	
	Parameters:
		data_granule: type=earthaccess.DataGranule
			- An `earthaccess.DataGranule` object.
	
	Returns:
		- The file name of the `data_granule`.
	"""
	# import re
	from pathlib import PurePosixPath
	from urllib.parse import urlparse, unquote
	import hashlib

	# Get file name from identifier
	# try:
	# 	for identifier in data_granule['umm']['DataGranule']['Identifiers']:
	# 		if identifier.get('IdentifierType') == 'ProducerGranuleId':
	# 			return identifier['Identifier']
	# 	raise

	# Get file name from URL
	# except:
	urls = data_granule.data_links()
	names = [unquote(PurePosixPath(urlparse(url).path).name) for url in urls]
	if not urls:
		raise ValueError("Could not find file name for data granule object.")
	elif len(urls) == 2:
		filepath,hashpath = sorted(names)
		if hashpath.lstrip(filepath+'.').lower() in \
			hashlib.algorithms_available:
			names = [filepath]
	if len(names) > 1:
		raise ValueError("Received multiple data links for data granule object.")
	return names[0]
################################ query_filename ################################

############################### check_file_hash ###############################
def check_file_hash(file, hash, digest=None, chunk_size=8192):
	"""Validates a file using a hash.
	
	Parameters:
		file: type=str
			- The file path.
		hash: type=str|IOBase
			- A path or file object of the hash file, or the hash string.
		digest: type=str, default=None
			- The digest to use.  This must be provided if a hash string is 
			given for the `hash` argument, or if the digest is undicernable from 
			the hash path name.
		chunk_size: type=str, default=None
			- The data chunk size to use when reading the file.  This is only 
			used if the Python version is <3.11.
	
	Returns:
		- `True` if the file's hash value matches the given hash, or `False` 
		otherwise.
	"""
	import os
	from pathlib import Path
	from io import IOBase
	import hashlib

	# Get the hash
	if isinstance(hash, IOBase):
		hashpath = hash.name
		hash = None if hash.closed else hash.read().rstrip('\n')
	elif isinstance(hash, str):
		if os.path.exists(hash):
			hashpath = hash
			hash = None
		else:
			hashpath = None
	elif isinstance(hash, Path):
		hashpath = str(hash)
		hash = None
	else:
		raise ValueError("`hash` must be a hash as a string, or a path or file " \
			"object to an existing hash file")
	if hash is None:
		with open(hashpath, 'r') as f:
			hash = f.read().rstrip('\n')

	# Get digest from end of file name if not provided
	if digest is None and hashpath is not None:
		for alg in hashlib.algorithms_available:
			if str(file).lower().endswith('.'+alg):
				digest = alg
				break
	if not digest:
		raise ValueError("Could not detect the digest - provide a `digest` "
			"argument.")
	
	# Use `hashlib.file_digest` for newer Python versions
	if hasattr(hashlib, 'file_digest'):
		with open(file, "rb") as f:
			return hashlib.file_digest(f, digest).hexdigest() == hash
		
	# Use the old method for older Python versions
	else:
		hasher = getattr(hashlib, digest)
		with open(file, "rb") as f:
			while chunk:=f.read(chunk_size):
				hasher.update(chunk)
		return hasher.hexdigest() == hash
############################### check_file_hash ###############################
