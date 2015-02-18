import numpy as np
import requests
import os
import pandas as pd

def main():
    
    find_mbas()
    
def find_mbas(output=None):    
    '''
    Queries the AstDys database for members of the main asteroid belt
    2.064 AU < a < 3.277 AU, e < 0.45, i < 40 deg, sini < 0.642 
    '''
    
    if output == None:
        output = 'mba_wofam_list.txt'
    output_dir = '/Users/admin/Desktop/MainBeltComets/getImages/mba'
    
    print "---------- \nSearching for obects of in the Main Asteroid Belt with \n \
            2.064 AU < a < 3.277 AU, e < 0.45, i < 40 deg \n----------"
        
    mba_wofam_list = []
    with open('mba/wo_fam_list.txt') as infile:
        for line in infile:
            mba_wofam_list.append(line)
    
    BASEURL = 'http://hamilton.dm.unipi.it/~astdys2/propsynth/numb.syn'
    
    r = requests.get(BASEURL)
    r.raise_for_status()
    table = r.content
    table_lines = table.split('\n')
    
    tableobject_list = []    
    a_list = []
    e_list = []
    sini_list = []
    for line in table_lines[2:]:
        if len(line.split()) > 0:
            tableobject_list.append(line.split()[0])
            a_list.append(float(line.split()[2]))
            e_list.append(float(line.split()[3]))
            sini_list.append(float(line.split()[4]))
    table_arrays = {'objectname': tableobject_list, 'semimajor_axis': a_list, 'eccentricity': e_list, 'sin_inclination': sini_list}
    all_objects_table = pd.DataFrame(data=table_arrays)
    #print all_objects_table

    a_list2 = []
    e_list2 = []
    sini_list2 = []
    name_list = []
    for objectname in mba_wofam_list[1:]:
        try:
            index = all_objects_table.query('objectname == "{}"'.format(objectname))
            if (float(index['semimajor_axis']) > 2.064) & (float(index['eccentricity']) < 0.45) & (float(index['sin_inclination']) < 0.642):
                name_list.append(objectname)
                a_list2.append(float(index['semimajor_axis']))
                e_list2.append(float(index['eccentricity']))
                sini_list2.append(float(index['sin_inclination']))
        except:
            print 'Could not find object {}'.format(objectname)
    table2_arrays = {'objectname': name_list, 'semimajor_axis': a_list2, 'eccentricity': e_list2, 'sin_inclination': sini_list2}
    objects_in_mb_table = pd.DataFrame(data=table2_arrays)

    print objects_in_mb_table
        
    print " Number of objects found: {}".format(len(name_list))            
    
    objects_in_mb_table.to_csv('asteroid_families/mba_wo_fam_data.csv', sep='\t', encoding='utf-8')
    name_list.to_csv('asteroid_families/mba_fam_list.txt', sep='\t', encoding='utf-8')
    
    #with open('asteroid_families/mba_wo_fam_data.txt', 'w') as outfile:
    #    outfile.write('{}'.format(objects_in_mb_table))
        
    #with open('asteroid_families/mba_fam_list.txt', 'w') as outfile:
    #    outfile.write('{}'.format(name_list))
              
    return mba_list


if __name__ == '__main__':
    main()