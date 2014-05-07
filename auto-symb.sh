# Get everything on the path

PATH=$PATH:/dls_sw/prod/R3.14.11/support/digitelMpc/4-27/data:/dls_sw/prod/R3.14.11/support/HostLink/3-0/data:/dls_sw/prod/R3.14.11/support/insertionDevice/4-13/data:/dls_sw/prod/R3.14.11/support/mks937a/2-69/data:/dls_sw/prod/R3.14.11/support/mks937b/2-8/data:/dls_sw/prod/R3.14.11/support/rackFan/2-4-1/data:/dls_sw/prod/R3.14.11/support/rga/4-4/data:/dls_sw/prod/R3.14.11/support/vacuum/3-38/data:/dls_sw/prod/R3.14.11/support/vacuumSpace/3-22/data:/dls_sw/prod/R3.14.11/support/dlsPLC/1-8/data:/dls_sw/prod/R3.14.11/support/vxStats/1-14/data:/dls_sw/prod/R3.14.11/support/devIocStats/3-1-5dls4/data

# List of files we want to convert
names="digitelMpcIonp-symbol digitelMpcTsp-symbol mks937aImg-symbol mks937aPirg-symbol rga-symbol vacuumValve-symbol"
symdir=symbols

mkdir $symdir

for name in $names; do
    # Copy edl file
    cp -f $(which $name.edl) $symdir/

    # Check if it's old style EDM
    if ! grep -q bgColor $symdir/$name.edl; then
        edm -convert $symdir/$name.edl $symdir/$name.edl
    fi

    python compress.py $symdir/$name.edl

    # Replace background color with bright pink
    sed -i -r '1,23 s/bgColor\s+index\s+[0-9]+/bgColor index 45/' $symdir/${name}2.edl

    # Wait for file to open with EDM, screenshot, then kill it
    edm -x $symdir/${name}2.edl &
    pid=$!
    sleep 1
    window_handle=$(xprop -root | grep "_NET_ACTIVE_WINDOW(WINDOW)")
    import -window ${window_handle:40} $symdir/$name.png
    kill -9 $(pgrep -P $pid); kill -9 $pid

    # Replace bright pink with transparent and crop empty border
    convert $symdir/$name.png -transparent \#ff00ff -trim +repage $symdir/$name.png

done

