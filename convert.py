

import os

EDMDATAFILES = None
# MPS
#EDMDATAFILES = '.:/dls_sw/prod/R3.14.11/support/devIocStats/Rx-y/data:/dls_sw/prod/R3.14.11/ioc/BR/MP/Rx-y/data:/dls_sw/prod/R3.14.11/ioc/SR/MP/Rx-y/data'
#ROOT = '/dls_sw/prod/R3.14.11/support/MPS/Rx-y/data'

# Master Oscillator
#ROOT = "/dls_sw/prod/R3.14.11/ioc/CS/CS-RF-IOC-02/Rx-y/data"
#EDMDATAFILES = "/dls_sw/prod/R3.14.11/support/devIocStats/Rx-y/data"

# Diagnostics overview
#EDMDATAFILES = "/dls_sw/prod/R3.14.12.3/ioc/Libera/2.05.15/opi:/dls_sw/prod/R3.14.12.3/ioc/TMBF/2.3/opi:/dls_sw/prod/R3.14.11/ioc/IsaPBPM/1-1/opi:.:/dls_sw/prod/R3.14.12.3/support/motor/6-7-1dls8/data:/dls_sw/prod/R3.14.12.3/support/vxStats/1-14-1/data:/dls_sw/prod/R3.14.12.3/support/enzLoCuM4/2-29/data:/dls_sw/prod/R3.14.12.3/support/pmacUtil/4-20/data:/dls_sw/prod/R3.14.12.3/support/vacuumValve/4-22/data:/dls_sw/prod/R3.14.12.3/support/TimingTemplates/6-6-3/data:/dls_sw/prod/R3.14.12.3/support/4chTimer/3-2/data"

# Vacuum
#ROOT = None
#EDMDATAFILES = "/dls_sw/prod/R3.14.11/support/digitelMpc/4-27/data:/dls_sw/prod/R3.14.11/support/HostLink/3-0/data:/dls_sw/prod/R3.14.11/support/insertionDevice/4-13/data:/dls_sw/prod/R3.14.11/support/mks937a/2-69/data:/dls_sw/prod/R3.14.11/support/mks937b/2-8/data:/dls_sw/prod/R3.14.11/support/rackFan/2-4-1/data:/dls_sw/prod/R3.14.11/support/rga/4-4/data:/dls_sw/prod/R3.14.11/support/vacuum/3-38/data:/dls_sw/prod/R3.14.11/support/vacuumSpace/3-22/data:/dls_sw/prod/R3.14.11/support/dlsPLC/1-8/data:/dls_sw/prod/R3.14.11/support/vxStats/1-14/data:/dls_sw/prod/R3.14.11/support/devIocStats/3-1-5dls4/data"
# BL04I
ROOT = None
EDMDATAFILES = "/dls_sw/prod/R3.14.11/ioc/BL02I/BL/2-16/data"



OUTDIR = './BL04I'

OPI_EXT = '.opi'
EDL_EXT = '.edl'

datadirs = []
if ROOT is not None:
    datadirs.append(ROOT)
if EDMDATAFILES is not None:
    datadirs.extend(EDMDATAFILES.split(':'))

def edl2opi(filename):
    print filename
    filename = os.path.basename(filename)
    print filename
    if filename.endswith(EDL_EXT):
        return filename[:-len(EDL_EXT)] + OPI_EXT




for dir in datadirs:
    print dir
    files = os.listdir(dir)
    print files
    files = [os.path.join(dir, file) for file in files]

    for file in files:
        print file
        if file.endswith('.edl'):
            opifilename = edl2opi(file)
            print opifilename
            destination = os.path.join(OUTDIR, opifilename)
            os.system('java -jar conv.jar %s %s' % (file, destination))
        elif file.endswith('.png'):
            destination = os.path.join(OUTDIR, file)
            os.system('cp %s %s' % (file, destination))
        else:
            print "Not doing anything with %s" % file



