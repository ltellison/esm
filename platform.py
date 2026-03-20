"""Platform
Module for creating and operating on classes of Earth Science Mission platforms.

Author:
	Luke Ellison

Version:
	0.1

History:
	v0.1, 03-Dec-2025, Luke Ellison: Module compiled.
	
Classes:
	Platform -- Defines an Earth Science Mission platform object.
	Satellite -- Defines an Earth Science Mission satellite object in orbit.
	Aircraft -- Defines an Earth Science Mission aircraft support object in 
		flight.

Functions:
	get_available_platforms -- Gets a list of all available platforms.
	get_standard_platform_id -- Gets the standardized name (ID) of the specified 
		platform.
	load_platform -- Creates either a Satellite or Aircraft object by searching 
		for its ID, or default to a general Platform object.
	xyz2lla -- Transforms ECEF X/Y/Z coordinates to longitude/latitude/altitude 
		coordinates in the WGS84 coordinate system.
	lla2xyz -- Converts WGS84 longitude/latitude/altitude coordinates to ECEF 
		X/Y/Z coordinates.
	uvw2enu -- Converts ECEF U/V/W vector coordinates to East-North-Up vector 
		coordinates at a given latitude and longitude.
	uvw2ecef -- Converts East-North-Up U/V/W vector coordinates to ECEF vector 
		coordinates at a given latitude and longitude.
"""

#---------------------------------- CLASSES ----------------------------------#

