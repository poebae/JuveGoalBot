import praw
import prawcore
import re
import time
from datetime import datetime, timedelta

#TODO: ? Separate out finding mirrors manually based on goal.id ?
#TODO: get fixture dates and times from subreddit.wiki[“trezebot/fixtures”].content_md will give you the text
#TODO: sent me a message when the bot fires up and posts goals
#TODO: rehost on imgur

def login():
    r = praw.Reddit('juvegoalbot')
    return r

def main():
    end_time = datetime.now() + timedelta(hours=3)
    r = login()
    goalSummary = ""
    matchThread = ""
    postMatchThread = ""
    searchTerms = ("Juventus", "Juve", "Szczesny", "De Sciglio", "Chiellini", "De Ligt", "Arthur Melo", "Khedira", "Cristiano",\
        "Ronaldo", "Ramsey", "Dybala", "Douglas Costa", "Alex Sandro", "Danilo", "McKennie", "Cuadrado", "Bonucci", "Rugani",\
        "Rabiot", "Demiral", "Bentancur", "Pinsoglio", "Bernardeschi", "Kulusevski", "Buffon", "Pirlo")

    with open("goalsfromrsoccer/logs/submissionsUsed.txt", "r") as f:
        submissions_used = f.read()
        submissions_used = submissions_used.split("\n")
        submissions_used = list(filter(None, submissions_used))

    with open("goalsfromrsoccer/logs/alternatesUsed.txt", "r") as f:
        alternates_used = f.read()
        alternates_used = alternates_used.split("\n")
        alternates_used = list(filter(None, alternates_used))

    with open("goalsfromrsoccer/logs/stickiesReplied.txt", "r") as f:
        stickies_replied = f.read()
        stickies_replied = stickies_replied.split("\n")
        stickies_replied = list(filter(None, stickies_replied))

    while datetime.now() < end_time:
        try:
            # Search through submissions on /r/juve
            # for submission in r.subreddit('juve').stream.submissions(skip_existing=True):
            for submission in r.subreddit('juve_goal_bot').stream.submissions(pause_after=-1):
                if submission is None:
                    break

                # Find the ID of the Match Thread
                if submission.link_flair_text == "Match Thread":
                   matchThread = r.submission(id=submission.id)

                # Find the ID of the Post-Match Thread
                if submission.link_flair_text == "Post-Match Thread":
                   postMatchThread = r.submission(id=submission.id)

            # Gather goal submissions #
            # for submission in r.subreddit('soccer').stream.submissions(skip_existing=True):
            for submission in r.subreddit('juve_goal_bot+soccer').stream.submissions(pause_after=-1):
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
                                matchThread.reply(newGoal)
                                goalSummary += newGoal

                                # Mark submission as used
                                submissions_used.append(submission.id)
                                # Write our updated list back to the file
                                with open("goalsfromrsoccer/logs/submissionsUsed.txt", "w") as f:
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
                                                    with open("goalsfromrsoccer/logs/alternatesUsed.txt", "w") as f:
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
                            with open("goalsfromrsoccer/logs/stickiesReplied.txt", "w") as f:
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
