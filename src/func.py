#! /usr/bin/python3

""" Funkce pro piratske statistiky """

import random, re, getopt, sys
import urllib.request
import json
import mysql.connector
import os
import hashlib
from xml.etree import ElementTree as ET

statList = []   # zde ukladej seznam vsech vygenerovanych statistik

class clsMySql:
	""" wrapper mysql databaze """

	def __init__(self, credentials, verbose=False):
		self.connected = False
		self.verbose = verbose
		try:
			self.db_connection = mysql.connector.connect(user=credentials['username'], 
														 password=credentials['password'], 
														 host=credentials['host'], 
														 database=credentials['databasename'])
			self.cursor = self.db_connection.cursor()
			self.connected = 1
		except:
			pass

		if self.verbose: 
			if self.connected:
				print("clsMySql:db %s connected" % (credentials['databasename']))
			else:	
				print("clsMySql:db %s CONNECTION FAILED" % (credentials['databasename']))

	def test_connection(self):
		if not self.connected:
			print("clsMySql: error: not connected")
			return False
		return True

	def execute(self,sql_query):
		"""Executes SQL query without string arguments, returns success"""
		if not self.test_connection():
			return False
		if self.verbose: 
			print("Performing query:" + sql_query)
		try:
			self.cursor.execute(sql_query)
			return True
		except mysql.connector.Error as err:
			print("clsMySql:error performing query: " + format(err))
			return False

	def fetchall(self,sql_query):
		"""executes SELECT SQL query and returns all data fetched"""
		self.execute(sql_query)
		return self.cursor.fetchall()
		
	def close(self):
		"""Cleanup, commit, close all open connections"""
		self.db_connection.commit()
		self.cursor.close()
		self.db_connection.close()
		if self.verbose: print("clsMySql:db connection closed")



class clsMyStat:
    ''' Trida pro ukladani statistik do databaze '''

    def __init__(self, database, stat_id, verbose=False):
        global statList
        statList.append(stat_id)
        self.database = database
        self.stat_id = stat_id
        self.tablename = 'statistics'
        self.verbose = verbose

    def getAllStats(self):
        """ Vrati seznam ID vsech statistik v databazi. 
            Pro volani teto funkce muze but trida konstruovana bez spravneho stat_id"""
        r = self.database.fetchall("SELECT DISTINCT id FROM %s" % (self.tablename))
        return [ x[0] for x in r ]

    def getLastValues(self,count=0):
        """ Vrati nejnovejsich count polozek statistiky. Je-li count=0, pak vsechny"""
        q = "SELECT date_start,value FROM %s WHERE (id='%s') ORDER BY date_start DESC" % (self.tablename,self.stat_id)
        if count:
            q += " LIMIT 0,%s" % count
        return self.database.fetchall(q )

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
        """
        # princip ukladani metody: z popisu (parametr method) vytvor md5 hash a uloz ji k zaznamu v tabluce statistiky
        # samotny popis uloz do tabulky methods, s md5 jako klicem
        method = method.replace("'",'*')    # HACK: hnus kvuli SQL dotazu, udelat slusne
        md5 = hashlib.md5(method.encode('utf-8')).hexdigest()
        self.database.execute("INSERT IGNORE INTO methods (md5, description) VALUES('%s', '%s');" % (md5,method))
        
        self.database.execute("INSERT IGNORE INTO %s (id,date_start,value, method) VALUES('%s',DATE_SUB(DATE(NOW()),INTERVAL %s DAY),%s,'%s');" % (self.tablename,self.stat_id,datediff,value,md5))
        self.database.execute("UPDATE %s SET value=%d, method='%s' WHERE (id='%s') AND (date_start=DATE_SUB(DATE(NOW()),INTERVAL %s DAY));" % (self.tablename, float(value), md5, self.stat_id,datediff))




def Stat(dbx,statname,value,datediff,friendlyName=""):
	"""Wrapper pro onelinery: Prida do statistiky jmenem statname hodnotu value pro datum datediff."""        
	if value:
		if friendlyName: 
			print("%s=%s\t%s" % (statname, repr(value), friendlyName[:30]))
		st = clsMyStat(dbx,statname)
		st.addStat(value, datediff, friendlyName)
	else:
		print("Skipping stat %s, value is None" % statname)

		
def PrintLastValues(dbx,statname,count):
    """ wrapper pro clsMyStat.printLastValues """
    st = clsMyStat(dbx,statname)
    st.printLastValues(count)


def getUrlContent(url,verbose=False):
    ''' Vrat obsah url jako retezec prevedeny na utf-8, nebo None pri neuspechu '''	
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
    
