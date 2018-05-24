import prepMTD as mtd
import downloadUnpack as du
import os

def main(startdate):


    enddate = []
    cloudcover = 25.00

    metafile, scenelist = decide(startdate, enddate, cloudcover)

    print metafile
    print scenelist


def decide(startdate, enddate, cloudcover):
    account = 'Etienne Le Bouder'
    passwd = 'C130Hercules'

    if not enddate:
        month = startdate[0]
        year = startdate[1]
    outputdir = 'U:/Fracking Pads/Unpacked Downloaded Products/%s_%s' % (month, year)
    if os.path.exists(outputdir):
        return 1
    else:
        os.makedirs(outputdir)
    metafile_rough, scenereqlist_rough, roughdict, metafields = mtd.search_mtd(month, year, cloudcover)

    checkval, txt, mcsv = mtd.refine_mtd(roughdict, month, year, metafields)

    if checkval == 1:
        meta_csv = mcsv
        scenelist = txt
    elif checkval == 2:
        meta_csv = metafile_rough
        scenelist = scenereqlist_rough

    p, rlocation = du.download_list(scenelist, account, passwd, outputdir)
    print ('final data')
    print p, rlocation, meta_csv, scenelist

    return meta_csv, scenelist


if __name__ == '__main__':
    listofmonths = [[2, 2014], [8, 2014], [5, 2016]]
    for l in listofmonths:
        main(l)

##TODO: delete rough meta and list once you have the refined version
## TODO: take care of checking if the data already exists in file (smooth exit)
## TODO: handle multiple continuous months as well as one month