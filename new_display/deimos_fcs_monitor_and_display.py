#! /kroot/rel/default/bin/kpython3

description = """
Name: 
	deimos_fcs_monitor_and_display

Purpose:
	Monitor the current FCS data directory for the last DEIMOS FCS image 
        and dis[play it in the DS9 client.

Syntax:
	deimos_fcs_monitor_and_display

"""
epilog = """
Modification history:

       2018-Jul-13      CAAI     Original version based on the script
                                 script mosfireMonitorAndDisplay.py 
                                 by NPK.
"""

#-----------------------#
# Import Python modules #
#-----------------------#

import sys, os
import ktl
import logging as lg
import inspect
import shlex
import subprocess as sp
import datetime as dt
import time as tm
from time import strftime
import argparse as arps
from argparse import RawTextHelpFormatter
import ds9_fcs


#-----------------------#
# Parse input arguments #
#-----------------------#

parser = arps.ArgumentParser(description=description, epilog=epilog, formatter_class=RawTextHelpFormatter, add_help=True)
parser.add_argument('-t', '--title', help='Title of the ds9 display to connect to. Default is deimos_fcs_autodisplay', default=False)
parser.add_argument('-d', '--debug', help='If set, then debug mode on.', action='store_true')
args = parser.parse_args()

if args.title:
   DS9_TITLE = args.title
else:
   DS9_TITLE = 'deimos_fcs_autodisplay'

if args.debug:
   DEBUG_MODE = True
   print('Debugging mode on')
else:
   DEBUG_MODE = False
   print('Debugging mode off')

#------------------#
# Define constants #
#------------------#

ZOOM_INI = 'fit'
SCALE_MODE_INI = 'zscale'
REGIONS_SHAPE_INI = 'box'
PRESERVE_PAN_INI = 'yes'
PRESERVE_REGIONS_INI = 'yes'
SLEEP_TIME = 5

#-------------------#
# configure logging #
#-------------------#

# extract the program name (minus extension) from argv[0]
head, tail = os.path.split(sys.argv[0])
prog_name, ext = os.path.splitext(tail)

logfile = os.environ['HOME'] + '/' + prog_name + '.log'
lg.basicConfig( filename=logfile, \
                level=lg.DEBUG, \
                format='%(asctime)s %(process)6d %(levelname)-8s %(filename)s %(lineno)d: %(message)s', \
                datefmt='%Y-%m-%dT%H:%M:%S')

# define a Handler which writes INFO messages or higher to the sys.stderr
console = lg.StreamHandler()
console.setLevel(lg.INFO)

# set a format which is simpler for console use
formatter = lg.Formatter('%(asctime)s %(levelname)s %(filename)s %(lineno)d: %(message)s')

# tell the handler to use this format
console.setFormatter(formatter)

# add the handler to the root logger
lg.getLogger('').addHandler(console)
lg.info( '---------- Starting up ----------')

#--------------------#
# Cache KTL keywords #
#--------------------#

outdir = ktl.cache('deifcs', 'OUTDIR')
outfile = ktl.cache('deifcs', 'OUTFILE')
frameno = ktl.cache('deifcs', 'FRAMENO')

#------------------#
# Define functions #
#------------------#

def path_to_file():
   """
   Return the full disk name of the last file written
   """
   
   try:

      file_path = str( '/s%s/%s%04d.fits' % (outdir.read(), outfile.read(), int(frameno.read())-1) )
      if ( os.path.exists(file_path) == True ):
         current_file = file_path
      else: 
         lg.info("DEIMOS FCS file %s is not available yet." % file_path)
         current_file = None

   except:           

      lg.error("deifcs keyword service is unreachable.")
      current_file = None

   return current_file


def wait_for_image(ds9_disp, last_file):
   """
   Iterate until the current frame changes, then return.
   The name of the new file will be stored in params["current_file"].
   """

   lg.info("State %s" % (inspect.stack()[0][3]))

   # loop until change in new image name...
   
   current_zoom = ds9_disp.xpaget('zoom')
   current_scale_mode = ds9_disp.xpaget('scale mode')
   current_regions_shape = ds9_disp.xpaget('regions shape')
   current_file = path_to_file()

   while ( current_file == last_file ):	
      lg.debug("Waiting for new image")
      current_zoom = ds9_disp.xpaget('zoom')
      current_scale_mode = ds9_disp.xpaget('scale mode')
      current_regions_shape = ds9_disp.xpaget('regions shape')
      current_file = path_to_file()

      if ( DEBUG_MODE == True ):
         print('')
         print(str(dt.datetime.now()))
         print('Waiting for new image...')
         print('current_zoom = ', current_zoom)
         print('current_scale_mode = ', current_scale_mode)
         print('current_regions_shape = ', current_regions_shape)
         print('current_file = ', current_file)
      
      tm.sleep(SLEEP_TIME)

   # get the lastfile..
   lg.info("New image %s has arrived" % current_file)

   if ( DEBUG_MODE == True ):
      print('')
      print(str(dt.datetime.now()))
      print('New image %s has arrived.')
      print('current_zoom = ', current_zoom)
      print('current_scale_mode = ', current_scale_mode)
      print('current_regions_shape = ', current_regions_shape)
      print('current_file = ', current_file)

   return current_zoom, current_scale_mode, current_regions_shape, current_file


def display_current_file(ds9_disp, zoom, scale_mode, regions_shape, filename):
   """ 
   Ask ds9 to display current file. 
   """

   lg.info("State %s" % (inspect.stack()[0][3]))

   if ( filename is None ):
      got_a_file = 0
   else:
      ds9_disp.open(filename, 1)
      ds9_disp.xpaset('zoom to ' + zoom)
      ds9_disp.xpaset('scale mode ' + scale_mode)
      ds9_disp.xpaset('regions shape ' + regions_shape)
      got_a_file = 1
      tm.sleep(SLEEP_TIME)

   return got_a_file


def startup():
   """
   Initialize DS9 display frame.
   """

   lg.info("State %s" % (inspect.stack()[0][3]))
   
   ds9_disp = ds9_fcs.ds9(DS9_TITLE)

   ds9_disp.xpaset('preserve pan ' + PRESERVE_PAN_INI)
   ds9_disp.xpaset('preserve regions ' + PRESERVE_REGIONS_INI)

   current_file = path_to_file()

   return ds9_disp, current_file


#-----------#
# Main Loop #
#-----------#

ds9_display, initial_file = startup()
file_exists = display_current_file(ds9_display, ZOOM_INI, SCALE_MODE_INI, REGIONS_SHAPE_INI, initial_file)

while True:

   # Loop for next image
   
   last_file = path_to_file()
   zoom, scale_mode, regions_shape, filename = wait_for_image(ds9_display, last_file)

   # Display current file 
   got_a_file = display_current_file(ds9_display, zoom, scale_mode, regions_shape, filename)
