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


def connect_to_mysql(username, password):
    # Manually specify the RDS host endpoint
    host = "email-summarizer-dev.cluster-cfoais5hmxcr.us-east-1.rds.amazonaws.com"
    port = 3306  # Default MySQL port

    try:
        # Establish a connection to the MySQL server
        connection = mysql.connector.connect(
            user=username,
            password=password,
            host=host,
            port=port
        )
        print(f"Successfully connected to the MySQL server.")
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        raise err


def recreate_database(connection, dbname):
    try:
        cursor = connection.cursor()
        # Drop the existing database if it exists and create a new one
        cursor.execute(f"DROP DATABASE IF EXISTS {dbname};")
        cursor.execute(f"CREATE DATABASE {dbname};")
        print(f"Recreated database '{dbname}'.")
        connection.commit()
    except mysql.connector.Error as err:
        print(f"Error recreating database: {err}")
        connection.rollback()
    finally:
        cursor.close()


def connect_to_database(username, password, dbname):
    # Connect directly to the specified database
    host = "email-summarizer-dev.cluster-cfoais5hmxcr.us-east-1.rds.amazonaws.com"
    port = 3306

    try:
        connection = mysql.connector.connect(
            user=username,
            password=password,
            host=host,
            port=port,
            database=dbname
        )
        print(f"Connected to the database '{dbname}'.")
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to database '{dbname}': {err}")
        raise err


def create_tables(connection):
    # SQL statements for creating the tables with updated schema
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        oauth_token TEXT NOT NULL,
        active BOOLEAN DEFAULT TRUE,  -- Indicates if the user is active or paused
        pause_end DATETIME DEFAULT NULL,  -- Indicates when a user's pause ends
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """

    create_preferences_table = """
    CREATE TABLE IF NOT EXISTS preferences (
        preference_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        summary_time VARCHAR(10) NOT NULL,  -- Morning, Afternoon, Evening
        prompt TEXT,  -- Store any user-specific prompt or instructions
        prompt_last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Track last updated time for 'prompt'
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
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

        # Step 2: Connect to the MySQL server
        connection = connect_to_mysql(username, password)

        # Step 3: Recreate the database (drop if it exists and create anew)
        recreate_database(connection, "email_summarizer")

        # Step 4: Connect directly to the recreated database
        connection_with_db = connect_to_database(username, password, "email_summarizer")

        # Step 5: Create the required tables in the database
        create_tables(connection_with_db)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Step 6: Close the connection if it was established
        if 'connection_with_db' in locals() and connection_with_db.is_connected():
            connection_with_db.close()
            print("Database connection closed.")
