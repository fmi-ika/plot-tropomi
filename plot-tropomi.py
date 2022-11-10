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
from cmcrameri import cm


def read_file(infile, conf):

    data = harp.import_product(infile)
    gridlat = data.latitude.data
    gridlon = data.longitude.data
    epochdate = conf["input"]["epochdate"]
    datetime_start = dayssince_to_timestamp(epochdate, data.datetime_start.data[0])
    datetime_stop = dayssince_to_timestamp(epochdate, data.datetime_stop.data[0])
    val = data[conf["input"]["harp_var_name"]].data
    description = data[conf["input"]["harp_var_name"]].description
    unit = data[conf["input"]["harp_var_name"]].unit

    return gridlat, gridlon, val, description, unit, datetime_start, datetime_stop


def dayssince_to_timestamp(epochdate, dayssince):

    epochdate = datetime.datetime.strptime(epochdate,"%Y%m%d")
    timestamp = (epochdate + datetime.timedelta(days=dayssince)).strftime('%Y%m%d%H%M')

    return timestamp
    

def plot_data(figname, gridlat, gridlon, val, description, unit, conf, datetime_start, datetime_stop, logos):
    
    colortable = cm.lajolla

    vmin = conf["plot"]["vmin"]
    vmax = conf["plot"]["vmax"]

    fig, axs = plt.subplots(figsize=(20,10))
    
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-180, 180, -90, 90], ccrs.PlateCarree())

    img = plt.pcolormesh(gridlon, gridlat, val[0,:,:], vmin=vmin, vmax=vmax, cmap=colortable, transform=ccrs.PlateCarree())
    ax.coastlines()
    ax.gridlines()

    cbar = fig.colorbar(img, ax=ax,orientation='vertical', fraction=0.04, pad=0.1)
    cbar.set_label(f'{description} [{unit}]')
    cbar.ax.tick_params(labelsize=14)

    # Add logos
    newax = fig.add_axes([0.01, 0.01, 0.2, 0.2], anchor='SW')
    newax.imshow(logos)

    newax.axis('off')
    axs.axis('off')
    
    fig.suptitle(f"{description}, L3 merged product, {datetime_start}-{datetime_stop}", fontsize=20)
    
    fig.savefig(figname)


def main():

    # Get config           
    config_file = f"conf/{options.var}.json"
    with open(config_file, "r") as jsonfile:
        conf = json.load(jsonfile)

    # Read data and logos
    infile = f'{conf["input"]["path"]}/{conf["input"]["filename"].format(date = options.date)}'
    print("infile: ", infile)
    gridlat, gridlon, val, description, unit, datetime_start, datetime_stop = read_file(infile, conf)
    logos = image.imread("logos.png")

    # Convert days since to timestamp
    dayssince_to_timestamp(epochdate="20000101", dayssince=8341.00196253472)

    # Plot data
    figname = f'{conf["output"]["path"]}/{conf["output"]["filename"].format(date = options.date)}'
    plot_data(figname, gridlat, gridlon, val, description, unit, conf, datetime_start, datetime_stop, logos)
        

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
