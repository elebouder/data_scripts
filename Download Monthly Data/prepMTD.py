import csv
import os
import operator

###inputs to search_mtd: start date, end date, and max cloudcover
###outputs of search_mtd: list of possible scenes and file of metadata for said scenes, as well
###as accompanying rough dictionary
###TODO: handle end-date support for creating download lists over cts months:possible to take care of this in Main
###refine_mtd: take the rough list of all possible mtd and scenes for that month, as well as the dict,
###and pick the best ones such that no overlap in path/row combo
###refine according to cloudcover; if two with the same cloudcover, just pick one

def search_mtd(month, year, cloudcover):
    # start and end date is in the format of [month, year]

    landsat_mtd = 'U:/Fracking Pads/LANDSAT_8.csv'

    minlon = -128.5312
    maxlon = -118.5996

    minlat = 53.4043
    maxlat = 60.7334
    listdict = []



    with open(landsat_mtd, 'rb') as fullmeta:
        reader = csv.DictReader(fullmeta)
        for row in reader:
            lon = float(row['sceneCenterLongitude'])
            lat = float(row['sceneCenterLatitude'])
            path = int(row['path'])
            roww = int(row['row'])
            scene = row['sceneID']
            clouds = float(row['cloudCoverFull'])
            dayornight = row['dayOrNight']
            date_raw = str(row['acquisitionDate'])
            d = date_raw.split('-')
            date_month = int(d[1])
            date_year = int(d[0])

            if (minlon < lon < maxlon and
                minlat < lat < maxlat and
                cloudcover >= clouds and
                dayornight == 'DAY' and
                month == date_month and
                year == date_year):
                print('found one')
                listdict.append({'scene': scene,
                                 'lon': lon,
                                 'lat': lat,
                                 'path': path,
                                 'row': roww,
                                 'cloudCover': clouds,
                                 'month': date_month,
                                 'year': date_year})
    for line in listdict:
        print line
    month_meta_file = 'U:/Fracking Pads/download_metas/%s_%srough.csv' % (date_month, date_year)

    if os.path.isfile(month_meta_file):
        os.remove(month_meta_file)

    writefields = ['scene',
                   'lon',
                   'lat',
                   'path',
                   'row',
                   'cloudCover',
                   'month',
                   'year']

    with open(month_meta_file, 'wb') as metafile:
        writer = csv.DictWriter(metafile, fieldnames=writefields)
        writer.writeheader()
        for row in listdict:
            writer.writerow(row)

    scene_request_list = 'U:/Fracking Pads/download_requests/%s_%srough.txt' % (date_month, date_year)

    if os.path.isfile(scene_request_list):
        os.remove(scene_request_list)

    request_open = open(scene_request_list, 'w')
    for row in listdict:
        scene = row['scene']
        request_open.write(scene + '\n')

    request_open.close()

    return month_meta_file, scene_request_list, listdict, writefields

#create dict of tuples {scene: [path, row]}
#flip into reverse multidict, and look for keys with more than 1 value
#write new files for meta and scene request list, accounting for duplicates
#return three values: first one is a check number
#Back in main, if the first returned value is 1, then that means there were duplicates to take care of
#If the first returned value is 2, that means there were no duplicates, and the original request lists
#should be used


def refine_mtd(roughdict, month, year, fields):
    multidict = {}
    for row in roughdict:
        multidict[row['scene']] = str(row['path']) + '_' + str(row['row'])

    rev_multidict = {}
    for key, value in multidict.items():
        rev_multidict.setdefault(value, set()).add(key)
    print rev_multidict

    dup_pathrows = [key for key, values in rev_multidict.items() if len(values) > 1]
    dup_scenes = [values for key, values in rev_multidict.items() if len(values) > 1]

    print ('dup_pathrows')
    print dup_pathrows

    losingscenes = []

    if len(dup_pathrows) > 0:
        for pathrow in dup_pathrows:
            scene_cloud_dict = {}
            scenes = rev_multidict[pathrow]
            for scene in scenes:
                tempdict = (item for item in roughdict if item['scene'] == scene).next()
                cloud = tempdict['cloudCover']
                scene_cloud_dict[scene] = cloud
            winning_scene, extrascenes = pickscene(scene_cloud_dict)
            losingscenes.append(extrascenes)
        print ('losingscenes')
        print losingscenes

        finaldict = []
        finaldict[:] = [d for d in roughdict if d['scene'] not in losingscenes]

        month_meta_file_final = 'U:/Fracking Pads/download_metas/%s_%sfinal.csv' % (month, year)
        scene_request_list_final = 'U:/Fracking Pads/download_requests/%s_%sfinal.txt' % (month, year)

        if os.path.isfile(month_meta_file_final):
            os.remove(month_meta_file_final)
        if os.path.isfile(scene_request_list_final):
            os.remove(scene_request_list_final)

        finallist = open(scene_request_list_final, 'w')
        with open(month_meta_file_final, 'wb') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            for row in finaldict:
                writer.writerow(row)
                finallist.write(row['scene'] + '\n')
        finallist.close()
        return 1, scene_request_list_final, month_meta_file_final
    else:
        return 2, 2, 2




def pickscene(scene_cloud_dict):
    sorted_scene_cloud = sorted(scene_cloud_dict.items(), key=operator.itemgetter(1))
    print('sorted_scene_cloud = ')
    print sorted_scene_cloud
    winning_scene = sorted_scene_cloud[0][0]
    all_scenes = scene_cloud_dict.keys()
    losing_scenes = all_scenes.remove(winning_scene)
    return winning_scene, losing_scenes
