import imageio
import glob
import os
from PIL import Image 

base_loc = os.path.join('C:\\','Users','laslo','OneDrive','Documents','Maria','MapAnimation')
png_path = os.path.join(base_loc,'map_png')
temp_file = os.path.join(png_path,'temp.png')

def animate_map(name2find,fileout,fpsvalue):

    # Go through the images and find the smallest height and width
    fileList = []
    min_h = 10000
    min_w = 10000

    # Go through the list of png files for this animation
    for file in os.listdir(png_path):
    
        if file.startswith(name2find):
        
            # Find the complete path name of each image and add to the list
            complete_path = os.path.join(png_path,file)        
            fileList.append(complete_path)
        
            # check to see if this is the lowers height/width so far. Update if it is.
            img = Image.open(complete_path) 
            width, height = img.size
        
            if width < min_w:
                min_w = width
    
            if height < min_h:
                min_h = height

    # Create a writer for the animation file/mp4
    writer = imageio.get_writer(f'{fileout}.mp4', fps=fpsvalue)

    # Go through the list of png files to add to the animation
    for im in fileList:
    
        # to resize and set the new width and height 
        img = Image.open(im)

        # find the current image size
        width, height = img.size

        # resize withe same center so that all files are at the same/minimum size
        top = int((height - min_h)/2)
        bottom = int(height - (height - min_h)/2)
        left = int((width - min_w)/2)
        right = int(width - (width - min_w)/2)

        # perform the crop and save to a temporary file
        cropped = img.crop((left,top,right,bottom))
        cropped.save(temp_file)
    
    # add the temporary file to the animation
    writer.append_data(imageio.imread(temp_file))
    
    # finalize and close the animation
    writer.close()

animate_map('PCPI','PCPI_Animation',1)