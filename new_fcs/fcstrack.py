#! /kroot/rel/default/bin/kpython3
"""fcstrack -- FCS control loop by cross-correlating the current FCS image 
            against the reference FCS image.

Purpose:    

To run the FCS control loop. The FCS reference image are defined in a
reference file whose filename matches the current configuration of the
instrument. Reference files are generated using the fcsref command.

If no reference file exists that matches the current configuration of the
instrument, then FCS tracking is inhibited until such time as either:
   1. A reference file matching the current configuration is created, or
   2. The instrument configuration is changed to correspond to an existing
      reference file

The script contains an attempt to detect spurious corrections that can
result if one of the two FCS CCDs is hit by a large cosmic ray event.
Unfortunately, this is not a simple matter of comparing the
corrections generated from the two CCDs for a single iteration,
because the corrections from each CCD can differ from each other due
to scale changes that can occur within the camera due to changes in
temperature and/or position angle.  Instead, we compare the respective
corrections for each CCD between the current iteration and the
previous iteration, and assume that for small changes in position
angle the changes in the corrections computed between the two
iterations should be nearly the same from each of the two FCS CCDs.

Usage:

fcstrack

Arguments:

None

Output:

None

Restrictions:

This script contains several simplifications and improvements with
respect to the original fcstrack cshell script:

- Single-spot is not supported.  
- Multi-spot is not supported.
- Cross-correlation in VISTA has been replaced by built-in
  cross-correlation in Python.

Example:

fcstrack

Modification history:

2017-Nov-17     CA     Original version based on the cshell script
                       fcstrack by R. Kibrick (2005)

"""

###########################
###########################
## Import Python modules ##
###########################
###########################

import sys, os
import ktl
from random import randint
import numpy as np
from fcs_exceptions import *
from astropy.io import fits

######################
######################
## Define constants ##
######################
######################

FCS_CONFIG_FILE = 'fcsconfig.dat'

#------------------------------------------------#
# Define possible values of ennumerated keywords #
#------------------------------------------------#

FCSSTATE_LST = ['OK', 'idle', 'warning', 'lockout', 'emergency']
FCSSTA_LST = ['Passive', 'Tracking', 'Warning', 'Seeking', 'Off_target', 'Lockout', 'Emergency']
FCSMODE_LST = ['Off', 'Monitor', 'Emergency', 'Track', 'Calibrate']
FCSTRACK_LST = ['on target', 'not correcting', 'seeking', 'off target']
FCSTASK_LST = ['Idle', 'Imaging', 'Processing', 'Correcting']

######################
######################
## Define functions ##
######################
######################

#--------------------------#
# Parse configuration file #
#--------------------------#

def parseConfigFile():

    """
    Read configuration file, parse content
    and create a dictionary with the file content.
    """

    f = open(FCS_CONFIG_FILE, 'r')
    data = f.readlines()
    f.close()
    
    param_set = {}
    
    for line in data:
        
        if ( len(line.strip()) != 0 ):

            if ( line.strip()[0] != '#' ):

                key = line.strip().split('=')[0].strip()
                value = line.strip().split('=')[1].strip()

                param_set[key] = value

    return param_set


##################
##################
## Main program ##
##################
##################

#--------------------------------------------#
# Load configuration from fcsconfig.dat file #
#--------------------------------------------#

config = parseConfigFile()

print (config)

# Define which FCS CCD is offline

OFFLINE = int(config['OFFLINE'])

# Set blinking mode

BLINK = int(config['BLINK'])

# Set FCS detector configuration

WINDOW_CFG = config['WINODW']
BINNING_CFG = config['BINNING']
AUTOSHUT_CFG = config['AUTOSHUT']

# Set additional FCS parameters

FCSFOTO1_CFG = config['FCSFOTO1'] 
FCSFOTO2_CFG = config['FCSFOTO2']
FCSCUSEL_CFG = config['FCSCUSEL']
FCSBOXX_CFG = config['FCSBOXX']
FCSBOXY_CFG = config['FCSBOXY'] 

# Set roator value and tolerance for the slider 2 center of flexure 

ROTATOR_CENTER_OF_FLEXURE = [float(config['SLIDER2_FLEXURE_CENTER']), \
                             float(config['SLIDER3_FLEXURE_CENTER']), \
                             float(config['SLIDER4_FLEXURE_CENTER'])]
ROTATOR_CENTER_OF_FLEXURE_TOL = \
[float(config['SLIDER2_FLEXURE_CENTER_DELTA']), \
 float(config['SLIDER3_FLEXURE_CENTER_DELTA']), \
 float(config['SLIDER4_FLEXURE_CENTER_DELTA'])]

# Tent mirror central position and tolerance

TENT_MIRROR_CENTER = float(config['TENT_MIRROR_CENTER'])
TENT_MIRROR_CENTER_TOL = float(config['TENT_MIRROR_CENTER_DELTA'])

