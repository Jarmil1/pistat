
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from func import clsMyStat, clsMySql
import datetime
import credentials
import os

def make_graph( dbx, stat_id, filename=""):
    """ Vytvori carovy graf. Ulozi jej do souboru,
        neni-li jmeno souboru definovano, zobrazi jej
    """    

    # ziskej statistiku
    stat = clsMyStat(dbx, stat_id)
    r = stat.getLastValues(0)
    r.reverse()

    # HACK: proste hnusne, prepsat pythonic way
    X, Y = [], []
    for row in r:
        X.append('{0:%d.%m.%Y}'.format(row[0]))
        Y.append(row[1])

    # create graph
    figure(num=None, figsize=(20, 12), dpi=80, facecolor='w', edgecolor='w')
    ax = plt.axes()
    plt.plot(X, Y, 'k-', linewidth=3.0) 
    ax.xaxis.set_major_locator(plt.MaxNLocator(10))
    plt.tick_params(axis='both', which='major', labelsize=16)
    if filename:
        plt.savefig(filename)
    else:
        plt.show()
    
    # nutne pro usetreni pameti    
    plt.close()    


dbx = clsMySql(credentials.FREEDB)

dirname = 'img'
if not os.path.isdir(dirname):
    os.mkdir(dirname)

s = clsMyStat(dbx, '')
stats = s.getAllStats()
i = 0
for stat in stats:
    i += 1
    print("[%s/%s]: Creating %s.png                       \r" % (i, len(stats), stat), end = '\r')
    make_graph(dbx, stat, "%s/%s.png" % (dirname, stat) )
   
print()
   
dbx.close()

