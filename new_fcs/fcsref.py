#! /kroot/rel/default/bin/kpython3
"""
fcsref -- Capture the relevant configuration parameters of
          for the reference image.

Purpose:    

Script to capture the relevant configuration parameters of DEIMOS for the
FCS reference image obtained for the reference state of the current
instrument configuration.

To obtain an FCS reference image for a given instrument configuration,
the observer should perform the following steps:

1. Configure DEIMOS for a particular observational setup (i.e., select
grating or mirror, set grating tilt, select filter, adjust focus)
 
2. Run the 'fcszero' script to rotate DEIMOS to the reference PA (i.e.,
the PA that corresponds to the center of the flexure curve for this
configuration) and drive the tent mirror, dewar translate, and
appropriate grating stage to their respective central positions.
Note that the obsever must have control of the DEIMOS rotator
(i.e., ROTATDCS=false), the rotator must be in postion mode (i.e.,
ROTATMOD=pos), and the rotator must be unlocked (ROTATLCK=unlocked).

3. Take one or more FCS images (adjusting FCS integration time) until
a usable FCS image is obtained.  That image should be saved to disk
(i.e., set DISK WRITE ENABLED on the FCS xpose GUI or set the
FCS keyword TODISK equal to 1.

Usage:

fcsref

Arguments:

None

Output:

FCS reference file

Restrictions:

Reference file naming conventions:

In this release of the FCS system, the reference file naming conventions
have been extended to support reference file names that contain the filter
name, i.e., file names of the form:

  fcsref.GRATING_NAME.sliderNUMBER.at.TILT_WAVELENGTH.FILTER_NAME.ref

Examples of reference file names using this new format are:

  fcsref.1200G.slider3.at.7800.0.OG550.ref

  fcsref.900ZD.slider4.at.4600.0.GG455.ref

  fcsref.Mirror.slider2.at.0.0.V.ref

Contents of the reference file:

REFNAME (the name of this file)
deimot.GRATENAM
deimot.GRATEPOS
deirot.ROTATVAL
deimot.GxTLTWAV
deimot.DWFILNAM
deimot.DWFOCRAW
deimot.FLAMPS
deifcs.TTIME
deifcs.OUTDIR
deifcs.OUTFILE
deifcs.LFRAMENO 

Example:

fcsref

Modification history:

2017-Aug-03     CAAI     Original version based on the cshell script
                         fcsref by R. Kibrick (2002)
2018-May-17     CAAI     Re-write the function parseConfigFile() as
                         in fcstrack.py

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
import fcs_exceptions
import fcs_auxiliary


#######################
#######################
## Main control loop ##
#######################
#######################

def main(config):

    #----------------------------------#
    # Connect to keyword services,     #
    # monitor keywords and check that  #
    # the current configuration is     #
    # adequate to take a reference     #
    # frame.                           #
    #----------------------------------#

    #--------------------#
    # Check grating name #
    #--------------------#

    gratenam = ktl.cache('deimot', 'GRATENAM')
    try:
        gratenam.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeimotCommunicationFailure('GRATENAM')

    if ( gratenam not in config['VALID_GRATING_NAMES'] ):
        raise fcs_exception.AbortOnInvalidGratingName(gratenam)

    #-----------------------#
    # Check slider position #
    #-----------------------#

    gratepos = ktl.cache('deimot','GRATEPOS')
    try:
        gratepos.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeimotCommunicationFailure('GRATEPOS')

    if ( gratepos not in config['VALID_GRATING_POSITIONS'] ):
        raise fcs_exception.AbortOnInvalidSliderPosition(gratepos)

    #----------------------------------#
    # Check grating central wavelength #
    #----------------------------------#

    if ( gratepos == 2 ) :
        tiltwav = 0.0
    elif ( gratepos == 3 ) or ( gratepos == 4 ) :
        grtltwav = ktl.cache('deimot', 'G'+str(gratepos)+'TLTWAV')
        try:
            grtltwav.monitor()
        except ktl.ktlError:
            raise fcs_exceptions.AbortOnDeimotCommunicationFailure('G'+str(gratepos)+'TLTWAV')
        tiltwav = grtltwav
    else:
        raise.fcs_exceptions.AbortOnGratingNotClampedForFcsRef()

    #---------------------------------------------------#
    # Round the wavelength to the number of significant #
    # digits defined in the configuration file          #
    #---------------------------------------------------#

    wavel = np.around(float(tiltwav), \
                      decimals=int(config['CENTRAL_WAVELENGTH_ACCURACY']))

    #---------------------#
    # Check rotator value #
    #---------------------#

    rotatval = ktl.cache('deirot', 'ROTATVAL')
    try:
        rotatval.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeirotCommunicationFailure('ROTATVAL')

    #-----------------------------------------------------#
    # Check that rotator is approximately centered on the #
    # flexure curve for each slider                       #
    #-----------------------------------------------------#

    if gratepos == 2:
        check_rotator_pa(gratepos, float(config['SLIDER2_FLEXURE_CENTER']), float(config['SLIDER2_FLEXURE_CENTER_DELTA']), pa)

    elif gratepos == 3:
        check_rotator_pa(gratepos, float(config['SLIDER3_FLEXURE_CENTER']), float(config['SLIDER3_FLEXURE_CENTER_DELTA']), pa)

    elif gratepos == 4:
        check_rotator_pa(gratepos, float(config['SLIDER4_FLEXURE_CENTER']), float(config['SLIDER4_FLEXURE_CENTER_DELTA']), pa)

    else:
        raise fcs_auxiliary.AbortOnNoSliderClampedDown()

    #---------------------------#
    # Check grating tilt offset #
    #---------------------------#

    if ( gratepos == 2 ) :
        tiltwav = 0.0

    if ( gratepos == 3 ) or ( gratepos == 4 ):
        grtltoff = ktl.cache('deimot', 'G'+str(gratepos)+'TLTOFF')
        try:
            grtltoff.monitor()
        except ktl.ktlError:
            raise fcs_exceptions.AbortOnDeimotCommunicationFailure('G'+str(gratepos)+'TLTOFF')
        
        if grtltoff == 0:
            raise fcs_exceptions.AbortOnGratingTiltOffsetNotCenteredForFcsRef(gratepos)

        tiltwav = grtltwav

    #-------------------#
    # Check filter name #
    #-------------------#

    dwfilnam = ktl.cache('deimot', 'DWFILNAM')
    try:
        dwfilnam.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeimotCommunicationFailure('DWFILNAM')

    #--------------------------------#
    # Check the tent mirror position #
    #--------------------------------#

    tmirrval = ktl.cache('deimot', 'TMIRRVAL')
    try:
        tmirrval.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeimotCommunicationFailure('TMIRRVAL')

    TENT_MIRROR_CENTER_LLIM = config['TENT_MIRROR_CENTER'] - config['TENT_MIRROR_CENTER_DELTA']
    TENT_MIRROR_CENTER_ULIM = config['TENT_MIRROR_CENTER'] + config['TENT_MIRROR_CENTER_DELTA']

    if ( tmirrval < TENT_MIRROR_CENTER_LLIM ) or ( tmirrval > TENT_MIRROR_CENTER_ULIM ):
        raise fcs_exceptions.AbortOnTentMirrorNotCenteredForFcsRef(tmirrval)

    #-------------------------------------#
    # Check the dewar X translation stage #
    #-------------------------------------#

    dwxl8raw = ktl.cache('deimot', 'DWXL8RAW')
    try:
        dwxl8raw.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeimotCommunicationFailure('DWXL8RAW')

    DEWAR_TRANSLATION_STAGE_CENTER_LLIM = config['DEWAR_TRANSLATION_STAGE_CENTER'] - config['DEWAR_TRANSLATION_STAGE_CENTER_DELTA']
    DEWAR_TRANSLATION_STAGE_CENTER_ULIM = config['DEWAR_TRANSLATION_STAGE_CENTER'] + config['DEWAR_TRANSLATION_STAGE_CENTER_DELTA']

    if ( dwxl8raw < DEWAR_TRANSLATION_STAGE_CENTER_LLIM ) or ( dwxl8raw > DEWAR_TRANSLATION_STAGE_CENTER_ULIM ):
        raise fcs_exceptions.AbortOnDewarXTranslationNotCenteredForFcsRef(dwxl8raw)

    #---------------------------------#
    # Check the DEIMOS internal focus #
    #---------------------------------#

    dwfocraw = ktl.cache('deimot', 'DWFOCRAW')
    try:
        dwfocraw.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeimotCommunicationFailure('DWFOCRAW')

    #----------------------------#
    # Check the FCS lamps status #
    #----------------------------#

    flamps = ktl.cache('deifcs', 'FLAMPS')
    try:
        flamps.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeifcsCommunicationFailure('FLAMPS')

    if ( flamps == 'Off' ):
        raise fcs_exceptions.AbortOnFcsLampsOffForFcsRef(flamps)

    #--------------------------------#
    # Check the FCS integration time #
    #--------------------------------#

    ttime = ktl.cache('deifcs', 'TTIME')
    try:
        ttime.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeifcsCommunicationFailure('TTIME')

    if ( ttime < config['FCS_MIN_EXPTIME'] ):
        raise fcs_exceptions.AbortOnFcsExptimeTooShortFcsRef(ttime)
    elif ( ttime > config['FCS_MAX_EXPTIME'] ):
        raise fcs_exceptions.AbortOnFcsExptimeTooShortFcsRef(ttime)

    #------------------------------------#
    # Check the FCS output filename root #
    #------------------------------------#

    outfile = ktl.cache('deifcs', 'OUTFILE')
    try:
        outfile.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeifcsCommunicationFailure('OUTFILE')

    #----------------------------#
    # Check the FCS frame number #
    #----------------------------#

    frameno = ktl.cache('deifcs', 'FRAMENO')
    try:
        frameno.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeifcsCommunicationFailure('FRAMENO')

    #--------------------------------#
    # Check the FCS output directory #
    #--------------------------------#

    outdir = ktl.cache('deifcs', 'OUTDIR')
    try:
        outdir.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeifcsCommunicationFailure('OUTDIR')

    output_dir = '/s'+str(outdir)

    # OVERRIDES output directory for testing purposes.

#    output_dir = '/home/calvarez/Work/scripts/deimos/test_data'

    os.chdir(output_dir)

    #---------------------------------------#
    # Construct the FCS reference file name #
    #---------------------------------------#

    refname = 'fcsref.' + gratenam + '.slider' + str(gratepos) + '.at.' + \
              str(wavel) + '.' + dwfilnam + '.ref'

    # If the FCS reference file already exists,
    # rename the existing file by adding a random 
    # number at the end of the file name.
    
    if os.path.isfile(refname):
        suffix = str("%05d" % randint(00000,99999))
        os.rename(refname, refname+'.'+suffix)

    #--------------------------------------#
    # Write the FCS reference file in disk #
    #--------------------------------------#

    try:
        f = open(refname, 'w')
    except:
        raise fcs_exceptions.AbortOnFcsWriteNotAllowed(refname, output_dir)

    f.write(refname + '\n')
    f.write(gratenam + '\n')
    f.write(str(gratepos) + '\n')
    f.write(str(rotatval) + '\n')
    f.write(str(wavel) + '\n')
    f.write(str(dwfilnam) + '\n')
    f.write(str(dwfocraw) + '\n')
    f.write(flamps + '\n')
    f.write(str(ttime) + '\n')
    f.write(str(output_dir) + '\n')
    f.write(outfile + '\n')
    f.write(str(frameno) + '\n')
    
    f.close()

    print('')
    print('#############################################')
    print('')
    print('fcsref successful. Contents of snapshot file:')

    f = open(refname, 'r')
    print(f.read())
    f.close()

    print('#############################################')
    print('')

    exit_code = 0
    exit_message = "MSG %d: fcsref successful. Exiting fcsref." % (exit_code)

    fcs_auxiliary.fcsState.abort(exit_code, exit_message)


######################
######################
## Define functions ##
######################
######################


def proceed(message):
    """
    Ask the user if she/he wants to proceed.
    """

    proceed = input(message)
                
    if ( len(proceed.strip()) == 0 ):
        proceed = 'n'
        
    if ( proceed.lower() != 'y' ):
        error_code = -550
        error_message = "ERROR %d: fcsref terminated by user." % (error_code)
        fcs_auxiliary.fcsState.interrupt(error_code, error_message)


def check_rotator_pa(gpos, pa_flexure_center, pa_flexure_center_delta, pa):
    """
    Check if the rotator is at the correct PA angle 
    for the slider center of flexure.
    """

    low_pa = pa_flexure_center - pa_flexure_center_delta
    high_pa = pa_flexure_center + pa_flexure_center_delta

    low_pa_360 = low_pa - 360.0
    high_pa_360 = high_pa - 360.0

    if pa_flexure_center == -999:
        
        question = str('FCS reference can be taken at any rotator angle for slider %d. Do you want to proceed (y/[n])?'% gratepos)
        proceed(question)

    elif ( ( pa > low_pa ) and ( pa < high_pa ) ) or ( ( pa > low_pa_360 ) and ( pa < high_pa_360 ) ):

        question = str('DEIMOS rotator is already at PA %d, which is the slider %d center of flexure', (pa, gpos))
        proceed(question)

    else:    

        fcs_auxiliary.AbortOnRotatorNotCenteredForFcsRef()


##################
##################
## Main program ##
##################
##################

if __name__ == '__main__':
    
    fcs_config = fcs_auxiliary.parseConfigFile()
 
    while True:

        try:
            main(fcs_config)

        except fcs_exceptions.FcsError as exception:
            fcs_auxiliary.logMessage(exception.error_code, exception.error_message)
                    
sys.exit(0)

