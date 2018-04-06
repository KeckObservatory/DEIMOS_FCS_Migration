#!/usr/local/ucolick/tcl831/bin/wishx
#+
# fcsfix -- interactively match FCS spot position to reference image
#
# Purpose:
#	Coordinate the process of recovering from an FCS fault by
#	displaying the FCS reference image and the current image
#	and leading the user through the process of marking the 
#	same feature in the two images.
#
# Usage:
#	fcsfix [-debug]
# 
# Flags:
#	-debug = run in DEBUG mode
# 
# Arguments:
#	None
#
# Output:
#	ds9 window to current display
# 
# Restrictions:
#	FCSIMGFI keyword must be defined
# 
# Exit values:
#	 0 = normal completion
#	 1 = wrong number of arguments
#
# Example:
#-
# Modification history:
#	2013-Dec-07	GDW	Original version
#	2013-Dec-24	GDW	Reorganized to make operation more clear
#-----------------------------------------------------------------------

proc myMessage { message {type error}} {
    set bigtype [string toupper $type]
    updateStatus "$bigtype: $message"
    tk_messageBox -message "$message" -icon $type -type ok
}

proc setCursor { {type {} } } {
    . configure -cursor $type
    update idletasks
}

# return 1 if ds9 is running on this display...
proc ds9Running { } {

    if {[catch {send ds9 ""}] == 0 } { 
	return 1
    } else {
	return 0
    }
}

proc myExec { command } {
    global debug
    updateStatus "Executing command $command" 1

    if { $debug } {
	echo "DEBUG: $command"
    } else {
	eval exec $command
    }
}

proc waitForFcsTracking { {maxiter 5} } {
    set niter 0
    while { 1 } {

	# quit if too many iterations...
	incr niter
	if { $niter > $maxiter } {
	    updateStatus "Failed to track within $maxiter iterations!  Please click Unstick Grating"
	    return 1
	}

	# wait for next FCS image...
	updateStatus "Waiting for next FCS image..."
	set command "wfifcs"
	myExec $command

	# get fcs status...
	set fcssta [exec show -s deifcs -terse fcssta]
	if { [string equal $fcssta "Tracking"] } {
	    updateStatus "FCS is now tracking."
	    return 0
	} else {
	    updateStatus "FCS is NOT tracking yet (interation $niter of $maxiter)."
	}
    }
}

proc abort { {message "ABORT!"} {status 1} } {
    puts stderr "\a\[[info script]\] $message"
    exit $status
}

# generate a timestamp...
proc timeStamp { } {
    return [clock format [clock seconds] -format "%Y-%m-%dT%T"]
}

proc updateStatus { message {noscreen 0} } {
    global statusText logunit

    # always log to file...
    set now [timeStamp]
    puts stderr "\[$now\] $message"
    puts $logunit "\[$now\] $message"
    flush $logunit

    # optional log to screen..
    if { $noscreen == 0 } {
	set statusText $message
	update idletasks
    }
}

#----------------------------------------
# confirm integers
#----------------------------------------
proc rangeCheck { x name } {

    set minval 0
    set maxval 2500

    if {[catch {expr int($x)} y]} {
	error "$name must be an integer value"
    }

    if { $y < $minval || $y > $maxval } {
	error "$name must be in the range $minval < $name < $maxval"
    }
    
    return $y    
}

#----------------------------------------
# set initial state
#----------------------------------------
proc initializeGui { } {
    global debug

    set line "----------------------------------------"
    updateStatus $line 1
    updateStatus Startup 1
    if { $debug } {
	updateStatus "DEBUG mode enabled" 1
    }
    updateStatus "Click 'Step 1' button to read and analyze latest FCS image"
}

