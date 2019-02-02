#! /usr/bin/python3

""" Generuje stranky s piratskymi statistikami. Dela primitivni zalohu DB.
    Parametry:
        -h      help: vypise tuto napovedu
        -oName  jmeno vystupniho adresare, napr -o../output
        -bName  provede dummy zalohu DB do adresare Name
"""

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import func
import datetime
import credentials
import shutil
import re

LINE_COLORS = ('b', 'g', 'r', 'c', 'k')

def arg(argumentName):
    return func.getArg(argumentName,"ho:b:")
    
    
def message_and_exit(message=""):    
    if message:
        print(message)
    print(__doc__)
    exit()


def make_graph( rowlist, stat_id, filename=""):
    """ Vytvori carovy graf. Ulozi jej do souboru,
        neni-li jmeno souboru definovano, zobrazi jej
        rowlist .. list s datovymi radami
    """    

    # HACK: proste hnusne, prepsat pythonic way
    datarows = {}
    for rows in rowlist.keys():
        X, Y = [], []
        for row in rowlist[rows]:
            X.append('{0:%d.%m.%Y}'.format(row[0]))
            Y.append(row[1])
        datarows[rows] = (X,Y)

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

    func.makedir(dirname)   # hack kvuli filenotfounderror na dalsim radku
    shutil.rmtree(dirname)
    func.makedir(dirname)
    func.makedir(dirname+"/img")

    s = func.clsMyStat(dbx, '')
    stats = s.getAllStats()
    
    statnames = func.getconfig('../config/statnames')

    i, index = 0, ['','']

    # Statistiky twitteru: kombinuj do spolecneho grafu TWEETS & FOLLOWERS
    for stat in stats: 
        found = re.search(r'TWITTER_(.+?)_TWEETS', stat)
        if found: 
            statname = "TWITTER_%s" % found.group(1)
            print("Creating %s                       \r" % (statname), end = '\r')
            
            # graf
            data_tweets = get_stat_for_graph(dbx, stat)
            data_followers = get_stat_for_graph(dbx, "TWITTER_%s_FOLLOWERS" % found.group(1))
            make_graph( { "TWEETS": data_tweets, "FOLLOWERS": data_followers }, stat, "%s/img/%s.png" % (dirname, statname) )
            
            # html stranka: bez zdrojovych dat
            page = func.replace_all(func.readfile('../templates/stat_nodata.htm'),
                { '%stat_name%': statname, '%stat_desc%': '', '%stat_image%': "img/%s.png" % statname,
                '%stat_id%': statname, '%stat_date%': '{0:%d.%m.%Y %H:%M:%S}'.format(datetime.datetime.now()) } )
            func.writefile(page, "%s/%s.htm" % (dirname, statname))    
            
            index[1] += "<a href='%s.htm'>%s</a>, \n" % (statname, statname)
        
    #exit()    

    for stat in stats: 
        i += 1
        print("[%s/%s]: Creating %s                       \r" % (i, len(stats), stat), end = '\r')
        
        if not re.search(r'TWITTER_(.+)', stat):

            # ziskej statistiku a vytvor graf
            r = get_stat_for_graph(dbx, stat)
            make_graph({ "graph": r }, stat, "%s/img/%s.png" % (dirname, stat) )
            
            # najdi pro ID statistiky odpovidajici radek ve statnames, 
            # nacti z nej nazev, dulezitost...
            info = list(filter(lambda x: x.startswith('%s\t' % stat ), statnames))
            statname = info[0].split('\t')[1] if info else stat
            if statname.startswith('!'):
                important = True
                statname = statname[1:]
            else:
                important = False

            # vytvor html soubor se zobrazenim statistiky
            page = func.replace_all(func.readfile('../templates/stat.htm'),
                { '%stat_name%': statname, '%stat_desc%': '', '%stat_image%': "img/%s.png" % stat,
                  '%stat_id%': stat, '%stat_date%': '{0:%d.%m.%Y %H:%M:%S}'.format(datetime.datetime.now()) } )
            func.writefile(page, "%s/%s.htm" % (dirname, stat))    
            index[0 if important else 1] += "<a href='%s.htm'>%s</a>, \n" % (stat, statname)
            
            # vytvor CSV soubor se zdrojovymi daty
            csv_rows = [ "%s;%s;%s;" % (stat, "{:%d.%m.%Y}".format(x[0]), x[1]) for x in r ]
            func.writefile("stat_id;date;value;\n" + "\n".join(csv_rows), "%s/%s.csv" % (dirname, stat))    


    page = func.replace_all(func.readfile('../templates/index.htm'), { '%important%': index[0], '%body%': index[1] } )
    func.writefile(page, "%s/index.htm" % dirname)    

    shutil.copytree('../templates/assets', "%s/assets" % dirname)


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
        