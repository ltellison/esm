"""Ancillary
Module of general ancillary functions.

Author:
	Luke Ellison

Version:
	0.1

History:
	v0.1, 26-Jan-2026, Luke Ellison: Module compiled.

Functions:
	iterable -- Determines if an object is iterable but not a string.
	assert_iterable -- Asserts if an object is of a given type or an iterable of 
		the given type.
	assert_slice -- Asserts a slice object, and returns a standardized version 
		if passes tests.
	validate_parameters -- Validates given dictionary or list of parameters 
		against a given function.
	login -- Logs in to Earthdata (https://urs.earthdata.nasa.gov/).
	breadth_first_search -- Performs a breadth-first path search with max 
		recursion depth and timeout options.
	getattr_recursive -- Recursively gets a multi-level attribute from an object.
	findattr -- Recursively searches an Earth Science Mission object and its 
		parents for a given attribute.
	set_attr_by_key -- Sets selected attributes from parent attribute with 
		selected keys.
	set_nadir_point -- Sets the swath and scan/frame nadir point in terms of 
		pixel indices.
	lon_convert -- Converts longitudes to be within a certain range.
	set_sigfigs -- Converts a number to have a given number of significant 
		figures.
"""

################################### iterable ###################################
def iterable(obj):
	"""Determines if an object is iterable but not a string.
	
	Parameters:
		obj: type=object
			- The object to test if a non-string iterable.
	
	External Modules:
		- numpy -- https://numpy.org/
	
	Returns:
		- A boolean value testing if the object is a non-string iterable object.
	"""
	from numpy import iterable as isiterable, isscalar
	import earthaccess as ea

	# Return if non-string iterable
	return isiterable(obj) and not isscalar(obj) and not isinstance(obj, \
		ea.DataGranule)
################################### iterable ###################################

############################### assert_iterable ###############################
def assert_iterable(obj, iterable_type=(list, tuple, set, dict), 
  item_type=None, item_none=True, item_numpy=True, item_test=None, size=None, 
  require_iterable=False):
	"""Asserts if an object is of a given type or an iterable of the given type.
	
	Parameters:
		obj: type=object
			- The object to test if a given type or iterable of given type.
		iterable_type: type=tuple, default=(list, tuple, set, dict)
			- An iterable type or tuple of iterable types to check the object 
			against.  Type checks are performed inside the iterables.
		item_type: type=type|tuple, default=None
			- A type or tuple of types to check the values against.  If `None`, 
			no type checking is performed apart from the iterable check.
		item_none: type=bool, default=True
			- If `True`, `NoneType` is added to the allowed types for `obj` 
			(except for inside iterables).
		item_numpy: type=bool, default=True
			- If `True`, will allow for numpy integer, float or character types 
			if corresponding Python types are included in `item_type` according 
			to this mapping: {`int`: `numpy.integer`, `float`: `numpy.inexact`, 
			`str`: `numpy.character`}.
		item_test: type=function, default=None
			- A function that takes an item value as input and returns a boolean 
			value indicating if the input passes the test.  A False return value 
			will result in a failed assertion.
		size: type=int|tuple|list, default=None
			- The expected size of the object if an iterable.  In the case of 
			numpy arrays, this may also be a tuple representing the shape of the 
			array.  If a list is given, must be a two-element list of 
			[lower bound, upper bound] sizes (does not allow for numpy array s
			hapes).  Use `None` for either bound if boundless.
		require_iterable: type=bool, default=False
			- If `True`, will require that `obj` is an iterable.
	
	External Modules:
		- numpy -- https://numpy.org/
	"""
	from types import NoneType
	import numpy as np

	# Check input types
	assert isinstance(item_type, (NoneType, type)) or isinstance(item_type, \
		tuple) and all(isinstance(t, type) for t in item_type)
	assert isinstance(iterable_type, type) or isinstance(iterable_type, tuple) \
		and all(isinstance(t, type) for t in iterable_type)
	assert item_test is None or callable(item_test)
	assert isinstance(size, (NoneType, int)) or isinstance(size, list) and \
		len(size) == 2 and all(isinstance(s, (NoneType, int)) for s in size) or \
		isinstance(size, tuple) and all(isinstance(s, int) for s in size)
	
	# Add Numpy equivalent types to item_types
	if item_numpy and item_type is not None:
		if not iterable(item_type):
			item_type = (item_type,)
		if int in item_type and not (np.integer in item_type or np.number \
		  in item_type or np.generic in item_type):
			item_type += (np.integer,)
		if float in item_type and not (np.inexact in item_type or \
		  np.number in item_type or np.generic in item_type):
			item_type += (np.inexact,)
		if str in item_type and not (np.character in item_type or \
		  np.flexible in item_type or np.generic in item_type):
			item_type += (np.character,)

	# Check item type and test function
	if not require_iterable and not iterable(obj):
		if item_type is None and item_test is None:
			raise ValueError("'item_type' and/or 'item_test' must be set in "
				"order to test scalar values, or else 'require_iterable' must "
				"be True to skip this test.")
		if item_type is not None:
			if item_none:
				assert isinstance(obj, (NoneType,)+item_type)
			else:
				assert isinstance(obj, item_type)
		if item_test is not None:
			assert obj is None or item_test(obj)

	# Check iterable type and contents
	else:
		# Check iterable type
		assert iterable(obj)
		assert isinstance(obj, iterable_type)

		# Check item types within iterable
		if item_type is not None:
			if isinstance(obj, set):
				assert all(isinstance(v, item_type) for v in list(obj))
			elif isinstance(obj, dict):
				assert all(isinstance(v, item_type) for v in obj.values())
			elif isinstance(obj, np.ndarray):
				assert np.issubdtype(obj.dtype, item_type)
			else:
				assert all(isinstance(v, item_type) for v in obj)

		# Check iterable size
		obj_size = getattr(obj, 'size', len(obj))
		if isinstance(size, int):
			assert obj_size == size
		elif isinstance(size, list):
			assert (size[0] is None or obj_size >= size[0]) and (size[1] is \
				None or obj_size <= size[1])
		elif isinstance(size, tuple):
			if not isinstance(obj, np.ndarray):
				obj = np.array(obj)
			assert obj.shape == size
		
		# Check test function
		if item_test is not None:
			if isinstance(obj, set):
				assert all(item_test(v) for v in list(obj))
			elif isinstance(obj, dict):
				assert all(item_test(v) for v in obj.values())
			elif isinstance(obj, np.ndarray):
				assert all(item_test(v) for v in obj.flat)
			else:
				assert all(item_test(v) for v in obj)
