import geopandas as gpd
from shapely import MultiPolygon, Polygon
from shapely.geometry import box, Point
from shapely.ops import polygonize, unary_union
import matplotlib.pyplot as plt

data = gpd.read_file("export(4).geojson")

lines = data[data.geometry.type.isin(["LineString", "MultiLineString"])]
polygons = data[data.geometry.type.isin(["Polygon", "MultiPolygon"])]

merged = unary_union(lines.geometry)                    # открытый coastline
minx, miny, maxx, maxy = data.total_bounds
bbox = box(minx, miny, maxx, maxy)
bbox_boundary = bbox.boundary

merged_with_bbox = unary_union([merged, bbox_boundary])

coast_polygons = list(polygonize(merged_with_bbox))



sea_test_point = Point(minx + (maxx - minx) * 0.01, miny + (maxy - miny) * 0.01)

coast_land = []
for p in coast_polygons:
    if not p.contains(sea_test_point) and p.area > 1e-6:   # отбрасываем крошечные артефакты
        coast_land.append(p)


existing_land = unary_union(list(polygons.geometry))
land = unary_union(coast_land + [existing_land] if not existing_land.is_empty else coast_land)



def plot_poly(poly):
    if isinstance(poly, Polygon):
        x, y = poly.exterior.xy
        plt.plot(x, y, 'b')
    elif isinstance(poly, MultiPolygon):
        for p in poly.geoms:
            x, y = p.exterior.xy
            plt.plot(x, y, 'b')

plot_poly(land)
plt.axis("equal")
plt.show()