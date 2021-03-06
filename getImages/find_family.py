import numpy as np
import requests
import argparse
import os
import pandas as pd

dir_path_base = '/Users/admin/Desktop/MainBeltComets/getImages/asteroid_families'
output_dir = '/Users/admin/Desktop/MainBeltComets/getImages/asteroid_families'

def main():

    # From the given input, make list of MBCs to query
    
    parser = argparse.ArgumentParser(description='Queries the AstDys database for members of specified family, family name is name of largest member.')
    parser.add_argument("--family", '-f',
                        action="store",
                        default="3330",
                        help='asteroid family number')
    parser.add_argument("--output", "-o",
                        action="store",
                        default="family.txt",   
                        help='Location and name of output file containing object names')
    parser.add_argument("--status", 
                        action='store',
                        default=3,
                        help='Family status, options: 0, 1, 2, 3, defaults to members of families')
    parser.add_argument('--fromfile',
                        action='store',
                        default=True,
                        help='Whether to find family members from search of from input file')
                        
    args = parser.parse_args()
    
    if args.fromfile is True:
        mba_list = []
        with open('{}/{}/{}_family.txt'.format(output_dir, args.family, args.family)) as infile: ## TEMP FILE
            for line in infile:
                mba_list.append(line.strip('\n'))
    else:
        mba_list = find_by_status(args.status)
    
    #find_family_members(args.family, args.output)
    #get_all_families_list(args.output)
    parse_for_all(mba_list, args.status, args.fromfile)
    #parse_for_mba(mba_list, args.status)
    
def find_family_members(familyname, output=None):    
    '''
    Queries the AstDys database for members of specified family, family name is name of largest member
    '''
    
    if output == None:
        output = '{}_family.txt'.format(familyname)
    output_dir = os.path.join(dir_path_base, familyname)
    if os.path.isdir(output_dir) == False:
        os.makedirs(output_dir)
    
    BASEURL = 'http://hamilton.dm.unipi.it/~astdys2/propsynth/numb.members'
    r = requests.get(BASEURL)
    r.raise_for_status()
    table = r.content
    table_lines = table.split('\n')
        
    print "----- Searching for obects of in family {} -----".format(familyname)
        
    asteroid_list = []
    for line in table_lines[1:len(table_lines)-1]:
        assert len(line.split()) > 0
        familyname_infile = line.split()[3]
        if familyname_infile == '{}'.format(familyname):
            asteroid_list.append(line.split()[0])
    
    assert len(asteroid_list) > 0
    print " Number of members in family {}: {}".format(familyname, len(asteroid_list))            
    
    with open('{}/{}'.format(output_dir, output), 'w') as outfile:
        for item in asteroid_list:
              outfile.write("{}\n".format(item))
              
    return asteroid_list

def get_all_families_list(output=None):
    '''
    Queries the AstDys database for members of all known families, family name is name of largest member
    '''
    
    if output == None:
        output = 'all_families.txt'

    BASEURL = 'http://hamilton.dm.unipi.it/~astdys2/propsynth/numb.famtab'
    r = requests.get(BASEURL)
    r.raise_for_status()
    table = r.content
    table_lines = table.split('\n')
        
    print "----- Searching for list of all family names -----"
        
    familyname_list = []
    for line in table_lines[2:len(table_lines)-1]:
        assert len(line.split()) > 0
        familyname_list.append(line.split()[0])
    
    assert len(familyname_list) > 0
    print " Number of asteroid families: {}".format(len(familyname_list))            
    
    with open('{}/{}'.format(dir_path_base, output), 'w') as outfile:
        for item in familyname_list:
              outfile.write("{}\n".format(item))
              
    return familyname_list

def find_by_status(status=3, output=None):    
    '''
    Queries the AstDys database for members of the main asteroid belt
    with a particular family designation status
    '''
    
    BASEURL = 'http://hamilton.dm.unipi.it/~astdys2/propsynth/numb.famrec'
    r = requests.get(BASEURL)
    r.raise_for_status()
    table = r.content
    table_lines = table.split('\n')
        
    print "----- Searching for objects of in the Main Asteroid Belt family designation status {} -----".format(status)
        
    mba_list = []
    for line in table_lines[1:]:
        if len(line.split()) > 0:
            mba_name = line.split()[0]
            mba_status = line.split()[2]
            if status == '0':
                if mba_status == '0':
                    mba_list.append(mba_name)
            else:
                if mba_status != '0':
                    mba_list.append(mba_name)

    assert len(mba_list) > 0
    print " Number of objects in the M.A.B. family designation status {}: {}".format(status, len(mba_list))            
    
    with open('{}/all_list_status_{}.txt'.format(output_dir, status), 'w') as outfile:
        for item in mba_list:
              outfile.write("{}\n".format(item))
    if status == '0':
        with open('{}/none/none_family.txt'.format(output_dir), 'w') as outfile:
            for item in mba_list:
                  outfile.write("{}\n".format(item))
    else:
        with open('{}/all/all_family.txt'.format(output_dir), 'w') as outfile:
            for item in mba_list:
                  outfile.write("{}\n".format(item))
              
    return mba_list

