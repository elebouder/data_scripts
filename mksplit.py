import os
import random
import shutil

root = '/home/elebouder/Data/landsat/'
xmlroot = root + 'ann_xml/'
imroot = root + 'ann_images_all/'
test_root = root + 'ssd_split/test/'
train_root = root + 'ssd_split/train/'

xmlbase = 'xml/'
imbase = 'images/'


trainsplit = 0.8

total = 0
for f in os.listdir(xmlroot):
    total += 1

print total

numtrain = int(trainsplit * total)
print numtrain
i = 0
while i<numtrain:
    nextf = os.listdir(xmlroot)[i]
    srcxml = xmlroot + nextf
    dstxml = train_root + xmlbase + nextf
    nextim = nextf.split('.')[0] + '.png'
    srcim = imroot + nextim
    dstim = train_root + imbase + nextim

    shutil.copyfile(srcxml, dstxml)
    shutil.copyfile(srcim, dstim)
    i += 1
    


for f in os.listdir(xmlroot):
    if f not in os.listdir(train_root + xmlbase):
        srcxml = xmlroot + f
        dstxml = test_root + xmlbase + f
        nextim = f.split('.')[0] + '.png'
        srcim = imroot + nextim
        dstim = test_root + imbase + nextim
    
        shutil.copyfile(srcxml, dstxml)
        shutil.copyfile(srcim, dstim)

