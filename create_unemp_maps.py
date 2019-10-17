#######################################################################################
## Title:   create_unemp_maps.py
## Author:  Maria Cupples Hudson
## Purpose: Read historical monthly unemployment from spreadsheets into a dataframe\
## Updates: 10/14/2019 Code Written
##
#######################################################################################
##
##
#######################################################################################
import folium
import pandas as pd
import json
import csv 
import os
import time
import datetime
from selenium import webdriver
from create_timepoint_maps import make_map

# location of this folder on the hard drive
base_loc = os.path.join('C:\\','Users','laslo','OneDrive','Documents','Maria','MapAnimation')

# Set locations for raw and clean data folders.
raw_loc = os.path.join('RawData')
clean_loc = os.path.join('CleanData')

map_html = os.path.join(base_loc,'map_html')
map_png = os.path.join(base_loc,'map_png')

#######################################################################################
## Import Unemployment data by county and month
#######################################################################################

# Read each of three sheets into a data frame
xlsfile = os.path.join(raw_loc,'GeoFRED_Unemployment_Rate_by_County_Percent2.xls')
xl = pd.ExcelFile(xlsfile)
df0 = xl.parse('Sheet0')
df0.drop(columns =['Series ID'], inplace = True) 

df1 = xl.parse('Sheet1')
df1.drop(columns =['Series ID','Region Name'], inplace = True) 

df2 = xl.parse('Sheet2')
df2.drop(columns =['Series ID','Region Name'], inplace = True) 

# merge the three data fames by region code (which is county-fips)
unemp = pd.merge(df0,pd.merge(df1,df2,on='Region Code'),on='Region Code')

# Pull the column names and prepare list for renaming
cols_in = unemp.columns
cols_rename = []

# Use the column titles to either rename to desired name or flag the column to be dropped
for col in cols_in:
    
    if col == 'Region Code':
        cols_rename.append('FIPS')
    elif col == 'Region Name':
        cols_rename.append('CountyName')
    elif col == 'Series ID' or col[0:3] in ('198','197'):
        cols_rename.append('DROP')
    elif "January" in col:
        cols_rename.append(f"Unemp_{col[0:4]}01")
    elif "February" in col:
        cols_rename.append(f"Unemp_{col[0:4]}02")
    elif "March" in col:
        cols_rename.append(f"Unemp_{col[0:4]}03")
    elif "April" in col:
        cols_rename.append(f"Unemp_{col[0:4]}04")
    elif "May" in col:
        cols_rename.append(f"Unemp_{col[0:4]}05")
    elif "June" in col:
        cols_rename.append(f"Unemp_{col[0:4]}06")
    elif "July" in col:
        cols_rename.append(f"Unemp_{col[0:4]}07")
    elif "August" in col:
        cols_rename.append(f"Unemp_{col[0:4]}08")
    elif "September" in col:
        cols_rename.append(f"Unemp_{col[0:4]}09")
    elif "October" in col:
        cols_rename.append(f"Unemp_{col[0:4]}10")
    elif "November" in col:
        cols_rename.append(f"Unemp_{col[0:4]}11")
    elif "December" in col:
        cols_rename.append(f"Unemp_{col[0:4]}12")
    else:
        cols_rename.append(col)

# Reset the column names
unemp.columns = cols_rename

# Get rid of dropped columns
unemp.drop(columns =['DROP'], inplace = True) 

# Initialize county and state fips and state abbreviation as character
unemp['STATEFP'] = ''
unemp['COUNTYFP'] = ''
unemp['StateAbbr'] = ''

# Make sure the fips codes have leading zeros. Excel drops these if it considered it a numeric value.
for obs in range(0,len(unemp)):
    if len(str(unemp.loc[obs,'FIPS'])) == 4:
        unemp.loc[obs,'FIPS'] = f"0{unemp.loc[obs,'FIPS']}"
    else:
        unemp.loc[obs,'FIPS'] = f"{unemp.loc[obs,'FIPS']}"
        
    # 46113 was renamed from Shannon County to Oglala Lakota County, SD in May 2015.  Oglala should have FIPS 46102 but
    # 46102 is not found on the big geojson file so we reset 46102 to 46113.
    if str(unemp.loc[obs,'FIPS']) == '46102':
        unemp.loc[obs,'FIPS'] = '46113'

    # set county/state fips
    unemp.loc[obs,'COUNTYFP'] = unemp.loc[obs,'FIPS'][2:5]
    unemp.loc[obs,'STATEFP'] = unemp.loc[obs,'FIPS'][0:2]

    # separate out the state abbreviation and county name
    unemp.loc[obs,'StateAbbr'] = unemp.loc[obs,'CountyName'][-2:]
    unemp.loc[obs,'CountyName'] = unemp.loc[obs,'CountyName'][:-4]
  