################################### Platform ###################################
class Platform:
	"""Defines an Earth Science Mission platform object.
	
	Functions:
		__init__ -- Initializes an Earth Science Mission platform object.
		set_state -- Sets the platform state (position, velocity).
		load_instrument -- Initializes an instrument on the Platform object.
	
	Returns:
		- An object defining an Earth Science Mission platform, including meta 
		data such as instrument payloads, and optionally including state 
		information.
	"""
	# from .config import EARTH_RADIUS as earth_radius
	
	# Constructor method
	def __init__(self, /, id, meta=None, load_instrument=None, \
	  available_platforms=dict(), **kwargs):
		"""Initializes an Earth Science Mission platform object.
	
		Parameters:
			id: type=str
				- The standardized name (ID) of the platform or one of its 
				alternative IDs or names.  If not found, will still create a 
				Platform object with no meta information or instruments.  To 
				fill in this data, use the 'meta' parameter.
			meta: type=dict, default=None
				- Information that will be added to the default information for 
				the given platform (duplicate keys in the default information 
				are overwritten).
			load_instrument: type=str|list|bool, default=None
				- The standardized name (ID) or list of IDs of the instrument 
				payload.  If True, will initialize all instruments on the 
				platform.  If None, only the instruments' metadata will be 
				recorded as a dictionary object.
		"""
		
		# Get standardized platform ID
		platform_id = _get_standard_platform_id(id, available_platforms)

		# Get meta data for given platform and any extra information
		if platform_id:
			platform_data = available_platforms[platform_id]
		else:
			platform_id = id.lower().strip()
			platform_data = dict()
		if meta is not None:
			platform_data.update(meta)

		# Save platform info
		self.id = platform_id
		for k,v in platform_data.items():
			setattr(self, k, v.copy() if hasattr(v, 'copy') else v)
		
		# Set state, if applicable
		try:
			self.set_state(**kwargs)
		except:
			pass

		# Initialize all instruments on the platform
		if load_instrument is not None:
			_ = self.load_instrument(load_instrument, **kwargs)
	
	# Magic method for representation output
	def __repr__(self):
		class_path = '.'.join([self.__module__, self.__class__.__qualname__])
		return f"<{class_path}({self.id})>"
	
	# Magic method for string output
	def __str__(self):
		class_name = self.__class__.__name__
		return f"{class_name}({getattr(self, 'name', self.id)})"

	# Method to set the platform state information (position, velocity, time)
	def set_state(self, /, *, lat=None, lon=None, alt=None, ortho_alt=None, 
	  elev=None, ortho_elev=None, und=None, h=None, vel=None, course=None, 
	  head=None, pitch=None, roll=None, time=None, crs=None, reset=True, 
	  **kwargs):
		"""Sets the platform's state information, namely:
		- Position: latitude, longitude, altitude, elevation, height
		- Velocity: direction (2D/3D vector), course, heading, velocity 
		(2D/3D vector), speed
		- Time: time
		The saved attributes will be in the WGS-84 CRS.  If the input values are 
		not already in this coordinate system, use the `crs` argument to specify.
	
		Parameters:
			lat: type=float, default=None
				- The platform's geodetic latitude in degrees.
			lon: type=float, default=None
				- The platform's geodetic longitude in degrees.
			alt: type=float, default=None
				- The platform's altitude from the ellipsoid surface.
			ortho_alt: type=float, default=None
				- The orthometric altitude, which is the altitude from the 
				geoid.  Must also provide the `und` argument.  Ignored if `alt` 
				is set.
			elev: type=float, default=None
				- The elevation of the nadir terrain point from the ellipsoid 
				surface.
			ortho_elev: type=float, default=None
				- The orthometric elevation, which is the eleveation from the 
				geoid.  Must also provide the `und` argument.  Ignored if `elev` 
				is set.
			und: type=float, default=None
				- The undulation, or geoid height, which is the difference 
				between the ellipsoidal and orthometric elevations (positive 
				values when geoid is above the ellipsoid.)
			h: type=float, default=None
				- The platform's height above the surface at nadir.
			vel: type=float, default=None
				- The platform's velocity, which can be given as either a scalar 
				speed or as a 2- or 3-element vector in the NED coordinate 
				system.
			course: type=float, default=None
				- The platform's course (direction of motion; clockwise from 
				North) in degrees.  Ignored if `vel` is given as a vector.  If 
				`None` and `vel` is not a vector, will be set to `head`.
			head: type=float, default=None
				- The platform's heading/bearing (orientation; clockwise from 
				North) in degrees.  If `None`, will be set to `course`.  The 
				difference between `course` and `head` is the yaw angle (Z-axis, 
				down).
			pitch: type=float, default=None
				- The platform's pitch angle in degrees (Y-axis, starboard).
			roll: type=float, default=None
				- The platform's roll angle in degrees (X-axis, forward).
			time: type=datetime.datetime, default=None
				- The UTC time of the moment goverend by the state information.
			crs: type=object, default=None
				- The coordinate reference system of the relevant arguments.  
				These will be transformed to EPSG:4326 (WGS-84) before being 
				saved as attributes.
			reset: type=bool, default=True
				- If `True`, will reset all the state information before setting 
				the new values; otherwise, will use the pre-saved values in 
				place of missing arguments.

		External modules:
			- pyproj -- https://pyproj4.github.io/pyproj/
			- numpy -- https://numpy.org/
		"""
		from types import NoneType
		import datetime as dt
		from pyproj.crs import CRS
		import numpy as np
		from scipy.spatial.transform import Rotation
		from .ancillary import assert_iterable, lon_convert
		
		# Check input formats
		assert isinstance(lat, (NoneType, float, np.floating, int, np.integer))
		assert isinstance(lon, (NoneType, float, np.floating, int, np.integer))
		assert isinstance(alt, (NoneType, float, np.floating, int, np.integer))
		assert isinstance(ortho_alt, (NoneType, float, np.floating, int, \
			np.integer))
		assert isinstance(elev, (NoneType, float, np.floating, int, np.integer))
		assert isinstance(ortho_elev, (NoneType, float, np.floating, int, \
			np.integer))
		assert isinstance(und, (NoneType, float, np.floating, int, np.integer))
		assert isinstance(h, (NoneType, float, np.floating, int, np.integer))
		assert np.iterable(vel) and not np.isscalar(vel) and len(vel) in [2,3] \
			or isinstance(vel, (NoneType, float, np.floating, int, np.integer))
		assert isinstance(course, (NoneType, float, np.floating, int, np.integer))
		assert isinstance(head, (NoneType, float, np.floating, int, np.integer))
		assert isinstance(pitch, (NoneType, float, np.floating, int, np.integer))
		assert isinstance(roll, (NoneType, float, np.floating, int, np.integer))
		assert isinstance(time, (NoneType, dt.datetime))
		assert_iterable(crs, (tuple, list, np.ndarray), (str, int, CRS), size=2)

		# Set missing arguments from saved attributes
		def _set_arg(arg, name):
			return getattr(self, name, None) if arg is None and not reset else \
				arg
		lat = _set_arg(lat, 'latitude')
		lon = _set_arg(lon, 'longitude')
		alt = _set_arg(alt, 'altitude')
		ortho_alt = _set_arg(ortho_alt, 'orthometric_altitude')
		elev = _set_arg(elev, 'elevation')
		ortho_elev = _set_arg(ortho_elev, 'orthometric_elevation')
		und = _set_arg(und, 'undulation')
		h = _set_arg(h, 'height')
		vel = _set_arg(vel, 'velocity')
		course = _set_arg(course, 'course')
		head = _set_arg(head, 'heading')
		pitch = _set_arg(pitch, 'pitch')
		roll = _set_arg(roll, 'roll')
		time = _set_arg(time, 'time')
		crs = _set_arg(crs, 'crs')
		
		# Set undulation
		if alt is not None and ortho_alt is not None and und is not None and \
		  not np.isclose(ortho_alt, alt-und):
			raise ValueError("'alt', 'ortho_alt' and 'und' are inconsistent "
				"with one another.")
		if elev is not None and ortho_elev is not None and und is not None and \
		  not np.isclose(ortho_elev, elev-und):
			raise ValueError("'elev', 'ortho_elev' and 'und' are inconsistent "
				"with one another.")
		if alt is not None and ortho_alt is not None and elev is not None and \
		  ortho_elev is not None and not np.isclose(alt-ortho_alt, \
		  elev-ortho_elev):
			raise ValueError("Using 'alt' and 'ortho_alt' results in a "
				"different undulation than using 'elev' and 'ortho_elev.")
		if und is not None:
			self.undulation = und
		elif alt is not None and ortho_alt is not None:
			self.undulation = und = alt-ortho_alt
		elif elev is not None and ortho_elev is not None:
			self.undulation = und = elev-ortho_elev
		else:
			und = None

		# Set altitude information
		if alt is not None:
			self.altitude = alt
		elif ortho_alt is not None and und is not None:
			self.altitude = alt = ortho_alt+und
		if ortho_alt is not None:
			self.orthometric_altitude = ortho_alt
		elif alt is not None and und is not None:
			self.orthometric_altitude = ortho_alt = alt-und

		# Set elevation information
		if elev is not None:
			self.elevation = elev
		elif ortho_elev is not None and und is not None:
			self.elevation = elev = ortho_elev+und
		if ortho_elev is not None:
			self.orthometric_elevation = ortho_elev
		elif elev is not None and und is not None:
			self.orthometric_elevation = ortho_elev = elev-und
		
		# Set height information
		if h is not None:
			if alt is not None and elev is not None:
				if not np.isclose(alt, elev+h):
					raise ValueError("Given altitude, elevation and height are "
						"inconsistent with each other.")
			self.height = h
		elif alt is not None and elev is not None:
			self.height = h = alt-elev
		elif ortho_alt is not None and ortho_elev is not None:
			self.height = h = ortho_alt-ortho_elev

		# Set location information
		if crs is not None:
			crs_to = "epsg:4326"
			if und is not None:
				_,_,und = _transform_crs(crs, crs_to, lon, lat, und, \
					always_xy=True)
				self.undulation = und
			if alt is not None:
				_,_,alt = _transform_crs(crs, crs_to, lon, lat, alt, \
					always_xy=True)
				self.altitude = alt
			if ortho_alt is not None:
				if alt is not None and und is not None:
					self.orthometric_altitude = ortho_alt = alt-und
				else:
					ortho_alt = None
					delattr(self, 'orthometric_altitude')
			if elev is not None:
				_,_,elev = _transform_crs(crs, crs_to, lon, lat, elev, \
					always_xy=True)
				self.elevation = elev
			if ortho_elev is not None:
				if elev is not None and und is not None:
					self.orthometric_elevation = ortho_elev = elev-und
				else:
					ortho_elev = None
					delattr(self, 'orthometric_elevation')
			if lat is not None and lon is not None:
				lon,lat,_ = _transform_crs(crs, crs_to, lon, lat, 0, \
					always_xy=True)
		if lat is not None and lon is not None:
			self.latitude = lat
			self.longitude = lon_convert(lon)

		# Set velocity etc. information
		if vel is not None:
			if np.iterable(vel):
				self.speed = np.linalg.norm(vel)
				self.velocity = np.zeros(3)
				self.velocity[:len(vel)] = vel
				self.direction = self.velocity/self.speed
				self.course = lon_convert(np.degrees(np.arctan2( \
					*self.direction[1::-1])), 180)
			else:
				self.speed = vel
				if course is None:
					course = head
				if course is not None:
					self.course = course
					course = np.radians(course)
					self.direction = (np.cos(course), np.sin(course), 0)
					self.velocity = vel * self.direction
		elif course is not None or head is not None:
			if course is None:
				course = head
			self.course = course
			course_rad = np.radians(course)
			self.direction = (np.sin(course_rad), np.cos(course_rad), 0)

		# Set heading information
		if not hasattr(self, 'heading'):
			if head is not None:
				self.heading = head
			elif hasattr(self, 'course'):
				self.heading = head = self.course

		# Set attitude information
		yaw = None if course is None or head is None else course-head
		if pitch is not None:
			self.pitch = pitch
		if roll is not None:
			self.roll = roll
		if yaw is not None and pitch is not None and roll is not None:
			self.attitude = Rotation.from_euler("ZYX", [yaw, pitch, roll], \
				degrees=True)
		
		# Set time
		if time is not None:
			self.time = time

	# Method to initialize an instrument on the Platform object
	def load_instrument(self, /, instrument_id, reload=False, **kwargs):
		"""Initializes an Instrument instance on the Platform object.
	
		Parameters:
			instrument_id: type=str|list|bool
				- The standardized name (ID) or list of IDs of the instrument 
				payload.  If True, will initialize all instruments on the 
				platform.
			reload: type=bool, default=False
				- If `False`, will recreate/reload the instrument only if not 
				yet created/loaded; if `True`, will always recreate/reload the 
				instrument even if it already exists.
		
		Returns:
			- An instance or list of instances of the instrument class that were 
			loaded.
		"""
		from .instrument import Instrument, get_instrument_class
		from .ancillary import iterable

		# Initialize instruments attribute if not set
		if not hasattr(self, 'instruments'):
			self.instruments = dict()

		# Check if multiple instruments requested
		isiterable = instrument_id is True or iterable(instrument_id)
		
		# Get list of instrument IDs to initialize
		if instrument_id is True:
			instrument_ids = [*self.instruments]
		elif isiterable:
			instrument_ids = list(instrument_id)
		else:
			instrument_ids = [instrument_id]
		
		# Create instance of instrument in place of instrument metadata
		instruments = []
		for i,instrument_id in enumerate(instrument_ids):
			if instrument_id in instrument_ids[:i]:
				instruments.append(instruments[instrument_ids.index( \
					instrument_id)])
			elif not reload and instrument_id in self.loaded_instruments():
				instruments.append(self.instruments[instrument_id])
			else:
				InstrumentClass = get_instrument_class(instrument_id, \
					platform=self.id)
				if InstrumentClass is Instrument:
					instruments.append(Instrument(instrument_id, \
						platform=self, **kwargs))
				else:
					instruments.append(InstrumentClass(platform=self, **kwargs))
		
		# Return instrument instance(s)
		return instruments if isiterable else instruments[0]
	
	# Method to return a dictionary of all loaded instruments
	def loaded_instruments(self):
		"""Filters the available instruments for those that have been loaded.
	
		Returns:
			- A dictionary of loaded instruments with the instrument names as 
			the keys.
		"""
		from .instrument import Instrument
		
		# Return dictionary of loaded instruments
		return {name:inst for name,inst in self.instruments.items() if \
			isinstance(inst, Instrument)}
