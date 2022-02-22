import geopandas as gpd
from shapely.strtree import STRtree
from shapely.ops import nearest_points



class Basin():
    @staticmethod
    def construct_basin_dict():
        full_basin_dict = {}
        full_parent_basin_dict = {}
        basin_lv12_path = '.cache/na_basin_lv12.geojson'
        full_basin_data = gpd.read_file(basin_lv12_path)
        # print(full_basin_data.head())
        for index, row in full_basin_data.iterrows():
            full_basin_dict[row['HYBAS_ID']] = row
            if row['MAIN_BAS'] not in full_parent_basin_dict:
                full_parent_basin_dict[row['MAIN_BAS']] = [row['HYBAS_ID']]
            else:
                full_parent_basin_dict[row['MAIN_BAS']].append(row['HYBAS_ID'])
        return full_basin_dict, full_parent_basin_dict

    @staticmethod
    def find_basins_btw_source_mouth_in_basin_lv12(source_basin_id, mouth_basin_id, full_basin_dict, found_basins_id):
        next_basin_id = full_basin_dict[source_basin_id]['NEXT_DOWN']
        next_basin = full_basin_dict[next_basin_id]
        # print(source_basin_id, 'next is', next_basin['HYBAS_ID'])
        found_basins_id = found_basins_id + [next_basin['HYBAS_ID']]
        if next_basin['HYBAS_ID'] == mouth_basin_id:
            # print('done', found_basins_id)
            if found_basins_id is not None:
                return found_basins_id
        return Basin.find_basins_btw_source_mouth_in_basin_lv12(next_basin['HYBAS_ID'], mouth_basin_id, full_basin_dict,
                                                          found_basins_id)

    def __init__(self):
        self.data_dict, self.main_basins_dict = self.construct_basin_dict()

    def find_point_belongs_to(self, point):
        full_basin_data = self.data_dict
        found_basins_id = []
        for key, value in full_basin_data.items():
            poly_geo = value['geometry']
            if poly_geo.contains(point):
                found_basins_id.append(value['HYBAS_ID'])
        return found_basins_id

    def get_children(self, query_basin_id):
        full_basin_data = self.data_dict
        found_basins_id = []
        for key, value in full_basin_data.items():
            if value['MAIN_BAS'] == query_basin_id:
                found_basins_id.append(value['HYBAS_ID'])
        return found_basins_id

    def get_parent(self, query_basin_id):
        return self.main_basins_dict[query_basin_id]['MAIN_BAS']

    def get_geo_by_id(self, query_basin_id):
        full_basin_data = self.data_dict
        if query_basin_id in full_basin_data:
            return full_basin_data[query_basin_id]['geometry']
        else:
            return None

    def find_basins_btw_source_mouth(self, source_basin_id, mouth_basin_id):
        return self.find_basins_btw_source_mouth_in_basin_lv12(source_basin_id, mouth_basin_id, self.data_dict, [])

    def find_nearest_basin(self, query_point):
        full_basin_data = self.data_dict
        found_basins_id = -1
        min_dist = float("inf")
        for key, value in full_basin_data.items():
            poly_geo = value['geometry']
            temp_dist = query_point.distance(poly_geo)
            if temp_dist < min_dist:
                found_basins_id = value['HYBAS_ID']
                min_dist = temp_dist
            if poly_geo.contains(query_point):
                found_basins_id = value['HYBAS_ID']
                break
        return found_basins_id


class River():
    @staticmethod
    def construct_river_dict():
        full_river_dict = {}
        river_path = '.cache/na_river_full.geojson'
        full_river_data = gpd.read_file(river_path)
        # print(full_river_data.head())
        for index, row in full_river_data.iterrows():
            full_river_dict[row['HYRIV_ID']] = row
        return full_river_dict

    def __init__(self):
        self.data_dict = self.construct_river_dict()

    def get_geo_by_id(self, query_river_id):
        full_river_data = self.data_dict
        if query_river_id in full_river_data:
            return full_river_data[query_river_id]['geometry']
        else:
            return None

    def get_rivers_id_in_basins(self, query_basin_id_list):
        full_river_data = self.data_dict
        found_river_id = []
        for key, value in full_river_data.items():
            if value['HYBAS_L12'] in query_basin_id_list:
                found_river_id.append(value['HYRIV_ID'])
        return found_river_id
