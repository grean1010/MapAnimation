# Animating County-Level Maps Using Python and Follium

This project is a work in progress.  I am expanding on work done as part of a data analytics project to create videos of animated maps. 

[![US Unemployment Rates by County 1990 - 2019](https://img.youtube.com/vi/Si6AaTbcIXQ/0.jpg)](https://www.youtube.com/watch?v=Si6AaTbcIXQ)

[![US Year over Year Change in Per-Capita Income by County 2002 - 2017](https://youtu.be/h3zXQxbX1Zk)](https://youtu.be/h3zXQxbX1Zk)

[![US Education Level by County 1970 - 2017](https://youtu.be/UTE-9tPcTls)](https://youtu.be/UTE-9tPcTls)

If link does not work, please go to the animations folder and download mp4 to see the animation. 


## Shape files were downloaded from this site:
   https://publications.newberry.org/ahcbp/downloads/united_states.html

## Next, I turned these into geojson format by using this site:
   https://mapshaper.org/

## I generated year and month specific geojson files
Using the start and stop dates on the large geojson file I created monthly geojson files at the county level from 1990 through 2000.  Then I merged county-level information (education, unemployment, per-capita income) onto those json files.

I used Python/Follium to create HTML maps for each month between March 1990 and July 2019.  Then using selenium I opened each file in a web browser and took a screen shot.  Finally, I reshaped and combined these images using PIL/Image and then put them together into an mp4 file using imageio.  

There is still a lot of cleaning up to do and many more animations to do!