################################### Platform ###################################

################################## Satellite ##################################
class Satellite(Platform):
	"""Defines an Earth Science Mission satellite object in orbit.
	
	Functions:
		__init__ -- Initializes an Earth Science Mission satellite object in 
			orbit.
		set_orbit -- Sets the orbital paramters with Keplerian elements or a TLE.
	
	Returns:
		- An object defining an Earth Science Mission satellite, including 
		metadata such as instrument payloads, and optionally including orbital 
		information.
	"""
	
	# Constructor method
	def __init__(self, /, id, meta=None, load_instrument=None, **kwargs):
		"""Initializes an Earth Science Mission satellite object in orbit.
	
		Parameters:
			id: type=str
				- The standardized name (ID) of the satellite.  If not found, 
				will still create a Satellite object with no meta information or 
				instruments.  To fill in this data, use the 'meta' parameter.
			meta: type=dict, default=None
				- Information that will be added to the default information for 
				the given satellite (duplicate keys in the default information 
				are overwritten).
			load_instrument: type=bool, default=None
				- The standardized name (ID) or list of IDs of the instrument 
				payload.  If `True`, will initialize all instruments on the 
				satellite.  If `None`, only the instruments' metadata will be 
				recorded as a dictionary object.
		"""
		from .config import AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS
		
		# Get meta data for given satellite and any extra information
		super().__init__(id, meta=meta, \
			available_platforms=AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS)
		
		# Set orbit and orbital position, or else set state, if applicable
		try:
			self.set_orbit(**kwargs)
		except:
			try:
				super().set_state(**kwargs)
			except:
				pass

		# Initialize all instruments on the satellite
		if load_instrument is not None:
			super().load_instrument(load_instrument)
	
	# Method to set the orbital paramters with Keplerian elements or a TLE
	def set_orbit(self, /, a=None, e=None, i=None, lan=None, ap=None, ta=None, \
	  tle=None, **kwargs):
		"""Sets the orbital paramters with Keplerian elements or a TLE.
	
		Parameters:
			a: type=float, default=None
				- The satellite's semi-major axis, determining the size of the 
				orbit.
			e: type=float, default=None
				- The satellite's eccentricity, determining the shape of the 
				orbit.
			i: type=float, default=None
				- The satellite's inclination, determining the tilt of the 
				orbit.
			lan: type=float, default=None
				- The satellite's longitude of the ascending node (Ω), 
				determining the orientation of the orbital plane.
			ap: type=float, default=None
				- The satellite's argument of periapsis (ω), determining the 
				relative orientation of the orbit.
			ta: type=float, default=None
				- The satellite's true anomaly (ν or θ), determining the 
				position in the orbit at a given time.
			tle: type=bool|str, default=None
				- The satellite's two-line element (TLE) set.  Used only if the 
				Keplerian elements are not provided.  Set to True to download 
				the TLE automatically.

		External Modules:
			- numpy -- https://numpy.org/
		"""
		pass
		if ta is not None:
			pass
			super().set_state()
