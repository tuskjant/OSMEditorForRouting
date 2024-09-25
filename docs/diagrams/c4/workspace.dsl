/*
C4 Diagrams: System Context, Container, and Component. 
*/
workspace "GIS Integral de Transport" {

	model {
		group "GIS Integral de transport" {
			routeplanner = person "Route Planner" "User that wants to calculate car routes between points" "routeplanner"
			networkmaintenance = person "Network maintenance operator" "User that edits the road network" "networkmaintenance"
		
			viewer = softwareSystem "GIS Integral de Transport Viewer" "Allows users to find the best route by car between 2 or more points" "viewer"{
				APIICGC = container "API Geocoder ICGC" "Provides forward and reverse geocoding services" "External" "External"
				OSMData = container "OSM Tile server" "OpenStreetMap tile map server. Provides map tiles" "External" "External"
				viewercontainer = container "GIS Integral de Transport Viewer" "Provides routing functionality and map display" "Typescript, Leaflet" {
					routingservice = component "Routing Service" "Gets routing data using the OSRM API" "Typescript"
					geocodingservice = component "Geocoding Service" "Gets forward or reverse geocoding data using the ICGC API" "Typescript"
					geocodercomponent = component "Geocoder Component" "Converts the user input into and address and coordinates" "Typescript"
					leafletroutecontroller = component "Leaflet route controller" "Responsible for communicating components with the Leaflet map" "Typescript/Leaflet"
					routepanel = component "Route Panel" "Handles route input, route and marker management, interacting with the Leaflet Route Controller" "Typesctipt"
					leafletmap = component "Leaflet Map" "Leaflet map, displays background maps, route and markers"	"Typescript/Leaflet"			
				}
			}
			
			editor = softwareSystem "GIS Integral de Transport Editor" "Allows editors to modify and prepare road network data. Serves routing data." "editor" {
				database = container "Database" "Stores OpenStreetMap data (ways, nodes and relations)." "PostgreSQL - PostGIS" "Database"
				osmosis = container "Osmosis" "Processes OSM data, reading/writing databases and files." "External" "External"
				osrm = container "Open Source Routing Machine OSRM" "Routing engine server for shortest paths in road networks." "External" "External"
				group "QGIS Software System"{
					qgiscore = container "QGIS core" "Geographic Information System Software that allows view and edit vector layers" "External" "External"
					osrmeditor = container "OSRM editor plugin" "A plugin that processes, converts, and modifies OSM data for use with OSRM" "Python, pyqgis" {

					}
				}
			}
		}

		#relationships between people and software systems
		routeplanner -> viewer "Uses"
		viewer -> editor "Gets routing data"
		networkmaintenance -> editor "Edits 
		
		#relationships to/from containers
		routeplanner -> viewercontainer "Calculates routes using"
		viewercontainer -> APIICGC "Makes API calls. Gets forward and reverse geocoding"
		viewercontainer -> OSMData "Use Tile Map Service. Gets map tiles"
		viewercontainer -> osrm "Makes API calls. Gets route data"
		
		networkmaintenance -> osrmeditor "Modifies route network using"
		osrmeditor -> qgiscore "Extends QGIS functionality"
		osrmeditor -> database "Insert and update OSM data"
		osmosis -> database "Reads from and writes OSM data to"
		osrmeditor -> osmosis "Makes calls to prepare OSRM data"
		osrmeditor -> osrm "Makes calls to convert OSM data"
		
		
		# relationships to/from components
		routepanel -> routingservice "Uses"
		routingservice -> osrm "Makes API calls to" "JSON/HTTPS"
		routepanel -> geocodingservice "Uses"
		geocodingservice -> APIICGC "Makes API calls to" "JSON/HTTPS"
		routepanel -> leafletroutecontroller "Uses"
		geocodercomponent -> geocodingservice "Uses"
		geocodercomponent -> leafletroutecontroller "Uses"
		leafletroutecontroller -> leafletmap "Uses"
		leafletmap -> OSMData "Makes API calls" "PNG/HTTPS"
	}
	
	views {
		systemlandscape "SystemLandscape" {
			include *
			autoLayout
		}
		
		container viewer "ContainersViewer" {
		    include *
            animation {
                APIICGC
                OSMData
                viewercontainer
            }
            autoLayout
            description "The container diagram for GIS Integral de Transport viewer."
        }
		
		container editor "ContainersEditor" {
			include *
			animation {
				qgiscore
				osrmeditor
				database
				osmosis
				osrm
			}
			autoLayout
            description "The container diagram for GIS Integral de Transport editor."
		}

		component viewercontainer "ViewerComponents"{
			include *
			animation {
				routepanel
				routingservice
				geocodingservice
				geocodercomponent
				leafletroutecontroller
				leafletmap
			}
			autolayout
			description "Componets diagram for GIS Integral de Transport Viewer container"
		}
		
		
		styles {
			element "Person" {
                color #ffffff
                fontSize 22
                shape Person
            }
            element "routeplanner" {
                background #08427b
            }
            element "networkmaintenance" {
                background #08427b
            }
			element "Software System" {
                background #1168bd
                color #ffffff
            }
			element "Container" {
                background #438dd5
                color #ffffff
            }
			element "External" {
                background #999999
                color #ffffff
            }
			element "Database" {
                shape Cylinder
            }
			element "Component" {
                background #85bbf0
                color #000000
            }
		}
	}
	
}