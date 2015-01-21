import datetime
import os
import warnings

from astropy.io import ascii
from astropy.time import Time
import requests
import sys
import argparse

import requests
    
    
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
parser.add_argument("--listin",
                        action="store",
                        default="mbc.txt",
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

with open(args.output, 'w') as outfile:
    outfile.write("{:>10s} {:>10s} {:>12s}\n".format("Object", "Image", "filter"))
    
search_start_date=Time('2013-01-01', scale='utc')
search_end_date=Time('2017-01-01', scale='utc')

with open(mbc_file) as infile: 
    filestr = infile.read()
input_mbc_lines = filestr.split('\n') # array of MBCs to query

SSOS_URL = "http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/cadcbin/ssos/ssosclf.pl"
payload = {'name': '176P'}
response = request.get(SSOS_URL, data=payload, search_start_date=search_start_date, search_end_date=search_end_date)

#    obs_in_filter = parse_ssois_return(queryget(response), camera_filter=camera_filter)
response2 = requests.post(SSOS_URL, data=params)
lines = response2.content

if len(lines) < 2 or "An error occured getting the ephemeris" in lines:
    raise IOError(os.errno.EACCES, "call to SSOIS failed on format error")

if os.access("backdoor.tsv", os.R_OK):
    lines += open("backdoor.tsv").read()
        
# parse_ssois_return
ret_table = []

table_reader = ascii.get_reader(Reader=ascii.Basic)
table_reader.inconsistent_handler = _skip_missing_data
table_reader.header.splitter.delimiter = '\t'
table_reader.data.splitter.delimiter = '\t'
table = table_reader.read(ssois_return)














"""
for mbc in storage.listdir(args.listin):
    image, obs_in_filter = parse_kbo(args.listin + mbc, args.filter)
    if len(obs_in_filter) > 0:
        with open(args.output, 'a') as outfile:
            for line in obs_in_filter:
                outfile.write("{:>10s} {:>10s}\n".format(image.name, line['Image'], line['Filter']))
            outfile.write('\n')
"""