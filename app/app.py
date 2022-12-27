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
print("App Started")

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
                print("Login successfully")
                return render_template('main.html')
            except:
                print("Login failed")
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
            print("Successfully created user")
            return render_template('main.html')
        except:
            print("User creation failed")
            return render_template('main.html',us=uds)

    return render_template('main.html')

def create_repo(gitToken,repo_name):
    try:
        g = Github(str(gitToken)) 
        u = g.get_user()
        repo = u.create_repo(repo_name)
        print("Successfully created repo")
    except:
        print("Repo creation failed")
        pass

def App(cfUser,gitUser,gitToken):
    # getting submissions
    repo_name = "CodeForces"
    try:
        r = requests.get("https://codeforces.com/api/user.status?handle="+str(cfUser)+"&from=1&count=50")
        json_format_before = r.json()
        json_format = []

        # current day submissions
        for i in range(50):
            timestamp = json_format_before["result"][i]["creationTimeSeconds"]
            value = datetime.datetime.fromtimestamp(timestamp)
            # timezone correction -> {
            format = "%d"
            # Current time in UTC
            UTC = datetime.datetime.now(timezone('UTC'))
            # Convert to local time zone
            local = UTC.astimezone(get_localzone())
                                                            # : 1)convert now() to current timezone (100% complete)
                                                            #       2)change it to be user input 
            if (datetime.datetime.now().day==value.day):    
                json_format.append(json_format_before["result"][i])
            else:
                break
            # } <-
        # no submission for the day
        if len(json_format)!=0:
            problems = {}
            for i in range(len(json_format)):
                problem_name = json_format[i]["problem"]["name"]
                if json_format[i]["verdict"]=="OK" and problem_name not in problems:
                    problem_type = json_format[i]["problem"]["index"]
                    submission_id = json_format[i]["id"]
                    contest_id = json_format[i]["contestId"]
                    problems[problem_name] = True
                    # get problem url and name
                    prblm_url = "https://codeforces.com/problemset/problem/"
                    prblm_link = "# "+prblm_url+str(contest_id)+'/'+str(problem_type)
                    prblm_name = "# "+str(problem_name)

                    # scrape solution
                    contest_url = "https://codeforces.com/contest/"
                    submission = requests.get(contest_url+str(contest_id)+"/submission/"+str(submission_id))
                    soup = bs4(submission.content,features="html.parser")
                    soln_code = soup.findAll("pre", attrs={"id": "program-source-text"})
                    code_prefix = '[<pre class="prettyprint lang-py linenums program-source" id="program-source-text" style="padding: 0.5em;">' # : generalize for lang
                    add_prblm_link = str(soln_code).replace(code_prefix,prblm_link+"\n"+prblm_name+"\n\n")
                    solution = str(add_prblm_link).replace("</pre>]","") 
                    file_text = solution
                    sha_link = requests.get("https://api.github.com/repos/"+str(gitUser)+"/"+str(repo_name)+"/contents/"+str(problem_type)+"/"+str(problem_name)+".py",
                                        auth=(str(gitUser), str(gitToken)))
                    try:    
                        sha = sha_link.json()['sha']
                        urlSafeEncodedBytes = base64.urlsafe_b64encode(file_text.encode("utf-8"))
                        urlSafeEncodedStr = str(urlSafeEncodedBytes, "utf-8")
                        payload = {"message": "added solutions to repo",
                                "author": {"name": str(gitUser),"email": "prabhakaran.code@gmail.com"},
                                "content": urlSafeEncodedStr,
                                "sha": sha}
                        readme = requests.put("https://api.github.com/repos/"+str(gitUser)+"/"+str(repo_name)+"/contents/"+str(problem_type)+"/"+str(problem_name)+".py", 
                                            auth=(str(gitUser), str(gitToken)), 
                                            json=payload)
                    except:
                        urlSafeEncodedBytes = base64.urlsafe_b64encode(file_text.encode("utf-8"))
                        urlSafeEncodedStr = str(urlSafeEncodedBytes, "utf-8")
                        payload = {"message": "added solutions to repo",
                                "author": {"name": str(gitUser),"email": "prabhakaran.code@gmail.com"},
                                "content": urlSafeEncodedStr}
                        readme = requests.put("https://api.github.com/repos/"+str(gitUser)+"/"+str(repo_name)+"/contents/"+str(problem_type)+"/"+str(problem_name)+".py", 
                                            auth=(str(gitUser), str(gitToken)), 
                                            json=payload)
    except:
        print("Fetch failed")

@app.route("/runscript")
def Iterate():
    inventory = db.child("userInfo").get()
    for user in inventory.each():
        App(user.val()['codeForces'],user.val()['github'],user.val()['gitToken'])
    print("============>Pushed to GitHub<============")
    return "Success"

def clampRotation(angle, lowerBound, upperBound):
    angle += 360 if angle < 0 else 0
    if angle>180:
        return max(angle, 360 + lowerBound)
    return min(angle, upperBound)

# if __name__ == "__main__":
#         app.run()

# Shut down the scheduler when exiting the app
