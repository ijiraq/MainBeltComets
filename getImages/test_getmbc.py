import datetime
import os
import warnings
from astropy.io import ascii
from astropy.time import Time
import requests
import sys
import argparse
import requests

from ssos import Query

# could not figure out how to import, so just copied here
def parse_ssois_return(ssois_return, object_name, camera_filter='r.MP9601', telescope_instrument='CFHT/MegaCam'):
    assert camera_filter in ['r.MP9601', 'u.MP9301']
    ret_table = []
    good_table = 0
    bad_table = 0

    table_reader = ascii.get_reader(Reader=ascii.Basic)
    table_reader.inconsistent_handler = _skip_missing_data
    table_reader.header.splitter.delimiter = '\t'
    table_reader.data.splitter.delimiter = '\t'
    table = table_reader.read(ssois_return)

    for row in table:
        # check if a dbimages object exists
        mjd = row['MJD']

        # Excludes the OSSOS wallpaper.
        # note: 'Telescope_Insturment' is a typo in SSOIS's return format
        if (row['Telescope_Insturment'] == telescope_instrument) and (row['Filter'] == camera_filter) \
                and not row['Image_target'].startswith('WP'):
            if (int(row['Exptime']) == 287) or (int(row['Exptime']) == 387 ) or (int(row['Exptime']) == 500 ):
                good_table += 1
                ret_table.append(row)
            else:
                bad_table += 1
        if (row['Telescope_Insturment'] == telescope_instrument) and (row['Filter'] == camera_filter) \
            and not (int(row['Exptime']) > 286):
            bad_table += 1
            
    print "Searching for object %s " % object_name
    
    if (good_table > 0):
        print " %d usable images found" % good_table
    
    if (bad_table > 0):        
        print " %d unusable images found " % bad_table
    
    if (good_table == 0) and (bad_table == 0):
        print " no images found "

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
        # object U0233 does not have enough columns in table
    
def main():

    # IDENTIFY PARAMETERS FOR QUERY OF SSOIS FROM INPUT

    # From the given input, make list of MBCs to query
    
    parser = argparse.ArgumentParser(description='Run SSOIS and return the available images in a particular filter.')

    parser.add_argument("--filter", "-f",
                    action="store",
                    default='r',
                    dest="filter",
                    choices=['r', 'u'],
                    help="passband: default is r'")
    parser.add_argument("--ossin",
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
    
    mbc_file = args.ossin
    with open(mbc_file) as infile: 
        filestr = infile.read()
    input_mbc_lines = filestr.split('\n') # array of MBCs to query

    # CONFIRM that the input is the proper format to search for the appropriate ephemeris

    # FROM the given input, identify the desired filter and rename appropriately

    if args.filter.lower().__contains__('r'):
        args.filter = 'r.MP9601'  # this is the old (standard) r filter for MegaCam
    if args.filter.lower().__contains__('u'):
        args.filter = 'u.MP9301'

    # Define time period of image search, basically while MegaCam in operation

    search_start_date=Time('2013-01-01', scale='utc')   # epoch1=2013+01+01
    search_end_date=Time('2017-01-01', scale='utc')     # epoch2=2017+1+1
    
    # Setup output, label columns
    
    with open(args.output, 'w') as outfile:
        outfile.write("{:>10s} {:>10s} {:>10s} {:>16s} {:>16s} {:>16s} {:>12s}\n".format(
            "Object", "Image", "Exp_time", "RA", "DEC", "time", "filter"))

    # Query a specific ephemeris depending on object naming convention. CADC : search = bynameCADC , MPC : search = bynameMPC
    # Specify search parameters
        # ephemeris, name, date range, resolve image extension, resolve to x,y, positional uncertainty?
        # http:// www3.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/cadcbin/ssos/ssosclf.pl?lang=en; object=elst-pizarro; search=bynameMPC; epoch1=2013+01+01; epoch2=2015+1+16; eellipse=; eunits=arcseconds; extres=yes; xyres=yes; format=tsv
        
    print "-------------------- \n Searching for images of input objects (%s) from CFHT/Megacam from the MPC ephemeris" % args.infile
    print " with filter %s and exposure time of 287, 387, 500 seconds (OSSOS data) \n--------------------"  % args.filter
        
    for object_name in input_mbc_lines:
        query = Query(object_name, search_start_date=search_start_date, search_end_date=search_end_date)

        # GET/REVIEW THE DATA RETURNED FROM THE SEARCH
        # Parse the data for Image, Instrument, Filter and create table for each object
        # Download files with appropriate names? ie object+SSOISfilename ??
        
        obs_in_filter = parse_ssois_return(query.get(), object_name, camera_filter=args.filter)

        # OUTPUT DATA

        if len(obs_in_filter) > 0:
            with open(args.output, 'a') as outfile:
                for line in obs_in_filter:
                    try:
                        outfile.write("{:>10s} {:>10s} {:>10d} {:8.16f} {:8.16f} {:>10s} {:>10s}\n".format(object_name,
                            line['Image'], line['Exptime'], line['Object_RA'], line['Object_Dec'],
                            Time(line['MJD'], format='mjd', scale='utc'), line['Filter']))
                    except:
                        print "cannot write to outfile"
                    

            # Confirm that there is coordinates for each image
            # Add information to table? or file corresponding to the image name?

if __name__ == '__main__':
    main()
    
# exp time = 287, 387, 500
