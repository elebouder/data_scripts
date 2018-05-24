import os
import csv
from datetime import datetime


officialList = 'U:/Fracking Pads/Well_Surface_Hole_Locations_Permitted.csv'
trainingList = 'U:/Fracking Pads/trainingSites.csv'



minlon = -126.7000
maxlon = -120.0000

minlat = 54.3000
maxlat = 60.0000

min_status_effective = datetime(2013, 05, 01)
bore_type = ['OIL', 'GAS']

fields = ['X',
          'Y',
          'WELL_ACTIVITY',
          'BORE_FLUID_TYPE',
          'STATUS_EFFECTIVE_DATE']

newfields = ['Lon',
             'Lat',
             'CurrentStatus',
             'BoreType',
             'EffectiveDate']

dictionary = []

with open(officialList, 'rb') as readlist:
    reader = csv.DictReader(readlist)
    for row in reader:
        lon = float(row['X'])
        lat = float(row['Y'])
        activity = row['WELL_ACTIVITY']
        fluid_type = row['BORE_FLUID_TYPE']
        date = row['STATUS_EFFECTIVE_DATE']
        date_format = datetime(int(date[0:4]), int(date[5:7]), int(date[8:10]))

        if(minlon < lon < maxlon and
           minlat < lat < maxlat and
           fluid_type in bore_type and
           date_format > min_status_effective):
            print lon, lat, activity, fluid_type, date, date_format
            dictionary.append({'Lat': lat,
                               'Lon': lon,
                               'CurrentStatus': activity,
                               'BoreType': fluid_type,
                               'EffectiveDate': date})
for row in dictionary:
    print(row)
print len(dictionary)

if os._exists(trainingList):
    os.remove(trainingList)

with open(trainingList, 'wb') as writelist:
    writer = csv.DictWriter(writelist, fieldnames=newfields)
    writer.writeheader()
    for dicts in dictionary:
        writer.writerow(dicts)



