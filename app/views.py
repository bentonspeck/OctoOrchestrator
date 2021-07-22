from __future__ import print_function

from app import app
from datetime import datetime
import pickle
import os.path
from flask import render_template
from flask_wtf import FlaskForm
from flask import request
from wtforms.fields.html5 import DateField
#from wtforms_components import TimeField
from wtforms.fields.html5 import TimeField
from wtforms.fields.html5 import EmailField
from wtforms import StringField

from .configs import Configs, Printers

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import pprint

app.secret_key = 'SHH!'

class ExampleForm(FlaskForm):
    dt = DateField('DateTimePicker', format='%Y-%m-%d')
    start_hour = TimeField('start_hour')
    end_hour = TimeField('end_hour')
    email = EmailField('email')

class ExampleUser(FlaskForm):
  username = StringField('Username')
  password = StringField('Password')

@app.route('/test')
def test():
  c = Configs()
  p = Printers(c)
  
  p.updateUserPermissions()

  return "Hi"

@app.route('/', methods=['POST','GET'])
def admin():
  c = Configs()
  p = Printers(c)
  form = ExampleForm()
  if form.validate_on_submit():
    print(form.dt.data.strftime('%Y-%m-%d'))
  #return render_template('admin.html', form=form, printers = p.list)
  form_data = request.form
  print(form_data)
  alert = ''
  
  if(form_data != {}):
    dt_start = datetime.strptime(form_data['dt'] + " " + form_data['start_hour'], '%Y-%m-%d %H:%M')
    dt_end = datetime.strptime(form_data['dt'] + " " + form_data['end_hour'], '%Y-%m-%d %H:%M')
    if(dt_end < dt_start):
      alert = "End time before start time"
    else:
      SCOPES = ['https://www.googleapis.com/auth/calendar']
      key_path = "EngineeringPrinterCalendars-783e49d14e33.json"
      creds = service_account.Credentials.from_service_account_file(
        key_path, scopes=SCOPES,)
      # Endpoint to calendar API
      service = build('calendar', 'v3', credentials=creds)

      EVENT = {
          'summary' : 'Test event insertion',
          'description' : form_data['email'],
          'start' : {'dateTime': dt_start.isoformat(), 'timeZone': 'America/New_York' },
          'end' : {'dateTime' : dt_end.isoformat(), 'timeZone': 'America/New_York'}

      }
      #print(EVENT)
      e = service.events().insert(calendarId = '', 
                                  sendNotifications = True, body = EVENT).execute()

  p.updateStatus()
  printers = c.printers

  return render_template('admin.html', form=form, printers = printers, alert = alert, len = len(printers))

@app.route('/update', methods = ['POST', 'GET'])
def update():
  c = Configs()
  p = Printers(c)
  form = ExampleUser()
  p.populateUsers()
  users = p.getUsers()
  # pprint.pprint(users)
  form_data = request.form
  # print(form_data)

  for user in users:
    print("Username: {}".format(user['name']) )
    pprint.pprint(user)

  if(form_data != {}):
    username = form_data['username']
    password = form_data['password']
    print("Username to insert: {}".format(username))
    print("Password to insert: {}".format(password))
    p.insertUser(username, password)
    users = p.getUsers()


  return render_template('update.html', form = form, printers = p, userlist = users, len = len(users))