############################### assert_iterable ###############################

################################# assert_slice #################################
def assert_slice(s):
	"""Asserts a slice object, and returns a standardized version if passes 
	tests.
	
	Parameters:
		s: type=slice|int|tuple|list
			- A slice object.
	
	External Modules:
		- numpy -- https://numpy.org/
	
	Returns:
		- Provided the tests are passed, returns a standardized version of the 
		slice, where lists if ints are used for iterables of integers.
	"""
	from types import NoneType, EllipsisType
	import numpy as np

	# Settings
	scalar_types = (slice, int, np.integer, NoneType, EllipsisType)

	# Test scalar single dimension slice
	if not iterable(s):
		assert isinstance(s, scalar_types)
		return s

	# Test iterable single dimension slice
	elif not isinstance(s, tuple):
		assert_iterable(s, (list, np.ndarray), int, require_iterable=True)
		return s if isinstance(s, list) else s.tolist()
	
	# Test multi-dimensional slice
	else:
		s2 = list(s)
		for i,elem in enumerate(s):
			if not iterable(elem):
				assert isinstance(elem, scalar_types)
			else:
				assert_iterable(elem, (tuple, list, np.ndarray), int, \
					require_iterable=True)
				if isinstance(elem, tuple):
					s2[i] = [int(e) for e in elem]
				elif isinstance(elem, np.ndarray):
					s2[i] = elem.tolist()
		return tuple(s2)
################################# assert_slice #################################

