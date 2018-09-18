
#! /kroot/rel/default/bin/kpython3
"""
fcs_auxiliary -- Define classes and functions common to
                 all FCS scripts (fcstrack, fcszero, fcsref)

Purpose: 

To define classes and functions common to all
DEIMOS FCS tracking software.

Usage:

N/A

Arguments:

N/A

Output:

N/A

Restrictions:

None

Example;

N/A

Modification history:

2018-May-17     CAAI     Original version


"""
###########################
###########################
## Import Python modules ##
###########################
###########################

import sys, os
import datetime as dt
from time import strftime
import ktl

######################
######################
## Define constants ##
######################
######################

FCS_CONFIG_FILE = 'fcsconfig.dat'
VERSION = 5.0

####################
####################
## Define classes ##
####################
####################

class fcsState:

    """
    Class to define the different states that can
    be adopted by the FCS system. The class takes
    input control variables, modifies them and
    returns the modified control variables.
    
    """

    def __init__ (self, ctrl_var):
        
        """
        Initialize class instances with the 
        current values of the control variables.
        """

        self.ctrl_var = ctrl_var

        return

    def idle(error_code, error_message):

        """
        Idle state
        """

        self.ctrl_var['fcs_state'] = 'idle'
        self.ctrl_var['fcs_track'] = 'not correcting'
        self.ctrl_var['fcs_task'] = 'Idle'
        logErrorMessage(error_code, error_message)

        return self.ctrl_var


    def warning(error_code, error_message):

        """
        Warning state
        """

        self.ctrl_var['fcs_state'] = 'warning'
        logErrorMessage(error_code, error_message)

        return self.ctrl_var


    def lockout(error_code, error_message):
        
        """
        Lockout state
        """

        if self.ctrl_var['fcs_mode'] == 'Off':
            self.ctrl_var['fcs_state'] = 'idle'
        else:
            self.ctrl_var['fcs_state'] = 'lockout'

        self.ctrl_var['fcs_task'] = 'Idle'
        logErrorMessage(error_code, error_message)

        return self.ctrl_var
    

    def emergency(error_code, error_message):
        
        """
        Emergency state
        """

        self.ctrl_var[fcs_state] = 'emergency'
        logErrorMessage(error_code, error_message)

        return self.ctrl_var


    def interrupt(error_code, error_message):

        """
        There is no need to update the control
        variables on interrupt, because the
        script is terminated.
        """
        
        fcssta = ktl.cache('deifcs', 'FCSSTA')
        fcsstate = ktl.cache('deifcs', 'FCSSTATE')
        fcstrack = ktl.cache('deifcs', 'FCSTRACK')
        fcstask = ktl.cache('deifcs', 'FCSTASK')
        fcssta.write('passive', wait=True)
        fcsstate.write('idle', wait=True)
        fcstask.write('Idle', wait=True)
        fcstrack.write('not correcting', wait=True)

        fcsreffi = ktl.cache('deifcs', 'FCSREFFI')
        fcsimgfi = ktl.cache('deifcs', 'FCSIMGFI')
        fcslogfi = ktl.cache('deifcs', 'FCSLOGFI')
        fcsreffi.write('', wait=True)
        fcsimgfi.write('', wait=True)
        fcslogfi.write('', wait=True)

        fcsintxm = ktl.cache('deifcs', 'FCSINTXM')
        fcsintym = ktl.cache('deifcs', 'FCSINTYM')
        fcsintxm.write(0.0, wait=True)
        fcsintym.write(0.0, wait=True)

        flamps = ktl.cache('deifcs', 'FLAMPS')
        flamps.write('off', wait=True)

        logErrorMessage(error_code, error_message)
        
        sys.exit(error_code)


    def abort(exit_code, exit_message):
        
        """
        There is no need to update the control
        variables on abort, because the script
        is terminated.
        """
 
        logErrorMessage(exit_code, exit_message)

        sys.exit(exit_code)


######################
######################
## Define functions ##
######################
######################

def logMessage(message):

    """
    Print message on the terminal.
    Update FCSMSG keyword.
    """

    fcsmsg = ktl.cache('deifcs', 'FCSMSG')

    if fcsmsg != message:
        fcsmsg.write(message, wait=True)
        
    print(str(dt.datetime.now())' --> ' message)


def logErrorMessage(error_code, error_message):

    """
    Prints error code and message on the terminal.
    Updates FCSERR and FCSMSG keywords.
    """

    fcserr = ktl.cache('deifcs', 'FCSERR')
    fcsmsg = ktl.cache('deifcs', 'FCSMSG')

    if fcserr != error_code:
        fcserr.write(error_code, wait=True)
    if fcsmsg != error_message:
        fcsmsg.write(error_message, wait=True)
        
    print(str(dt.datetime.now()) + ' --> ' + error_message)


