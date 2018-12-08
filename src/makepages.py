#! /usr/bin/python3

""" Generuje stranky s piratskymi statistikami
    Parametry:
        -h      help: vypise tuto napovedu
        -oName  jmeno vystupniho adresare, napr -o../output
"""

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import func
import datetime
import credentials
import shutil

def arg(argumentName):
    return func.getArg(argumentName,"ho:")
    
    
def message_and_exit(message=""):    
    if message:
        print(message)
    print(__doc__)
    exit()


def make_graph( dbx, stat_id, filename=""):
    """ Vytvori carovy graf. Ulozi jej do souboru,
        neni-li jmeno souboru definovano, zobrazi jej
    """    

    # ziskej statistiku
    stat = func.clsMyStat(dbx, stat_id)
    r = stat.getLastValues(0)
    r.reverse()

    # HACK: proste hnusne, prepsat pythonic way
    X, Y = [], []
    for row in r:
        X.append('{0:%d.%m.%Y}'.format(row[0]))
        Y.append(row[1])

    # create graph
    figure(num=None, figsize=(16, 10), dpi=80, facecolor='w', edgecolor='w')
    ax = plt.axes()
    ax.xaxis.set_major_locator(plt.MaxNLocator(6))  # pocet ticku na X ose
    plt.plot(X, Y, 'k-', linewidth=3.0) 
    plt.tick_params(axis='both', which='major', labelsize=16) # velikost fontu na osach
    if filename:
        plt.savefig(filename, bbox_inches='tight')
    else:
        plt.show()
    
    plt.close()   # pri vetsim poctu grafu nutne (memory leak)  


def make_pages(dbx, dirname):
    """ Nageneruj stranky a obrazky do adresare dirname """

    func.makedir(dirname)   # hack kvuli filenotfounderror na dalsim radku
    shutil.rmtree(dirname)
    func.makedir(dirname)
    func.makedir(dirname+"/img")

    s = func.clsMyStat(dbx, '')
    stats = s.getAllStats()
    
    statnames = func.readfile('../config/statnames').split('\n')

    i, index = 0, ['','']
    for stat in stats: 
        i += 1
        print("[%s/%s]: Creating %s                       \r" % (i, len(stats), stat), end = '\r')

        make_graph(dbx, stat, "%s/img/%s.png" % (dirname, stat) )
        
        # najdi pro ID statistiky odpovidajici radek ve statnames, 
        # nacti z nej nazev, dulezitost...
        info = list(filter(lambda x: x.startswith('%s\t' % stat ), statnames))
        statname = info[0].split('\t')[1] if info else stat
        if statname.startswith('!'):
            important = True
            statname = statname[1:]
        else:
            important = False

        page = func.replace_all(func.readfile('../templates/stat.htm'),
            { '%stat_name%': statname, '%stat_desc%': '', '%stat_image%': "img/%s.png" % stat,
              '%stat_date%': '{0:%d.%m.%Y}'.format(datetime.datetime.now()) } )
        func.writefile(page, "%s/%s.htm" % (dirname, stat))    
        index[0 if important else 1] += "<a href='%s.htm'>%s</a>, \n" % (stat, statname)

    page = func.replace_all(func.readfile('../templates/index.htm'), { '%important%': index[0], '%body%': index[1] } )
    func.writefile(page, "%s/index.htm" % dirname)    

    shutil.copytree('../templates/assets', "%s/assets" % dirname)


if __name__=='__main__':
    if arg('h'):
        message_and_exit()
    elif not arg('o'):        
        message_and_exit("ERROR: missing argument -o")
    else:        
        dbx = func.clsMySql(credentials.FREEDB)
        make_pages(dbx, arg('o'))   
        print("Done"+' '*70)
        dbx.close()
        