import credentials
import datetime
import json
import praw
import prawcore
import re
import requests
import time
import telegram
import urllib.request
import youtube_dl
from dateutil import tz, parser
from bs4 import BeautifulSoup

#TODO: rehost on imgur
#TODO: move downloading and Telegram to further down the thread

def login():
    r = praw.Reddit('juvegoalbot')
    return r

# Find the kickoff time of the next match
def getKickoff():
    url = 'https://www.fctables.com/teams/juventus-187903/iframe/?type=team-next-match&country=108&team=187903&timezone=Australia/Sydney&time=24'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    nextMatch = (soup.find("div", {"class": "date"}).text)
    teamA = (soup.find("div", {"class": "team_a"}).text)
    teamB = (soup.find("div", {"class": "team_b"}).text)
    kickoff = datetime.datetime.strptime(nextMatch, '%d %B %Y %H:%M')
    countdown = kickoff - datetime.datetime.now()
    print(f"Countdown to {teamA} vs {teamB} at {kickoff} is {countdown}")
    return kickoff, countdown, teamA, teamB

# Notify via Telegram
def telegram_send(subid):
    chat_id = credentials.telegram_chat_id
    token = credentials.telegram_token
    bot = telegram.Bot(token=token)
    bot.send_video(chat_id=chat_id, video=open(f'videos/{subid}.mp4', 'rb'), supports_streaming=True)

# Download video
def ytdownload(subid,suburl):
    ydl_opts = {'outtmpl': ('videos/{0}.mp4').format(subid)}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'{suburl}'])

def main():
    r = login()
    goalSummary = ""
    matchThread = ""
    postMatchThread = ""
    searchTerms = ("Juventus", "Juve", "Szczesny", "De Sciglio", "Chiellini", "De Ligt", "Arthur Melo", "Khedira", "Cristiano",\
        "Ronaldo", "Ramsey", "Dybala", "Douglas Costa", "Alex Sandro", "Danilo", "McKennie", "Cuadrado", "Bonucci", "Rugani",\
        "Rabiot", "Demiral", "Bentancur", "Pinsoglio", "Bernardeschi", "Kulusevski", "Buffon", "Pirlo")

    with open("logs/goalsfromrsoccer/submissionsUsed.txt", "r") as f:
        submissions_used = f.read()
        submissions_used = submissions_used.split("\n")
        submissions_used = list(filter(None, submissions_used))

    with open("logs/goalsfromrsoccer/alternatesUsed.txt", "r") as f:
        alternates_used = f.read()
        alternates_used = alternates_used.split("\n")
        alternates_used = list(filter(None, alternates_used))

    with open("logs/goalsfromrsoccer/stickiesReplied.txt", "r") as f:
        stickies_replied = f.read()
        stickies_replied = stickies_replied.split("\n")
        stickies_replied = list(filter(None, stickies_replied))

    # Get kickoff times
    kickoff, countdown, teamA, teamB = getKickoff()
    
    # If match hasn't kicked off, wait until it has. Otherwise continue.
    if kickoff > datetime.datetime.now():
        print(f"Waiting {round((countdown).total_seconds())} seconds until match starts")
        time.sleep(countdown.seconds)
        # TODO: - telegram_send(f"{teamA} vs {teamB} is starting. Bot starting up!")
    
    # Tell the script how long to run
    end_time = datetime.datetime.now() + datetime.timedelta(hours=3)

    while datetime.datetime.now() < end_time:
        try:
            # Search through submissions on /r/juve
            for submission in r.subreddit('juve').stream.submissions(pause_after=-1):
                if submission is None:
                    break

                # Find the ID of the Match Thread
                if submission.link_flair_text == "Match Thread":
                   matchThread = r.submission(id=submission.id)

                # Find the ID of the Post-Match Thread
                if submission.link_flair_text == "Post-Match Thread":
                   postMatchThread = r.submission(id=submission.id)

            # Gather goal submissions #
            for submission in r.subreddit('soccer').stream.submissions(skip_existing=True):
                if submission is None:
                    break

                if matchThread != "":
                    for i in searchTerms:
                    # Search for submissions containing search terms and flaired as Media or Mirror
                        if re.search(i, submission.title, re.IGNORECASE) and (submission.link_flair_text == "Media" or submission.link_flair_text == "Mirror"):
                            if submission.id not in submissions_used:
                                # Post goals to the match thread
                                print(f"({submission.id}) Posting \"{submission.title}\" to {matchThread.title}")
                                newGoal=f"[{submission.title}]({submission.url}) | {str(submission.author)} | [discuss]({submission.permalink})\n\n"

                                # Download video
                                ytdownload(submission.id,submission.url)
                                # Send to Telegram
                                telegram_send(submission.id)
                                # Post goal to match thread
                                matchThread.reply(newGoal)
                                # Add to goal summary
                                goalSummary += newGoal
                                # Mark submission as used
                                submissions_used.append(submission.id)
                                # Write our updated list back to the file
                                with open("logs/goalsfromrsoccer/submissionsUsed.txt", "w") as f:
                                    for i in submissions_used:
                                            f.write(i + "\n")

                            # Find alternate angles
                            for top_level_comment in submission.comments:
                                submission.comments.replace_more(limit=None)
                                if top_level_comment.stickied:
                                    for second_level_comment in top_level_comment.replies:
                                        if "http" in second_level_comment.body and second_level_comment.id not in alternates_used:
                                            
                                            # Post AA to match thread
                                            for top_level_comment in matchThread.comments:
                                                if submission.id in top_level_comment.body:
                                                    print(f"({second_level_comment.id} -> {submission.id}) Adding AA to {submission.title}")
                                                    top_level_comment.reply(f"{second_level_comment.body} | {str(second_level_comment.author)} | [discuss]({second_level_comment.permalink})")

                                                    # Mark AA as used
                                                    alternates_used.append(second_level_comment.id)

                                                    # Write our updated list back to the file
                                                    with open("logs/goalsfromrsoccer/alternatesUsed.txt", "w") as f:
                                                        for i in alternates_used:
                                                            f.write(i + "\n")

            if postMatchThread != "" and goalSummary != "":
                # Reply to post-match thread
                for top_level_comment in postMatchThread.comments:
                    # If we find a stickied comment that contains the keywords:
                    if top_level_comment.stickied and ("highlights" in top_level_comment.body or "to this comment" in top_level_comment.body):
                        # If comment hasn't been replied to
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

        # For session time outs
        except prawcore.exceptions.ServerError as http_error:
            print(http_error)
            print('waiting 1 minute')
            time.sleep(60)
        except prawcore.exceptions.ResponseException as response_error:
            print(response_error)
            print('waiting 1 minute')
            time.sleep(60)
        except prawcore.exceptions.RequestException as request_error:
            print(request_error)
            print('waiting 1 minute')
            time.sleep(60)
        except Exception as e:
            print('error: {}'.format(e))
            print('waiting 1 minute')
            time.sleep(60)


if __name__ == '__main__':
    main()
