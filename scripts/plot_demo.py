from shapely.geometry import Point
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
from watersheds._base import Basin, River


# demo plot for St lawrence river
na_basin = Basin()
na_river = River()
stl_river_mouth_point = Point(-71.225, 46.77)
stl_river_source_point = Point(-76.4, 44.1)
result_mouth = na_basin.find_point_belongs_to(stl_river_mouth_point)
print(result_mouth)
result_source = na_basin.find_point_belongs_to(stl_river_source_point)
print(result_source)

all_btw_basins = na_basin.find_basins_btw_source_mouth(result_source[0], result_mouth[0])
print(all_btw_basins)
all_btw_basins_gpd = [gpd.GeoSeries(na_basin.get_basin_geo_by_id(b)) for b in all_btw_basins]

all_children_basins_stlr = na_basin.find_children_basins(result_mouth[0])
print(len(all_children_basins_stlr), 'children')
all_children_basins_gpd = [gpd.GeoSeries(na_basin.get_basin_geo_by_id(b)) for b in all_children_basins_stlr]

stl_river_source_point = gpd.GeoSeries(stl_river_source_point)
stl_river_mouth_point = gpd.GeoSeries(stl_river_mouth_point)

geo_stlr_basin = na_basin.get_basin_geo_by_id(result_source[0])[0]
geo_stlr_basin = gpd.GeoSeries(geo_stlr_basin)

geo_stlr_basin2 = na_basin.get_basin_geo_by_id(result_mouth[0])[0]
geo_stlr_basin2 = gpd.GeoSeries(geo_stlr_basin2)

all_btw_rivers = na_river.find_all_rivers_in_basins(all_btw_basins)
print('len ', len(all_btw_rivers))
geo_stlr_rivers = [gpd.GeoSeries(na_river.get_river_geo_by_id(item)) for item in all_btw_rivers]

fig, ax = plt.subplots()
ax = plt.gca()

stl_river_source_point.plot(ax=ax, color='blue', markersize=10)
stl_river_mouth_point.plot(ax=ax, color='blue', markersize=10)

geo_stlr_basin.plot(ax=ax, facecolor='red', alpha=0.5)
geo_stlr_basin2.plot(ax=ax, facecolor='red', alpha=0.5)
for a_b in all_btw_basins_gpd:
    a_b.plot(ax=ax, facecolor='black', alpha=0.3)
for a_b in all_children_basins_gpd:
    a_b.plot(ax=ax, facecolor='grey', alpha=0.5)
for r in geo_stlr_rivers:
    r.plot(ax=ax, color='yellow', markersize=8)

cx.add_basemap(ax, crs='EPSG:4326', source=cx.providers.CartoDB.Voyager)
plt.show()