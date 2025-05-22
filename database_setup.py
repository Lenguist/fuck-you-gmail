import boto3
from botocore.exceptions import ClientError
import json
import mysql.connector


def get_secret():
    secret_name = "rds!cluster-3ccc57c2-2cb2-4732-8128-430ea57eb383"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        # Retrieve the secret from AWS Secrets Manager
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise e

    # Extract and parse the secret
    secret = json.loads(get_secret_value_response['SecretString'])

    # Extract only the username and password
    username = secret.get('username')
    password = secret.get('password')

    if not username or not password:
        raise ValueError("The secret must contain 'username' and 'password' fields.")

    return username, password


def connect_to_mysql(username, password, dbname=None):
    # Manually specify the RDS host endpoint
    host = "email-summarizer-dev.cluster-cfoais5hmxcr.us-east-1.rds.amazonaws.com"
    port = 3306  # Default MySQL port

    try:
        # Establish a connection to the MySQL server
        connection = mysql.connector.connect(
            user=username,
            password=password,
            host=host,
            port=port,
            database=dbname  # `dbname` is None if not specified
        )
        if dbname:
            print(f"Successfully connected to the database '{dbname}'.")
        else:
            print("Successfully connected to the MySQL server.")
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        raise err


def create_database_if_not_exists(connection, db_name):
    try:
        # Create a cursor object to interact with MySQL
        cursor = connection.cursor()

        # List existing databases
        cursor.execute("SHOW DATABASES;")
        databases = [db[0] for db in cursor.fetchall()]

        # Check if the database already exists
        if db_name in databases:
            print(f"Database '{db_name}' already exists.")
        else:
            # Create the database if it does not exist
            cursor.execute(f"CREATE DATABASE {db_name};")
            print(f"Database '{db_name}' created successfully.")

        # Clean up the cursor
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
        raise


def create_tables(connection):
    # SQL statements for creating the tables
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        oauth_token TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_preferences_table = """
    CREATE TABLE IF NOT EXISTS preferences (
        preference_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        summary_time VARCHAR(10) NOT NULL,
        active BOOLEAN DEFAULT TRUE,
        prompt_url VARCHAR(255),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """

    try:
        # Create a cursor and execute the table creation queries
        cursor = connection.cursor()
        cursor.execute(create_users_table)
        print("Created or verified 'users' table.")
        cursor.execute(create_preferences_table)
        print("Created or verified 'preferences' table.")
        connection.commit()
    except mysql.connector.Error as err:
        print(f"Error creating tables: {err}")
        connection.rollback()
    finally:
        cursor.close()


if __name__ == "__main__":
    try:
        # Step 1: Retrieve the credentials from Secrets Manager
        username, password = get_secret()

        # Step 2: Connect to the MySQL server without specifying a database
        connection = connect_to_mysql(username, password)

        # Step 3: Create the database if it does not exist
        create_database_if_not_exists(connection, "email_summarizer")

        # Step 4: Close the initial connection
        connection.close()

        # Step 5: Reconnect to the MySQL server with the specified database
        connection_with_db = connect_to_mysql(username, password, "email_summarizer")

        # Step 6: Create the required tables in the database
        create_tables(connection_with_db)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Step 7: Close the connection if it was established
        if 'connection_with_db' in locals() and connection_with_db.is_connected():
            connection_with_db.close()
            print("Database connection closed.")