############################# validate_parameters #############################
def validate_parameters(func, params, **kwargs):
	"""Validates given dictionary or list of parameters against a given function.
	
	Parameters:
		func: type=function
			- A function for which to check its parameters against the given 
			parameters.
		params: type=dict|list
			- A list of parameter names or dictionary of parameter names and 
			their values.
		**kwargs:
			- Accepts additional keyword arguments for the following classes:
				- inspect.Parameter: empty, name, default, annotation, kind
	
	Returns:
		- A dictionary or list matching the given `params` argument type with 
		items not part of the `func` function definition or those that do not 
		pass the given values or functions of the `inspect.Parameter` attributes 
		in `**kwargs` removed.
	"""
	import inspect

	# Define Exception class to exit nested loops
	class ContinueOuterLoop(Exception):
		pass

	# Initialize accepted dictionary/list of parameters
	isdict = isinstance(params, dict)
	func_params = {} if isdict else []

	# Loop thru parameters in function
	for param in inspect.signature(func).parameters.values():
		# Eliminate parameter if name not available
		if param.name not in params:
			continue
		
		# Eliminate parameter if parameter attributes don't pass check
		try:
			for k,v in kwargs.items():
				vparam = getattr(param, k)
				if callable(v):
					if not v(vparam):
						raise ContinueOuterLoop
				elif v != vparam:
					try:
						if type(v)(vparam) != v:
							raise ContinueOuterLoop
					except Exception as e:
						if isinstance(e, ContinueOuterLoop):
							raise
		except ContinueOuterLoop:
			continue
		
		# Add parameter to dictionary/list of accepted parameters
		if isdict:
			func_params.update({param.name, params[param.name]})
		else:
			func_params.append(param.name)

	# Return dictionary/list of accepted parameters
	return func_params
############################# validate_parameters #############################

#################################### login ####################################
def login(reload=False, **kwargs):
	"""Logs in to Earthdata (https://urs.earthdata.nasa.gov/).
	
	Parameters:
		reload: type=bool, default=False
			- A boolean determining whether a fresh login session should be 
			executed.
		**kwargs:
			- Accepts additional keyword arguments for the following 
			functions:
				- earthaccess.login: strategy, persist, system
	
	External Modules:
		- earthaccess -- https://earthaccess.readthedocs.io/
	
	Returns:
		- An `earthaccess.Auth` authentication object.
	"""
	import inspect
	import earthaccess as ea
	from . import config

	# Login if not logged in or reload requested or failed previous login
	if config.AUTH is None or reload or config.AUTH.authenticated is False:
		if kwargs:
			login_params = list(inspect.signature(ea.login).parameters)
			login_kwargs = {k:v for k,v in kwargs.items() if k in login_params}
		else:
			login_kwargs = dict()
		config.AUTH = ea.login(**login_kwargs)
	
	# Return authentication object
	return config.AUTH
#################################### login ####################################

############################# breadth_first_search #############################
def breadth_first_search(relpath, root_dir=".", max_level=None, timeout=10):
	"""Performs a breadth-first path search with max recursion depth and timeout 
	options.
	
	Parameters:
		relpath: type=str|pathlib.Path
			- The relative path to search for within the root directory.
		root_dir: type=str|pathlib.Path, default="."
			- The root directory within which to search.
		max_level: type=int, default=None
			- The maximum recursion depth for search.  A value of `None` 
			indicates an infinite depth.
		timeout: type=int|float, default=10
			- The number of seconds before the search times out and returns 
			`None`.
	
	Returns:
		- The first occurrence of the path in a breadth-first search, or `None` 
		if path not found or if timeout occurs.
	"""
	import warnings
	from pathlib import Path
	import os
	import threading

	# Function to walk through directories only at one level at a time
	def _search(relpath, root_dir, max_level, results):
		# Initialization
		relpath = str(relpath)
		root_dir = str(root_dir)
		search_list = [root_dir]
		level = 0

		# Loop while unsearched directories exist
		while search_list:
			# Check for max level
			level += 1
			if max_level is not None and level > max_level:
				results.append(None)
				return
			
			# Search for match
			for _ in range(len(search_list)):
				for item in os.scandir(root:=search_list.pop(0)):
					if relpath.startswith(item.name) and os.path.exists(path:= \
					  os.path.join(root, relpath)):
						results.append(path)
						return
					elif item.is_dir():
						search_list.append(item.path)
			search_list.sort(reverse=True)
		
		# Return None if no more directories to search
		results.append(None)

	# Initialize mutable array for results
	results = []

	# Use interruptable thread for search
	thread = threading.Thread(target=_search, args=(relpath, root_dir, \
		max_level, results), daemon=True)
	thread.start()
	thread.join(timeout)

	# Return search result
	if thread.is_alive():
		warnings.warn("\033[38;5;208mTimeout occurred when searching for "
			f"directory '{relpath}' in '{root_dir}'.\033[0m", stacklevel=2)
		return None
	else:
		return results[0] and Path(results[0])
############################# breadth_first_search #############################

