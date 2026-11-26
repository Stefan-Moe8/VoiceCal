import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import webbrowser
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from O365 import Account

calendar = None 
"""None if no sign in has been done"""
# Functions
def sign_into_calendar():
    """:Function: Signs into the selected calendar - Returns None if no calendar is selected"""
    return None
def change_calendar_account():
    """:Function: Signs into the selected calendar - None if no calendar is selected"""
    return None
def read_calendar(requestedInfo: list = ['summary'], minDateTime : str = 'now', maxDateTime : str = None, maxEntries : int = 10, query : str = None, asJson : bool = False):
    return None
def add_event(inputDict : dict):
    return None

# Reading Calendar
def read_calendar_google(requestedInfo: list = ['summary'], minDateTime : str = 'now', maxDateTime : str = None, maxEntries : int = 10, query : str = None, asJson : bool = False):
    """Reads events from the selected calendar

        summary - Name of the event

        description - Description of the event

        location - Location of the event

        start - Time the event starts

        end - Time the event ends

        :param requestedInfo: some combination of ['summary', 'description', 'location', 'start', 'end'] to return
        :type requestedInfo: List
        :param minDateTime: 'now' is now, Earliest date to search for events, Default: None
        :type minDateTime: datetime.isoformat() String
        :param maxDateTime: Lastest date to search for events, Default: None
        :type maxDateTime: datetime.isoformat() String
        :param maxEntries: Maximum number of events to return, Default: 10
        :type maxEntries: Int
        :param query: Search for a word or prase in events, Default: None
        :type query: String
        :param asJson: Whether to return a Dict of Dicts or a Json formatted string, Default: Dicts; False
        :type asJson: Bool

        :returns: A dict keyed by google Event etag containing dict keyed by requestedInfo input
        :rtype: Json Formated String or Dict of Dicts
    """
    
    if minDateTime == 'now':
        minDateTime = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    events_result = (calendar.events().list(calendarId='primary', timeMin = minDateTime, timeMax = maxDateTime, maxResults = maxEntries, singleEvents = True, orderBy = "startTime", q=query).execute())
    events = events_result.get("items", [])
    returnEvents = {}
    for event in events:
        print(event)
        returnEvents[event['etag']] = {}
        for key in requestedInfo:
            if key in event:
                if key == 'start' or key == 'end':
                    returnEvents[event['etag']][key] =  event[key].get('dateTime') or event[key].get('date')
                else:
                    returnEvents[event['etag']][key] = event[key]
            else:
                continue
    if asJson:
        return json.dumps(returnEvents)
    return returnEvents

def read_calendar_outlook(requestedInfo: list = ['summary'], minDateTime : str = 'now', maxDateTime : str = None, maxEntries : int = 10, query : str = None, asJson : bool = False):
    """Reads events from the selected calendar

        summary - Name of the event

        description - Description of the event

        location - Location of the event

        start - Time the event starts

        end - Time the event ends

        :param requestedInfo: some combination of ['summary', 'description', 'location', 'start', 'end'] to return
        :type requestedInfo: List
        :param minDateTime: Earliest date to search for events, Default: None
        :type minDateTime: datetime.isoformat() String
        :param maxDateTime: Lastest date to search for events, Default: None
        :type maxDateTime: datetime.isoformat() String
        :param maxEntries: Maximum number of events to return, Default: 10
        :type maxEntries: Int
        :param query: Search for a word or prase in events, Default: None
        :type query: String
        :param asJson: Whether to return a Dict of Dicts or a Json formatted string, Default: Dicts; False
        :type asJson: Bool

        :returns: A dict keyed by outlook event.object_id containing dict keyed by requestedInfo input
        :rtype: Json Formated String or Dict of Dicts
        
    """

    if minDateTime == 'now':
        minDateTime = datetime.datetime.now(tz=datetime.timezone.utc)
    else:
        minDateTime = datetime.datetime.fromisoformat(minDateTime)

    if maxDateTime is not None:
        maxDateTime = datetime.datetime.fromisoformat(maxDateTime)
    else:
        maxDateTime = minDateTime + datetime.timedelta(days=7)

    builder = calendar.new_query()
    filterQuery = None

    if query is not None:
        filterQuery = builder.contains('subject', query)

    if not query is None:
        filterQuery.chain('and').contains('subject', query)

    events = calendar.get_default_calendar().get_events(start_recurring=minDateTime,end_recurring=maxDateTime,include_recurring= True, order_by="start/dateTime asc", limit = maxEntries, query=filterQuery)
    returnEvents = {}
    for event in events:
        print(event)
        returnEvents[event.object_id] = {}
        if 'summary' in requestedInfo:
            returnEvents[event.object_id]['summary'] = event.subject
        if 'description' in requestedInfo:
            returnEvents[event.object_id]['description'] = event.body
        if 'location' in requestedInfo:
            returnEvents[event.object_id]['location'] = event.location.get('displayName', '') if isinstance(event.location, dict) else ''
        if 'start' in requestedInfo:
            returnEvents[event.object_id]['start'] = event.start.isoformat()
        if 'end' in requestedInfo:
            returnEvents[event.object_id]['end'] = event.end.isoformat()
    if asJson:
        return json.dumps(returnEvents)
    return returnEvents

