#! /usr/bin/python3

""" Funkce pro piratske statistiky """

import random, re, getopt, sys
import urllib.request
import mysql.connector

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

    def printLastValues(self,count=0):
        """ Vytiskne nejnovejsich count polozek statistiky.
            Je-li count=0, tiskne vsechny"""
        if self.verbose:    
            print("Poslednich %s hodnot ve statistice %s:" % (count,self.stat_id))
        q = "SELECT date_start,value FROM %s WHERE (id='%s') ORDER BY date_start DESC" % (self.tablename,self.stat_id)
        if count:
            q += " LIMIT 0,%s" % count
        r = self.database.fetchall(q )
        for row in r:
            print("%s\t%s" % (row[0],row[1]))
        
    def addStat(self,value,datediff):
        """Prida jednu polozku statistiky pod udane datum. Pokud uz existuje, prepise ji
            datediff    .. vzdalenost data od dnesniho, napr. 1=vcera, 2=predevcirem atd
            """
        self.database.execute("INSERT IGNORE INTO %s (id,date_start,value) VALUES('%s',DATE_SUB(DATE(NOW()),INTERVAL %s DAY),%s);" % (self.tablename,self.stat_id,datediff,value))
        self.database.execute("UPDATE %s SET value=%d WHERE (id='%s') AND (date_start=DATE_SUB(DATE(NOW()),INTERVAL %s DAY));" % (self.tablename,float(value), self.stat_id,datediff))


def Stat(dbx,statname,value,datediff,friendlyName=""):
	"""Wrapper pro onelinery: Prida do statistiky jmenem statname hodnotu value pro datum datediff."""        
	if value:
		if friendlyName: 
			print("%s,%s: %s" % (statname,friendlyName,repr(value)))
		st = clsMyStat(dbx,statname)
		st.addStat(value,datediff)
	else:
		print("Skipping stat %s, value is None" % statname)

		
def PrintLastValues(dbx,statname,count):
    """ wrapper pro clsMyStat.printLastValues """
    st = clsMyStat(dbx,statname)
    st.printLastValues(count)


def getUrlContent(url,verbose=False):
    ''' Vraci obsah url jako retezec prevedeny na utf-8, nebo None pri neuspechu '''	
    if verbose: print("Opening %s" % url)
    try:
        with urllib.request.urlopen(url) as f:
            return f.read().decode('utf-8')
    except:
        return None

        
def getLines(url,verbose=False):
    ''' Vraci obsah url jako seznam radku, nebo None pri neuspechu '''	
    cont = getUrlContent(url, verbose)
    return cont.split("\n") if cont else None

    
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

