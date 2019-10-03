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
import datetime
import json
from func import lmap


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


def arg(argumentName):
    return func.getArg(argumentName,"tvqs:p:ha")


def statFioBalance(account):	
    """ Statistika zustatku na uctu, vraci zjistenou hodnotu nebo 0 
        HACK: z HTML vypisu hleda sesty radek se suffixem CZK
        Uklada jen nezaporny zustatek (simple test proti pitomostem)
    """	
    url = "https://ib.fio.cz/ib/transparent?a=%s&format=csv" % account
    lines = func.getLines(url)
    if lines:
        regexp = r'&nbsp;CZK'
        line = func.grep(regexp,lines)[5:6][0].strip()
        balance = float(re.sub(regexp,"",line).replace(",",".").replace(chr(160),"") )
        if balance>=0:
            func.Stat(dbx, "BALANCE_%s" % account, balance, 0, "Stav uctu %s, scrappingem z %s" % (account, url))
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
            
        func.Stat(dbx, id, count, 0, 'Pocet clenu krajskeho sdruzeni v %s, scrappingem z piratskeho fora jako pocet clenu prislusne skupiny' % id[11:])	
    else:
        print("Error: Nemohu najit pocet clenu %s: %s " % (id,url))
        count = 0

    return count

    
def stat_forum():
    """ Pocet prispevku a uzivatelu fora"""
    lines = func.getUrlContent('https://forum.pirati.cz/index.php')
    
    res = re.search(r'Celkem p(.*?)<strong>(.*?)</strong> &bull', lines)
    if res and len(res.groups())>1:
        func.Stat(dbx, "PI_FORUM_POSTS", int(res.group(2)), 0, 'Pocet prispevku na piratskem foru (scrappingem z https://forum.pirati.cz/index.php)')
    
    res = re.search(r'Celkem zaregistrovan(.*?)<strong>(.*?)</strong> &bull', lines)
    if res and len(res.groups())>1:
        func.Stat(dbx, "PI_FORUM_USERS", int(res.group(2)), 0, 'Pocet uzivatelu na piratskem foru (scrappingem z https://forum.pirati.cz/index.php)')


def redmine_issues(redmine_id, stat_id, odbor_name):
    """ redmine: pocet otevrenych podani odboru nebo jine slozky.
        vytvori dva druhy metriky: prvni pro vsechna podani, druha pouze pro podani od 1.1.2019 (maji 'NEW' ve jmene metriky)
            redmine_id      identifikace odboru v Redmine (soucast url)
            stat_id         identifikace odboru ve statistikach, soucast ID statistiky, napr pro 'AO' 
                            to bude REDMINE_AO_OPENTICKETS_COUNT
            odbor_name      jmeno odboru v dlouhem popisu statitstiky, napriklad 'Kancelar'
    """
    
    base_url = 'https://redmine.pirati.cz/projects/%s/issues.json?tracker_id=12' % redmine_id
    resp = func.get_json(base_url)
    if resp:
        original_count = resp['total_count']
        all_issues = []
        if original_count:
            total_count, offset, total_sum = 0, 0, 0
            while offset < original_count: 
                resp = func.get_json(base_url + '&amp;limit=100&amp;offset=%s' % offset)
                offset +=100
                all_issues.extend(resp['issues'])

        # ze ziskanych dat staci jen datumy    
        all_issues = lmap( lambda x: datetime.datetime.strptime(x['start_date'][:10], "%Y-%m-%d").date(), all_issues)

        new_issues = list(filter( lambda x: x >= datetime.date(2019,1,1), all_issues))

        sum_all_issues_ages = sum(lmap( lambda x: (datetime.date.today() - x).days, all_issues))
        sum_new_issues_ages = sum(lmap( lambda x: (datetime.date.today() - x).days, new_issues))
        
        func.Stat(dbx, "REDMINE_%s_OPENTICKETS_COUNT" % stat_id, len(all_issues), 0, 'Pocet otevrenych podani slozky %s, REST dotazem do Redmine' % odbor_name)
        func.Stat(dbx, "REDMINE_%s_NEWOPENTICKETS_COUNT" % stat_id, len(new_issues), 0, 'Prumerne stari otevrenych podani (po 1.1.2019) slozky %s, REST dotazem do Redmine' % odbor_name)

        if len(all_issues):
            func.Stat(dbx, "REDMINE_%s_OPENTICKETS_AGE" % stat_id, round(sum_all_issues_ages/len(all_issues), 2), 0, 'Prumerne stari otevrenych podani slozky %s, REST dotazem do Redmine' % odbor_name)
        if len(new_issues):
            func.Stat(dbx, "REDMINE_%s_NEWOPENTICKETS_AGE" % stat_id, round(sum_new_issues_ages/len(new_issues), 2), 0, 'Prumerne stari otevrenych podani (po 1.1.2019) slozky %s, REST dotazem do Redmine' % odbor_name)


