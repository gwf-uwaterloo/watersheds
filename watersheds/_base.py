import geopandas as gpd


def construct_basin_lv12():
    full_basin_dict = {}
    full_parent_basin_dict = {}

    basin_lv12_path = 'watersheds/data/na_basin_lv12.geojson'
    full_basin_data = gpd.read_file(basin_lv12_path)
    print(full_basin_data.head())
    for index, row in full_basin_data.iterrows():
        full_basin_dict[row['HYBAS_ID']] = row
        if row['MAIN_BAS'] not in full_parent_basin_dict:
            full_parent_basin_dict[row['MAIN_BAS']] = [row['HYBAS_ID']]
        else:
            full_parent_basin_dict[row['MAIN_BAS']].append(row['HYBAS_ID'])
    return full_basin_dict, full_parent_basin_dict


def find_basins_btw_source_mouth_in_basin_lv12(source_basin_id, mouth_basin_id, full_basin_dict, found_basins_id):
    next_basin_id = full_basin_dict[source_basin_id]['NEXT_DOWN']
    next_basin = full_basin_dict[next_basin_id]
    # print(source_basin_id, 'next is', next_basin['HYBAS_ID'])
    found_basins_id = found_basins_id + [next_basin['HYBAS_ID']]
    if next_basin['HYBAS_ID'] == mouth_basin_id:
        print('done', found_basins_id)
        if found_basins_id is not None:
            return found_basins_id
    return find_basins_btw_source_mouth_in_basin_lv12(next_basin['HYBAS_ID'], mouth_basin_id, full_basin_dict,
                                                      found_basins_id)


class Basin():
    def __init__(self):
        self.data_dict, self.main_basins_dict = construct_basin_lv12()

    def find_point_belongs_to(self, point):
        full_basin_data = self.data_dict
        found_basins_id = []
        for key, value in full_basin_data.items():
            poly_geo = value['geometry']
            if poly_geo.contains(point):
                found_basins_id.append(value['HYBAS_ID'])
        return found_basins_id

    def find_children_basins(self, query_basin_id):
        full_basin_data = self.data_dict
        found_basins_id = []
        for key, value in full_basin_data.items():
            if value['MAIN_BAS'] == query_basin_id:
                found_basins_id.append(value['HYBAS_ID'])
        return found_basins_id

    def find_parent_basins(self, query_basin_id):
        found_basins_id = []
        full_parent_basin_dict = self.main_basins_dict
        # todo can a basin have multiple parents?
        for k, v in full_parent_basin_dict.items():
            if query_basin_id in v:
                found_basins_id.append(k)
        return found_basins_id

    def get_basin_geo_by_id(self, query_basin_id):
        full_basin_data = self.data_dict
        if query_basin_id in full_basin_data:
            return full_basin_data[query_basin_id]['geometry']
        else:
            return None

    def find_basins_btw_source_mouth(self, source_basin_id, mouth_basin_id):
        return find_basins_btw_source_mouth_in_basin_lv12(source_basin_id, mouth_basin_id, self.data_dict, [])