# Add event
def add_event_google(inputDict : dict):
    """Writes events to the selected calendar

    :param inputDict: {'summary', 'description', 'location', 'start', 'end'}
    :type inputDict: Dict
    
    description:
        summary - Name of the event - str

        description - Description of the event - str - optional

        location - Location of the event - str

        start - Time the event starts - datetime object

        end - Time the event ends - datetime object     

    :returns: True if successful False if not   
    """
    event_body = {}

    if 'summary' in inputDict:
        event_body['summary'] = inputDict['summary']
    if 'description' in inputDict:
        event_body['description'] = inputDict['description']
    if 'location' in inputDict:
        event_body['location'] = inputDict['location']
    if 'start' in inputDict:
        event_body['start'] = {'dateTime': inputDict['start'].isoformat()}
    if 'end' in inputDict:
        event_body['end'] = {'dateTime': inputDict['end'].isoformat()}

    try:
        calendar.events().insert(calendarId='primary', body=event_body).execute()
        return 1
    except Exception as e:
        return 0

def add_event_outlook(inputDict : dict):
    """Writes events to the selected calendar

    :param inputDict: {'summary', 'description', 'location', 'start', 'end'}
    :type inputDict: Dict
    
    description:
        summary - Name of the event - str

        description - Description of the event - str - optional

        location - Location of the event - str

        start - Time the event starts - datetime object

        end - Time the event ends - datetime object     

    :returns: True if successful False if not   
    """
    new_event = calendar.get_default_calendar().new_event()
    if 'summary' in inputDict:
        new_event.subject = inputDict['summary']
    if 'description' in inputDict:
        new_event.body = inputDict['description']
    if 'location' in inputDict:
        new_event.location = inputDict['location']
    if 'start' in inputDict:
        new_event.start = inputDict[ 'start']
    if 'end' in inputDict:
        new_event.end = inputDict['end']
    return bool(new_event.save())


# Sign into Calender

def sign_in_google():
    """Opens google sign-in in a new tab and propts the user to sign in, granting access to calendar\n
        :returns: 1 if it successfully signs in"""
    try:
        g_scopes = ['https://www.googleapis.com/auth/calendar']
        creds = None

        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", g_scopes)

        if not creds or not creds.valid:
            # Allow http://localhost for local OAuth testing
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

            # Credentials (Google requires both client_id and client_secret)

            g_flow = Flow.from_client_secrets_file(client_secrets_file="credentials.json",scopes=g_scopes,redirect_uri = "http://localhost:8000")

            g_auth_response = {}


            class OAuthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/favicon.ico':
                        self.send_response(404)
                        self.end_headers()
                        return
                    g_auth_response['url'] = f'http://localhost:8000{self.path}'
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'<h1>Sign-in complete! You can close this tab.</h1>')
                def log_message(self, format, *args):
                    pass


            server = HTTPServer(('localhost', 8000), OAuthHandler)

            # prompt='select_account' ensures the Google account chooser appears every time
            g_url, _ = g_flow.authorization_url()
            webbrowser.open(g_url)
            while 'url' not in g_auth_response:
                server.handle_request()
    
            g_flow.fetch_token(authorization_response=g_auth_response['url'])

            creds = g_flow.credentials
            
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        # Build the Calendar service and fetch the primary calendar
        g_service = build('calendar', 'v3', credentials=creds)
        global calendar
        calendar = g_service
        print('Connected to:', calendar.calendars().get(calendarId='primary').execute()['summary'])
        return 1
    except Exception as e:
        return 0

