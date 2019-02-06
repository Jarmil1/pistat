#! /usr/bin/python3

""" Generuje stranky s piratskymi statistikami. Dela primitivni zalohu DB.
    Parametry:
        -h      help: vypise tuto napovedu
        -oName  jmeno vystupniho adresare, napr -o../output
        -bName  provede dummy zalohu DB do adresare Name
"""

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import datetime
import shutil
import re

import credentials
import func
import html

LINE_COLORS = ('b', 'g', 'r', 'c', 'm', 'y', 'k')

def arg(argumentName):
    return func.getArg(argumentName,"ho:b:")
    
    
def message_and_exit(message=""):    
    if message:
        print(message)
    print(__doc__)
    exit()


def make_graph( rowlist, filename=""):
    """ Vytvori carovy graf. Ulozi jej do souboru,
        neni-li jmeno souboru definovano, zobrazi jej
        rowlist .. list s datovymi radami
    """    

    # HACK: proste hnusne, prepsat pythonic way
    datarows = {}
    for rowname in rowlist.keys():
        X, Y = [], []
        for row in rowlist[rowname]:
            X.append('{0:%d.%m.%Y}'.format(row[0]))
            Y.append(row[1])
        datarows[rowname] = (X,Y)

    # create graph
    figure(num=None, figsize=(16, 10), dpi=80, facecolor='w', edgecolor='w')
    ax = plt.axes()
    ax.xaxis.set_major_locator(plt.MaxNLocator(6))  # pocet ticku na X ose
    
    i = 0
    for key in datarows.keys():
        plt.plot(datarows[key][0], datarows[key][1], '%s-' % LINE_COLORS[i], linewidth=4.0, label=key) 
        i += 1
        
    ax.spines['top'].set_visible(False)             # odstran horni a pravy ramecek grafu
    ax.spines['right'].set_visible(False)
    plt.ylim(bottom=0)                              # osa Y zacina vzdy od nuly
    plt.ticklabel_format(style='plain', axis='y')
    plt.tick_params(axis='both', which='major', labelsize=16) # velikost fontu na osach

    if len(rowlist) > 1: 
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

    func.makedir(dirname)   # hack kvuli filenotfounderror na dalsim radku
    shutil.rmtree(dirname)
    func.makedir(dirname)
    func.makedir(dirname+"/img")

    s = func.clsMyStat(dbx, '')
    stats = s.getAllStats()
    
    i, statnames, groups = 0, {}, {}

    # vytvor ve trech krocich seznam vsech generovanych grafu:
    
    # 1) nacti ty z konfigurace, preved na hashtabulku
    mixed_graphs = {}
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
            statnames[statid] = "Twitter %s" % found.group(1) # default name
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
        paragraph = ''
        for statid in groups[groupname]:
            statname = statnames[statid] if statid in statnames.keys() else statid
            paragraph += html.a("%s.htm" % statid, statname) + '\n'
        mybody += html.h2(groupname) + html.p(paragraph)
        
    page = func.replace_all(func.readfile('../templates/index.htm'), { '%body%': mybody } )
    func.writefile(page, "%s/index.htm" % dirname)    
    shutil.copytree('../templates/assets', "%s/assets" % dirname)

            
    # Vytvor vsechny kombinovane grafy, vynech statistiky s nejvyse jednou hodnotou
    for statid in mixed_graphs: 

        i += 1

        # graf
        involved_stats = {}
        for invstat in mixed_graphs[statid]:
            involved_stats[invstat] = get_stat_for_graph(dbx, invstat)
            
        singlestat = (len(involved_stats.values()) == 1)
            
        if max(list(map(len,involved_stats.values()))) > 1: # involved_stats musi obsahovat aspon 1 radu o >=2 hodnotach

            print("[%s/%s]: Creating %s                       \r" % (i, len(mixed_graphs), statid), end = '\r')
            make_graph( involved_stats, "%s/img/%s.png" % (dirname, statid) )
            
            # najdi nazev statistiky
            statname = statnames[statid] if statid in statnames.keys() else statid

            # html stranka
            page = func.replace_all(func.readfile('../templates/stat.htm' if singlestat else '../templates/stat_nodata.htm' ),
                { '%stat_name%': statname, '%stat_desc%': '', '%stat_image%': "img/%s.png" % statid,
                '%stat_id%': statid, '%stat_date%': '{0:%d.%m.%Y %H:%M:%S}'.format(datetime.datetime.now()) } )
            func.writefile(page, "%s/%s.htm" % (dirname, statid))    

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
        