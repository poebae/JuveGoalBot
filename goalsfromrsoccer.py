import praw
import prawcore
import re
import time
from datetime import datetime, timedelta

#TODO: get fixture dates and times from subreddit.wiki[“trezebot/fixtures”].content_md will give you the text

def login():
    r = praw.Reddit('juvegoalbot')
    return r

def main():
    end_time = datetime.now() + timedelta(hours=3)
    r = login()
    message = ""
    submissions_checked = []

    while datetime.now() < end_time:
        try:

            # Search through submissions
            for submission in r.subreddit('juve_goal_bot+soccer').stream.submissions(pause_after=-1):
                if submission is None:
                    break

                # Search for submissions containing Juventus and flaired as Media or Mirror
                if re.match("Juventus", submission.title, re.IGNORECASE) and (submission.link_flair_text == "Media" or submission.link_flair_text == "Mirror"):
                    with open("logs/submissionsChecked.txt", "r") as f:
                        submissions_checked = f.read()
                        submissions_checked = submissions_checked.split("\n")
                        submissions_checked = list(filter(None, submissions_checked))

                    # If submission hasn't been replied to
                    if submission.id not in submissions_checked:
                        print(submission.title)
                        message += "[" + submission.title + "](" + submission.url + ")" + " - " + "[" + str(submission.author) + "](" + submission.permalink + ")" + '\n\n'

                        # Add submission id to list
                        submissions_checked.append(submission.id)

                        # Write our updated list back to the file
                        with open("logs/submissionsChecked.txt", "w") as f:
                            for submission.id in submissions_checked:
                                f.write(submission.id + "\n")

            # Search through comments
            for top_level_comment in r.subreddit('juve_goal_bot').stream.comments(pause_after=-1):
                if top_level_comment is None:
                    break

                # If we find a stickied comment that contains the keywords:
                if top_level_comment.stickied and ("highlights" in top_level_comment.body
                                                   or "to this comment" in top_level_comment.body):

                    with open("logs/postMatchThreads.txt", "r") as f:
                        comments_replied_to = f.read()
                        comments_replied_to = comments_replied_to.split("\n")
                        comments_replied_to = list(filter(None, comments_replied_to))

                    # If comment hasn't been replied to
                    if top_level_comment.id not in comments_replied_to and message != "":
                        print("Replying to comment " + top_level_comment.id + ':\n\n' + message)
                        top_level_comment.reply(message)

                        # Add comment id to list
                        comments_replied_to.append(top_level_comment.id)

                        # Write our updated list back to the file
                        with open("logs/postMatchThreads.txt", "w") as f:
                            for top_level_comment.id in comments_replied_to:
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
