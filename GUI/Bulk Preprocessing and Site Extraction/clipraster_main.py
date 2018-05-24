import gdal
from gdal import ogr, osr
import sys
import pyproj
import csv
import numpy as np
import math
from PIL import Image
gdal.UseExceptions()



def extract(parentOutputDirectory, outputbasename, inputscene):

    # set up init fields
    trainingsites_csv = 'U:/Fracking Pads/trainingSites_touse.csv'
    sitecoords_nonextent = []
    sitecoord_extent = []

    # import raster(s), get projection, prepare transform projections and find current extent
    src_ds, srcband, prj, epsg_prj = import_raster_bands(inputscene)
    src1 = srcband[0]
    src2 = srcband[1]
    src3 = srcband[2]

    if epsg_prj == 'nothing':
        print 'projection not in current list of projections handled by this code'
        sys.exit(1)

    # epsg is 8901 for projected, 4326 for decimal lat/lon
    pproj = pyproj.Proj(init='epsg:%s' % epsg_prj)
    praw = pyproj.Proj(init='epsg:4326')

    # run through trainingsites_csv and pick up all the sites coords to sitecoords_nonextent
    with open(trainingsites_csv, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            x = float(row[0])
            y = float(row[1])
            sitecoords_nonextent.append([x, y])


    # transform all site coords from decimal lat/lon to current proj, check those that are present, store in tuple list
    sitecoord_extent = remove_outofbounds_points(sitecoords_nonextent,
                                                 src_ds,
                                                 sitecoord_extent,
                                                 praw,
                                                 pproj)

    # TODO: export sampled raster data to georaster database

    # creeate point geometry and add all points to it
    multipoint = ogr.Geometry(ogr.wkbMultiPoint)
    for tup in sitecoord_extent:
        x = tup[0]
        y = tup[1]
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(x, y)
        multipoint.AddGeometry(point)


    # make_site_raster(multipoint, src_ds)
    siteArrayList, lonlist, latlist = make_site_array(multipoint, src_ds, src1, src2, src3)
    """for site in siteArrayList:
        #print'site'
        for l in site:
            print l"""
    sitesfor_sqldb = []
    namenums = len(siteArrayList)
    for i in range(namenums):
        newRasterindex = i
        array = siteArrayList[i]
        lon = lonlist[i]
        lat = latlist[i]
        sitename = array2raster(pproj,
                                praw,
                                array,
                                lon,
                                lat,
                                src_ds,
                                newRasterindex,
                                parentOutputDirectory,
                                outputbasename)
        sitesfor_sqldb.append([sitename, newRasterindex])
    #TODO: check that latlist, lonlist, arraylist, and namenums iteration indexing works properly

    return sitesfor_sqldb    #returns a list of all the full file names of each site processed

def import_raster_bands(inputfile):
    switcher = {
        'WGS 84 / UTM zone 8N': 32608,
        'WGS 84 / UTM zone 9N': 32609,
        'WGS 84 / UTM zone 10N': 32610,
        'WGS 84 / UTM zone 11N': 32611,
        'WGS 84 / UTM zone 12N': 32612
    }


    try:
        src_ds = gdal.Open(inputfile)
    except RuntimeError, e:
        print 'Unable to open' + inputfile
        print e
        sys.exit(1)
    src_b = src_ds.GetRasterBand(1)
    src_g = src_ds.GetRasterBand(2)
    src_r = src_ds.GetRasterBand(3)
    prj = src_ds.GetProjection()
    print prj
    srs = osr.SpatialReference(wkt=prj)
    if srs.IsProjected():
        projcs = srs.GetAttrValue('projcs')
        print projcs
        epsg = switcher.get(projcs, 'nothing')

    return src_ds, [src_b, src_g, src_r], prj, epsg


    # convert raster to array form


def raster2array(raster):
    array = raster.ReadAsArray()
    return array

    # find current projective raster boundaries


def find_raster_extent(src_ds):
    gt = src_ds.GetGeoTransform()
    minx = gt[0]
    maxy = gt[3]
    maxx = minx + gt[1] * src_ds.RasterXSize
    miny = maxy + gt[5] * src_ds.RasterYSize
    return [minx, miny, maxx, maxy]

    # take a multipoint geometry and generate a list of parent value arrays for each site that falls
    # within current non-null projection bounds


def make_site_array(multipoint, src_ds, src1, src2, src3):
    siteArrayList = []
    lonlist = []
    latlist = []
    for i in range(0, multipoint.GetGeometryCount()):
        g = multipoint.GetGeometryRef(i)
        mx, my = g.GetX(), g.GetY()  # map units
        # convert from map to pixel coords
        # check for no rotation
        gt = src_ds.GetGeoTransform()
        px = int((mx - gt[0]) / gt[1])  # x pixel
        py = int((my - gt[3]) / gt[5])  # y pixel
        pxmin = px - 25
        pxmax = px + 25
        pymin = py - 25
        pymax = py + 25
        x_range = range(pxmin, pxmax)
        y_range = range(pymin, pymax)
        w = len(x_range)
        h = len(y_range)
        x_array = range(0, w)
        y_array = range(0, h)
        sitearray1 = np.array([[0 for i in range(w)] for j in range(h)])
        sitearray2 = np.array([[0 for i in range(w)] for j in range(h)])
        sitearray3 = np.array([[0 for i in range(w)] for j in range(h)])
        for x in x_array:
            for y in y_array:
                siteposx = x + pxmin
                siteposy = y + pymin
                intval1 = src1.ReadAsArray(siteposx, siteposy, 1, 1)
                intval2 = src2.ReadAsArray(siteposx, siteposy, 1, 1)
                intval3 = src3.ReadAsArray(siteposx, siteposy, 1, 1)
                if intval1 is None:
                    intval1, intval2, intval3 = [[0]], [[0]], [[0]]
                sitearray1[x][y] = intval1[0][0]
                sitearray2[x][y] = intval2[0][0]
                sitearray3[x][y] = intval3[0][0]
                if x == 0 and y == 0:
                    lonlist.append(siteposx)
                    latlist.append(siteposy)
        bandarrays = [sitearray1, sitearray2, sitearray3]
        siteArrayList.append(bandarrays)
    site_array_list = np.array(siteArrayList)
    return site_array_list, lonlist, latlist

    # converts the pixel coordinates of a point to the affine projection coordinates


def pixel2mapunits(pproj, praw, px, py, src_ds):
    gt = src_ds.GetGeoTransform()
    mx = gt[0] + px * gt[1]
    my = gt[3] + py * gt[5]
    x2, y2 = pyproj.transform(pproj, praw, mx, my)
    return x2, y2

    # run through the list of decimal coordinate for the sites, removes all the ones outside of the
    # current projected area
    # Contains a call to a deprecated (possibly?) function over_null_area, checking if the pixel value
    # at each projected location is null, and removing the point if so
    # all the sites that 'passed' the two location tests are added to the tuple list 'sitecoord_extent'
    # to be used to generate site raster array templates


def remove_outofbounds_points(sitecoords_nonextent, src_ds, sitecoord_extent, praw, pproj):
    ras_extent = find_raster_extent(src_ds)
    for tup in sitecoords_nonextent:
        x1 = tup[0]
        y1 = tup[1]
        x2, y2 = pyproj.transform(praw, pproj, x1, y1)
        if (ras_extent[0] < x2 < ras_extent[2] and
                        ras_extent[1] < y2 < ras_extent[3]):
            # may soon be deprecated, checks if projected coordinates lie in the
            # projected area but in a null data location, such as along the lower right
            # corner of a landsat raster
            if over_null_area(x2, y2, src_ds) is False:
                sitecoord_extent.append([x2, y2])
    return sitecoord_extent

    # checks if the geometry object in question occupies a null data site


def over_null_area(x, y, src_ds):
    gt = src_ds.GetGeoTransform()
    px = int((x - gt[0]) / gt[1])  # x pixel
    py = int((y - gt[3]) / gt[5])  # y pixel
    rasterval = src_ds.ReadAsArray(px, py, 1, 1)
    #print rasterval
    if (math.isnan(rasterval[0][0]) or
            math.isnan(rasterval[1][0]) or
            math.isnan(rasterval[2][0])):
        return True
    elif (rasterval[0][0] == 255 or
          rasterval[1][0] == 255 or
          rasterval[2][0] == 255):
        return True
    else:
        return False

        # for each array of pixel values representing a site, array2raster converts to rasterband
        # bearing current projection and writes a raster to disk


def array2raster(pproj,
                 praw,
                 array,
                 lon,
                 lat,
                 src_ds,
                 newRasterindex,
                 parentOutputDirectory,
                 outputbasename):
    array1 = array[0]
    array2 = array[1]
    array3 = array[2]
    cols = array1.shape[1]
    rows = array1.shape[0]
    originX, originY = pixel2mapunits(pproj, praw, lon, lat, src_ds)
    pixelWidth = 4
    pixelHeight = 4
    newRastername = parentOutputDirectory + '/' + outputbasename + '_%s.TIF' % (newRasterindex)
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRastername, cols, rows, 3, gdal.GDT_Byte)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband1 = outRaster.GetRasterBand(1)
    outband1.WriteArray(array1)
    outband2 = outRaster.GetRasterBand(2)
    outband2.WriteArray(array2)
    outband3 = outRaster.GetRasterBand(3)
    outband3.WriteArray(array3)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband1.FlushCache()
    outband2.FlushCache()
    outband3.FlushCache()

    newPNGname = "U:/Fracking Pads/Training Data/Unclassified/_%s.jpg" % newRasterindex
    """driver2 = gdal.GetDriverByName("JPEG")
    driver1 = gdal.GetDriverByName("MEM")
    ds = driver1.Create(" ", cols, rows, 3, gdal.GDT_UInt16)
    outPNG = driver1.CreateCopy(newPNGname, ds, 0)
    outPNG = None"""

    #img = Image.open(open(newRastername, 'rb'))
    #img.save(newPNGname, 'PNG')

    #print 'saved ', newPNGname

    return newRastername





    # TODO: get improved version of code with data-checking ability from personal PC