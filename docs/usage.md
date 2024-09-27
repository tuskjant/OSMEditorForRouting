# Detailed usage
This page describes the options available for the OSRM Editor plugin.

## Workflow
1. Load OpenStreetMap (OSM) data into the database
2. Add the network layer to the map
3. Edit – modify the layer using the plugin's tools
4. Export the layer and convert it to the format used by OSRM
5. *[Launch the OSRM server with the newly modified data]*
6. *[Calculate routes from the GIS Integral de Transport Viewer]* 


## Data Loading
OSM data for the area of interest in PBF format can be loaded into the database from the **Load pbf to database** tab. The connection parameters should be entered beforehand in **Settings**. The PBF file is specified in *Input OSM pbf file*.
OSM data can be downloaded using the plugin *OSMDownloader*, and in that case, it can be converted from OSM to PBF using **Convert osm to pbf**.
<img src="/docs/images/data_management.PNG" alt="Data management" width="400">

Once the data is in the database, the network layer to be used for route calculation is added to the map via **Add ways layer**. This layer is created by filtering OSM data to show only the elements considered for routing. A style is applied to the layer to highlight the editable attributes.
<img src="/docs/images/layers.PNG" alt="layers" width="200"> 

## Edit network segments
Click **Select road** and choose the network segments on the map that you want to edit. For each selected segment, the routing-related data will be displayed. Batch editing is supported, allowing you to permit or deny access to the segment, set it as one-way or two-way, define the maximum speed, and change the direction of traffic flow.
Edited segments will be marked as modified, and the original information will be stored in the tags attribute, making it possible to restore the previous data at any time using **Undo changes**.
To deselect the segments, click **Select road** again.
<img src="/docs/images/editsegment.PNG" alt="Edit layer" width="400">.

## Add new network segments
For adding new segments to the network, go to the Add segment tab and click **Add segment**. This will activate the tool to add a segment, with snapping enabled to existing segments. Once the segment is added graphically to the temporary layer, you can edit its attributes: segment type, traffic flow, and speed. To add the segment to the database, click **Create Segment**, and to delete it, click **Delete Segment**.
<img src="/docs/images/addsegment.PNG" alt="Edit layer" width="400">.

## Prepare data for OSRM routing engine
Once the data has been modified, it can be exported from the database to pbf format (using Osmosis). In Settings, select the **Output OSM pbf folder** and click **Export from db to pbf**.
To convert the data into the OSRM format for routing (OSRM), select **Input OSM pbf file**, and the files will be created in the **Output OSM pbf folder**.

## Use case
1. Data Update Prior to OSM Update: Once the OSM data has been downloaded and loaded onto the routing server, a route is calculated to a point where it becomes evident that no route exists.
<img src="/docs/images/inicial3.PNG" alt="Edit layer" width="400">
OSM data can be updated with the OSM Routing Editor and reloaded into OSRM, allowing the route to be calculated using the newly added segment:
<img src="/docs/images/final3.PNG" alt="Edit layer" width="400">

2. Temporary changes that will not be updated in original OSM Data: Access to a segment can be temporarily denied, or the direction of the segment can be changed. The OSM data is edited, loaded, and served from OSRM. These temporary changes will now be used on routing calculation.


## Settings
In Settings, the following parameters are entered:
+ Connection parameters for the PostgreSQL database where OSM data is stored.
+ Directory for the Osmosis utility.
+ Docker image corresponding to the OSRM routing server.
+ Input osm or pbf file.
+ Output pbf folder.
<img src="/docs/images/Settings.PNG" alt="Settings" width="400"/>
