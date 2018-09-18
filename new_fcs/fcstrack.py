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
- Cross-correlation in VISTA replaced by cross-correlation in Python.

Example:

fcstrack

Modification history:

2017-Nov-17     CAAI     Original version based on the cshell script
                         fcstrack by R. Kibrick (2005)

"""

###########################
###########################
## Import Python modules ##
###########################
###########################

import sys, os
from pathlib import Path 
import datetime as dt
from time import strftime
import ktl
from random import randint
import numpy as np
import fcs_exceptions
import fcs_auxiliary
from astropy.io import fits

#######################
#######################
## Main control loop ##
#######################
#######################

def main(config, control_variables):

    while True:

        #------------------------------------#
        # Check communications with services #
        #------------------------------------#

        control_variables = checkCommunications(control_variables)

        #------------------#
        # Update FCS state #
        #------------------#

        control_variables = updateState(config, control_variables)

        #---------------------#
        # DEIMOS sanity check #
        #---------------------#

        control_variables = checkSanity(config, control_variables)
        
        #---------------------------#
        # Search FCS reference file #
        #---------------------------#
        
        fcs_ref_image, control_variables = searchFcsRefImage(config, control_variables)

        #-------------------#
        # Take an FCS image #
        #-------------------#
        
        fcs_image, control_variables = takeFcsImage(config, control_variables)

        #-----------------------------#
        # Calculate cross-correlation #
        #-----------------------------#

        results, control_variables = calculateXcorr(config, control_variables, fcs_image, fcs_ref_image)

        #-------------------------#
        # Move stages as required #
        #-------------------------#

        control_variables = moveStages(config, control_variables, results)


######################
######################
## Define functions ##
######################
######################

def initializeControlLoop(config):

    """
    - Connect to keyword services and monitor keywords
    - Initialize configuration keywords
    - Initialize control loop variables
    """
    
    #---------------------------------#
    # Connect to keyword services and #
    # and monitor keywords.           #
    #---------------------------------#

    fcsmsg = ktl.cache('deifcs', 'FCSMSG')
    fcsmsg.monitor()
    fcserr = ktl.cache('deifcs', 'FCSERR')
    fcserr.monitor()

    # Announce that we are starting up

    msg = 'fcstrack Version ' + str(fcs_auxiliary.VERSION) + ' starting at ' + str(dt.datetime.now()) + \
          ' with offline = ' + str('%1d' % config['OFFLINE'])
    fcs_auxiliary.logMessage(msg)

    # Monitor grating name
    
    gratenam = ktl.cache('deimot', 'GRATENAM')
    gratenam.monitor()

    # Monitor slider position
    
    gratepos = ktl.cache('deimot', 'GRATEPOS')
    gratepos.monitor()
        
    # Monitor filter name

    dwfilnam = ktl.cache('deimot', 'DWFILNAM')
    dwfilnam.monitor()

    # Monitor rotator value

    rotatval = ktl.cache('deirot', 'ROTATVAL')
    rotatval.monitor()

    # Monitor the FCS output directory

    outdir = ktl.cache('deifcs', 'OUTDIR')
    outdir.monitor()

    # Monitor FCS operation mode

    fcsmod = ktl.cache('deifcs', 'FCSMODE')
    fcsmod.monitor()

    # Monitor FCS error
    
    fcserr = ktl.cache('deifcs', 'FCSERR')
    fcserr.monitor()

    # Monitor selected Cu lamp

    fcscusel = ktl.cache('deifcs', 'FCSCUSEL')
    fcscusel.monitor()

    # Monior FCS lamps status

    flamps = ktl.cache('deimot', 'FLAMPS')
    flamps.monitor()
    
    # Monitor the FCS filename keywords

    fcsreffi = ktl.cache('deifcs', 'FCSREFFI')
    fcsreffi.monitor()
    fcsimgfi = ktl.cache('deifcs', 'FCSIMGFI')
    fcsimgfi.monitor()
    fcslogfi = ktl.cache('deifcs', 'FCSLOGFI')
    fcslogfi.monitor()
    
    # Monitor FCS X-correlation keywords

    fcsintxm = ktl.cache('deifcs', 'FCSINTXM')
    fcsintxm.monitor()
    fcsintym = ktl.cache('deifcs', 'FCSINTYM')
    fcsintym.monitor()
        
    # Monitor various FCS status and state variables

    # FCSSTATE: Possible values are: 
    #
    # 0 --> OK
    # 1 --> idle
    # 2 --> warning
    # 3 --> lockout
    # 4 --> emergency
    
    fcsstate = ktl.cache('deifcs', 'FCSSTATE')
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
    
    fcssta = ktl.cache('deifcs', 'FCSSTA')
    fcssta.monitor()

    # FCSMODE: Possible values are:
    #
    # 0 --> Off
    # 1 --> Monitor
    # 2 --> Engineering
    # 3 --> Track
    # 4 --> Calibrate
    
    fcsmode = ktl.cache('deifcs', 'FCSMODE')
    fcsmode.monitor()

    # FCSTRACK: Possible values are:
    #
    # 0 --> on target
    # 1 --> not correcting
    # 2 --> seeking
    # 3 --> off target
    
    fcstrack = ktl.cache('deifcs', 'FCSTRACK')
    fcstrack.monitor()
    
    # FCSTASK: Possible values are:
    #
    # 0 --> Idle
    # 1 --> Imaging
    # 2 --> Processing
    # 3 --> Correcting
    
    fcstask = ktl.cache('deifcs', 'FCSTASK')
    fcstask.monitor()

    # FCSSKIPS, FCSCCNOX/Y, FCSEXNOX/Y, FCSHBEAT
    
    fcsskips = ktl.cache('deifcs', 'FCSSKIPS')
    fcsskips.monitor()
    fcsccnox = ktl.cache('deifcs', 'FCSCCNOX')
    fcsccnox.monitor()
    fcsccnoy = ktl.cache('deifcs', 'FCSCCNOY')
    fcsccnoy.monitor()
    fcsexnox = ktl.cache('deifcs', 'FCSEXNOX')
    fcsexnox.monitor()
    fcsexnoy = ktl.cache('deifcs', 'FCSEXNOY')
    fcsexnoy.monitor()
    
    fcshbeat = ktl.cache('deifcs', 'FCSHBEAT')
    fcshbeat.monitor()
    
    # Monitor FCS detector configuration
    
    window = ktl.cache('deifcs', 'WINDOW')
    window.monitor()
    
    binning = ktl.cache('deifcs', 'BINNING')
    binning.monitor()
    
    autoshut = ktl.cache('deifcs', 'AUTOSHUT')
    autoshut.monitor()
    
    # Monitor additional FCS keywords
    
    fcsfoto1 = ktl.cache('deifcs', 'FCSFOTO1')
    fcsfoto1.monitor()    
    fcsfoto2 = ktl.cache('deifcs', 'FCSFOTO2')
    fcsfoto2.monitor()
    
    fcscusel = ktl.cache('deifcs', 'FCSCUSEL')
    fcscusel.monitor()
    
    fcsboxx = ktl.cache('deifcs', 'FCSBOXX')
    fcsboxx.monitor()
    fcsboxy = ktl.cache('deifcs', 'FCSBOXY')
    fcsboxy.monitor()
    
    # Monitor number of matching reference files

    fcsnogra = ktl.cache('deifcs', 'FCSNOGRA')
    fcsnogra.monitor()
    fcsnosli = ktl.cache('deifcs', 'FCSNOSLI')
    fcsnosli.monitor()
    fcsnowav = ktl.cache('deifcs', 'FCSNOWAV')
    fcsnowav.monitor()
    fcsnofil = ktl.cache('deifcs', 'FCSNOFIL')
    fcsnofil.monitor()
    fcsnofoc = ktl.cache('deifcs', 'FCSNOFOC')
    fcsnofoc.monitor()


    #-----------------------------------#
    # Initialize configuration keywords #
    #-----------------------------------#

    # Start with no errors

    fcserr.write(0)

    # Intialize FCS state keywords

    fcsstate.write('OK', wait=True)
    fcssta.write('Passive', wait=True)
    fcsmode.write('Off', wait=True)
    fcstrack.write('not correcting', wait=True)
    fcstask.write('Idle', wait=True)

    # Initialize focus tolerance keywords

    fcsfoto1.write(config['FCSFOTO1'])
    fcsfoto2.write(config['FCSFOTO2'])

    # Initialize CuAr selected lamp keyword
    
    fcscusel.write(config['FCSCUSEL'])
    
    # Initialize FCS box size keywords

    fcsboxx.write(config['FCSBOXX'])
    fcsboxy.write(config['FCSBOXY'])

    # Initialize nuber of matching reference files

    fcsnogra.write(0)
    fcsnosli.write(0)
    fcsnowav.write(0)
    fcsnofil.write(0)
    fcsnofoc.write(0)
    
    # Initialize detector configuration keywords

    chip = config['WINDOW'].split(',')[0]
    xstart = config['WINDOW'].split(',')[1]
    ystart = config['WINDOW'].split(',')[2]
    xlen = config['WINDOW'].split(',')[3]
    ylen = config['WINDOW'].split(',')[4]
    
    xbinning = config['BINNING'].split(',')[0]
    ybinning = config['BINNING'].split(',')[1]

    window_str = '\n\tchip number ' + chip + '\n\txstart ' + xstart + \
                 '\n\tystart ' + ystart + '\n\txlen ' + xlen + '\n\tylen ' + ylen
    binning_str = '\n\tXbinning ' + xbinning + '\n\tYbinning ' + ybinning
    
    window.write(window_str)
    binning.write(binning_str)
    autoshut.write(config['AUTOSHUT'])
    

    #------------------------------#
    # Initialize control veriables #
    #------------------------------#

    output_dir = '/s'+str(outdir)

    # OVERRIDES output directory for testing purposes.

    output_dir = '/home/calvarez/Work/scripts/deimos/test_data'

    os.chdir(output_dir)

    fcs_err = fcserr.read()
    fcs_state = fcsstate.read()
    fcs_sta = fcssta.read()
    fcs_mode = fcsmode.read()
    fcs_track = fcstrack.read()
    fcs_task = fcstask.read()
    fcs_heart_beat = 0

    active_flamp = 'none'

    fcs_ref_files_found = 0

    fcs_gain = 0

    ref_name = fcsreffi.read()
    ref_image = fcsimgfi.read()
    log_name = fcslogfi.read()

    fcsslbad = 0
    fcsetmis = 0
    fcslamis = 0
    fcsfomis = 0
    fcstmlim = 0
    fcsdxlim = 0
    fcsdymin = 0

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
    

    #------------------------------#
    # Define dictionary containing #
    # the control variables.       #
    #------------------------------#

    ctrl_var = { 'fcs_err':fcs_err, 'fcs_state':fcs_state, 'fcs_sta': fcs_sta, \
                 'fcs_mode': fcs_mode, 'fcs_track': fcs_track, 'fcs_task': fcstask, \
                 'fcs_heart_beat': fcs_heart_beat, 'active_flamp': active_flamp, \
                 'fcs_ref_files_found': fcs_ref_files_found, 'fcs_gain': fcs_gain, \
                 'ref_name': ref_name, 'ref_image': ref_image, 'log_name': log_name, \
                 'output_dir': output_dir }

    return ctrl_var


def checkCommunications(ctrl_var):
    
    """
    Check communications with keyword services
    """

    # Check communications with the deifcs service.
    
    fcstask = ktl.cache('deifcs', 'FCSTASK')
    try:
        fcstask.monitor()
    except ktl.ktlError:
        ctrl_var = fcs_exceptions.DeifcsCommunicationFailure('FCSTASK', ctrl_var)

    # Check communications with the deiccd service.

    ampmode = ktl.cache('deiccd', 'AMPMODE')
    try:
        ampmode.monitor()
    except ktl.ktlError:
        ctrl_var = fcs_exceptions.DeiccdCommunicationFailure('AMPMODE', ctrl_var)

    # Check communications with the deimot service.
    
    gratenam = ktl.cache('deimot', 'GRATENAM')
    try:
        gratenam.monitor()
    except ktl.ktlError:
        ctrl_var = fcs_exceptions.DeimotCommunicationFailure('GRATENAM', ctrl_var)

    # Check communications with the deirot service.

    rotatval = ktl.cache('deirot', 'ROTATVAL')
    try:
        rotatval.monitor()
    except ktl.ktlError:
        ctrl_var = fcs_exceptions.DeirotCommunicationFailure('ROTATVAL', ctrl_var)

    return ctrl_var


def updateState(config, ctrl_var):
    
    """
    Update the master STATUS of the FCS loop
    """

    fcscusel = ktl.cache('deifcs', 'FCSCUSEL')
    fcserr = ktl.cache('deifcs', 'FCSERR')
    fcstask = ktl.cache('deifcs', 'FCSTASK')
    fcsstate = ktl.cache('deifcs', 'FCSSTATE')
    fcssta = ktl.cache('deifcs', 'FCSSTA')
    fcstrack = ktl.cache('deifcs', 'FCSTRACK')
    fcsmode = ktl.cache('deifcs', 'FCSMODE')
    fcshbeat = ktl.cache('deifcs', 'FCSHBEAT')

    #---------------------------------------------#
    # Compute master status. Logic is based on    #
    # memo from Wirth and Faber, "Proposed design #
    # for FCS GUI", January 2, 2003.              #
    #---------------------------------------------#

    # Color codes based on the FCSSTA keyword:
    #
    # 0 --> Passive    --> Gray
    # 1 --> Tracking   --> Green
    # 2 --> Warning    --> Yellow
    # 3 --> Seeking    --> Yellow
    # 4 --> Off_target --> Red
    # 5 --> Lockout    --> Red
    # 6 --> Emergency  --> Red

    if ( fcsstate.read() == 'emergency' ):
        ctrl_var['fcs_status'] = 'Emergency'
    elif ( fcsstate.read() == 'lockout' ):
        ctrl_var['fcs_status'] = 'Lockout'
    elif ( fcstrack.read() == 'off target' ):
        ctrl_var['fcs_status'] = 'Off_target'
    elif ( fcsstate.read() == 'OK' ) and ( fcstrack.read() == 'seeking' ):
        ctrl_var['fcs_status'] = 'Seeking'
    elif ( fcsstate.read() == 'warning' ):
        ctrl_var['fcs_status'] = 'Warning'
    elif ( fcsstate.read() == 'OK' ) and ( fcstrack.read() == 'on target' ):
        ctrl_var['fcs_status'] = 'Tracking'
    elif ( fcsmode.read() == 'Off' ) or ( fcsmode.read() == 'Monitor' ) or \
         ( fcsstate.read() == 'idle' ) or ( fcstrack.read() == 'not correcting' ):
        ctrl_var['fcs_status'] = 'Passive'
    else:
        ctrl_var['fcs_status'] = 'Emergency'


    # Send notification of any changes in FCS TASK
        
    if fcstask.read() != ctrl_var['fcs_task']:
        msg = 'fcstask changed from ' + fcstask.read() + ' to ' + \
              ctr_lvar['fcs_task'] + ' at ' + str(dt.datetime.now())
        fcs_auxiliary.logMessage(msg)
        fcstask.write(ctrl_var['fcs_task'], wait=True)

    # Send notification of any changes in FCS STATE
        
    if fcsstate.read() != ctrl_var['fcs_state']:
        msg = 'fcsstate changed from ' + fcsstate.read() + ' to ' + \
              ctr_lvar['fcs_state'] + ' at ' + str(dt.datetime.now())
        fcs_auxiliary.logMessage(msg)
        fcsstate.write(ctrl_var['fcs_state'], wait=True)

    # Send notification of any changes in FCS TRACK
        
    if fcstrack.read() != ctrl_var['fcs_track']:
        msg = 'fcstrack changed from ' + fcstrack.read() + ' to ' + \
              ctr_lvar['fcs_track'] + ' at ' + str(dt.datetime.now())
        fcs_auxiliary.logMessage(msg)
        fcstrack.write(ctrl_var['fcs_track'], wait=True)

    # Send notification of any changes in FCS master STATUS
        
    if fcssta.read() != ctrl_var['fcs_status']:
        msg = 'fcssta changed from ' + fcssta.read() + ' to ' + \
            ctr_lvar['fcs_status'] + ' at ' + str(dt.datetime.now())
        fcs_auxiliary.logMessage(msg)
        fcssta.write(ctrl_var['fcs_status'], wait=True)

    # Update the name of the active FCS lamp

     if ( ctrl_var['active_flamp'] == 'Cu1' ) or ( ctrl_var['active_flamp'] != 'Cu2' ) and ( fcscusel.read() != ctrl_var['active_flamp'] ):
        ctrl_var['active_flamp'] = fcscusel.read()
        fcs_exceptions.SwitchToAnotherFcsLamp(fcscusel.read())

    # Clear any previous error state

    if ( fcserr.read() < 0 ) and ( fcserr.read() != ctrl_var['fcs_err'] ):
        ctrl_var['fcs_err'] = 0
        fcserr.write(ctrl_var['fcs_err'], wait=True)

    # FCS state control variable at the start of the current 
    # loop iteration is OK.

    ctrl_var['fcs_state'] = 'OK', wait=True)

    # Update FCS heartbeat keyword.

    ctrl_var['fcs_heart_beat'] = ctrl_var['fcs_heart_beat'] + 1
    ctrl_var['fcs_heart_beat'] = ctrl_var['fcs_heart_beat'] % 10000
    fcshbeat.write(ctrl_var['fcs_heart_beat'], wait=True)

    return ctrl_var


def checkSanity(config, ctrl_var):
    
    """
    Check that DEIMOS has the minimum optical configuration required for 
    the FCS to function correctly.
    """

    gratenam = ktl.cache('deimot', 'GRATENAM')
    gratepos = ktl.cache('deimot', 'GRATEPOS')
    grtltwav = ktl.cache('deimot', 'G'+str(gratepos)+'TLTWAV')
    grtltnom = ktl.cache('deimot', 'G'+str(gratepos)+'TLTNOM')

    dwfilnam = ktl.cache('deimot', 'DWFILNAM')

    outdir = ktl.cache('deifcs', 'OUTDIR')

    try:
        gratenam.monitor()
        gratepos.monitor()
        grtltwav.monitor()
        grtltnom.monitor()
        dwfilnam.monitor()
    except ktl.ktlError:
        ctrl_var = fcs_exceptions.DeimotKeywordAccessFailure(ctrl_var)
        
    if ( gratenam == 'Unknown' ) or ( gratepos == -999 ):
        ctrl_var = fcs_exceptions.NoSliderClampedDown(ctrl_var)

    if ( gratepos not in config['VALID_GRATING_POSITIONS'] ):
        ctrl_var = fcs_exceptions.NoSliderClampedDown(ctrl_var)

    if ( dwfilnam == 'Unknown' ):
        ctrl_var = fcs_exceptions.FilterChangeInProgress(ctrl_var)

    try:
        outdir.monitor()
    except ktl.ktlError:
        ctrl_var = fcs_exceptions.FcsOutdirNotAccessibleFromDeifcs(ctrl_var)

    return ctrl_var


def searchFcsRefImage(config, ctrl_var):

    """
    Search for an FCS reference file corresponding to
    the current optical cofiguration. Files can be
    located in either the current directory or in
    the FCS reference frames archive.
    """
    
    #------------------------------------#
    # List possible reference file names #
    #------------------------------------#

    # Determine the current optical configuration

    gratenam = ktl.cache('deimot', 'GRATENAM')
    gratepos = ktl.cache('deimot', 'GRATEPOS')

    gratenam.monitor()
    gratepos.monitor()

    if ( gratepos == 2 ) or ( gratepos == 0 ):
        tiltwav = 0.0
    else:
        grtltwav = ktl.cache('deimot', 'G'+str(gratepos)+'TLTWAV')
        grtltwav.monitor()
        tiltwav = grtltwav

    # Round the wavelength to the number of significant
    # digits defined in the configuration file
    
    wavel = np.around(float(tiltwav), \
                      decimals=int(config['CENTRAL_WAVELENGTH_ACCURACY']))

    dwfilnam = ktl.cache('deimot', 'DWFILNAM')
    dwfilnam.monitor()

    outdir = ktl.cache('deifcs', 'OUTDIR')
    outdir.monitor()
    
    ctrl_var['output_dir'] = '/s'+str(outdir)

    ### OVERRIDES output directory for testing purposes. ###

    ctrl_var['output_dir'] = '/home/calvarez/Work/scripts/deimos/test_data'
    os.chdir(output_dir)

    approot = '.' + gratenam.read() + '.slider' + gratepos.read() + '.at.' + str(wavel)
    refroot = 'fcsref' + approot + '.' + dwfilnam.read()
    ctrl_var['ref_file'] = refroot + '.ref'

    fcsref_filename_for_current_config = output_dir + '/' + ref_file

    fcsreffi = ktl.cache('deifcs', 'FCSREFFI')
    fcsreffi.monitor()
    fcsimgfi = ktl.cache('deifcs', 'FCSIMGFI')
    fcsimgfi.monitor()
    fcslogfi = ktl.cache('deifcs', 'FCSLOGFI')
    fcslogfi.monitor()

    fcsnogra = ktl.cache('deifcs', 'FCSNOGRA')
    fcsnogra.monitor()
    fcsnosli = ktl.cache('deifcs', 'FCSNOSLI')
    fcsnosli.monitor()
    fcsnowav = ktl.cache('deifcs', 'FCSNOWAV')
    fcsnowav.monitor()
    fcsnofil = ktl.cache('deifcs', 'FCSNOFIL')
    fcsnofil.monitor()
    fcsnofoc = ktl.cache('deifcs', 'FCSNOFOC')
    fcsnofoc.monitor()

    #-------------------------------------------------#
    # Check if the reference file name stored in the  #
    # keyword FCSREFFI is on either the local FCS     #
    # directory, or on the FCSREF_ARCHIVE directory.  #
    #-------------------------------------------------#

    if fcsreffi != fcsref_filename_for_current_config:

        #-------------------------------------------------------------#
        # If FCSREFFI does not match the current configuration, then  #
        # this is because the optical configuration has changed since #
        # the last time the keyword FCSREFFI was written.             #
        #-------------------------------------------------------------#

        fcs_ref_files_found = 0

        message = 'Configuration has just changed.'
        fcs_auxiliary.logMessage(message)

        if Path(fcsref_filename_for_current_config).is_file():

            #----------------------------------------------------#
            # Check if there is a file in the current FCS outdir # 
            # that matches the FCS reference file name for the   #
            # current optical configuration.                     #
            #----------------------------------------------------#

            ctrl_var['ref_name'] = fcsref_filename_for_current_config
            message = 'Reference file for this configuration is %s.' % refname
            fcs_auxiliary.logMessage(message)
            ctrl_var['log_name'] = fcsref_filename_for_current_config[:-4] + '.log'

            fcsnogra.write(1)
            fcsnosli.write(1)
            fcsnowav.write(1)
            fcsnofil.write(1)

            fcs_ref_files_found = 1 

        else:

            #-------------------------------------------#
            # Look for the reference file in the on the #
            # FCS reference file archive.               #
            #-------------------------------------------#

            this_year = int(dt.datetime.now().year)
            year_list = this_year - range(config['YEARS_BACK'])
        
            all_archived_ref_dates = os.listdir(config['FCSREF_ARCHIVE'])

            selected_archived_ref_dates_full_path = []

            for year in year_list:

                for date_dir in all_old_dates:

                    dir_matches_year = re.match(str(year), datedir)

                    if dir_matches_year != None:

                        selected_archived_ref_dates_full_path.append(config['FCSREF_ARCHIVE'] + datedir)

            matched_archived_ref_dirs = []
            matched_archived_ref_files = []

            for date_dir_full_path in selected_archived_ref_dates_full_path:

                file_matches_current_config_ref_file = re.match(date_dir_full_path, ref_file)

                if file_matches_current_config_ref_file != None:

                    matched_archived_ref_dirs.append(date_dir_full_path)
                    matched_archived_ref_files.append(date_dir_full_path + '/' + ref_file)
               
            number_of_matched_ref_files = len(matched_archived_ref_files)
     
            fcsnogra.write(number_of_matched_ref_files)
            fcsnosli.write(number_of_matched_ref_files)
            fcsnowav.write(number_of_matched_ref_files)
            fcsnofil.write(number_of_matched_ref_files)

            fcs_ref_files_found = number_of_matched_ref_files

            #------------------------------------------#
            # Update the refname, refimage and logname #
            # variables depending on how many matching #
            # files have been found.                   #
            #------------------------------------------#
                
            if number_of_matched_ref_files > 0:
                
                # Select the first matching file on the list
                # and create the corresponding log file
                                
                ctrl_var['ref_name'] = matched_archived_ref_files[0]
                message = 'Matched reference file for this configuration is %s.' % refname
                fcs_auxiliary.logMessage(message)
                ctrl_var['log_name'] = fcsref_filename_for_current_config[:-4] + '.log'
                
            else:

                # There is NOT a file that matches the 
                # FCS reference name for the current 
                # configuration.

                ctrl_var['ref_name'] = ''
                ctrl_var['log_name'] = ''

                raise fcs_exceptions.FcsrefAccessFailure(fcsref_filename_for_current_config)                    

        #-----------------------------------------------#
        # Create a log file if a matching FCS reference #
        # file exists the log file does not exist yet.  #
        #-----------------------------------------------#

        if fcs_ref_files_found > 0:

            if not Path(logname).is_file():
            
                try:
                    Path(logname).touch()
                    message = 'Log file %s successdully created.' % logname
                    fcs_auxiliary.logMessage(message)
                except:
                    raise fcs_exceptions.FcsLogFileWriteNotAllowed(logname)
        
        fcsreffi.write(ctrl_var['ref_file'])
        fcslogfi.write(ctrl_var['logname'])


        #----------------------------------------------#
        # If an FCS reference file was found for the   #
        # current optical configuration, then read it. #
        #----------------------------------------------#

        if fcs_ref_files_found > 0:

            f = open(fcsref_filename_for_current_config, 'r')
            all_lines = f.readlines()
            f.close()
            
            if len(all_lines) != 12:
                raise fcs_exceptions.IncompleteFcsReferenceFile(fcsref_filename_for_current_config)

            ref_outdir = all_lines[9].strip()
            ref_outfile = all_lines[10].strip()
            ref_frameno = all_lines[11].strip()

            msg = 'Reference image file outdir is %s' % ref_outdir
            fcs_auxiliary.logMessage(msg)
            msg = 'Reference image file outfile is %s' % ref_outfile
            fcs_auxiliary.logMessage(msg)
            msg = 'Reference image file frameno is %s' % ref_frameno
            fcs_auxiliary.logMessage(msg)

            ref_file_name = ref_outdir + 


    else:

        #------------------------------------------------#
        # The keyword FCSREFFI matches the FCS reference #
        # file name corresponding to the current optical #
        # configuration.                                 #
        #------------------------------------------------#

        ctrl_var['ref_name'] = fcsreffi.read()
        ctrl_var['ref_image'] = fcsimgfi.read()
        ctrl_var['log_name'] = fcslogfi.read()
        ctrl_var['fcs_gain'] = fcs_gain

    return ctrl_var


def takeFcsImage(config, ctrl_var):

    """
    - Check FCS and science CCDs exposure status
    - Take a new FCS image, if possible    
    """

    return fcsimage, ctrl_var


def calculateXcorr(config, ctrl_var, fcsimage, refimage):

    """
    - Perform x-corr between current and reference FCS images
    - Transform x-corr results into corrections
    """

    return results, ctrl_var

    
def moveStages(config, ctrl_var, results):

    """
    - Read corrections from calculateXcorr
    - Move stages if needed
    - Update the FCS status keywords
    """

    return ctrl_var

##################
##################
## Main program ##
##################
##################

if __name__ == '__main__':
    
    fcs_config = fcs_auxiliary.parseConfigFile()
    control_var = intializeControlLoop(fcs_config)
 
    while True:

        try:
            main(fcs_config, control_var)

        except fcs_exceptions.FcsError as exception:
            fcs_auxiliary.logErrorMessage(exception.error_code, exception.error_message)
                    

sys.exit(0)

