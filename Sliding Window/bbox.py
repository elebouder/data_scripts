import numpy as np
import matplotlib.pyplot as plt
import caffe
import cv2
import numpy
import numpy.ma as ma

class BBOX:

    def __init__(self, cam, img):
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
        """
        images = [self.blur, self.img, ma.masked_equal(th4, 0),
                  self.blur, self.img, ma.masked_equal(th5, 0),
                  self.blur, self.img, ma.masked_equal(self.th_high, 0)]
        titles = ['Gaussian filtered Image', 'IMG', "Combined Threshold",
                  'Gaussian filtered Image', 'IMG', "Low Threshold",
                  'Gaussian filtered Image', 'IMG', "High Threshold"]"""

        images = [self.blur, self.img, ma.masked_equal(self.th_high, 0)]
        titles = ['Gaussian filtered Image', 'IMG', "High Threshold"]

        for i in xrange(1):
            plt.subplot(3, 3, i * 3 + 1), plt.imshow(images[i * 3], 'viridis')
            plt.title(titles[i * 3]), plt.xticks([]), plt.yticks([])
            plt.subplot(3, 3, i * 3 + 2), plt.imshow(images[i * 3 + 1])
            plt.title(titles[i * 3 + 1]), plt.xticks([]), plt.yticks([])
            plt.subplot(3, 3, i * 3 + 3), plt.imshow(images[i * 3 + 1]), plt.imshow(images[i * 3 + 2], 'viridis')
            plt.title(titles[i * 3 + 2]), plt.xticks([]), plt.yticks([])
        plt.show()


    def gen_bbox(self):

        self.modthresh, self.contours, self.hierarchy = \
            cv2.findContours(self.th_high, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # cv2.drawContours(self.th_high, self.contours, -1)
        for contour in self.contours:
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(self.th_high, (x, y), (x + w, y + h), (255, 255, 255), thickness=3)


    def gen_thresh(self):
        # ret4, th4 = cv2.threshold(self.blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # ret5, th5 = cv2.threshold(self.blur, self.thresholdlow, 255, cv2.THRESH_TOZERO)
        self.ret_high, self.th_high = cv2.threshold(self.blur, self.thresholdhigh, 255, cv2.THRESH_TOZERO)