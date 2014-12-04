#!/bin/bash

symbol_file=$1
filename=`basename $symbol_file`
symdir=tmp/symbols

# compress.py appends pixel size to name (eg x-33.edl)
nfilename=$(basename $(ls $symdir/${filename%.*}-*.edl))
nbase=${nfilename%.*}

# Replace background color with bright pink
sed -i -r '1,23 s/bgColor\s+index\s+[0-9]+/bgColor index 45/' $symdir/$nfilename

# Ensure png files in symbols directory are available to EDM
export EDMDATAFILES=.:$symdir

# Wait for file to open with EDM, screenshot, then kill it
edm -x $symdir/$nfilename &
pid=$!
sleep 1
window_handle=$(xprop -root | grep "_NET_ACTIVE_WINDOW(WINDOW)")
import -window ${window_handle:40} $symdir/$nbase.png
kill -9 $(pgrep -P $pid); kill -9 $pid

# Replace bright pink with transparent and crop empty border
convert $symdir/$nbase.png -transparent \#ff00ff $symdir/$nbase.png


echo $symdir/$nbase.png
