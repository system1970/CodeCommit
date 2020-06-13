from flask import *
import requests
import datetime
from pytz import timezone
from tzlocal import get_localzone
import atexit
from github import Github
import os
import base64
import json
import time
import pyrebase
from git import Repo
import threading,time
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup as bs4

config = {
"apiKey": "",
"authDomain": "",
"databaseURL": "",
"projectId": "",
"storageBucket": "",
"messagingSenderId": "",
"appId": "",
"measurementId": ""
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()
auth = firebase.auth()
app = Flask(__name__)
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True

@app.route('/', methods=['GET', 'POST'])

def login():
    unsuccessful = 'Please check your credentials'
    successful = 'Login successful'
    try:
        auth.revoke_refresh_tokens(uid)
        currentUser = auth.get_user(uid)
    except:
        if request.method == 'POST':
            email = request.form['name']
            password = request.form['pass']
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                return render_template('main.html')
            except:
                return render_template('signin.html', us=unsuccessful)

    return render_template('signin.html')

@app.route('/infoGet', methods=['GET', 'POST'])

def GetData():
    uds = 'Please check your credentials'
    if request.method == 'POST':
        cfUser = request.form['CFuser']
        gitUser = request.form['GITuser']
        gitToken = request.form['GIToken']
        try:
            data = {"gitToken":gitToken,
                    "codeForces":cfUser,
                    "github":gitUser}
            repo_name = "CodeForces"
            userToken = db.child("userInfo").push(data)
            create_repo(gitToken,repo_name)
            print(userToken,"why?")
            return render_template('main.html')
        except:
            return render_template('main.html',us=uds)

    return render_template('main.html')

def create_repo(gitToken,repo_name):
    try:
        g = Github(str(gitToken)) 
        u = g.get_user()
        repo = u.create_repo(repo_name)
    except:
        pass
    
# if __name__ == "__main__":
#         app.run()

# Shut down the scheduler when exiting the app
