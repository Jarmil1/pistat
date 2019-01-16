#! /usr/bin/python3

""" 
    Projde parametrem zadane piratske forum a vypise vsechny prispevky, ve kterych
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
import shutil
import random
import os


MARKER_JS = """var latlng = new google.maps.LatLng($lat, $lon);
		var img = new google.maps.MarkerImage('markers/$img');
		var marker = new google.maps.Marker({
		title: "$text",
		icon: img,
		position: latlng
		});
		marker.setMap(map);
"""

GOOGLE_MAP_HTML = """<html>
<head>
<meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
<meta http-equiv="content-type" content="text/html; charset=UTF-8"/>
<title>Google Maps - pygmaps </title>
<script type="text/javascript" src="https://maps.googleapis.com/maps/api/js?libraries=visualization&sensor=true_or_false"></script>
<script type="text/javascript">
	function initialize() {
		var centerlatlng = new google.maps.LatLng($lat, $lon);
		var myOptions = {
			zoom: $scale,
			center: centerlatlng,
			mapTypeId: google.maps.MapTypeId.ROADMAP
		};
		var map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);

		$markers

	}
</script>
</head>
<body style="margin:0px; padding:0px;" onload="initialize()">
	<div id="map_canvas" style="width: 100%; height: 100%;"></div>
</body>
</html>
"""


def arg(argumentName):
    return func.getArg(argumentName,"hcmf:r:s:l:L:i:")


def dead_parrot(message=""):    
    if message:
        print(message)
    print(__doc__)
    exit()


def _dummy_child(name, element):
    """ Vrat prvni XML element, jehoz tag konci na 'name'.
        HACK kvuli dekorovanym jmenum tagu: obsahuji {atom}
    """    
    for child in element:
        if child.tag.endswith(name):
            return child


def _get_coords(coords, tag):
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
         rozptyl .. maximalni hodnota nahodnho posunu markeru proti skutecnym koordinatum
    """
    records = []

    entries = func.atom_entries("https://forum.pirati.cz/feed/topic/%s" % arg('i'))
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


def flush_feed():
    # vystup feedu do stdout
    for r in read_feed():
        print("%s\t%s\t%s;%s\t%s\t%s" % (r["author"], r["date"], r["latitude"], r["longitude"], ','.join(r["tags"]), r["content"]) )


def js_marker(lat, lon, img, text):
    return MARKER_JS.replace('$lat', str(lat)).replace('$lon', str(lon)). \
            replace('$img', img).replace('$text', text)

        
def html_map(lat, lon, scale, markers):
    return GOOGLE_MAP_HTML.replace('$lat', str(lat)).replace('$lon', str(lon)). \
            replace('$scale', str(scale)).replace('$markers', markers)


def make_map(filename, latitude, longitude, scale, rozptyl):
    """ Vytvor HTML stranku s mapou ze vsech tagu nalezenych ve foru. Znackam prirad obrazek, existuje-li"""

    # markery je treba prekopirovat do vysledneho adresare...
    dirname = os.path.dirname(filename) + "/markers"
    func.makedir(dirname)   # hack kvuli filenotfounderror na dalsim radku
    shutil.rmtree(dirname)
    shutil.copytree('../venv/lib/python3.6/site-packages/gmplot/markers', dirname)

    # ...vcetne vlastnich markeru
    my_markers_path = '../templates/markers/'
    for file_name in os.listdir(my_markers_path):
        full_file_name = os.path.join(my_markers_path, file_name)
        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, dirname)
        
    # dej na mapu markery
    feed = read_feed(rozptyl)
    markers = ""
    for r in feed:

        text = re.sub('<[^<]+?>', '', r['content'])
        text = re.sub('Statistiky: .+$', '', text).strip()
        text = re.sub('#[a-zA-Z]+', '', text)
        color = None

        image = "_default_.png"
        for tag in r['tags']:
            if (os.path.isfile(os.path.join(my_markers_path, "%s.png" % tag))):
                image = "%s.png" % tag
                
        markers += js_marker(r['latitude'], r['longitude'], image, "%s [%s]" % (text, r['author']))

    func.writefile(html_map(latitude, longitude, scale, markers), filename)
    
    
if __name__ == '__main__': 

    if arg('m') and not arg('f'):
        dead_parrot('argument error: must specify -m and -f together')

    # nacti koordinaty mest a mistnich nazvu
    with open("../config/cities","r") as f:
        coords = f.readlines()

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
        flush_feed()
