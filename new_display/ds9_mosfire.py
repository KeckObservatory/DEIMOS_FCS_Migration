#!/bin/env python2.4

import numpy
import os
import pyfits
import shlex
import subprocess
import time
import logging as lg

class ds9:
	title = None
	'''
	The ds9 class provides wrappers around the unix commands xpaget
	and xpaset. The class is smart enough to automatically detect
	a running ds9 and attach automatically displayed images to it
	'''
	def __init__(self, title):
		''' ds9 construction init checks to see if a ds9 called title
		is currently running. If not, a new ds9 instance is created with
		that title'''
		self.title = title
               
                ''' Parameter specifying the output directory
                    2012-oct-30: MK - added to retrieve and use the outdir
                                      by default for loading files
                '''
		poutdir = subprocess.Popen(["outdir"],stdout=subprocess.PIPE)
                outdir = poutdir.communicate()[0]

		cmd = shlex.split("/usr/local/bin/xpaget %s" % self.title)

		devnull = open( '/dev/null', 'w')
		retcode = subprocess.call( cmd, stdout=devnull, 
					   stderr=devnull)
		if retcode == 1:

			''' Lines below are older than 2012 Oct - MK
			subprocess.Popen(["ds9", "-title", self.title])
			subprocess.Popen(["ds9", "-title", self.title , "-preserve", "pan", "yes"])
			'''
			''' 
			2012-oct-30: MK - added to retrieve and use the outdir
                                      by default for loading files
                                      also added the preserve pan and zoom options
			'''
			subprocess.Popen(["ds9", "-title", self.title , "-preserve", "pan", "yes","-cd", "/s/sdata1300/mosfire9"])        

                        
			time.sleep(5)
                        

	def xpaget(self, cmd):
		'''xpaget is a convenience function around unix xpaget'''
		cmd = shlex.split("/usr/local/bin/xpaget %s %s" % (self.title, cmd))
		retcode = subprocess.call(cmd)

	def xpapipe(self, cmd, pipein):
		''' xpapipe is a convenience wrapper around echo pipein | xpaset ...'''
		
		cmd = shlex.split('/usr/local/bin/xpaset %s %s' % (self.title, cmd))
		p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		p.stdin.write(pipein)
		p.stdin.flush()
		print p.communicate()


	def xpaset(self, cmd):
		'''xpaget is a convenience function around unix xpaset'''
		xpacmd = "/usr/local/bin/xpaset -p %s %s" % (self.title, cmd)
		lg.debug(xpacmd)

		cmd = shlex.split(xpacmd)

		retcode = subprocess.call(cmd)
		lg.debug("retcode = %s" % retcode) 


	def frameno(self, frame):
		'''frameno sets the ds9 frame number to [frame]'''
		self.xpaset("frame %i" %frame)

	def open(self, fname, frame):
		'''open opens a fits file [fname] into frame [frame]'''
		self.frameno(frame)
		self.xpaset("file %s" % fname)