def sign_in_outlook():
    """Checks if the user is already signed in then may propt the user to sign in\n
        :returns: 1 if it successfully signs in"""
    try:
        #Client ID
        credentials = ('57db46ba-9e70-4bcc-aded-5516137ca290',)
        redirect_uri = 'http://localhost:8000'
        scopes = ['User.Read', 'Calendars.ReadWrite.Shared', 'Calendars.ReadWrite']

        account = Account(credentials, auth_flow_type='public', tenant_id='common')

        if not account.is_authenticated:
            auth_response = {}
            class OAuthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/favicon.ico':
                        self.send_response(404)
                        self.end_headers()
                        return
                    auth_response['url'] = f'http://localhost:8000{self.path}'
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'<h1>Sign-in complete! You can close this tab.</h1>')
                def log_message(self, format, *args):
                    pass
            
            server = HTTPServer(('localhost', 8000), OAuthHandler)

            url, flow = account.con.get_authorization_url(requested_scopes=scopes, redirect_uri=redirect_uri)
            
            url += "&prompt=select_account"
            webbrowser.open(url)
                
            while 'url' not in auth_response:
                server.handle_request()

            account.con.request_token(auth_response['url'], flow=flow, redirect_uri=redirect_uri)
        global calendar
        calendar = account.schedule()
        print("Connected to:", calendar.name)
        return 1
    except Exception as e:
        return 0

# Change Acount
def change_account_google():
    """Opens google sign-in in a new tab and propts the user to sign in, granting access to calendar\n
    :returns: 1 if it successfully signs in"""
    try:
        g_scopes = ['https://www.googleapis.com/auth/calendar']
        creds = None
        # Allow http://localhost for local OAuth testing
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

        g_redirect_uri = 'http://localhost:8000'

        # Credentials (Google requires both client_id and client_secret)

        g_flow = Flow.from_client_secrets_file(client_secrets_file="credentials.json",scopes=g_scopes,redirect_uri = "http://localhost:8000")
        

        g_auth_response = {}


        class OAuthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/favicon.ico':
                    self.send_response(404)
                    self.end_headers()
                    return
                g_auth_response['url'] = f'http://localhost:8000{self.path}'
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>Sign-in complete! You can close this tab.</h1>')
            def log_message(self, format, *args):
                pass


        server = HTTPServer(('localhost', 8000), OAuthHandler)

        # prompt='select_account' ensures the Google account chooser appears every time
        g_url, _ = g_flow.authorization_url()
        webbrowser.open(g_url)
        while 'url' not in g_auth_response:
            server.handle_request()

        g_flow.fetch_token(authorization_response=g_auth_response['url'])

        creds = g_flow.credentials
        with open("token.json", "w") as token:
            token.write(creds.to_json())

        # Build the Calendar service and fetch the primary calendar
        g_service = build('calendar', 'v3', credentials=creds)
        global calendar
        calendar = g_service
        print('Connected to:', calendar.calendars().get(calendarId='primary').execute()['summary'])
        return 1
    except Exception as e:
        return 0

def change_account_outlook():
    """Opens outlook sign-in in a new tab and propts the user to sign in, granting access to calendar\n
         :returns: 1 if it successfully signs in"""
    try:
        #Client ID
        credentials = ('57db46ba-9e70-4bcc-aded-5516137ca290',)
        redirect_uri = 'http://localhost:8000'
        scopes = ['User.Read', 'Calendars.ReadWrite.Shared', 'Calendars.ReadWrite']

        account = Account(credentials, auth_flow_type='public', tenant_id='common')


        auth_response = {}
        class OAuthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/favicon.ico':
                    self.send_response(404)
                    self.end_headers()
                    return
                auth_response['url'] = f'http://localhost:8000{self.path}'
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>Sign-in complete! You can close this tab.</h1>')
            def log_message(self, format, *args):
                pass
            
        server = HTTPServer(('localhost', 8000), OAuthHandler)

        url, flow = account.con.get_authorization_url(requested_scopes=scopes, redirect_uri=redirect_uri)

        url += "&prompt=select_account"
        webbrowser.open(url)
            
        while 'url' not in auth_response:
            server.handle_request()

        account.con.request_token(auth_response['url'], flow=flow, redirect_uri=redirect_uri)
        global calendar
        calendar = account.schedule()
        print("Connected to:", calendar.name)
        return 1
    except Exception as e:
        return 0

# Change Calendar
def set_calendar_site(calendar_provider: str):
    """Sets either Google or Outlook calendar

        :param calendar_provider: 'google' or 'outlook' or anything starting with 'g' or 'o' - not case sensitive

        **Exaple**:: 

            set_calendar_site('Google')
            if not sign_into_calendar():
                print("Something Hates You :(")
            else:
                print("It worked and you are connected to google calendar") """
    global sign_into_calendar, change_calendar_account, read_calendar, add_event
    if calendar_provider.lower()[0] == 'g':
        print("Calendar set to Google")
        sign_into_calendar = sign_in_google
        change_calendar_account = change_account_google
        read_calendar = read_calendar_google
        add_event = add_event_google
    else:
        print("Calendar set to Outlook")
        sign_into_calendar = sign_in_outlook
        change_calendar_account = change_account_outlook
        read_calendar = read_calendar_outlook
        add_event = add_event_outlook