#! /usr/bin/python3
# -*- coding: utf-8 -*-

""" Vytvari piratske statistiky z nedatabazovych zdroju, napr. CSV
    a uklada je do MySQL databaze, z niz mohou byt nacteny napr. Grafanou
    Parametry:
        -h      help: vypise tuto napovedu
        -a      vypis seznam ID vsech statistik
        -t      spusti jen testovaci cast kodu ve funkci test()
                pouziva se pri ladeni, kdy nechces spustit cele statistiky,
                ale jen urcitou cast
        -v 	    verbose vystup
        -q      vypis na zaver seznam sql dotazu do grafany
        -sName  uloz stup do statistiky Name a skonci. 
                Vstupem je celociselna hodnota na stdin. Priklad:
                    cat somefile | wc -l | pistat.py -sSTAT_SOMEFILE_LINES
        -pName  print. Vytiskni statistiku Name
"""

import func
import credentials
import re
import random

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

# sledovane youtube kanaly
YOUTUBERS = {
    "YOUTUBE_PIRATI": [ "https://www.youtube.com/channel/UC_zxYLGrkmrYazYt0MzyVlA", "https://www.youtube.com/user/CeskaPiratskaStrana/about" ],
    "YOUTUBE_TOP09": [ "https://www.youtube.com/user/topvidea", "https://www.youtube.com/user/topvidea/about" ], 
    "YOUTUBE_ODS": [ "https://www.youtube.com/user/tvods", "https://www.youtube.com/user/tvods/about" ],
    "YOUTUBE_ANO2011": [ "https://www.youtube.com/user/anobudelip", "https://www.youtube.com/user/anobudelip/about" ],
}


def arg(argumentName):
    return func.getArg(argumentName,"tvqs:p:ha")


def statFioBalance(account):	
    """ Statistika zustatku na uctu, vraci zjistenou hodnotu nebo 0 
        HACK: z HTML vypisu hleda sesty radek se suffixem CZK
        Uklada jen nezaporny zustatek (simple test proti pitomostem)
    """	
    lines = func.getLines("https://ib.fio.cz/ib/transparent?a=%s&format=csv" % account)
    if lines:
        regexp = r'&nbsp;CZK'
        line = func.grep(regexp,lines)[5:6][0].strip()
        balance = float(re.sub(regexp,"",line).replace(",",".").replace(chr(160),"") )
        if balance>=0:
            func.Stat(dbx, "BALANCE_%s" % account, balance, 0, "Stav uctu %s" % account)		
            return balance
    return 0       
            
            
def statNrOfMembers(id, url):
    """ Statistika poctu clenu krajsekho sdruzeni, zjistuje se z piratskeho fora,
        jako pocet clenu dane skupiny, vypsany na samostatnem radku "XX uzivatelu"
    """
    lines = func.grep(r'[0-9]{1,5} uživatel', func.getLines(url))
    if len(lines)==1:
        lineparts = lines[0].strip().split()
        try:
            count = int(lineparts[0])
        except ValueError:
            count = 0
            
        func.Stat(dbx, id, count, 0, 'Pocet clenu v %s' % id[11:])	
    else:
        print("Error: Nemohu najit pocet clenu %s: %s " % (id,url))
        count = 0

    return count

    
def stat_forum():
    """ Pocet prispevku a uzivatelu fora"""
    lines = func.getUrlContent('https://forum.pirati.cz/index.php')
    
    res = re.search(r'Celkem p(.*?)<strong>(.*?)</strong> &bull', lines)
    if res and len(res.groups())>1:
        func.Stat(dbx, "PI_FORUM_POSTS", int(res.group(2)), 0, 'Pocet prispevku na piratskem foru')
    
    res = re.search(r'Celkem zaregistrovan(.*?)<strong>(.*?)</strong> &bull', lines)
    if res and len(res.groups())>1:
        func.Stat(dbx, "PI_FORUM_USERS", int(res.group(2)), 0, 'Pocet uzivatelu na piratskem foru')


def message_and_exit(message=""):    
    if message:
        print(message)
    print(__doc__)
    exit()


