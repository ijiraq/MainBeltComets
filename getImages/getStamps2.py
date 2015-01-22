

# INPUT LIST OF IMAGES IN COMMAND LINE
"""Retrieval of cutouts of the FITS images associated with the OSSOS detections.
Takes a directory of .ast file (in dbase format) as input

An Example URL for cutouts
http://www.canfar.phys.uvic.ca/vospace/auth/synctrans?TARGET=vos://cadc.nrc.ca~
vospace/OSSOS/dbimages/1625356/1625356p.fits&DIRECTION=pullFromVoSpace&PROTOCOL=
ivo://ivoa.net/vospace/core%23httpget&view=cutout&cutout=CIRCLE+ICRS+242.1318+-1
2.4747+0.05
"""
	# PERMISSIONS DENIED, WHAT IS .AST FILE IN DBASE FORM?
	
import argparse
import logging
import getpass
import requests
import os

from ossos import mpc		# CONFIRM THAT THIS IS OK, OR NEED TO ADAPT
from ossos import storage	# CONFIRM THAT THIS IS OK, OR NEED TO ADAPT

BASEURL = "http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/vospace/auth/synctrans"

# PARSE INFORMATION INPUTTED FROM THE COMMAND LINE
	# VERSION - OSSOS DATA RELEASE VERSION THE STAMPS ARE TO BE ASSIGNED TO
	# INPUT FILE
	# BLOCKS - PREFIXES OF OBJECT DESIGNATIONS TO BE USED
	# RADIUS - SIZE OF CIRCULAR CUTOUT
	
# CADC PERMISSIONS

# PARSE THROUGH INPUT FILE FOR IMAGE INFORMATION
	# mpcREADER format? - initialize mpc_obervations attribute to hold observations
	# give provisional_name
	# If file exists: mpc_observations = read input file

# FOR IMAGES WITH PREFIX BLOCK
	# ASSIGN: storage.postage_stamps, agrs.version, provisional_name
		# storage.POSTAGE_STAMPS => POSTAGE_STAMPS = 'vos:OSSOS/postage_stamps'
		# this creates a new directory is OSSOS ??
	# MAKE A DIRECTORY FOR OUTPUT?
		 # FIND DIRECTORY OR MAKE ONE
	# CUT OUT IMAGE
		# PASS: object, directory, radius, CADC permissions
		
# CUT OUT (object, directory, radius, CADC permissions)
	# for each attribute in mpc_observations:
		# select calibrated images, CONFIRM
		# find coordinate.ra.degree, coordinate.dec.degree, radius
		# storage.get_image - Get a FITS file for this expnum/ccd  from VOSpace
		# OR: storage.vospace.fixURI and  (WHERE IS THIS?)
			# storage.get_uri (Build the uri for an OSSOS image stored in the dbimages containerNode)
		# define parameters for request: target, protocol, direction, cutout, view
		# request image : url, parameters, cadc permissions
		# assign to a file
		
		
		
		
		
		
		