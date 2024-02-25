import logging
import boto3
from botocore.exceptions import ClientError
import os
import json
import tempfile
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar",
          "https://www.googleapis.com/auth/calendar.readonly",
          "https://www.googleapis.com/auth/calendar.events"]

S3_BUCKET = 'love-coupon-bucket'
REGION = 'us-west-2'
SECRET_NAME = "love-coupon-google-auth-secrets"

def get_secret():

    secret_name = SECRET_NAME
    region_name = REGION

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
      
    secrets = get_secret_value_response['SecretString']
    secrets_json = json.loads(secrets)
    token = secrets_json['token']
    refresh_token = secrets_json['refresh_token']
    client_id = secrets_json['client_id']
    client_secret = secrets_json['client_secret']
    return token, refresh_token, client_id, client_secret


def _get_google_api_credentials():
  token, refresh_token, client_id, client_secret = get_secret()

  creds_json = {
    "token": token,
    "refresh_token": refresh_token,
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": client_id,
    "client_secret": client_secret,
    "scopes": [
      "https://www.googleapis.com/auth/calendar",
      "https://www.googleapis.com/auth/calendar.readonly",
      "https://www.googleapis.com/auth/calendar.events"
    ],
    "universe_domain": "googleapis.com",
    "expiry": "2024-02-13T05:00:53.478484Z"
  }
  
  with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
      # Dump the JSON object to the temporary file
      json.dump(creds_json, temp_file, indent=2)

      # Get the path of the temporary file
      temp_file_path = temp_file.name
  
  if os.path.exists(temp_file_path):
    creds = Credentials.from_authorized_user_file(temp_file_path, SCOPES)
  return creds
  

def create_event(title, description, start_date, start_time, end_date, end_time):
  creds = _get_google_api_credentials()

  try:
    service = build("calendar", "v3", credentials=creds)

    event = {
      'summary': f'{title}',
      'description': f'{description}',
      'start': {
        'dateTime': f'{start_date}T{start_time}',
        'timeZone': 'America/Denver',
      },
      'end': {
        'dateTime': f'{end_date}T{end_time}',
        'timeZone': 'America/Denver',
      },
      'attendees': [
        {
          'email': 'remolloy101@gmail.com'
        },
        {
          'email': 'remolloy101aws@gmail.com' 
        },
        {
          'email' : 'benbrewerbowman@gmail.com'
        }
      ],
      'sendNotifications': True,
      'sendUpdates': 'all'
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    return 'Event created: %s' % (event.get('htmlLink'))
    
  except HttpError as error:
    return f"An error occurred: {error}"
    
def _get_upcoming_google_events():
  creds = _get_google_api_credentials()
  
  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))

  except HttpError as error:
    print(f"An error occurred: {error}")
    
  return events


def lambda_handler(event, context):
    # Extract the selected_date from the event payload
    start_date = event.get('selected_start_date', None)
    start_time = event.get('selected_start_time', None)
    end_date = event.get('selected_end_date', None)
    end_time = event.get('selected_end_time', None)
    title = event.get('title', None)
    description = event.get('description', None)
    
    file_content = f'Event,Date,Time\nStart,{start_date},{start_time}\nEnd,{end_date},{end_time}'
    # Temporary file path to store the text file
    temp_file_path = f"/tmp/scheduled_event.txt"
    
    # Write the content to the temporary file
    with open(temp_file_path, 'w') as file:
        file.write(file_content)
    s3 = boto3.client('s3')
    s3.upload_file(temp_file_path, S3_BUCKET, f"{title}/scheduled_event.txt")

    # Clean up the temporary file
    os.remove(temp_file_path)
        
    # Log the selected date
    logger.info(f"Selected Date: {start_date}")

    # Create the Google Calendar event
    msg = create_event(title, description, start_date, start_time, end_date, end_time)

    # Return a response (optional)
    response = {'statusCode': 200, 'body': msg}
    logger.info(f"Response: {response}")
    return response
