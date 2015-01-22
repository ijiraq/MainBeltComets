"""Retrieval of cutouts of the FITS images associated with the OSSOS detections.
Takes a directory of .ast file (in dbase format) as input

An Example URL for cutouts from OSSOS (not CFHT/MegaCam)
http://www.canfar.phys.uvic.ca/vospace/auth/synctrans?TARGET=vos://cadc.nrc.ca~
vospace/OSSOS/dbimages/1625356/1625356p.fits&DIRECTION=pullFromVoSpace&PROTOCOL=
ivo://ivoa.net/vospace/core%23httpget&view=cutout&cutout=CIRCLE+ICRS+242.1318+-1
2.4747+0.05
"""

# in this case, the image is the exposure number

	
import argparse
import logging
import getpass
import requests
import os
import storage

import numpy as np
import pandas as pd
from astropy.table import Table, Column

BASEURL = "http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/vospace/auth/synctrans"


# CUT OUT (image, RA, DEC, radius, CADC permissions)
	# for each attribute in mpc_observations:
		# storage.vospace.fixURI and  (WHERE IS THIS?)
			# storage.get_uri (Build the uri for an OSSOS image stored in the dbimages containerNode)
		# define parameters for request: target, protocol, direction, cutout, view
		# request image : url, parameters, cadc permissions
		# assign to a file
		
def cutout(image, RA, DEC, radius, username, password):
    
        this_cutout = "CIRCLE ICRS {} {} {}".format(RA, DEC, radius)                                 
        print this_cutout

        target = storage.vospace.fixURI(storage.get_uri(image))
        direction = "pullFromVoSpace"
        protocol = "ivo://ivoa.net/vospace/core#httpget"
        view = "cutout"
        params = {"TARGET": target,
                  "PROTOCOL": protocol,
                  "DIRECTION": direction,
                  "cutout": this_cutout,
                  "view": view}
        r = requests.get(BASEURL, params=params, auth=(username, password))
        r.raise_for_status()  # confirm the connection worked as hoped
        postage_stamp_filename = "{}_{:11.5f}_{:09.5f}_{:+09.5f}.fits".format(obj.provisional_name,
                                                                              obs.date.mjd,
                                                                              obs.coordinate.ra.degree,
                                                                              obs.coordinate.dec.degree)
        with open(postage_stamp_filename, 'w') as tmp_file:
            tmp_file.write(r.content)
            storage.copy(postage_stamp_filename, obj_dir + "/" + postage_stamp_filename)
        os.unlink(postage_stamp_filename)  # easier not to have them hanging around	


# PARSE INFORMATION INPUTTED FROM THE COMMAND LINE
	# VERSION - OSSOS DATA RELEASE VERSION THE STAMPS ARE TO BE ASSIGNED TO
	# INPUT FILE
	# BLOCKS - PREFIXES OF OBJECT DESIGNATIONS TO BE USED
	# RADIUS - SIZE OF CIRCULAR CUTOUT
    
def main():
    
    # INPUT LIST OF IMAGES IN COMMAND LINE
    # IDENTIFY PARAMETERS FOR QUERY OF SSOIS FROM INPUT

    parser = argparse.ArgumentParser(
        description='Parse a directory of TNO .ast files and create links in the postage stamp directory '
                    'that allow retrieval of cutouts of the FITS images associated with the OSSOS detections. '
                    'Cutouts are defined on the WCS RA/DEC of the object position.')

    parser.add_argument("version",
                        help="The OSSOS data release version these stamps should be assigned to.")
    parser.add_argument("--ossin",
                        action="store",
                        default="lixImages.txt",
                        help="The vospace containerNode that clones ossin dbaseclone"
                             "holding the .ast files of astrometry/photometry measurements.")
    parser.add_argument("--radius", '-r',
                        action='store',
                        default=0.02,
                        help='Radius (degree) of circle of cutout postage stamp.')
    
    ''' Necessary for debugging, but not used in the code
    parser.add_argument("--debug", "-d",
                        action="store_true")
    parser.add_argument("--verbose", "-v",
                        action="store_true")
    '''
    
    args = parser.parse_args()
    
# PRINT HEADER

    print "-------------------- \n Cutting postage stamps of objects in input file %s from CFHT/MegaCam images \n--------------------" % args.infile	
# CADC PERMISSIONS
    username = raw_input("CADC username: ")
    password = getpass.getpass("CADC password: ")

# PARSE THROUGH INPUT FILE FOR IMAGE INFORMATION
    # format into lines, parse for image, RA and DEC
# CUT OUT IMAGE
	# PASS: object, directory, radius, CADC permissions                    

    with open(in_file) as infile: 
        for line in infile.readlines()[1:]:
            s = str(line)
            image = s[10:21].strip()    # string
            RA = s[33:54].strip()       # string, needs to be float ?
            DEC = s[54:75].strip()      # string, needs to be float ?
            cutout(image, RA, DEC, args.radius, username, password)
		
	
		
		
		
		
		