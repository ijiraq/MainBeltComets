

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
    
def main():
    
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
###    parser.add_argument("--blocks", "-b",
                        action="store",
                        default=["o3e", "o3o"],
                        choices=["o3e", "o3o", "O13BL", "Col3N"],
                        help="Prefixes of object designations to include.")
    parser.add_argument("--radius", '-r',
                        action='store',
                        default=0.02,
                        help='Radius (degree) of circle of cutout postage stamp.')
    parser.add_argument("--debug", "-d",
                        action="store_true")
    parser.add_argument("--verbose", "-v",
                        action="store_true")

    args = parser.parse_args()
	
# CADC PERMISSIONS
    username = raw_input("CADC username: ")
    password = getpass.getpass("CADC password: ")

# PARSE THROUGH INPUT FILE FOR IMAGE INFORMATION
    # format into lines
	# mpcREADER format? - initialize mpc_obervations attribute to hold observations
	# give provisional_name
	# If file exists: mpc_observations = read input file
    
    in_file = args.infile
    with open(in_file) as infile: 
        filestr = str(infile.readlines())
    input_lines = filestr.split('\\n') # array of objects to query
    
    for fn in input_lines:
        obj = mpc.MPCReader(input_lines + fn)  # let MPCReader's logic determine the provisional name
            # Object    Image      Exp_time     RA   DEC    time    filter
        for block in args.blocks:
            if obj.provisional_name.startswith(block):
###                obj_dir = '{}/{}/{}'.format(storage.POSTAGE_STAMPS, args.version, obj.provisional_name)
                if not storage.exists(obj_dir, force=True):
                    storage.mkdir(obj_dir)
                
# FOR IMAGES WITH PREFIX BLOCK
	# ASSIGN: storage.postage_stamps, agrs.version, provisional_name
		# storage.POSTAGE_STAMPS => POSTAGE_STAMPS = 'vos:OSSOS/postage_stamps'
		# this creates a new directory is OSSOS ??
	# MAKE A DIRECTORY FOR OUTPUT?
		 # FIND DIRECTORY OR MAKE ONE
	# CUT OUT IMAGE
		# PASS: object, directory, radius, CADC permissions                
                
                cutout(obj, obj_dir, args.radius, username, password)
		
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
		
def cutout(obj, obj_dir, radius, username, password):
    for obs in obj.mpc_observations:  # FIXME: TESTING ONLY
        if obs.null_observation:
            continue
###        expnum = obs.comment.frame.split('p')[0] 
        this_cutout = "CIRCLE ICRS {} {} {}".format(obs.coordinate.ra.degree,
                                               obs.coordinate.dec.degree,
                                               radius)
        print this_cutout

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
        r.raise_for_status()  # confirm the connection worked as hoped
        postage_stamp_filename = "{}_{:11.5f}_{:09.5f}_{:+09.5f}.fits".format(obj.provisional_name,
                                                                              obs.date.mjd,
                                                                              obs.coordinate.ra.degree,
                                                                              obs.coordinate.dec.degree)
        with open(postage_stamp_filename, 'w') as tmp_file:
            tmp_file.write(r.content)
            storage.copy(postage_stamp_filename, obj_dir + "/" + postage_stamp_filename)
        os.unlink(postage_stamp_filename)  # easier not to have them hanging around		
		
		
		
		
		