def message_and_exit(message=""):    
    if message:
        print(message)
    print(__doc__)
    exit()


def stat_from_regex( statid, url, regex, humandesc="" ):
    """ Prida do dnesni statistiku hodnotu ze stranky url, vyhledanou regularnim vyrazem.
        Jako hodnota se prida prvni skupina (v zavorkach) daneho vyrazu, napr:
          r'before (.*?) behind'
        Pokud se tato hodnota neda interpretovat jako int nebo neni nalezena, bude 
        zobrazena do stdout chybova hlaska a hodnota se neulozi.
        Jako popis ziskani se ulozi humandesc, doplnena o URL, z nejz je scrappovano
    """        
    res = re.search(regex, func.getUrlContent(url))
    humandesc = "%s (scrappingem z %s)" % (humandesc, url)
    if res and len(res.groups()):
        try:
            value = int(res.group(1))
        except ValueError:
            print("ERROR Statistika %s: Hodnotu \"%s\" vracenou regexem nelze prelozit jako int." % (statid, res.group(1)))
            return 
        func.Stat(dbx, statid, value, 0, humandesc)
            
    else:
        print("ERROR Statistika %s: Regex nenalezl zadnou hodnotu" % (statid))


def main():

    # testovaci nahodna hodnota
    func.Stat(dbx,"RANDOM",random.randint(1,1000),0,'Nahodna hodnota bez vyznamu, jako test funkcnosti statistik')	

    # Pocet lidi *se smlouvami* placenych piraty - jako pocet radku z payroll.csv, obsahujich 2 ciselne udaje oddelene carkou
    lines = func.getLines('https://raw.githubusercontent.com/pirati-byro/transparence/master/payroll.csv', arg('v'))
    if lines:
        func.Stat(dbx, "PAYROLL_COUNT", len(func.grep(r'[0-9]+,[0-9]+',lines)), 0, 'Pocet lidi placenych piraty, zrejme zastarale: jako pocet radku v souboru https://raw.githubusercontent.com/pirati-byro/transparence/master/payroll.csv')	

    # piroplaceni: pocet a prumerne stari (od data posledni upravy) zadosti ve stavu "Schvalena hospodarem" (state=3)
    resp = func.get_json('https://piroplaceni.pirati.cz/rest/realItem/?format=json&amp;state=3')
    if resp:
        func.Stat(dbx, "PP_APPROVED_COUNT", len(resp), 0, 'Pocet zadosti o proplaceni ve stavu Schvalena hospodarem, REST dotazem do piroplaceni')
        if len(resp):
            resp = lmap( lambda x: (datetime.date.today() - datetime.datetime.strptime(x['updatedStamp'], "%d.%m.%Y, %H:%M").date()).days, resp)
            func.Stat(dbx, "PP_APPROVED_AGE", round(sum(resp)/len(resp), 2), 0, 'Prumerne stari zadosti o proplaceni ve stavu Schvalena hospodarem, REST dotazem do piroplaceni')

    # piroplaceni: pocet a prumerne stari (od data posledni upravy) zadosti ve stavu "Ke schvaleni hospodarem" (state=2)
    resp = func.get_json('https://piroplaceni.pirati.cz/rest/realItem/?format=json&amp;state=2')
    if resp:
        func.Stat(dbx, "PP_TOAPPROVE_COUNT", len(resp), 0, 'Pocet zadosti o proplaceni ve stavu Ke schvaleni hospodarem, REST dotazem do piroplaceni')
        if len(resp):
            resp = lmap( lambda x: (datetime.date.today() - datetime.datetime.strptime(x['updatedStamp'], "%d.%m.%Y, %H:%M").date()).days, resp)
            func.Stat(dbx, "PP_TOAPPROVE_AGE", round(sum(resp)/len(resp), 2), 0, 'Prumerne stari zadosti o proplaceni ve stavu Ke schvaleni hospodarem, REST dotazem do piroplaceni')

    # piroplaceni: prumerne stari (od data posledni upravy) zadosti ve stavu "Ke schvaleni hospodarem" nebo "Rozpracovana"
    def _counts( url ):
        resp = func.get_json(url)
        if resp and len(resp):
            resp = lmap( lambda x: (datetime.date.today() - datetime.datetime.strptime(x['updatedStamp'], "%d.%m.%Y, %H:%M").date()).days, resp)
            return (sum(resp), len(resp))

    sums = list(_counts( 'https://piroplaceni.pirati.cz/rest/realItem/?format=json&amp;state=1'))  # rozprac
    x = _counts( 'https://piroplaceni.pirati.cz/rest/realItem/?format=json&amp;state=2')  # ke schvaleni hosp
    sums[0] += x[0]
    sums[1] += x[1]
    func.Stat(dbx, "PP_UNAPPROVED_AGE", round(sums[0]/sums[1], 2), 0, 'Prumerne stari zadosti o proplaceni ve stavu Ke schvaleni hospodarem nebo Rozpracovana, pocitano od data posledni upravy. REST dotazem do piroplaceni')

    # pocet priznivcu, z fora
    stat_from_regex('PI_REGP_COUNT', 'https://forum.pirati.cz/memberlist.php?mode=group&g=74', r'<div class=\"pagination\">\s*(.*?)\s*už', "Pocet registrovanych priznivcu")

    # redmine: pocty a prumerna stari otevrenych podani pro jednotlive organizacni slozky
    redmine_issues('ao', 'AO', 'Administrativni odbor')
    redmine_issues('kancelar-strany', 'KANCL', 'Kancelar strany')
    redmine_issues('kk', 'KK', 'Kontrolni komise')
    redmine_issues('medialni-odbor', 'MO', 'Medialni odbor')
    redmine_issues('po', 'PO', 'Personalni odbor')
    redmine_issues('pravni-tym', 'PRAVNI', 'Pravni tym')
    redmine_issues('rp', 'RP', 'Republikove predsednictvo')
    redmine_issues('republikovy-vybor', 'RV', 'Republikovy vybor')
    redmine_issues('to', 'TO', 'Technicky odbor')
    redmine_issues('zo', 'ZO', 'Zahranicni odbor')

    # Zustatky na vsech transparentnich FIO uctech uvedenych na wiki FO
    content = func.getUrlContent("https://wiki.pirati.cz/fo/seznam_uctu")
    if content:
        fioAccounts = list(set(re.findall(r'[0-9]{6,15}[ \t]*/[ \t]*2010', content)))
        total = 0
        for account in fioAccounts:
            account = account.split("/")[0].strip()
            total += statFioBalance(account)
        func.Stat(dbx, "BALANCE_FIO_TOTAL", total, 0, 'Soucet zustatku na vsech FIO transparentnich uctech, sledovanych k danemu dni')

    # Pocty clenu v jednotlivych KS a celkem ve strane (prosty soucet dilcich)		
    total = 0
    for id in PIRATI_KS:
        total += statNrOfMembers(id, PIRATI_KS[id])
    func.Stat(dbx, "PI_MEMBERS_TOTAL", total, 0, 'Pocet clenu CPS celkem, jako soucet poctu clenu v KS')			

    # piratske forum
    stat_forum()
    youtubers = json.loads(func.getUrlContent('https://raw.githubusercontent.com/Jarmil1/pistat-conf/yt-rm-to-conf/youtubers.json'))
    # pocty odberatelu vybranych Youtube kanalu
    for id in youtubers:
        # odberatelu
        content = func.getUrlContent(youtubers[id][0])
        m = re.findall(r'([\xa00-9]+)[ ]+odb.{1,1}ratel', content)
        value = int(re.sub(r'\xa0','',m[0])) if m else 0
        func.Stat(dbx, id + '_SUBSCRIBERS', value, 0, "Odberatelu youtube kanalu, scrappingem verejne Youtube stranky")
        
        # shlednuti
        content = func.getUrlContent(youtubers[id][1])
        m = re.findall(r'<b>([\xa00-9]+)</b> zhl.{1,1}dnut', content)
        value = int(re.sub(r'\xa0','',m[0])) if m else 0
        func.Stat(dbx, id + '_VIEWS', value, 0, "Pocet shlednuti youtube kanalu, scrappingem verejne Youtube stranky")

    # pocty followeru a tweetu ve vybranych twitter kanalech, konfiguraci nacti z druheho gitu
    twitter_accounts = func.filter_config(func.getLines('https://raw.githubusercontent.com/Jarmil1/pistat-conf/master/twitters'))[:200]
    for id in twitter_accounts:
        content = func.getUrlContent("https://twitter.com/%s" % id)
        if content:
            m = re.findall(r'data-count=([0-9]*)', content)
            if m:
                func.Stat(dbx, "TWITTER_%s_FOLLOWERS" % id.upper() , int(m[2]), 0, "Followers uzivatele, scrappingem verejneho profilu na Twitteru (treti nalezene cislo)")   # hack, predpoklada toto cislo jako treti nalezene
                func.Stat(dbx, "TWITTER_%s_TWEETS" % id.upper() , int(m[0]), 0, "Tweets uzivatele, scrappingem verejneho profilu na Twitteru (prvni nalezene cislo)")         # hack dtto    
                if len(m)>3:
                    func.Stat(dbx, "TWITTER_%s_LIKES" % id.upper() , int(m[3]), 0, "Likes uzivatele, scrappingem verejneho profilu na Twitteru (ctvrte nalezene cislo)")          # hack dtto    
                else: 
                    print(id, "skipped: no likes found")
        else:
            print(id, "skipped: this account does not exist?")
        



        
