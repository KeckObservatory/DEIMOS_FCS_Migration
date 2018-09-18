#! /kroot/rel/default/bin/kpython3
"""
fcs_exceptions -- List a series of exceptions definitions that are specific to
                  the operation of the FCS system.

Purpose: 

To define a series of exceptions that are specific to the operation of
the DEIMOS FCS tracking software.


Usage:

N/A

Arguments:

N/A

Output:

Warning messages have code > 0 
Error messages have code < 0
A code=0 clears all previous errors 

List of error and warning codes for fcstrack:

Trigger                                        Code        fcsstate
----------------------------------------------------------------------
Control loop is idle:                             0        idle
Science CCD is erasing:                           5        (info)
Science CCD is paused:                            6        lockout
Science CCD is reading out:                       7        lockout
Turned on FCS lamp:                               8        (info)
Comparison lamp is on:                            9        lockout
Comparison lamps are on:                         10        lockout
Grating tilt does not match ref:                 20        lockout
FCS image is writing to disk:                    20        (info)
FCS image finished writing to disk:              21        (info)
Processing FCS image:                            22        (info)
Tent mirror recentering is needed:               23        (info)
FCS image now aligned within tolerance:          24        (info)
Applying FCS corrections:                        25        (info)
Re-centering tent mirror:                        26        (info)
Grating tilt adjusted for tent recenteting:      27        (info)
FCS corrections applied:                         28        (info)
FCS tracking not available for config:           50        lockout
Filter change in progress:                       52        lockout
Slider unclamp during FCS exposure:              68        ignore image
Slider/grating changed during FCS exposure:      69        ignore image
Grating tilt changed during FCS exposire:        70        ignore image
Filter changed during FCS exposure:              71        ignore image
Focus changed during FCS exposure:               72        ignore image
Tracking reference level re-established:        150        (info)
FCS senses deimos rotation slew:                160        (info) 
Switch active lamp:                             170        (info)
Filter changed during FCS readout:              171        ignore image
Focus changed during FCS readout:               172        ignore image

Tent mirror failed to complete move:            -10        emergency
Cannot adjust grating tilt on mirror recenter:  -11        emergency
Dewar stage failed to complete the move:        -11        emergency
Error commanding shutter close:                 -14        emergency
Keyword read error:                             -21        emergency
Cannot read output directory:                   -22        emergency
Account no read access:                         -23        (info)
Incomplete reference file:                      -24        lockout
No gain file for config:                        -25        (info)
Account cannot access to gain file:             -26        (info)
No default gain file for config:                -27        lockout 
Error reading deimot keywords:                  -28        emergency
Filter missmatch:                               -29        lockout
Focus does not match reference:                 -30        warning
Error reading deifcs keywords:                  -31        emergency
Account cannot create log file:                 -32        warning
Error reading deiccd keywords:                  -33        emergency
FCS lamp state does not match reference:        -34        (info)
Cannot turn on FCS lamp:                        -35        emergency
Cannot read FCS exposure time keyword:          -36        emergency
FCS exposure time does not match ref:           -37        (info)
Cannot set the FCS exposure time:               -38        emergency
Account lacks write access:                     -39        warning 
Cannot read shutter status:                     -40        emergency
FCS lamps were not off:                         -41        (info)
Cannot turn off FCS lamps:                      -42        emergency
Cannot read comparison lamps status:            -43        emergency
No slider clamped:                              -51        lockout
(*) Invalid grating name for FCS:               -52        lockout
(*) Invalid slider position for FCS:            -53        lockout
Reference image not found:                      -60        lockout
Account lacks read access:                      -61        lockout
Cannot read deimot keywords:                    -67        emergency
FCS image did not write to disk within 30 sec:  -73        emergency
Error reading FCS disk file keywords:           -74        emergency
FCS image did not finish writing disk 15 sec:   -75        emergency
Expected FCS image file does not exist:         -76        emergency
Account lacks read access to FCS image file:    -77        emergency
ROTATVAL keyword not found in FCS FITS header:  -78        warning
Error reading ROTATVAL:                         -79        warning
GXTLTNOM not found in FCS FITS header:          -80        warning
Error reading GXTLTNOM:                         -81        warning
GXTLTOFF not found in FCS FITS header:          -82        warning
Error reading GXTLTOFF:                         -83        warning
TMIRRRAW not found in FCS FITS header:          -84        warning
Error reading TMIRRRAW:                         -85        warning
DWXL8RAW not found in FCS FITS header:          -86        warning
Error reading DWXL8RAW:                         -87        warning
LFRAMENO is different from FRAMENO in header:   -88        emergency
X-Correlation failed. Image contrast too low:   -89        emergency
FCS CCDs differ in X. Cosmic ray?               -90        ignore image
FCS CCDs differ in Y. Cosmic ray?               -91        ignore image
Dewar translation stage negative limit reached: -95        emergency
Dewar translation stage positive limit reached: -96        emergency
Tent mirror low limit reached:                  -97        emergency
Tent mirror high limit reached:                 -98        emergency
FCS correction not possible. Missing vals:     -100        emergency
Cannot pause science exp. to recenter mirror:  -101        emergency
Cannot resume science exposure after tent rec: -103        emergency
Closing the shutter:                           -104        (info)
Focus too far from reference focus:            -110        lockout
Error reading FCS lamps:                       -128        emergency
Error reading calibration lamps:               -129        emergency
FCS CCDs differ in X. Cosmic ray?              -190        ignore image
FCS CCDs differ in Y. Cosmic ray?              -191        ignore image
-----------------------------------------------------------------------


List of error and warning codes for fcszero:

Trigger                                        Code        fcsstate
-----------------------------------------------------------------------
Abort on deifcs communication faliure          -200        abort
Abort on deimot communication faliure          -201        abort
Abort on deirot communication faliure          -202        abort
Rotator is locked                              -204        warning
Abort on setting the rotation mode             -205        abort
Abort because rotator is locked                -206        abort
Abort on error rotating deimos                 -209        abort
Abort on centering slider 3 tilt offset        -211        abort
Abort on centering slider 4 tilt offset        -213        abort
Abort on no Slider clamped down                -215        abort
Abort on recentering tent mirror               -216        abort
Abort on recentering dewar X translation stage -218        abort
Abort on wrong input parameters                -400        abort
-----------------------------------------------------------------------

List of error and warning codes for fcsref:

Trigger                                        Code        fcsstate
-----------------------------------------------------------------------
Abort On tent mirror not centered              -500        abort
Abort On dewar X Translation not Centered      -501        abort
Abort On fcs lamps off                         -502        abort
Abort On fcs exptime too short                 -503        abort
Abort On fcs exptime too long                  -504        abort
Abort On grating tilt offset mot centered      -505        abort
Abort On grating not clamped                   -506        abort
Abort On rotator not centered                  -507        abort
-----------------------------------------------------------------------




Restrictions:

None

Example;

N/A

Modification history:

2018-May-18     CAAI     Original version
      
"""

