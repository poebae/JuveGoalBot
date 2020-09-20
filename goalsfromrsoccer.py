import praw
import prawcore
import re
import time
from datetime import datetime, timedelta

#TODO: get fixture dates and times from subreddit.wiki[“trezebot/fixtures”].content_md will give you the text
#TODO: rehost on imgur

def login():
    r = praw.Reddit('juvegoalbot')
    return r

def main():
    end_time = datetime.now() + timedelta(hours=3)
    r = login()
    goalSummary = ""
    submissions_used = []
    goalPosts = []
    alternatePosts = []
    matchThreadID = ""
    postMatchThreadID = ""

    while datetime.now() < end_time:
        try:

            # Search through submissions on /r/juve
            for submission in r.subreddit('juve_goal_bot').stream.submissions(pause_after=-1):
            # for submission in r.subreddit('juve_goal_bot').stream.submissions(skip_existing=True, pause_after=-1):
                if submission is None:
                    break

                # Find the ID of the Match Thread
                if submission.link_flair_text == "Match Thread":
                    matchThreadID = submission.id

                # Find the ID of the Post-Match Thread
                if submission.link_flair_text == "Post-Match Thread":
                    postMatchThreadID = submission.id


            # GATHER GOAL SUBMISSIONS #
            # for submission in r.subreddit('soccer').stream.submissions(skip_existing=True, pause_after=-1):
            for submission in r.subreddit('soccer').stream.submissions(pause_after=-1):
                if submission is None:
                    break

                # Search for submissions containing Juventus and flaired as Media or Mirror
                if re.search("Tottenham", submission.title, re.IGNORECASE) and (submission.link_flair_text == "Media" or submission.link_flair_text == "Mirror"):
                
                    with open("logs/submissionsChecked.txt", "r") as f:
                        submissions_used = f.read()
                        submissions_used = submissions_used.split("\n")
                        submissions_used = list(filter(None, submissions_used))
                    
                    # Add to list of submissions
                    if submission.id not in submissions_used:
                        print("Found: " +submission.title + " (" + submission.id + ")")
                        goalPosts.append(str(submission))

            # POST GOALS TO MATCH THREAD #
            for i in goalPosts:
                goalID = r.submission(id=i)
                # If there's a match thread
                if matchThreadID != "":
                    replyTarget = r.submission(id=matchThreadID)
                    # If goal hasn't been used
                    if goalID.id not in submissions_used:
                        newGoal = "[" + goalID.title + "](" + goalID.url + ") | " + str(goalID.author) + " | [discuss](" + goalID.permalink + ")" + '\n\n'
                        # Post goals to the match thread
                        print("Posting to " + replyTarget.title + " - " + goalID.title)
                        replyTarget.reply(newGoal)

                        # Add submission id to list of used submissions
                        submissions_used.append(i)

                        # Write our updated list back to the file
                        with open("logs/submissionsChecked.txt", "w") as f:
                            for i in submissions_used:
                                f.write(i + "\n")

                # COLLECT ALTERNATE ANGLES #
                with open("logs/alternateAngles.txt", "r") as f:
                    alternate_used = f.read()
                    alternate_used = alternate_used.split("\n")
                    alternate_used = list(filter(None, alternate_used))
                for top_level_comment in goalID.comments:
                    goalID.comments.replace_more(limit=None)
                    if top_level_comment.stickied:
                        for second_level_comment in top_level_comment.replies:
                            # Add to list of alternate angles
                            if "http" in second_level_comment.body and second_level_comment.id not in alternate_used:
                                parentgoal = goalID.id
                                alternatePosts.append(second_level_comment.id)

                # POST ALTERNATE ANGLES #
                for i in alternatePosts:
                    if i not in alternate_used:
                        # For the match thread
                        if matchThreadID != "":
                            replyTarget = r.submission(id=matchThreadID)
                            for top_level_comment in replyTarget.comments:
                                # If the title of the goal matches a link posted by the bot
                                if top_level_comment.author == 'JuveGoalBot' and goalID.title in top_level_comment.body and second_level_comment.id not in alternate_used:
                                    alternateAngle = second_level_comment.body + " | " + str(second_level_comment.author) + " | [discuss](" + second_level_comment.permalink + ")" + '\n\n'
                                    # Reply with the alternate angle
                                    print("Adding AA to " + goalID.title + " (" + second_level_comment.id + ")")
                                    top_level_comment.reply(alternateAngle)
                                    # Add alternate angle to post-match summary
                                    goalSummary += "\n\n* [" + goalID.title + "](" + goalID.url + ") | " + str(goalID.author) + " | [discuss](" + goalID.permalink + ")" + '\n\n'
                                    goalSummary += " * "+ alternateAngle

                                    # Add submission id to list
                                    alternate_used.append(second_level_comment.id)

                                    # Write our updated list back to the file
                                    with open("logs/alternateAngles.txt", "w") as f:
                                        for second_level_comment.id in alternate_used:
                                            f.write(second_level_comment.id + "\n")

            # POST GOAL SUMMARY IN POST-MATCH THREAD #

            if postMatchThreadID != "":
                with open("logs/postMatchThreads.txt", "r") as f:
                    comments_replied_to = f.read()
                    comments_replied_to = comments_replied_to.split("\n")
                    comments_replied_to = list(filter(None, comments_replied_to))
                    replyTarget = r.submission(id=postMatchThreadID)
                for top_level_comment in replyTarget.comments:
                    # If we find a stickied comment that contains the keywords:
                    if top_level_comment.stickied and ("highlights" in top_level_comment.body
                                                    or "to this comment" in top_level_comment.body):
                        # If comment hasn't been replied to
                        if top_level_comment.id not in comments_replied_to and goalSummary != "":
                            print("Posting goal summary to " + replyTarget.title + " (" + top_level_comment.id + "):\n")

                            # Submit the goal summary
                            top_level_comment.reply(goalSummary)

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
