#!ProgramData/Anaconda2/python
import numpy as np
import matplotlib.pyplot as plt
import caffe
import gdal
from gdal import osr, ogr
import pyproj
import sys
import constants
from PIL import Image
import loc_CAMexperiment2 as loc
import cv2
import skimage
from multiprocessing import Pool, Process
import multiprocessing as mp
import caffe
import Queue
import time
import threading
import collections
import math

class Scanner:

    def __init__(self, infile, batchx, batchy):
        print infile
        self.src = gdal.Open(infile)
        self.src_b = self.src.GetRasterBand(1)
        self.src_g = self.src.GetRasterBand(2)
        self.src_r = self.src.GetRasterBand(3)
        self.prj = self.src.GetProjection()
        self.get_proj()
        self.get_keyvals()
        self.batchx = batchx
        self.sizex = (batchx * 25) + 25
        self.batchy = batchy
        self.sizey = (batchy * 25) + 25
        self.window_x = 0
        self.window_y = 0
        self.stop = 0
        print self.rows



    def get_proj(self):
        switcher = {
            'WGS 84 / UTM zone 8N': 32608,
            'WGS 84 / UTM zone 9N': 32609,
            'WGS 84 / UTM zone 10N': 32610,
            'WGS 84 / UTM zone 11N': 32611,
            'WGS 84 / UTM zone 12N': 32612
        }

        srs = osr.SpatialReference(wkt=self.prj)
        if srs.IsProjected():
            projcs = srs.GetAttrValue('projcs')
            print projcs
            self.epsg = switcher.get(projcs, 'nothing')

        if self.epsg == 'nothing':
            print 'projection not in current list of projections handled by this code'
            sys.exit(1)

        # epsg is 8901 for projected, 4326 for decimal lat/lon
        self.pproj = pyproj.Proj(init='epsg:%s' % self.epsg)
        self.praw = pyproj.Proj(init='epsg:4326')

    def get_keyvals(self):
        self.cols = self.src.RasterXSize
        self.rows = self.src.RasterYSize
        print self.cols, self.rows
        self.bands = 3

        geotransform = self.src.GetGeoTransform()
        self.originX = geotransform[0]
        self.originY = geotransform[3]
        self.pixelWidth = geotransform[1]
        self.pixelHeight = geotransform[5]
        self.bandType = gdal.GetDataTypeName(self.src_b.DataType)

    # @profile
    def scan(self):
        xoff = self.window_x
        yoff = self.window_y
        if xoff == -1:
            return None, None

        try:
            arr_b = np.array(self.src_b.ReadAsArray(xoff, yoff, self.sizex, self.sizey))
            arr_g = np.array(self.src_g.ReadAsArray(xoff, yoff, self.sizex, self.sizey))
            arr_r = np.array(self.src_r.ReadAsArray(xoff, yoff, self.sizex, self.sizey))

            self.arr = np.array([arr_b, arr_g, arr_r])
            self.disp_arr = np.stack([arr_b, arr_g, arr_r], axis=2)

        except IndexError as e:
            print'End Of Raster'
            print 'Killing sliding window'
            return None, None

        self.arr = skimage.img_as_float(self.disp_arr * 1).astype(np.float32)
        return self.arr, self.disp_arr

    # @profile
    def next_window(self, count):
        """if count >= 5:
            print 'limit reached'
            self.window_x = -1
            self.window_y = -1
            return -1, -1"""
        if (self.window_y > (self.rows - self.sizey)) and self.window_x == 0:
            self.window_y = (self.rows - self.sizey)
        elif (self.window_y == (self.rows - self.sizey)) and ((self.cols - self.sizex) == self.window_x):
            self.window_y = -1
            self.window_x = -1
        elif self.window_x < (self.cols - ((self.sizex * 2) - 25)):
            self.window_x = self.window_x + (self.sizex - 25)
            self.window_y = self.window_y
        # FIXME hacky conditional for proceding to next y row
        elif (self.cols - self.sizex) == self.window_x:
            self.window_x = 0
            self.window_y += self.sizey - 25
        elif (self.cols - 25) > self.window_x > (self.cols - (self.sizex * 2)):
            self.window_x = self.cols - self.sizex
        print self.window_x, self.window_y

        return self.window_x, self.window_y



    def get_pad_img_coords(self, xoff, yoff, i):
        stepx = (i % self.batchx) * 25 - 25
        stepy = (math.floor(i / self.batchx)) * 25 - 25
        xoff += stepx
        yoff += stepy

        gt = self.src.GetGeoTransform()
        mx = gt[0] + xoff * gt[1]
        my = gt[3] + yoff * gt[5]
        x2, y2 = pyproj.transform(self.pproj, self.praw, mx, my)

        return x2, y2

    #TODO handle whatis x y
    def get_pad_coords_cam(self, i, xoff, yoff, centroid):
        x, y = centroid
        stepx = ((i % self.batchx) * 25 + x)
        stepy = ((math.floor(i / self.batchx)) * 25 + y)
        xoff += stepx
        yoff += stepy

        gt = self.src.GetGeoTransform()
        mx = gt[0] + xoff * gt[1]
        my = gt[3] + yoff * gt[5]
        x2, y2 = pyproj.transform(self.pproj, self.praw, mx, my)

        return x2, y2

    # @profile
    def getslices(self):

        self.arrlst = []
        self.disp_arrlst = []
        iy = 0
        stepx = 25
        stepy = 25
        for n in range(self.batchy):
            ix = 0
            for i in range(self.batchx):
                temp = self.arr[iy:(iy+50), ix:(ix+50), :]
                self.disp_arrlst.append(self.disp_arr[iy:(iy+50), ix:(ix+50), :])
                self.arrlst.append(temp)
                ix += stepx
            iy += stepy
        return self.arrlst

    def getdispslice(self, i):

        # ix = (i * 25) - 1
        i = self.disp_arrlst[i]

        return i

    def close(self):
        self.src = None


