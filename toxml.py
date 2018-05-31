from xml.etree.ElementTree import Element, ElementTree, SubElement, Comment, tostring
import os
import csv
import ast
import sys


csv_dir = '/home/elebouder/Data/landsat/ann_files/'
xml_dir = '/home/elebouder/Data/landsat/ann_xml/'

imsize = '50'
imdepth = '3'

def iter_csv():
    large_dict = {}
    for f in os.listdir(csv_dir):
        with open(csv_dir + f, 'r') as nextcsv:
            reader = csv.DictReader(nextcsv)
            # prev_id = 'random'
            # prev_attr = []
            for row in reader: 
                try:
                    im_id = row["#filename"]
                except KeyError:
                    im_id = row["image"]
                #rcount = row['region_count']
                #rid = row['region_id']
                shape_data = ast.literal_eval(row['region_shape_attributes'])
                print shape_data
                #if not shape_data:
                #    continue
                if im_id in large_dict:
                    large_dict[im_id].append(shape_data)
                else:
                    large_dict[im_id] = [shape_data]

    return large_dict




def write_xml(dictlist, key):
    print "======================"
    print key
    ann_root = Element('annotation')
    key_fname = SubElement(ann_root, 'filename')
    key_fname.text = key
    size = SubElement(ann_root, 'size')
    width = SubElement(size, 'width')
    height = SubElement(size, 'height')
    depth = SubElement(size, 'depth')
    width.text = imsize
    height.text = imsize
    depth.text = imdepth

    for elem in dictlist:
        if not elem:
            continue
        obj = SubElement(ann_root, 'object')
        bndbox = SubElement(obj, 'bndbox')
        name = SubElement(obj, 'name')
        name.text = 'pos'
        xmin = SubElement(bndbox, 'xmin')
        ymin = SubElement(bndbox, 'ymin')
        xmax = SubElement(bndbox, 'xmax')
        ymax = SubElement(bndbox, 'ymax')
        print elem
        x = elem['x']
        y = elem['y']
        h = elem['height']
        w = elem['width']
        
        x_adj, y_adj, xmax_adj, ymax_adj = enforce_bounds(x, y, h, w)

        xmin.text = str(x_adj)
        ymin.text = str(y_adj)
        xmax.text = str(xmax_adj)
        ymax.text = str(ymax_adj)

    elementtree = ElementTree(element=ann_root)
    newxml = xml_dir + key.split('.')[0] + '.xml'
    elementtree.write(newxml)
    
def iter_idx(large_dict):
    for key in large_dict:
        dictlist = large_dict[key]
        write_xml(dictlist, key)


def csv2xml():
    large_dict = iter_csv()
    iter_idx(large_dict)


def enforce_bounds(x, y, h, w):
    if (x < 0):
        x = 0
    if (y < 0):
        y = 0
    xmax = x + w
    ymax = y + h
    if (xmax > 50):
        xmax = 50
    elif (ymax > 50):
        ymax = 50
        
    return x, y, xmax, ymax       

csv2xml()



