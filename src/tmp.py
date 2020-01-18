#! /usr/bin/python3

""" 
    Some tests
"""

from func import *
import func
import re 
import credentials

if __name__ == '__main__': 

    dbx = func.clsMySql(credentials.LOCALHOST)
    #dbx = func.PG(credentials.PGHOME, verbose=arg('v'))

    r = dbx.fetchall("SELECT md5, description from METHODS")
    for m,d in r:
        print(m,d)


    dbx.close()
        