class DataTraffic:

    def __init__(self, net, inim, scanobj, batch, meanfile):
        self.count = 0
        self.hitlist = []
        self.keepgoing = True
        self.batch = batch
        self.scanobj = scanobj
        self.mean = np.load(meanfile).mean(1).mean(1)
        self.net = net
        self.inputim = inim
        self.idx_win_out = 0
        self.idy_win_out = 0
        self.net_io_control()

    def transformer(self, datum):

        datum = cv2.resize(datum, (227, 227))
        # datum = skimage.transform.resize(datum, [227, 227])
        datum = np.swapaxes(datum, 0, 2)
        datum = datum[::-1, :, :]
        datum *= 255
        datum[2, :, :] = datum[2, :, :] - self.mean[2]
        datum[1, :, :] = datum[1, :, :] - self.mean[1]
        datum[0, :, :] = datum[0, :, :] - self.mean[0]

        return datum

    # @profile
    def net_io_control(self):
        while self.keepgoing:
            datum, disp_datum = self.scanobj.scan()
            if datum is None:
                self.keepgoing = False
                write_coords(self.hitlist)
                break
            arrlist = self.scanobj.getslices()
            caffe_data = self.transform(arrlist)
            self.pred = self.net.forwards_pass(caffe_data)
            print self.pred
            for i in range(self.batch):
                if self.pred[i] != 0:
                    self.count += 1
                    self.net.calc_CAM(i)
                    cam = self.net.get_cam()
                    outputs = self.net.get_outputs()
                    image = self.scanobj.getdispslice(i)
                    image = Image.fromarray(image)
                    bbox = loc.BBOX(cam, image, outputs)
                    bbox.gen_thresh()
                    bbox.gen_bbox()
                    xcoord, ycoord = self.scanobj.get_pad_coords_cam(i,
                                                                     self.idx_win_out,
                                                                     self.idy_win_out,
                                                                     bbox.centroid)
                    self.hitlist.append([xcoord, ycoord])
                    bbox.display()
                    image = image.point(lambda p: p * 1)
                    image.save('C:/Users/Admin/Pictures/CAMs/%s_%s.tif' % (str(self.count), str(i)))
            x, y = self.scanobj.next_window(self.count)
            self.idx_win_out = x
            self.idy_win_out = y


    """
    def set_transformer(self):
        self.transformer = caffe.io.Transformer({'data': self.net.net.blobs['data'].data.shape})
        self.transformer.set_mean('data', np.load(self.net.caffe_root + '/data/L8_all/mean.npy').mean(1).mean(1))
        self.transformer.set_transpose('data', (2, 0, 1))
        self.transformer.set_channel_swap('data', (2, 1, 0))
        self.transformer.set_raw_scale('data', 255.0)"""

    # @profile
    def transform(self, arrlist):
        caffe_data = []
        for i in range(self.batch):
            # caffe_data.append(np.asarray([self.transformer.preprocess('data', arrlist[i])]))
            caffe_data.append(np.asarray([self.transformer(arrlist[i])]))
        return caffe_data


def write_coords(list, img='LC80460222015190LGN00'):
    import csv
    basedir = 'C:/Users/Admin/Documents/GAPnet eval shapefiles'
    csvname = img + '.csv'
    filename = basedir + '/' + csvname
    fieldnames = ['X', 'Y']
    with open(filename, 'w') as fille:
        writer = csv.DictWriter(fille, fieldnames=fieldnames)
        writer.writeheader()
        for elem in list:
            x = elem[0]
            y = elem[1]
            writer.writerow({'X': x, 'Y': y})

"""
def slide_net(scanobj, net, inim, batch):
    count = 0
    while scanobj.window_y != -1:
        print scanobj.window_x, scanobj.window_y
        datum, disp_datum = scanobj.scan()
        arrlist = scanobj.getslices()
        pred = net.forwards_pass(arrlist)
        print pred
        count += 1
        for i in range(batch):
            if pred[i] != 0:
                image = scanobj.getdispslice(i)
                # count += 1
                # net.calc_CAM()
                # cam = net.get_cam()
                image = Image.fromarray(image)
                # bbox = loc.BBOX(cam, image)
                # bbox.gen_thresh()
                # bbox.gen_bbox()
                # x, y = scanobj.get_pad_coords(bbox.centroid)
                # print x, y
                image = image.point(lambda p: p * 3)
                image.save('C:/Users/Admin/Pictures/CAMs/%s_%s.tif' % (inim, str(count)))
                # bbox.display()
                # write x, y, pred to file

        scanobj.next_window(count)
    print count
"""

def control(img="LC80460222015190LGN00"):
    im = 'C:/Projects/Training Data/scenes/%s.tif' % img
    batch = 1024
    batchx = 16
    batchy = 64
    scanobj = Scanner(im, batchx, batchy)
    net = loc.GAPnet(batch)
    DataTraffic(net, img, scanobj, batch, 'C:/Projects/caffe/data/L8_all/mean.npy')

control()