import datetime
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load the service account key JSON file
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Calendar IDs for 109 and 209
CALENDAR_ID_MAP = {

    "CS-109": "31b285e2a089b57ecbfbfc2f879c16406d7a4f3d26d0eb5703cd94a86b4805ff@group.calendar.google.com",
    "CS-209": "31b285e2a089b57ecbfbfc2f879c16406d7a4f3d26d0eb5703cd94a86b4805ff@group.calendar.google.com"
}


SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_event(lab, summary, description, start_time, end_time):
    try:
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
        if not calendar_id:
            print(f"❌ Calendar ID for lab '{lab}' not found.")
            return None

        result = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"✅ Event created: {result.get('htmlLink')}")
        return result.get('htmlLink')
    except Exception as e:
        print("❌ Google Calendar error:", e)
        return None

def get_upcoming_events(calendar_id, max_results=10):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=credentials)

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return events_result.get('items', [])
