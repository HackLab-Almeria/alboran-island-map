# -*- coding: utf-8 -*-
import os
import sys
from pymclevel import mclevel, box, materials, nbt
from pymclevel.materials import alphaMaterials as m
from osgeo import gdal
from osgeo import gdalconst
from osgeo import gdal_array
gdal.UseExceptions()

import sqlite3
import numpy as np

blocks = {
    '0,0,0' : 'default:stone',
    '255,255,255' : 'default:dirt' 
}

def Usage():
    print('$ generate_map.py DEM_map features_map')
    sys.exit(1)

def getBlockAsInteger(i, j, k):
    return k*16777216 + j*4096 + i

def getBlock(r, g, b):
    rgb = '{0},{1},{2}'.format(r, g, b)
    try:
        return blocks[rgb]
    except:
        return blocks['0,0,0']

def createBlob(block):
    return '25,9,2,2,120,156,237,193,49,1,0,0,0,194,160,245,79,109,12,31,160,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,128,183,1,64,0,0,1,120,156,99,0,0,0,1,0,1,0,0,0,255,255,255,255,0,0,1,0,0,0,6,105,103,110,111,114,101,10,0,0'

# Fin definiciones

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

if not os.path.exists("./minetest"):
    os.makedirs("./minetest/")

with open("./minetest/world.mt", "w+") as wo:
    wo.write("backend = sqlite3\n")
    wo.write("gameid = minetest\n")

if not os.path.exists("./minetest" + "/worldmods"):
    os.makedirs("./minetest"+"/worldmods")
if not os.path.exists("./minetest" + "/worldmods/mcimport"):
    os.makedirs("./minetest"+"/worldmods/mcimport")
if not os.path.exists("./minetest"+"/worldmods/mcimport/init.lua"):
    with open("./minetest/worldmods/mcimport/init.lua", "w+") as sn:
        sn.write("-- map conversion requires a special water level\n")
        sn.write("minetest.set_mapgen_params({water_level = -2})\n\n")
        sn.write("-- prevent overgeneration in incomplete chunks, and allow lbms to work\n")
        sn.write("minetest.set_mapgen_params({chunksize = 1})\n\n")
        sn.write("-- comment the line below if you want to enable mapgen (will destroy things!)\n")
        sn.write("minetest.set_mapgen_params({mgname = \"singlenode\"})\n\n")
        sn.write("-- below lines will recalculate lighting on map block load\n")
        sn.write("minetest.register_on_generated(function(minp, maxp, seed)\n")
        sn.write("        local vm = minetest.get_voxel_manip(minp, maxp)\n")
        sn.write("        vm:set_lighting({day = 15, night = 0}, minp, maxp)\n")
        sn.write("        vm:update_liquids()\n")
        sn.write("        vm:write_to_map()\n")
        sn.write("        vm:update_map()\n")
        sn.write("end)\n\n")

mt_blocks = []
int_blocks = []
for i in range(0, len(dem_values)):
    for j in range(0, len(dem_values[i])):
       mt_blocks.append(getBlock(features_r[i][j], features_g[i][j], features_b[i][j]))
       int_blocks.append(getBlockAsInteger(i,j,dem_values[i][j]))

conn = sqlite3.connect(os.path.join("./minetest/map.sqlite"))
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS `blocks` (\
            `pos` INT NOT NULL PRIMARY KEY, `data` BLOB);")

for i in range(0, len(mt_blocks)):
    cur.execute("INSERT INTO blocks VALUES (?,?)",
                        (int_blocks[i],
                        createBlob(mt_blocks[i])))
                    
conn.commit()
conn.close()