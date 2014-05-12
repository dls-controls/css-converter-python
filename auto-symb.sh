
symbol_file=$1
filename=`basename $symbol_file`
symdir=symbols


# Copy edl file
cp -f $symbol_file $symdir/

# Check if it's old style EDM
if ! grep -q bgColor $symdir/$filename; then
    edm -convert $symdir/$filename $symdir/$filename
fi

echo $symdir/$filename
python compress.py $symdir/$filename

# compress.py appends pixel size to name (eg x-33.edl)
nfilename=$(basename $(ls $symdir/${filename%.*}-*.edl))
nbase=${nfilename%.*}
echo $nbase

# Replace background color with bright pink
sed -i -r '1,23 s/bgColor\s+index\s+[0-9]+/bgColor index 45/' $symdir/$nfilename

# Wait for file to open with EDM, screenshot, then kill it
edm -x $symdir/$nfilename &
pid=$!
sleep 1
window_handle=$(xprop -root | grep "_NET_ACTIVE_WINDOW(WINDOW)")
import -window ${window_handle:40} $symdir/$nbase.png
kill -9 $(pgrep -P $pid); kill -9 $pid

# Replace bright pink with transparent and crop empty border
convert $symdir/$nbase.png -transparent \#ff00ff -trim +repage $symdir/$nbase.png