def test():
    """ Zde se testuji nove statistiky, spousti se s parametrem -t """

    redmine_issues('ao', 'AO', 'Administrativni odbor')
    redmine_issues('kancelar-strany', 'KANCL', 'Kancelar strany')
    redmine_issues('kk', 'KK', 'Kontrolni komise')
    redmine_issues('medialni-odbor', 'MO', 'Medialni odbor')
    redmine_issues('po', 'PO', 'Personalni odbor')
    redmine_issues('pravni-tym', 'PRAVNI', 'Pravni tym')
    redmine_issues('rp', 'RP', 'Republikove predsednictvo')
    redmine_issues('republikovy-vybor', 'RV', 'Republikovy vybor')
    redmine_issues('to', 'TO', 'Technicky odbor')
    redmine_issues('zo', 'ZO', 'Zahranicni odbor')

    pass


if __name__ == '__main__':
    dbx = func.clsMySql(credentials.FREEDB, verbose=arg('v'))

    if arg('t'):
        test()
    elif arg('h'):
        message_and_exit()
    elif arg('a'):
        s = func.clsMyStat(dbx, '')
        lst = s.getAllStats()
        for l in lst:
            print(l)
    elif arg('s'):
        try:
            value = int(sys.stdin.read().strip())
        except ValueError:
            message_and_exit("ERROR: expected number on stdio")
        if value:
            func.Stat(dbx, arg('s'), value, 0, 'Neznamy puvod, importovano')
    elif arg('p'):
        stat = func.clsMyStat(dbx, arg('p'))
        stat.printLastValues()
    else:
        main()

    if arg('q'):    
        print()
        for statid in statList:
            print("SELECT $__time(date_start), value as %s FROM statistics WHERE id='%s'" % (statid, statid))
            
    dbx.close()