import sys
import fcs_auxiliary


class FcsError(RuntimeError):
    """
    An FcsError instance will have a .error_code and .error_message
    attributes for processing by the caller of the fcstrack main()
    function.
    """
    pass


#-----------------------------------#
# Exceptions in the fcstrack script #
#-----------------------------------#

class TentMirrorNeedsRecentering(FcsError):

    """
    Exception when the tent mirror needs
    to be recentered.
    """

    def __init__(self, tmirrval):

        self.tmirrval = tmirrval

        error_code = 23

        msg = "MSG %d: Tent mirror position %7.3f is not centered in its range." \
              % (error_code, self.tmirrval)

        error_message = msg

        fcs_auxiliary.logErrorMessage(error_code, error_message)


class FilterChangeInProgress(FcsError):

    """
    Exception when filter name is unknown, likely
    due to a filter change in progress.
    """

    def __init__(self, ctrl_var):

        self.ctrl_var = ctrl_var

        error_code = 52

        msg = "MSG %d: Filter change in progress?" \
              % (error_code)

        error_message = msg

        # Number of reference filters and focus values found.

        fcsnofil = ktl.cache('deifcs', 'FCSNOFIL')
        fcsnofoc = ktl.cache('deifcs', 'FCSNOFOC')

        fcsnofil.write(0)
        fcsnofoc.write(0)

        self.ctrl_var = fcs_auxiliary.fcsState(self.ctrl_var).lockout(error_code, error_message)
        
        return self.ctrl_var


