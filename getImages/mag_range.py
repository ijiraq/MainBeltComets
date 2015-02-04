# horizons.py
# Query JPL Horizons via the web service

import urllib2 as url
import time
from astropy.time import Time
import numpy as np

# QUERY THE JPL DATABASE FOR A GIVEN:
    # object, date range, geocentric position, quantity 9
        

# Run a Horizons query
# eg. output = batch("Haumea", "2010-12-28 10:00", "2010-12-29 10:00", 1, su='d')

def batch(object, time_start, time_end, step, su='d'):
    
    if step == None: # default
        step = 1
    else:
        step = int(step)
        
    # Construct the queary URL

    s = '9' # apparent magnitude
    
    # URL pieces that Horizon needs for its processing instructions
    urlArr = ["http://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1&COMMAND=",
              '',
              "&MAKE_EPHEM='YES'&TABLE_TYPE='OBSERVER'&START_TIME=",
              '',
              "&STOP_TIME=",
              '',
              "&STEP_SIZE=",
              '',
              "&QUANTITIES=" + s,
              "&CSV_FORMAT='YES'"]
              
    # Change the object name, start and end times, and time step into proper url-formatting
    url_style_output = []
    for obj in [object, time_start, time_end]:
        os = obj.split()
        if len(os) > 1:
            ob = "'" + os[0] + '%20' + os[1] + "'"
        else:
            ob =  "'" + object + "'"
        url_style_output.append(ob)
    step = "'" + str(step) + "%20" + su + "'"
     
    # URL components
    urlArr[1] = url_style_output[0]  # formatted object name
    urlArr[3] = url_style_output[1]  # start time
    urlArr[5] = url_style_output[2]  # end time
    urlArr[7] = step  # timestep   
       
    urlStr = "".join(urlArr)  # create the url to pass to Horizons
       
    # Query Horizons; if it's busy, wait and try again in a minute
    done = 0
    while not done:
        urlHan = url.urlopen(urlStr)
        urlData = urlHan.readlines()
        urlHan.close()
        if len(urlData[0].split()) > 1:
            if "BUSY:" <> urlData[0].split()[1]:
                done = 1
            else:
                print urlData[0],
                print "Sleeping 60 s and trying again"
                time.sleep(60)
        else:
            done = 1   
       
    date_start = change_date(time_start)
    date_end = change_date(time_end)
    
    mag_list = []
    
    for idx, line in enumerate(urlData):  #testing
        try:
            date_jpl = line.split()[0]+' '+(line.split()[1]).strip(',')
            if date_start == date_jpl:
                index_start = idx
        except:
            None
             
    for idx, line in enumerate(urlData):  #testing
        try:
            date_jpl = line.split()[0]+' '+(line.split()[1]).strip(',')
            if date_end == date_jpl:
                index_end = idx
        except:
            None
 
    for line in urlData[index_start:index_end+1]:
        try:
            mag_list.append(float((line.split()[4]).strip(',')))
        except:
            None
    
    print mag_list
    mean = np.mean(mag_list)
    std = np.std(mag_list)
    maxval = np.amax(mag_list)
    minval = np.amin(mag_list)
        
    return mag_list, mean, std
    
    
       
def change_date(date):
    # convert time format 01-01-2001 00:00 to 01-Jan-2001 00:00
    date_split = date.split('-')
    month = int(date_split[1])
    month_name = ['nan', 'Jan', "Feb", 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for i in range(0,13):
        if i == month:
            month_jpl = month_name[i]
    date_new = date_split[0]+'-'+month_jpl+'-'+date_split[2]
    
    return date_new
    
# Run the script from the command line
if __name__ == "__main__":
    mag_list = batch("Haumea", "2010-12-28 10:00", "2010-12-30 10:00", 1, su='d')  # for example
    
    
         
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        