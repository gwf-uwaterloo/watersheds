import geopandas as gpd
from collections import defaultdict


class Basin():
    @staticmethod
    def construct_basin_dict():
        full_basin_dict = {}
        full_parent_basin_dict = defaultdict(list)
        full_next_basin_id_dict = defaultdict(list)
        
        basin_lv12_path = '.cache/na_basin_lv12.geojson'
        full_basin_data = gpd.read_file(basin_lv12_path)
        # print(full_basin_data.head())
        for index, row in full_basin_data.iterrows():
            full_basin_dict[row['HYBAS_ID']] = row
            full_parent_basin_dict[row['MAIN_BAS']].append(row['HYBAS_ID'])
            full_next_basin_id_dict[row['NEXT_DOWN']].append(row['HYBAS_ID'])
        return full_basin_dict, full_parent_basin_dict, full_next_basin_id_dict

    @staticmethod
    def find_basins_btw_source_mouth_in_basin_lv12(source_basin_id, mouth_basin_id, full_basin_dict, found_basins_id):
        if source_basin_id == mouth_basin_id or source_basin_id == 0:
            # print('done', found_basins_id)
            return found_basins_id + [mouth_basin_id]
        
        next_basin_id = full_basin_dict[source_basin_id]['NEXT_DOWN']
        return Basin.find_basins_btw_source_mouth_in_basin_lv12(next_basin_id, mouth_basin_id, full_basin_dict,
                                                          found_basins_id + [source_basin_id])

    def __init__(self):
        self.data_dict, self.main_basins_dict, self.next_basin_id_dict = self.construct_basin_dict()

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
        found_basins_id = []
        full_parent_basin_dict = self.main_basins_dict
        # todo can a basin have multiple parents?
        for k, v in full_parent_basin_dict.items():
            if query_basin_id in v:
                found_basins_id.append(k)
        return found_basins_id

    def get_geo_by_id(self, query_basin_id):
        full_basin_data = self.data_dict
        if query_basin_id in full_basin_data:
            return full_basin_data[query_basin_id]['geometry']
        else:
            return None

    def find_basins_btw_source_mouth(self, source_basin_id, mouth_basin_id):
        return self.find_basins_btw_source_mouth_in_basin_lv12(source_basin_id, mouth_basin_id, self.data_dict, [])


class River():
    @staticmethod
    def construct_river_dict():
        full_river_dict = {}
        full_next_river_id_dict = defaultdict(list)
        river_path = '.cache/na_river_full.geojson'
        full_river_data = gpd.read_file(river_path)
        # print(full_river_data.head())
        for index, row in full_river_data.iterrows():
            full_river_dict[row['HYRIV_ID']] = row
            full_next_river_id_dict[row['NEXT_DOWN']].append(row['HYRIV_ID'])
        return full_river_dict, full_next_river_id_dict

    def __init__(self):
        self.data_dict, self.next_river_id_dict = self.construct_river_dict()

    def get_geo_by_id(self, query_river_id):
        full_river_data = self.data_dict
        if query_river_id in full_river_data:
            return full_river_data[query_river_id]['geometry']
        else:
            return None
    
    def get_metadata_by_id(self, query_river_id):
        full_river_data = self.data_dict
        if query_river_id in full_river_data:
            river_segment = full_river_data[query_river_id]
            [river_segment['ORD_STRA'], river_segment['ORD_CLAS'], river_segment['ORD_FLOW']]
        else:
            return None

    def get_rivers_id_in_basins(self, query_basin_id_list):
        full_river_data = self.data_dict
        found_river_id = []
        for key, value in full_river_data.items():
            if value['HYBAS_L12'] in query_basin_id_list:
                found_river_id.append(value['HYRIV_ID'])
        return found_river_id