class SwitchToAnotherFcsLamp(FcsError):

    """
    Exception when we need to switch from one
    FCS lamp to another one.
    """

    def __init__(self, fcscusel):

        self.fcscusel = fcscusel

        error_code = 140

        msg = "MSG %d: Switching to %s lamp as the default CuAr source." \
              % (error_code, self.fcscusel)

        error_message = msg

        fcs_auxiliary.logErrorMessage(error_code, error_message)


class DeimotKeywordAccessFaiulure(FcsError): 

    """
    Exception when a grating keyword cannot be accessed.
    """

    def __init__(self, ctrl_var):

        self.ctrl_var = ctrl_var

        error_code = -21

        msg = "ERROR %d: Cannot read grating name, position, tilt wavelenghts or filter name." % (error_code)

        error_message = msg

        self.ctrl_var = fcs_auxiliary.fcsState(self.ctrl_var).emergency(error_code, error_message)

        return self.ctrl_var


class FcsOutdirNotAccessibleFromDeifcs(FcsError): 

    """
    Exception when the outdir keyword cannot be accessed
    from the deifcs service.
    """

    def __init__(self, ctrl_var):

        self.ctrl_var = ctrl_var

        error_code = -22

        msg = "ERROR %d: Cannot read FCS output directory from deifcs service, retrying." % (error_code)

        error_message = msg

        self.ctrl_var = fcs_auxiliary.fcsState(self.ctrl_var).emergency(error_code, error_message)

        return self.ctrl_var 
        

class FcsrefAccessFailure(FcsError): 

    """
    Exception when the FCS reference file cannot be accessed.
    """

    def __init__(self, name):

        self.name = name

        error_code = -23

        msg = "ERROR %d: This account does not have read access to the reference file '%s'." % (error_code, self.name)

        error_message = msg

        fcs_auxiliary.logErrorMessage(error_code, error_message)
        

class IncompleteFcsReferenceFile(FcsError): 

    """
    Exception when the FCS reference file does not
    have the correct number of arguments.
    """

    def __init__(self, name, ctrl_var):

        self.name = name
        self.ctrl_var = ctrl_var

        error_code = -24

        msg = "ERROR %d: Incomplete reference file '%s'." % (error_code, self.name)

        error_message = msg

        self.ctrl_var = fcs_auxiliary.fcsState(ctrl_var).lockout(error_code, error_message)

        return self.ctrl_var


class DeimotCommunicationFailure(FcsError):

    """
    Exception when there is a communication failure
    with the deimot service
    """

    def __init__ (self, keyword, ctrl_var):

        self.keyword = keyword
        self.ctrl_var = ctrl_var

        error_code = -28
        
        msg = "ERROR %d: Cannot read %s keyword from deimot service." \
              % (error_code, self.keyword)

        error_message = msg

        self.ctrl_var = fcs_auxiliary.fcsState(self.ctrl_var).emergency(error_code, error_message)
        
        return self.ctrl_var


class DeifcsCommunicationFailure(FcsError):

    """
    Exception when there is a communication failure
    with the deifcs service
    """

    def __init__ (self, keyword, ctrl_var):
        
        self.keyword = keyword
        self.ctrl_var = ctrl_var

        error_code = -31
        
        msg = "ERROR %d: Cannot read %s keyword from deifcs service." \
              % (error_code, self.keyword)

        error_message = msg

        self.ctrl_var = fcs_auxiliary.fcsState(self.ctrl_var).emergency(error_code, error_message)

        return self.ctrl_var


class FcsLogFileWriteNotAllowed(FcsError):

    """
    Exception when it is not possible to create the log file
    in the current FCS data directory.
    """

    def __init__(self, filename, ctrl_var):

        self.filename = filename
        self.ctrl_var = ctrl_var

        error_code = -32

        msg = "ERROR %d: Cannot create logfile %s." \
              % (error_code, self.filename)

        error_message = msg

        self.ctrl_var = fcs_auxiliary.fcsState(self.ctrl_var).warning(error_code, error_message)

        return self.ctrl_var