############################## getattr_recursive ##############################
def getattr_recursive(obj, *args, dicts=False):
	"""Recursively get a multi-level attribute from an object.
	
	Parameters:
		obj: type=object
			- The object from which to get the attribute.
		attr: type=str
			- The attribute name/location to get.  Successive levels of 
			attributes should be separated by periods (e.g. 
			`instrument.platform.id`).
		default: type=object, optional
			- The default value to return if `attr` is not found.  If not 
			provided, an `AttributeError` is raised if `attr` is not found.
		dicts: type=bool, default=False
			- If `True`, will allow traversing into dictionaries as well as 
			attributes of classes.
	
	Returns:
		- The value of the attribute if found, or raises an `AttributeError` if 
		not found (or `KeyError` if `dicts` is `True` and current object is a 
		dictionary).
	"""

	# Check input parameters
	if len(args) < 1 or len(args) > 2:
		raise AttributeError("Must provide two or three arguments.")
	isdefault = len(args) == 2
	if isdefault:
		attr,default = args
	else:
		attr = args[0]
	assert isinstance(attr, str) and attr

	# Validate attribute name
	attr = attr.strip().strip('.')

	# Determine if object is a dictionary
	isdict = dicts and isinstance(obj, dict)

	# Recursively get attribute
	if '.' in attr:
		attrs = attr.split('.')
		if not (attrs[0] in obj if isdict else hasattr(obj, attrs[0])):
			if isdefault:
				return default
			elif isdict:
				raise KeyError(f"Key '{attrs[0]}' not found in dictionary.")
			else:
				raise AttributeError(f"Attribute '{attrs[0]}' not found in "
					"object.")
		attr = obj[attrs[0]] if isdict else getattr(obj, attrs[0])
		attr2 = '.'.join(attrs[1:])
		return getattr_recursive(attr, attr2, default) if isdefault else \
			getattr_recursive(attr, attr2)
	elif isdict:
		return obj.get(attr, default) if isdefault else obj[attr]
	else:
		return getattr(obj, attr, default) if isdefault else getattr(obj, attr)
############################## getattr_recursive ##############################

################################## find_attr ##################################
def findattr(obj, *args, top_level=None, parent=False, group=None):
	"""Recursively search an Earth Science Mission object and its parents for a 
	given attribute.
	
	Parameters:
		obj: type=object
			- The object from where to start the search for `attr`.
		attr: type=str
			- The attribute name to find.  If not found in the object, parent 
			objects will be searched recursively all the way up to the 
			`Platform` object (or class given by `top_level`) until it is 
			located.
		default: type=object, optional
			- The default value to return if `attr` is not found.  If not 
			provided, an `AttributeError` is raised if the attribute is not 
			found.
		group: type=str|list, default=None
			- The key of a dictionary within which to search for `attr`.  Set to 
			a list of keys to search within multiple dictionaries.  Use `None` 
			(even within a list) to specify searching for an attribute of the 
			object directly.
		top_level: type=type, default=None
			- If provided, the program will discontinue the recursive search 
			after this data type is encountered.
		parent: type=bool, default=False
			- If `True`, will return the parent object along with the attribute 
			value.
	
	Returns:
		- The value of the attribute if found, or returns the default value or 
		raises an `AttributeError` if not found.  If `parent` is `True`, returns 
		the tuple: (attribute value, parent object).
	"""
	from .platform import Platform
	from .instrument import Instrument
	from .product import Product
	from .data import Dataset
	from .ancillary import iterable

	# Check input parameters
	if len(args) < 1 or len(args) > 2:
		raise AttributeError("Must provide two or three arguments.")
	isdefault = len(args) == 2
	if isdefault:
		attr,default = args
	else:
		attr = args[0]
	assert isinstance(attr, str) and attr
	assert top_level is None or isinstance(top_level, type)

	# Validate attribute name
	attr = attr.strip()

	# Ensure group is a list
	group = list(group) if iterable(group) else [group]

	# Find attribute recursively
	seq = [(Platform, None), (Instrument, 'platform'), (Product, 'instrument'), 
		(Dataset, 'product'), (None, 'dataset')]
	for test_type,parent_attr in seq:
		if test_type and not isinstance(obj, test_type):
			continue
		for key in group:
			if key is None and hasattr(obj, attr):
				attr_val = getattr(obj, attr)
			elif key is not None and isinstance(d:=getattr(obj, key, None), dict) and attr in d:
				attr_val = d[attr]
			else:
				continue
			return (attr_val, obj) if parent else attr_val
		if not parent_attr or top_level is not None and isinstance(obj, \
		  top_level) or not hasattr(obj, parent_attr):
			if isdefault:
				return default
			else:
				raise AttributeError("Reached the top level object before "
					f"attribute '{attr}' found.")
		else:
			return findattr(getattr(obj, parent_attr), *args, group=group, \
				top_level=top_level, parent=parent)
