import numpy as np
import requests
import argparse


def main():

    # IDENTIFY PARAMETERS FOR QUERY OF SSOIS FROM INPUT

    # From the given input, make list of MBCs to query
    
    parser = argparse.ArgumentParser(description='Run SSOIS and return the available images in a particular filter.')

    parser.add_argument("--filter", "-f",
                    action="store",
                    default='r',
                    dest="filter",
                    choices=['r', 'u'],
                    help="passband: default is r'")
    parser.add_argument("--ossin",
                        action="store",
                        default="3330",
                        help='asteroid family number')
    parser.add_argument("--dbimages",
                        action="store",
                        default="vos:OSSOS/dbimages",
                        help='vospace dbimages containerNode')
    parser.add_argument('--type',
                        default='p',
                        choices=['o', 'p', 's'], 
                        help="restrict type of image (unprocessed, reduced, calibrated)")
    parser.add_argument("--output", "-o",
                        action="store",
                        default="/Users/admin/Desktop/MainBeltComets/findObjects/family.txt",   
                        help='Location and name of output file containing object names')

    args = parser.parse_args()
    
    
    familyname = args.ossin
    
    BASEURL = 'http://hamilton.dm.unipi.it/~astdys2/propsynth/numb.members'
    
    r = requests.get(BASEURL)
    r.raise_for_status()
    
    table = r.content
    table_lines = table.split('\n')
        
    print "-------------------- \n Searching for obects of in family %s \n--------------------" % args.ossin
        
    print len(table_lines)
    asteroid_list = []
        
    for line in table_lines[1:50000]:
        assert len(line.split()) > 0
        familyname = line.split()[3]
        if familyname == '3330':
            asteroid_list.append(line.split()[0])
            
    
    for line in table_lines[50000:len(table_lines)-1]:
        assert len(line.split()) > 0
        familyname = line.split()[3]
        if familyname == '3330':
            asteroid_list.append(line.split()[0])
                
    with open(args.output, 'w') as outfile:
        for item in asteroid_list:
              outfile.write("{}\n".format(item))


if __name__ == '__main__':
    main()