import sep
import numpy as np


# Identify objects in each postage stamp


def main(): 
    with open("lix_images_test.txt") as infile: 
        for line in infile.readlines()[1:]: 
            assert len(line.split()) > 0
            x = float(line.split()[3])   # change from RA, DEC to x,y for non WCS images ?
            y = float(line.split()[4])
            data = np.array([x, y]) # needs to be a 2d array, how to do for 1 object?
            output = SEx(data)
            print output
        
    
def SEx(data):
    # Do i need to include a table with coordinates for each image?
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
    # CHOOSE APPROPRIATE THRESHOLD
    thresh = 1.5 * bkg.globalrms    # ensure the threshold is high enough wrt background        
    objs = sep.extract(data, thresh)

    # Sum the flux in ellipses of a = 3.0
    flux, fluxerr, flag = sep.sum_ellipse(data, objs['x'], objs['y'], 3.0)

    # Specify a per-pixel "background" error and a gain. This is suitable when the data have been background subtracted.
    # WHAT IS THE IMAGE GAIN? 1.67 ?
    flux, fluxerr, flag = sep.sum_ellipse(data, objs['x'], objs['y'], 3.0, err=bkg.globalrms, gain=1.0)


if __name__ == '__main__':
    main()

