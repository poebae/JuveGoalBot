import praw
import prawcore
import re
import time
from datetime import datetime, timedelta

#TODO: ? Separate out finding mirrors manually based on goal.id ?
#TODO: get fixture dates and times from subreddit.wiki[“trezebot/fixtures”].content_md will give you the text
#TODO: sent me a message when the bot fires up
#TODO: rehost on imgur

def login():
    r = praw.Reddit('juvegoalbot')
    return r

def main():
    end_time = datetime.now() + timedelta(hours=3)
    r = login()
    goalSummary = ""
    searchTerms = ("Juventus", "Juve", "Szczesny", "De Sciglio", "Chiellini", "De Ligt", "Arthur Melo", "Khedira", "Ronaldo",\
        "Ramsey", "Dybala", "Douglas Costa", "Alex Sandro", "Danilo", "McKennie", "Cuadrado", "Bonucci", "Rugani", "Rabiot",\
        "Demiral", "Bentancur", "Pinsoglio", "Bernardeschi", "Kulusevski", "Buffon")

    with open("logs/submissionsChecked.txt", "r") as f:
        submissions_used = f.read()
        submissions_used = submissions_used.split("\n")
        submissions_used = list(filter(None, submissions_used))

    with open("logs/alternateAngles.txt", "r") as f:
        alternate_used = f.read()
        alternate_used = alternate_used.split("\n")
        alternate_used = list(filter(None, alternate_used))

    while datetime.now() < end_time:
        try:
            # SEARCH THROUGH SUBMISSIONS ON /r/juve
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
            for submission in r.subreddit('soccer').stream.submissions(pause_after=-1):
                if submission is None:
                    break

                for i in searchTerms:
                # Search for submissions containing search terms and flaired as Media or Mirror
                    if re.search(i, submission.title, re.IGNORECASE) and (submission.link_flair_text == "Media" or submission.link_flair_text == "Mirror"):
                        if submission.id not in submissions_used:
                            # Post goals to the match thread
                            print("Posting " + submission.title + " to " + matchThread.title + " (" + submission.id + ")")
                            matchThread.reply("[" + submission.title + "](" + submission.url + ") | " + str(submission.author) + " | [discuss](" + submission.permalink + ")\n\n")

                            # Mark submission as used
                            submissions_used.append(submission.id)
                            # Write our updated list back to the file
                            with open("logs/submissionsChecked.txt", "w") as f:
                                for i in submissions_used:
                                        f.write(i + "\n")

                        # Find alternate angles
                        for top_level_comment in submission.comments:
                            submission.comments.replace_more(limit=None)
                            if top_level_comment.stickied:
                                for second_level_comment in top_level_comment.replies:
                                    if "http" in second_level_comment.body and second_level_comment.id not in alternate_used:
                                        # Post AA to match thread
                                        for top_level_comment in matchThread.comments:
                                            if submission.id in top_level_comment.body:
                                                print("Adding " + second_level_comment.id + " to " + submission.title + " (" + submission.id + ")")
                                                top_level_comment.reply(second_level_comment.body + " | " + str(second_level_comment.author) + " | [discuss](" + second_level_comment.permalink + ")")

                                                # Mark AA as used
                                                alternate_used.append(second_level_comment.id)

                                                # Write our updated list back to the file
                                                with open("logs/alternateAngles.txt", "w") as f:
                                                    for i in alternate_used:
                                                        f.write(i + "\n")

            # # POST GOAL SUMMARY IN POST-MATCH THREAD #
            # with open("logs/postMatchThreads.txt", "r") as f:
            #     comments_replied_to = f.read()
            #     comments_replied_to = comments_replied_to.split("\n")
            #     comments_replied_to = list(filter(None, comments_replied_to))
            # for top_level_comment in postMatchThread.comments:
            #     # If we find a stickied comment that contains the keywords:
            #     if top_level_comment.stickied and ("highlights" in top_level_comment.body
            #                                     or "to this comment" in top_level_comment.body):
            #         # If comment hasn't been replied to
            #         if top_level_comment.id not in comments_replied_to and goalSummary != "":
            #             print("Posting goal summary to " + postMatchThread.title + " (" + top_level_comment.id + "):\n")

            #             # Submit the goal summary
            #             top_level_comment.reply(goalSummary)

            #             # Add comment id to list
            #             comments_replied_to.append(top_level_comment.id)

            #             # Write our updated list back to the file
            #             with open("logs/postMatchThreads.txt", "w") as f:
            #                 for top_level_comment.id in comments_replied_to:
            #                     f.write(top_level_comment.id + "\n")

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
