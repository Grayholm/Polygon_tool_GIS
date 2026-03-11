# from global_land_mask import globe
# import geopandas as gpd

# data = gpd.read_file("export(8).geojson")

# populated = data[data['place'].isin(['village', 'city', 'town'])]
# seeds = [(p.centroid.x, p.centroid.y)
#             for p in populated.geometry]

# for s in seeds:
#     print(s, globe.is_land(s[1], s[0]))

# print(seeds)