################################## Satellite ##################################

################################### Aircraft ###################################
class Aircraft(Platform):
	"""Defines an Earth Science Mission aircraft support object in flight.
	
	Functions:
		__init__ -- Initializes an Earth Science Mission aircraft support object 
			in flight.
	
	Returns:
		- An object defining an Earth Science Mission aircraft support, 
		including metadata such as instrument payloads, and optionally including 
		state information.
	"""
	
	# Constructor method
	def __init__(self, /, id, **kwargs):
		"""Initializes an Earth Science Mission aircraft support object in 
		flight.
	
		Parameters:
			id: type=str
				- The standardized name (ID) of the aircraft.  If not found, 
				will still create an Aircraft object with no meta information or 
				instruments.  To fill in this data, use the 'meta' parameter.
		"""
		from .config import AVAILABLE_AIRCRAFT_PLATFORMS
		
		# Get meta data for given aircraft and any extra information, and set 
		# state and initialize instruments if applicable
		super().__init__(id, available_platforms=AVAILABLE_AIRCRAFT_PLATFORMS, \
			**kwargs)
################################### Aircraft ###################################


#--------------------------------- FUNCTIONS ---------------------------------#

########################### get_available_platforms ###########################
def get_available_platforms(satellites=False, aircraft=False):
	"""Gets a list of all available platforms.

	Parameters:
		satellites: type=bool, default=False
			- Set to `True` to only include satellites.
		aircraft: type=bool, default=False
			- Set to `True` to only include aircraft.

	Returns:
		- A sorted list of the standardized names (IDs) of all available 
		platforms.
	"""
	from .config import AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS, \
		AVAILABLE_AIRCRAFT_PLATFORMS
	
	# Return sorted list of available satellites and/or aircraft
	if satellites and not aircraft:
		return sorted(AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS.keys())
	elif not satellites and aircraft:
		return sorted(AVAILABLE_AIRCRAFT_PLATFORMS.keys())
	else:
		sat = list(AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS.keys())
		air = list(AVAILABLE_AIRCRAFT_PLATFORMS.keys())
		return sorted(sat+air)
