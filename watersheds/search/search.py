import json
from collections import deque
import geopandas as gpd
import time


# need to add pyserini to sys path before new release containing searcher is made
# import sys
# sys.path.insert(1, '/home/matthewyang/pyserini')

from pyserini.search.lucene import LuceneGeoSearcher
from pyserini.search.lucene._geo_searcher import JSort, JLatLonDocValuesField, JLatLonShape, JQueryRelation, JLongPoint
from pyserini.search.lucene import LuceneSearcher


def get_mouth_segment(result, searcher):
  # if we have the mouth, or we have neither the mouth nor the source
  if (1 in result['details']['coordinate_state']) or (1 not in result['details']['coordinate_state'] and 0 not in result['details']['coordinate_state']):
    mouth_index = 0
    if 1 in result['details']['coordinate_state']:
      mouth_index = result['details']['coordinate_state'].index(1)

    # query for initial segment
    query = JLatLonShape.newBoxQuery("geometry", JQueryRelation.INTERSECTS, -90, 90, -180, 180)
    sort = JSort(JLatLonDocValuesField.newDistanceSort("point", result['details']['coordinate'][mouth_index][1], result['details']['coordinate'][mouth_index][0]))
    hits = searcher.search(query, 1, sort)
    mouth_segment = json.loads(hits[0].raw)

  # if we only have the source, trace down to the bottom to get mouth segment
  elif 0 in result['details']['coordinate_state']:
    # get source coordinate index
    source_index = result['details']['coordinate_state'].index(0)

    # query for source segment
    query = JLatLonShape.newBoxQuery("geometry", JQueryRelation.INTERSECTS, -90, 90, -180, 180)
    sort = JSort(JLatLonDocValuesField.newDistanceSort("point", result['details']['coordinate'][source_index][1], result['details']['coordinate'][source_index][0]))
    hits = searcher.search(query, 1, sort)
    mouth_segment = json.loads(hits[0].raw)

    # move down the river to eventually end up with the mouth segment
    while mouth_segment['NEXT_DOWN'] != 0:
      nextQuery = JLongPoint.newExactQuery('HYRIV_ID', mouth_segment['NEXT_DOWN'])
      hits = searcher.search(nextQuery, 1)
      mouth_segment = json.loads(hits[0].raw)
  
  return mouth_segment

def bfs(result, searcher, mouth_segment, basin, t0):
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
    hits = searcher.search(query, 4)
    for hit in hits:
      q.append(json.loads(hit.raw))

  print("")
  print("BFS: Done ActualBFS, Time:", time.time() - t0)
  # convert river wkt to list
  segments = gpd.GeoSeries.from_wkt(wkts)
  result['geometry'] = [[[[p[1], p[0]] for p in list(line.coords)], data] for line, data in zip(segments, metadata)]

  print("")
  print("BFS: Done convert river wkt to list, Time:", time.time() - t0)
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
  print("BFS: Done convert basins ids to basin geometries, Time:", time.time() - t0)

def get_geometries(text, basin):
  t0 = time.time()
  # get rivers and their mouths from text
  print("Time:", time.time() - t0)
  print("Searching for rivers in wiki...")
  searcher = LuceneSearcher('indexes/wikidata')
  hits = searcher.search(text, fields={'contents': 1.0}, k=25)
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
    print(f"Getting mouth segment of {result['contents']}...")
    print(result)
    mouth_segment = get_mouth_segment(result, searcher)
    print(mouth_segment)

    print("Time:", time.time() - t0)
    print(f"BFS on {result['contents']}...")
    bfs(result, searcher, mouth_segment, basin, t0)

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