# Dewar X translation stage center and tolerance

DEWAR_TRANSLATION_STAGE_CENTER = float(config['DEWAR_TRANSLATION_STAGE_CENTER'])
DEWAR_TRANSLATION_STAGE_CENTER_TOL = float(config['DEWAR_TRANSLATION_STAGE_CENTER_DELTA'])

# Number of significant decimal digits to define the
# central wavelength

CENTRAL_WAVELENGTH_ACCURACY = int(config['CENTRAL_WAVELENGTH_ACCURACY'])

# Central wavelength margin error

CENTRAL_WAVELENGTH_DELTA = int(config['CENTRAL_WAVELENGTH_DELTA'])

# FCS minimum and maximum exposure time

FCS_MIN_EXPTIME = int(config['FCS_MIN_EXPTIME'])
FCS_MAX_EXPTIME = int(config['FCS_MAX_EXPTIME'])

# List of valid grating positions (sliders)

VALID_GRATING_POS = config['VALID_GRATING_POSITIONS'].split(',')

# List of valid grating names

VALID_GRATING_NAM = config['VALID_GRATING_NAMES'].split(',')
NUMBER_OF_VALID_OPTICAL_ELEMENTS = len(VALID_GRATING_NAM))

# Optical model coefficients

OMODEL_PARS = {config['MODEL1_NAME']: \
               [float64(config['MODEL1_SCALE']), float(config['MODEL1_ZERO']), \
                float(config['MODEL1_OFFSET'])], config['MODEL2_NAME']: \
               [float64(config['MODEL2_SCALE']), float(config['MODEL2_ZERO']), \
                float(config['MODEL2_OFFSET'])], config['MODEL3_NAME']: \
               [float64(config['MODEL3_SCALE']), float(config['MODEL3_ZERO']), \
                float(config['MODEL3_OFFSET'])], config['MODEL4_NAME']: \
               [float64(config['MODEL4_SCALE']), float(config['MODEL4_ZERO']), \
                float(config['MODEL4_OFFSET'])], config['MODEL5_NAME']: \
               [float64(config['MODEL5_SCALE']), float(config['MODEL5_ZERO']), \
                float(config['MODEL5_OFFSET'])], config['MODEL6_NAME']: \
               [float64(config['MODEL6_SCALE']), float(config['MODEL6_ZERO']), \
                float(config['MODEL6_OFFSET'])]}

#----------------------------------#
# Connect to keyword services,     #
# monitor keywords and check that  #
# the current configuration is     #
# adequate to take a reference     #
# frame.                           #
#----------------------------------#

deimot = ktl.cache('deimot')
deirot = ktl.cache('deirot')
deifcs = ktl.cache('deifcs')
deiccd = ktl.cache('deiccd')

# Monitor grating name

gratenam = deimot['GRATENAM']
gratenam.monitor()
if ( gratenam not in VALID_GRATING_NAM ):
    raise InvalidGratingName(gratenam)

# Monitor slider position

gratepos = deimot['GRATEPOS']
gratepos.monitor()
if ( gratepos not in VALID_GRATING_POS ):
    raise InvalidSliderPosition(gratepos)

# Monitor grating central wavelength

if ( gratepos == 2 ):
    tltwav = 0.0
else:
    grtltwav = deimot['G'+str(gratepos)+'TLTWAV']
    grtltwav.monitor()
    tltwav = grtltwav

# Round the wavelength to the number of significant
# digits defined in the configuration file

wavel = np.around(float(tltwav), \
                  decimals=int(config['CENTRAL_WAVELENGTH_ACCURACY']))


# Monitor filer name

dwfilnam = deimot['DWFILNAM']
dwfilnam.monitor()

# Monitor rotator value

rotatval = deirot['ROTATVAL']
rotatval.monitor()

# Monitor the FCS output directory

outdir = deifcs['OUTDIR']
outdir.monitor()

output_dir = '/s'+str(outdir)

# OVERRIDES output directory for testing purposes.

output_dir = '/home/calvarez/Work/scripts/deimos/test_data'

os.chdir(output_dir)

# Monitor FCS operating mode

fcsmod = deifcs['FCSMODE']
fcsmod.monitor()

# Monitor FCS error

external_fcserr = deifcs['FCSERR']
external_fcserr.monitor()

# Monitor selected Cu lamp

fcscusel = deifcs['FCSCUSEL']
fcscusel.monitor()

# Monitor various FCS status and state variables

# FCSSTATE: Possible values are: 
#
# 0 --> OK
# 1 --> idle
# 2 --> warning
# 3 --> lockout
# 4 --> emergency

fcsstate = deifcs['FCSSTATE']
fcsstate.monitor()

