#! /kroot/rel/default/bin/kpython3

"""
fcszero -- Rotate DEIMOS to a PA that corresponds to the center of
           the flexure range for the currently selected slider.

Purpose: 

Rotate DEIMOS to a PA that corresponds to the center of the
flexure range for the currently selected slider.  If invoked with no
arguments or with the 'new' argument, it will also reset the tent mirror,
dewar X translation stage, and any applicable tilt offsets to the center
of their respective ranges.  If invoked with the 'match' argument, only
the PA will be adjusted.

Usage:

fcszero [ new | match ]

Arguments:

new:   Configure DEIMOS to take a new reference frame.
match: Configure DEIMOS to take a matching reference frame.

Output:

None

Restrictions:

None

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

    # -----------------------------#
    # Parse command line arguments #
    # -----------------------------#

    if len(sys.argv) == 1:
        mode = 'new'
    elif sys.argv[1] == 'new':
        mode = 'new'
    elif sys.argv[1] == 'match':
        mode = 'match'
    else:
        raise fcs_exceptions.AbortOnWrongInputParameters()

    message = str('Starting fcszero in mode %s' % mode)
    fcs_auxiliary.logMEssage(message)

    # ------------------------#
    # Check state of FCSSTATE #
    # ------------------------#

    fcsstate = ktl.cache('deifcs', 'FCSSTATE')
    try:
        fcsstate.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeifcsCommunicationFailure('FCSSTATE')
    
    if fcsstate != 'idle':
        raise fcs_exceptions.AbortOnFcsStateNotIdle()

    # ---------------------------#
    # Determine Grating Position #
    # ---------------------------#

    gratepos = ktl.cache('deimot', 'GRATEPOS')
    try:
        gratepos.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeimotCommunicationFailure('GRATEPOS')

    message = str('Slider %s is clamped in position' % gratepos)
    fcs_auxiliary.logMessage(message)

    message = ('FCS about to configure DEIMOS for %s reference image' % mode)
    message_code = 0
    fcs_auxiliary.logErrorMessage(message, message_code)

    # ---------------------------#
    # Determine PA from ROTATVAL #
    # ----------------------------#

    rotatval = ktl.cache('deirot', 'ROTATVAL')
    try:
        rotatval.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeirotCommunicationFailure('ROTATVAL')

    pa = int(rotatval)

    # -------------#
    # Get ROTATLCK #
    # -------------#

    rotatlck = ktl.cache('deirot', 'ROTATLCK')
    rotatlck.monitor()
    if rotatlck != 'UNLOCKED':
        raise fcs_exceptions.RotatorLocked('')
        
    # -------------------------------#
    # Change the rotator mode to POS #
    # -------------------------------#

    rotatmod = ktl.cache('deirot', 'ROTATMOD')
    try:
        rotatmod.monitor()
        rotatmod.write('pos')
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnSettingTheRotationMode()

    # -----------------------------------#
    # Rotate to PA based on GRATEPOS     #
    # Re-center the slider if mode = new #
    # -----------------------------------#

    if gratepos == 2:
        rotate_to_pa(gratepos, float(config['SLIDER2_FLEXURE_CENTER']), float(config['SLIDER2_FLEXURE_CENTER_DELTA']), pa, rotatlck)

    elif gratepos == 3:
        rotate_to_pa(gratepos, float(config['SLIDER3_FLEXURE_CENTER']), float(config['SLIDER3_FLEXURE_CENTER_DELTA']), pa, rotatlck)
        if mode == 'new':
            new_reference(gratepos)

    elif gratepos == 4:
        rotate_to_pa(gratepos, float(config['SLIDER4_FLEXURE_CENTER']), float(config['SLIDER4_FLEXURE_CENTER_DELTA']), pa, rotatlck)
        if mode == 'new':
            new_reference(gratepos)

    else:
        raise fcs_auxiliary.AbortOnNoSliderClampedDown()

    # -----------------------------------------------#
    # If this is a new reference, then recenter tent #
    # mirror and dewar translation stage.            #
    # -----------------------------------------------#

    if mode == 'new':

        #----------------------#
        # Recenter tent mirror #
        #----------------------#
        
        tmirrval = ktl.cache('deimot', 'TMIRRVAL')
        try:
            tmirrval.monitor()
        except ktl.ktlError:
            raise fcs_exceptions.DeimotCommunicationFailure('TMIRRVAL')

        tmirr_cen_down = float(config['TENT_MIRROR_CENTER']) - float(config['TENT_MIRROR_CENTER_DELTA'])
        tmirr_cen_up = float(config['TENT_MIRROR_CENTER']) + float(config['TENT_MIRROR_CENTER_DELTA'])

        if ( tmirrval < tmirr_cen_down ) or ( tmirrval > tmirr_cen_up ):

            message = str('DEIMOS tent mirror position of %i not centered in its range' % tmirrval)
            fcs_auxiliary.logMessage(message)
            message = 'Re-centering the tent mirror'
            fcs_auxiliary.logMessage(message)

            try:
                tmirrval.write(config['TENT_MIRROR_CENTER'])
            except:
                raise fcs_exceptions.AbortOnRecenteringTentMirror()
        else:

            message = 'DEIMOS tent mirror position is already centered in its range'
            fcs_auxiliary.logMessage(message)
        
        #----------------------------------#
        # Recenter dewar translation stage #
        #----------------------------------#

        dwxl8raw = ktl.cache('deimot', 'DWXL8RAW')
        try:
            dwxl8raw.monitor()
        except ktl.ktlError:
            raise fcs_exceptions.DeimotCommunicationFailure('DWXL8RAW')

        
        dwxl8_cen_down = float(config['DEWAR_TRANSLATION_STAGE_CENTER']) - float(config['DEWAR_TRANSLATION_STAGE_CENTER_DELTA'])
        dwxl8_cen_up = float(config['DEWAR_TRANSLATION_STAGE_CENTER']) + float(config['DEWAR_TRANSLATION_STAGE_CENTER_DELTA'])

        if ( dwxl8raw < dwxl8_cen_down ) or ( dwxl8raw > dwxl8_cen_up ):

            message = str('DEIMOS X translation stage value %i is not centered in its range' % dwxl8raw))
            fcs_auxiliary.logMessage(message)
            message = 'Re-centering the dewar translate stage'
            fcs_auxiliary.logMessage(message)
            
            try:
                dwxl8raw.write(config['DEWAR_TRANSLATION_STAGE_CENTER'])
            except:
                raise fcs_exceptions.AbortOnRecenteringDewarXTranslationStage()

        else:

            message = 'DEIMOS dewar translation stage is already centered in its range'
            fcs_auxiliary.logMessage(message)

    exit_code = 0
    exit_message = "MSG %d: fcszero $s successful. You are now ready to take reference images" % (mode, exit_code)

    fcs_auxiliary.fcsState.abort(exit_code, exit_message)


######################
######################
## Define functions ##
######################
######################

def new_reference(gpos):
    """
    Recenter the grating tilt for sliders 3 and 4
    """

    gr_tlt_off = 'G' + str(gpos) + 'TLTOFF'
    
    grtiltoff = ktl.cache('deimot', gr_tlt_off)
    try:
        grtltoff.monitor()
    except ktl.ktlError:
        raise fcs_exceptions.AbortOnDeimotCommunicationFailure(grtltoff)

    if grtltoff != 0:
        
        message = str('Slider %d tilt offset %s is not centered in its range' % (gpos, gtltoff))
        fcs_auxliary.logMessage(message)
        message = str('About to recenter the slider %d tilt by setting offset = 0' % gpos)
        fcs_auxliary.logMessage(message)

        try:
            grtltoff.write(0)
        except:
            raise fcs_exceptions.AbortOnCenteringSliderTiltOffset(gpos)

    else:
        
        message = str('Slider %d tilt is already centered in its range' % gpos)
        fcs_auxliary.logMessage(message)


def rotate_to_pa(gpos, pa_flexure_center, pa_flexure_center_delta, pa, rotlck):
    """
    Rotate to required position angle for center of flexure
    """

    low_pa = pa_flexure_center - pa_flexure_center_delta
    high_pa = pa_flexure_center + pa_flexure_center_delta

    low_pa_360 = low_pa - 360.0
    high_pa_360 = high_pa - 360.0

    if pa_flexure_center == -999:
        
        message = str('Slider %d can be clamped at any rotation angle. Clamping at PA = %d', (gpos, pa))
        fcs_auxliary.logMessage(message)

    elif ( ( pa > low_pa ) and ( pa < high_pa ) ) or ( ( pa > low_pa_360 ) and ( pa < high_pa_360 ) ):

        message = str('DEIMOS rotator is already at PA %d, which is the slider %d center of flexure', (pa, gpos))
        fcs_auxliary.logMessage(message)

    else:    

        message = str('DEIMOS rotator PA of %d is not at the center of flexure for slider %d' % (pa, gpos))
        fcs_auxiliary.logMessage(message)

        if rotlck != 'UNLOCKED':

            fcs_auxiliary.AbortBecauseRotatorIsLocked()

        else:

            message = str('About tor rotate DEIMOS to PA %d, slider %d center of flexure' % (pa, gpos))
            fcs_auxiliary.logMessage(message)

            rotatval = ktl.cache('deirot', 'ROTATVAL')

            try:
                rotatval.write(pa_flexure_center)
            except:
                fcs_auxiliary.AbortOnErrorWhenRotatingDeimos(pa_flexure_center)


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


