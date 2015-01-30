import os
import sep
import numpy as np
from astropy.io import fits
from astropy.table import Table, vstack
from astropy.io import ascii
import argparse
from drizzlepac import pixtosky
# to install drizzlepac:
# pip install stsci.distutils
# pip install stscipython
# pip install --upgrade drizzlepac

import sys
sys.path.append('/Users/admin/Desktop/MainBeltComets/getImages/ossos_scripts/')

import ossos_scripts.ssos
import ossos_scripts.wcs as wcs
from ossos_scripts.storage import get_astheader

# Identify objects in each postage stamp


def main(): 
    
    parser = argparse.ArgumentParser(
        description='For an input .fits image, aperture size, threshold, and output file: preforms photometry')
    parser.add_argument("--ossin",
                        action="store",
                        default="3330_stamps_gt8/",
                        help="The directory in getImages/3330/ with input .fits files for astrometry/photometry measurements.")

# CREATE A DIRECTORY FOR OUTPUT?
#    parser.add_argument("--output", "-o",
#                        action="store",
#                        default="/Users/admin/Desktop/MainBeltComets/getImages/sep_phot.txt",   
#                        help='Location and name of output file containing image photometry values.')
# dir_path = os.path.join(self.feed, self.address)  # will return 'feed/address'
#os.makedirs(dir_path)                             # create directory [current_path]/feed/address
#output = open(os.path.join(dir_path, file_name), 'wb')

    parser.add_argument("--radius", '-r',
                        action='store',
                        default=10.0,
                        help='aperture (degree) of circle for photometry.')
    parser.add_argument("--thresh", '-t',
                            action='store',
                            default=5.0,
                            help='threshold value.')
    parser.add_argument("--images", '-i',
                            action='store',
                            default='test_images.txt',
                            help='image information text file.')
                            
# PARSE IN MEASURED X AND Y COORDINATES
    dir_path_base = '/Users/admin/Desktop/MainBeltComets/getImages/'
    
    args = parser.parse_args()
    
    global imageinfo
    imageinfo = args.images
    global ap
    ap = float(args.radius)
    global th
    th = float(args.thresh)
    
    global x
    x = 420
    global y
    y = 388
    
    # perhaps there's a better way of doing this, self.variable?
    
    for image in os.listdir('/Users/admin/Desktop/MainBeltComets/getImages/{}'.format(args.ossin)):
        if image.endswith('.fits') == True:
            objectname = str(image.split('_')[0])
            imagename = str(image.split('_')[1])
            dir_path = os.path.join(dir_path_base, objectname)
            if os.path.isdir(dir_path) == False:
                os.makedirs(dir_path)
            with fits.open('{}/{}'.format(args.ossin, image)) as hdulist:
                # doesnt work for 304757_1692837p_242.335075_-14.024202.fits specifically for default values
                print "Doing photometry on image %s " % image
                #print hdulist.info()
                #if (hdulist[0].data == None):
                if hdulist[0].data is None:
                    table1 = dosep(hdulist[1].data)
                    table2 = dosep(hdulist[2].data)
                    table = vstack([table1, table2])
                    ascii.write(table, os.path.join(dir_path, '{}_info.txt'.format(image)))
                    astheader = hdulist[0].header
                    compare(table, imagename, astheader) # how to get header information ??
                else:
                    table0 = dosep(hdulist[0].data)
                    astheader = hdulist[0].header
                    ascii.write(table0, os.path.join(dir_path, '{}_info.txt'.format(image)))
                    compare(table0, imagename, astheader)
                #print data
        
def dosep(data):
        
    # Measure a spatially variable background of some image data (numpy array)
    bkg = sep.Background(data) #, mask=mask, bw=64, bh=64, fw=3, fh=3) # optional parameters
        
    # Evaluate the spatially variable background and RMS:
    back = bkg.back() # creates an array, same shape and type as data
    rms = bkg.rms()   # creates an array, same shape and type as data
        
    # Directly subtract the background from the data in place
    bkg.subfrom(data)
    bkg.globalback    # Global "average" background level
    bkg.globalrms     # Global "average" RMS of background
        
    # for the background subtracted data, detect objects in data given some threshold
    # ****CHOOSE APPROPRIATE THRESHOLD****
    thresh = th * bkg.globalrms    # ensure the threshold is high enough wrt background        
    objs = sep.extract(data, thresh)
    #print len(objs)
    #print objs['x'][0] # print flux-wieghted 

    # calculate the Kron radius for each object, then we perform elliptical aperture photometry within that radius
    kronrad, krflag = sep.kron_radius(data, objs['x'], objs['x'], objs['y'], objs['b'], objs['theta'], ap)
    flux, fluxerr, flag = sep.sum_ellipse(data, objs['x'], objs['x'], objs['y'], objs['b'], objs['theta'], 2.5*kronrad, subpix=1)
    flag |= krflag  # combine flags into 'flag'
    
    # mask = np.zeros(data.shape, dtype=np.bool)
    # sep.mask_ellipse(mask, objs['x'], objs['y'], obs['a'], objs['b'], objs['theta'], r=3.)

    # Specify a per-pixel "background" error and a gain. This is suitable when the data have been background subtracted.
    # ***WHAT IS THE IMAGE GAIN? 1.67 ?***
    # flux, fluxerr, flag = sep.sum_circle(data, objs['x'], objs['y'], 3.0, err=bkg.globalrms, gain=1.0)

    # write to ascii table
    table = Table([objs['x'], objs['y'], flux], names=('x', 'y', 'flux'))
    return table

def compare(septable, imagename, astheader):
    # compare predicted RA and DEC to that measured by sep photometry
    # get predicted RA and DEC from text output from getImages
    # print '{}'.format(imageinfo)
    with open('{}'.format(imageinfo)) as infile:
        for line in infile.readlines()[1:]:
            assert len(line.split()) > 0
            objectname = line.split()[0]
            image = line.split()[1]
            pRA = float(line.split()[3])
            pDEC = float(line.split()[4])
            
            pvwcs = wcs.WCS(astheader)
            pRA_pix, pDEC_pix = pvwcs.sky2xy(pRA, pDEC)
            print "  predicted pix: {} {}".format(pRA_pix, pDEC_pix)
            
            expnum = (line.split()[1]).rstrip('p')
            if image == imagename:
                print " Predicted RA and DEC for object {} in image {}: {}  {}".format(objectname, image, pRA, pDEC)

                # parse through table and get RA and DEC closest to measured-by-eye coordinates
                # compare to predicted
                #print septable
                x_max = pRA_pix + 25
                x_min = pRA_pix - 25
                y_max = pDEC_pix + 5
                y_min = pDEC_pix - 5
                print " Specified x,y coordinates on image: {} {}".format(x,y)
                try:
                    for row in septable:
                        #print row['x'], row['y']
                        if (float(row['x']) < x_max) & (float(row['x']) > x_min) & (float(row['y']) < y_max) & (float(row['y']) > y_min):
                            mRA_pix = float(row['x'])
                            mDEC_pix = float(row['y'])
                            #print mRA_pix, mDEC_pix
                            mRA, mDEC = pvwcs.xy2sky(mRA_pix, mDEC_pix)
                
                            # print mRA, mDEC
                            print " Measured RA and DEC for object {} in image {}: {}  {}".format(objectname, image, mRA, mDEC)
                            diffRA = mRA - pRA
                            diffDEC = mDEC - pDEC
                            print " Difference: {} {}".format(diffRA, diffDEC)
                except:
                    print "no rows qualify"
            else:
                print image, imagename
        
if __name__ == '__main__':
    main()

