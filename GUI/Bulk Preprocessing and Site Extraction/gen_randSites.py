import clipraster_main as clip
from numpy import random
import gdal
import sys
import pyproj
from gdal import ogr, osr
import os
import postgresql_access as psg
import decimal


def manage_extraction():

    inputdct = "U:/Fracking Pads/RGB Scenes Ready for Site-Lifting"
    parentOutputDirectory = "U:/Fracking Pads/Training Data/Unclassified"
    month = 7
    yr = 2015


    for image in os.listdir(inputdct):
        if image.endswith('.tif'):
            inputscene = inputdct + '/' + image
            outputbasename = image.split('.')[0]
            sitesfor_sqldb = extract(parentOutputDirectory, outputbasename, inputscene)
            print 'extract done'
            for s in sitesfor_sqldb:
                print s
            #[psg.into_file_db(site[0], site[1], outputbasename, month, yr) for site in sitesfor_sqldb]


def extract(parentOutputDirectory, outputbasename, inputscene):

    # import raster(s), get projection, prepare transform projections and find current extent
    src_ds, srcband, prj, epsg_prj = clip.import_raster_bands(inputscene)
    src1 = srcband[0]
    src2 = srcband[1]
    src3 = srcband[2]

    if epsg_prj == 'nothing':
        print 'projection not in current list of projections handled by this code'
        sys.exit(1)

    pproj = pyproj.Proj(init='epsg:%s' % epsg_prj)
    praw = pyproj.Proj(init='epsg:4326')

    print pproj, praw

    [minx, miny, maxx, maxy] = clip.find_raster_extent(src_ds)
    print [minx, miny, maxx, maxy]
    sitecoord_nonextent = randomize(minx, miny, maxx, maxy)

    sitecoord_extent = remove_outofbounds_points(sitecoord_nonextent,
                                                 src_ds,
                                                 [],
                                                 praw,
                                                 pproj)
    # create point geometry and add all points to it
    multipoint = ogr.Geometry(ogr.wkbMultiPoint)
    for tup in sitecoord_extent:
        x = tup[0]
        y = tup[1]
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(x, y)
        multipoint.AddGeometry(point)


    # make_site_raster(multipoint, src_ds)
    siteArrayList, lonlist, latlist = clip.make_site_array(multipoint, src_ds, src1, src2, src3)
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


def randomize(minx, miny, maxx, maxy):
    array = []
    d = decimal.Decimal(str(maxx))
    d = abs(d.as_tuple().exponent)
    for x in range(200):
        #[minx, maxx] = sorted([minx, maxx])
        #[miny, maxy] = sorted([miny, maxy])
        x = round(random.uniform(minx, maxx, 1), d)
        y = round(random.uniform(miny, maxy, 1), d)
        #print x, y
        array.append([x, y])

    return array

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
    originX, originY = clip.pixel2mapunits(pproj, praw, lon, lat, src_ds)
    pixelWidth = 4
    pixelHeight = 4
    newRastername = parentOutputDirectory + '/F' + outputbasename + '_%s_5.TIF' % (newRasterindex)
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


    return newRastername

def remove_outofbounds_points(sitecoords_nonextent, src_ds, sitecoord_extent, praw, pproj):
    ras_extent = clip.find_raster_extent(src_ds)
    for tup in sitecoords_nonextent:
        x1 = tup[0]
        y1 = tup[1]
        if (ras_extent[0] < x1 < ras_extent[2] and
                        ras_extent[1] < y1 < ras_extent[3]):
            # may soon be deprecated, checks if projected coordinates lie in the
            # projected area but in a null data location, such as along the lower right
            # corner of a landsat raster
            if clip.over_null_area(x1, y1, src_ds) is False:
                sitecoord_extent.append([x1, y1])


    return sitecoord_extent

manage_extraction()