class DeiccdCommunicationFailure(FcsError):

    """
    Exception when there is a communication failure
    with the deiccd service
    """

    def __init__ (self, keyword, ctrl_var):
        
        self.keyword = keyword
        self.ctrl_var = ctrl_var

        error_code = -33
        
        msg = "ERROR %d: Cannot read %s keyword from deiccd service." \
              % (error_code, self.keyword)

        error_message = msg

        self.ctrl_var = fcs_auxiliary.fcsState(self.ctrl_var).emergency(error_code, error_message)

        return self.ctrl_var


class DeirotCommunicationFailure(FcsError):

    """
    Exception when there is a communication failure
    with the deirot service
    """

    def __init__ (self, keyword):
        
        self.keyword = keyword
        self.ctrl_var = ctrl_var

        error_code = -33
        
        msg = "ERROR %d: Cannot read %s keyword from deirot service." \
              % (error_code, self.keyword)

        error_message = msg

        self.ctrl_var = fcs_auxiliary.fcsState(self.ctrl_var).emergency(error_code, error_message)

        return self.ctrl_var


class FcsWriteNotAllowed(FcsError):

    """
    Exception when it is not possible to write a file
    in the current FCS data directory.
    """

    def __init__(self, filename, dirname, ctrl_var):

        self.filename = filename
        self.dirname = dirname
        self.ctrl_var = ctrl_var

        error_code = -39

        msg = "ERROR %d: Cannot write %s in %s." \
              % (error_code, self.filename, self.dirname)

        error_message = msg

        self.ctrl_var = fcs_auxiliary.fcsState(self.ctrl_var).warning(error_code, error_message)

        return self.ctrl_var


class NoSliderClampedDown(FcsError):

    """
    Exception when there is no slider clamped down,
    likely because there is a slider change in progress.
    """

    def __init__(self, ctrl_var):

        self.ctrl_var = ctrl_var

        error_code = -51

        msg = "ERROR %d: No slider is clampled down. Slider change in progress?" \
              % (error_code)

        error_message = msg

        # Number of reference gratings, sliders, wavelenghts,
        # filters and focus values found.

        fcsnogra = ktl.cache('deifcs', 'FCSNOGRA')
        fcsnosli = ktl.cache('deifcs', 'FCSNOSLI')
        fcsnowav = ktl.cache('deifcs', 'FCSNOWAV')
        fcsnofil = ktl.cache('deifcs', 'FCSNOFIL')
        fcsnofoc = ktl.cache('deifcs', 'FCSNOFOC')

        fcsnogra.write(0)
        fcsnosli.write(0)
        fcsnowav.write(0)
        fcsnofil.write(0)
        fcsnofoc.write(0)

        # Integral and adjusted additional correction calculated in experimental
        # predictive algorithm when tracking rotator velocity is near those
        # encountered through the keyhole.

        fcsintxm = ktl.cache('deifcs', 'FCSINTXM')
        fcsintym = ktl.cache('deifcs', 'FCSINTYM')
        fcsadjxm = ktl.cache('deifcs', 'FCSADJXM')
        fcsadjym = ktl.cache('deifcs', 'FCSADJYM')

        fcsintxm.write(0)
        fcsintym.write(0)
        fcsadjxm.write(0)
        fcsadjym.write(0)
        
        self.ctrl_var = fcs_auxiliary.fcsState(self.ctrl_var).lockout(error_code, error_message)

        return self.ctrl_var


class InvalidGratingName(FcsError):

    """
    Exception when the grating name is not in
    the list of allowed grating names.
    """

    def __init__(self, grname, ctrl_var):

        self.grname = grname
        self.ctrl_val = ctrl_val

        error_code = -52

        msg = "ERROR %d: Grating name %s is not valid for FCS." \
              % (error_code, self.grname)

        error_message = msg

        self.ctrl_val = fcs_auxiliary.fcsState(self.ctrl_var).lockout(error_code, error_message)

        return self.ctrl_var


