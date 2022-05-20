import json
from collections import deque
import time

# need to add pyserini to sys path before new release containing searcher is made
import sys
sys.path.insert(1, '/home/matthewyang/pyserini')

from pyserini.search.lucene import LuceneGeoSearcher
from pyserini.search.lucene._geo_searcher import JSort, JLatLonDocValuesField, JLatLonShape, JQueryRelation, JLongPoint
from pyserini.search.lucene import LuceneSearcher

def get_segment_from_coordinate(lat, lon, searcher):
    query = JLatLonShape.newBoxQuery("geometry", JQueryRelation.INTERSECTS, -90, 90, -180, 180)
    sort = JSort(JLatLonDocValuesField.newDistanceSort("point", lat, lon))
    hits = searcher.search(query, 1, sort)
    segment = json.loads(hits[0].raw)
    return segment

def get_mouth_source_segment(result, searcher):
  mouth_segment, source_segment = None, None
  # if we don't have source
  if 0 not in result['details']['coordinate_state']:
    mouth_index = 0
    # no source, but at least we have mouth
    if 1 in result['details']['coordinate_state']:
      mouth_index = result['details']['coordinate_state'].index(1)
    # we have neither source nor mouth
    if not result['details']['coordinate_state']:
      return None, None

    # query for initial segment
    mouth_segment = get_segment_from_coordinate(result['details']['coordinate'][mouth_index][1], result['details']['coordinate'][mouth_index][0], searcher)

  # if we have source, but not mouth
  elif 1 not in result['details']['coordinate_state']:
    # get source coordinate index
    source_index = result['details']['coordinate_state'].index(0)
    # query for source segment
    source_segment = get_segment_from_coordinate(result['details']['coordinate'][source_index][1], result['details']['coordinate'][source_index][0], searcher)

    # move down the river to eventually end up with the mouth segment
    mouth_query = JLongPoint.newExactQuery('HYRIV_ID', source_segment['MAIN_RIV'])
    hits = searcher.search(mouth_query, 1)
    mouth_segment = json.loads(hits[0].raw)
  
  # if we have source AND mouth
  else:
    # get mouth/source coordinate indices
    mouth_index = result['details']['coordinate_state'].index(1)
    source_index = result['details']['coordinate_state'].index(0)

    # get mouth/source segments
    mouth_segment = get_segment_from_coordinate(result['details']['coordinate'][mouth_index][1], result['details']['coordinate'][mouth_index][0], searcher)
    source_segment = get_segment_from_coordinate(result['details']['coordinate'][source_index][1], result['details']['coordinate'][source_index][0], searcher)

  return mouth_segment, source_segment

def bfs_river(river, mouth_id):
  # keep track of river geometries and basin ids
  wkts = []
  metadata = []
  basin_ids = set()
  visited = set()

  # bfs from mouth segment
  q = deque([mouth_id])
  while q:
    cur_id = q.popleft()
    if cur_id in visited: continue
    if cur_id not in river.data_dict: continue

    wkts.append(river.get_geo_by_id(cur_id))
    metadata.append(river.get_metadata_by_id(cur_id))
    basin_ids.add(river.data_dict[cur_id]['HYBAS_L12'])
    visited.add(cur_id)

    if cur_id not in river.next_river_id_dict: continue
    for neighbour in river.next_river_id_dict[cur_id]:
      q.append(neighbour)

  return wkts, metadata, basin_ids

def bfs_basin(basin, starting_basin_ids):
  basin_ids = set()

  q = deque(starting_basin_ids)
  while q:
    cur_id = q.popleft()
    if cur_id in basin_ids: continue

    basin_ids.add(cur_id)

    if cur_id not in basin.next_basin_id_dict: continue
    for neighbour in basin.next_basin_id_dict[cur_id]:
      q.append(neighbour)

  return basin_ids

