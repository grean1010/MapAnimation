#######################################################################################
## Title:   create_timepoint_geojson_after2000.py
## Author:  Maria Cupples Hudson
## Purpose: Create json files for distinct points in time using historical shape
##          files downloaded from the Atlas of Historical County Boudaries. This code
##          creates a function that can be called by other programs.
##          Note that this program focuses on years after 2000, which were not part
##          of the download from the aAtlas of Historical County Boudaries.  Instead
##          these files were downloaded from the Census Bureau.
## Updates: 10/14/2019 Code Written
##
#######################################################################################
##
## Shape files were downloaded from this site:
##   https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.2000.html
##
## Next, we turned these into geojson format by using this site:
##   https://mapshaper.org/
##
## The resulting json files are the input to this program.
## 
## Dependencies:  json, datetime, os
##
#######################################################################################\
import json
import os
import datetime

# Set locations for raw and clean data folders.
raw_loc = os.path.join('RawData')
clean_loc = os.path.join('CleanData')

# File location for the downloaded geojson file. Note that we used the .05 degree tolerance
# version of the file.  More finely detailed, but larger files have the same structure and
# could be subtituted here.
json_loc = os.path.join('..','countyMapData')

# Create a geojson file for a given point in time by pulling records from the big/historical
# geojson file and keeping only records that were active as of that date.  Note that the 
# historical file covers years 1629 to 2000.
def create_timepoint_geojson(timepoint):
    
    # create a reference to the output file
    outfile = os.path.join(clean_loc,f'FinalGeoFile{timepoint}.json')

    print(f"Creating output geojson file {outfile}")

    # pull the year from the date variable
    year2check = int(timepoint[0:4])
    
    # for years greater than 2000 we also need the two digit year
    yr = str(year2check)[2:4]
    
    # create a reference to the input geojson file. Different years have different files/formats
    if year2check <= 2000:
        infile = os.path.join(json_loc,f'FinalGeoFile{year2check}.json')
    elif year2check <= 2009:
        infile = os.path.join(json_loc,f'co99_d00.json')
    elif year2check < 2013:
        infile = os.path.join(json_loc,f'gz_2010_us_050_00_20m.json')
    elif year2check <= 2018:
        infile = os.path.join(json_loc,f'cb_{year2check}_us_county_20m.json')
    else:
        infile = os.path.join(json_loc,f'cb_2018_us_county_20m.json')

    print(f"Creating geojson file for timepoint: {timepoint}")
    print(f"infile = {infile}")
    print(f"outfile = {outfile}")
   
    # Create a blank geojson for the final result
    geojson = {}
        
    # Open up the existing geojson file and read it into the empty geojson dictionary
    # created above. While reading it in, pull the matching state and county fips from
    # the data2add dictionary so we can add the unemployment info to the geojson.
    with open(infile, 'r') as f:
        geojson = json.load(f)
        
        for feature in geojson['features']:
            
            featureProperties = feature['properties']
            if year2check <= 2000:
                FIPS = featureProperties['FIPS']
                STATEFP = str(FIPS)[0:2]
                COUNTYFP = str(FIPS)[2:5]
            elif year2check <= 2012:
                STATEFP = featureProperties['STATE']
                COUNTYFP = featureProperties['COUNTY']
                FIPS = STATEFP + COUNTYFP
            else:
                STATEFP = featureProperties['STATEFP']
                COUNTYFP = featureProperties['COUNTYFP']
                FIPS = STATEFP + COUNTYFP
            
            # Make sure FIPS, STATEFP, and COUNTYFP are all consistently defined
            featureProperties['FIPS'] = FIPS
            featureProperties['STATEFP'] = STATEFP
            featureProperties['COUNTYFP'] = COUNTYFP
                
    # Output a new geojson file specific to this year.
    # Output this updated geojson.
    with open(outfile, 'w') as f:
        json.dump(geojson, f)

for year in range(2001,2010):
    create_timepoint_geojson(f'{year}0101')  