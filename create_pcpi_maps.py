#######################################################################################
## Title:   create_pcpi_maps.py
## Author:  Maria Cupples Hudson
## Purpose: Read historical yearly per-capita income from spreadsheets into a dataframe
##          Merge with geojson files to map by county, color code by change in PCPI
##          Create HTML maps, then take PNG screenshot
## Updates: 10/22/2019 Code Written 
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
## Import Per Capita Income data by county and month
#######################################################################################

xlsfile = os.path.join(raw_loc,'GeoFRED_Per_Capita_Personal_Income_by_County_Dollars2.xls')
xl = pd.ExcelFile(xlsfile)
pcpi = xl.parse('Sheet0')
cols_in = pcpi.columns
cols_rename = []

for col in cols_in:
    if col == 'Region Code':
        cols_rename.append('FIPS')
    elif col == 'Region Name':
        cols_rename.append('CountyName')
    elif col == 'Series ID':
        cols_rename.append('DROP')
    elif int(col) >= 2001:
        cols_rename.append(f"PCPI_{col}")
    else:
        cols_rename.append('DROP')

pcpi.columns = cols_rename
pcpi.drop(columns =['DROP'], inplace = True) 

# Make sure the fips codes have leading zeros.
for obs in range(0,len(pcpi)):
    if len(str(pcpi.loc[obs,'FIPS'])) == 4:
        pcpi.loc[obs,'FIPS'] = f"0{pcpi.loc[obs,'FIPS']}"
    else:
        pcpi.loc[obs,'FIPS'] = f"{pcpi.loc[obs,'FIPS']}"
        
    # 46113 was renamed from Shannon County to Oglala Lakota County, SD in May 2015.  Oglala should have FIPS 46102 but
    # 46102 is not found on the big geojson file so we reset 46102 to 46113.
    if str(pcpi.loc[obs,'FIPS']) == '46102':
        pcpi.loc[obs,'FIPS'] = '46113'
        
    # Calculate percent change in PCPI
    for year in range (2002,2018):
        pyear = year - 1
        pcpi.loc[obs,f'PCPI_PctChange_{year}'] = round(100 * (pcpi.loc[obs,f'PCPI_{year}'] - pcpi.loc[obs,f'PCPI_{pyear}'])/pcpi.loc[obs,f'PCPI_{year}'],2)

pcpi_final_cols = pcpi.columns.to_list()
print(pcpi_final_cols)

#######################################################################################
## Create a function to set county color based on change in per-capita income
#######################################################################################

def pcpi_colors(feature):
    
    try: 
        test_value = feature['properties']['PCPI_PctChange']
    except:
        test_value = -1
        
    #print(test_value)
    
    """Maps low values to green and high values to red."""
    if test_value > 15:
        return '#006837' 
    elif test_value > 10:
        return '#1a9850'
    elif test_value > 5:
        return '#66bd63'
    elif test_value > 3:
        return  '#a6d96a' 
    elif test_value > 0:
        return '#d9ef8b'
    elif test_value > -3:
        return '#fee08b'
    elif test_value > -5:
        return '#fdae61'
    elif test_value > -10:
        return '#f46d43'
    elif test_value > -15:
        return '#d73027' 
    elif test_value > -99:
        return '#a50026'
    else:
        return "#lightgray"

#######################################################################################
## Create html text to generate a legend for the same colors
#######################################################################################
pcpi_legend_html = '''
     <div style="position: fixed; 
                 bottom: 5%;
                 right: 5%;
                 z-index: 1000;
                 padding: 6px 8px;
                 width: 85px;
                 font: 12px Arial, Helvetica, sans-serif;
                 font-weight: bold;
                 background: #8d8a8d;
                 border-radius: 5px;
                 box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
                 line-height: 18px;
                 color: 'black';">

     <i style="background: #006837"> &nbsp &nbsp</i> 15+ <br>
     <i style="background: #1a9850"> &nbsp &nbsp</i> 10 to 15<br>
     <i style="background: #66bd63"> &nbsp &nbsp</i> 5 to 10<br>
     <i style="background: #a6d96a"> &nbsp &nbsp</i> 3 to 5<br>
     <i style="background: #d9ef8b"> &nbsp &nbsp</i> 0 to 3<br>
     <i style="background: #fee08b"> &nbsp &nbsp</i> -3 to 0<br>
     <i style="background: #fdae61"> &nbsp &nbsp</i> -5 to -3<br>
     <i style="background: #f46d43"> &nbsp &nbsp</i> -10 t0 -5<br>
     <i style="background: #d73027"> &nbsp &nbsp</i> -15 to -10<br>
     <i style="background: #a50026"> &nbsp &nbsp</i> < -15<br>
      </div>
     '''
    
#######################################################################################
## Create a function to create a map for each point in time and save as html and png
#######################################################################################

def make_map(timepoint,legend_html):

    import datetime
    import folium
    import json
    
    # pull the year from the date variable
    year2check = int(timepoint[0:4])
    pyear = year2check - 1

    # Pull the year and month from the timepoint 
    yearpoint = timepoint[0:4]

    json_input = os.path.join(clean_loc,f'FinalGeoFile{year2check}0101.json')

    json_output = os.path.join(clean_loc,f'PCPIGeoFile{year2check}.json')
    save_html = os.path.join(map_html,f'PCPIMap_{year2check}.html')
    save_png = os.path.join(map_png,f'PCPIMap_{year2check}.png')

    ratedata4timepoint = {}

    # Loop through the dataframe and add information to the data2add dictionary. 
    # We will use this to put these values into the geojson.
    for row, rowvals in pcpi.iterrows():
        
        # pull the fips code from the first entry in the row
        FIPS = rowvals[1]
    
        # If we have not previously seen this fips code, add it ot the dictionary
        if FIPS not in ratedata4timepoint:
            ratedata4timepoint[FIPS]={}
            
        # pull county name, state abbreviation and the per-capita income amount and for this timepoint
        ratedata4timepoint[FIPS]['CountyName'] = rowvals[pcpi_final_cols.index('CountyName')]
        ratedata4timepoint[FIPS]['PCPI'] = rowvals[pcpi_final_cols.index(f'PCPI_{year2check}')]  
        ratedata4timepoint[FIPS]['PCPI_Previous'] = rowvals[pcpi_final_cols.index(f'PCPI_{pyear}')]  
        ratedata4timepoint[FIPS]['PCPI_PctChange'] = rowvals[pcpi_final_cols.index(f'PCPI_PctChange_{year2check}')]  
            
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

    # Create a list of fields to be included in the tooltip and a list of descriptions for those variables
    # Use the name of the variable to determine the tooltip list contents
    tip_fields = ['CountyName','PCPI_Previous','PCPI','PCPI_PctChange']
    tip_aliases = ['County Name:', f'PerCapita Income {pyear}', f'PerCapita Income {year}',f'Percent Change {pyear} to {year2check}']

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
        <h3><b>{yearpoint}</b></h3></div>'''

    m.get_root().html.add_child(folium.Element(title_html))

    # Add the legend that was created in the main program
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.GeoJson(json_output,
                   style_function=lambda feature: {
                                            'fillColor': pcpi_colors(feature),
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

#for year in range(2008,2018):
    # Call the function to create the html and png maps
    #make_map(f'{year}', pcpi_legend_html)

make_map('2009',pcpi_legend_html)