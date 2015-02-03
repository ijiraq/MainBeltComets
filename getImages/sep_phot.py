import os
import sep
import numpy as np
from astropy.io import fits
from astropy.table import Table, vstack
from astropy.io import ascii
import argparse
from scipy.spatial import cKDTree
import math


import sys
sys.path.append('/Users/admin/Desktop/MainBeltComets/getImages/ossos_scripts/')

import ossos_scripts.ssos
import ossos_scripts.wcs as wcs
from ossos_scripts.storage import get_astheader

# Identify objects in each postage stamp


def main(): 
    
    parser = argparse.ArgumentParser(
        description='For an input .fits image, aperture size, threshold, and output file: preforms photometry')
    parser.add_argument("--family", '-f',
                        action="store",
                        default="testfamily",
                        help="The directory in getImages/family/ with input .fits files for astrometry/photometry measurements.")
    parser.add_argument("--radius", '-r',
                        action='store',
                        default=10.0,
                        help='aperture (degree) of circle for photometry.')
    parser.add_argument("--thresh", '-t',
                            action='store',
                            default=5.0,
                            help='threshold value.')
    parser.add_argument("--object", '-o',
                            action='store',
                            default='test',
                            help='the object to preform photometry on')
                            
    args = parser.parse_args()
    
    
    global familyname
    familyname = args.family
    global objectname
    objectname = args.object
    global ap
    ap = float(args.radius)
    global th
    th = float(args.thresh)
    # perhaps there's a better way of doing this, self.variable?
    
    dir_path_base = '/Users/admin/Desktop/MainBeltComets/getImages/'
    global family_dir
    family_dir = os.path.join(dir_path_base, familyname)
    object_dir = os.path.join(family_dir, familyname+'_'+objectname)
    output_dir = os.path.join(object_dir, 'sep_phot_output')
    if os.path.isdir(output_dir) == False:
        os.makedirs(output_dir)
        
    # to do: make output file, still need to add entries to this
    with open('{}/{}_r{}_t{}_output.txt'.format(object_dir, objectname, ap, th), 'w') as outfile:
        outfile.write("{:>3s} {:>8s} {:>14s} {:>14s} {:>18s} {:>16s} {:>10s}\n".format(
            "Image", "mRA", "diffRA", "mDEC", "diffDEC", "flux", "mag"))
    
    mag_list = []
    
    for file in os.listdir('{}'.format(object_dir)):
        
        if file.endswith('.fits') == True:
            expnum_p = file.split('_')[1]

            with fits.open('{}/{}'.format(object_dir, file)) as hdulist:
                print "Preforming photometry on image {} ".format(file)
                #print hdulist.info()
                
                if hdulist[0].data is None: # STILL NOT WORKING, what if more than 2ccd mosaic? could just be aperture values?
                    try:
                        zeropt = fits.getval('{}/{}'.format(object_dir, file), 'PHOTZP', 1)
                        table1 = sep_phot(hdulist[1].data)
                        table2 = dosep(hdulist[2].data)
                        table = vstack([table1, table2])
                        #ascii.write(table, os.path.join(output_dir, '{}_phot.txt'.format(expnum_p)))
                        astheader = hdulist[0].header
                    except LookupError: # maybe not correct error type?
                        print " no PHOTZP in header "
                    
                else:
                    try:
                        table = sep_phot(hdulist[0].data)
                        astheader = hdulist[0].header
                        #ascii.write(table, os.path.join(output_dir, '{}_phot.txt'.format(expnum_p)))
                        zeropt = fits.getval('{}/{}'.format(object_dir, file), 'PHOTZP', 0)
                    except LookupError:
                        print " no PHOTZP in header "
                        
                object_data = comp_coords(table, expnum_p, astheader, zeropt)
                mag_list.append(object_data[6])
                
                if len(object_data) > 0:
                    with open('{}/{}_r{}_t{}_output.txt'.format(object_dir, objectname, ap, th), 'a') as outfile:
                        try:
                            outfile.write('{} {} {} {} {} {} {}\n'.format(
                                    object_data[0], object_data[1], object_data[2], object_data[3], object_data[4], object_data[5], object_data[6]))
                        except:
                            print "cannot write to outfile"
    
    # should query JPL Horizons to see how much the object varies in magnitude about its orbit
    '''
    mag_list = [21, 21.5, 21.6, 22, 26]
    avg = np.mean(mag_list)
    assert len(mag_list) > 0
    for element in mag_list:
        if abs(element - avg) < 1:
            print " object successfully identified"
        else:
            print " mag: {}    average: {}    difference: {}".format(element, avg, abs(element - avg))
            print " magnitude varies by more than one, object not identified correctly"
        mag0 = element
    '''
        
