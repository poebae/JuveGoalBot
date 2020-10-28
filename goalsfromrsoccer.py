import credentials
import datetime
import json
import praw
import prawcore
import re
import requests
import sys
import time
import telegram
import urllib3
import urllib.request
import youtube_dl
from dateutil import tz, parser
from bs4 import BeautifulSoup

#TODO: rehost on imgur

graham_chat_id = credentials.graham_chat_id
gjustjuve_chat_id = credentials.gjustjuve_chat_id
token = credentials.telegram_token
bot = telegram.Bot(token=token)

def login():
    r = praw.Reddit('juvegoalbot')
    return r

r = login()

# Find the kickoff time of the next match
def getKickoff():
    while True:
        try: 
            url = 'https://www.fctables.com/teams/juventus-187903/iframe/?type=team-next-match&country=108&team=187903&timezone=Australia/Sydney&time=24'
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            nextMatch = (soup.find("div", {"class": "date"}).text)
            global teamA
            teamA = (soup.find("div", {"class": "team_a"}).text)
            global teamB
            teamB = (soup.find("div", {"class": "team_b"}).text)
            kickoff = datetime.datetime.strptime(nextMatch, '%d %B %Y %H:%M')
            countdown = kickoff - datetime.datetime.now() - datetime.timedelta(minutes=30)
            return kickoff, countdown, teamA, teamB

        except requests.ConnectionError as e:
            print("Connection Error. Make sure you are connected to the internet.\n")
            print(str(e))            
            continue
        except requests.Timeout as e:
            print("Timeout Error")
            print(str(e))
            continue
        except requests.RequestException as e:
            print("General Error")
            print(str(e))
            continue
        except (KeyboardInterrupt, SystemExit):
            print("\ngetKickoff interrupted")
            sys.exit(0)
        
# Telegram video
def telegram_video(chatid,subid,caption):
    bot.send_video(chat_id=chatid, caption=caption, video=open(f'videos/{subid}.mp4', 'rb'), supports_streaming=True)
    
# Telegram message
def telegram_msg(message):
    bot.send_message(chat_id=graham_chat_id, text=message)

# Download video
def ytdownload(subid,suburl):
    ydl_opts = {'no-check-certificate': True, 'outtmpl': ('videos/{0}.mp4').format(subid)}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'{suburl}'])

def getMatchThread():
    # Look for match thread on /r/juve
    for submission in r.subreddit('juve').stream.submissions(pause_after=-1):
    # for submission in r.subreddit('juve').stream.submissions(skip_existing=True):
        if submission is None:
            break
        if submission.link_flair_text == "Match Thread":
            print(f"Match thread found: {submission.id}")
            matchThread = r.submission(id=submission.id)
        else:
            matchThread = ""
    return matchThread

def getPostMatchThread():
    for submission in r.subreddit('juve').stream.submissions(skip_existing=True):
    # for submission in r.subreddit('juve').stream.submissions(pause_after=-1):
        if submission is None:
            break
        # Find the ID of the Post-Match Thread
        if submission.link_flair_text == "Post-Match Thread":
            postMatchThread = r.submission(id=submission.id)
            print(f"({datetime.datetime.now().time()}) Post-match thread found: {submission.title} ({submission.id})")
        else:
            postMatchThread = ""
    return postMatchThread

def getGoals():
    searchTerms = ("Juventus", "Juve", "Szczesny", "De Sciglio", "Chiellini", "De Ligt", "Arthur Melo", "Khedira", "Cristiano",\
        "Ronaldo", "Ramsey", "Dybala", "Douglas Costa", "Alex Sandro", "Danilo", "McKennie", "Cuadrado", "Bonucci", "Rugani",\
        "Rabiot", "Demiral", "Bentancur", "Pinsoglio", "Bernardeschi", "Kulusevski", "Buffon", "Pirlo", teamA, teamB)
    with open("logs/goalsfromrsoccer/submissionsUsed.txt", "r") as f:
        submissions_used = f.read()
        submissions_used = submissions_used.split("\n")
        submissions_used = list(filter(None, submissions_used))

    for submission in r.subreddit('soccer').stream.submissions(pause_after=-1):
    # for submission in r.subreddit('soccer').stream.submissions(skip_existing=True):
        if submission is None:
            break

        for i in searchTerms:
        # Search for submissions containing search terms and flaired as Media or Mirror
            if re.search(i, submission.title, re.IGNORECASE) and (submission.link_flair_text == "Media" or submission.link_flair_text == "Mirror"):
                # Mark submission as used
                if submission.id not in submissions_used and submission.id not in submission_queue:
                    submission_queue.append(submission.id)
                    print(f"Submission queue: {submission_queue}")

