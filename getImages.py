import wget
from datetime import timedelta, datetime
import numpy as np
import sys
from PIL import Image
import os
#url = 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/20d/550/2019/07/27/094000_8_0.png'

base_url = 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/{1}d/550/{0:%Y/%m/%d/%H%M%S}_{2}_{3}.png'
#filepath = 'C:/Users/<username>/Documents/Himawari8Downloader/'
filepath = os.getcwd()+'/'


resolution=20 # best resolution: 20, valid: [1, 2, 4, 8, 16, 20]
#startdate
year=2019
month=7
day=26
hour=0
minutes=0 #multiple of 10

number_of_frames=500
number=1 #at what frame to start. Default: 1
#usefull to continue after e.g. an network-error

start_tile_x=6
start_tile_y=0

number_of_tiles_x=4
number_of_tiles_y=3


def removeTempFiles():
    filelist = [ f for f in os.listdir(filepath+'temp/') if f.endswith(".png") ]
    for f in filelist:
        os.remove(os.path.join(filepath+'temp/', f))

def mergeImages(number):
    images = [[Image.open(filepath+'temp/{0}-{1}.png'.format(x,y)) for x in np.arange(number_of_tiles_x)+start_tile_x] for y in np.arange(number_of_tiles_y)+start_tile_y] 
    total_width = 550*number_of_tiles_x
    max_height = 550*number_of_tiles_y

    new_im = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    y_offset = 0
    for x in np.arange(number_of_tiles_x):
        x_offset=x*550
        for y in np.arange(number_of_tiles_y)+start_tile_y:
            y_offset=y*550
            new_im.paste(images[y][x], (x_offset,y_offset))

    new_im.save(filepath+'Result/{0:04d}.png'.format(number))
    removeTempFiles()





start_date = datetime(year, month, day, hour, minutes, 0)

if not os.path.exists(filepath+'Result/'):
    os.makedirs(filepath+'Result/')
if not os.path.exists(filepath+'temp/'):
    os.makedirs(filepath+'temp/')
removeTempFiles()

for td in (start_date + timedelta(minutes=10*it) for it in range(number-1,number_of_frames)):
    for tile_x in np.arange(number_of_tiles_x)+start_tile_x:
        for tile_y in np.arange(number_of_tiles_y)+start_tile_y:
            filename = wget.download(base_url.format(td,resolution,tile_x,tile_y),filepath+'temp/{0}-{1}.png'.format(tile_x,tile_y))
    mergeImages(number)
    number=number+1
