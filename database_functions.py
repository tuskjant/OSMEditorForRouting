import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_READ_COMMITTED


def connect_to_database(database_params):
    """
    Set database connection to postgresql
    :database_params: dictionay with database parameters {'dbname':*, 'user':*, 'password':*, 'host':*, 'port':*, 'schema':*}
    :return: Database connection and cursor.
    *default schema is public
    """
    del database_params["schema"]# schema parameter is not used in connection-> del schema parameter
    
    try:
        conn = psycopg2.connect(**database_params)
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(e)
        return None, None

def close_connection(connection, cursor):
    try:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        return True
    except:
        return False

def change_line_direction(connection, cursor, way_id):
    """Change segment direction:
    1- Reverse geometry of linestring
    2- Reverse nodes order from ways table - nodes field
    3- Reverse way nodes sequence from way_nodes table where way_id is given id
    """
    ways_table = "ways"
    way_node_table = "way_nodes"

    
    try:
        ### 1- Reverse geometry of linestring
        query_linestring = f"UPDATE {ways_table} SET linestring = ST_Reverse(linestring) WHERE id = %s"
        cursor.execute(query_linestring,( way_id,))
        
        ### 2- Reverse nodes order from ways table - nodes field
        # Get nodes
        query_nodes = f"SELECT nodes FROM {ways_table} WHERE id = %s "
        cursor.execute(query_nodes, (way_id,))
        result = cursor.fetchone()
        if result is None:
            return False
        current_array = result[0]

        # Reverse nodes list
        reversed_array = current_array[::-1]

        # Update nodes field
        query_update_nodes = f"UPDATE {ways_table} SET nodes = %s WHERE id = %s"
        cursor.execute(query_update_nodes, (reversed_array, way_id))

        ### 3- Reverse way nodes sequence from way_nodes table where way_id is given id
        # Get max sequence id for way_id
        query_way_nodes = f"SELECT node_id, sequence_id FROM {way_node_table} WHERE way_id=%s"
        cursor.execute(query_way_nodes, (way_id,))
        rows = cursor.fetchall()
        if not rows:
            return False
        max_sequence_id = max(row[1] for row in rows)

        # Reverse sequence id for rows
        reversed_rows = [(row[0], max_sequence_id - row[1]) for row in rows]

        # Reverse sequence id: delete previous values and insert new values (avoid restriction)
        delete_query = f"DELETE FROM {way_node_table} WHERE way_id = %s"
        cursor.execute(delete_query, (way_id,))

        insert_query = f"INSERT INTO {way_node_table} (way_id, node_id, sequence_id) VALUES (%s, %s, %s)"
        for row in reversed_rows:
            cursor.execute(insert_query, (way_id, row[0], row[1]))
        
        connection.commit()
    
    except Exception as e:
        print(e)
        connection.rollback()
        return False
    
    return True

def create_db(conn_params):
    # Connect using postgres database and create new database using parameters values
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=conn_params["user"],
            password=conn_params["password"],
            host=conn_params["host"],
        )
        # deactivate autocommit mode
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        query = f"CREATE DATABASE {conn_params["dbname"]};"
        cursor.execute(query)
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_extensions(connection, cursor):
    # Create postgis i hstore extensions
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS hstore;")
        connection.commit()
        return True
    except Exception as e:
        print(e)
        connection.rollback()
        return False

def execute_sql_file(connection, cursor, sql_file_path):
    with open(sql_file_path, 'r') as sql_file:
        sql_commands = sql_file.read()

    try:
        cursor.execute(sql_commands)
        connection.commit()  
    except Exception as e:
        print(e)
        connection.rollback()  
        return False
    return True

def get_max_node_id(cursor):
    nodes_table = "nodes"
    # Get nodes
    try:
        query_nodes = f"SELECT max(id) as max_id FROM {nodes_table}"
        cursor.execute(query_nodes)
        result = cursor.fetchone()
        if result is None:
            return False
        max_id = result[0]
    except Exception as e:
        print(e)
        return False
    return max_id

def get_max_way_id(cursor):
    ways_table ="ways"
    try:
        query_nodes = f"SELECT max(id) as max_id FROM {ways_table}"
        cursor.execute(query_nodes)
        result = cursor.fetchone()
        if result is None:
            return False
        max_id = result[0]
    except Exception as e:
        print(e)
        return False
    return max_id

def get_osrm_user_from_db(cursor):
    users_table = "users"
    try:
        query_user = f"SELECT id, name FROM {users_table} WHERE id=99999999"
        cursor.execute(query_user)
        result = cursor.fetchone()
        if result is None:
            return "nouser"
        else:
            return "user"
    except Exception as e:
        print(e)
        return False 

def get_connected_node(cursor, point_x_y):
    nodes_table = "nodes"
    try:
        query_user = f"SELECT id FROM {nodes_table} ORDER BY geom <-> ST_SetSRID(ST_MakePoint({point_x_y[0]},{point_x_y[1]}), 4326) LIMIT 1"
        cursor.execute(query_user)
        result = cursor.fetchone()
        if result is None:
            return False
        node_id = result[0]
    except Exception as e:
        print(e)
        return False 
    return node_id

def insert_data_into_table(conn, cursor, table_name, data_list):
    for data in data_list:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        values = list(data.values())

        cursor.execute(sql, values)
    
def add_segment(connection, cursor, nodes_data, way_nodes_data, ways_data, user_data):
    # insert user_data only when there's not user in the database
    try:
        insert_data_into_table(connection, cursor, "nodes", nodes_data)
        insert_data_into_table(connection, cursor, "way_nodes", way_nodes_data)
        insert_data_into_table(connection, cursor, "ways", ways_data)
        if user_data:
            insert_data_into_table(connection, cursor, "users", user_data)
        connection.commit()
        return True

    except Exception as e:
        print(e)
        if connection:
            connection.rollback()
        return False
