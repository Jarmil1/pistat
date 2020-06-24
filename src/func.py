#! /usr/bin/python3

""" Funkce pro piratske statistiky """

import re, getopt, sys
import urllib.request
import json
import os
import hashlib
import time
import requests
import psycopg2
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta

import credentials

statList = []   # zde ukladej seznam vsech vygenerovanych statistik


class PG:
    """ wrapper Postgres databaze
        Prednostne se pripojuje k env promennym
    """

    def __init__(self, credentials, verbose=False):
        self.connected = False
        self.verbose = verbose

        u = os.getenv('METRIKY_PSQL_USER', credentials['username'])
        p = os.getenv('METRIKY_PSQL_PASSWORD', credentials['password'])
        h = os.getenv('METRIKY_PSQL_HOST', credentials['host'])
        d = os.getenv('METRIKY_PSQL_DBNAME', credentials['databasename'])
        if self.verbose:
            print("Postgres: connecting to %s@%s " % (d, h))

        try:
            self.db_connection = psycopg2.connect(user=u, password=p, host=h, database=d)
            self.cursor = self.db_connection.cursor()
            self.connected = 1
        except Exception as e:
            print(e)
            pass

        if self.verbose:
            if self.connected:
                print("Postgres:db %s connected" % (credentials['databasename']))
            else:
                print("Postgres:db %s CONNECTION FAILED" % (credentials['databasename']))

    def test_connection(self):
        if not self.connected:
            print("Postgres: error: not connected")
            return False
        return True

    def execute(self, sql_query):
        """Executes SQL query without string arguments, returns success"""
        if not self.test_connection():
            return False
        if self.verbose:
            print("Performing query:" + sql_query)
        try:
            self.cursor.execute(sql_query)
            return True
        except Exception as err:
            print("Postgres:error performing query: " + format(err))
            return False

    def fetchall(self, sql_query):
        """executes SELECT SQL query and returns all data fetched"""
        self.execute(sql_query)
        return self.cursor.fetchall()

    def close(self):
        """Cleanup, commit, close all open connections"""
        self.db_connection.commit()
        self.cursor.close()
        self.db_connection.close()
        if self.verbose: print("Postgres:db connection closed")


class Influx:

    def __init__(self, my_credentials):
        self.url = my_credentials['host']
        self.db = my_credentials['databasename']
        self.user = my_credentials['username']
        self.password = my_credentials['password']

    def insert(self, serie_name, value, my_timestamp):
        """ Vrazi data do time serie v influxu. Zaokrouhluje na dny.
            Neprepisuje stara data. Vraci uspesnost
        """
        data = '%s value=%s %s000000000' % (serie_name, str(value), str(int(my_timestamp)))
        r = requests.post(self.url + "/write?db=" + self.db, data.encode(), auth=(self.user, self.password))
        return r.status_code in range(200, 300)

    def delete(self, serie_name):
        """ Smaze vsechna data v serie_name. Vraci uspesnost """
        data = 'q=DELETE FROM \"%s\"' % serie_name
        r = requests.get(self.url + "/query?db=" + self.db, data.encode(), auth=(self.user, self.password))
        return r.status_code in range(200, 300)


class clsMyStat:
    """ Trida pro ukladani statistik do databaze """

    def __init__(self, stat_id, verbose=False):
        global statList
        statList.append(stat_id)
        self.database = Influx(credentials.INFLUX_TEST)
        self.stat_id = stat_id
        self.tablename = 'statistics'
        self.verbose = verbose

    def getAllStats(self):
        """ Vrati seznam ID vsech statistik v databazi. 
            Pro volani teto funkce muze but trida konstruovana bez spravneho stat_id"""
        r = self.database.fetchall("SELECT DISTINCT id FROM %s" % (self.tablename))
        return [ x[0] for x in r ]

    def getLastValues(self, count=0, with_methods=False):
        """ Vrati nejnovejsich count polozek statistiky. 
                count           pocet polozek, je-li=0, pak vsechny
                with_methods    vrati textovy popis metod ziskani zaznamu z tabulky methods (pomalejsi)
        """
        if with_methods:
            q = "SELECT date_start,value, methods.description FROM methods RIGHT JOIN %s on method=md5 WHERE (id='%s') ORDER BY date_start DESC" % (self.tablename, self.stat_id)
        else:
            q = "SELECT date_start,value FROM %s WHERE (id='%s') ORDER BY date_start DESC" % (self.tablename,self.stat_id)
        if count:
            q += " LIMIT 0,%s" % count
        return self.database.fetchall(q)

    def printLastValues(self,count=0):
        """ Vytiskne nejnovejsich count polozek statistiky.
            Je-li count=0, tiskne vsechny"""
        if self.verbose:    
            print("Poslednich %s hodnot ve statistice %s:" % (count,self.stat_id))
        r = self.getLastValues(count)
        for row in r:
            print("%s\t%s" % (row[0],row[1]))
        
    def addStat(self, value, datediff, method=''):
        """Prida jednu polozku statistiky pod udane datum. Pokud uz existuje, prepise ji
            datediff    vzdalenost data od dnesniho, napr. 1=vcera, 2=predevcirem atd
            method      textovy popis, jak byla statistika ziskana
            value       hodnota, zaokrouhluje se na 2 desetinna mista
        """
        # princip ukladani metody: z popisu (parametr method) vytvor md5 hash a uloz ji k zaznamu v tabluce statistiky
        # samotny popis uloz do tabulky methods, s md5 jako klicem
        method = method.replace("'",'*')    # HACK: hnus kvuli SQL dotazu, udelat slusne
        md5 = hashlib.md5(method.encode('utf-8')).hexdigest()
        # self.database.execute("INSERT INTO methods (md5, description) VALUES('%s', '%s') ON CONFLICT(md5) DO NOTHING;" % (md5,method))
        
        value = round(float(value), 2)
        mydate = datetime.now() - timedelta(days=datediff)
        self.database.insert(self.stat_id, value, datetime.timestamp(mydate))


