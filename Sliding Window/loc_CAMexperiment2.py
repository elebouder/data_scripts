#!ProgramData/Anaconda2/python

import caffe
import matplotlib.pyplot as plt
import numpy as np
import scipy
from PIL import Image
import math
import os
import cv2
import numpy
import numpy.ma as ma




class GAPnet:

    def __init__(self, batch):
        caffe.set_mode_gpu()
        caffe.set_device(0)
        self.caffe_root = 'C:/Projects/caffe/'
        # Load the Alexnet_modded-GAP network.
        self.net = caffe.Net(self.caffe_root + 'models/bvlc_alexnet/build 1.8/GAPnet2classes/deploy.prototxt',
                             self.caffe_root +
                             'models/bvlc_alexnet/build 1.8/GAPnet2classes/caffe_alexnet_train_iter_40000.caffemodel',
                             caffe.TEST)
        self.batch = batch


    # @profile
    def forwards_pass(self, data_array):

        self.data_array = data_array
        self.net.blobs['data'].reshape(self.batch, 3, 227, 227)
        # make classification map by forward and print prediction indices at each location
        for i in range(self.batch):
            self.net.blobs['data'].data[i, ...] = data_array[i]
        out = self.net.forward_all(data=self.net.blobs['data'].data)
        pred = out['prob']
        preds = []
        [preds.append(i.argmax(axis=0)) for i in pred]
        # show net input and confidence map (probability of the top prediction at each location)
        # plot = self.transformer.deprocess('data', self.net.blobs['data'].data[0])

        return preds



    def calc_CAM(self, i):
        #print self.net.params['fc9'][0].data
        #print 'shape2', self.net.blobs['convfc7'].data[i].shape
        self.class_weights = self.net.params['fc9'][0].data
        conv_outputs = self.net.blobs['convfc7'].data[i]
        self.conv_outputs = conv_outputs[:, :, :]
        self.cam = np.zeros(dtype=np.float32, shape=self.conv_outputs.shape[1:3])
        self.outputs = np.zeros(dtype=np.float32, shape=self.conv_outputs.shape[1:3])
        target_class = 1
        for i, w in enumerate(self.class_weights[target_class, :]):
            if i == 1 or i == 612:
                self.cam += w * self.conv_outputs[i, :, :]
                self.outputs += self.conv_outputs[i, :, :]
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

    def get_outputs(self):
        plt.imsave("C:\Users\Admin\Pictures\CAMs/outputs.jpg", self.outputs)
        im = Image.open("C:\Users\Admin\Pictures\CAMs/outputs.jpg")
        im = im.resize((300, 300), Image.ANTIALIAS)
        im.save("C:\Users\Admin\Pictures\CAMs/outputs.jpg")
        im = cv2.imread("C:\Users\Admin\Pictures\CAMs/outputs.jpg", cv2.IMREAD_GRAYSCALE)
        return im




class BBOX:

    def __init__(self, cam, img, outputs):
        self.outputs = outputs
        img = img.point(lambda p: p * 2)
        self.img = numpy.array(img)
        im = cv2.medianBlur(cam, 5)
        # getextrema works only if single-band
        min = im.min()
        max = im.max()
        self.thresholdlow = min + ((max - min) * 0.60)
        self.thresholdhigh = min + ((max - min) * 0.80)
        self.blur = cv2.GaussianBlur(im, (5, 5), 0)


    def display(self):
        disp_datum2 = cv2.resize(self.img, (300, 300), interpolation=Image.ANTIALIAS)
        disp_outputs = cv2.resize(self.outputs, (300, 300), interpolation=Image.ANTIALIAS)

        """
        images = [self.blur, self.img, ma.masked_equal(th4, 0),
                  self.blur, self.img, ma.masked_equal(th5, 0),
                  self.blur, self.img, ma.masked_equal(self.th_high, 0)]
        titles = ['Gaussian filtered Image', 'IMG', "Combined Threshold",
                  'Gaussian filtered Image', 'IMG', "Low Threshold",
                  'Gaussian filtered Image', 'IMG', "High Threshold"]"""
        images = [self.img,
                  ma.masked_equal(self.th_high, 0),
                  self.blur,
                  disp_outputs,
                  disp_outputs + self.blur,
                  scipy.ndimage.interpolation.rotate(self.blur, 90),
                  scipy.ndimage.interpolation.rotate(ma.masked_equal(self.th_high, 0), 90)]
        titles = ['IMG',
                  "High Threshold",
                  'CAM',
                  "Conv Outputs",
                  "Conv Outpt + CAM",
                  "270 fCAM rot",
                  "270 tfCAM rot"]
        lent = len(os.listdir('C:/Users/Admin/Pictures/CAMs'))
        for i in xrange(1):
            plt.subplot(3, 3, 1), plt.imshow(images[0], 'viridis')
            plt.title(titles[0]), plt.xticks([]), plt.yticks([])
            plt.subplot(3, 3, 2), plt.imshow(disp_datum2), plt.imshow(images[1])
            plt.title(titles[1]), plt.xticks([]), plt.yticks([])
            plt.subplot(3, 3, 3), plt.imshow(images[2], 'viridis')
            plt.title(titles[2]), plt.xticks([]), plt.yticks([])
            plt.subplot(3, 3, 4), plt.imshow(disp_outputs)
            plt.title(titles[3]), plt.xticks([]), plt.yticks([])
            plt.subplot(3, 3, 5), plt.imshow(images[4])
            plt.title(titles[4]), plt.xticks([]), plt.yticks([])
            plt.subplot(3, 3, 6), plt.imshow(images[5])
            plt.title(titles[5]), plt.xticks([]), plt.yticks([])
            plt.subplot(3, 3, 7), plt.imshow(disp_datum2), plt.imshow(images[6])
            plt.title(titles[6]), plt.xticks([]), plt.yticks([])
        plt.show()
        # plt.savefig('C:/Users/Admin/Pictures/CAMs/%s.jpg' % str(lent))


    def gen_bbox(self):

        self.modthresh, self.contours, self.hierarchy = \
            cv2.findContours(self.th_high, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(self.th_high)

        for contour in self.contours:
            incontour = cv2.pointPolygonTest(contour, maxLoc, False)
            if incontour == 1 or incontour == 0:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(self.th_high, (x, y), (x + w, y + h), (255, 255, 255), thickness=3)
                self.calc_bbox_centroid(x, y, w, h)


    def gen_thresh(self):
        # ret4, th4 = cv2.threshold(self.blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # ret5, th5 = cv2.threshold(self.blur, self.thresholdlow, 255, cv2.THRESH_TOZERO)
        self.ret_high, self.th_high = cv2.threshold(self.blur, self.thresholdhigh, 255, cv2.THRESH_TOZERO)

    def calc_bbox_centroid(self, x, y, w, h):
        mx = math.floor((int((x + w)/2))/4.54)
        my = math.floor((int((y + h)/2))/4.54)
        self.centroid = [mx, my]