import datetime
import os
import warnings

from astropy.io import ascii
from astropy.time import time
import requests
import sys

def main():
    '''
    From a list of CMBs, query ssois and get relavent images
    '''
    
    parser = argparse.ArgumentParser(
        description='Run SSOIS on a given set of minor planets and return the available images in a particular filter.')

    parser.add_argument("--filter", "-f",
                        action="store",
                        default='r',
                        dest="filter",
                        choices=['r', 'u'],
                        help="passband: default is r'")
    parser.add_argument("--ossin",
                        action="store",
                        default="vos:OSSOS/dbaseclone/ast/",
                        help='vospace dbaseclone containerNode')
    parser.add_argument("--dbimages",
                        action="store",
                        default="vos:OSSOS/dbimages",
                        help='vospace dbimages containerNode')
    parser.add_argument('--type',
                        default='p',
                        choices=['o', 'p', 's'],
                        help="restrict type of image (unprocessed, reduced, calibrated)")
    parser.add_argument("--output", "-o",
                        action="store",
                        default="/Users/admin/Desktop/band.txt",   
                        help='Location and name of output file containing image IDs.')

    args = parser.parse_args()
    
    if args.filter.lower().__contains__('r'):
        args.filter = 'r.MP9601'  # this is the old (standard) r filter for MegaCam
    if args.filter.lower().__contains__('u'):
        args.filter = 'u.MP9301'
        
        
    # Define columns of data
    with open(args.output, 'w') as outfile:
        outfile.write("{:>10s} {:>10s} {:>2s} {:>5s} {:>5s} {:>16s} {:>16s} {:>16s} {:>12s}\n".format(
            "Object", "Image", "Ext", "X", "Y", "RA", "DEC", "time", "filter"))
            
    for cmbobject in mbc.txt:
#########################

def Query(object)
    '''
    Query the MPC's Solar System Object search for a given list of CMB's
    Inputs - a list of main belt comets
    Optional - a tuple of the start and end times to be searched between. Format '%Y-%m-%d'
    Otherwise the temporal range defaults to spanning from the start
    of OSSOS surveying on 2013-01-01 to the present day.
    '''
    
    search_start_date=Time('2013-01-01', scale='utc')
    search_end_date=Time('2017-01-01', scale='utc'))
    
#########################

def parse_MPC(object)
    