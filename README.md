# watersheds
watersheds provide Api for users to easily search in HydroBASINS and HydroRIVERS. For HydroBASINS and HydroRIVERS, we convert them from .shp to .geojson

## Project Environment
- python 3.7.11
- install environment
	```
	pip install requirements.txt
	```

## Project Structure
	- requirements.txt
	- /scripts
		- plot_demo.py
			demo to use watersheds api search and plot
	- / watersheds
		- /data
			all HydroBASINS and HydroRIVERS geojson files here
		- _base.py
