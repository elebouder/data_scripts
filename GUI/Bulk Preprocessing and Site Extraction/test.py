import subprocess
import os
import re
import sys
dataset = 'U:/Fracking Pads/Unpacked Downloaded Products/7_2015/LC80490222015211LGN00'
os.environ['path'] = ';'.join(
    [path for path in os.environ['path'].split(";")
     if "msvcr90.dll" not in map((lambda x: x.lower()), os.listdir(path))])

def initsetup(location):
    location = 'LC80490222015211LGN00'
    #Define grass database
    gisdb = os.path.join(os.path.expanduser("~"), "U:/grassdata")
    mapset = "PERMANENT"

    #path to GRASS GIS launch script
    grass7bin = r'C:\Program Files\GRASS GIS 7.2.0\grass72.bat'

    #Query GRASS GIS for GISBASE
    startcmd = [grass7bin, '--config', 'path']
    try:
        p = subprocess.Popen(startcmd,
                             shell=False,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=True)
        out, err = p.communicate()

    except OSError as error:
        sys.exit("ERROR: Cannot find GRASS GIS start script"
                 "{cmd}: {error}"
                 .format(cmd=startcmd[0], error=error))
    if p.returncode != 0:
        sys.exit("ERROR: Issues running GRASS GIS start script")
    gisbase =out.strip(os.linesep)

    #set GISBASE environment variable
    os.environ['GISBASE'] = gisbase

    #define GRASS Python environment
    grass_pydir = os.path.join(gisbase, "etc", "python")
    sys.path.append(grass_pydir)

    #import some GRASS Python bindings
    import grass.script as grass
    import grass.script.setup as gsetup

    #launch session
    rcfile = gsetup.init(gisbase, gisdb, location, mapset)
    #gscript.setup.set_gui_path()

    grass.message("Current GRASS GIS environment:")
    print os.environ
    print(grass.gisenv())

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

    os.remove(rcfile)
def read2_command(*args, **kwargs):
    import grass.script as grass
    kwargs['stdout'] = grass.PIPE
    kwargs['stderr'] = grass.PIPE
    ps = grass.start_command(*args, **kwargs)
    print ps.communicate()
    return ps.communicate()

initsetup('trash')
