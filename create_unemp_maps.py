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

#######################################################################################
## Create a function to set county color based on unemployment value
#######################################################################################

def unemp_colors(feature):
    
    try: 
        test_value = feature['properties']['UnemploymentRate']
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
## Create a function to create a map for each point in time and save as html and png
#######################################################################################

def make_map(timepoint,legend_html):

    import datetime
    import folium
    import json

    #print(data_to_map['22001'])

    json_input = os.path.join(clean_loc,f'FinalGeoFile{timepoint}01.json')
    json_output = os.path.join(clean_loc,f'UnempGeoFile{timepoint}01.json')
    save_html = os.path.join(map_html,f'UnemploymentMap_{timepoint}.html')
    save_png = os.path.join(map_png,f'UnemploymentMap_{timepoint}.png')
    
    ratedata4timepoint = {}

    # Loop through the dataframe and add information to the data2add dictionary. 
    # We will use this to put these values into the geojson.
    for row, rowvals in unemp.iterrows():
        
        # pull the fips code from the first entry in the row
        FIPS = rowvals[0]
    
        # If we have not previously seen this fips code, add it ot the dictionary
        if FIPS not in ratedata4timepoint:
            ratedata4timepoint[FIPS]={}
            
        # pull county name, state abbreviation and the unemployment rate for this timepoint
        ratedata4timepoint[FIPS]['CountyName'] = rowvals[cols_reorder.index('CountyName')]   
        ratedata4timepoint[FIPS]['StateAbbr'] = rowvals[cols_reorder.index('StateAbbr')]  
        ratedata4timepoint[FIPS]['UnemploymentRate'] = rowvals[cols_reorder.index(f'Unemp_{timepoint}')]  
            
    # Add the data we will be mapping to the json file
    # Create a blank geojson that we will build up with the existing one plus the new information
    geojson = {}
    
    # Open up the existing geojson file and read it into the empty geojson dictionary created above.
    # While reading it in, pull the matching fips from the data2add dictionary so we can add the
    # variable as a feature/property in the geojson.
    with open(json_input, 'r') as f:
        geojson = json.load(f)
        for feature in geojson['features']:
            featureProperties = feature['properties']
            FIPS = featureProperties['FIPS']

            featureData = ratedata4timepoint.get(FIPS, {})
            for key in featureData.keys():
                featureProperties[key] = featureData[key]
                
    # Output this updated geojson.
    with open(json_output, 'w') as f:
        json.dump(geojson, f)

    # Pull the year and month from the timepoint 
    yearpoint = timepoint[0:4]
    monthpoint = datetime.date(int(timepoint[0:4]), int(timepoint[4:6]), 1).strftime('%B')

    # Create a list of fields to be included in the tooltip and a list of descriptions for those variables
    # Use the name of the variable to determine the tooltip list contents
    tip_fields = ['CountyName','StateAbbr','UnemploymentRate']
    tip_aliases = ['County Name:', 'State:',f'Unemployment Rate {monthpoint}, {yearpoint}:']

    m = folium.Map([43,-100], tiles='cartodbpositron', zoom_start=4.25)

    # Display the month on the top of the page
    title_html = f'''
        <div style="position: fixed; 
                 bottom: 90%;
                 right: 50%;
                 align: center;
                 z-index: 1001;
                 padding: 6px 8px;
                 font: 40px Arial, Helvetica, sans-serif;
                 font-weight: bold;
                 line-height: 18px;
                 color: 'black';">
        <h3><b>{yearpoint} Month {timepoint[4:6]}</b></h3></div>'''

    m.get_root().html.add_child(folium.Element(title_html))

    # Add the legend that was created in the main program
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.GeoJson(json_output,
                   style_function=lambda feature: {
                                            'fillColor': unemp_colors(feature),
                                            'fillOpacity' : '0.9',
                                            'color' : 'black',
                                            'weight' : 1
                                            },   
                    highlight_function=lambda x: {'weight':2,'fillOpacity':1},    
                    tooltip=folium.features.GeoJsonTooltip(
                                            fields=tip_fields,
                                            aliases=tip_aliases)      
    ).add_to(m)

    # Save the map to an html file
    m.save(save_html)

    # Open a browser window...
    browser = webdriver.Chrome()

    #..that displays the map...
    browser.get(save_html)

    # Give the map tiles some time to load
    time.sleep(5)

    # Grab the screenshot and save it as a png file
    browser.save_screenshot(save_png)
    
    # Close the browser
    browser.quit()

    
#######################################################################################
## Create maps for each month and year from 1990 through 2000
#######################################################################################

for year in range(1990,2000):

    for m in range(1,13): 
        month = m
        if m < 10:
            month = f'0{m}'

        # Call the function to create the html and png maps
        make_map(f'{year}{month}', unemp_legend_html)
