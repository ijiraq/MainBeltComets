import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
%matplotlib inline
from astropy.io import ascii
from astropy.table import Table, Column


# PARSING ALL OBJECTS FROM MPC ORBITAL
# ephemeris: http://www.minorplanetcenter.net/iau/MPCORB.html
# format: http://www.minorplanetcenter.net/iau/info/MPOrbitFormat.html

with open("MPCORB.txt", "rw+") as infile: 

    MPCORBnumlist = []
    MPCORBqlist = []
    MPCORBecclist = []
    MPCORBinclist = []
    MPCORBnamelist = []

    for line in infile.readlines():
        s = line #str(infile.readlines(line))
        number = s[0:8].strip()     # object number
        q = float(s[37:47].strip()) # perihelion distance (AU)
        ecc = float(s[70:80].strip()) # orbital eccentricity
        inc = float(s[59:69].strip()) # inclination, J@00.0 (degrees)
        name = s[107:117].strip()   # designation and name
        MPCORBnumlist.append(number)
        MPCORBqlist.append(q)
        MPCORBecclist.append(ecc)
        MPCORBinclist.append(inc)
        MPCORBnamelist.append(name)
    
MPCORBtabledata = Table([MPCORBnumlist, MPCORBqlist, MPCORBecclist, MPCORBinclist], 
          names=('object_number', 'perihelion', 'eccentricity', 'inclination'))

MPCORBtabledata["semimajor_axis"] = MPCORBtabledata['perihelion']/(1 - MPCORBtabledata['eccentricity'])  # a = q /(1-e)
MPCORBtabledata["data_type"] = 'MPCORB'

# convert from astropy.table to panda.DataFrame so that I don't have to change query section
MPCORBtable = pd.DataFrame(np.array(MPCORBtabledata))

# PARSING LIST OF KNOWN MAIN BELT COMETS

mbcs = pd.read_excel("MBCs_woScheila.xlsx")
num_list = mbcs["number"]

mbc_qlist = []
mbc_alist = []
mbc_elist = []
mbc_ilist = []
mbc_type = []

for num in num_list:
    object = Ctable.query('number == "{}"'.format(num))
    q1 = float(object["perihelion"])
    a1 = float(object["semimajor_axis"])
    inc1 = float(object["inclination"])
    ecc1 = float(object["eccentricity"])
    mbc_qlist.append(q1)
    mbc_alist.append(a1)
    mbc_elist.append(ecc1)
    mbc_ilist.append(inc1)
    typeof = 'iden_comet'
    mbc_type.append(typeof)

mbctable = Table([num_list, mbc_qlist, mbc_elist, mbc_ilist, mbc_alist, mbc_type], 
          names=('number', 'perihelion', 'eccentricity', 'inclination', 'semimajor_axis', 'data_type'))

mbc_table = pd.DataFrame(np.array(mbctable))



