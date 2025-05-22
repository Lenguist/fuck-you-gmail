import mysql.connector
from mysql.connector import Error
import boto3
from botocore.exceptions import ClientError
import json

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

def connect_to_mysql(username, password, dbname='email_summarizer'):
    """Establish a connection to the MySQL database."""
    host = "email-summarizer-dev.cluster-cfoais5hmxcr.us-east-1.rds.amazonaws.com"
    port = 3306

    connection = mysql.connector.connect(
        user=username,
        password=password,
        host=host,
        port=port,
        database=dbname
    )
    return connection

def check_users():
    """Fetch and print the last 5 sign-ups and their preferences."""
    connection = None
    cursor = None
    try:
        username, password = get_secret()  # Get your username and password
        connection = connect_to_mysql(username, password)
        
        cursor = connection.cursor()

        # Query to fetch the last 5 sign-ups along with their preferences
        query = """
        SELECT u.user_id, u.email, u.oauth_token, u.active, u.pause_end, u.created_at, u.updated_at,
               p.summary_time, p.prompt, p.prompt_last_updated, p.updated_at AS preference_updated_at
        FROM users u
        LEFT JOIN preferences p ON u.user_id = p.user_id
        ORDER BY u.created_at DESC
        LIMIT 5;
        """
        cursor.execute(query)
        results = cursor.fetchall()

        # Print user details
        if results:
            print("Last 5 sign-ups and their preferences:")
            for row in results:
                user_id, email, oauth_token, active, pause_end, created_at, user_updated_at, summary_time, prompt, prompt_last_updated, preference_updated_at = row
                print(f"User ID: {user_id}")
                print(f"Email: {email}")
                print(f"OAuth Token: {oauth_token}")
                print(f"Active: {active}")
                print(f"Pause End: {pause_end}")
                print(f"User Created At: {created_at}")
                print(f"User Updated At: {user_updated_at}")
                print(f"Summary Time: {summary_time}")
                print(f"Prompt: {prompt}")
                print(f"Prompt Last Updated: {prompt_last_updated}")
                print(f"Preference Updated At: {preference_updated_at}")
                print("-" * 50)
        else:
            print("No users found in the database.")

    except Error as err:
        print(f"Error: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

if __name__ == '__main__':
    check_users()