########################### get_available_platforms ###########################

####################### (LOCAL) get_standard_platform_id #######################
def _get_standard_platform_id(platform, available_platform_instruments):
	"""Gets the standardized name (ID) of the specified platform from a 
	dictionary of available platforms and instruments.

	Parameters:
		platform: type=str
			- The ID or name of the platform.
		available_platform_instruments: type=dict
			- A dictionary of available platforms and instruments within which 
			to search for the ID of the platform.
	
	Returns:
		- The standardized name (ID) of the platform, or `None` if not found.
	"""

	# Format platform input
	platform = platform.lower().strip()

	# Find the platform ID or name
	reserve_id = None
	for platform_id,platform_data in available_platform_instruments.items():
		ids = [platform_id.lower()]
		if 'alternative_ids' in platform_data:
			ids.extend([p.lower() for p in platform_data['alternative_ids']])
		if platform in ids:
			return platform_id
		if reserve_id is None and 'name' in platform_data:
			names = [platform_data['name'].lower()]
			if 'alternative_names' in platform_data:
				names.extend([p.lower() for p in platform_data['alternative_names']])
			if platform in names:
				reserve_id = platform_id
		
	# Return the standardized platform ID
	return reserve_id
####################### (LOCAL) get_standard_platform_id #######################

########################### get_standard_platform_id ###########################
def get_standard_platform_id(platform, satellite=False, aircraft=False):
	"""Gets the standardized name (ID) of the specified platform.

	Parameters:
		platform: type=str
			- The ID or name of the platform.
		satellite: type=bool, default=False
			- Set to True to specify that the `platform` is a satellite.
		aircraft: type=bool, default=False
			- Set to True to specify that the `platform` is an aircraft.
	
	Returns:
		- The standardized name (ID) of the platform, or `None` if not found.
	"""
	from collections import ChainMap
	from .config import AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS, \
		AVAILABLE_AIRCRAFT_PLATFORMS
	
	# Get set of available platform instruments
	if satellite and not aircraft:
		available_platforms = AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS
	elif not satellite and aircraft:
		available_platforms = AVAILABLE_AIRCRAFT_PLATFORMS
	else:
		available_platforms = ChainMap(AVAILABLE_SATELLITE_PLATFORMS_INSTRUMENTS, \
			AVAILABLE_AIRCRAFT_PLATFORMS)
	
	# Return standardized platform ID
	return _get_standard_platform_id(platform, available_platforms)
########################### get_standard_platform_id ###########################

################################ load_platform ################################
def load_platform(id, **kwargs):
	"""Create either a Satellite or Aircraft object by searching for its ID, or 
	default to a general Platform object.

	Parameters:
		id: type=str
			- The ID or name of the platform.  Will check for satellites first 
			and then for aircraft before defaulting to a Platform object.

	Returns:
		- Either a Satellite or Aircraft object depending on if the ID is found 
		in available lists, or defaults to a Platform object.
	"""

	# Return a Satellite, Aircraft or Platform object with the given arguments
	if platform_id:=get_standard_platform_id(id, satellite=True):
		return Satellite(platform_id, **kwargs)
	elif platform_id:=get_standard_platform_id(id, aircraft=True):
		return Aircraft(platform_id, **kwargs)
	else:
		return Platform(id, **kwargs)
################################ load_platform ################################

############################ (LOCAL) transform_crs ############################
def _transform_crs(crs_from, crs_to, *args, **kwargs):
	"""Transform coordinates from one CRS to another.

	Parameters:
		crs_from: type=object
			- The CRS identifier for the CRS that the input parameters `args` 
			are in.
		crs_to: type=object
			- The CRS identifier for the CRS that the output will be in.
		*args:
			- The data (one argument for each dimension) to convert from one CRS 
			to another.

	External modules:
		- pyproj -- https://pyproj4.github.io/pyproj/
	
	Returns:
		- The transformed coordinates.
	"""
	import pyproj

	# Get CRS object from CRS arguments
	crs_from = pyproj.crs.CRS.from_user_input(crs_from)
	crs_to = pyproj.crs.CRS.from_user_input(crs_to)
	
	# Get transformer object to convert coordinates from one CRS to another
	transformer = pyproj.Transformer.from_crs(crs_from, crs_to, **kwargs)
	
	# Return transformed coordinates
	return transformer.transform(*args)