def parseConfigFile():

    """
    Read configuration file, parse content
    and create a dictionary with the file content.
    """

    f = open(FCS_CONFIG_FILE, 'r')
    data = f.readlines()
    f.close()
    
    integer_params = {'OFFLINE': True, 'BLINK': True, 'AUTOSHUT': True, \
                      'FCSFOTO1': True, 'FCSFOTO2': True, 'G3TLTNOM_ZO': True, \
                      'GRATING_TILT_LLIM': True, 'GRATING_TILT_ULIM': True, \
                      'TENT_MIRROR_LLIM': True, 'TENT_MIRROR_ULIM': True, \
                      'TENT_MIRROR_BUFF': True, \
                      'FCS_MIN_EXPTIME': True, 'FCS_MAX_EXPTIME': True, \
                      'DEWAR_TRANSLATION_STAGE_CENTER': True, \
                      'DEWAR_TRANSLATION_STAGE_CENTER_DELTA': True, \
                      'DEWAR_TRANSLATION_STAGE_ULIM': True, \
                      'DEWAR_TRANSLATION_STAGE_LLIM': True, \
                      'DEWAR_TRANSLATION_STAGE_BUFF': True, \
                      'CENTRAL_WAVELENGTH_ACCURACY': True, \
                      'MODEL1_ZERO': True, 'MODEL2_ZERO': True, 'MODEL3_ZERO': True, \
                      'MODEL4_ZERO': True, 'MODEL5_ZERO': True, 'MODEL6_ZERO': True
                  }

    float_params = {'FCSBOXX': True, 'FCSBOXY': True, 'TENT_MIRROR_CENTER': True, \
                    'TENT_MIRROR_CENTER_DELTA': True, \
                    'MODEL2_SCALE': True, 'SLIDER2_FLEXURE_CENTER': True, \
                    'SLIDER2_FLEXURE_CENTER_DELTA': True, \
                    'SLIDER3_FLEXURE_CENTER': True, 'SLIDER3_FLEXURE_CENTER_DELTA': True, \
                    'SLIDER4_FLEXURE_CENTER': True, 'SLIDER4_FLEXURE_CENTER_DELTA': True, \
                    'CENTRAL_WAVELENGTH_DELTA': True, \
                    'MODEL1_SCALE': True, 'MODEL1_OFFSET': True, \
                    'MODEL2_SCALE': True, 'MODEL2_OFFSET': True, \
                    'MODEL3_SCALE': True, 'MODEL3_OFFSET': True, \
                    'MODEL4_SCALE': True, 'MODEL4_OFFSET': True, \
                    'MODEL5_SCALE': True, 'MODEL5_OFFSET': True, \
                    'MODEL6_SCALE': True, 'MODEL6_OFFSET': True
                }

    optical_model_params = []

    param_set = {}
    
    for line in data:
        
        if ( len(line.strip()) != 0 ):

            if ( line.strip()[0] != '#' ):

                key = line.strip().split('=')[0].strip()
                value = line.strip().split('=')[1].strip()
            
                if ( key in float_params ) or ( key in integer_params ):
                    
                    value = float(value)
                    
                    if ( value in integer_params ):
                        value = round(value)
                        value = int(value)

                if ( key == 'VALID_GRATING_POSITIONS' ):
                    value = value.split(',')
                    
                if ( key == 'VALID_GRATING_NAMES' ):
                    value = value.split(',')

                param_set[key] = value

    param_set['NUMBER_OF_VALID_OPTICAL_ELEMENTS'] = len(param_set['VALID_GRATING_NAMES'])
    
    # Optical model coefficients
    
    param_set['OMODEL_PARS'] = {param_set['MODEL1_NAME']: \
                   [param_set['MODEL1_SCALE'], param_set['MODEL1_ZERO'], \
                    param_set['MODEL1_OFFSET']], param_set['MODEL2_NAME']: \
                   [param_set['MODEL2_SCALE'], param_set['MODEL2_ZERO'], \
                    param_set['MODEL2_OFFSET']], param_set['MODEL3_NAME']: \
                   [param_set['MODEL3_SCALE'], param_set['MODEL3_ZERO'], \
                    param_set['MODEL3_OFFSET']], param_set['MODEL4_NAME']: \
                   [param_set['MODEL4_SCALE'], param_set['MODEL4_ZERO'], \
                    param_set['MODEL4_OFFSET']], param_set['MODEL5_NAME']: \
                   [param_set['MODEL5_SCALE'], param_set['MODEL5_ZERO'], \
                    param_set['MODEL5_OFFSET']], param_set['MODEL6_NAME']: \
                   [param_set['MODEL6_SCALE'], param_set['MODEL6_ZERO'], \
                    param_set['MODEL6_OFFSET']]}

            
    return param_set
