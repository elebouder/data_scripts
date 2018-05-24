import localize as loc
import numpy as np
import cv2
import localize as loc
import caffe
import os
from skimage.transform import resize


class Transform:
    def __init__(self, meanfile, empty_array):
        self.mean = np.load(meanfile).mean(1).mean(1)
        self.net = loc.GAPnet(1)
        self.datum = empty_array
        self.dir = os.path.dirname(__file__)
        self.iot = self.dir + '/' + 'iotransformer.csv'
        self.t = self.dir + '/' + 'transformer.csv'
        

    # @profile
    def CVtransform(self):
        datum = self.datum.copy()
        datum = cv2.resize(datum, (227, 227), interpolation=cv2.INTER_CUBIC)
        # datum = resize(datum, [227, 227])
        datum = np.swapaxes(datum, 0, 2)
        datum = datum[::-1, :, :]
        datum *= 255
        datum[2, :, :] = datum[2, :, :] - self.mean[2]
        datum[1, :, :] = datum[1, :, :] - self.mean[1]
        datum[0, :, :] = datum[0, :, :] - self.mean[0]
        print datum
        return datum

    def caffeIOtransform(self):
        datum = self.datum.copy()
        self.iotransformer = caffe.io.Transformer({'data': self.net.net.blobs['data'].data.shape})
        self.iotransformer.set_mean('data', self.mean)
        self.iotransformer.set_transpose('data', (2, 0, 1))
        self.iotransformer.set_channel_swap('data', (2, 1, 0))
        self.iotransformer.set_raw_scale('data', 255.0)
        datum = np.asarray([self.iotransformer.preprocess('data', datum)]).astype(np.float32)
        print 'next'
        print datum

        return datum

empty_array = np.random.rand(50, 50, 3) * 10
print empty_array
t = Transform('C:/Projects/caffe/data/L8_all/mean.npy', empty_array)
print 'next'
t.CVtransform()
t.caffeIOtransform()