################################## find_attr ##################################

############################### set_attr_by_key ###############################
def set_attr_by_key(obj, attr_name, change=False, value=False, 
  empty=False, silent=False):
	"""Sets selected attributes from parent attribute with selected keys.

	Parameters:
		obj: type=object
			- The object to which the selected attribute(s) will be saved.
		attr_name: type=str
			- The attribute name that will be searched for in parent objects.
		change: type=bool, default=False
			- If `True`, will not save any attributes that are not a subset of 
			the original attribute found in a parent object.
		value: type=bool, default=False
			- If `True`, will only save final values, i.e. no dictionaries with 
			multiple possible values.
		empty: type=bool, default=False
			- If `True` and `change` is `False`, will set any subset of 
			attributes that result in an empty dictionary to `None` in the given 
			object.
		silent: type=bool, default=False
			- If `True`, will supress any exceptions raised, such as when an 
			attribute is not found.
	"""

	# Get attribute value and parent object of attribute
	try:
		attr_val,attr_parent = findattr(obj, attr_name, parent=True)
	except:
		if silent:
			return
		else:
			raise

	# Check if attribute value is a dictionary
	if isinstance(attr_val, dict):
		# Get associate attribute key name
		attr_key_name = f"{attr_name}_key"
		try:
			attr_key = getattr(attr_parent, attr_key_name)
		except:
			if silent:
				return
			else:
				raise
		
		# Get attribute key value(s)
		if '.' in attr_key:
			i = attr_key.index('.')
			attr_key = (attr_key[:i], attr_key[i+1:])
		else:
			attr_key = (attr_key, None)
		try:
			attr_key_val = findattr(obj, attr_key[0])
			if attr_key[1] is not None:
				attr_key_val = getattr_recursive(attr_key_val, attr_key[1])
		except:
			if silent:
				return
			else:
				raise
		
		# Check if iterable attribute keys
		if iterable(attr_key_val):
			# Check if no change in dictionary items
			if change and len(attr_val) > 1 and all(k in attr_key_val for k in \
			  attr_val):
				return
			
			# Save selected attribute value(s)
			iattr_val = {k:v for k,v in attr_val.items() if k in \
				attr_key_val}
			if not value and len(iattr_val) >= 2:
				setattr(obj, attr_name, iattr_val)
				setattr(obj, attr_key_name, attr_key)
			elif len(iattr_val) == 1:
				setattr(obj, attr_name, list(iattr_val.values())[0])
			elif empty and not iattr_val:
				setattr(obj, attr_name, None)
		
		# Save selected attribute value
		elif attr_key_val in attr_val:
			setattr(obj, attr_name, attr_val[attr_key_val])
		
		# Save empty attribute
		elif empty:
			setattr(obj, attr_name, None)

	# Save attribute to current object
	elif not change:
		setattr(obj, attr_name, attr_val)
############################### set_attr_by_key ###############################

