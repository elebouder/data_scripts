import caffe
import matplotlib.pyplot as plt
import numpy as np
import scipy
from PIL import Image
from test import BBOX
import os
import cv2

"""
This can be merged with class caffenet in sliding_win.py at some point
"""
class GAPnet:

    def __init__(self):

        self.caffe_root = 'C:/Projects/caffe/'
        # Load the Alexnet_modded-GAP network.
        self.net = caffe.Net(self.caffe_root + 'models/bvlc_alexnet/build 1.8/GAPnet/deploy.prototxt',
                             self.caffe_root +
                             'models/bvlc_alexnet/build 1.8/GAPnet/caffe_alexnet_train_iter_20000.caffemodel',
                             caffe.TEST)

        self.set_transformer()

    def forwards_pass(self, data_array):
        self.data_array = data_array
        # make classification map by forward and print prediction indices at each location
        out = self.net.forward_all(data=np.asarray([self.transformer.preprocess('data', data_array)]))
        pred = out['prob'][0].argmax(axis=0)
        print pred
        # show net input and confidence map (probability of the top prediction at each location)
        plot = self.transformer.deprocess('data', self.net.blobs['data'].data[0])

        return pred, plot

    def set_transformer(self):

        self.transformer = caffe.io.Transformer({'data': self.net.blobs['data'].data.shape})
        self.transformer.set_mean('data', np.load(self.caffe_root + '/data/L8_all/mean.npy').mean(1).mean(1))
        self.transformer.set_transpose('data', (2, 0, 1))
        self.transformer.set_channel_swap('data', (2, 1, 0))
        self.transformer.set_raw_scale('data', 255.0)

    def calc_CAM(self):
        self.class_weights = self.net.params['fc9'][0].data
        conv_outputs = self.net.blobs['convfc7'].data
        self.conv_outputs = conv_outputs[0, :, :, :]
        self.cam = np.zeros(dtype=np.float32, shape=self.conv_outputs.shape[1:3])
        target_class = 1
        for i, w in enumerate(self.class_weights[target_class, :]):
            self.cam += w * self.conv_outputs[i, :, :]
        # self.cam = scipy.ndimage.interpolation.rotate(self.cam, 270)
        return self.cam

    def display(self):
        plt.rcParams['figure.figsize'] = (10, 10)
        plt.rcParams['image.interpolation'] = 'bicubic'
        feat = self.net.blobs['prob'].data[0]
        plt.subplot(2, 1, 1)
        plt.plot(feat.flat)
        plt.title('Softmax')
        plt.draw()
        plt.subplot(2, 2, 3)
        plt.imshow(self.data_array)
        plt.subplot(2, 2, 4)
        plt.imshow(self.cam)
        plt.show()
        plt.imsave("C:\Users\Admin\Pictures\CAMs/cam.jpg", self.cam)
        im = Image.open("C:\Users\Admin\Pictures\CAMs/cam.jpg")
        im = im.resize((300, 300), Image.ANTIALIAS)
        im.save("C:\Users\Admin\Pictures\CAMs/cam.jpg")

    def get_cam(self):
        plt.imsave("C:\Users\Admin\Pictures\CAMs/cam.jpg", self.cam)
        im = Image.open("C:\Users\Admin\Pictures\CAMs/cam.jpg")
        im = im.resize((300, 300), Image.ANTIALIAS)
        im.save("C:\Users\Admin\Pictures\CAMs/cam.jpg")
        im = cv2.imread("C:\Users\Admin\Pictures\CAMs/cam.jpg", cv2.IMREAD_GRAYSCALE)
        return im


caffe_root = 'C:/Projects/caffe/'
net = GAPnet()
path = caffe_root + "examples/landsat"
for img in os.listdir(path):
    if img.endswith('tif'):
        image = caffe.io.load_image(path + '/' + img)
        net.forwards_pass(image)
        net.calc_CAM()
        cam = net.get_cam()
        image = Image.open(path + '/' + img).resize((300, 300), Image.ANTIALIAS)
        bbox = BBOX(cam, image)
        bbox.gen_thresh()
        bbox.gen_bbox()
        bbox.display()