############################ (LOCAL) transform_crs ############################

################################### xyz2lla ###################################
def xyz2lla(x, y, z, **kwargs):
	"""Transform ECEF X/Y/Z coordinates to longitude/latitude/altitude 
	coordinates in the WGS84 coordinate system.

	Parameters:
		x: type=float
			- ECEF X-coordinate.
		y: type=float
			- ECEF Y-coordinate.
		z: type=float
			- ECEF Z-coordinate.

	Returns:
		- Longitude, latitude and altitude coordinates.
	"""
	# import pyproj
	
	# Convert ECEF to WGS84 geodetic coordinates
	# transformer = pyproj.Transformer.from_crs("epsg:4978", "epsg:4326", \
	# 	always_xy=True)
	
	# Return lon/lat/alt coordinates
	# return transformer.transform(x, y, z)
	return _transform_crs("epsg:4978", "epsg:4326", x, y, z, **(kwargs | \
		{'always_xy': True}))
################################### xyz2lla ###################################

################################### lla2xyz ###################################
def lla2xyz(lon, lat, alt, **kwargs):
	"""Convert WGS84 longitude/latitude/altitude coordinates to ECEF X/Y/Z 
	coordinates.

	Parameters:
		lon: type=float
			- The geodetic longitude coordinate.
		lat: type=float
			- The geodetic latitude Y-coordinate.
		alt: type=float
			- The geodetic altitude Z-coordinate.

	Returns:
		- ECEF X, Y and Z coordinates.
	"""
	# import pyproj
	
	# Convert WGS84 geodetic to ECEF coordinates
	# transformer = pyproj.Transformer.from_crs("epsg:4326", "epsg:4978", \
	# 	always_xy=True)
	
	# Return X,Y,Z coordinates
	# return transformer.transform(lon, lat, alt)
	return _transform_crs("epsg:4326", "epsg:4978", lon, lat, alt, **(kwargs | \
		{'always_xy': True}))
################################### lla2xyz ###################################

################################### uvw2enu ###################################
def _transform_vect(u, v, w, lat, lon, func):
	"""Convert ECEF U/V/W vector coordinates to East-North-Up vector coordinates 
	at a given latitude and longitude.

	Parameters:
		u: type=float
			- ECEF U-coordinate of vector.
		v: type=float
			- ECEF V-coordinate of vector.
		w: type=float
			- ECEF W-coordinate of vector.
		lat: type=float
			- The latitude in degrees of the point in ENU-space.
		lon: type=float
			- The longitude in degrees of the point in ENU-space.
		func:
			- The transformation function to take a latitude and longitude pair 
			as separate arguments in that order in units of radians and output 
			a transformation matrix, e.g. from ECEF to ENU coordinate systems.

	External modules:
		- numpy -- https://numpy.org/
	
	Returns:
		- East, North and Up coordinates of the given vector.  If the inputs are 
		arrays, the new dimension will be the first dimension of the output array.
	"""
	import numpy as np
	from .ancillary import iterable

	# Convert latitude and longitude values to radians
	lat = np.radians(lat)
	lon = np.radians(lon)
	
	# Broadcast inputs if needed
	llisiterable = iterable(lat) or iterable(lon)
	isiterable = iterable(u) or iterable(v) or iterable(w) or llisiterable
	if llisiterable:
		masks = [a.mask if np.ma.isMA(a) else None for a in [u,v,w,lat,lon]]
		u,v,w,lat,lon = np.broadcast_arrays(np.atleast_1d(u), v, w, lat, lon, \
			subok=True)
		for a,mask in zip([u,v,w,lat,lon], masks):
			if mask is not None:
				a.mask = np.broadcast_to(mask, a.shape)
	else:
		masks = [a.mask if np.ma.isMA(a) else None for a in [u,v,w]]
		u,v,w = np.broadcast_arrays(np.atleast_1d(u), v, w)
		for a,mask in zip([u,v,w], masks):
			if mask is not None:
				a.mask = np.broadcast_to(mask, a.shape)
	
	# Function to get rotation matrix from ECEF to ENU coordinates
	def _ecef2enuR(lat, lon):
		clat,clon = np.cos([lat,lon])
		slat,slon = np.sin([lat,lon])
		return np.array([
			[-slon,			clon,			0],
			[-clon*slat, 	-slon*slat,		clat],
			[clon*clat,		slon*clat,		slat]
		])

	# Convert ECEF vector to East-North-Up coordinate at lat/lon origin
	if llisiterable:
		n = u.size
		enu = np.zeros((3,n))
		for i in range(n):
			enu[:,i] = _ecef2enuR(lat.flat[i], lon.flat[i]) @ \
				[u.flat[i], v.flat[i], w.flat[i]]
	else:
		enu = _ecef2enuR(lat,lon) @ np.vstack((u.ravel(), v.ravel(), w.ravel()))

	# Return transformed vector
	return enu.reshape(3, *u.shape) if isiterable else enu[:,0]
