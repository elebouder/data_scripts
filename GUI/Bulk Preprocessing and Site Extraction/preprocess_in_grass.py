import grass.script as grass
import re
import os
import fnmatch


def read2_command(*args, **kwargs):
    kwargs['stdout'] = grass.PIPE
    kwargs['stderr'] = grass.PIPE
    ps = grass.start_command(*args, **kwargs)
    print ps.communicate()
    return ps.communicate()


def preprocess(reflbandnames, panbandnames, dataset, outputraster, scene):
    options, flags = grass.parser()
    pansuffix = ['red', 'green', 'blue']
    print os.environ
    importregex = re.compile('.*[.]TIF')

    counter = 1
    for file in os.listdir(dataset):
        if re.search(importregex, file):
            if len(file) == 29:
                num = file[23] + file[24]
            else:
                num = file[23]
            print num
            print dataset
            read2_command('r.external', input=dataset + '/' + file, output='B' + num, overwrite=True, flags='e')
        counter = counter + 1

    for file in os.listdir(dataset):
        if fnmatch.fnmatch(file, '*.txt'):
            mtl = file
    metfile = os.path.join(dataset, mtl)

    read2_command('i.landsat.toar', input='B', output='B_refl', metfile=metfile, sensor='oli8', overwrite=True)
    print('reflectance calculated')

    read2_command('r.colors', map=reflbandnames, flags='e', color='grey')
    print('histograms equalized')

    read2_command('i.colors.enhance', red=reflbandnames[0], green=reflbandnames[1], blue=reflbandnames[2])
    print('colors enhanced')


    # pansharpen
    read2_command('i.fusion.brovey', ms3=reflbandnames[0], ms2=reflbandnames[1], ms1=reflbandnames[2],
                      pan=panbandnames[3], overwrite=True, flags='l', output_prefix='brov')
    pannames = ['brov.' + s for s in pansuffix]
    pannames255 = [s + '_255' for s in pannames]
    print('pansharpening and composition achieved')
    read2_command('g.region', raster=pannames)
    read2_command('r.colors', map=pannames, flags='e', color='grey')
    for raster in pannames:
        minmax = grass.parse_command('r.info', map=raster, flags='r')
        print(minmax)
        newrast = raster + '_255'
        grass.write_command('r.recode', input=raster, output=newrast, rules='-',
                            stdin=minmax[u'min'] + ':' + minmax[u'max'] + ':0:255',
                            overwrite=True)
    print('rasters recoded to CELL type')
    # equalize colors once again
    read2_command('r.colors', map=[pannames255[0], pannames255[1], pannames255[2]], flags='e', color='grey')
    read2_command('i.colors.enhance', red=pannames255[0], green=pannames255[1], blue=pannames255[2])
    #read2_command('r.composite', red=pannames[0], green=pannames[1], blue=pannames[2], output='comp',
    #                 overwrite=True)

    # create imagery group
    read2_command('i.group', group='pangroup876', subgroup='pangroup876', input=pannames255)
    print('created imagery group')

    read2_command('r.out.gdal', input='pangroup876', output=outputraster,
                  overwrite=True, format='GTiff', type='Byte', flags='fm')

def reproject(raw_dataset_path, scene):
    #import subprocess, os
    lfile = os.listdir(raw_dataset_path)
    lfile = lfile[0]
    #batpath = "C:/Program Files/GRASS GIS 7.2.0/grass72.bat"
    #input = raw_dataset_path + '/' + lfile
    #cmd = " %s -c %s U:/grassdata/%s/PERMANENT" % (batpath, input, scene)
    #subprocess.call(cmd, shell=True)
    options, flags = grass.parser()

    read2_command('r.in.gdal', input=raw_dataset_path + '/' + lfile, output='B1', overwrite=True, flags='c',
                  location=scene)
    print 'reprojected to ', scene


