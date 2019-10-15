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
import sys
import json
import csv 
import os
import math
import time
from selenium import webdriver

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
    elif col in ('Series ID','Region Name') or col[0:3] in ('198','197'):
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

#######################################################################################
## Create a function to set county color based on unemployment value
#######################################################################################

def unemp_colors(feature):
    
    try: 
        test_value = temp_dict[feature['properties']['FIPS']]
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
## Create a function to produce maps for each time period
## 1. As an html file
## 2. As a png file (by navigating to the html file and taking a screen shot)
#######################################################################################
