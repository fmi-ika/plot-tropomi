import os
import json
import argparse
import datetime

import harp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.image as image
import cartopy.crs as ccrs
import cmcrameri.cm as cmc


def read_file(infile, conf):
    """ Read satellite data and configure from files
                                                                                 
    Keyword arguments: 
    infile -- satellite data file
    conf -- config dictionary

    Return:                        
    latitudes -- observation latitude data
    longitudes -- observation longitude data
    obs_data -- data values
    description -- data description
    unit -- data unit
    datetime_start -- first timestamp of data
    datetime_stop -- last timestamp of data
 
    """

    # Open file with HARP
    data = harp.import_product(infile)

    # Read observation data and its description and unit
    obs_data = data[conf["input"]["harp_var_name"]].data
    description = data[conf["input"]["harp_var_name"]].description
    unit = data[conf["input"]["harp_var_name"]].unit    

    # Read lat and lon data
    latitudes = data.latitude.data
    longitudes = data.longitude.data

    # Read datetimes and convert "since epochdate" to timestamp
    epochdate = conf["input"]["epochdate"]
    datetime_start = dayssince_to_timestamp(epochdate, data.datetime_start.data[0])
    datetime_stop = dayssince_to_timestamp(epochdate, data.datetime_stop.data[0])

    return latitudes, longitudes, obs_data, description, unit, datetime_start, datetime_stop


def dayssince_to_timestamp(epochdate, dayssince):
    """ Convert days since epochdate to timestamp
                                                                                 
    Keyword arguments: 
    epochdate -- date from which days since is calculated in format %Y%m%d
    dayssince -- number of days (can be decimal) since epochdate

    Return:                        
    timestamp -- timestamp corresponding to dayssince
 
    """    

    epochdate = datetime.datetime.strptime(epochdate,"%Y%m%d")
    timestamp = (epochdate + datetime.timedelta(days=dayssince)).strftime('%Y-%m-%d %H:%M')

    return timestamp
    

def plot_data(figname, latitudes, longitudes, obs_data, description, unit, conf, datetime_start, datetime_stop, logos):
    """ Plot satellite data and logos

    Keyword arguments:
    figname -- filename for saving plot
    latitudes -- observation latitude data
    longitudes -- observation longitude data
    obs_data -- data values
    description -- data description
    unit -- data unit
    conf -- config dictionary
    datetime_start -- first timestamp of data
    datetime_stop -- last timestamp of data
    logos -- logos image to be added in the picture
 
    """

    # Read config plot parameters
    vmin = conf["plot"]["vmin"]
    vmax = conf["plot"]["vmax"]
    colormap = conf["plot"]["colormap"]

    # Create plot
    fig, axs = plt.subplots(figsize=(20,10))
    fig.suptitle(f"L3 merged product of {description} \n Times between {datetime_start} and {datetime_stop}", fontsize=20)    

    # Plot map
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-180, 180, -90, 90], ccrs.PlateCarree())
    img = plt.pcolormesh(longitudes, latitudes, obs_data[0,:,:], vmin=vmin, vmax=vmax, cmap=colormap, transform=ccrs.PlateCarree())
    ax.coastlines()
    ax.gridlines()

    # Add colorbar
    cbar = fig.colorbar(img, ax=ax,orientation='vertical', fraction=0.04, pad=0.1)
    cbar.set_label(f'{description} [{unit}]',fontsize=14)
    cbar.ax.tick_params(labelsize=14)

    # Add logos
    newax = fig.add_axes([0.01, 0.01, 0.2, 0.2], anchor='SW')
    newax.imshow(logos)

    # Remove extra axis
    newax.axis('off')
    axs.axis('off')

    # Save figure to file
    fig.savefig(figname)


def main():

    # Read config file into dictionary
    config_file = f"conf/{options.var}.json"
    with open(config_file, "r") as jsonfile:
        conf = json.load(jsonfile)

    # Read data and logos
    infile = f'{conf["input"]["path"]}/{conf["input"]["filename"].format(date = options.date)}'
    latitudes, longitudes, obs_data, description, unit, datetime_start, datetime_stop = read_file(infile, conf)
    logos = image.imread("logos.png")

    # Plot data
    figname = f'{conf["output"]["path"]}/{conf["output"]["filename"].format(date = options.date)}'
    plot_data(figname, latitudes, longitudes, obs_data, description, unit, conf, datetime_start, datetime_stop, logos)
        

if __name__ == '__main__':
    #Parse commandline arguments  
    parser = argparse.ArgumentParser()
    parser.add_argument('--var',
                        type = str,
                        default = 'no2-nrti',
                        help = 'Tropomi variable to plot. Options: no2-nrti, so2-nrti, co-nrti, o3-nrti')
    parser.add_argument('--date',
                        type = str,
                        default = '20221102',
                        help = 'Date to plot.')

    options = parser.parse_args()
    main()
