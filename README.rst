Earth Science Missions Python Package
=====================================

With the advent of more and more unique spaceborne and airborne instruments and missions used for earth science research, and with the number of Python users of such data increasing as well, it is important to deal with any chokepoints in the research chain.  The Earth Science Mission (ESM) Python package fills a gap between the data acquisition and archiving step and the data analysis step by increasing data accessibility, individual and team productivity, and reproducibility and accuracy of results.

At its core, ESM automatically builds model associations between platform, instrument, product, dataset, and granule or grid objects.  The objective is to achieve as much of this as possible behind the scenes for the user, accomplished using class interactions and stored metadata inputs, along with any necessary custom functions.  It is also built to be modular, providing an easy way to add in more instruments.

Peer collaboration is encouraged to help mature the product to fill in metadata and custom functions for a large array of spaceborne and airborne instruments.

**Example code**

*Ways to get a MODIS instrument object*

.. code-block:: python
	
	# Example 1
	from esm.instrument import load_instrument
	modis = load_instrument('modis', platform='terra')

	# Example 2
	from esm.platform import Satellite
	terra = Satellite('terra', load_instrument='modis')
	modis = terra.instruments['modis']
	
	# Example 3
	from esm.instrument import get_instrument_class
	MODIS = get_instrument_class('modis')
	modis = MODIS('terra')
	
*Read MODIS radiance data*

.. code-block:: python
	
	import datetime as dt
	from esm.instrument import load_instrument
	
	# Settings
	platform = "terra"
	collection = 6.1
	timestamp = dt.datetime(2025, 1, 1, 12, 0)
	band = 13
	measurement = "radiance"
	
	# Create instrument object
	modis = load_instrument('modis', platform)
	
	# Get data
	data = modis.get_radiance(measurement, band, \
		timestamp=timestamp, version=collection)

*Get height data for a file*

.. code-block:: python
	
	from esm.data import Dataset, Granule
	file = "MOD03.A2025006.0455.061.2025006123710.hdf"
	ds = Dataset(file)
	scene = Granule("Height", dataset=ds, dims=True, lats=True, lons=True)