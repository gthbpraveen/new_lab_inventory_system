# google_calendar.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

# 🔐 Path to your service account JSON key (download from Google Developer Console)
SERVICE_ACCOUNT_FILE = 'credentials.json'

# 📅 Replace this with your Google Calendar ID (found in calendar settings)
CALENDAR_ID = 'c_4eb3878e5aa632ed423aa849e18abe7ddda57e21bf79bd239301afd9a83af2cc@group.calendar.google.com'  # or 'your_calendar_id@group.calendar.google.com'

# Required scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']


def create_event(summary, description, start, end, timezone='Asia/Kolkata'):
    """
    Creates an event on the configured Google Calendar.

    Parameters:
    - summary (str): Title of the event
    - description (str): Additional notes
    - start (str): ISO format start time (e.g. '2025-07-30T10:00:00')
    - end (str): ISO format end time (e.g. '2025-07-30T12:00:00')
    - timezone (str): Time zone of the event
    """

    # Load credentials
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Build Google Calendar service
    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start,
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end,
            'timeZone': timezone,
        },
    }

    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    print(f"📅 Event created: {created_event.get('htmlLink')}")
    return created_event
