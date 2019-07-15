#! /usr/bin/python3

""" Generuje stranky s piratskymi statistikami. Dela primitivni zalohu DB.
    Parametry:
        -h      help: vypise tuto napovedu
        -oName  jmeno vystupniho adresare, napr -o../output
        -bName  provede dummy zalohu DB do adresare Name
        -sName  pouze statistiku Name
"""

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import datetime
import shutil
import re
import operator

import credentials
import func
import html

LINE_COLORS = ('b', 'g', 'r', 'c', 'm', 'y', 'k')

def arg(argumentName):
    return func.getArg(argumentName,"ho:b:s:")
    
    
def merge_dicts(x, y):
    """ Slouci dva slovniky do jednoho a vrati vysledek. """
    z = x.copy()   
    z.update(y)    
    return z

    
def message_and_exit(message=""):    
    if message:
        print(message)
    print(__doc__)
    exit()


def get_oldest_timeline(rowlist_in):
    """ Vraci klic te casove rady, ktera ma nejstarsi datum """
    oldest_date, oldest_id, lastkey = datetime.datetime.now().date(), None, None
    rowlist = rowlist_in
    for id in rowlist:
        lastkey = id
        datelist = list(map(lambda x: x[0], rowlist[id]))
        if datelist:
            oldest_in_row = min(datelist)
            if oldest_in_row<oldest_date:
                oldest_date = oldest_in_row
                oldest_id = id
    return oldest_id if oldest_id else lastkey
    
    
class Stat():
    """ Pro slozitejsi manipulace se statistikou """

    def __init__(self, name, values):
        self.name = name
        self.values = list(values)
        
    def max(self):
        """ vrat nejvyssi hodnotu statistiky nebo None, je-li soubor prazdny """
        return max(map(lambda x: x[1], self.values)) if self.values else None

    def min(self):
        """ vrat nejnizzsi hodnotu statistiky nebo None, je-li soubor prazdny """
        return min(map(lambda x: x[1], self.values)) if self.values else None

    def oldest(self):
        """ vrat nejstarsi datum souboru dat nebo None, je-li soubor prazdny"""
        return min(map(lambda x: x[0], self.values)) if self.values else None

    def newest(self):
        """ vrat nejnovejsi datum souboru dat nebo None, je-li soubor prazdny """
        return max(map(lambda x: x[0], self.values)) if self.values else None
        
    def fill_range(self, min, max, value=None):
        """ dopln do souboru dat chybejici hodnoty z rozsahu min-max, vcetne.
            vysledek setrid podle data
        """

        just_dates = list(map(lambda x: x[0], self.values))

        startdate = min
        while startdate <= max:
            startdate += datetime.timedelta(days=1)
            if not startdate in just_dates:
                self.values.append( [startdate, value] )
        
        newvalues = [ list(x) for x in self.values ]
        
        newvalues.sort()
        self.values = newvalues
            
        

def make_graph( rowlist, filename=""):
    """ Vytvori carovy graf. Ulozi jej do souboru,
        neni-li jmeno souboru definovano, zobrazi jej
        rowlist .. list s datovymi radami
    """    

    rowlist_count = len(rowlist)
    minimal_value = min(list(map(lambda x: x[1], sum(list(rowlist.values()),[]))))

    # datove rady mohou obsahovat chubejici hodnoty, diky nimz 
    # graf vypada zmatene. Je treba data normalizovat:
    # preved data na objekty Stat, zjisti rozsah dat, normalizuj 
    # zabudovanou funkci a preved zpet na rowlist 
    stats = []
    for row in rowlist:
        stats.append(Stat(row, rowlist[row]))
    
    oldest_date = min(filter(lambda x: x, map(lambda x: x.oldest(), stats)))
    newest_date = max(filter(lambda x: x, map(lambda x: x.newest(), stats)))

    rowlist = {}
    for s in stats:
        s.fill_range(oldest_date, newest_date)
        rowlist[s.name] = s.values
        

    # create graph
    figure(num=None, figsize=(16, 10), dpi=80, facecolor='w', edgecolor='w')
    ax = plt.axes()
    ax.xaxis.set_major_locator(plt.MaxNLocator(6))  # pocet ticku na X ose
    
    i = 0
    while len(rowlist.keys()):
        X, Y, oldest = [], [], get_oldest_timeline(rowlist)
        for row in rowlist[oldest]:
            X.append('{0:%d.%m.%Y}'.format(row[0]))
            Y.append(row[1])
        plt.plot(X, Y, '%s-' % LINE_COLORS[i], linewidth=4.0, label=oldest) 
        rowlist = {i:rowlist[i] for i in rowlist if i!=oldest}
        i += 1
        
    ax.spines['top'].set_visible(False)             # odstran horni a pravy ramecek grafu
    ax.spines['right'].set_visible(False)
    if minimal_value > 0:                           # osa Y zacina od nuly u kladnych grafu
        plt.ylim(bottom=0)                              
    plt.ticklabel_format(style='plain', axis='y')
    plt.tick_params(axis='both', which='major', labelsize=16) # velikost fontu na osach

    if rowlist_count > 1: 
        ax.legend()

    if filename:
        plt.savefig(filename, bbox_inches='tight')
    else:
        plt.show()
    
    plt.close()   # pri vetsim poctu grafu nutne (memory leak)  


