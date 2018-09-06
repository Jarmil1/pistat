#! /usr/bin/python3

""" Vytvari piratske statistiky z nedatabazovych zdroju, napr. CSV
    a uklada je do MySQL databaze, z niz mohou byt nacteny napr. Grafanou
    Parametry:
        -t      spusti jen testovaci cast kodu ve funkci test()
                pouziva se pri ladeni, kdy nechces spustit cele statistiky,
                ale jen urcitou cast
        -v 	    verbose vystup
"""

from func import *
import credentials


# Pro zjistovani poctu clenu: id statistiky a URL na forum prislusne skupiny KS
PIRATI_KS = { 
    "PI_MEMBERS_ZLINSKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=39",
    "PI_MEMBERS_VYSOCINA": "https://forum.pirati.cz/memberlist.php?mode=group&g=37",
    "PI_MEMBERS_USTECKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=42",
    "PI_MEMBERS_STREDOCESKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=78",
    "PI_MEMBERS_PRAHA": "https://forum.pirati.cz/memberlist.php?mode=group&g=33",
    "PI_MEMBERS_PLZENSKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=44",
    "PI_MEMBERS_PARDUBICKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=35",
    "PI_MEMBERS_OLOMOUCKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=38",
    "PI_MEMBERS_MORAVSKOSLEZSKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=34",
    "PI_MEMBERS_LIBERECKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=41",
    "PI_MEMBERS_KRALOVEHRADECKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=32",
    "PI_MEMBERS_KARLOVARSKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=43",
    "PI_MEMBERS_JIHOMORAVSKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=36",
    "PI_MEMBERS_JIHOCESKY": "https://forum.pirati.cz/memberlist.php?mode=group&g=40",
    "PI_MEMBERS_NEZARAZENI": "https://forum.pirati.cz/memberlist.php?mode=group&g=437"
    }

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
        line = grep(regexp,lines)[5:6][0].strip()
        balance = float(re.sub(regexp,"",line).replace(",",".").replace(chr(160),"") )
        if balance>=0:
            Stat(dbx, "BALANCE_%s" % account, balance, 0, "Stav uctu %s" % account)		

            
def statNrOfMembers(id, url):
    """ Statistika poctu clenu krajsekho sdruzeni, zjistuje se z piratskeho fora,
        jako pocet clenu dane skupiny, vypsany na samostatnem radku "XX uzivatelu"
    """
    lines = grep(r'[0-9]{1,5} uživatel', getLines(url))
    if len(lines)==1:
        lineparts = lines[0].strip().split()
        try:
            count = int(lineparts[0])
        except ValueError:
            count = 0
            
        Stat(dbx, id, count, 0, 'Pocet clenu v %s' % id[11:])	
    else:
        print("Error: Nemohu najit pocet clenu %s: %s " % (id,url))
        count = 0

    return count

    
##############################################################################################################
# KOD
##############################################################################################################

def main():

    # testovaci nahodna hodnota
    Stat(dbx,"RANDOM",random.randint(1,1000),0,'Nahodna hodnota')	

    # Pocet lidi *se smlouvami* placenych piraty - jako pocet radku z payroll.csv, obsahujich 2 ciselne udaje oddelene carkou
    lines = getLines('https://raw.githubusercontent.com/pirati-byro/transparence/master/payroll.csv', arg('v'))
    if lines:
        Stat(dbx, "PAYROLL_COUNT", len(grep(r'[0-9]+,[0-9]+',lines)), 0, 'Pocet lidi placenych piraty')	

    # Zustatky na vsech transparentnich FIO uctech uvedenych na wiki FO
    content = getUrlContent("https://wiki.pirati.cz/fo/seznam_uctu")
    if content:
        fioAccounts = list(set(re.findall(r'[0-9]{6,15}[ \t]*/[ \t]*2010', content)))
        for account in fioAccounts:
            account = account.split("/")[0].strip()
            statFioBalance(account)

    # Pocty clenu v jednotlivych KS a celkem ve strane (prosty soucet dilcich)		
    sum = 0
    for id in PIRATI_KS:
        sum += statNrOfMembers(id, PIRATI_KS[id])
    Stat(dbx, "PI_MEMBERS_TOTAL", sum, 0, 'Pocet clenu CPS celkem')			

    
def test():
    """ Zde se testuji nove statistiky, spousti se s parametrem -t """
    pass

if __name__ == '__main__': 
    dbx = clsMySql(credentials.FREEDB, verbose=arg('v'))
    if arg('t'):
        test()
    else:	
        main()
    dbx.close()

