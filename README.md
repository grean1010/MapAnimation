# Animating County-Level Maps Using Python and Follium

This project is a work in progress.  I am expanding on work done as part of a data analytics project to create videos of animated maps. 


![US Unemployment Rates by County 1990 - 2019](animations/UnemploymentAnimation.mp4)


## Shape files were downloaded from this site:
   https://publications.newberry.org/ahcbp/downloads/united_states.html

## Next, we turned these into geojson format by using this site:
   https://mapshaper.org/

## We generated year and month specific geojson files
Using the start and stop dates on the large geojson file we created monthly geojson files at the county level from 1990 through 2000.  Then we merged county-level information (education, unemployment, per-capita income) onto those json files.

We used Python/Follium to create HTML maps for each month between March 1990 and July 2019.  Then using selenium we opened each file in a web browser and took a screen shot.  Finally, we reshaped and combined these images using PIL/Image and then put them together into an mp4 file using imageio.  

There is still a lot of cleaning up to do and many more animations to do!