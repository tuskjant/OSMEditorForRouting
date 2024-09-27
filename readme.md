# OSM Routing Editor
## Overview
OSM Routing Editor is a QGIS plugin that provides functionalities to prepare OpenStreetMap (OSM) data for use with the OSRM routing server. The data in OSM format is loaded into the database using Osmosis, which then allows for the editing of the data to modify the routing graph by changing parameters that affect route calculations, such as traffic direction, speed, and access. It also enables the creation of new network segments by graphically editing their positions.

Once the data has been edited, it is exported back to PBF format and converted into routing network data for use by the OSRM calculation engine. The data served by OSRM can be accessed through the [Gis Integral de Transport Viewer](https://github.com/tuskjant/gis_transport_visor).


## Usage
See [user guide](/docs/usage.md) for instructions.

## Installation
QGIS installation is required. QGIS minimum version: 3.0
+ Download the zip file and from the QGIS Plugin Manager select Install from ZIP file.

or

+ Download this repository and copy it into the QGIS plugin location (QGIS_PLUGINPATH). Restart QGIS and add the pluggin from the Plugin Manager. 

## External Dependencies
For full functionality of the plugin, it is necessary to have the Osmosis utility and the OSRM server installed.

## Development
See [architecture overview](/docs/architecture-overview.md) for details.