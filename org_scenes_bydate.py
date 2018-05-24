import os
import datetime



#basedir for the processed scenes ready for detection
root_dir = "/home/elebouder/BULKDATA/Fracking Data/RGB Scenes Ready for Site-Lifting"


for scene in os.listdir(root_dir):
    if scene.startswith('FF'):
        fscene = scene[2:]
    else:
        fscene = scene
    print scene
    year = fscene[9:13]
    julday = fscene[13:16]
    month = (datetime.datetime(int(year), 1, 1) + datetime.timedelta(int(julday)-1)).month
    filepattern = root_dir + '/{}_{}/'.format(month, year)
    if not os.path.exists(filepattern):
        os.makedirs(filepattern)
    src = root_dir + '/' + scene
    dst = filepattern + fscene
    os.rename(src, dst)


"""
for d in os.listdir(root_dir):
    for f in os.listdir(root_dir + '/' + d):
        src = root_dir + '/' + d + '/' + f
        dst = root_dir + '/' + f
        os.rename(src, dst)
"""
