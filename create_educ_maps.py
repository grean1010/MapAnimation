#######################################################################################
## Title:   create_educ_maps.py
## Author:  Maria Cupples Hudson
## Purpose: Read historical education data from spreadsheets into a dataframe
##          Merge with geojson files to map by county, color by % with 4-year degree
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
## Import Education data by county 
#######################################################################################

xlsfile = os.path.join(raw_loc,'EducationByCounty2.xls')
xl = pd.ExcelFile(xlsfile)
edu = xl.parse('Education 1970 to 2017')
cols_in = edu.columns

print('Original Column Names:')
print(cols_in)
cols_rename = []

for col in cols_in:
    if col == 'FIPS Code':
        cols_rename.append('FIPS')  
    elif col == 'State':
        cols_rename.append('StateAbbr')  
    elif col == 'Area name':
        cols_rename.append('CountyName')  

    elif col == 'Percent of adults with less than a high school diploma, 1970':
        cols_rename.append('1970_LTHS')
    elif col == 'Percent of adults with a high school diploma only, 1970':
        cols_rename.append('1970_HS')
    elif col == 'Percent of adults completing some college (1-3 years), 1970':
        cols_rename.append('1970_SomeColl')
    elif col == 'Percent of adults completing four years of college or higher, 1970':
        cols_rename.append('1970_GRAD')

    elif col == 'Percent of adults with less than a high school diploma, 1980':
        cols_rename.append('1980_LTHS')
    elif col == 'Percent of adults with a high school diploma only, 1980':
        cols_rename.append('1980_HS')
    elif col == 'Percent of adults completing some college (1-3 years), 1980':
        cols_rename.append('1980_SomeColl')
    elif col == 'Percent of adults completing four years of college or higher, 1980':
        cols_rename.append('1980_GRAD')
        
    elif col == 'Percent of adults with less than a high school diploma, 1990':
        cols_rename.append('1990_LTHS')
    elif col == 'Percent of adults with a high school diploma only, 1990':
        cols_rename.append('1990_HS')
    elif col == "Percent of adults completing some college or associate's degree, 1990":
        cols_rename.append('1990_SomeColl')
    elif col == "Percent of adults with a bachelor's degree or higher, 1990":
        cols_rename.append('1990_GRAD')        

    elif col == 'Percent of adults with less than a high school diploma, 2000':
        cols_rename.append('2000_LTHS')
    elif col == 'Percent of adults with a high school diploma only, 2000':
        cols_rename.append('2000_HS')
    elif col == "Percent of adults completing some college or associate's degree, 2000":
        cols_rename.append('2000_SomeColl')
    elif col == "Percent of adults with a bachelor's degree or higher, 2000":
        cols_rename.append('2000_GRAD')        

    elif col == 'Percent of adults with less than a high school diploma, 2013-17':
        cols_rename.append('2013_LTHS')
    elif col == 'Percent of adults with a high school diploma only, 2013-17':
        cols_rename.append('2013_HS')
    elif col == "Percent of adults completing some college or associate's degree, 2013-17":
        cols_rename.append('2013_SomeColl')
    elif col == "Percent of adults with a bachelor's degree or higher, 2013-17":
        cols_rename.append('2013_GRAD')        
        
    else:
        cols_rename.append('DROP')


print('Renamed Column Names:')
print(cols_rename)
        
edu.columns = cols_rename
edu.drop(columns =['DROP'], inplace = True) 
edu["In Edu"] = 1

# Make sure the fips codes have leading zeros.
for obs in range(0,len(edu)):
    if len(str(edu.loc[obs,'FIPS'])) == 4:
        edu.loc[obs,'FIPS'] = f"0{edu.loc[obs,'FIPS']}"
    else:
        edu.loc[obs,'FIPS'] = f"{edu.loc[obs,'FIPS']}"
        
    # FIPS code 0 for nation or last 3 digit 000 indicate state total
    if len(str(edu.loc[obs,'FIPS'])) == 1:
        edu.loc[obs,'FIPS'] = "DROP"
    elif edu.loc[obs,'FIPS'][2:5] == '000':
        edu.loc[obs,'FIPS'] = "DROP"

    # 46113 was renamed from Shannon County to Oglala Lakota County, SD in May 2015.  Oglala should have FIPS 46102 but
    # 46102 is not found on the big geojson file so we reset 46102 to 46113.
    if str(edu.loc[obs,'FIPS']) == '46102':
        edu.loc[obs,'FIPS'] = '46113'

