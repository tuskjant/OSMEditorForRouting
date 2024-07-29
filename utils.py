from qgis.core import QgsDataSourceUri, QgsVectorLayer



def db_connection(host, port, user, password, database, schema):
    uri = QgsDataSourceUri()
    uri.setConnection(host, port, database, user, password)
    uri.setDataSource(schema, "ways", "linestring")
    try:
        pg_layer = QgsVectorLayer(uri.uri(), "ways", "postgres")
        return pg_layer
    except:
        return
        

def add_layer(vector_layer):
    if not vector_layer.isValid():
        iface.messageBar().pushMessage("", "No es pot accedir a la base de dades.", Qgis.Warning, 10)
        return
    else:
        QgsProject.instance().addMapLayer(vector_layer)
        iface.setActiveLAyer(vector_layer)
        iface.zoomToActiveLayer()