#----------------------------------------
# launch unstick grating
#----------------------------------------
proc unstick { } {

    # change cursor...
    setCursor watch

    # save current wavelength...
    set wavelenOrig [exec wavelen]
    updateStatus "Original wavelength is $wavelenOrig"

    # turn off FCS...
    updateStatus "Turning FCS OFF"
    set command "modify -s deifcs fcsmode=Off"
    myExec $command

    # turn off FCS...
    updateStatus "Waiting for FCS to go passive..."
    set command "waitfor -s deifcs fcssta=Passive"
    myExec $command

    # unstick grating...
    updateStatus "Running unstick grating procedure.  Please wait 3 minutes."
    set command "unstick_grating"
    myExec $command

    # return to original wavelength...
    updateStatus "Setting wavelength back to $wavelenOrig"
    set command "wavelen $wavelenOrig"
    myExec $command

    # verify wavelength...
    set wavelenFinal [exec wavelen]
    updateStatus "Wavelength is now $wavelenFinal"
    if { $wavelenFinal == $wavelenOrig } {
	updateStatus "Successfully restored original wavelength."
    } else {
	myMessage "failed to restore original wavelength!  Please try running 'Unstick Grating' again"
	setCursor
	return
    }

    # turn on FCS...
    updateStatus "Turning FCS ON..."
    set command "modify -s deifcs fcsmode=Track"
    myExec $command

    # wait for tracking...
    updateStatus "Waiting for FCS to track..."
    if { [waitForFcsTracking] == 0 } {
	myMessage "SUCCESS! FCS is tracking; please proceed with observing." info"
    } else {
	myMessage "FCS is NOT tracking; please contact Support Astronomer!"
    }

    setCursor
    return
}

#----------------------------------------
# display the current and reference FCS images in ds9...
#----------------------------------------
proc displayFcsImages { } {

    global fcsref fcslast niter moveButton
    global x1 x2 y1 y2

    # increment counter...
    incr niter
    updateStatus "Entered displayFcsImags with niter=$niter" 1

    # change cursor...
    setCursor watch

    # clear moves...
    set x1 0
    set x2 0
    set y1 0
    set y2 0
    update idletasks

    # get reference image name...
    set fcsref [exec show -s deifcs -terse fcsimgfi]
    
    # check for blank name...
    if { [string equal $fcsref ""]} {
	myMessage "FCS reference image is undefined!  Enable FCS tracking and re-try."
	setCursor
	return
    }
    
    # check for non-existent image...
    if { [file exists $fcsref] == 0 } {
	myMessage "FCS reference file $fcsref not found."
	setCursor
	return
    }
    
    # launch ds9 window...
    if { [ds9Running] } { 
	send ds9 "set ds9(next) Frame1\; GotoFrame"
    } else {
	updateStatus "Launching ds9 window"
	set cmd {ds9 -geometry 1280x512 -scale mode zscale -zoom 8 -view image &}
	myExec $cmd
    }
    
    # display image...
    set ntries 0
    set maxtries 5
    set keepgoing 1
    while { 1 } {
	
	# check for okay...
	if { [ds9Running] } { 
	    updateStatus "ds9 now ready"
	    break 
	}
	
	# check for max tries exceeded...
	if { $ntries > $maxtries } {
	    myMessage "ds9 is not talking to me!  Please kill ds9 and click 'Step 1' again."
	    setCursor
	    return
	}
	
	# increment, wait, try again...
	updateStatus "waiting for ds9 ($ntries)..."
	incr ntries
	after 1000
    }
    
    # load reference file...
    updateStatus "displaying reference frame $fcsref"
    send ds9 "LoadFits $fcsref"
    send ds9 "FinishLoad"
    
    # locate last frame...
    set fcslast [exec lastfcsimage]
    updateStatus "displaying latest frame $fcslast"
    
    # check for non-existent image...
    if { [file exists $fcslast] == 0 } {
	myMessage "current FCS file $fcslast not found."
	setCursor
	return
    }
    
    # load last frame...
    if { $niter == 1 } {
	send ds9 "CreateFrame"
    } else {
	send ds9 "set ds9(next) Frame2\; GotoFrame"
    }
    send ds9 "LoadFits $fcslast"
    
    # complete loading process...
    send ds9 "FinishLoad"
    
    # put the display into the proper mode...
    send ds9 "set ds9(display,user) tile"
    send ds9 "set tile(mode) row"
    send ds9 "DisplayMode"

    # enable move...
    $moveButton configure -state normal

    # update status...
    updateStatus "Enter X/Y coords of a spot appearing on both images and click 'Step 3' button"

    # restore cursor...
    setCursor
}