def get_geometries(result, wkts, metadata, basin_ids, basin):
  # convert river wkt to list
  result['geometry'] = [[[[p[1], p[0]] for p in list(line.coords)], data] for line, data in zip(wkts, metadata)]
  # convert basins ids to basin geometries
  basin_polygons = []
  for id in basin_ids:
    polygon = basin.get_geo_by_id(id)
    if polygon:
      basin_polygons.append(polygon)

  result['basin_geometry'] = []
  for multipolygon in basin_polygons:
    for polygon in multipolygon.geoms:
      result['basin_geometry'].append([[[p[1], p[0]] for p in list(polygon.exterior.coords)], []])


def search_river(text, basin, river, debug=True):
  t0 = time.time()
  # get rivers and their mouths from text
  if debug: print("Searching for rivers in wiki...", time.time() - t0)
  searcher = LuceneSearcher('indexes/wikidata')
  hits = searcher.search(text, fields={'contents': 1.0}, k=15)
  searcher.close()
  
  # convert raw string results to json
  if debug: print("Converting string results to json...", time.time() - t0)
  results = []
  for i in range(len(hits)):
    raw = json.loads(hits[i].raw)
    results.append(raw)
  
  # get geometries of each river
  if debug: print("Loading searcher...", time.time() - t0)
  searcher = LuceneGeoSearcher('indexes/hydrorivers')
  
  for i, result in enumerate(results):
    # set key
    result['key'] = i
    if debug: print("KEY", result['key'])

    if debug: print(f"Getting mouth/source segment of {result['contents']}...", time.time() - t0)
    mouth_segment, source_segment = get_mouth_source_segment(result, searcher)
    if debug: print(f"Mouth segment: {mouth_segment}, source segment: {source_segment}")
    
    # neither segments found
    if not mouth_segment and not source_segment:
      continue
    
    # found mouth but not source
    if not source_segment:
      if debug: print("Search with no source...", time.time() - t0)
      wkts, metadata, basin_ids = bfs_river(river, mouth_segment['HYRIV_ID'])
    
    # otherwise, we must have both (source but not mouth impossible since if we have source, we can trace mouth)
    else:
      if debug: print("Search with both mouth and source...", time.time() - t0)
      river_basin_ids = set(basin.find_basins_btw_source_mouth(source_segment['HYBAS_L12'], mouth_segment['HYBAS_L12']))
      river_ids = river.get_rivers_id_in_basins(river_basin_ids)
      
      basin_ids = bfs_basin(basin, river_basin_ids)
      tributary_ids = river.get_rivers_id_in_basins(basin_ids)

      # add main river geometries
      wkts = []
      metadata = []
      visited = set()
      
      for id in river_ids:
        if not id or id in visited: continue
        
        wkts.append(river.get_geo_by_id(id))
        metadata.append([1, 1, 1])

        visited.add(id)

      # add tributary river geometries, and to separate them from the main rivers, make their color lighter
      for id in tributary_ids:
        if not id or id in visited: continue
        
        wkts.append(river.get_geo_by_id(id))
        
        tributary_metadata = river.get_metadata_by_id(id)
        # makes color lighter
        for i in range(len(tributary_metadata)):
          tributary_metadata[i] += 2
        metadata.append(tributary_metadata)
        
        visited.add(id)

    if debug: print("Getting geometries...", time.time() - t0)
    get_geometries(result, wkts, metadata, basin_ids, basin)

    # set zoom bounds, first point bottom left and second point top right
    if debug: print("Setting bounds and finishing up...", time.time() - t0)
    min_lat, max_lat = 90, -90
    min_lon, max_lon = 180, -180
    for geo in result['geometry']:
      line = geo[0]
      for point in line:
        min_lat, max_lat = min(min_lat, point[0]), max(max_lat, point[0])
        min_lon, max_lon = min(min_lon, point[1]), max(max_lon, point[1])

    result['bounds'] = [
      [min_lat, min_lon],
      [max_lat, max_lon]
    ]

  return results
