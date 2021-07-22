from octorest import OctoRest # https://github.com/dougbrion/OctoRest/blob/master/examples/basic/basic.py
import time
import pytz
from datetime import datetime
from datetime import timezone
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import pprint

# Allow engineeringcalendaraccount@engineeringprint-1609644207615.iam.gserviceaccount.com to view and edit the calendar & sheet

def convertStringToDateTime(s):
  s = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
  s = datetime.strftime(s, "%Y-%m-%dT%H:%M:%S")
  s = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")

  return s


class Configs:
  def __init__(self):
    # TODO: Load this data from a Google Spreadsheet
    # Maybe set up a timer so this is pulled every minute or so, pickle in the mean time
    #self.data_sheet = "TODO"
    #self.printers = [{"name":"P1", "ip":"192.168.1.5", "active":True, "calendar":"c_r7jkg25rvirsqgq0forq36eq14@group.calendar.google.com"},
    #                 {"name":"P2", "ip":"192.168.1.5", "active":True, "calendar":"c_9epim815br09idqsdkm5tc6ohs@group.calendar.google.com"},
    #                ]
    self.printers = [{"name":"P1", "ip":"192.168.1.71:5000", "active":True, "calendar":"", 
                      "api_key" : ''}
                    ]
    self.printer_open_hour = "8AM"
    self.printer_close_hour = "9PM"
    self.printer_application_name = 'PrinterManager'
    self.users = [{"username" : "bob", "password" : "apple"}, 
                  {"username" : "bill", "password" : "banana"}, 
                  {"username" : "phil", "password" : "car"}]
                  # {"username" : "phil", "password" : "car", "email" : "something@gmail.com"}
    self.cal = Calendar(self)

class Calendar:
  # useful code for event data retrieval
  # events_result = service.events().list(calendarId='uindy.edu_tbged76iuh3nj034t99cucqcvc@group.calendar.google.com', timeMin=now,
  #                                      maxResults=10, singleEvents=True,
  #                                      orderBy='startTime').execute()
  # https://developers.google.com/calendar/v3/reference/events/list
  def __init__(self, config):
    self.config = config

  # needs to return a dictionary where key is the printer name
  # and the value is a list of active/ inactive users
  def getActiveUsers(self):
    return {'P1' : ['bob', 'bill']}

  def getInactiveUsers(self):
    return {'P1' : ['phil']}


class Printers:
  def __init__(self, config):
    self.configs = config
    self.list = self.configs.printers
    self.client = OctoRest(url=f"http://{self.configs.printers[0]['ip']}", apikey = self.configs.printers[0]['api_key'])
    self.updateStatus()

  def updateStatus(self):
    for printer in self.configs.printers:
      attempt = 2
    while attempt > 0:
      try:
        print(f"http://{printer['ip']}")
        self.client.connect()
        printer['status'] = str(self.client.printer()['state']['text'])
        break
      except Exception as e:
        printer['status'] = e
        # Try to do a connect
        time.sleep(1)
        attempt -= 1

  # populates users in all printers and sets read-only access by default
  def populateUsers(self):
    for printer in self.configs.printers: 
      self.client.connect()

      for user in self.configs.users:
        # print("Username {}".format(user['username']))
        try:
          self.client.delete_user(user['username'])
          self.client.user(user['username'])
          print("Already registered")
        except:
          self.client.add_user(user['username'], user['password'], False, False)
          setting = {'user' : ['inactive']}
          self.client.update_user_settings(user['username'], setting)

  # Looks up who has full access based on calendar information
  # everyone else has read-only access

  def updateUserPermissions(self):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    key_path = "EngineeringPrinterCalendars-783e49d14e33.json"
    creds = service_account.Credentials.from_service_account_file(
            key_path, scopes=SCOPES,)
    service = build('calendar', 'v3', credentials=creds)
    events_result = service.events().list(calendarId = ''
                                          ).execute()
    events = events_result.get('items', [])
    self.client.connect()

    if not events:
      print('No upcoming events found.')
    else:
      # pprint.pprint(events)
      for event in events:
        start = convertStringToDateTime(event['start']['dateTime'])
        end = convertStringToDateTime(event['end']['dateTime'])
        
        now = datetime.now(pytz.timezone('America/New_York') ).isoformat()
        now = datetime.strptime(now, '%Y-%m-%dT%H:%M:%S.%f%z')
        now = datetime.strftime(now, '%Y-%m-%dT%H:%M:%S')
        now = datetime.strptime(now, '%Y-%m-%dT%H:%M:%S')
        
        print("Start: {} to End: {}".format(start, end) )
        print("{} from {} to {}".format(event['summary'], start, end) )
        print(now)

        if now > start and now < end:
          print("Success!")
          user = event['description'].split("@")[0]
          print("User: {}".format(user) )
          setting = {'user' : ['active']}
          self.client.update_user_settings(user, setting)
          # (user data, admin privs, active)
          self.client.update_user(user, False, True)
        """
        else:
          user = event['description'].split("@")[0]
          setting = {'user' : ['inactive']}
          self.client.update_user_settings(user, setting)
          self.client.update_user(user, False, False)
        """

  def getUsers(self):
    self.client.connect()
    try:
      test = self.client.users()['users']
      #print(test)
      return test
    except:
      print("No users in system")

  def getUser(self, user):
    self.client.connect()
    try:
      test = self.client.user(user)
      print(test['name'])
    except:
      print("User not found")

  def insertUser(self, user, password):
    self.client.connect()

    try:
      self.client.user(user)
      print("User already registered")
    except:
      print(client.add_user(user, password, False, False))
      setting = {'user' : ['readonly']}
      self.client.update_user_settings(user['username'], setting)

  def deleteUser(self, user):
    self.client.connect()
    try:
      self.client.delete_user(user)
      print("Deleted {}".format(user))
    except:
      print("{} not found".format(user))