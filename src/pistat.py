#! /usr/bin/python3

""" Vytvari piratske statistiky z nedatabazovych zdroju, napr. CSV
	a uklada je do MySQL databaze, z niz mohou byt nacteny napr. Grafanou
	Parametry:
		-t 		spusti jen testovaci cast kodu ve funkci test()
				pouziva se pri ladeni, kdy nechces spustit cele statistiky,
				ale jen urcitou cast
		-v 		verbose vystup
"""

from func import *
import credentials

# Syntax one-liners	
def arg(argumentName):	return getArg(argumentName,"tv")

##############################################################################################################
# FUNKCE
##############################################################################################################

def statFioBalance(account):	
	""" Statistika zustatku na uctu. 
		HACK: z HTML vypisu hleda sesty radek se suffixem CZK
		Uklada jen nezaporny zustatek (simple test proti pitomostem)
	"""	
	lines = getLines("https://ib.fio.cz/ib/transparent?a=%s&format=csv" % account)
	if lines:
		regexp = r'&nbsp;CZK'
		line = grep(lines,regexp)[5:6][0].strip()
		balance = float(re.sub(regexp,"",line).replace(",",".").replace(chr(160),"") )
		if balance>=0:
			Stat(dbx, "BALANCE_%s" % account, balance, 0, "Stav uctu %s" % account)		
		
##############################################################################################################
# KOD
##############################################################################################################

def main():

	# testovaci nahodna hodnota
	Stat(dbx,"RANDOM",random.randint(1,1000),0,'Nahodna hodnota')	

	# Pocet lidi *se smlouvami* placenych piraty - jako pocet radku z payroll.csv, obsahujich 2 ciselne udaje oddelene carkou
	lines = getLines('https://raw.githubusercontent.com/pirati-byro/transparence/master/payroll.csv', arg('v'))
	if lines:
		Stat(dbx, "PAYROLL_COUNT", len(grep(lines,r'[0-9]+,[0-9]+')), 0, 'Pocet lidi placenych piraty')	
	
	# Zustatky na transparentnich FIO uctech
	for account in ( "2100643125", "2100048174", "2901172853", "2400643143", "2100643205", "2400643151", "2700643161" ):
		statFioBalance(account)
			

def test():
	""" Zde se testuji nove statistiky, spousti se s parametrem -t """
	for account in ( "2100643125", "2100048174", "2901172853", "2400643143", "2100643205", "2400643151", "2700643161" ):
		PrintLastValues(dbx,"BALANCE_%s" % account,4)
	pass
			
	
if __name__ == '__main__': 
	dbx = clsMySql(credentials.FREEDB, verbose=arg('v'))
	if arg('t'):
		test()
	else:	
		main()
	dbx.close()

	