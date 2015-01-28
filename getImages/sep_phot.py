import os
import sep
import numpy as np
from astropy.io import fits
from astropy.table import Table, vstack
from astropy.io import ascii
import argparse


# Identify objects in each postage stamp


def main(): 
    
    parser = argparse.ArgumentParser(
        description='For an input .fits image, aperture size, and output file: preforms photometry')
    parser.add_argument("--ossin",
                        action="store",
                        default="3330_stamps_gt8/*.fits",
                        help="The input .fits files for astrometry/photometry measurements.")
    parser.add_argument("--output", "-o",
                        action="store",
                        default="/Users/admin/Desktop/MainBeltComets/getImages/sep_phot.txt",   
                        help='Location and name of output file containing image photometry values.')
    parser.add_argument("--radius", '-r',
                        action='store',
                        default=6.0,
                        help='aperture (degree) of circle for photometry.')
    parser.add_argument("--thresh", '-t',
                            action='store',
                            default=1.5,
                            help='threshold value.')
    
    
    args = parser.parse_args()
    global ap
    ap = float(args.radius)
    global th
    th = float(args.thresh)
    
    with fits.open('3330_stamps_gt8/304757_1692837p_242.335075_-14.024202.fits') as hdulist: # 
        
        print hdulist.info()
        if (hdulist[0].data == None):
            table1 = dosep(hdulist[1].data)
            table2 = dosep(hdulist[2].data)
            table = vstack([table1, table2])
            ascii.write(table, '{}'.format(args.output))
            # what if more than two ccds???
        else:
            table0 = dosep(hdulist[0].data)
            print "hi"
            ascii.write(table0, '{}'.format(args.output))
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
    table = Table([objs['x'], objs['y'], flux, fluxerr], names=('x', 'y', 'flux', 'flux_err'))
    return table


if __name__ == '__main__':
    main()

