# -*- coding: utf-8 -*-
# generate MC world
import os
import sys
import numpy as np
from pymclevel import mclevel, box, materials, nbt
from pymclevel.materials import alphaMaterials as m

import random

from osgeo import gdal
from gdalconst import *

gdal.UseExceptions()


# We set the script data dictionary for manipulating raster maps with GDAL
# we set to 1 as default since multiplication has no effect if not changed.
DEM_ds  = None          # DEM map gdal datastore
FEATURES_ds = None      # features map gdal datastore
DEM_band = None
BAND_NUM = 1          # hardcoded constant: we expect DEM maps with just one altitude band of Byte type
DEM_height = 1          # map heigth, DEM_ds.RasterYSize
DEM_width = 1           # map width, DEM_ds.RasterXSize
DEM_XpixelSize = 1          # pixel X resolution on DEM map
DEM_YpixelSize = 1          # pixel Y resolution on DEM map
DEM_AltitudeResolution = 1  # Not used, not sure if available from DEM's
DEM_Horizontal_scale = 1    # Not used, not sure if available from DEM's
DEM_Vertical_scale = 1      # suposed to be get from DEMband.GetScale()
FEATURES_height = 1         # map height
FEATURES_width= 1           # map width
MAP_Altitude = 1        # altitude_max - altitude_min + extra_space

# user parameters, to be coded if we wish to parametrize more
USER_Horizontal_scale = 1   # Not used yet
USER_Vertical_scale = 1     # Not used yet
USER_height = 1             # Not used yet
USER_width = 1              # Not used yet
USER_altitude = 1           # Not used yet

def Usage():
    print("""
    $ map_generator.py DEM_map features_map
    """)
    sys.exit(1)


#### user input // settings ####

# path where MC world is saved to
work_dir = os.getcwd()[:-6]
minecraft_save_dir = work_dir+"/../worlds"

print "Saving MC world at: %s" % minecraft_save_dir

# main #

print(sys.argv)

## tenemos que añadir otra opción más de escalado (u opcionalmente dos, de escalado horizontal y de vertical)
if len(sys.argv) < 3:
    print """
        [ ERROR ] you must supply two arguments: DEM_map features_map
       """
    Usage()

DEM_file = sys.argv[1]
FEATURES_file = sys.argv[2]

print "Loading maps"
DEM_ds = gdal.Open(DEM_file, GA_ReadOnly)
if DEM_ds is None:
    print 'Unable to open %s' % DEM_file
    sys.exit(1)

FEATURES_ds = gdal.Open (FEATURES_file, GA_ReadOnly)
if FEATURES_ds is None:
    print "Unable to open %s" % FEATURES_file
    sys.exit(1)

# transform DEM to our work pixel resolution of 1x1 meters


geotransform = DEM_ds.GetGeoTransform()
DEM_width = DEM_ds.RasterXSize * int(abs(geotransform[1]))
DEM_height = DEM_ds.RasterYSize * int(abs(geotransform[5]))

tmp_drv = gdal.GetDriverByName("VRT")
TMP_ds = tmp_drv.Create("test.vrt", DEM_width, DEM_height, 0)
tmp_drv = None

gdal.Translate("furullo.tif", DEM_ds, width=DEM_width, height=DEM_height)

# but we really want to keep the beautiful DEM_ds name:
DEM_ds = ( TMP_ds)
##TMP_ds = None


print("DEM size = %s wdith x %s height  " % (DEM_width, DEM_height))

FEATURES_height = FEATURES_ds.RasterYSize
FEATURES_width = FEATURES_ds.RasterXSize
print("Features map size = %s wdith x %s height  " % (FEATURES_width, FEATURES_height))

# maps sizes control:
if  DEM_width != FEATURES_width:
    print "Files widths are different: DEM %s != FEATURES %s" %(DEM_width , FEATURES_width)
    sys.exit(1)
if  DEM_height != FEATURES_height:
    print "Files heights are different: DEM %s != FEATURES %s" %(DEM_height , FEATURES_height)
    sys.exit(1)

# DEM altitudes are expected to be coded in just 1 band
try:
    DEM_band = DEM_ds.GetRasterBand(1)
except RuntimeError, e:
    print 'No band %i found for altitude' %( DEM_band)
    print e
    sys.exit(1)

print "DEM_band :", DEM_band

## print geo data from DEM elevation file, just for fun
print 'Driver: ', DEM_ds.GetDriver().ShortName,'/', \
      DEM_ds.GetDriver().LongName
print 'Size is ',DEM_ds.RasterXSize,'x',DEM_ds.RasterYSize, \
      'x',DEM_ds.RasterCount
print 'Projection is ',DEM_ds.GetProjection()
geotransform = DEM_ds.GetGeoTransform()
if not geotransform is None:
    print 'Origin = (',geotransform[0], ',',geotransform[3],')'
    DEM_XpixelSize = geotransform[1]
    DEM_YpixelSize = geotransform[5]
    print 'Pixel Size = (%s, %s)' % (DEM_XpixelSize, DEM_YpixelSize)

print "DEM_ds :", DEM_ds
print "DEM_band :", DEM_band
altitude_max = DEM_band.GetMaximum()
altitude_scale = DEM_band.GetScale()
altitude_min = DEM_band.GetMinimum()

MAP_altitude =  altitude_max - altitude_min + 30 # add 30 blocks of extra MAP altitude over the maximun DEM altitude

# hopefully DEM_band.GetUnitType() will be meters, so will assume 1 meter -> 1 cube

# traversing datastores
for i in range(0, DEM_width):
    # we run through columns
    row = []
    for j in range(0, DEM_height):
        # we run throught rows
        # read DEM pixel, read FEATURE pixel,
        # interpret FEATURE pixel
        # write MAP feature
        print i,j