############################### set_nadir_point ###############################
def set_nadir_point(obj):
	"""Sets the swath and scan/frame nadir point in terms of pixel indices.

	Parameters:
		obj: type=object
			- The object to which to save the nadir points.
	"""
	from .platform import Platform
	from .instrument import Instrument, WhiskbroomScanner, PushbroomScanner

	# Get specs
	swath_width = findattr(obj, 'swath_width', None)
	swath_length = findattr(obj, 'swath_length', None)
	scan_width = findattr(obj, 'scan_width', None)
	frame_width = findattr(obj, 'frame_width', None)
	pixel_scale = findattr(obj, 'pixel_scale', getattr(obj, 'ifov', None))

	# Stop if missing information
	if any(item is None or isinstance(item, dict) for item in \
	  [swath_width, pixel_scale]) or all(item is None or isinstance(item, \
	  dict) for item in [swath_length, scan_width, frame_width]):
		return
	
	# Make specs 2D
	pixel_offset = findattr(obj, 'pixel_offset', 0)
	if not iterable(pixel_offset):
		pixel_offset = (pixel_offset,)*2
	if not iterable(pixel_scale):
		pixel_scale = (pixel_scale,)*2
	
	# Get platform attitude
	p = obj if isinstance(obj, Platform) else getattr(obj, 'platform', None)
	platform_attitude = None if p is None else getattr(p, 'attitude', None)

	# Get instrument orientation
	i = obj if isinstance(obj, Instrument) else getattr(obj, 'instrument', None)
	instrument_attitude = None if i is None else getattr(i, 'orientation', None)

	# Get pitch and roll angles in radians
	if platform_attitude is not None and instrument_attitude is not None:
		_,pitch,roll = (platform_attitude* \
			instrument_attitude).as_euler('ZYX')
	elif platform_attitude is not None:
		_,pitch,roll = platform_attitude.as_euler('ZYX')
	elif instrument_attitude is not None:
		_,pitch,roll = instrument_attitude.as_euler('ZYX')
	else:
		pitch = roll = 0
	
	# Reverse cross-track direction if necessary
	reversed_cross_track = findattr(obj, 'reversed_cross_track', False)
	if reversed_cross_track:
		# pixel_offset = (pixel_offset[0], -pixel_offset[1])
		roll *= -1
	
	# Set the swath nadir point
	if swath_length is not None:
		obj.swath_nadir_point = ((swath_length-1)//2-pixel_offset[0]- \
			pitch/pixel_scale[0], (swath_width-1)//2-pixel_offset[1]- \
			roll/pixel_scale[1])
	
	# Set the scan/frame nadir point
	if isinstance(i, WhiskbroomScanner):
		frame_width = None
	elif isinstance(i, PushbroomScanner):
		scan_width = None
	for label,width in [('scan', scan_width), ('frame', frame_width)]:
		if width is not None:
			setattr(obj, f"{label}_nadir_point", ((width-1)//2-pixel_offset[0]- \
				pitch/pixel_scale[0], (swath_width-1)//2-pixel_offset[1]- \
				roll/pixel_scale[1]))
			break
############################### set_nadir_point ###############################

################################# lon_convert #################################
def lon_convert(lons, centlon=0, radians=False):
	"""Converts longitudes to be within a certain range.
	
	Parameters:
		lons: type=float
			- The longitude(s) to center around `centlon`.
		centlon: type=float, default=0
			- The longitude around which the resulting longitudes should be 
			centered.
		radians: type=bool, default=False
			- If set to `True`, it signifies that the inputs `lon` and `centlon` 
			are given in units of radians instead of degrees.
	
	External modules:
		- numpy -- https://numpy.org/
	
	Returns:
		- The longitudes from input `lon` converted to be within closest range 
		of `centlon`.
	"""
	import numpy as np
	
	# Convert to numpy array if list or tuple
	convert = type(lons) if type(lons) in [list, tuple] else False
	if callable(convert) or np.iterable(lons) and not isinstance(lons, \
	  np.ndarray):
		lons = np.array(lons)
	
	# Define pi with correct units
	pi = (radians and np.pi or 180)
	
	# Get longitude limits
	lonmin = centlon - pi
	lonmax = centlon + pi
	
	# Get lon to within ballpark
	lons = lons + 2*pi*(np.trunc(centlon/(2*pi)) - \
		np.trunc(lons/(2*pi))).astype(int)
	
	# Fit lon within limits (`astype` needed to avoid rounding errors from 
	# `trunc` being float16 type)
	lons += 2*pi*(np.trunc(lons < lonmin) - np.trunc(lons > lonmax)).astype(int)
	
	# Convert back to list
	if callable(convert):
		lons = convert(lons)
	
	# Return
	return lons
################################# lon_convert #################################

################################# set_sigfigs #################################
def set_sigfigs(number, sigfigs):
	"""Converts a number to have a given number of significant figures.
	
	Parameters:
		number: type=float
			- The number to set its significant figures.
		sigfigs: type=int
			- The number of significant figures to set the `number` to.
	
	External Modules:
		- numpy -- https://numpy.org/
	
	Returns:
		- The given `number` with the number of significant figures given by 
		`sigfigs`.
	"""
	import numpy as np

	# Check input types
	assert np.issubdtype(type(number), np.number)
	assert np.issubdtype(type(sigfigs), np.integer)

	# Get the least significant digit for number to given significant figures
	msd = -np.floor(np.log10(abs(number))).astype(int)
	lsd = msd+sigfigs-1

	# Return the number with given significant digits
	return round(number, lsd)
################################# set_sigfigs #################################
