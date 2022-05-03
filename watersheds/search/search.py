import json
from collections import deque
import geopandas as gpd
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
    if 1 in result['details']['coordinate_state']:
      mouth_index = result['details']['coordinate_state'].index(1)
    if not result['details']['coordinate_state']:
      return None

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

def bfs(searcher, mouth_segment, t0):
  # keep track of river geometries and basin ids
  wkts = []
  metadata = []
  basin_ids = set()

  # bfs from mouth segment
  q = deque([mouth_segment])
  while q:
    cur_segment = q.popleft()

    wkts.append(cur_segment['geometry'])
    metadata.append([cur_segment['ORD_STRA'], cur_segment['ORD_CLAS'], cur_segment['ORD_FLOW']])
    basin_ids.add(cur_segment['HYBAS_L12'])

    query = JLongPoint.newExactQuery('NEXT_DOWN', cur_segment['HYRIV_ID'])
    hits = searcher.search(query, 150)
    for hit in hits:
      q.append(json.loads(hit.raw))

  print("")
  print("Done BFS, Time:", time.time() - t0)

  return wkts, metadata, basin_ids

# def bfs_basin(mouth_basin_id, searcher):
#   basin_ids = set()

#   q = deque([mouth_basin_id])
#   while q:
#     cur_id = q.popleft()
#     basin_ids.add(cur_id)

#     query = JLongPoint.newExactQuery('NEXT_DOWN', cur_id)
#     hits = searcher.search(query, 120)
#     for hit in hits:
#       print(hit)
#       print("")
#       print(hit.lucene_document)
#       q.append(hit.lucene_document['HYRIV_ID'])

#   return basin_ids

def get_geometries(result, wkts, metadata, basin_ids, basin, t0):
  # convert river wkt to list
  segments = gpd.GeoSeries.from_wkt(wkts)
  result['geometry'] = [[[[p[1], p[0]] for p in list(line.coords)], data] for line, data in zip(segments, metadata)]

  print("")
  print("Done converting river wkt to list, Time:", time.time() - t0)
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
  
  print("")
  print("Done converting basins ids to basin geometries, Time:", time.time() - t0)

def search_river(text, basin, river):
  t0 = time.time()
  # get rivers and their mouths from text
  print("Time:", time.time() - t0)
  print("Searching for rivers in wiki...")
  searcher = LuceneSearcher('indexes/wikidata')
  hits = searcher.search(text, fields={'contents': 1.0}, k=20)
  searcher.close()
  
  # convert raw string results to json
  print("Time:", time.time() - t0)
  print("Converting string results to json...")
  results = []
  for i in range(len(hits)):
    raw = json.loads(hits[i].raw)
    results.append(raw)
  
  # get geometries of each river
  print("Time:", time.time() - t0)
  print("Getting geometries of rivers...")
  searcher = LuceneGeoSearcher('indexes/hydrorivers')
  
  for i, result in enumerate(results):
    print("Time:", time.time() - t0)
    print(f"Getting mouth/source segment of {result['contents']}...")
    print(result)
    mouth_segment, source_segment = get_mouth_source_segment(result, searcher)
    
    print("Time:", time.time() - t0)
    # neither segments found
    if not mouth_segment and not source_segment:
      continue
    
    # found mouth but not source
    if not source_segment:
      print(f"BFS on {result['contents']}...")
      wkts, metadata, basin_ids = bfs(searcher, mouth_segment, t0)
    
    # otherwise, we must have both (source but not mouth impossible since if we have source, we can trace mouth)
    else:
      river_basin_ids = set(basin.find_basins_btw_source_mouth(source_segment['HYBAS_L12'], mouth_segment['HYBAS_L12']))
      river_ids = river.get_rivers_id_in_basins(river_basin_ids)

      wkts = []
      metadata = []
      for id in river_ids:
        if not id: continue
        query = JLongPoint.newExactQuery('HYRIV_ID', id)
        hits = searcher.search(query, 1)
        river_segment = json.loads(hits[0].raw)

        wkts.append(river_segment['geometry'])
        metadata.append([river_segment['ORD_STRA'], river_segment['ORD_CLAS'], river_segment['ORD_FLOW']])
    
      print("mouth segment:", mouth_segment)
      _, _, basin_ids = bfs(searcher, mouth_segment, t0)
      print("basin_ids: ", basin_ids)

    get_geometries(result, wkts, metadata, basin_ids, basin, t0)

    # set zoom bounds, first point bottom left and second point top right
    print("Time:", time.time() - t0)
    print(result['geometry'][0])
    result['bounds'] = [
      [min([min(line[0], key=lambda p: p[0]) for line in result['geometry']], key=lambda p: p[0])[0], min([min(line[0], key=lambda p: p[1]) for line in result['geometry']], key=lambda p: p[1])[1]],
      [max([max(line[0], key=lambda p: p[0]) for line in result['geometry']], key=lambda p: p[0])[0], max([max(line[0], key=lambda p: p[1]) for line in result['geometry']], key=lambda p: p[1])[1]]
    ]

    # set key
    result['key'] = i

  return results
