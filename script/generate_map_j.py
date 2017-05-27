# -*- coding: utf-8 -*-
import os
import sys
from pymclevel import mclevel, box, materials, nbt
from pymclevel.materials import alphaMaterials as m
from osgeo import gdal
from osgeo import gdalconst
from osgeo import gdal_array
gdal.UseExceptions()

import numpy as np

def Usage():
    print('$ generate_map.py DEM_map features_map')
    sys.exit(1)



# Fin definiciones    

work_dir = os.getcwd()[:-6]
print "Working directory: %s" % work_dir
minecraft_save_dir = work_dir+"/../worlds"

if len(sys.argv) < 3:
    print '[ ERROR ] you must supply two arguments: DEM_map features_map'
    Usage()

file_elevation = sys.argv[1]
file_features = sys.argv[2]

print "Loading maps"
DEM_ds = gdal.Open( file_elevation, gdalconst.GA_ReadOnly )
if DEM_ds is None:
    print 'Unable to open %s' % file_elevation
    sys.exit(1)

FEATURES_ds = gdal.Open (file_features, gdalconst.GA_ReadOnly)
if FEATURES_ds is None:
    print "Unable to open %s" % file_features
    sys.exit(1)

DEM_heigth = DEM_ds.RasterYSize
DEM_width = DEM_ds.RasterXSize
print('DEM size = {0} wdith x {1} height'.format(DEM_width, DEM_heigth))

FEATURES_heigth = FEATURES_ds.RasterYSize
FEATURES_width = FEATURES_ds.RasterXSize
print('Features size = {0} wdith x {1} height'.format(FEATURES_width, FEATURES_heigth))

# DEM altitudes are expected to be coded in just 1 band
band_num = 1
try:
    DEMband = DEM_ds.GetRasterBand(band_num)
except RuntimeError, e:
    print 'No band %i found for altitude' % band_num
    print e
    sys.exit(1)

geotransform = DEM_ds.GetGeoTransform()
WIDTH = DEM_ds.RasterXSize * int(abs(geotransform[1]))
HEIGHT = DEM_ds.RasterYSize * int(abs(geotransform[5]))
mDEM_ds = gdal.Translate( '', DEM_ds, format="MEM", outputType = gdal.GDT_Int32, width=WIDTH, height=HEIGHT)
print('DEM size = {0} wdith x {1} height'.format(mDEM_ds.RasterXSize, mDEM_ds.RasterYSize))

#Iteramos
dem_values = mDEM_ds.GetRasterBand(1).ReadAsArray()

max_alt = mDEM_ds.GetRasterBand(1).GetMaximum()

try:
    features_r = FEATURES_ds.GetRasterBand(1).ReadAsArray()
    features_g = FEATURES_ds.GetRasterBand(2).ReadAsArray()
    features_b = FEATURES_ds.GetRasterBand(3).ReadAsArray()
except RuntimeError, e:
    print 'Features image is not RGB encoded'
    sys.exit(1)

#for i in range(0, len(dem_values)):
#    for j in range(0, len(dem_values[i])):
#        print a

if not os.path.exists(worlddir):
    worlddir = os.path.join(minecraft_save_dir, 'cazcalandia')

world = mclevel.MCInfdevOldLevel(worlddir, create=True)
from pymclevel.nbt import TAG_Int, TAG_String, TAG_Byte_Array
tags = [TAG_Int(0, "MapFeatures"),
        TAG_String("flat", "generatorName"),
        TAG_String("0", "generatorOptions")]
for tag in tags:
    world.root_tag['Data'].add(tag)
