import os
import setup_grassenv as setup



bands = [8, 7, 6, 8]
rgb_bands = [8, 7, 6]
bandnames =  ['B' + str(s) for s in bands] #list comprehension
reflbandnames = ['B_refl' + str(s) for s in rgb_bands]
panbandnames = ['B_refl' + str(s) for s in bands]
outputpath = 'U:/Fracking Pads/RGB Scenes Ready for Site-Lifting'
scene = 'LC80460222015190LGN00'
raw_dataset_path = 'U:/Fracking Pads/Unpacked Downloaded Products/7_2015/LC80460222015190LGN00'


def main():
    rgb_bands = [bands[0], bands[1], bands[2]]
    reflbandnames = ['B_refl' + str(s) for s in rgb_bands]
    panbandnames = ['B_refl' + str(s) for s in bands]
    outputraster = outputpath + '/' + scene + '.tif'
    location = 'genLocation'

    # remove external dlls
    os.environ['path'] = ';'.join(
        [path for path in os.environ['path'].split(";")
         if "msvcr90.dll" not in map((lambda x: x.lower()), os.listdir(path))])
    # set up grass environment
    rcfile = setup.initsetup(location)
    import preprocess_in_grass as pp
    import grass.script as grass
    # run preprocessing, classify, vectorize, create polygon masks, and save raster clips to database
    pp.reproject(raw_dataset_path, scene)
    os.remove(rcfile)
    location = scene
    rcfile = setup.initsetup(location)
    import preprocess_in_grass as pp
    import grass.script as grass
    pp.preprocess(reflbandnames, panbandnames, raw_dataset_path, outputraster, scene)
    os.remove(rcfile)
    return outputraster


def read2_command(*args, **kwargs):
    kwargs['stdout'] = grass.PIPE
    kwargs['stderr'] = grass.PIPE
    ps = grass.start_command(*args, **kwargs)
    return ps.communicate()


if __name__ == "__main__":
    main()