# Grab the current column order
cols_reorder = unemp.columns.to_list()

# take out the columns we are moving to the front
cols_reorder.remove('STATEFP')
cols_reorder.remove('COUNTYFP')
cols_reorder.remove('FIPS')
cols_reorder.remove('StateAbbr')
cols_reorder.remove('CountyName')

# Move the columns we want to the front
cols_reorder.insert(0,'StateAbbr')
cols_reorder.insert(0,'CountyName')
cols_reorder.insert(0,'COUNTYFP')
cols_reorder.insert(0,'STATEFP')
cols_reorder.insert(0,'FIPS')

# reset the column order
unemp = unemp[cols_reorder]

# set the FIPS code as the index
unemp = unemp.set_index('FIPS')
fnl_cols = unemp.columns.to_list()

# recreate the unemployment data as a dictionary so it can be tacked onto a geojson file
#data2add = unemp[fnl_cols].T.to_dict('dict')
#print(data2add['45001'])

data2add = {}

# Loop through the dataframe and add information to the data2add dictionary. 
# We will use this to put these values into the geojson.
for row, rowvals in unemp.iterrows():
        
    FIPS = rowvals[0]
    
    if FIPS not in data2add:
        data2add[FIPS]={}
            
    # pull information from dataframe into temporary variables
    for vname in fnl_cols:
        data2add[FIPS][f'{vname}'] = rowvals[fnl_cols.index(f'{vname}')]   

print(data2add['45001'])
#######################################################################################
## Create a function to set county color based on unemployment value
#######################################################################################

def unemp_colors(feature):
    
    try: 
        test_value = data_to_map[feature['properties']['FIPS']]
    except:
        test_value = -1
        
    #print(test_value)
    
    """Maps low values to green and hugh values to red."""
    if test_value > 9:
        return '#a50026' 
    elif test_value > 8:
        return '#d73027'
    elif test_value > 7:
        return '#f46d43'
    elif test_value > 6:
        return  '#fdae61' 
    elif test_value > 5:
        return '#fee08b'
    elif test_value > 4:
        return '#d9ef8b'
    elif test_value > 3:
        return '#a6d96a'
    elif test_value > 2:
        return '#66bd63'
    elif test_value > 1:
        return '#1a9850' 
    elif test_value > 0:
        return '#006837'
    else:
        return "#lightgray"

#######################################################################################
## Create html text to generate a legend for the same colors
#######################################################################################
unemp_legend_html = '''
     <div style="position: fixed; 
                 bottom: 5%;
                 right: 5%;
                 z-index: 1000;
                 padding: 6px 8px;
                 width: 60px;
                 font: 12px Arial, Helvetica, sans-serif;
                 font-weight: bold;
                 background: #8d8a8d;
                 border-radius: 5px;
                 box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
                 line-height: 18px;
                 color: 'black';">

     <i style="background: #a50026"> &nbsp &nbsp</i> 9+ <br>
     <i style="background: #d73027"> &nbsp &nbsp</i> 8 - 9<br>
     <i style="background: #f46d43"> &nbsp &nbsp</i> 7 - 8<br>
     <i style="background: #fdae61"> &nbsp &nbsp</i> 6 - 7<br>
     <i style="background: #fee08b"> &nbsp &nbsp</i> 5 - 6<br>
     <i style="background: #d9ef8b"> &nbsp &nbsp</i> 4 - 5<br>
     <i style="background: #a6d96a"> &nbsp &nbsp</i> 3 - 4<br>
     <i style="background: #66bd63"> &nbsp &nbsp</i> 2 - 3<br>
     <i style="background: #1a9850"> &nbsp &nbsp</i> 1 - 2<br>
     <i style="background: #006837"> &nbsp &nbsp</i> 0 - 1<br>
      </div>
     '''
    
#######################################################################################
## Create maps for each month and year from 1990 through 2000
#######################################################################################

for year in range(1991,1992):

    for m in range(1,13):
        month = m
        if m < 10:
            month = f'0{m}'

        # Call the function to create the html and png maps
        make_map(f'{year}{month}',\
                data2add,\
                os.path.join(clean_loc,\
                f'FinalGeoFile{year}{month}01.json'),\
                f'Unemp_{year}{month}',\
                os.path.join(map_html,f'UnemploymentMap_{year}{month}.html'),\
                os.path.join(map_png,f'UnemploymentMap_{year}{month}.png'),\
                unemp_colors,\
                unemp_legend_html)