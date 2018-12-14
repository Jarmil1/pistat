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
    -m  vytvori google mapu
    -f  jmeno souboru s mapou
    -rVal maximalni nahodny rozptyl markeru. Val je desetinne cislo:
         0.0001 vhodne pro rozptyl v ramci mesta
         0.001 rozptyl v ramci republiky

    Vstup:
    -iForum: id fora, z nejz budou nacteny tagy
         
    Uvodni rozmer a pozice mapy:     
    -sVal  scale, rozsah cca 1..20. Default: 9 (velikost CR)
    -lVal  latitude, default 49.80
    -LVal  longitude, default 15.55 (cca koordinaty havlickova brodu)
    
"""

from func import *
import func
import re 
from xml.etree import ElementTree as ET
from gmplot import gmplot
import shutil
import random
import os


def arg(argumentName):
    return func.getArg(argumentName,"hcmf:r:s:l:L:i:")


def dead_parrot(message=""):    
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


def read_feed(rozptyl):
    """ nacti prispevky z atom feedu vybranych for. u vsech, kde je 
        uveden #hastag se jmenem mesta, dopln koordinaty a uloz do struktury
    """
    records = []

    xml = _getXml("https://forum.pirati.cz/feed/topic/%s" % arg('i'))
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
                "tags": tags,
            }   
            for tag in tags:
                lat, lon = _get_coords(coords, tag)
                if lat:
                    record["latitude"] = float(lat)
                    record["longitude"] = float(lon)        
                    # posun nahodne koordinaty 
                    record["latitude"] += record["latitude"]  * rozptyl * (random.random() - 0.5)
                    record["longitude"] += record["longitude"]  * rozptyl * (random.random() - 0.5)
                    
        if "latitude" in record.keys():
            records.append(record)                

    return records


def main():

    # vystup do stdout
    for r in read_feed():
        print("%s\t%s\t%s;%s\t%s\t%s" % (r["author"], r["date"], r["latitude"], r["longitude"], ','.join(r["tags"]), r["content"]) )



def make_map(filename, latitude, longitude, scale, rozptyl):
    """ Vytvor HTML stranku s mapou (ceska republika je centrovana cca havlickuv brod)
        ze vsech tagu nalezenych ve foru. Kazde znace prirad barvu podle posledniho uvedeneho tagu
    """

    # markery je treba prekopirovat do vysledneho adresare
    dirname = os.path.dirname(filename) + "/markers"
    func.makedir(dirname)   # hack kvuli filenotfounderror na dalsim radku
    shutil.rmtree(dirname)
    shutil.copytree('../venv/lib/python3.6/site-packages/gmplot/markers', dirname)

    gmap = gmplot.GoogleMapPlotter(latitude, longitude, scale)

    # dej na mapu markery
    for r in read_feed(rozptyl):

        text = re.sub('<[^<]+?>', '', r['content'])
        text = re.sub('Statistiky: .+$', '', text).strip()
        text = re.sub('#[a-zA-Z]+', '', text)
        color = None
        for tag in r['tags']:
            try:
                color = list(filter(lambda x: x.startswith(tag+'\t'), tags_to_colors))[0].split('\t')[1].strip()
            except IndexError:
                pass
        color = color if color else 'black'        
        gmap.marker(r['latitude'], r['longitude'], color, title="%s [%s]" % (text, r['author']))

    gmap.draw(filename)

    # HACK: gmap uklada do HTML cestu k obrazkum markeru nekam do riti. oprav to 
    c = re.sub( r"MarkerImage\('.+?gmplot/markers", "MarkerImage('markers", func.readfile(filename))
    func.writefile(c, filename)
    
    
if __name__ == '__main__': 

    if arg('m') and not arg('f'):
        dead_parrot('argument error: must specify -m and -f together')

    # nacti koordinaty mest
    with open("../config/cities","r") as f:
        coords = f.readlines()

    # nacti prirazeni tagu barvam
    with open("../config/colors","r") as f:
        tags_to_colors = f.readlines()

    if arg('c'):
        for city in coords:
            print('#' + city.split("\t")[0] )
    elif arg('h'):
        dead_parrot()
    elif arg('m'):
        if not arg('i'): 
            dead_parrot("argument error: must specify -i")
        rozptyl = float(arg('r')) if arg('r') else 0
        scale = int(arg('s')) if arg('s') else 9
        lat = float(arg('l')) if arg('l') else 49.80
        lon = float(arg('L')) if arg('L') else 15.55
        make_map(arg('f'), lat, lon, scale, rozptyl)
    else:
        main()
