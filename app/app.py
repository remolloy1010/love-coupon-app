import streamlit as st
from streamlit_card import card
import os
import boto3
import matplotlib.image as mpimg
import tempfile
from botocore.exceptions import ClientError, NoCredentialsError
import datetime
import json
import logging
import pandas as pd
from io import StringIO
import numpy as np

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

st.set_page_config(layout="wide")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_BUCKET_NAME = "love-coupon-bucket"
AWS_REGION = "us-west-2"
LAMBDA_FUNCTION_NAME = 'love_coupon_lambda'
AWS_SECRETS = 'love-coupon-google-auth-secrets'

s3 = boto3.client("s3", region_name=AWS_REGION)

STYLES = {
  "card": {
      "width": "100%", 
      "height": "100px", 
      "background-color" : "#01F8C5",
      "padding" : "0px"
  },
  "title": {
      "font-family": "serif",
      "color" : "020035"
  },
  "filter": {
      "background-color": "rgba(0, 0, 0, 0)" 
  }
}

with open('coupon_ideas.json', 'r') as json_file:
    # Load the JSON data into a Python object
    CATEGORIES = json.load(json_file)

def get_secret():

    secret_name = AWS_SECRETS
    region_name = AWS_REGION

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

    df = pd.DataFrame({'start_dttm' : [],
                       'summary' : []})
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      df_event = pd.DataFrame({
        'start_dttm' : [start],
        'summary' : [event["summary"]]
      })
      df = pd.concat([df, df_event])
  except HttpError as error:
    print(f"An error occurred: {error}")
    
  return df

def list_event_schedule(title):
  creds = _get_google_api_credentials()
  service = build("calendar", "v3", credentials=creds)
 
  # Call the Calendar API
  now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
  events_result = (
      service.events()
      .list(
          calendarId="primary",
          timeMin=now,
          timeMax=(datetime.datetime.utcnow() + datetime.timedelta(days=20)).isoformat() + "Z",
          singleEvents=True,
          orderBy="startTime",
      )
      .execute()
  )
  events = events_result.get("items", [])
  if not events:
    print("No upcoming events found.")
    return

  # Prints the start and name of the next 10 events
  for event in events:
    start = event["start"].get("dateTime", event["start"].get("date"))
    if event['summary'] == title:
      return start
        
def invoke_lambda_function(title, description, selected_start_date, selected_start_time,
                           selected_end_date, selected_end_time):
    client = boto3.client('lambda', region_name=AWS_REGION)

    try:
        payload = {
            'title' : title,
            'description' : description,
            'selected_start_date': selected_start_date.isoformat() if selected_start_date else None,
            'selected_start_time': selected_start_time.isoformat() if selected_start_time else None,
            'selected_end_date': selected_end_date.isoformat() if selected_end_date else None,
            'selected_end_time': selected_end_time.isoformat() if selected_end_time else None
        }
        payload_data = json.dumps(payload)

        response = client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='Event',  # Set to 'Event' for asynchronous invocation
            LogType='Tail',  # Optionally, set to 'Tail' to include logs in the response
            Payload=payload_data
        )
        return response
    except Exception as e:
        print(f"Error invoking AWS Lambda function: {e}")
        return e

def round_to_nearest_hour():
    # Round to the next nearest hour
    current_time = datetime.datetime.combine(datetime.datetime.today(), datetime.datetime.now().time())
    rounded_time = current_time.replace(second=0, microsecond=0, minute=0) + datetime.timedelta(hours=1)
    return rounded_time

def show_balloons():
  st.balloons()
  
def _check_if_image_in_s3(title):
  # Create an S3 client
  # s3_client = boto3.client(
  #     's3',
  #     aws_access_key_id=AWS_ACCESS_KEY_ID,
  #     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
  #     region_name=AWS_REGION
  # )
  s3_client = boto3.client(
      's3'
  )
  
  objects = s3_client.list_objects_v2(Bucket=AWS_BUCKET_NAME)

  if 'Contents' in objects.keys():
    obj_list = [obj['Key'] for obj in objects['Contents']]
    name_list = [os.path.splitext(os.path.basename(obj['Key']))[0] for obj in objects['Contents']]
    image_name = f'{title}'.lower().replace(' ', '_')
  else:
    return False
  
  try:
    index = name_list.index(image_name)
    filename = obj_list[index]
    return filename
  except:
      return False
  