def get_stat_for_graph(dbx, stat):
    """ Vrati seznam: vsechna data grafu, nejstarsi prvni """
    stat_object = func.clsMyStat(dbx, stat)
    r = stat_object.getLastValues(0)
    r.reverse()
    return r


def make_pages(dbx, dirname):
    """ Nageneruj stranky a obrazky do adresare dirname """

    def add_stat_to_group(groups, groupname, statid):
        try:
            groups[groupname].append(statid)
        except KeyError:
            groups[groupname] = [statid]
            
    def stat_min_date(stat):
        ''' vrat nejmensi datum v datove rade statistiky stat = [ (datum, hodnota), (datum, hodnota) ...] '''
        return min(list(map(lambda x: x[0],stat))) if stat else None

    def stat_max_date(stat):
        ''' obdobne vrat nejvetsi datum '''
        return max(list(map(lambda x: x[0],stat))) if stat else None

    func.makedir(dirname)   # hack kvuli filenotfounderror na dalsim radku
    shutil.rmtree(dirname)
    func.makedir(dirname)
    func.makedir(dirname+"/img")

    s = func.clsMyStat(dbx, '')
    stats = s.getAllStats()
    
    i, statnames, statnames_index, groups = 0, {}, {}, {}

    # vytvor seznam vsech generovanych grafu:
    mixed_graphs = {}
    
    # pridej automaticky vytvareny seznam nejvice tweetujicich uzivatelu
    best_twitters = {}
    for stat in stats: 
        if re.search(r'TWITTER_(.+?)_TWEETS', stat):
            mystat = Stat(stat, get_stat_for_graph(dbx, stat))
            best_twitters[stat] = mystat.max()
    sorted_twitters = sorted(best_twitters.items(), key=operator.itemgetter(1))[-7:]
    stat_id = 'BEST_TWITTERS'
    mixed_graphs[stat_id] = [ x[0] for x in sorted_twitters]
    add_stat_to_group( groups, 'Porovnání', stat_id)
            
    # 1) nacti ty z konfigurace, preved na hashtabulku
    for line in func.getconfig('../config/graphs'):
        lineparts = list(map(str.strip,line.split(' ')))
        mixed_graphs[lineparts[0]] = lineparts[1:]
        statnames[lineparts[0]] = lineparts[0]
        add_stat_to_group( groups, 'Porovnání', lineparts[0])
    
    # 2) pridej automaticky vytvarene twitter kombinovane grafy
    # TWEETS, FOLLOWERS a LIKES
    for stat in stats: 
        found = re.search(r'TWITTER_(.+?)_TWEETS', stat)
        if found: 
            statid = "TWITTER_%s" % found.group(1)
            mixed_graphs[statid] = [ stat, "TWITTER_%s_FOLLOWERS" % found.group(1), 
                "TWITTER_%s_LIKES" % found.group(1) ]
            statnames[statid] = "Twitter %s" % found.group(1)   # default jmeno
            statnames_index[statid] = "%s" % found.group(1)     # default jmeno na titulni stranku
            add_stat_to_group( groups, 'Twitteři', statid)

    # 3) pridej vsechny ostatni statistiky, vynechej TWITTERY
    # vytvor ponekud nesystemove defaultni nazvy
    for stat in stats: 
        if not re.search(r'TWITTER_(.+)', stat):
            mixed_graphs[stat] = [ stat ]
            found = re.search(r'BALANCE_(.+)', stat)
            if found: 
                statnames[stat] = "Zůstatek %s" % found.group(1) 
                add_stat_to_group( groups, 'Finance', stat)
                continue
            found = re.search(r'PI_MEMBERS_(.+)', stat)
            if found: 
                statnames[stat] = "Počet členů %s" % found.group(1) 
                add_stat_to_group( groups, 'Členové', stat)
                continue
            found = re.search(r'YOUTUBE_(.+)', stat)
            if found: 
                statnames[stat] = "Youtube %s" % found.group(1) 
                add_stat_to_group( groups, 'Youtube', stat)
                continue
            found = re.search(r'PP_(.+)', stat)
            if found: 
                add_stat_to_group( groups, 'Kancelář', stat)
                continue
            add_stat_to_group( groups, 'Ostatní', stat)
                
    # donacti jmena statistik z konfigurace
    for line in func.getconfig('../config/statnames'):
        try:
            (a, b) = line.split('\t',2)
            statnames[a] = b
        except ValueError:
            pass

    # titulni stranka & assets
    mybody = ""
    for groupname in groups:
        paragraph = []
        for statid in groups[groupname]:
            if statid in statnames_index.keys():
                statname = statnames_index[statid] 
            elif statid in statnames.keys():
                statname = statnames[statid] 
            else:
                statname = statid
            paragraph.append(html.a("%s.delta.htm" % statid, statname))
        paragraph.sort()
        mybody += html.h2(groupname) + html.p(",\n".join(paragraph))
        
    page = func.replace_all(func.readfile('../templates/index.htm'), 
        { '%body%': mybody, '%stat_date%': '{0:%d.%m.%Y %H:%M:%S}'.format(datetime.datetime.now()) } )
    func.writefile(page, "%s/index.htm" % dirname)    
    shutil.copytree('../templates/assets', "%s/assets" % dirname)

    # Vytvor vsechny kombinovane grafy, vynech statistiky s nejvyse jednou hodnotou
    for statid in mixed_graphs: 

        if arg('s') and statid!=arg('s'):
            continue
            
        i += 1

        # graf
        involved_stats, involved_deltas = {}, {}
        statInstances = []
        for invstat in mixed_graphs[statid]:
            tmpstat = get_stat_for_graph(dbx, invstat)
            involved_stats[invstat] = tmpstat
            statInstances.append(Stat(invstat, involved_stats[invstat]))
            
            # spocitej delta statistiku 
            deltastat, lastvalue = [], None
            for entry in tmpstat:
                deltastat.append([entry[0], 0 if lastvalue is None else entry[1] - lastvalue])
                lastvalue = entry[1]
            involved_deltas[invstat] = deltastat
        
        singlestat = (len(involved_stats.values()) == 1)
            
        if max(list(map(len,involved_stats.values()))) > 1: # involved_stats musi obsahovat aspon 1 radu o >=2 hodnotach

            print("[%s/%s]: Creating %s                       \r" % (i, len(mixed_graphs), statid), end = '\r')
            
            # zakladni a delta graf
            make_graph( involved_stats, "%s/img/%s.png" % (dirname, statid) )
            make_graph( involved_deltas, "%s/img/%s.delta.png" % (dirname, statid) )
            
            # html stranka
            statname = statnames[statid] if statid in statnames.keys() else statid
            min_date = min(list(map(stat_min_date, filter(lambda x: x, involved_stats.values()))))   # rozsah dat
            max_date = max(list(map(stat_max_date, filter(lambda x: x, involved_stats.values()))))
            bottom_links = (html.a("%s.csv" % statid, "Zdrojová data ve formátu CSV") + html.br()) if singlestat else ""
            bottom_links += html.a("index.htm", "Všechny statistiky")
            try:
                min_value = str(min(map( lambda x: x.min(), statInstances)))
            except TypeError:
                min_value = '-'
            try:
                max_value = str(max(map( lambda x: x.max(), statInstances)))
            except TypeError:
                max_value = '-'

            common_replaces = { '%stat_name%': statname, '%stat_desc%': '', '%stat_id%': statid, 
                  '%stat_date%': '{0:%d.%m.%Y %H:%M:%S}'.format(datetime.datetime.now()),
                  '%bottomlinks%': bottom_links, '%daterange%': '%s - %s' % (min_date, max_date),
                  '%max%': max_value, '%min%': min_value
            }
            
            page = func.replace_all(func.readfile('../templates/stat.htm'), merge_dicts(common_replaces, { '%stat_image%': "img/%s.png" % statid, '%stat_type%': "Absolutní hodnoty" } ) )
            func.writefile(page, "%s/%s.htm" % (dirname, statid))    
            page = func.replace_all(func.readfile('../templates/stat.htm'), merge_dicts( common_replaces, { '%stat_image%': "img/%s.delta.png" % statid, '%stat_type%': "Denní přírůstky (delta)" } ) )
            func.writefile(page, "%s/%s.delta.htm" % (dirname, statid))    

            # vytvor CSV soubor se zdrojovymi daty
            if singlestat:
                csv_rows = [ "%s;%s;%s;" % (statid, "{:%d.%m.%Y}".format(x[0]), x[1]) for x in list(involved_stats.values())[0] ]
                func.writefile("stat_id;date;value;\n" + "\n".join(csv_rows), "%s/%s.csv" % (dirname, statid))    


def dummy_backup_db(dbx, dirname):
    """ Primitivni zaloha db do adresare dirname """
    print("(dummy) database backup to %s" % dirname)

    func.makedir(dirname)   # hack kvuli filenotfounderror na dalsim radku
    shutil.rmtree(dirname)
    func.makedir(dirname)
    
    s = func.clsMyStat(dbx, '')
    for stat in s.getAllStats():
        stat_object = func.clsMyStat(dbx, stat)
        r = stat_object.getLastValues(0)
        r = [ "\t".join(('{0:%d.%m.%Y}'.format(x[0]), str(x[1]))) for x in r]
        func.writefile("\n".join(r), "%s/%s" % (dirname, stat))


if __name__=='__main__':
    if arg('h'):
        message_and_exit()
    elif not arg('o') and not arg('b'):        
        message_and_exit("error: missing argument. specify -o or -b")
    else:        
        dbx = func.clsMySql(credentials.FREEDB)
        if arg('o'):
            make_pages(dbx, arg('o'))   
            print("Done"+' '*70)
        if arg('b'):
            dummy_backup_db(dbx, arg('b'))
        dbx.close()
        