def postGoals():
    goalSummary = ""
    with open("logs/goalsfromrsoccer/submissionsUsed.txt", "r") as f:
        submissions_used = f.read()
        submissions_used = submissions_used.split("\n")
        submissions_used = list(filter(None, submissions_used))

    for i in submission_queue:
        submission = r.submission(id=i)
        submission.comments.replace_more(limit=None)
        if submission.id not in submissions_used:
            print(f"\n({submission.id}) Posting \"{submission.title}\" to {matchThread.title}")
            newGoal=f"[{submission.title}]({submission.url}) | {str(submission.author)} | [discuss]({submission.permalink})\n\n"
            # Post goal to match thread
            matchThread.reply(newGoal)
            # Add to goal summary
            goalSummary += newGoal

            # Also post goal to sticky comment in match thread
            for top_level_comment in matchThread.comments:
                if top_level_comment.stickied:
                    print(f"Posting {submission.id} to match thread sticky")
                    top_level_comment.reply(newGoal)

            # Mark submission as used
            submissions_used.append(submission.id)

            # Write our updated list back to the file
            with open("logs/goalsfromrsoccer/submissionsUsed.txt", "w") as f:
                for i in submissions_used:
                        f.write(i + "\n")

            # Download video
            ytdownload(submission.id,submission.url)

            # Send to GJustJuve group
            print(f"\n({submission.id}) GJustjuve: sending {submission.title}")
            telegram_video(gjustjuve_chat_id,submission.id,submission.title)

            # Send to Graham
            print(f"({submission.id}) Graham: sending {submission.title}\n")
            telegram_video(graham_chat_id,submission.id,submission.title)

def alternateAngles():
    with open("logs/goalsfromrsoccer/alternatesUsed.txt", "r") as f:
        alternates_used = f.read()
        alternates_used = alternates_used.split("\n")
        alternates_used = list(filter(None, alternates_used))

    for i in submission_queue:
        submission = r.submission(id=i)      
        submission.comments.replace_more(limit=None)
        for top_level_comment in submission.comments:
            if top_level_comment.stickied:
                for second_level_comment in top_level_comment.replies:
                    if "http" in second_level_comment.body and second_level_comment.id not in alternates_used:
                        # Post AA to match thread
                        for top_level_comment in matchThread.comments:
                            if submission.id in top_level_comment.body:
                                print(f"({second_level_comment.id} -> {submission.id}) Adding AA to {submission.title}({top_level_comment.id})")
                                top_level_comment.reply(f"{second_level_comment.body} | {str(second_level_comment.author)} | [discuss]({second_level_comment.permalink})")

                                # Mark AA as used
                                alternates_used.append(second_level_comment.id)

                                # Write our updated list back to the file
                                with open("logs/goalsfromrsoccer/alternatesUsed.txt", "w") as f:
                                    for i in alternates_used:
                                        f.write(i + "\n")

