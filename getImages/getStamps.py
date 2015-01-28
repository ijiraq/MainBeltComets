"""Retrieval of cutouts of the FITS images associated with the CFHT/MegaCam detections.
Takes a table (getmbc.py output) as input

An Example URL for cutouts from OSSOS (not CFHT/MegaCam)
http://www.canfar.phys.uvic.ca/vospace/auth/synctrans?
TARGET=vos://cadc.nrc.ca~vospace/OSSOS/dbimages/1625356/1625356p.fits&
DIRECTION=pullFromVoSpace&
PROTOCOL=ivo://ivoa.net/vospace/core%23httpget&
view=cutout&
cutout=CIRCLE+ICRS+242.1318+-12.4747+0.05
"""
# in this case, the image is the exposure number

import argparse
import logging
import getpass
import requests
import os
import vos

import storage
import coding
import mpc
import util

import numpy as np
import pandas as pd
from astropy.table import Table, Column

BASEURL = "http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/vospace/auth/synctrans"
	
def cutout(objectname, image, RA, DEC, radius, username, password):

# CUT OUT (image, RA, DEC, radius, CADC permissions)
	# for each attribute in mpc_observations:
		# storage.vospace.fixURI and 
			# storage.get_uri (Build the uri for an OSSOS image stored in the dbimages containerNode)
		# define parameters for request: target, protocol, direction, cutout, view
		# request image : url, parameters, cadc permissions
		# assign to a file
    
    ''' Test for image known to work   
    image = '1667879p'
    RA = 21.1236333333
    DEC = 11.8697277778
    '''
    
    this_cutout = "CIRCLE ICRS {} {} {}".format(RA, DEC, radius)                                 
    print "cut out: ", this_cutout

    expnum = image.split('p')[0] # only want calibrated images    
    target = storage.vospace.fixURI(storage.get_uri(expnum)) 
    direction = "pullFromVoSpace"
    protocol = "ivo://ivoa.net/vospace/core#httpget"
    view = "cutout"
    params = {"TARGET": target,
                  "PROTOCOL": protocol,
                  "DIRECTION": direction,
                  "cutout": this_cutout,
                  "view": view}
    r = requests.get(BASEURL, params=params, auth=(username, password))
    if r.status_code == 403:
        print " Image cannot be cut out, response status = 403 "
    else:
        r.raise_for_status()  # confirm the connection worked as hoped
        postage_stamp_filename = "{}_{}_{:8f}_{:8f}.fits".format(objectname, image, RA, DEC)
        with open(postage_stamp_filename, 'w') as tmp_file:
            tmp_file.write(r.content)


def main():
    
# PARSE INFORMATION INPUTTED FROM THE COMMAND LINE
	# VERSION - OSSOS DATA RELEASE VERSION THE STAMPS ARE TO BE ASSIGNED TO
	# INPUT FILE
	# RADIUS - SIZE OF CIRCULAR CUTOUT
    
    # INPUT LIST OF IMAGES IN COMMAND LINE
    # IDENTIFY PARAMETERS FOR QUERY OF SSOIS FROM INPUT

    parser = argparse.ArgumentParser(
        description='Parse an obects.txt input file (getmbc.py output) and create links in the postage stamp directory '
                    'that allow retrieval of cutouts of the FITS images associated with the CHT/MegaCam detections. '
                    'Cutouts are defined on the WCS RA/DEC of the object position.')
    parser.add_argument("--ossin",
                        action="store",
                        default="lixImages.txt",
                        help="The input .txt files of astrometry/photometry measurements.")
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
    print "-------------------- \n Cutting postage stamps of objects in input file %s from CFHT/MegaCam images \n--------------------" % args.ossin	

    # CADC PERMISSIONS
    username = raw_input("CADC username: ")
    password = getpass.getpass("CADC password: ")

    # PARSE THROUGH INPUT FILE FOR IMAGE INFORMATION
        # format into lines, parse for image, RA and DEC
        # CUT OUT IMAGE
	        # PASS: object, directory, radius, CADC permissions                    
    
    with open(args.ossin) as infile: 
        for line in infile.readlines()[42:]: # testing for one image only
            assert len(line.split()) > 0
            objectname = line.split()[0]
            image = line.split()[1]
            RA = float(line.split()[3])   
            DEC = float(line.split()[4])
            cutout(objectname, image, RA, DEC, args.radius, username, password)
		
if __name__ == '__main__':
    main()	
		
		
		
		
		