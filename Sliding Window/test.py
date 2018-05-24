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
import localize as loc
import cv2
import skimage
from multiprocessing import Pool, Process
import multiprocessing as mp
import caffe
import Queue
import time
import threading
import collections

class Scanner:

    def __init__(self, infile, batchx, batchy, threadID):
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
        self.endy = int(threadID[0] * self.rows / threadID[1])
        self.start_y = int((threadID[0] - 1) * self.rows / threadID[1])



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
    def scan(self, window_x, window_y):
        xoff = window_x
        yoff = window_y
        arr_b = np.array(self.src_b.ReadAsArray(xoff, yoff, self.sizex, self.sizey))
        arr_g = np.array(self.src_g.ReadAsArray(xoff, yoff, self.sizex, self.sizey))
        arr_r = np.array(self.src_r.ReadAsArray(xoff, yoff, self.sizex, self.sizey))

        self.arr = np.array([arr_b, arr_g, arr_r])
        self.disp_arr = np.stack([arr_b, arr_g, arr_r], axis=2)

        self.arr = skimage.img_as_float(self.disp_arr * 3).astype(np.float32)
        return self.arr, self.disp_arr

    # @profile
    def next_window(self, count, window_x, window_y):
        if count == 18:
            window_x = -1
            window_y = -1
        if window_y > self.endy:
            window_x = -1
            window_y = -1
        if (window_y > (self.rows - self.sizey)) and window_x == 0:
            window_y = (self.rows - self.sizey)
        elif (window_y == (self.rows - self.sizey)) and ((self.cols - self.sizex) == window_x):
            window_y = -1
            window_x = -1
        elif window_x < (self.cols - ((self.sizex * 2) - 25)):
            window_x = window_x + (self.sizex - 25)
            window_y = window_y
        # FIXME hacky conditional for proceding to next y row
        elif (self.cols - self.sizex) == window_x:
            window_x = 0
            window_y += self.sizey - 25
        elif (self.cols - 25) > window_x > (self.cols - (self.sizex * 2)):
            window_x = self.cols - self.sizex

        return window_x, window_y


    """
    def get_pad_coords(self, centroid):
        x, y = centroid
        pxl_x = int(x/6) + window_x
        pxl_y = int(y/6) + window_y

        gt = self.src.GetGeoTransform()
        mx = gt[0] + pxl_x * gt[1]
        my = gt[3] + pxl_y * gt[5]
        x2, y2 = pyproj.transform(self.pproj, self.praw, mx, my)

        return x2, y2"""

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

def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

class DataTraffic:

    def __init__(self, net, inim, scanobj, batch, threadID):
        self.count = 0
        self.batch = batch
        self.scanobj = scanobj
        self.net = net
        self.set_transformer()
        self.inputim = inim
        self.xq = collections.deque()
        self.yq = collections.deque()
        self.xq.append(0)
        self.yq.append(self.scanobj.start_y)
        self.idx_win_out = 0
        self.idy_win_out = 0
        self.queue = Queue.Queue(maxsize=30)
        self.run_queue()

    # @profile
    def net_io_control(self):
        if self.yq[-1] != -1:
            for i in range(30):
                print self.xq[-1], self.yq[-1]
                caffe_data = self.queue.get(True)
                self.idx_win_out = self.xq.pop()
                self.idy_win_out = self.yq.pop()
                self.pred = self.net.forwards_pass(caffe_data)
                self.count += 1
                print self.pred
            self.run_queue()

    # @profile
    def pull_batch(self):
        x, y = self.scanobj.next_window(self.count, self.xq[0], self.yq[0])
        self.xq.appendleft(x); self.yq.appendleft(y)
        datum, disp_datum = self.scanobj.scan(x, y)
        arrlist = self.scanobj.getslices()
        caffe_data = self.transform(arrlist)
        self.queue.put(caffe_data)

    def set_transformer(self):
        self.transformer = caffe.io.Transformer({'data': self.net.net.blobs['data'].data.shape})
        self.transformer.set_mean('data', np.load(self.net.caffe_root + '/data/L8_all/mean.npy').mean(1).mean(1))
        self.transformer.set_transpose('data', (2, 0, 1))
        self.transformer.set_channel_swap('data', (2, 1, 0))
        self.transformer.set_raw_scale('data', 255.0)

    # @profile
    def transform(self, arrlist):
        caffe_data = []
        for i in range(self.batch):
            caffe_data.append(np.asarray([self.transformer.preprocess('data', arrlist[i])]))
        return caffe_data

    # @threaded
    # @profile
    def run_queue(self):
        for i in range(30):
            print 'start load'
            self.pull_batch()
            print 'loaded queue'
        self.net_io_control()


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

def control(thread_ID, img="LC80460222015190LGN00"):
    im = 'C:/Projects/Training Data/%s.tif' % img
    batch = 1024
    batchx = 16
    batchy = 64
    scanobj = Scanner(im, batchx, batchy, thread_ID)
    net = loc.GAPnet(batch)
    DataTraffic(net, img, scanobj, batch, thread_ID)

