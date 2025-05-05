import pymysql

print("Attempting to connect to MySQL...")

try:
    # Connect to the MySQL database
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='317394',
        database='medstock_db'
    )
    
    # Create a cursor
    cursor = connection.cursor()
    
    # Get some basic database info
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print("Successfully connected to MySQL!")
    print(f"Database: medstock_db")
    print(f"Tables found: {len(tables)}")
    print("Table list:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Close the connection
    connection.close()
    print("Connection closed.")
    
except Exception as e:
    print(f"Error connecting to MySQL: {e}") 