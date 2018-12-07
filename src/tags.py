#! /usr/bin/python3

""" 
    Projde vybrana piratska fora a vypise vsechny prispevky, ve kterych
    byl hashtag podporovaneho mesta. Hashtag se pise bez hacku, carek a mezer,
    napr #roznovpodradhostem
    Ke kazdemu prispevku jsou automaticky doplneny zemepisne koordinaty.
    
    Koordinaty mest se nacitaji ze souboru cities, jako radky ve tvaru
        hastag \t plne jmeno mesta bez hacku \t latitude \t longitude
    Zdroj: http://www.tageo.com/index-e-ez-cities-CZ-step-4.htm    
    
    Vypis je formatovan: jeden zaznam na radek, hodnoty oddelene tabulatorem
    
    Parametry:
    -h  vypise tuto napovedu
    -c  vypise seznam tagu mest
"""

from func import *
import re 
from xml.etree import ElementTree as ET

#  Seznam ID for, ktera budou prohledavana
FORUM_IDS = [
    1786,   # pozornosti hodne clanky
    41976,  # testovaci
]


def arg(argumentName):
    return getArg(argumentName,"hc")


def message_and_exit(message=""):    
    if message:
        print(message)
    print(__doc__)
    exit()


def _getXml(url):
    try:
        with urllib.request.urlopen(url) as fn:
            xml = ET.parse(fn)
        fn.close()	
        return xml
    except:
        return None


def _dummy_child(name, element):
    """ Vrat prvni XML element, jehoz tag konci na 'name'.
        HACK kvuli dekorovanym jmenum tagu: obsahuji {atom}
    """    
    for child in element:
        if child.tag.endswith(name):
            return child


def _get_coords(coords,tag):
    """ Vraci par latitude, longitude koordinatu pro mesto identifikovane 
        tagem tag. 
    """
    for l in coords:
       if l.startswith(tag.lower()+'\t'):
            parts = l.strip().split('\t')
            return parts[-2], parts[-1]
    return None, None


def main():

    # nacti prispevky z atom feedu vybranych for.
    # u vsech, kde je uveden #hastag se jmenem mesta, dopln koordinaty,
    # a uloz do struktury
    records = []
    for id in FORUM_IDS:
        xml = _getXml("https://forum.pirati.cz/feed/topic/%s" % id)
        entries  = [x for x in xml.getroot() if x.tag[-5:] == 'entry']
        for entry in entries:
            record = {}
            cont = _dummy_child('content', entry).text.strip()
            tags = re.findall(r'#([a-zA-Z0-9]{1,30})', cont)
            if tags:            
                record = {
                    "author": _dummy_child('name',_dummy_child('author', entry)).text,
                    "date": _dummy_child('published', entry).text,
                    "content": cont,
                    "tags": ",".join(tags),
                }   
                for tag in tags:
                    lat, lon = _get_coords(coords, tag)
                    if lat:
                        record["latitude"] = lat
                        record["longitude"] = lon        
            if "latitude" in record.keys():
                records.append(record)                

    # vystup 
    for r in records:
        print("%s\t%s\t%s;%s\t%s\t%s" % (r["author"], r["date"], r["latitude"], r["longitude"], r["tags"], r["content"]) )

    
if __name__ == '__main__': 

    # nacti koordinaty mest
    with open("cities","r") as f:
        coords = f.readlines()

    if arg('c'):
        for city in coords:
            print('#' + city.split("\t")[0] )
    elif arg('h'):
        message_and_exit()
    else:
        main()