# Drop state and national total lines
edu = edu.loc[edu["FIPS"] != 'DROP',:]

final_cols =edu.columns.to_list()
print(final_cols)

#######################################################################################
## Create a function to set county color based on change in per-capita income
#######################################################################################

def edu_colors(feature):
    
    try: 
        test_value = feature['properties']['GRAD']
    except:
        test_value = -1
        
    #print(test_value)
    
    """Maps low values to green and high values to red."""
    if test_value > 45:
        return '#543005' 
    elif test_value > 30:
        return '#8c510a'
    elif test_value > 30:
        return '#bf812d'
    elif test_value > 25:
        return  '#dfc27d' 
    elif test_value > 20:
        return '#f6e8c3'
    elif test_value > 15:
        return '#c7eae5'
    elif test_value > 10:
        return '#80cdc1'
    elif test_value > 7:
        return '#35978f'
    elif test_value > 5:
        return '#01665e' 
    elif test_value > 0:
        return '#003c30'
    else:
        return "#lightgray"

#######################################################################################
## Create html text to generate a legend for the same colors
#######################################################################################
edu_legend_html = '''
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

     <i style="background: #543005"> &nbsp &nbsp</i> 45+ <br>
     <i style="background: #8c510a"> &nbsp &nbsp</i> 40 - 45<br>
     <i style="background: #bf812d"> &nbsp &nbsp</i> 30 - 40<br>
     <i style="background: #dfc27d"> &nbsp &nbsp</i> 25 - 30<br>
     <i style="background: #f6e8c3"> &nbsp &nbsp</i> 20 - 25<br>
     <i style="background: #c7eae5"> &nbsp &nbsp</i> 15 - 20<br>
     <i style="background: #80cdc1"> &nbsp &nbsp</i> 10 - 15<br>
     <i style="background: #35978f"> &nbsp &nbsp</i> 7 - 10<br>
     <i style="background: #01665e"> &nbsp &nbsp</i> 5 - 7<br>
     <i style="background: #003c30"> &nbsp &nbsp</i> 0 - 5<br>
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

    json_output = os.path.join(clean_loc,f'EDUGeoFile{year2check}.json')
    save_html = os.path.join(map_html,f'EDUMap_{year2check}.html')
    save_png = os.path.join(map_png,f'EDUMap_{year2check}.png')

    ratedata4timepoint = {}

    # Loop through the dataframe and add information to the data2add dictionary. 
    # We will use this to put these values into the geojson.
    for row, rowvals in edu.iterrows():
        
        # pull the fips code from the first entry in the row
        FIPS = rowvals[0]
    
        # If we have not previously seen this fips code, add it ot the dictionary
        if FIPS not in ratedata4timepoint:
            ratedata4timepoint[FIPS]={}
            
        # pull county name, state abbreviation and the per-capita income amount and for this timepoint
        ratedata4timepoint[FIPS]['CountyName'] = rowvals[final_cols.index('CountyName')]
        ratedata4timepoint[FIPS]['GRAD'] = rowvals[final_cols.index(f'{year2check}_GRAD')]  
        ratedata4timepoint[FIPS]['LTHS'] = rowvals[final_cols.index(f'{year2check}_LTHS')]  
        ratedata4timepoint[FIPS]['HS'] = rowvals[final_cols.index(f'{year2check}_HS')]  
        ratedata4timepoint[FIPS]['SomeColl'] = rowvals[final_cols.index(f'{year2check}_SomeColl')]  
            
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
    tip_fields = ['CountyName','LTHS','HS','SomeColl','GRAD']
    tip_aliases = ['County Name:', f'% with less than high school {year2check}', f'% completing high school {year2check}',\
                    f'% with some college {year2check}',f'% with college degree or higher {year2check}']

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
                                            'fillColor': edu_colors(feature),
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

make_map('1970',edu_legend_html)
make_map('1980',edu_legend_html)
make_map('1990',edu_legend_html)
make_map('2000',edu_legend_html)
make_map('2013',edu_legend_html)