#----------------------------------------
# move the optics and check FCS status
#----------------------------------------
proc sendMoves { } {

    global x1 x2 y1 y2 moveButton

    # change cursor...
    setCursor watch

    # rangecheck coords...
    set ix1 [rangeCheck $x1 x1]
    set ix2 [rangeCheck $x2 x2]
    set iy1 [rangeCheck $y1 y1]
    set iy2 [rangeCheck $y2 y2]

    # turn off FCS...
    updateStatus "Turning FCS OFF"
    set command "modify -s deifcs fcsmode=Off"
    myExec $command

    # turn off FCS...
    updateStatus "Waiting for FCS to go passive..."
    set command "waitfor -s deifcs fcssta=Passive"
    myExec $command

    # execute the move...
    updateStatus "Sending FCS moves..."
    set command "fcsmov $ix2 $iy2 $ix1 $iy1"
    myExec $command

    # turn on FCS...
    updateStatus "Turning FCS ON..."
    set command "modify -s deifcs fcsmode=Track"
    myExec $command

    # wait for tracking...
    updateStatus "Waiting for FCS to track..."
    if { [waitForFcsTracking] == 0 } {
	myMessage "SUCCESS! FCS is tracking; please proceed with observing." info
    } else {
	myMessage "FCS is NOT tracking; please click 'Unstick Grating' button."
    }

    # turn OFF the move button...
    $moveButton configure -state disabled

    # restore cursor...
    setCursor
}

#----------------------------------------
# move the optics and check FCS status
#----------------------------------------
proc quitGui { } {

    # check for okay...
    if { [ds9Running] } { 

	# need to wrap this in a catch, else will crash tcl...
	updateStatus "Terminating ds9"
	catch {send ds9 "exit"}

    }

    updateStatus "Normal exit"
    exit
}

#------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------

global x1 x2 y1 y2 fcsref fcslast niter statusText moveButton debug logunit

# set counter...
set debug 0
set niter 0
set logfile fcsfix.log
set logunit [open $logfile "a"]

# truncate last element from arg list (appears to be a bug in wishx)...
set n [expr [llength $argv] - 1]
set argv [lreplace $argv $n $n]

# parse command-line args...
foreach arg $argv {
    switch -glob -- $arg {
	-D* {set debug 1}
    }
}

# verify DISPLAY...
if { [info exists env(DISPLAY)] == 0 } { 
    abort "ERROR: DISPLAY is not defined -- abort!"
}

# refuse to mess up the existing ds9 window...
if {[catch {send ds9 ""}] == 0 } { 
    set msg "ERROR: operation would affect existing ds9 window!\nPlease run this command on another display."
    abort $msg
}

# define GUI name...
set gui_name "DEIMOS FCS Fix Tool"

# set up GUI...
wm title . $gui_name

set bgcolor [. cget -background]
set active_color grey
. configure -borderwidth 5 -background $bgcolor

#----------------------------------------
# frame for primary method...
#----------------------------------------
set primary [frame .primary -borderwidth 1 -relief solid -background $bgcolor]
label $primary.toplabel -text "Primary Recovery Method: Try this first" -background $bgcolor
grid $primary.toplabel -row 1 -column 1 -padx 5 -pady 5

#----------------------------------------
# frame for image names...
#----------------------------------------
set f [frame $primary.images -background $bgcolor]
grid $f -row 2 -column 1 -padx 5 -pady 5
label $f.reflabel -text "Reference FCS image:" -background $bgcolor
entry $f.reffile -width 50 -textvariable fcsref -justify left \
    -background $bgcolor
label $f.curlabel -text "Current FCS image:" -background $bgcolor
entry $f.curfile -width 50 -textvariable fcslast -justify left \
    -background $bgcolor

button $f.display -width 10 -text "Step 1: Grab FCS images" \
    -command displayFcsImages \
    -background $bgcolor  -activebackground $active_color

set row 0
incr row
grid $f.display  -row $row -column 1 -columnspan 2 -padx 5 -pady 5 -sticky news
incr row
grid $f.reflabel -row $row -column 1 -padx 5 -pady 5 -sticky nes
grid $f.reffile  -row $row -column 2 -padx 5 -pady 5 -sticky news
incr row
grid $f.curlabel -row $row -column 1 -padx 5 -pady 5 -sticky nes
grid $f.curfile  -row $row -column 2 -padx 5 -pady 5 -sticky news

#----------------------------------------
# frame for coordinates...
#----------------------------------------
set f [frame $primary.coords -background $bgcolor]
grid $f -row 3 -column 1 -padx 5 -pady 5
label $f.instructions1 -text "Step 2: Enter feature coordinates" -background $bgcolor -justify center
label $f.instructions2 -text "Locate a feature common to both FCS images and enter coordinates below." -background $bgcolor -justify center