class InvalidSliderPosition(FcsError):

    """
    Exception when the slider position is not in the
    list of allowed slider positions.
    """

    def __init__(self, pos, ctrl_var):

        self.pos = pos
        self.ctrl_var = ctrl_var

        error_code = -53

        msg = "ERROR %d: Grating postion number %d is not valid for FCS." \
              % (error_code, pos)

        error_message = msg

        self.ctrl_val = fcs_auxiliary.fcsState(self.ctrl_var).emergency(error_code, error_message)

        return self.ctrl_var


class FcsInterrupt(FcsError):

    """
    Exception triggered when the FCS tracking
    loop is interrupted.
    """

    def __init__(self, ctrl_var):
        
        self.ctrl_var = ctrl_var

        error_code = -300

        msg = "ERROR %d: fcstrack shut down." \
              % (error_code, file, dir)
        error_message = msg

        fcs_auxiliary.fcsState(self.ctrl_var).interrupt(error_code, error_message)


#----------------------------------#
# Exceptions in the fcszero script #
#----------------------------------#

class AbortOnDeifcsCommunicationFaliure(FcsError):

    """
    Exception when the fcszero script cannot stablish
    communication with the deifcs service.
    """

    def __init__(self, keyword):

        error_code = -200

        msg = "ERROR %d: Cannot read %s keyword from deifcs service." % (error_code, keyword)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnDeimotCommunicationFaliure(FcsError):

    """
    Exception when the fcszero script cannot stablish
    communication with the deimot service.
    """

    def __init__(self, keyword):

        error_code = -201

        msg = "ERROR %d: Cannot read %s keyword from deimot service." % (error_code, keyword)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnDeirotCommunicationFaliure(FcsError):

    """
    Exception when the fcszero script cannot stablish
    communication with the deirot service.
    """

    def __init__(self, keyword):

        error_code = -202

        msg = "ERROR %d: Cannot read %s keyword from deirot service." % (error_code, keyword)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class RotatorLocked(FcsError):

    """
    Exception when the rotation system is locked
    """

    def __init__(self):

        error_code = -204

        msg = "WARNING %d: The DEIMOS rotation system is locked." % (error_code)

        error_message = msg

        fcs_auxiliary.LogErrorMessage(error_code, error_message)


class AbortOnSettingTheRotationMode(FcsError):

    """
    Exception when the fcsstate differs from idle
    """

    def __init__(self):

        error_code = -205

        msg = "ERROR %d: Cannot set the rotation mode to pos" % (error_code)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortBecauseRotatorIsLocked(FcsError):

    """
    Exception when it is not possible to rotate DEIMOS
    because rotator is locked.
    """

    def __init__(self):

        error_code = -206

        msg = "ERROR %d: Unable to rotate DEIMOS because rotator is locked." % (error_code)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnErrorRotatingDeimos(FcsError):

    """
    Exception when the DEIMOS rotator fails
    rotating to a given position.
    """

    def __init__(self, target_pa):

        error_code = -209

        msg = "ERROR %d: Error rotating DEIMOS to PA %d" % (error_code, target_pa)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnCenteringSliderTiltOffset(FcsError):

    """
    Exception when recentering the slider tilt offset
    fails. This exception includes both, slider 3 and 4.
    """

    def __init__(self, gpos):

        if gpos == 3:
            error_code = -211
        if gpos == 4:
            error_code = -213

        msg = "ERROR %d: Cannot recenter the slider %d tilt offset" % (error_code, gpos)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnNoSliderClampedDown(FcsError):

    """
    Exception when no slider is clamped down.
    """

    def __init__(self):

        error_code = -215

        msg = "ERROR %d: No slider is clamped in place, so FCS cannot be zeroed" % (error_code)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnRecenteringTentMirror(FcsError):

    """
    Exception when recentering the tent mirror fails.
    """

    def __init__(self):

        error_code = -216

        msg = "ERROR %d: Error recentering the tent mirror." % (error_code)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnRecenteringDewarXTranslationStage(FcsError):

    """
    Exception when recentering the dewar
    X translation stage fails.
    """

    def __init__(self):

        error_code = -218

        msg = "ERROR %d: Error recentering the dewar X translation stage." % (error_code)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnWrongInputParameters(FcsError):

    """
    Exception when the fcszero script has the wrong
    input parameters.
    """

    def __init__(self):

        error_code = -400

        msg = "ERROR %d: Incorrect usage. Correct usage is: fcszero [ new| match ]." % (error_code)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


