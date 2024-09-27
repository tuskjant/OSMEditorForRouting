# GIS Integral de Transport: Architecture Overview
This repository it's one main part of the GIS Integral de Transport System: Here is hosted and described the GIS Integral de Transport Editor.

## 1.System Context 
The GIS Integral Transport System is designed to provide route planning and network maintenance functionality for users. It consists of two main interacting systems: GIS Integral de Transport Viewer and GIS Integral de Transport Editor used by two user types.
<!---![Context diagram](/docs/diagrams/c4/01_Context.png) --->
<img src="/docs/diagrams/c4/01_Context.png" alt="Context diagram" width="300"/>

### Main Actors
+ **Route Planner:** A user who needs to find the optimal route between two or more locations.
+ **Network Maintenance Operator:** A user responsible for editing and updating the road network using the Editor.
### Internal systems
+ **GIS Integral de Transport Viewer:** Map viewer that allows users to plan routes and visualize them on the map by selecting two or more points. This system is located in [this repository](https://github.com/tuskjant/gis_transport_visor)
+ **GIS Integral de Transport Editor:** Allows network operators to edit road data and update the routing network. This system is located and described in this repository.
### External systems
+ **Open Source Routing Machine:** The routing engine that calculates the routes. [OSRM backend](https://github.com/Project-OSRM/osrm-backend)

## 2. GIS Integral de transport Editor: Container diagram 
The Editor container provides functionality for editing the road network and handling OSM data, interfacing with the database and external tools like Osmosis and OSRM.
<!---![Editor container diagram](/docs/diagrams/c4/02_ContainersEditor.png)--->
<img src="/docs/diagrams/c4/02_ContainersEditor.png" alt="Editor container diagram" width="300"/>

+ **QGIS Core:** The geographic information system aplication used for visualizing and editing the network data.
+ **OSRM Editor Plugin:** A custom QGIS plugin developed to allow the network modification: editing and adding new network segments. It handles OSM data processing and conversion for use with OSRM interacting with Osmosis utility and OSRM server.
+ **Osmosis:** External tool used to process OSM data: read and write to the database and OSM data format conversion. [Osmosis](https://github.com/openstreetmap/osmosis)
+ **PostgreSQL with PostGIS:** The database used to store OSM data, including ways, nodes, and relations. 

## 3. OSRM Editor Plugin: Components diagram
The Editor plugin is composed of modular components that handle specific tasks. Each component is responsible for different aspects of the road network editing workflow, from data conversion to map updates.
<!---![OSRM Editor Plugin component diagram](/docs/diagrams/c4/03_EditorComponents.png)--->
<img src="/docs/diagrams/c4/03_EditorComponents.png" alt="OSRM Editor Plugin component diagram" width="300"/>

+ **UI Component:** The graphical user interface for the QGIS plugin. Created using Qt designer for QGIS.
+ **Data Handler:** Manages the import, export, and conversion of OSM data making calls to Osmosis utility and OSRM tools.
+ **Select Feature Tool:** QGIS tool that allows the operator to select specific segments from the road network.
+ **Way Feature Handle:** Handles operations related to existing way features. Update attributes and reverse geometry.
+ **New Segment Handler:** Manages the creation, modification, and updating of new road segments.
+ **Database Functions:** Handles all interactions with the PostgreSQL/PostGIS database, including querying, inserting, updating, and deleting data. Use psycopg2 library.
+ **Routing Editor Component:**  Coordinates the core data processing logic interacting with other components. 

## The database: PostgreSQL 
PostgreSQL has been used as the OSM data store for QGIS. The PostGIS extension is used to handle geographic components, and the hstore extension manages the tags from OpenStreetMap data. The Python psycopg2 library is used to interact with the database.

OSM data in PBF format is loaded into the database using the Osmosis tool. The schema created by Osmosis includes the tables "Ways," "Nodes," and "Way-Nodes," which are edited through the plugin.
<!---![Esquema Osmosis de la base de datos](/docs/diagrams/database/db_relations.PNG)--->
<img src="/docs/diagrams/database/db_relations.PNG" alt="Esquema Osmosis de la base de datos" width="300"/>

## Technologies and Libraries Used
The plugin is developed in Python using the PyQGIS library as the main framework. For the user interface, Qt Designer for QGIS has been used. The plugin [Plugin Builder](https://plugins.qgis.org/plugins/pluginbuilder/) has been used to create the initial plugin template.

