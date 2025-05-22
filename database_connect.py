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