def main():

    # testovaci nahodna hodnota
    func.Stat(dbx,"RANDOM",random.randint(1,1000),0,'Nahodna hodnota')	

    # Pocet lidi *se smlouvami* placenych piraty - jako pocet radku z payroll.csv, obsahujich 2 ciselne udaje oddelene carkou
    lines = func.getLines('https://raw.githubusercontent.com/pirati-byro/transparence/master/payroll.csv', arg('v'))
    if lines:
        func.Stat(dbx, "PAYROLL_COUNT", len(func.grep(r'[0-9]+,[0-9]+',lines)), 0, 'Pocet lidi placenych piraty')	

    # Zustatky na vsech transparentnich FIO uctech uvedenych na wiki FO
    content = func.getUrlContent("https://wiki.pirati.cz/fo/seznam_uctu")
    if content:
        fioAccounts = list(set(re.findall(r'[0-9]{6,15}[ \t]*/[ \t]*2010', content)))
        sum = 0
        for account in fioAccounts:
            account = account.split("/")[0].strip()
            sum += statFioBalance(account)
        func.Stat(dbx, "BALANCE_FIO_TOTAL", sum, 0, 'Celkovy stav vsech FIO transparentnich uctu')

    # Pocty clenu v jednotlivych KS a celkem ve strane (prosty soucet dilcich)		
    sum = 0
    for id in PIRATI_KS:
        sum += statNrOfMembers(id, PIRATI_KS[id])
    func.Stat(dbx, "PI_MEMBERS_TOTAL", sum, 0, 'Pocet clenu CPS celkem')			

    # piratske forum
    stat_forum()
    
    # pocty odberatelu vybranych Youtube kanalu
    for id in YOUTUBERS:
        # odberatelu
        content = func.getUrlContent(YOUTUBERS[id][0])
        m = re.findall(r'([\xa00-9]+)[ ]+odb.{1,1}ratel', content)
        value = int(re.sub(r'\xa0','',m[0])) if m else 0
        func.Stat(dbx, id + '_SUBSCRIBERS', value, 0, id + '_SUBSCRIBERS')
        
        # shlednuti
        content = func.getUrlContent(YOUTUBERS[id][1])
        m = re.findall(r'<b>([\xa00-9]+)</b> zhl.{1,1}dnut', content)
        value = int(re.sub(r'\xa0','',m[0])) if m else 0
        func.Stat(dbx, id + '_VIEWS', value, 0, id + '_VIEWS')

    # pocty followeru a tweetu ve vybranych twitter kanalech
    twitter_accounts = func.getconfig('../config/twitters')[:200]
    for id in twitter_accounts:
        content = func.getUrlContent("https://twitter.com/%s" % id)
        m = re.findall(r'data-count=([0-9]*)', content)
        if m:
            func.Stat(dbx, "TWITTER_%s_FOLLOWERS" % id.upper() , int(m[2]), 0, id + " Followers")   # hack, predpoklada toto cislo jako treti nalezene
            func.Stat(dbx, "TWITTER_%s_TWEETS" % id.upper() , int(m[0]), 0, id + " Tweets")         # hack dtto    
            func.Stat(dbx, "TWITTER_%s_LIKES" % id.upper() , int(m[3]), 0, id + " Tweets")          # hack dtto    

    
def test():
    """ Zde se testuji nove statistiky, spousti se s parametrem -t """
    twitter_accounts = func.getconfig('../config/twitters')[:200]
    for id in twitter_accounts:
        content = func.getUrlContent("https://twitter.com/%s" % id)
        m = re.findall(r'data-count=([0-9]*)', content)
        if m:
            func.Stat(dbx, "TWITTER_%s_FOLLOWERS" % id.upper() , int(m[2]), 0, id + " Followers")   # hack, predpoklada toto cislo jako treti nalezene
            func.Stat(dbx, "TWITTER_%s_TWEETS" % id.upper() , int(m[0]), 0, id + " Tweets")         # hack dtto    
            if len(m)>3:
                func.Stat(dbx, "TWITTER_%s_LIKES" % id.upper() , int(m[3]), 0, id + " Likes")          # hack dtto    
            else: 
                print(id, "skipped, no likes found")



if __name__ == '__main__': 
    dbx = func.clsMySql(credentials.FREEDB, verbose=arg('v'))

    if arg('t'):
        test()
    elif arg('h'):
        message_and_exit()
    elif arg('a'):
        s = clsMyStat(dbx, '')
        lst = s.getAllStats()
        for l in lst:
            print(l)
    elif arg('s'):
        try:
            value = int(sys.stdin.read().strip())
        except ValueError:
            message_and_exit("ERROR: expected number on stdio")
        if value:
            Stat(dbx, arg('s'), value, 0, '')
    elif arg('p'):
        stat = clsMyStat(dbx, arg('p'))
        stat.printLastValues()
    else:
        main()

    if arg('q'):    
        print()
        for statid in statList:
            print("SELECT $__time(date_start), value as %s FROM statistics WHERE id='%s'" % (statid, statid))
            
    dbx.close()

