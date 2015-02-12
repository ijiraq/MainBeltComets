import numpy as np
import requests
import argparse
import os

dir_path_base = '/Users/admin/Desktop/MainBeltComets/getImages/asteroid_families'

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

    args = parser.parse_args()
    
    find_family_members(args.family, args.output)
    
def find_family_members(familyname, output=None):    
    '''
    Queries the AstDys database for members of specified family, family name is name of largest member
    '''
    
    if output == None:
        output = familyname+'_family.txt'
        
    
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
        
    for line in table_lines[1:50000]:
        assert len(line.split()) > 0
        familyname_infile = line.split()[3]
        if familyname_infile == '{}'.format(familyname):
            asteroid_list.append(line.split()[0])
    
    for line in table_lines[50000:len(table_lines)-1]:
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


if __name__ == '__main__':
    main()