################################### uvw2enu ###################################

################################### uvw2enu ###################################
def uvw2enu(u, v, w, lat, lon):
	"""Convert ECEF U/V/W vector coordinates to East-North-Up vector coordinates 
	at a given latitude and longitude.

	Parameters:
		u: type=float
			- ECEF U-coordinate of vector.
		v: type=float
			- ECEF V-coordinate of vector.
		w: type=float
			- ECEF W-coordinate of vector.
		lat: type=float
			- The latitude in degrees of the point in ENU-space.
		lon: type=float
			- The longitude in degrees of the point in ENU-space.

	External Modules:
		- numpy -- https://numpy.org/
	
	Returns:
		- East, North and Up coordinates of the given vector.  If the inputs are 
		arrays, the new dimension will be the first dimension of the output 
		array.
	"""
	import numpy as np
	from .ancillary import iterable

	# Convert latitude and longitude values to radians
	lat = np.radians(lat)
	lon = np.radians(lon)
	
	# Broadcast inputs if needed
	llisiterable = iterable(lat) or iterable(lon)
	isiterable = iterable(u) or iterable(v) or iterable(w) or llisiterable
	if llisiterable:
		masks = [a.mask if np.ma.isMA(a) else None for a in [u,v,w,lat,lon]]
		u,v,w,lat,lon = np.broadcast_arrays(np.atleast_1d(u), v, w, lat, lon, \
			subok=True)
		for a,mask in zip([u,v,w,lat,lon], masks):
			if mask is not None:
				a.mask = np.broadcast_to(mask, a.shape)
	else:
		masks = [a.mask if np.ma.isMA(a) else None for a in [u,v,w]]
		u,v,w = np.broadcast_arrays(np.atleast_1d(u), v, w)
		for a,mask in zip([u,v,w], masks):
			if mask is not None:
				a.mask = np.broadcast_to(mask, a.shape)
	
	# Function to get rotation matrix from ECEF to ENU coordinates
	def _ecef2enuR(lat, lon):
		clat,clon = np.cos([lat,lon])
		slat,slon = np.sin([lat,lon])
		return np.array([
			[-slon,			clon,			0],
			[-clon*slat, 	-slon*slat,		clat],
			[clon*clat,		slon*clat,		slat]
		])

	# Convert ECEF vector to East-North-Up coordinate at lat/lon origin
	if llisiterable:
		n = u.size
		enu = np.zeros((3,n))
		for i in range(n):
			enu[:,i] = _ecef2enuR(lat.flat[i], lon.flat[i]) @ \
				[u.flat[i], v.flat[i], w.flat[i]]
	else:
		enu = _ecef2enuR(lat,lon) @ np.vstack((u.ravel(), v.ravel(), w.ravel()))

	# Return transformed vector
	return enu.reshape(3, *u.shape) if isiterable else enu[:,0]
################################### uvw2enu ###################################

################################### uvw2ecef ###################################
def uvw2ecef(u, v, w, lat, lon):
	"""Convert East-North-Up U/V/W vector coordinates to ECEF vector coordinates 
	at a given latitude and longitude.

	Parameters:
		u: type=float
			- ENU East-coordinate of vector.
		v: type=float
			- ENU North-coordinate of vector.
		w: type=float
			- ENU Up-coordinate of vector.
		lat: type=float
			- The latitude in degrees of the point in ENU-space.
		lon: type=float
			- The longitude in degrees of the point in ENU-space.

	External Modules:
		- numpy -- https://numpy.org/
	
	Returns:
		- ECEF coordinates of the given vector.  If the inputs are arrays, the 
		new dimension will be the first dimension of the output array.
	"""
	import numpy as np
	from .ancillary import iterable

	# Convert latitude and longitude values to radians
	lat = np.radians(lat)
	lon = np.radians(lon)
	
	# Broadcast inputs if needed
	llisiterable = iterable(lat) or iterable(lon)
	isiterable = iterable(u) or iterable(v) or iterable(w) or llisiterable
	if llisiterable:
		masks = [a.mask if np.ma.isMA(a) else None for a in [u,v,w,lat,lon]]
		u,v,w,lat,lon = np.broadcast_arrays(np.atleast_1d(u), v, w, lat, lon, \
			subok=True)
		for a,mask in zip([u,v,w,lat,lon], masks):
			if mask is not None:
				a.mask = np.broadcast_to(mask, a.shape)
	else:
		masks = [a.mask if np.ma.isMA(a) else None for a in [u,v,w]]
		u,v,w = np.broadcast_arrays(np.atleast_1d(u), v, w)
		for a,mask in zip([u,v,w], masks):
			if mask is not None:
				a.mask = np.broadcast_to(mask, a.shape)
	
	# Function to get rotation matrix from ENU to ECEF coordinates
	def _enu2ecefR(lat, lon):
		clat,clon = np.cos([lat,lon])
		slat,slon = np.sin([lat,lon])
		return np.array([
			[-slon,		-clon*slat,		clon*clat],
			[clon, 		-slon*slat,		slon*clat],
			[0,			clat,			slat]
		])

	# Convert East-North-Up vector to ECEF coordinate at lat/lon origin
	if llisiterable:
		n = u.size
		ecef = np.zeros((3,n))
		for i in range(n):
			ecef[:,i] = _enu2ecefR(lat.flat[i], lon.flat[i]) @ \
				[u.flat[i], v.flat[i], w.flat[i]]
	else:
		ecef = _enu2ecefR(lat,lon) @ np.vstack((u.ravel(), v.ravel(), w.ravel()))

	# Return transformed vector
	return ecef.reshape(3, *u.shape) if isiterable else ecef[:,0]
