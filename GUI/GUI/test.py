import sys
import os
from PIL import Image


path = 'C:/Projects/deep-visualization-toolbox/input_images/bee'
path2 = 'C:/Projects/deep-visualization-toolbox/input_images'

for img in os.listdir(path):
    im = Image.open(path + '/' + img)
    im = im.point(lambda p: p * 3)
    im.resize((256, 256))
    imname = img.split('.')[0]
    im.save(path2 + '/' + imname + '.jpg')
