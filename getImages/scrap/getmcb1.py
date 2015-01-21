import datetime
import os
import warnings

from astropy.io import ascii
from astropy.time import Time
import requests
import sys
import argparse

import requests


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
    
    for mbc in storage.listdir(args.listin):
        image, obs_in_filter = parse_kbo(args.listin + mbc, args.filter)
        if len(obs_in_filter) > 0:
            with open(args.output, 'a') as outfile:
                for line in obs_in_filter:
                    outfile.write("{:>10s} {:>10s}\n".format(image.name, line['Image'], line['Filter']))
                outfile.write('\n')
        

def parse_kbo(mbc_file, camera_filter, search_start_date=Time('2013-01-01', scale='utc'), search_end_date=Time('2017-01-01', scale='utc')):
    # read input file
    with open(mbc_file) as infile: 
        filestr = infile.read()
    input_mbc_lines = filestr.split('\n') # array of MBCs to query

    #headers = {'User-Agent': 'OSSOS Target Track'}
    
    # testing with only one object
    payload = {'name': '176P'}
    response = request.get(SSOS_URL, data=payload, search_start_date=search_start_date, search_end_date=search_end_date)
    
    # dont need because this builds a dictionary
    # query = Query(input_mbc_lines, search_start_date=search_start_date, search_end_date=search_end_date))
    
    obs_in_filter = parse_ssois_return(queryget(response), camera_filter=camera_filter)
    
    return obs_in_filter
    
# from ossos ssos.py

def queryget(mbc):
    """
    :return: astropy.table.table
    :raise: AssertionError
    """
    
    # ssois URL: http://www3.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/ssois/#arc
    # SSOS_URL = "http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/cadcbin/ssos/ssos.pl"
    SSOS_URL = "http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/cadcbin/ssos/ssosclf.pl"
    
    params = {'name': '176P'}
    logger.debug("{}\n".format(params))
    self.response = requests.post(SSOS_URL, data=params)
    logger.info(self.response.url)
    
    assert isinstance(self.response, requests.Response)

    assert (self.response.status_code == requests.codes.ok )

    lines = self.response.content
    # note: spelling 'occured' is in SSOIS
    if len(lines) < 2 or "An error occured getting the ephemeris" in lines:
        raise IOError(os.errno.EACCES,
                      "call to SSOIS failed on format error")

    if os.access("backdoor.tsv", os.R_OK):
        lines += open("backdoor.tsv").read()

    return lines

def parse_ssois_return(ssois_return, camera_filter='r.MP9601', telescope_instrument='CFHT/MegaCam'):
    assert camera_filter in ['r.MP9601', 'u.MP9301']
    ret_table = []

    table_reader = ascii.get_reader(Reader=ascii.Basic)
    table_reader.inconsistent_handler = _skip_missing_data
    table_reader.header.splitter.delimiter = '\t'
    table_reader.data.splitter.delimiter = '\t'
    table = table_reader.read(ssois_return)

    for row in table:
        # check if a dbimages object exists
        ccd = int(row['Ext']) - 1
        expnum = row['Image'].rstrip('p')

        # Excludes the OSSOS wallpaper.
        # note: 'Telescope_Insturment' is a typo in SSOIS's return format
        if (row['Telescope_Insturment'] == telescope_instrument) and (row['Filter'] == camera_filter) \
                and not row['Image_target'].startswith('WP'):
            ret_table.append(row)

    return ret_table


def _skip_missing_data(str_vals, ncols):
    """
    add a extra column if one is missing, else return None.
    """
    if len(str_vals) == ncols - 1:
        str_vals.append('None')
        return str_vals
    else:
        raise ValueError("not enough columns in table")
        