################################### uvw2ecef ###################################

################################### eul2quat ###################################
# def eul2quat(angles, radians=False, seq="ZYX", vect=None, **kwargs):
# 	"""Convert Euler angles to quaternion representation.

# 	Parameters:
# 		angles: type=float
# 			- Euler angles specified in degrees.  For a single character `seq`, 
# 			`angles` can be:
# 				- a single value
# 				- an array with shape (N,), where each `angle[i]` corresponds to 
# 				a single rotation
# 				- an array with shape (N, 1), where each `angle[i, 0]` 
# 				corresponds to a single rotation
# 			- For 2- and 3-character wide `seq`, `angles` can be:
# 				- an array with shape (W,) where W is the width of `seq`, which 
# 				corresponds to a single rotation with W axes
# 				- an array with shape (N, W) where each `angle[i]` corresponds 
# 				to a sequence of Euler angles describing a single rotation
# 			- Since the default `seq` is "ZYX", the default `angles` input is a 
# 			3-element array ([yaw, pitch, roll]) in degrees.
# 		radians: type=bool, default=False
# 			- Set to `True` if `angles` are in radians.
# 		seq: type=str, default="ZYX"
# 			- Specifies sequence of axes for rotations, where the x-, y- and 
# 			z-axes rotations correspond to the roll, pitch and yaw angles, 
# 			respectively.  Up to 3 characters belonging to the set {'X', 'Y', 
# 			'Z'} for intrinsic rotations, or {'x', 'y', 'z'} for extrinsic 
# 			rotations, are allowed.  Extrinsic and intrinsic rotations cannot be 
# 			mixed in one function call.
# 		xxvect: type=float
# 			- A 3-element vector (e.g. [1,0,0] for the unit vector pointed in 
# 			the pre-rotated direction of flight) or an (N, 3) array representing 
# 			the vector(s) to be rotated using the quaternion.  If not provided, 
# 			the function will return only the quaternion representation.

# 	External modules:
# 		- scipy -- https://scipy.org/
	
# 	Returns:
# 		- The quaternion representation as a 4-element array [qx, qy, qz, qw], 
# 		or the given `vect` rotated by `angles`.
# 	"""
# 	from scipy.spatial.transform import Rotation as R

# 	# Get the rotation object from the Euler angles
# 	rot = R.from_euler(seq, angles, degrees=not radians)

# 	# Return the quaternion representation
# 	return rot.as_quat()
################################### eul2quat ###################################

################################### quat2eul ###################################
# def quat2eul(quat, seq='ZYX', radians=False, xxvect=None, **kwargs):
# 	"""Convert quaternion representation to Euler angles.

# 	Parameters:
# 		quat: type=float
# 			- The quaternion of the rotation.
# 		seq: type=str, default="ZYX"
# 			- Specifies sequence of axes for rotations, where the x-, y- and 
# 			z-axes rotations correspond to the roll, pitch and yaw angles, 
# 			respectively.  Up to 3 characters belonging to the set {'X', 'Y', 
# 			'Z'} for intrinsic rotations, or {'x', 'y', 'z'} for extrinsic 
# 			rotations, are allowed.  Extrinsic and intrinsic rotations cannot be 
# 			mixed in one function call.
# 		radians: type=bool, default=False
# 			- Set to `True` if resulting Euler angles are to be in radians.
	
# 	External modules:
# 		- scipy -- https://scipy.org/
	
# 	Returns:
# 		- The Euler angles as a tuple (yaw, pitch, roll) in degrees.
# 	"""
# 	# import numpy as np
# 	from scipy.spatial.transform import Rotation as R

# 	# Get the rotation object from the quaternion
# 	rot = R.from_quat(quat, **kwargs)

# 	# Return the Euler angles
# 	return rot.as_euler(seq, degrees=not radians)

# 	# # Compute Euler angles from quaternion components
# 	# siny_cosp = 2 * (qw * qz + qx * qy)
# 	# cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
# 	# yaw = np.arctan2(siny_cosp, cosy_cosp)

# 	# sinp = 2 * (qw * qy - qz * qx)
# 	# sinp = np.clip(sinp, -1, 1)  # Clamp value to avoid invalid input to arcsin
# 	# pitch = np.arcsin(sinp)

# 	# sinr_cosp = 2 * (qw * qx + qy * qz)
# 	# cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
# 	# roll = np.arctan2(sinr_cosp, cosr_cosp)

# 	# # Convert angles to degrees
# 	# return (np.degrees(yaw), np.degrees(pitch), np.degrees(roll))
################################### quat2eul ###################################
