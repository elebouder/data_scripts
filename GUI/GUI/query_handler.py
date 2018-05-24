import psycopg2
from PIL import Image
import os


################### TODO list for query functions/scripts


# gets the name of a rast table that has not yet been classified
# currently deprecated, may soon be removes

def select_unclassed_siteID():

    conn = psycopg2.connect(database='test_rastrun', user='postgres', host='localhost',
                            password='p432')
    cursor = conn.cursor()
    query = "SELECT raster_id FROM raster_dataset WHERE classification_status = 'FALSE'"
    cursor.execute(query)
    row = cursor.fetchone()
    conn.close()
    return row[0]


#PostgreSQL Storage of Data, deprecated
"""
# uses name of unclassed rast table to find it and extract a triband rast as png
# takes rid (ID of scene and of rtable)
def extract_unclassed_site_as_png(rtable_id):

    conn = psycopg2.connect(database='test_rastrun', user='postgres', host='localhost',
                            password='p432')
    cursor = conn.cursor()

    params = ("U:/PyCharm Projects/GUI/tmp/%s.png" % rtable_id, rtable_id)

    select = "SELECT ST_AsPNG(rast) As %s" \
             "From %s WHERE rid=1"

    cursor.execute(select, params)
    conn.close()
    return params[0]

# after site has been assigned class via Tkinter, update that site in the raster_dataset with the new class
# includes search by prim key and update of classification_status column from False to True
def update_class_val():
    return None

# NOTE this may soon be deprecated
def shut_down_conn():
    return None

"""

# 0 is Neg, 1 is Pos, 2 is Unknown, 5 is Not Yet Classified
# run through input directory db and compile list of not-yet-classed raster clips

def list_tbClassified(path):
    imgList = []
    for img in os.listdir(path):
        if img.endswith('_5.TIF'):
            imgList.append(img)
    return imgList

# assign a classification to the filename of a clip (rename file to new directory if needed)

def assignClass2file(path, path2, name, classification, last_assign):
    tmp = name.split('.')[0]
    basename = tmp[:-2]
    src_ds = path + '/' + name
    if os.path.exists(src_ds) is False:
        print 'looks like you are trying to overwrite a choice on ', name
        src_ds = path2 + '/' + basename + '_%s.tif' % last_assign
    dst_ds = path2 + '/' + basename + "_%s.tif" % classification
    os.rename(src_ds, dst_ds)
    print 'wrote value to filedb'

# assign a classification a clip in the raster database in PostgreSQL

def assignClass2SQL(name, classification):
    conn = psycopg2.connect(database='test_rastrun', user='postgres', host='localhost',
                            password='p432')
    params = (classification, name)
    cursor = conn.cursor()
    query = "UPDATE public.raster_dataset SET classification_status = TRUE, " \
            "classification = %s WHERE raster_id = %s"
    cursor.execute(query, params)
    print'wrote value to server'
    return






