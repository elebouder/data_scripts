import preprocess_main as prep
import clipraster_main as clip
import os
import sys
import postgresql_access as db


def main():
    unpacked_products_path = 'U:/Fracking Pads/Unpacked Downloaded Products'
    outputdataset = 'U:/Fracking Pads/trialtrainingrasters'
    intermediary_scene_dataset = 'U:/Fracking Pads/RGB Scenes Ready for Site-Lifting'
    bands = [4, 3, 2, 8]

    ### EITHER
    ### 1) use the temporal type 'months' (specifying a distinct list of months
    #######and years to pick run through), or
    ### 2) pick a beginning and end date and have everthing on file within that interval
    ####### as data ('period')
    ### the choice is made by initializing temporal type as 'months' or 'period'
    #TODO: build support in the sql db writing for handling multiple months

    months = [[7, 2015]]

    start_month = []
    end_month = []

    temporal_type = 'months'
    scenes_ready2clip = []


    if temporal_type == 'months':
        print 'number of months is: ', len(months)
        for month in months:
            filename = '%s_%s' % (month[0], month[1])
            filepath1 = unpacked_products_path + '/' + filename
            for scene in os.listdir(filepath1):
                print 'working on scene' + scene
                filepath2 = filepath1 + '/' + scene
                finishedScene = prep.preprocess(bands, filepath2, scene, intermediary_scene_dataset)
                scenes_ready2clip.append([scene, finishedScene, month[0], month[1]])
    elif temporal_type == 'period':
        print 'searching by period'
        mlist = []
        for dct in os.listdir(unpacked_products_path):
            splt = dct.split('_')
            m = splt[0]
            yr = splt[-1]
            if (start_month[1] <= yr <= end_month[1] and
                start_month[0] <= m <= end_month[0]):
                mlist.append([dct, m, yr])
        print 'number of months is: ', len(mlist)
        for l in mlist:
            m = l[0]
            filename = m
            filepath1 = unpacked_products_path + '/' + filename
            for scene in os.listdir(filepath1):
                print 'working on scene' + scene
                filepath2 = filepath1 + '/' + scene
                finishedScene = prep.preprocess(bands, filepath2, scene, intermediary_scene_dataset)
                scenes_ready2clip.append([scene, finishedScene, l[1], l[2]])
    else:
        print 'enter one of "months" or "period" for temporal_type'
        sys.exit(1)

    print'finished preprocessing steps'
    print'beginning site extraction'
    for files in os.listdir(intermediary_scene_dataset):            #temp code start
        print files
        if files.endswith('.tif'):
            sceneraster = intermediary_scene_dataset + '/' + files
            scene = files.split('.')[0]
            scenes_ready2clip.append([scene, sceneraster, 7, 2015])          #temp code end

    for elem in scenes_ready2clip:
        print 'extracting: ', elem
        sceneID = elem[0]
        sceneraster = elem[1]
        month = elem[2]
        yr = elem[3]
        sitesfor_sqldb = clip.extract(outputdataset, sceneID, sceneraster)
        #[db.into_db(site[0], site[1], sceneID, month, yr) for site in sitesfor_sqldb]
        #[db.into_file_db(site[0], site[1], sceneID, month, yr) for site in sitesfor_sqldb]
    #sitepaths is a full list of all the freshly processed sites, to be written into postgis db





if __name__ == '__main__':
    main()
