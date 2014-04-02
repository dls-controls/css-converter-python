'''
Simple python script to find and convert EDM .edl files into CSS
.opi files. It uses conv.jar, built from the latest version
of the OPIBuilder converter (as of March 2014).

    java -jar conv.jar <filename> <destination>

It also uses edm to convert old-style files into new style files
if necessary:

    edm -convert <filename>

Since this function automatically puts the file in the same directory, 
it copies the EDM files to a tmp directory first.

Steps:
 - if file is .edl file, try and convert
  - if conversion fails, it may be an old-style .edl file
  - try converting using edm, then converting again
 - if file is an image, copy across directly
'''

import os
import shutil
import stat

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
ROOT = None
EDMDATAFILES = "/dls_sw/prod/R3.14.11/support/digitelMpc/4-27/data:/dls_sw/prod/R3.14.11/support/HostLink/3-0/data:/dls_sw/prod/R3.14.11/support/insertionDevice/4-13/data:/dls_sw/prod/R3.14.11/support/mks937a/2-69/data:/dls_sw/prod/R3.14.11/support/mks937b/2-8/data:/dls_sw/prod/R3.14.11/support/rackFan/2-4-1/data:/dls_sw/prod/R3.14.11/support/rga/4-4/data:/dls_sw/prod/R3.14.11/support/vacuum/3-38/data:/dls_sw/prod/R3.14.11/support/vacuumSpace/3-22/data:/dls_sw/prod/R3.14.11/support/dlsPLC/1-8/data:/dls_sw/prod/R3.14.11/support/vxStats/1-14/data:/dls_sw/prod/R3.14.11/support/devIocStats/3-1-5dls4/data"
# BL04I
#ROOT = None
#EDMDATAFILES = "/dls_sw/prod/R3.14.11/ioc/BL02I/BL/2-16/data"

OUTDIR = './opi/vacuum'


TMPDIR = './tmp'

OPI_EXT = 'opi'
EDL_EXT = 'edl'

COPY_EXTS = ['png']

CONVERT_CMD = 'java -jar conv.jar %s %s'
UPDATE_CMD = 'edm -convert %s'

# Assemble the directories to convert.
datadirs = []
if ROOT is not None:
    datadirs.append(ROOT)
if EDMDATAFILES is not None:
    datadirs.extend(EDMDATAFILES.split(':'))


def update_edm(filename):
    '''
    Copy EDM file to temporary location.  Attempt to convert to
    new format using EDM. Return location of converted file.
    '''
    tmp_edm = os.path.join(TMPDIR, os.path.basename(filename))
    print "moving file to ", tmp_edm
    if os.path.exists(tmp_edm):
        os.chmod(tmp_edm, stat.S_IWUSR)
    shutil.copyfile(filename, tmp_edm)
    #    print "successful copy"
    x = os.system(UPDATE_CMD % tmp_edm)
    if not x:
        print "new file is %s" % tmp_edm
        os.chmod(tmp_edm, 0o777)
        return tmp_edm
    else:
        print "update finished with code", x


def convert(filename, destination):
    '''
    Try to convert .edl file.  If it fails, try updating .edl file
    using edm before converting again.
    '''
    # first try
    x = os.system('java -jar conv.jar %s %s' % (filename, destination))
    if x != 0: # conversion failed
        print 'conversion failed with code %d' % x
        new_edl = update_edm(filename)
        if new_edl is not None:
            print 'converted to new edl', new_edl
            command = CONVERT_CMD % (new_edl, destination)
            print command
            x = os.system(command)
    return x == 0


for dir in datadirs:
    print dir
    files = os.listdir(dir)
    print files
    files = [os.path.join(dir, file) for file in files]

    for file in files:
        print file
        if file.endswith(EDL_EXT):
            # change extension
            name = os.path.basename(file)
            opifile = name[:-len(EDL_EXT)] + OPI_EXT
            print opifile
            destination = os.path.join(OUTDIR, opifile)
            if os.path.isfile(destination):
                print "skipping converted file %s" % destination
            else:
                print "the destination is", destination
                if convert(file, destination):
                    print "successful"
                else:
                    print "unsuccessful"
        elif file.split('.')[-1] in COPY_EXTS:
            name = os.path.basename(file)
            destination = os.path.join(OUTDIR, name)
            os.system('cp %s %s' % (file, destination))
        else:
            print "Not doing anything with %s" % file



