# Running Watersheds App
## Setting Up the Repo
1. Clone the repo and create a virtual env
```
git clone https://github.com/gwf-uwaterloo/watersheds.git && conda create -n YOUR_ENV 
```
2. Activate the conda env
3. Run `yarn` at `watersheds/watersheds/search/app/client/`
4. Run `pip install requirements.txt` at `watersheds/`
5. In `watersheds/watersheds/search/search.py`, change `sys.path.insert(1, '/home/matthewyang/pyserini')` to `sys.path.insert(1, PATH_TO_PYSERINI_ON_YOUR_LOCAL_MACHINE)`
6. Add a `.env` file in `watersheds/watersheds/search/app/client/` and add `BACKEND_ENDPOINT="http://127.0.0.1:5000/` to the file

## Building the Rivers Indices
1. Download HydroRIVERS data and extract it: `wget https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_shp.zip && unzip HydroRIVERS_v10_shp.zip`
2. Convert to json: `python anserini/tools/scripts/geosearch/file_to_json.py --input SHAPE_FILE_FROM_PREVIOUS_STEP --output WHERE_YOU_WANT_YOUR_JSON_OUTPUT`
3. Put the output (JSON file) from the previous step into `anserini/collections/hydrorivers` (if the folder doesn't exist, create it)
4. Index using Anserini:
```
sh target/appassembler/bin/IndexCollection -threads 1 -collection JsonCollection \
 -generator GeoGenerator -input collections/hydrorivers \
 -index indexes/hydrorivers -storeRaw 
```
5. Put `watersheds/watersheds/search/app/server/indexes/hydrorivers` into `watersheds/watersheds/search/app/server/indexes`

## Adding the Rivers and Basins Geojson
1. Download both HydroRIVERS data and HydroBASINS data
2. Convert them to GeoJSON using QGIS
3. Add geojson files to `watersheds/watersheds/search/app/server/.cache` as `basin.geojson` and `river.geojson`

## Running the App
1. Start the backend with `flask run` at `watersheds/watersheds/search/app/server/`
2. Start the frontend with `yarn start` at `watersheds/watersheds/search/app/client/`
3. Your app should now be running at `http://127.0.0.1:3000`
