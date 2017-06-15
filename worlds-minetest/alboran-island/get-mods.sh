#!/bin/sh
# run this script to automatically get all the required mods
cd worldmods
for mod in LNJ2/carpet minetest-mods/signs_lib minetest-mods/xdecor minetest-mods/plantlife_modpack Jeija/minetest-mod-mesecons pilzadam/nether minetest-mods/crops minetest-mods/quartz minetest-mods/biome_lib oOChainLynxOo/hardenedclay minetest-mods/lapis minetest-mods/flowerpot; do
    echo "Fetching: $mod"
    s=`basename $mod`
    curl -q -L -o master.zip https://codeload.github.com/$mod/zip/master
    unzip -qq master.zip
    rm master.zip
    mv $s-master $s
done
for ex in plantlife_modpack/dryplants plantlife_modpack/along_shore plantlife_modpack/molehills plantlife_modpack/woodsoils plantlife_modpack/bushes plantlife_modpack/bushes_classic plantlife_modpack/youngtrees plantlife_modpack/3dmushrooms plantlife_modpack/cavestuff plantlife_modpack/poisonivy plantlife_modpack/trunks; do
    echo "Pruning: $ex"
    rm -rf $ex
done
