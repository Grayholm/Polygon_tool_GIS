# import geopandas as gpd
# from shapely import Point

# data = gpd.read_file("water_polygons.geojson")


# lakes_wgs84 = data[data['water'] == 'lake']

# lakes = lakes_wgs84.to_crs(epsg=3857)

# lakes = lakes[lakes.geometry.area > 5000000]

# lakes_filtered = lakes.to_crs(4326)

# lakes_polygons = [i for i in lakes_filtered.geometry]

# x = Point(lakes_polygons[0].centroid)

# for i in lakes_polygons:
#     if i.contains(x):
#         print("yes")
#     else:
#         print("no")