def sep_phot(data):
    ''' preform photometry similar to source extractor '''
        
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
    kronrad, krflag = sep.kron_radius(data, objs['x'], objs['y'], objs['a'], objs['b'], objs['theta'], ap)
    flux, fluxerr, flag = sep.sum_ellipse(data, objs['x'], objs['y'], objs['a'], objs['b'], objs['theta'], 2.5*kronrad, subpix=1)
    flag |= krflag  # combine flags into 'flag'
    
    # mask = np.zeros(data.shape, dtype=np.bool)
    # sep.mask_ellipse(mask, objs['x'], objs['y'], obs['a'], objs['b'], objs['theta'], r=3.)

    # Specify a per-pixel "background" error and a gain. This is suitable when the data have been background subtracted.
    # *** check image header for gain value ***
    # flux, fluxerr, flag = sep.sum_circle(data, objs['x'], objs['y'], 3.0, err=bkg.globalrms, gain=1.0)

    # write to ascii table
    table = Table([objs['x'], objs['y'], flux], names=('x', 'y', 'flux'))
    return table

def comp_coords(septable, expnum_p, astheader, zeropt):
    '''compare predicted RA and DEC to that measured by sep photometry'''

    x_array = np.array(septable['x'])
    y_array = np.array(septable['y'])
    tree = cKDTree(zip(x_array.ravel(), y_array.ravel()))
    # print tree.data

    imageinfo = familyname+'_images.txt'
    with open('{}/{}'.format(family_dir, imageinfo)) as infile:
        for line in infile.readlines()[1:]:
            assert len(line.split()) > 0
            objectname = line.split()[0]
            expnum_p_fromfile = line.split()[1]
            pRA = float(line.split()[3])
            pDEC = float(line.split()[4])
            
            pvwcs = wcs.WCS(astheader)
            
            
            
            expnum = (line.split()[1]).rstrip('p')
            
            # for entries in *_images.txt that correspond to images of the object
            if expnum_p_fromfile == expnum_p:
                
                pRA_pix, pDEC_pix = pvwcs.sky2xy(pRA, pDEC) # convert from WCS to pixels
                #print " Predicted RA and DEC: {}  {}".format(pRA, pDEC)
                #print "  in pixels: {} {}".format(pRA_pix, pDEC_pix)
                
                # parse through table and get RA and DEC closest to predicted coordinates (in pixels)
                
                coords = np.array([pRA_pix, pDEC_pix])
                d, i = tree.query(coords)
                
                for row in septable[i:i+1]:
                    mRA_pix = row['x']
                    mDEC_pix = row['y']
                    flux = row['flux']
                                    
                mRA, mDEC = pvwcs.xy2sky(mRA_pix, mDEC_pix) # convert from pixels to WCS
                #print " Measured RA and DEC: {}  {}".format(mRA, mDEC)
                #print "  in pixels: {} {}".format(mRA_pix, mDEC_pix)
                
                diffRA = mRA - pRA
                diffDEC = mDEC - pDEC
                #print " Difference: {} {}".format(diffRA, diffDEC)
                
                APmag = -2.5*math.log10(flux)+zeropt
                print "   Flux, mag: {}, {}".format(flux, APmag)
                        
                return expnum_p, mRA, diffRA, mDEC, diffDEC, flux, APmag

        
if __name__ == '__main__':
    main()