def get_all_astrometry(mba_list, status=3):
    
    print '----- Getting astrometry -----'    
    
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
    i_list = np.degrees(np.arcsin(sini_list))
    table_arrays = {'objectname': tableobject_list, 'semimajor_axis': a_list, 'eccentricity': e_list, 'inclination': i_list}
    all_objects_table = pd.DataFrame(data=table_arrays)
    #all_objects_table.to_csv('{}/all_data_table.txt'.format(dir_path_base, status), sep='\t', encoding='utf-8')
    #print all_objects_table
    
    return all_objects_table

def parse_for_all(mba_list, status=3, fromfile=True):    
    '''
    Queries the AstDys database for all objects of a specified status and gets astrometry
    '''
    
    '''
    if fromfile is True:
        all_objects_table = pd.read_table('asteroid_families/all_data_table.txt', sep='\t')
    else:
        all_objects_table = get_all_astrometry(mba_list, status) 
    '''
    all_objects_table = get_all_astrometry(mba_list, status) 
        
    print "----- Searching for obects of in AstDys -----"
        
    a_list2 = []
    e_list2 = []
    i_list2 = []
    name_list = []

    for objectname in mba_list:
        index = all_objects_table.query('objectname == "{}"'.format(objectname))
        try:
            name_list.append(objectname)
            a_list2.append(float(index['semimajor_axis']))
            e_list2.append(float(index['eccentricity']))
            i_list2.append(float(index['inclination']))
        except:
            print objectname
            print index
    print " Number of objects found: {}".format(len(name_list)) 
    
    table2_arrays = {'objectname': name_list, 'semimajor_axis': a_list2, 'eccentricity': e_list2, 'inclination': i_list2}
    objects_table = pd.DataFrame(data=table2_arrays)
        
    objects_table.to_csv('{}/all_data_status_{}.txt'.format(dir_path_base, status), sep='\t', encoding='utf-8', index=False)
        
    with open('{}/all_list_status_{}.txt'.format(dir_path_base, status), 'w') as outfile:
        for item in name_list:
            outfile.write('{}\n'.format(item))
              
    return name_list  
    
def parse_for_mba(mba_list, status=3):    
    '''
    Queries the AstDys database for members of the main asteroid belt and astrometry
    a > 2.067 AU, e < 0.45, i < 40 deg, sini < 0.642 
    '''
    all_objects_table = get_all_astrometry(mba_list, status)
    
    print "----- Searching for obects of in the Main Asteroid Belt with a > 2.064 AU, e < 0.45, i < 40 deg -----"
    
    a_list2 = []
    e_list2 = []
    sini_list2 = []
    name_list = []
    x = 0
    for objectname in mba_list:
        index = all_objects_table.query('objectname == "{}"'.format(objectname))
        try:
            if (float(index['semimajor_axis']) > 2.064) & (float(index['eccentricity']) < 0.45) & (float(index['sin_inclination']) < 0.642):
                name_list.append(objectname)
                a_list2.append(float(index['semimajor_axis']))
                e_list2.append(float(index['eccentricity']))
                sini_list2.append(float(index['sin_inclination']))
        except:
            x += 1
    i_list2 = np.degrees(np.arcsin(sini_list2))
    table2_arrays = {'objectname': name_list, 'semimajor_axis': a_list2, 'eccentricity': e_list2, 'inclination': i_list2}
    objects_in_mb_table = pd.DataFrame(data=table2_arrays)

    print objects_in_mb_table
        
    print " Number of objects found: {}".format(len(name_list))            
    
    objects_in_mb_table.to_csv('{}/mba_data_status_{}.txt'.format(dir_path_base, status), sep='\t', encoding='utf-8', index=False)
        
    with open('{}/mba_list_status_{}.txt'.format(dir_path_base, status), 'w') as outfile:
        outfile.write('{}'.format(name_list))
              
    return name_list    


if __name__ == '__main__':
    main()