def Stat(statname, value, datediff, method=""):
    """ Wrapper pro onelinery: Prida do statistiky jmenem statname hodnotu value pro datum datediff. """
    if value:
        if method:
            print("%s=%s\t%s" % (statname, repr(value), method[:36]))
        st = clsMyStat(statname)
        st.addStat(value, datediff, method)
    else:
        print("Skipping stat %s, value is None" % statname)


def getUrlContent(url,verbose=False):
    """ Vrat obsah url jako retezec prevedeny na utf-8, nebo None pri neuspechu """
    if verbose: print("Opening %s" % url)
    try:
        with urllib.request.urlopen(url) as f:
            return f.read().decode('utf-8')
    except:
        return None

        
def getLines(url,verbose=False):
    ''' Vrat obsah url jako seznam radku, nebo None pri neuspechu '''	
    cont = getUrlContent(url, verbose)
    return cont.split("\n") if cont else None


def get_json(url):
    """ Vrat JSON odpoved z adresy URL nebo none v pripade chyby """
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla'})
    try:
        r = urllib.request.urlopen(req).read()
        return json.loads(r.decode('utf-8'))    
    except Exception as e:
        return None

    
def grep(regexp,list_of_strings):
    ''' returns list_of_strings filtered for lines matching regepx '''
    rc = re.compile(regexp)		
    return list(filter(rc.search, list_of_strings))


def getArg(argumentName,allowedArguments):
    ''' Vraci parametr prikazoveho radku. 
        allowedArguments:	specifikace povolenych argumentu v syntaxi funkce getopt()
        return: 			U parametru typu flag vrati true/false, u retezcoveho aktualni hodnotu.
    '''
    (volbytmp,argumenty) = getopt.getopt(sys.argv[1:],allowedArguments)
    for v in volbytmp: 
        if v[0]=="-" + argumentName: 
            return v[1] if v[1] else True
    return False


def readfile(filename):
    """ Vrat obsah souboru filename """
    with open(filename,'r') as f:
        ret = f.read()
    return ret
    

def replace_all(string, replaces):    
    """ proved nahrady v retezci string. 'replaces' je hash tabulka """
    for x in replaces:
        string = string.replace(x, replaces[x])
    return string
    

def writefile(string, filename):
    """ Uloz retezec string do filename. """
    with open(filename, 'w') as f:
        f.write(string)
        
    
def makedir(dirname):
    """ zajisti, ze adresar dirname existuje """
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

    
def atom_entries(url):
    """ Vrat seznam XML elementu 'entry' z atom feedu s adresou URL """
    try:
        with urllib.request.urlopen(url) as fn:
            xml = ET.parse(fn)
        fn.close()	
    except:
        return None
        
    entries  = [x for x in xml.getroot() if x.tag[-5:] == 'entry']
    return entries

    
def filter_config(rawinput):
    ''' Vrat list radku z listu rwainput, bez komentaru a prazdnych radku, 
        bez duplicit, radky orezane o whitespaces, v nahodnem poradi
    '''    
    x = list(set(filter(
        lambda x: (not x.strip().startswith('#')) and (x.strip()), rawinput)))
    return list(map(str.strip, x))
    
    
def getconfig(filename):
    ''' Vrat list radku v konfiguracnim souboru filename, bez komentaru
        a prazdnych radku, bez duplicit, radky orezane o whitespaces, 
        v nahodnem poradi
    '''    
    return filter_config(readfile(filename).split('\n'))
    

def lmap(function, argument):
    ''' pro zprehledneni casto pouzivaneho zapisu '''
    return list(map(function, argument))


def wait(sleep_length):
    """ Ceka stanoveny pocet vterin, zobrazuje counter """
    for sleepiter in range(sleep_length):
        print("Sleeping for %s sec...  \r" % (sleep_length-sleepiter), end = '\r')
        time.sleep(1)
    print()


