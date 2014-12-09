#!/bin/bash

cd "$(dirname "$0")"

./fix_layers.py conf/layers.path
./grouping_container.py conf/groups.path
./menu_mux.py output/
./apply_patches.py
