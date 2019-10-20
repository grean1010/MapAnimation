#######################################################################################
## Title:   create_timepoint_geojson.py
## Author:  Maria Cupples Hudson
## Purpose: Create json files for distinct points in time using historical shape
##          files downloaded from the Atlas of Historical County Boudaries. This code
##          creates a function that can be called by other programs.
## Updates: 10/14/2019 Code Written
##
#######################################################################################
##
## Shape files were downloaded from this site:
##   https://publications.newberry.org/ahcbp/downloads/united_states.html
##
## Next, we turned these into geojson format by using this site:
##   https://mapshaper.org/
##
## The resulting json files are the input to this program.
## 
## Dependencies:  json, datetime
##
#######################################################################################
import sys
import json
import os
import datetime

# Set locations for raw and clean data folders.
raw_loc = os.path.join('RawData')
clean_loc = os.path.join('CleanData')

# File location for the downloaded geojson file. Note that we used the .05 degree tolerance
# version of the file.  More finely detailed, but larger files have the same structure and
# could be subtituted here.
big_geojson = os.path.join('..','countyMapData','US_HistCounties_Gen05.json')

# Create a geojson file for a given point in time by pulling records from the big/historical
# geojson file and keeping only records that were active as of that date.  Note that the 
# historical file covers years 1629 to 2000.
def create_timepoint_geojson(timepoint):
    
    # create a reference to the output file
    outfile = os.path.join(clean_loc,f'FinalGeoFile{timepoint}.json')

    print(f"Creating output geojson file {outfile}")

    # Create a numeric version of the date to check against
    date2check = datetime.date(int(timepoint[0:4]), int(timepoint[4:6]), int(timepoint[6:8]))

    # Create a blank list of the features we will keep
    features = []
    
    # Open up the existing geojson file and read it into the empty geojson dictionary
    # created above. While reading it in, pull the matching state and county fips from
    # the data2add dictionary so we can add the unemployment info to the geojson.
    with open(big_geojson, 'r') as f:
        temp = json.load(f)
        
        for feature in temp['features']:
            
            featureProperties = feature['properties']
            FIPS = featureProperties['FIPS']
            STATEFP = featureProperties['FIPS'][0:2]
            COUNTYFP = featureProperties['FIPS'][2:6]

            # pull everything after the first dash
            char_start_mmdd = featureProperties["START_DATE"][(featureProperties["START_DATE"]).find('-') + 1:]
            char_end_mmdd = featureProperties["END_DATE"][(featureProperties["END_DATE"]).find('-') + 1:]
            
            # There should be a dash between the month and day. If so, pick off the month and day.  If not, default to January 1st.
            if char_start_mmdd.find('-') > -1:
                char_start_month = char_start_mmdd[0:char_start_mmdd.find('-')]
                char_start_day = char_start_mmdd[char_start_mmdd.find('-') + 1:char_start_mmdd.find('T')]
            else:
                char_start_month = '01'
                char_start_day = '01'

            if char_end_mmdd.find('-') > -1:
                char_end_month = char_end_mmdd[0:char_end_mmdd.find('-')]
                char_end_day = char_end_mmdd[char_end_mmdd.find('-') + 1:char_end_mmdd.find('T')]
            else:
                char_end_month = '01'
                char_end_day = '01'

            # pull the start and stop dates for the current record in the big geojson
            start_date = datetime.date(int(featureProperties["START_DATE"][0:4]), int(char_start_month), int(char_start_day))
            end_date = datetime.date(int(featureProperties["END_DATE"][0:4]), int(char_end_month), int(char_end_day))
            
            # Add the state and county fips codes so this json will look like the ones for later years from Census
            featureProperties['STATEFP'] = STATEFP
            featureProperties['COUNTYFP'] = COUNTYFP
        
            if start_date <= date2check and date2check <= end_date:
                features.append(feature)
                
    last_feature = len(features)-1
                
    # Output a new geojson file specific to this year.
    with open(outfile,'w') as f:
        f.write('{"type":"FeatureCollection","features": [')
        for feature in features:
            json.dump(feature, f)
            if features.index(feature) < last_feature:
                f.write(',')
        f.write(']}')


create_timepoint_geojson('19900101')

#create_timepoint_geojson('19700101')
#create_timepoint_geojson('19800101')
#for year in range(1990,2001):
#    for month in range(1,10):
#        create_timepoint_geojson(f'{year}0{month}01')  
#    for month in range(10,13):
#        create_timepoint_geojson(f'{year}{month}01')  