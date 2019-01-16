#! /usr/bin/python3

""" 
    Some tests
    
"""

from func import *
import func
import re 
import shutil
import random
import os

def _dummy_child(name, element):
    """ Vrat prvni XML element, jehoz tag konci na 'name'.
        HACK kvuli dekorovanym jmenum tagu: obsahuji {atom}
    """    
    for child in element:
        if child.tag.endswith(name):
            return child
    
if __name__ == '__main__': 

    # nacti vlakna z redmine, vypis nazvy prispevku a pocet
    # TODO: Atom redmine vraci pouze 15 (asi) nejnovejsich prispevku, nelze tedy pres nej zjistovat pocty ukolu.
    with open("../config/redmine","r") as f:
        lines = f.readlines()    

    for l in lines:
        if not l.strip().startswith('#'):
            m = re.search(r"[ \t]*(.*?)[ \t]+(.*)", l)
            if m and len(m.groups())>1:
                print(m.group(1),m.group(2))
                entries  = func.atom_entries(m.group(2))
                for entry in entries:
                    cont = _dummy_child('title', entry).text.strip()
                    print(cont)
                print(len(entries))