#---------------------------------#
# Exceptions in the fcsref script #
#---------------------------------#

#----------------------------------------------#
# Exceptions also used for the fcszero script: #
#                                              #
# AbortOnDeifcsCommunicationFaliure            #
# AbortOnDeimotCommunicationFaliure            #
# AbortOnDeirotCommunicationFaliure            #
#----------------------------------------------#

class AbortOnTentMirrorNotCenteredForFcsRef(FcsError):

    """
    Exception when the tent mirror needs
    to be recentered.
    """

    def __init__(self, tmirrval):

        error_code = -500

        msg = "ERROR %d: DEIMOS tent mirror position %7.3f is not centered in its range. Please, use fcszero command to re-center the tent mirror and then re-take the spot image. Aborting fcsref..." % (error_code, tmirrval)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnDewarXTranslationNotCenteredForFcsRef(FcsError):

    """
    Exception when the dewar X translation stage
    needs to be recentered.
    """

    def __init__(self, dwxl8raw):

        error_code = -501

        msg = "ERROR %d: Dewar X translation stage value %d is not centered in its range. Please, use fcszero command to re-center the dewar X translation stage and then re-take the spot image. Aborting fcsref..." % (error_code, dwxl8raw)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnFcsLampsOffForFcsRef(FcsError):

    """
    Exception when none of the Cu lamps in the 
    FCS system are on.
    """

    def __init__(self):

        error_code = -502

        msg = "ERROR %d: None of the FCS lamps are turned on. You must have an FCS lamp on to capture the spots. Aborting fcsref..." % (error_code)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnFcsExptimeTooShortForFcsRef(FcsError):

    """
    Exception when the FCS exposure time is too short
    """

    def __init__(self, ttime):

        error_code = -503

        msg = "ERROR %d: FCS exposure time of %d is too short. Aborting fcsref..." % (error_code, ttime)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnFcsExptimeTooLongForFcsRef(FcsError):

    """
    Exception when the FCS exposure time is too short
    """

    def __init__(self, ttime):

        error_code = -504

        msg = "ERROR %d: FCS exposure time of %d is too long. Aborting fcsref..." % (error_code, ttime)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnGratingTiltOffsetNotCenteredForFcsRef(FcsError):

    """
    Exception when the fcs grating tilt offset
    is not centered.
    """

    def __init__(self, slider):

        error_code = -507

        msg = "ERROR %d: Slider %d not centered in its range. Please, use fcszero command to reset the DEIMOS PA and then re-take spot image. Aborting fcsref..." % (error_code, pa, slider)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnGratingNotClampedForFcsRef(FcsError):

    """
    Exception when no grating is clamped
    """

    def __init__(self):

        error_code = -506

        msg = "ERROR %d: No slider is currently clamped in position. You must have a slider clamped in order to capture the reference spot. Aborting fcsref..." % (error_code)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnRotatorNotCenteredForFcsRef(FcsError):

    """
    Exception when the rotator is not centered on the
    flexure curve for a given slider.
    """

    def __init__(self, pa, slider):

        error_code = -507

        msg = "ERROR %d: DEIMOS PA of %6.1f not centered on flexure curve for slider %d. Please, use fcszero command to reset the DEIMOS PA and then re-take spot image. Aborting fcsref..." % (error_code, pa, slider)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnInvalidGratingName(FcsError):

    """
    Exception when the grating name is not in
    the list of allowed grating names.
    """

    def __init__(self, grname):

        error_code = -508

        msg = "ERROR %d: Grating name %s is not valid for FCS." \
              % (error_code, grname)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)


class AbortOnInvalidSliderPosition(FcsError):

    """
    Exception when the slider position is not in the
    list of allowed slider positions.
    """

    def __init__(self, pos):

        error_code = -509

        msg = "ERROR %d: Slider postion number %d is not valid for FCS." \
              % (error_code, pos)

        error_message = msg

        fcs_auxiliary.fcsState.abort(error_code, error_message)

