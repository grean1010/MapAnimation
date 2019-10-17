#######################################################################################
## Title:   create_timepoint_maps.py
## Author:  Maria Cupples Hudson
## Purpose: Create county-level, color-coded maps in HTML and PNG format for distinct
##          points in time.  This program creates a function that can be called by
##          other programs.
## Updates: 10/15/2019 Code Written
##
#######################################################################################
## 
## Dependencies:  os, folium, json, datetime, time, webdriver from selenium
##
#######################################################################################

# Inputs to make_map function:
# timepoint:  the date we are mapping in format yyyymm
# json_input: a file reference to the geojson file to be used
# var_to_plot:  the name of the column we will use to color the counties
# save_html:  file reference for the html map to be created 
# save_png:  file reference for the png map to be created 
# color_function: Name of the function used to color the counties
# legend_html: text to use as the legend

def make_map(timepoint,data_to_map,json_input,var_to_plot,save_html,save_png,color_function,legend_html):

    import datetime
    import folium
    import json

    #print(data_to_map['22001'])

    # Add the data we will be mapping to the json file
    # Create a blank geojson that we will build up with the existing one plus the new information
    geojson = {}
    
    # Open up the existing geojson file and read it into the empty geojson dictionary created above.
    # While reading it in, pull the matching fips from the data_to_map dictionary so we can add the
    # variable as a feature/property in the geojson.
    with open(json_input, 'r') as f:
        geojson = json.load(f)
        for feature in geojson['features']:
            featureProperties = feature['properties']
            FIPS = featureProperties['FIPS']
            
            featureData = data_to_map.get(FIPS, {})
            for key in featureData.keys():
                featureProperties[key] = featureData[key]

    # Output this updated geojson.
    with open(json_input, 'w') as f:
        json.dump(geojson, f)

    # Pull the year and month from the timepoint 
    yearpoint = timepoint[0:4]
    monthpoint = datetime.date(int(timepoint[0:4]), int(timepoint[4:6]), 1).strftime('%B')

    # Create a list of fields to be included in the tooltip and a list of descriptions for those variables
    # Use the name of the variable to determine the tooltip list contents
    if var_to_plot[0:5] == 'Unemp':
        tip_fields = ['FULL_NAME','STATE_TERR',var_to_plot]
        tip_aliases = ['County Name:', 'State:',f'Unemployment Rate {monthpoint} {yearpoint}:']
    else:
        tip_fields = ['FULL_NAME','STATE_TERR',var_to_plot]
        tip_aliases = ['County Name:', 'State:',var_to_plot]

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

    folium.GeoJson(json_input,
                    style_function=lambda feature: {
                                            'fillColor': color_function(feature),
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