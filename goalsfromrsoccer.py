import praw
import prawcore
import re
import time
from datetime import datetime, timedelta

#TODO: post alternate angles to post-match thread
#TODO: get fixture dates and times from subreddit.wiki[“trezebot/fixtures”].content_md will give you the text
#TODO: rehost on imgur

def login():
    r = praw.Reddit('juvegoalbot')
    return r

def main():
    end_time = datetime.now() + timedelta(hours=3)
    r = login()
    message = ""
    newSubmission = ""
    goalName = ""
    submissions_checked = []

    while datetime.now() < end_time:
        try:

            # Search through submissions
            for submission in r.subreddit('juve_goal_bot+soccer').stream.submissions(pause_after=-1):
                if submission is None:
                    break

                # Search for submissions containing Juventus and flaired as Media or Mirror
                if re.search(".*Juventus.*", submission.title, re.IGNORECASE) and (submission.link_flair_text == "Media" or submission.link_flair_text == "Mirror"):
                    with open("logs/submissionsChecked.txt", "r") as f:
                        submissions_checked = f.read()
                        submissions_checked = submissions_checked.split("\n")
                        submissions_checked = list(filter(None, submissions_checked))

                    # If submission hasn't been replied to
                    if submission.id not in submissions_checked:
                        print("Found: " + submission.title + '\n')
                        newGoal = "[" + submission.title + "](" + submission.url + ") | " + str(submission.author) + " | [discuss](" + submission.permalink + ")" + '\n\n'
                        goalName = submission.title

                        # Append the new goal to the summary that's being prepared for the post-match thread
                        message += newGoal

                        # Add submission id to list
                        submissions_checked.append(submission.id)

                        # Write our updated list back to the file
                        with open("logs/submissionsChecked.txt", "w") as f:
                            for submission.id in submissions_checked:
                                f.write(submission.id + "\n")

                        # If there's an ongoing match thread, post the goal to it immediately
                        for submission in r.subreddit('juve_goal_bot+juve').search("Match Thread",time_filter='day'):
                            print("Posting to thread: " + submission.title + ':\n' + newGoal)
                            submission.reply(newGoal)

                    # Search for alternate angles
                    for top_level_comment in submission.comments:
                        submission.comments.replace_more(limit=None)
                        for second_level_comment in top_level_comment.replies:

                            with open("logs/alternateAngles.txt", "r") as f:
                                alternate_checked = f.read()
                                alternate_checked = alternate_checked.split("\n")
                                alternate_checked = list(filter(None, alternate_checked))

                            # If alternate angle hasn't already been used
                            if second_level_comment.id not in alternate_checked and "http" in second_level_comment.body:
                                print("Found Alternate Angle: " + second_level_comment.body + '\n')
                                alternateAngle = second_level_comment.body + " | " + str(second_level_comment.author) + " | [discuss](" + second_level_comment.permalink + ")" + '\n\n'
                                print(alternateAngle)

                                # Add submission id to list
                                alternate_checked.append(second_level_comment.id)

                                # Write our updated list back to the file
                                with open("logs/alternateAngles.txt", "w") as f:
                                    for second_level_comment.id in alternate_checked:
                                        f.write(second_level_comment.id + "\n")

                                # If there's an ongoing match thread
                                for submission in r.subreddit('juve_goal_bot+juve').search("Match Thread",time_filter='day'):
                                    if submission.link_flair_text == "Match Thread":
                                        for top_level_comment in submission.comments:
                                            # If the title of the goal matches a link posted by the bot
                                            if top_level_comment.author == 'JuveGoalBot' and goalName in top_level_comment.body:
                                                # Reply with the alternate angle
                                                print("Replying to comment: " + top_level_comment.body + ':\n' + alternateAngle + '\n')
                                                top_level_comment.reply(alternateAngle)

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
                        print("Replying to comment " + top_level_comment.id + ':\n' + message)
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
