#!/usr/bin/env python
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

def Usage():
    print('$ generate_map.py DEM_map features_map')
    sys.exit(1)

# R-values from the texture TIFF are converted to blocks of the given
# blockID, blockData, depth.
block_id_lookup = {
    '35,35,35' : (m.Grass.ID, None, 2),
    '86,191,208' : (m.Water.ID, 0, 1), # blockData 1 == grass can't spread
    '136,136,136' : (m.Grass.ID, None, 2),
    '255,255,255' : (m.Sand.ID, None, 2),
    '40,25,7' : (m.StoneBricks.ID, None, 2),
    '10,193,3' : (m.Cobblestone.ID, None, 2),
    '29,142,94' : (m.Cobblestone.ID, None, 2),
    '151,151,151' : (m.WoodPlanks.ID, None, 2),
    '0,0,0'  : (m.Grass.ID, 1, 2),
    '193,193,193' : (m.Gravel.ID, None, 2)
}

# Fin definiciones

def setspawnandsave(world, point):
    """Sets the spawn point and player point in the world and saves the world.
    Taken from TopoMC and tweaked to set biome.
    """
    world.GameType = 1
    spawn = point
    spawn[1] += 2
    world.setPlayerPosition(tuple(point))
    world.setPlayerSpawnPosition(tuple(spawn))

    # In game mode, set the biome to Plains (1) so passive
    #  mobs will spawn.
    # In map mode, set the biome to Ocean (0) so they won't.
    biome = 0
    numchunks = 0
    biomes = TAG_Byte_Array([biome] * 256, "Biomes")
    for i, cPos in enumerate(world.allChunks, 1):
        ch = world.getChunk(*cPos)
        if ch.root_tag:
            ch.root_tag['Level'].add(biomes)
        numchunks += 1

    world.saveInPlace()
    print "Saved %d chunks." % numchunks

# Fin funciones aux

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
print('Non scaled DEM size = {0} wdith x {1} height'.format(DEM_width, DEM_heigth))

FEATURES_height = FEATURES_ds.RasterYSize
FEATURES_width = FEATURES_ds.RasterXSize
print('Features size = {0} wdith x {1} height'.format(FEATURES_width, FEATURES_height))

# To avoid indexes mismatchs between DEM_ds and FEATURES_ds will use only FEATURES_width, FEATURES_height

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
mDEM_ds = gdal.Translate( '', DEM_ds, format="MEM", outputType = gdal.GDT_Int32, width=FEATURES_width, height=FEATURES_height)
print('Scaled DEM size = {0} wdith x {1} height'.format(mDEM_ds.RasterXSize, mDEM_ds.RasterYSize))

# Looking for the maximum altitude:
dem_values = mDEM_ds.GetRasterBand(1).ReadAsArray()
max_alt = np.amax(dem_values)

# Should we look for the minimum altitude too, shouldn't we?

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

# Where does the world file go?
minecraft_save_dir = './'
y_min = 0
elevation_min = 0

i = 0
worlddir = None
while not worlddir or os.path.exists(worlddir):
    i += 1
    name = "world" + " " + str(i)
    worlddir = os.path.join(minecraft_save_dir, name)

print "Creating world %s" % worlddir
world = mclevel.MCInfdevOldLevel(worlddir, create=True)
from pymclevel.nbt import TAG_Int, TAG_String, TAG_Byte_Array
tags = [TAG_Int(0, "MapFeatures"),
        TAG_String("flat", "generatorName"),
        TAG_String("0", "generatorOptions")]
for tag in tags:
    world.root_tag['Data'].add(tag)

print "Creating chunks."

x_extent = FEATURES_height
x_min = 0
x_max = FEATURES_height

z_min = 0
z_extent = FEATURES_width
z_max = z_extent

extra_space = 1

bedrock_bottom_left = [-extra_space, 0,-extra_space]
bedrock_upper_right = [x_extent + extra_space + 1, y_min-1, z_extent + extra_space + 1]

glass_bottom_left = list(bedrock_bottom_left)
glass_bottom_left[1] += 1
glass_upper_right = [x_extent + extra_space+1, max_alt, z_extent + extra_space+1]

air_bottom_left = (0,y_min,0)
air_upper_right = [x_extent, max_alt, z_extent]

# Glass walls
wall_material = m.Glass
print "Putting up walls: %r %r" % (glass_bottom_left, glass_upper_right)
tilebox = box.BoundingBox(glass_bottom_left, glass_upper_right)
chunks = world.createChunksInBox(tilebox)
world.fillBlocks(tilebox, wall_material)

# Air in the middle.
bottom_left = (0, 1, 0)
upper_right = (FEATURES_height, max_alt, FEATURES_width)
print "Carving out air layer. %r %r" % (bottom_left, upper_right)
tilebox = box.BoundingBox(bottom_left, upper_right)
world.fillBlocks(tilebox, m.Air, [wall_material])

max_height = (world.Height-elevation_min)

peak = [0, 0, 0]

print "Populating chunks."
for i in range(FEATURES_height):
    for j in range(1, FEATURES_width):
        block_id = '{0},{1},{2}'.format(features_r[i][FEATURES_width-j], features_g[i][FEATURES_width-j], features_b[i][FEATURES_width-j]) #poner otros colores
        try:
            block_id, block_data, depth = block_id_lookup[block_id]
        except KeyError, e:
            block_id, block_data, depth = block_id_lookup['0,0,0']

        y = dem_values[i][FEATURES_width-j]
        actual_y = y + y_min

        if ((i == FEATURES_height/2) and (j == FEATURES_width/2)):
            peak = [i, y, j]

        # Don't fill up the whole map from bedrock, just draw a shell.
        start_at = max(1, actual_y-depth-10)

        # If we were going to optimize this code, this is where the
        # optimization would go. Lay down the stone in big slabs and
        # then sprinkle goodies into it.
        stop_at = actual_y-depth
        for elev in range(start_at, stop_at):
            world.setBlockAt(i,elev,j, m.Stone.ID)

        start_at = actual_y - depth
        stop_at = actual_y + 1
        if block_id == m.WaterActive.ID:
            # Carve a little channel for active water so it doesn't overflow.
            start_at -= 1
            stop_at -= 1
        for elev in range(start_at, stop_at):
            world.setBlockAt(i, elev, j, block_id)
            if block_data:
                world.setBlockDataAt(i, elev, j, block_data)

setspawnandsave(world, peak)