# FCSSTA: Possible values are:
#
# 0 --> Passive
# 1 --> Tracking
# 2 --> Warning
# 3 --> Seeking
# 4 --> Off_target
# 5 --> Lockout
# 6 --> Emergency

fcssta = deifcs['FCSSTA']
fcssta.monitor()

# FCSMODE: Possible values are:
#
# 0 --> Off
# 1 --> Monitor
# 2 --> Engineering
# 3 --> Track
# 4 --> Calibrate

fcsmode = deifcs['FCSMODE']
fcsmode.monitor()

# FCSTRACK: Possible values are:
#
# 0 --> on target
# 1 --> not correcting
# 2 --> seeking
# 3 --> off target

fcstrack = deifcs['FCSTRACK']
fcstrack.monitor()

# FCSTASK: Possible values are:
#
# 0 --> Idle
# 1 --> Imaging
# 2 --> Processing
# 3 --> Correcting

fcstask = deifcs['FCSTASK']
fcstask.monitor()

# FCSSKIPS, FCSCCNOX/Y, FCSEXNOX/Y, FCSHBEAT

fcsskips = deifcs['FCSSKIPS']
fcsskips.monitor()

fcsccnox = deifcs['FCSCCNOX']
fcsccnox.monitor()

fcsccnoy = deifcs['FCSCCNOY']
fcsccnoy.monitor()

fcsexnox = deifcs['FCSEXNOX']
fcsexnox.monitor()

fcsexnoy = deifcs['FCSEXNOY']
fcsexnoy.monitor()

fcshbeat = deifcs['FCSHBEAT']
fcshbeat.monitor()

# Monitor FCS detector configuration

window = deifcs['WINDOW']
window.monitor()

binning = deifcs['BINNING']
binning.monitor()

autoshut = deifcs['AUTOSHUT']
autoshut.monitor()

# Monitor additional FCS keywords

fcsfoto1 = deifcs['FCSFOTO1']
fcsfoto1.monitor()

fcsfoto2 = deifcs['FCSFOTO2']
fcsfoto2.monitor()

fcscusel = deifcs['FCSCUSEL']
fcscusel.monitor()

fcsboxx = deifcs['FCSBOXX']
fcsboxx.monitor()

fcsboxy = deifcs['FCSBOXY']
fcsboxy.monitor()

#-----------------------------#
# Initialize control keywords #
#-----------------------------#

fcsslbad = 0
fcsetmis = 0
fcslamis = 0
fcsfomis = 0
fcstmlim = 0
fcsdxlim = 0
fcsdymin = 0
fcsnogra = 0
fcsnosli = 0
fcsnowav = 0
fcsnofil = 0
fcsnofoc = 0

x_integ = 0
y_integ = 0

x_track_min =  999.999
x_track_max = -999.999
y_track_min =  999.999
y_track_max = -999.999

x_slew_min =  999.999
x_slew_max = -999.999
y_slew_min =  999.999
y_slew_max = -999.999

clear_pending = 0

window.write(WINDOW_CFG)
binning.write(BINNING_CFG)
autoshut.write(AUTOSHUT_CFG)

fcsfoto1.write('FCSFOTO1_CFG')
fcsfoto1.write('FCSFOTO2_CFG')

fcscusel.write('FCSCUSEL_CFG')
active_flamp = 'none'

fcsboxx.write('FCSBOXX_CFG')
fcsboxy.write('FCSBOXY_CFG')


#######################
#######################
## Main control loop ##
#######################
#######################

while ( fcsstate == 'ok' ):

#------------------#
# Check FCS status #
#------------------#

#---------------------#
# DEIMOS sanity check #
#---------------------#

#-------------------#
# Take an FCS image #
#-------------------#

#-----------------------------#
# Calculate cross-correlation #
#-----------------------------#

#-------------------------#
# Move stages as required #
#-------------------------#




# Construct the FCS reference file name

refname = 'fcsref.' + gratenam + '.slider' + str(gratepos) + '.at.' +\
          str(wavel) + '.' + dwfilnam + '.ref'

# Rename the file name if already exists

if os.path.isfile(refname):
    suffix = str("%05d" % randint(00000,99999))
    os.rename(refname, refname+'.'+suffix)

#--------------------------------------#
# Write the FCS reference file in disk #
#--------------------------------------#

try:
    f = open(refname, 'w')
except:
    raise FcsWriteNotAllowed(refname, output_dir)

f.write(refname + '\n')
f.write(gratenam + '\n')
f.write(str(gratepos) + '\n')
f.write(str(rotatval) + '\n')
f.write(str(wavel) + '\n')
f.write(str(output_dir) + '\n')

f.close()

print ('')
print ('#############################################')
print ('')
print ('fcsref successful. Contents of snapshot file:')

f = open(refname, 'r')
print (f.read())
f.close()

print ('#############################################')
print ('')

sys.exit(0)

