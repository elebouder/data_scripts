import psycopg2
import subprocess
import sys, os
import gdal


# TODO: make sure the lat and lon values are not the corner values used in the array2raster projections,
# todo but the centre unprojected values
# TODO: define seperate schemas for rasterdatasets, considering there will eventually be tens of thousands of them

def into_db(site, index, scene_id, month, year):
    #input fields
    rastername = site
    rasterID = scene_id + '_%s' % index
    print rastername

    try:
        src_ds = gdal.Open(rastername)
    except RuntimeError, e:
        print 'Unable to open' + rastername
        print e
        sys.exit(1)
    src_b = src_ds.GetRasterBand(1)
    src_g = src_ds.GetRasterBand(2)
    src_r = src_ds.GetRasterBand(3)


    xsize = src_ds.RasterXSize
    ysize = src_ds.RasterYSize
    gt = src_ds.GetGeoTransform()
    minx = gt[0]
    maxy = gt[3]
    maxx = minx + gt[1]*xsize
    miny = maxy + gt[5]*ysize
    lon = (minx + maxx)/2
    lat = (miny + maxy)/2

    src_ds = None



    os.environ['PATH'] = r';C:\Program Files\PostgreSQL\9.2\bin'
    os.environ['PGHOST'] = 'localhost'
    os.environ['PGPORT'] = '5432'
    os.environ['PGUSER'] = 'postgres'
    os.environ['PGPASSWORD'] = 'p432'
    os.environ['PGDATABASE'] = 'test_rastrun'

    conn = psycopg2.connect(database='test_rastrun', user='postgres', host='localhost',
                            password='p432')
    cursor = conn.cursor()

    cmds = 'raster2pgsql -I -C -s 4326 -l 2 -t ' \
           + str(xsize) + 'x' + str(ysize) + ' "' + rastername + '" public.' \
           + rasterID + ' | psql -h localhost -d test_rastrun'
    subprocess.call(cmds, shell=True)


    update = "INSERT INTO raster_dataset (raster_id, scene_origin, lon, lat, classification_status, " \
             "classification, cnn_class_assignment, month, year)" \
             "VALUES (%s,%s,%s,%s,%s,%s,%s,%s, %s)"

    listt = (rasterID, scene_id, lon, lat, False, False, False, month, year)
    cursor.execute(update, listt)
    conn.commit()
    conn.close()


def into_file_db(site, index, scene_id, month, year):
    # input fields
    rastername = site
    rasterID = scene_id + '_%s' % index
    file_db = 'U:/Fracking Pads/Training Data/Unclassified'
    print rastername

    try:
        src_ds = gdal.Open(rastername)
    except RuntimeError, e:
        print 'Unable to open' + rastername
        print e
        sys.exit(1)
    src_b = src_ds.GetRasterBand(1)
    src_g = src_ds.GetRasterBand(2)
    src_r = src_ds.GetRasterBand(3)

    xsize = src_ds.RasterXSize
    ysize = src_ds.RasterYSize
    gt = src_ds.GetGeoTransform()
    minx = gt[0]
    maxy = gt[3]
    maxx = minx + gt[1] * xsize
    miny = maxy + gt[5] * ysize
    lon = (minx + maxx) / 2
    lat = (miny + maxy) / 2

    src_ds = None


    conn = psycopg2.connect(database='test_rastrun', user='postgres', host='localhost',
                            password='p432')
    cursor = conn.cursor()

    update = "INSERT INTO raster_dataset (raster_id, scene_origin, lon, lat, classification_status, " \
             "classification, cnn_class_assignment, month, year)" \
             "VALUES (%s,%s,%s,%s,%s,%s,%s,%s, %s)"

    listt = (rasterID, scene_id, lon, lat, False, False, False, month, year)
    cursor.execute(update, listt)
    conn.commit()
    conn.close()