def upload_to_s3(file, title):
    if file is not None:
      extension = os.path.splitext(os.path.basename(file.name))[-1]
      object_name = title.lower().replace(' ', '_') + extension

      s3 = boto3.client('s3')

      try:
          s3.upload_fileobj(file, AWS_BUCKET_NAME, f"{title}/{object_name}")
          st.success("File uploaded successfully.")
      except NoCredentialsError:
          st.error("Credentials not available.")
      except Exception as e:
          st.error(f"Error: {e}")
          
def redeemed_button_text(title):
  s3_client = boto3.client('s3')
  
  objects = s3_client.list_objects_v2(Bucket=AWS_BUCKET_NAME)  

  if 'Contents' in objects.keys():
    obj_list = [obj['Key'] for obj in objects['Contents']]
  else:
    obj_list = []

  if (len(obj_list) > 0) & (f"{title}/scheduled_event.txt" in obj_list):
    # Event has already been scheduled
    label = 'Redeemed!'
  else:
    label = 'Redeem Coupon'
  return label
  
def disabled_button(title):
  s3_client = boto3.client('s3')
  
  objects = s3_client.list_objects_v2(Bucket=AWS_BUCKET_NAME)

  if 'Contents' in objects.keys():
    obj_list = [obj['Key'] for obj in objects['Contents']]
  else:
    obj_list = []

  if (len(obj_list) > 0) & (f"{title}/scheduled_event.txt" in obj_list):
    # Event has already been scheduled
    disabled = True
  else:
    disabled = False
  return disabled
  
def get_scheduled_event_from_s3(title):
  s3_client = boto3.client('s3')
  
  objects = s3_client.list_objects_v2(Bucket=AWS_BUCKET_NAME)

  if 'Contents' in objects.keys():
    obj_list = [obj['Key'] for obj in objects['Contents']]
  else:
    obj_list = []

  event_file = f"{title}/scheduled_event.txt"

  if event_file in obj_list:
    # Use get_object to retrieve the file
    response = s3.get_object(Bucket=AWS_BUCKET_NAME, Key=event_file)

    # Read the content of the file
    file_content = response['Body'].read().decode('utf-8')

    # Convert the DataFrame to a string
    df = pd.read_csv(StringIO(file_content))
    df['test'] = df['Date'].astype(str) + ' ' + df['Time'].astype(str)
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    start_dttm = df[df['Event'] == 'Start']['Datetime'].values[0]
    end_dttm = df[df['Event'] == 'End']['Datetime'].values[0]
    return start_dttm
  
  else:
    return None

