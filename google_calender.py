import datetime
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load the service account key JSON file
SERVICE_ACCOUNT_FILE = 'path/to/service_account.json'

# Calendar IDs for 109 and 209
CALENDAR_ID_MAP = {
    "CS-109": "your_calendar_id_109@group.calendar.google.com",
    "CS-209": "your_calendar_id_209@group.calendar.google.com"
}

SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_event(lab, summary, description, start_time, end_time):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=credentials)

    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
    }

    calendar_id = CALENDAR_ID_MAP.get(lab)
    if calendar_id:
        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        return event_result.get('htmlLink')
    return None
