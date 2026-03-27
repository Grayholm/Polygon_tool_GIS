from pathlib import Path

import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent
file_path = BASE_DIR.parent / "ne_10m_land" / "ne_10m_land.shp"


data = gpd.read_file(file_path)

print(data)

land = data.union_all()

print(land)