def love_coupon(title, description):
  with st.container(border=True):
    st.markdown("""<style> .title {
      text-align: center; font-size: 30px; font-weight: bold; color: #01F8C5;} 
      .description {
      text-align: center; font-size: 18px; font-style: italic;} 
      </style> """, unsafe_allow_html=True)
    st.markdown(f'<p class="title">{title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="description">{description}</p>', unsafe_allow_html=True)
  
    st.markdown(
      """
      <style>
      [data-testid="stButton"] {
          display: flex;
          justify-content: center;
      }
      [data-testid="baseButton-primary"] {
          font-size: 20px;
          background-color: #01F8C5;
          color: #020035;
          width: 50%;
          display: flex;
          justify-content: center;
          height: 25px;
      }
      [data-testid="stFileUploadDropzone"] {
        background-color: grey;
      }
      [class="st-ag st-ch"] {
        color: #020035;
      }
      [data-testid="stDateInput-Input"] {
        color: #020035;
      }
      [data-testid="stTimeInput-timeDisplay"] {
        color: #020035;
      }
      [data-baseweb="icon"] {
        color: #020035;
      }
      [data-testid="baseButton-secondaryFormSubmit"] {
        background-color: grey;
      }
      </style>
      """,
      unsafe_allow_html=True,
    )
    
    image_name = _check_if_image_in_s3(title)
    rounded_time = round_to_nearest_hour()
    redeem = st.button(label=redeemed_button_text(title), key=f"redeem_button_{title}", type="secondary", 
                       use_container_width=True, disabled=disabled_button(title))
    if redeem:
      with st.form('redeem_form'):
        st.balloons()
        col1, col2 = st.columns(2)
        with col1:
          selected_start_date = st.date_input('Schedule Event Start Date:', min_value=datetime.date.today() - datetime.timedelta(days = 1), 
                                        key='selected_start_date')
        with col2:
          selected_start_time = st.time_input('Schedule Event Start Time:', value=rounded_time, 
                                        step=datetime.timedelta(minutes = 30), label_visibility='hidden', 
                                        key='selected_start_time')
        with col1:
          selected_end_date = st.date_input('Schedule Event End Date:', min_value=datetime.date.today() - datetime.timedelta(days = 1), 
                                        key='selected_end_date')
        with col2:
          selected_end_time = st.time_input('Schedule Event End Time:', value=rounded_time + datetime.timedelta(hours=1), 
                                        step=datetime.timedelta(minutes = 30), label_visibility='hidden', 
                                        key='selected_end_time')
        st.form_submit_button('Schedule', on_click=lambda: invoke_lambda_function(title, description, 
                                                                                  st.session_state.get('selected_start_date'), 
                                                                                  st.session_state.get('selected_start_time'), 
                                                                                  st.session_state.get('selected_end_date'), 
                                                                                  st.session_state.get('selected_end_time')))
    if disabled_button(title):
      start_dttm = get_scheduled_event_from_s3(title)
      list_event_schedule(title)
      
      if start_dttm is None:
        st.warning("Scheduled event is missing from S3 Bucket. May be ")
      
      elif start_dttm <= np.datetime64(datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)):
        scheduled_date = pd.to_datetime(str(start_dttm)).strftime('%B %d, %Y')
        st.success(f"Event Passed! Hope you enjoyed the date on {scheduled_date}!", icon="💖")
      
      else:
        scheduled_date = pd.to_datetime(str(start_dttm)).strftime('%B %d, %Y')
        scheduled_time = pd.to_datetime(str(start_dttm)).strftime('%I:%M %p')
        st.success(f"Event Scheduled for {scheduled_date} at {scheduled_time}. Check Gmail Calendar.", icon="🔥")
        
    st.markdown(
        """
        <style>
        [class="st-emotion-cache-6i8naw e1f1d6gn0"] {
        }
        [data-testid="stImage"] {
          padding: 40px;
          width: 100%;
          margin-top: 20px;
          margin-bottom: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if image_name is False:
      uploaded = st.file_uploader('Upload an Image of Event!', key=f"upload_button_{title}", 
                       type=['png', 'jpg', 'jpeg'] #, on_change=upload_to_s3(title)
                       )
      upload_to_s3(uploaded, title)
    else:
      # s3 = boto3.resource(
      #     's3',
      #     aws_access_key_id=AWS_ACCESS_KEY_ID,
      #     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
      #     region_name=AWS_REGION
      #   )
      s3 = boto3.resource('s3')
      
      bucket = s3.Bucket(AWS_BUCKET_NAME)
      object = bucket.Object(image_name)

      tmp = tempfile.NamedTemporaryFile()
      try:
        with open(tmp.name, 'wb') as f:
            object.download_fileobj(f)
            img=mpimg.imread(tmp.name)
        st.image(img, caption="")
      except:
        st.write('No file found')
      
  
def _get_list_of_card_titles():
  if st.session_state.get('category') is None:
    return [], []
  else:
    category = st.session_state.get('category')
    cards = CATEGORIES[category]
    return list(cards.keys()), list(cards.values())
    
st.markdown(
    """
    <style>
    [data-testid="stButton"] {
        display: flex;
        justify-content: center;
    }
    [data-testid="baseButton-secondary"] {
        font-size: 20px;
        background-color: #01F8C5;
        color: #020035;
        width: 75%;
        display: flex;
        justify-content: center;
        height: 75px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def main():
    st.title("Ben's Love Coupons :kiss:")

    # Three columns for Date Night In, Date Night Out, and Weekend Getaway
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Date Day/Night In"):
          st.session_state['category'] = "Date Day/Night In"

    with col2:
        if st.button("Date Night Out"):
            st.session_state['category'] = "Date Night Out"

    with col3:
        if st.button("Weekend Getaway"):
            st.session_state['category'] = "Weekend Getaway"
            
    with col1:
        if st.button("House Helper"):
          st.session_state['category'] = "House Helper"

    with col2:
        if st.button("Date Day Out"):
            st.session_state['category'] = "Date Day Out"

    with col3:
        if st.button("Miscellaneous"):
            st.session_state['category'] = "Miscellaneous"

    st.divider()
    coupon_list, coupon_descr = _get_list_of_card_titles()
    indices = [i % 3 for i in range(len(coupon_list))]
    
    if not None:
      cols = st.columns(3)
      for i, coupon_index in enumerate(indices):
          with cols[coupon_index]:
              love_coupon(coupon_list[i], coupon_descr[i])


if __name__ == "__main__":
    main()
  # list_event_schedule('Testing..')