label $f.toplabel -text "Coordinates from top image -->" -background $bgcolor -justify right
label $f.botlabel -text "Coordinates from bottom image -->" -background $bgcolor -justify right
label $f.xtoplabel -text "X:" -background $bgcolor
label $f.ytoplabel -text "Y:" -background $bgcolor
label $f.xbotlabel -text "X:" -background $bgcolor
label $f.ybotlabel -text "Y:" -background $bgcolor
entry $f.xtopcoord -width 4 -textvariable x1 -justify right \
    -background $bgcolor 
entry $f.ytopcoord -width 4 -textvariable y1 -justify right \
    -background $bgcolor
entry $f.xbotcoord -width 4 -textvariable x2 -justify right \
    -background $bgcolor
entry $f.ybotcoord -width 4 -textvariable y2 -justify right \
    -background $bgcolor

set row 1
grid $f.instructions1 -row $row -column 1 -padx 5 -pady 0 -sticky news -columnspan 5
incr row
grid $f.instructions2 -row $row -column 1 -padx 5 -pady 0 -sticky news -columnspan 5

incr row
grid $f.toplabel  -row $row -column 1 -padx 5 -pady 5 -sticky nes
grid $f.xtoplabel -row $row -column 2 -padx 5 -pady 5 -sticky nes
grid $f.xtopcoord -row $row -column 3 -padx 5 -pady 5 -sticky news
grid $f.ytoplabel -row $row -column 4 -padx 5 -pady 5 -sticky nes
grid $f.ytopcoord -row $row -column 5 -padx 5 -pady 5 -sticky nes

incr row 
grid $f.botlabel  -row $row -column 1 -padx 5 -pady 5 -sticky nes
grid $f.xbotlabel -row $row -column 2 -padx 5 -pady 5 -sticky nes
grid $f.xbotcoord -row $row -column 3 -padx 5 -pady 5 -sticky news
grid $f.ybotlabel -row $row -column 4 -padx 5 -pady 5 -sticky nes
grid $f.ybotcoord -row $row -column 5 -padx 5 -pady 5 -sticky nes

set moveButton [button $f.move -width 10 -text "Step 3: Send FCS moves" -command sendMoves \
		    -background $bgcolor  -activebackground $active_color \
		    -stat disabled]
incr row
grid $f.move -row $row -column 1 -padx 5 -pady 5 -sticky news -columnspan 5

#----------------------------------------
# frame for secondary method...
#----------------------------------------
set secondary [frame .secondary -borderwidth 1 -relief solid -background $bgcolor]
label $secondary.toplabel -text "Secondary Recovery Method: Try this if the primary method fails" -background $bgcolor
grid $secondary.toplabel -row 1 -column 1 -padx 5 -pady 5

set w 20
button $secondary.unstick  -width $w  \
    -text "Unstick Grating" -command unstick \
    -background $bgcolor -activebackground $active_color
grid $secondary.unstick -row 2 -column 1 -padx 5 -pady 5

#----------------------------------------
# frame for status
#----------------------------------------
set f [frame .status -background $bgcolor]
label $f.label  -text "Status:" -background $bgcolor
entry $f.text -width 65 -textvariable statusText -justify left \
    -background $bgcolor
grid $f.label  -row 1 -column 1 -padx 5 -pady 5 -sticky news
grid $f.text -row 1 -column 2 -padx 5 -pady 5 -sticky news

#----------------------------------------
# control frame...
#----------------------------------------
set f [frame .control -background $bgcolor]
set w 20
button $f.quit   -width $w -text "Quit"  -command quitGui \
    -background $bgcolor -activebackground $active_color
grid $f.quit -sticky news -padx 5 -pady 5

#----------------------------------------
# final assembly...
#----------------------------------------
set row 1
grid .status    -row [incr row] -column 1 -padx 5 -pady 5 -sticky news
grid .primary   -row [incr row] -column 1 -padx 5 -pady 5 -sticky news
grid .secondary -row [incr row] -column 1 -padx 5 -pady 5 -sticky news
grid .control   -row [incr row] -column 1 -padx 5 -pady 5 -sticky news

initializeGui
