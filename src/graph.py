
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import func
import datetime
import credentials
import shutil

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
    plt.plot(X, Y, 'k-', linewidth=3.0) 
    ax.xaxis.set_major_locator(plt.MaxNLocator(6))
    plt.tick_params(axis='both', which='major', labelsize=16)
    if filename:
        plt.savefig(filename)
    else:
        plt.show()
    
    # nutne pro usetreni pameti    
    plt.close()    


def make_pages(dbx, dirname):
    """ Nageneruj stranky a obrazky do adresare dirname """

    shutil.rmtree(dirname)
    func.makedir(dirname)
    func.makedir(dirname+"/img")
    #func.makedir(dirname+"/assets")

    s = func.clsMyStat(dbx, '')
    stats = s.getAllStats()

    i, index = 0, ""
    for stat in stats[:5]:
        i += 1
        print("[%s/%s]: Creating %s                       \r" % (i, len(stats), stat), end = '\r')
        make_graph(dbx, stat, "%s/img/%s.png" % (dirname, stat) )
        page = func.replace_all(func.readfile('../templates/stat.htm'),
            { '%stat_name%': stat, '%stat_desc%': '', '%stat_image%': "img/%s.png" % stat } )
        func.writefile(page, "%s/%s.htm" % (dirname, stat))    
        index += "<a href='%s.htm'>%s</a>\n" % (stat, stat)

    page = func.replace_all(func.readfile('../templates/index.htm'), { '%body%': index } )
    func.writefile(page, "%s/index.htm" % dirname)    

    shutil.copytree('../templates/assets', "%s/assets" % dirname)


if __name__=='__main__':
    dbx = func.clsMySql(credentials.FREEDB)
    make_pages(dbx, '../output')   
    print("Done"+' '*70)
    dbx.close()

