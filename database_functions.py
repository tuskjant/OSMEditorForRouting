import psycopg2

def connect_to_database(database_params):
    """
    Set database connection to postgresql
    :database_params: dictionay with database parameters {'dbname':*, 'user':*, 'password':*, 'host':*, 'port':*}
    :return: Database connection and cursor.
    *default schema is public
    """
    try:
        conn = psycopg2.connect(**database_params)
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        return None, None


def close_connection(connection, cursor):
    try:
        cursor.close()
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

        # Updata nodes field
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
        print(f"maxsequence {max_sequence_id}")

        # Reverse sequence id for rows
        reversed_rows = [(row[0], max_sequence_id - row[1]) for row in rows]
        print(reversed_rows)

        # Reverse sequence id: delete preveious values and insert new values (avoid restriction)
        delete_query = f"DELETE FROM {way_node_table} WHERE way_id = %s"
        print(delete_query)
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



