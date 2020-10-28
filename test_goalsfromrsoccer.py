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
    # Search through submissions on /r/juve
    for submission in r.subreddit('juve_goal_bot').stream.submissions(pause_after=-1):
        if submission is None:
            break
        if submission.link_flair_text == "Match Thread":
            matchThread = r.submission(id=submission.id)
        else:
            matchThread = ""
    return matchThread

def getPostMatchThread():
    for submission in r.subreddit('juve_goal_bot').stream.submissions(pause_after=-1):
        if submission is None:
            break
        # Find the ID of the Post-Match Thread
        if submission.link_flair_text == "Post-Match Thread":
            postMatchThread = r.submission(id=submission.id)
            print(f"({datetime.datetime.now().time()}) Post-match thread found: {submission.title} ({submission.id})")
        else:
            postMatchThread = ""
    return postMatchThread

def main():
    goalSummary = ""
    matchThread = ""
    postMatchThread = ""
    altAngles = []
    searchTerms = ("Fulham", "Villa", "Liverpool", "Arsenal", "Bologna", "Belenenses", "Genk", "Antalyaspor", "Fluminense", "Khimki", "Troyes", "Paderborn", "Jong", "Telstar", "Estoril", "Boluspo", "Menemenspor")
    # searchTerms = (input("Enter search terms: ")).split()

    # Tell the script how long to run
    end_time = datetime.datetime.now() + datetime.timedelta(hours=3)
    while datetime.datetime.now() < end_time:
        try:
            if matchThread == "":
                matchThread = getMatchThread()
            if postMatchThread == "":
                postMatchThread = getPostMatchThread()

            # Gather goal submissions
            for submission in r.subreddit('soccer').stream.submissions(pause_after=-1):
                if submission is None:
                    break

                if matchThread != "":
                    matchThread.comments.replace_more(limit=None)
                    for i in searchTerms:
                    # Search for submissions containing search terms and flaired as Media or Mirror
                        if re.search(i, submission.title, re.IGNORECASE) and (submission.link_flair_text == "Media" or submission.link_flair_text == "Mirror"):
                            submission.comments.replace_more(limit=None)

                            with open("logs/goalsfromrsoccer/submissionsUsed.txt", "r") as f:
                                submissions_used = f.read()
                                submissions_used = submissions_used.split("\n")
                                submissions_used = list(filter(None, submissions_used))

                            if submission.id not in submissions_used:
                                # Post goals to the match thread
                                print(f"({submission.id}) Posting \"{submission.title}\" to {matchThread.title}")
                                newGoal=f"[{submission.title}]({submission.url}) | {str(submission.author)} | [discuss]({submission.permalink})\n\n"

                                # Post goal to match thread
                                matchThread.reply(newGoal)

                                for top_level_comment in matchThread.comments:
                                    if top_level_comment.stickied:
                                        print(f"{submission.id} Posting to match thread sticky comment")
                                        top_level_comment.reply(newGoal)

                                # Add to goal summary
                                goalSummary += newGoal
                                # Mark submission as used
                                submissions_used.append(submission.id)
                                # Write our updated list back to the file
                                with open("logs/goalsfromrsoccer/submissionsUsed.txt", "w") as f:
                                    for i in submissions_used:
                                            f.write(i + "\n")

                                # Download video
                                ytdownload(submission.id,submission.url)

                                # Send to GJustJuve group
                                # print(f"\n({submission.id}) GJustjuve: sending {submission.title}")
                                # telegram_video(gjustjuve_chat_id,submission.id,submission.title)

                                # Send to Graham
                                print(f"\n({submission.id}) Graham: sending {submission.title}")
                                telegram_video(graham_chat_id,submission.id,submission.title)

            # Find alternate angles
            with open("logs/goalsfromrsoccer/submissionsUsed.txt", "r") as f:
                submissions_used = f.read()
                submissions_used = submissions_used.split("\n")
                submissions_used = (list(filter(None, submissions_used)))[-5:]

            with open("logs/goalsfromrsoccer/alternatesUsed.txt", "r") as f:
                alternates_used = f.read()
                alternates_used = alternates_used.split("\n")
                alternates_used = list(filter(None, alternates_used))

            for i in submissions_used:
                submission = r.submission(id=i)      
                submission.comments.replace_more(limit=None)
                for top_level_comment in submission.comments:
                    if top_level_comment.stickied:
                        for second_level_comment in top_level_comment.replies:
                            if "http" in second_level_comment.body and second_level_comment.id not in alternates_used:
                                # Post AA to match thread
                                for top_level_comment in matchThread.comments:
                                    if submission.id in top_level_comment.body:
                                        print(f"({second_level_comment.id} -> {submission.id}) Adding AA to {submission.title}({top_level_comment.id}")
                                        top_level_comment.reply(f"{second_level_comment.body} | {str(second_level_comment.author)} | [discuss]({second_level_comment.permalink})")

                                        # Mark AA as used
                                        alternates_used.append(second_level_comment.id)

                                        # Write our updated list back to the file
                                        with open("logs/goalsfromrsoccer/alternatesUsed.txt", "w") as f:
                                            for i in alternates_used:
                                                f.write(i + "\n")

                                # Find unique AAs that aren't just mirrors and send videos via Telegram
                                if any(i in second_level_comment.body for i in ["AA","lternate","ngle","ommenta"]):
                                    altAngles = re.findall('(?<=)http.+?(?=[)\'\" ])', second_level_comment.body)
                                    for i in altAngles:
                                        print(f"\n({second_level_comment.id}) Downloading AA: {i} for {submission.title}")
                                        try:
                                            # Download video
                                            ytdownload(second_level_comment.id,i)
                                            pass
                                        #TODO: this is bogus. Need to catch the right error
                                        except urllib3.exceptions.HTTPError as http_error:
                                            print(http_error)
                                            continue

                                        try:
                                            # Send to GJustJuve group
                                            # print(f"\n({second_level_comment.id}) GJustJuve: sending AA: {i}")
                                            # telegram_video(gjustjuve_chat_id,second_level_comment.id,f"Replay of {submission.title}")
                                            # pass

                                            # Send to Graham
                                            print(f"\n({second_level_comment.id}) Graham: sending AA: {i}")
                                            telegram_video(graham_chat_id,second_level_comment.id,f"Replay of {submission.title}")
                                            pass

                                        #TODO: this is bogus. Need to catch the right error
                                        except urllib3.exceptions.TimeoutError as timeout_error:
                                            print(timeout_error)
                                            continue

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
