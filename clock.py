from apscheduler.schedulers.blocking import BlockingScheduler
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
from bs4 import BeautifulSoup as bs4

def App(cfUser,gitUser,gitToken):
    # getting submissions
    repo_name = "CodeForces"
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
                                                        # : 1)convert now() to current timezone (100% completeT)
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
                    readme = requests.put("https://api.github.com/repos/"+str(gitUser)+"/"+str(repo_name)+"/contents/Codeforces/"+str(problem_type)+"/"+str(problem_name)+".py", 
                                        auth=(str(gitUser), str(gitToken)), 
                                        json=payload)

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

sched = BlockingScheduler()

@sched.scheduled_job('interval', hours=24, max_instances=999)
def Iterate():
    inventory = db.child("userInfo").get()
    for user in inventory.each():
        App(user.val()['codeForces'],user.val()['github'],user.val()['gitToken'])
    print("Pushed to GitHub")
sched.start()
