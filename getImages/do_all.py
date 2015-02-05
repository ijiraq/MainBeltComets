import argparse

from find_family import find_family_members
from getImages import get_image_info
from getStamps import get_stamps
from sep_phot import find_objects_by_phot

from ossos_scripts import storage
import ossos_scripts.coding
import ossos_scripts.mpc
import ossos_scripts.util


def main():
    """
    Input asteroid family name and an asteroid number and get out photometry values
    """
    
    parser = argparse.ArgumentParser(description='Run SSOIS and return the available images in a particular filter.')

    parser.add_argument("--filter",
                    action="store",
                    default='r',
                    dest="filter",
                    choices=['r', 'u'],
                    help="passband: default is r'")
    parser.add_argument("--family",
                        action="store",
                        default="3330",
                        help='list of objects to query')
    parser.add_argument('--type',
                        default='p',
                        choices=['o', 'p', 's'], 
                        help="restrict type of image (unprocessed, reduced, calibrated)")
    parser.add_argument("--radius", '-r',
                        action='store',
                        default=0.02,
                        help='Radius (degree) of circle of cutout postage stamp.')
    parser.add_argument("--aperture", '-a',
                        action='store',
                        default=10.0,
                        help='aperture (degree) of circle for photometry.')
    parser.add_argument("--thresh", '-t',
                            action='store',
                            default=5.0,
                            help='threshold value.')
    parser.add_argument("--object", '-o',
                            action='store',
                            default='54286',
                            help='the object to preform photometry on')
                            
    args = parser.parse_args()
    
    do_all_things(args.family, args.object, args.filter, args.type, args.radius, args.aperture, args.thresh)

def do_all_things(familyname, objectname=None, filtertype=None, imagetype=None, radius=None, aperture=None, thresh=None):
    
    if filtertype == None:
        filtertype = 'r'
    if imagetype == None:
        imagetype == 'p'
    if radius == None:
        radius == 0.02
    if aperture == None:
        aperture == 10.0
    if thresh == None:
        thresh = 5.0
    
    # find_family.py - family name
        # find_family_members()
        # get list of asteroids in a family
    #asteroid_list = find_family_members(familyname)
    
    # getImages.py - family name, filter, type
        # get_image_info()
        # get images information from SSOIS
    image_list = get_image_info(familyname, filtertype, imagetype)
    
    if objectname == None:
        objectname = image_list[0]
        
    # getStamps.py - family name, radius of cutout
        # get_stamps()
        # cutout a piece of each image with object in it
    get_stamps(familyname, radius)
        
    # sep_phot.py - family name, object name, aperture, threshold
        # find_objects_by_phot()
        # identify objects in image by photometry values and coordinates                
    find_objects_by_phot(familyname, objectname, aperture, thresh)                    
                        
                        
if __name__ == '__main__':
    main()                        
    