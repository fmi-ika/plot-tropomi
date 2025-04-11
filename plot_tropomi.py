import os
import json
import argparse
import datetime
import logging
import time
import csv
import shapefile

import harp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.image as image
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import natural_earth, Reader
import cmcrameri.cm as cmc
from shapely.geometry import shape
from cartopy.feature import ShapelyFeature
from cartopy.io import shapereader
from shapely.geometry import LineString


def read_file(infile, conf, timeperiod):
    """ Read satellite data and configure from files
                                                                                 
    Keyword arguments: 
    infile -- satellite data file
    conf -- config dictionary
    timeperiod -- length of merged data to plot, options: day|month

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
    logger.debug(f'Reading data file {infile}')    
    try:
        data = harp.import_product(infile)        
    except Exception as e:
        logger.error(f'Error while reading the data file {infile}')
        logger.error(e)
    
    # Read observation data and its description and unit
    obs_data = data[conf["input"][timeperiod]["harp_var_name"]].data
    obs_data = obs_data.squeeze()
    description = data[conf["input"][timeperiod]["harp_var_name"]].description
    unit = data[conf["input"][timeperiod]["harp_var_name"]].unit
    
    # Get min value if min_value in conf and mark values under it np.nan
    plot_conf = conf["plot"][timeperiod]
    min_value = plot_conf.get("min_value")
    if min_value:
        obs_data[obs_data < min_value] = np.nan
    
    # Read lat and lon data
    latitudes = data.latitude.data
    longitudes = data.longitude.data

    # Read datetimes and convert "since epochdate" to timestamp
    epochdate = conf["input"][timeperiod]["epochdate"]
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
    

def plot_data(figname, latitudes, longitudes, obs_data, description, unit, conf, timeperiod, datetime_start, datetime_stop, logos, fmi_logo):
    """ Plot satellite data and logos

    Keyword arguments:
    figname -- filename for saving plot
    latitudes -- observation latitude data
    longitudes -- observation longitude data
    obs_data -- data values
    description -- data description
    unit -- data unit
    conf -- config dictionary
    timeperiod -- length of merged data to plot, options: day|month
    datetime_start -- first timestamp of data
    datetime_stop -- last timestamp of data
    logos -- logos image to be added in the picture
 
    """

    # Read config plot parameter
    vmin = conf["plot"][timeperiod]["vmin"]
    vmax = conf["plot"][timeperiod]["vmax"]
    colormap = conf["plot"][timeperiod]["colormap"]
    
    print("np.nanmin(obs_data)", np.nanmin(obs_data))
    print("np.nanmax(obs_data)", np.nanmax(obs_data))
    
    # Create plot
    logger.debug('Plotting image')
    fig, axs = plt.subplots(figsize=(20,10))

    # Plot map
    ax = plt.axes(projection = ccrs.PlateCarree())
    ax.set_extent([-180, 180, -90, 90], ccrs.PlateCarree())
    img = plt.pcolormesh(longitudes, latitudes, obs_data, vmin = vmin, vmax = vmax, cmap = colormap, transform = ccrs.PlateCarree())
    ax.coastlines()
    ax.gridlines()
    ax.set_title(f"L3 merged product of {description} \n First timestamp: {datetime_start}   Last timestamp: {datetime_stop}", fontsize=16)

    # Add colorbar
    cbar = fig.colorbar(img, fraction=0.046, pad=0.02, shrink=0.91, aspect=20*0.91)
    cbar.set_label(f'{description} [{unit}]',fontsize=15)
    cbar.ax.tick_params(labelsize=14)

    # Add logos
    newax = fig.add_axes([0.13, 0.07, 0.5, 0.05], anchor='SW')
    newax.imshow(logos)
    newax2 = fig.add_axes([0.13, 0.87, 0.5, 0.05], anchor='SW')
    newax2.imshow(fmi_logo)

    # Remove extra axis
    newax.axis('off')
    newax2.axis('off')
    axs.axis('off')

    # Save figure to file
    logger.debug(f'Save image to file {figname}')
    fig.savefig(figname, bbox_inches = 'tight') #, dpi = 300)


def plot_data_ukraine(figname, latitudes, longitudes, obs_data, description, unit, conf, timeperiod, datetime_start, datetime_stop, logos, fmi_logo):
    """ 
    Plot satellite data with country borders and major city names.
    
    Parameters:
    figname -- filename for saving plot
    latitudes -- observation latitude data
    longitudes -- observation longitude data
    obs_data -- data values
    description -- data description
    unit -- data unit
    conf -- config dictionary
    timeperiod -- length of merged data to plot, options: day|month
    datetime_start -- first timestamp of data
    datetime_stop -- last timestamp of data
    logos -- logos image to be added in the picture
    fmi_logo -- FMI logo image to be added in the picture
    """

    # Read config plot parameters
    vmin = conf["plot"][timeperiod]["vmin"]
    vmax = conf["plot"][timeperiod]["vmax"]
    colormap = conf["plot"][timeperiod]["colormap"]

    logger.debug("Plotting image")
    fig, ax = plt.subplots(figsize=(20, 20), facecolor='w', edgecolor='w', subplot_kw={'projection': ccrs.PlateCarree()})
    
    # Set map extent to Ukraine region
    ax.set_extent([21, 41.1, 44, 53.5], crs=ccrs.PlateCarree())

    # Plot country borders from Geojson files
    for country in ["Belarus", "Moldova", "Romania", "Slovakia", "Hungary", "Poland", "Russia", "Ukraine"]:
    
        # Load the GeoJSON file
        with open(f"{country}_border.geojson") as f:
            geojson_data = json.load(f)

        # Extract geometries
        geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

        # Create a shapely feature from geometries
        if country == "Ukraine":
            country_feature = ShapelyFeature(geometries,
                                 ccrs.PlateCarree(),
                                 edgecolor='black',
                                 facecolor='none',
                                 linewidth=2.5)
        else:
            country_feature = ShapelyFeature(geometries,
                                 ccrs.PlateCarree(),
                                 edgecolor='gray',
                                 facecolor='none',
                                 linewidth=1) 

        # Add the country feature
        ax.add_feature(country_feature)
    
    # Plot roads, exclude ferry routes
    roads_path = natural_earth(resolution='10m',
                           category='cultural',
                           name='roads')
    for record in Reader(roads_path).records():
        road_type = record.attributes.get('type')
        if road_type != 'Ferry Route':
            ax.add_geometries([record.geometry], crs=ccrs.PlateCarree(),
                          edgecolor='lightgray', linewidth=0.6, facecolor='none')

    # Plot observation data
    img = ax.pcolormesh(longitudes, latitudes, obs_data, vmin=vmin, vmax=vmax, cmap=colormap, transform=ccrs.PlateCarree())

    # Add coastline
    ax.add_feature(cfeature.COASTLINE, linewidth=1, edgecolor="black")
    
    # Add major cities
    csv_filename = "ukraine_cities.csv"
    city_names = []
    latitudes = []
    longitudes = []

    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            city_names.append(row[0])
            latitudes.append(float(row[1]))
            longitudes.append(float(row[2]))
            
    for i, (lat, lon) in enumerate(zip(latitudes, longitudes)):
        ax.plot(lon, lat, 'o',
            markersize=10,
            markeredgecolor='#252525',
            markerfacecolor='none',
            zorder=9)
    for i, (lat, lon) in enumerate(zip(latitudes, longitudes)):
        if city_names[i] == 'Zaporizhzhia':
            # For Zaporizhzhia, position the label below the marker
            txt = ax.annotate(city_names[i], (lon, lat), textcoords="offset points", xytext=(10, -20), ha='center',
                              fontsize=16, color="#525252", weight="bold", zorder=10)
        elif city_names[i] == 'Kyiv':
            txt = ax.annotate(city_names[i], (lon, lat), textcoords="offset points", xytext=(10, 13), ha='center',
                              fontsize=20, color="#525252", weight="bold", zorder=10)
        else:
            # Default label position
            txt = ax.annotate(city_names[i], (lon, lat), textcoords="offset points", xytext=(10, 10), ha='center',
                              fontsize=16, color="#525252", weight="bold", zorder=10)

    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.right_labels = False
    gl.top_labels = False

    # Title
    ax.set_title(f"L3 merged product of {description} \n First timestamp: {datetime_start}   Last timestamp: {datetime_stop}", fontsize=16)

    # Add colorbar
    cbar = fig.colorbar(img, fraction=0.046, pad=0.02, shrink=0.91, aspect=20 * 0.91)
    cbar.set_label(f'{description} [{unit}]', fontsize=15)
    cbar.ax.tick_params(labelsize=14)

    # Add logos
    newax = fig.add_axes([0.13, 0.07, 0.5, 0.05], anchor='SW')
    newax.imshow(logos)
    newax2 = fig.add_axes([0.13, 0.87, 0.5, 0.05], anchor='SW')
    newax2.imshow(fmi_logo)

    # Remove axis from logos
    newax.axis('off')
    newax2.axis('off')

    # Save figure to file
    logger.debug(f'Saving image to file {figname}')
    fig.savefig(figname, bbox_inches='tight')



def main():

    # Read config file into dictionary
    config_file = f"conf/{options.var}.json"
    logger.debug(f'Reading config file {config_file}')
    try:
        with open(config_file, "r") as jsonfile:
            conf = json.load(jsonfile)
    except Exception as e:
        logger.error(f'Error while reading the configuration file {config_file}')
        logger.error(e)
        
    # Read data and logos
    timeperiod = options.timeperiod
    infile = f'{conf["input"][timeperiod]["path"]}/{conf["input"][timeperiod]["filename"].format(date = options.date)}'
    latitudes, longitudes, obs_data, description, unit, datetime_start, datetime_stop = read_file(infile, conf, timeperiod)
    fmi_logo = image.imread("fmi_logo.png")
    logos = image.imread("logos.png")

    # Plot data
    figname = f'{conf["output"][timeperiod]["path"]}/{conf["output"][timeperiod]["filename"].format(date = options.date)}'
    if not "ukraine" in options.var:
        plot_data(figname, latitudes, longitudes, obs_data, description, unit, conf, timeperiod, datetime_start, datetime_stop, logos, fmi_logo)
    else:
        plot_data_ukraine(figname, latitudes, longitudes, obs_data, description, unit, conf, timeperiod, datetime_start, datetime_stop, logos, fmi_logo)
    

if __name__ == '__main__':
    #Parse commandline arguments  
    parser = argparse.ArgumentParser()
    parser.add_argument('--var',
                        type = str,
                        default = 'so2-nrti',
                        help = 'Tropomi variable to plot. Options: no2-nrti, so2-nrti, co-nrti, o3-nrti')
    parser.add_argument('--date',
                        type = str,
                        default = '20230209',
                        help = 'Date to plot.')
    parser.add_argument('--timeperiod',
                        type = str,
                        default = 'day',
                        help = 'Time period to plot. Options: day|month')
    parser.add_argument('--loglevel',
                        default='info',
                        help='minimum severity of logged messages,\
                        options: debug, info, warning, error, critical, default=info')


    options = parser.parse_args()

    # Setup logger
    loglevel_dict={'debug':logging.DEBUG,
                   'info':logging.INFO,
                   'warning':logging.WARNING,
                   'error':logging.ERROR,
                   'critical':logging.CRITICAL}

    logger = logging.getLogger("logger")
    logger.setLevel(loglevel_dict[options.loglevel])
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s | (%(filename)s:%(lineno)d)','%Y-%m-%d %H:%M:%S')
    logging.Formatter.converter = time.gmtime # use utc                                                                    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    main()
