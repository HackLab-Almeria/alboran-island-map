# -*- coding: utf-8 -*-
# generate an editable features map for full DEM + features map generation

import sys

from osgeo import gdal
gdal.UseExceptions()

def Usage():
    print("""
    $ create-feature-map.py DEM.tif map.png
    """)
    sys.exit(1)


# main #

print(sys.argv)

if len(sys.argv) < 3:
    print """
        [ ERROR ] you must supply two arguments: DEM.tif map.png
       """
    Usage()

DEM_file = sys.argv[1]
MAP_file = sys.argv[2]


ds = gdal.Open(DEM_file)
geotransform = ds.GetGeoTransform()
WIDTH = ds.RasterXSize * abs(geotransform[1])
HEIGHT = ds.RasterYSize * abs(geotransform[5])
ds = gdal.Translate(MAP_file, ds, format="PNG", outputType = gdal.GDT_Byte, width=WIDTH, height=HEIGHT)
ds = None