def uniqueAA():
    altAngles = []
    with open("logs/goalsfromrsoccer/alternatesUsed.txt", "r") as f:
        alternates_used = f.read()
        alternates_used = alternates_used.split("\n")
        alternates_used = list(filter(None, alternates_used))

    for i in alternates_used:
        comment = r.comment(id=i)
        # Find unique AAs that aren't just mirrors and send videos via Telegram
        if any(j in comment.body for j in ["AA","lternate","ngle","ommenta"]):
            altAngles = re.findall('(?<=)http.+?(?=[)\'\" ])', comment.body)
            for k in altAngles:
                print(f"\n({comment.id}) Downloading unique AA: {k}")
                try:
                    # Download video
                    ytdownload(comment.id,k)
                    pass
                #TODO: this is bogus. Need to catch the right error
                except urllib3.exceptions.HTTPError as http_error:
                    print(http_error)
                    continue

                try:
                    # Send to GJustJuve group
                    print(f"\n({second_level_comment.id}) GJustJuve: sending AA: {i}")
                    telegram_video(gjustjuve_chat_id,second_level_comment.id,f"Replay of {submission.title}")
                    pass

                    # Send to Graham
                    print(f"\n({comment.id}) Graham: sending AA: {k}")
                    telegram_video(graham_chat_id,comment.id,f"Replay of {submission.title}")
                    pass

                #TODO: this is bogus. Need to catch the right error
                except urllib3.exceptions.TimeoutError as timeout_error:
                    print(timeout_error)
                    continue

def postMatchSummary():
    if postMatchThread != "" and goalSummary != "":
        # Reply to post-match thread
        postMatchThread.comments.replace_more(limit=None)
        for top_level_comment in postMatchThread.comments:
            # If we find a stickied comment that contains the keywords:
            if top_level_comment.stickied and ("highlights" in top_level_comment.body or "to this comment" in top_level_comment.body):
                # If comment hasn't been replied to

                with open("logs/goalsfromrsoccer/stickiesReplied.txt", "r") as f:
                    stickies_replied = f.read()
                    stickies_replied = stickies_replied.split("\n")
                    stickies_replied = list(filter(None, stickies_replied))

                if top_level_comment.id not in stickies_replied:
                    print(f"Posting goal summary to {postMatchThread.title} ({top_level_comment.id})\n")

                    # Submit the goal summary
                    top_level_comment.reply(goalSummary)

                    # Add comment id to list
                    stickies_replied.append(top_level_comment.id)

                    # Write our updated list back to the file
                    with open("logs/goalsfromrsoccer/stickiesReplied.txt", "w") as f:
                        for top_level_comment.id in stickies_replied:
                            f.write(top_level_comment.id + "\n")

def main():
    matchThread = ""
    postMatchThread = ""
    global submission_queue
    submission_queue = []

    # Get kickoff times
    kickoff, countdown, teamA, teamB = getKickoff()

    # If match hasn't kicked off, wait until it has.
    if kickoff > datetime.datetime.now():
        print(f"({datetime.datetime.now().time()}) Script for {teamA} vs {teamB} at {kickoff} starting in {countdown}")
        print(f"({datetime.datetime.now().time()}) Starting script in {round((countdown).total_seconds())} seconds")
        time.sleep(countdown.seconds)
        print(f"({datetime.datetime.now().time()}) Telegram: sending bot init message for {teamA} vs {teamB}")
        telegram_msg(f"({datetime.datetime.now().time()}) {teamA} vs {teamB} is kicking off soon. Bot starting up!")

    else:
        print(f"({datetime.datetime.now().time()}) {teamA} vs {teamB} already started {datetime.datetime.now() - kickoff} ago.")

    # Tell the script how long to run
    end_time = datetime.datetime.now() + datetime.timedelta(hours=3)

    while datetime.datetime.now() < end_time:
        try:
            if matchThread == "":
                matchThread = getMatchThread()
            if matchThread == "":
                postMatchThread = getPostMatchThread()

            getGoals()
            time.sleep(30)
            if submission_queue != []:
                postGoals()
                alternateAngles()
                uniqueAA()
                postMatchSummary()
                postMatchThread = getPostMatchThread()

        # For session time outs
        except prawcore.exceptions.ServerError as http_error:
            print(http_error)
        except prawcore.exceptions.ResponseException as response_error:
            print(response_error)
        except prawcore.exceptions.RequestException as request_error:
            print(request_error)
        except Exception as e:
            print('error: {}'.format(e))
        except (KeyboardInterrupt, SystemExit):
            print("\nProgram closed by keyboard interrupt")
            sys.exit(0)

    # After script has run for prescribed length, run it again for the next kickoff time
    main()

if __name__ == '__main__':
    main()
