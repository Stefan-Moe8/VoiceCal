# Connect to Google Calendar or Outlook. Implement functions to check existing events, check availability, create events, and handle API errors.
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Loads variables from .env into the environment
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"] # Premisiion level for crediential requests
TZ = ZoneInfo(os.getenv("CALENDAR_TZ", "UTC"))

_service = None

# Custom exception handler
class CalendarError(Exception):
    """Raised when Google Calendar is misconfigured or a request fails."""

# Retrieve calendar id
def get_calendar_id():
    calendar_id = os.getenv("CALENDAR_ID")
    if not calendar_id:
        raise CalendarError("CALENDAR_ID not found. Check your .env file.")
    return calendar_id

# Retrieve the key and id
def get_service():
    global _service
    if _service is None:
        key_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        if not key_file:
            raise CalendarError("GOOGLE_SERVICE_ACCOUNT_FILE not found. Check your .env file.")
        creds = service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)
        _service = build("calendar", "v3", credentials=creds)
    return _service

# Shared method for fetching events for a month, week, day, ...
def _list_events(start, end):
    events = []
    token = None
    try:
        while True:
            resp = get_service().events().list(
                calendarId=get_calendar_id(),
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True, # Expands recurring events into individual instances
                orderBy="startTime",
                pageToken=token,
            ).execute()
            events += resp.get("items", [])
            token = resp.get("nextPageToken")
            if not token:
                return events
    except HttpError as e:
        raise CalendarError(f"Could not fetch events ({e.resp.status}): ({e.reason})") from e


# Define midnight for a day
def _midnight(d):
    return datetime(d.year, d.month, d.day, tzinfo=TZ)

# Fetch all events within a months boundaries (will be used for web application to show users monthly schedule)
def fetch_month(year=None, month=None):
    today = datetime.now(TZ).date()
    year, month = year or today.year, month or today.month
    # Start of Month
    start = datetime(year, month, 1, tzinfo=TZ)
    # End of Month
    end = datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=TZ)  # first of next month
    return _list_events(start, end)

# Fetch all events within a week boundaries
def fetch_week(day=None):
    day = day or datetime.now(TZ).date()
    # Start of Week
    sunday = day - timedelta(days=(day.weekday() + 1) % 7)
    start = _midnight(sunday)
    return _list_events(start, start + timedelta(days=7))


# Fetch all events within a day boundaries
def fetch_day(day=None):
    day = day or datetime.now(TZ).date()
    # Start of day
    start = _midnight(day)
    return _list_events(start, start + timedelta(days=1))

# Helper function, checks if the time slot is free
def is_free(start, end):
    calendar_id = get_calendar_id()
    body = {
        "timeMin": start.isoformat(), 
        "timeMax": end.isoformat(), 
        "items": [{"id": calendar_id}]}
    try:
        resp = get_service().freebusy().query(body=body).execute()
    except HttpError as e:
        raise CalendarError(f"Could not check availability ({e.resp.status}): {e.reason}") from e
    
    calendar = resp["calendars"][calendar_id]
    if calendar.get("errors"):
        raise CalendarError(f"Could not read calendar availability: {calendar['errors']}")
    return not calendar["busy"]


# Add an event to the calendar
def add_event(summary, start, end, description=None, allow_conflict=False):
    # Check that event contains the minimum required information
    if end <= start:
        raise ValueError("End must be after start.")
    if not allow_conflict and not is_free(start, end):
        raise CalendarError("That time overlaps an existing event.")
    body = {
        "summary": summary,
        "start": {"dateTime": start.isoformat(), "timeZone": str(TZ)},
        "end": {"dateTime": end.isoformat(), "timeZone": str(TZ)},
    }
    if description:
        body["description"] = description
    try:
        return get_service().events().insert(calendarId=get_calendar_id(), body=body).execute()
    except HttpError as e:
        raise CalendarError(f"Could not create event ({e.resp.status}): {e.reason}") from e