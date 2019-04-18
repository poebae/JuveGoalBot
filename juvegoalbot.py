# !/usr/bin/env python
# coding=utf-8

# Bot to serve Juventus goals to /r/juve
# Author: /u/droidonomy

import praw
import prawcore
import psycopg2
import time
import unidecode
import re
import os
import credentials


def login():
    r = praw.Reddit('juvegoalbot')
    return r

FOOTER = '''___\n\n
^^[Wiki](https://www.reddit.com/r/juve_goal_bot/wiki/index)
^^| ^^[Data](https://www.reddit.com/r/juve_goal_bot/wiki/dataset)
^^| ^^[Usage](https://www.reddit.com/r/juve_goal_bot/wiki/usage)
^^| ^^[Creator](/u/droidonomy)'''


def parse_body_goal(body):
    # Find comments that start with the keyword and index the characters
    start_index = body.find('!goal ')
    # Remove first 5 characters to pull request
    body = body[start_index + 5:]
    # End indexing at a new line
    end_index = body.find('\n')

    print('user query: {}'.format(body))
    # Split the query into different sections at each comma
    query = body.split(',')
    return query


def parse_body_assist(body):
    # Find comments that start with the keyword and index the characters
    start_index = body.find('!assist ')
    # Remove first 8 characters to pull request
    body = body[start_index + 8:]
    # End indexing at a new line
    end_index = body.find('\n')

    print('user query: {}'.format(body))
    # Split the query into different sections at each comma
    query = body.split(',')

    return query


def parse_body_team(body):
    # Find comments that start with the keyword and index the characters
    start_index = body.find('!team ')
    # Remove first 5 characters to pull request
    body = body[start_index + 5:]
    # End indexing at a new line
    end_index = body.find('\n')

    print('user query: {}'.format(body))
    # Split the query into different sections at each comma
    query = body.split(',')

    return query


def parse_thread_title(title):
    # Find thread titles that contain the keyword
    start_index = title.find('Juventus vs ')
    # Remove first 11 characters to pull request
    title = title[start_index + 13:]
    query = title.split(',')
    print(query)
    return query


def get_goal_items(query):
    # Create an empty array for params to be added to
    params = []
    # Designate variable for first portion of the query
    player_name = query[0].strip()
    # Remove special characters
    player_name_string = unidecode.unidecode(player_name)
    # Add player_name to params array
    params.append(player_name_string)

    # If only the scorer name is given
    if len(query) == 1:
        sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE scorer = %s; '''
        return sqlquery, params

    # If query is longer than one section..
    elif 0 <= 1 < len(query):

        # Create a variable for the second portion of the query
        second_query = query[1].strip()

        # Search to see if the second portion is a competion specific query
        if second_query == "icc" or        \
           second_query == "serie a" or    \
           second_query == "serie b" or    \
           second_query == "allstars" or   \
           second_query == "ucl" or        \
           second_query == "coppa" or      \
           second_query == "friendly" or   \
           second_query == "supercoppa" or \
           second_query == "europa":

            # Add second portion to the params
            params.append(second_query)

            if 0 <= 2 < len(query):
                third_query = query[2].strip()
                params.append(third_query)
                sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE scorer = %s AND competition = %s AND season = %s; '''
                return sqlquery, params

            # Build a query specific to search for player and competion
            sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE scorer = %s AND competition = %s; '''
            print("Searching by competition")
            return sqlquery, params

        elif second_query[0].isdigit():
            params.append(second_query)
            sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE scorer = %s AND season = %s; '''
            return sqlquery, params

        elif second_query is None:
            # TODO handle this better....
            print('No second query item')
            return("no item")

        # If the second query does not state a competition
        else:
            # add second query to params
            params.append(second_query)
            if 0 <= 2 < len(query):
                third_query = query[2].strip()
                params.append(third_query)
                sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE scorer = %s AND opposition = %s AND season = %s; '''
                return sqlquery, params

            # Query specifically for player and opposition
            sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE scorer = %s AND opposition = %s; '''
            print("No league specified")
            return sqlquery, params


def get_assist_items(query):
    # Create an empty array for params to be added to
    params = []
    # Designate variable for first portion of the query
    player_name = query[0].strip()
    # Remove special characters
    player_name_string = unidecode.unidecode(player_name)
    # Add player_name to params array
    params.append(player_name_string)

    # If only the assister name is given
    if len(query) == 1:
        sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE assist = %s; '''
        return sqlquery, params

    # If query is longer than one section..
    elif 0 <= 1 < len(query):

        # Create a variable for the second portion of the query
        second_query = query[1].strip()

        # If queries > 1 and second is a competition
        if second_query == "icc" or        \
           second_query == "serie a" or    \
           second_query == "serie b" or    \
           second_query == "allstars" or   \
           second_query == "ucl" or        \
           second_query == "coppa" or      \
           second_query == "friendly" or   \
           second_query == "supercoppa" or \
           second_query == "europa":

            # Add second portion to the params
            params.append(second_query)

            # If there's a third query
            if 0 <= 2 < len(query):
                third_query = query[2].strip()

                # If query 3 is a season
                if third_query[0].isdigit():
                    params.append(third_query)
                    sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE assist = %s AND competition = %s AND season = %s; '''
                    return sqlquery, params

            # Build a query specific to search for player and competion
            sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE assist = %s AND competition = %s; '''
            print("Searching by competition")
            return sqlquery, params

        # If 2 queries and query 2 is a season
        elif second_query[0].isdigit():
            params.append(second_query)
            sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE assist = %s AND season = %s; '''
            return sqlquery, params

        # If 2 queries and query 2 is not a competition
        else:

            # add second query to params
            params.append(second_query)

            # If queries > 2
            if 0 <= 2 < len(query):
                third_query = query[2].strip()

                # If query 3 is a season
                if third_query[0].isdigit():
                    params.append(third_query)
                    sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE assist = %s AND opposition = %s AND season = %s; '''
                    return sqlquery, params

            # Query specifically for player and opposition
            # sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE assist = %s AND opposition = %s; '''
            # print("No league specified")
            # return sqlquery, params

            # Query specifically for assister and scorer
            sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE assist = %s AND scorer = %s; '''
            # print("Assister and scorer query")
            return sqlquery, params


def get_team_items(query):
    # Create an empty array for params to be added to
    params = []
    # Designate variable for first portion of the query
    team_name = query[0].strip()
    # Remove special characters
    team_name_string = unidecode.unidecode(team_name)
    # Add team_name to params array
    params.append(team_name_string)

    # If query is longer than one section..
    if 0 <= 1 < len(query):

        # Create a variable for the second portion of the query
        second_query = query[1].strip()

        # If the second query is a season number
        if second_query[0].isdigit():
            params.append(second_query)
            sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE opposition = %s AND season = %s; '''
            return sqlquery, params

        # Otherwise just show all goals against specified team
        else:
            sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE opposition = %s; '''
            return sqlquery, params

    else:
        sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE opposition = %s; '''
        return sqlquery, params


def get_urls(sqlquery, params):
    # Define our connection string
    conn_string = credentials.login

    # print the connection string we will use to connect
    # print("Connecting to database\n	->%s" % (conn_string))

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    print("Connected!\n")

    cursor = conn.cursor()
    # Execute query to db for data
    cursor.execute(sqlquery, params)
    reply = ''

    if cursor:
        # For each record that comes back, loop through and build the reply
        # record[5] = scorer
        # record[2] = score
        # record[1] = opposition
        # record[6] = assist
        # record[4] = season
        # record[3] = competition
        # record[0] = date
        # record[7] = url

        for record in cursor:
            scorer = record[5].rstrip()
            score = record[2].rstrip()
            opposition = record[1].rstrip()
            assist = record[6].rstrip()
            season = record[4].rstrip()
            competition = record[3].rstrip()
            date = record[0].rstrip()
            url = record[7].rstrip()

            reply += f'[{scorer.title()} {score} vs {opposition.title()} (assist: {assist.title()}), {season} {competition.title()} - {date}](https://imgur.com/{url})'
            reply += '\n\n'
            reply = reply.replace("Ucl", "UCL")
            reply = reply.replace("Icc", "ICC")

        reply += FOOTER
        return reply


def main():
    # Authenticate the user
    r = login()
    while True:
        # When authenticated...run the bot
        try:
            # Get all comments from designated subreddits
            for comment in r.subreddit('juve+juve_goal_bot').stream.comments(pause_after=-1):
                if comment is None:
                    break

                body = comment.body

                # Pull in gifs of goals
                if "!goal" in body:
                    # print("!goal command executed")

                    # Store list of existing comments associated with goals
                    with open('logs/goalComments.txt', 'r') as outfile:
                        seen_comments = outfile.read().splitlines()
                    # print(comment.id)

                    # Check if comment already answered
                    if comment.id not in seen_comments:

                        body = comment.body.lower()
                        query = parse_body_goal(body)
                        sql = get_goal_items(query)

                        # If query is invalid
                        if sql is None:
                            reply = 'It looks like your request is in a format I do not understand. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
                            comment.reply(reply)
                            with open('logs/goalComments.txt', 'a+') as outfile:
                                outfile.write(comment.id + '\n')

                            print("not valid query..")
                            time.sleep(10)

                        # If query is valid
                        else:
                            print("SQL: ", sql)
                            sqlThing = sql[0]
                            sqlParams = sql[1]
                            reply = get_urls(sqlThing, sqlParams)

                            # Create and send the reply
                            if reply:
                                comment.reply(reply)
                                with open('logs/goalComments.txt', 'a+') as outfile:
                                    outfile.write(comment.id + '\n')

                                print("Sleep for 10...")
                                time.sleep(10)
                            # Query returned no results
                            else:
                                reply = 'Clip not found. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
                                comment.reply(reply)
                                with open('logs/goalComments.txt', 'a+') as outfile:
                                    outfile.write(comment.id + '\n')

                                print("Sleep for 10...")
                                time.sleep(10)
                    # else:
                    #     print('This clip has already been requested')

                # Pull in gifs of assists
                if "!assist" in body:
                    # print("!assist commmand executed")

                    # Store list of existing comments associated with assists
                    with open('logs/assistComments.txt', 'r') as outfile:
                        seen_comments = outfile.read().splitlines()
                    # print(comment.id)

                    # Check if comment already answered
                    if comment.id not in seen_comments:

                        body = comment.body.lower()
                        query = parse_body_assist(body)
                        sql = get_assist_items(query)

                        # Query not in correct format
                        if sql is None:
                            reply = 'It looks like your request is in a format I do not understand. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
                            comment.reply(reply)
                            with open('logs/assistComments.txt', 'a+') as outfile:
                                outfile.write(comment.id + '\n')

                            print("not valid query..")
                            time.sleep(10)

                        # If query is valid
                        else:
                            print("SQL: ", sql)
                            sqlThing = sql[0]
                            sqlParams = sql[1]
                            reply = get_urls(sqlThing, sqlParams)

                            # Create and send the reply
                            if reply:
                                comment.reply(reply)
                                with open('logs/assistComments.txt', 'a+') as outfile:
                                    outfile.write(comment.id + '\n')

                                print("Sleep for 10...")
                                time.sleep(10)

                            # Query returned no results
                            else:
                                reply = 'Clip not found. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
                                comment.reply(reply)
                                with open('logs/assistComments.txt', 'a+') as outfile:
                                    outfile.write(comment.id + '\n')

                                print("Sleep for 10...")
                                time.sleep(10)
                    # else:
                    #     print('This clip has already been requested')

                # Pull in gifs of all goals against specific team
                if "!team" in body:
                    # print("!team command executed")

                    # Store list of existing comments associated with team goals
                    with open('logs/teamComments.txt', 'r') as outfile:
                        seen_comments = outfile.read().splitlines()
                    # print(comment.id)

                    # See if the comment has not already been answered.
                    if comment.id not in seen_comments:

                        body = comment.body.lower()
                        query = parse_body_team(body)
                        sql = get_team_items(query)

                        # Query not in correct format
                        if sql is None:
                            reply = 'It looks like your request is in a format I do not understand. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
                            comment.reply(reply)
                            with open('logs/teamComments.txt', 'a+') as outfile:
                                outfile.write(comment.id + '\n')

                            print("not valid query..")
                            time.sleep(10)

                        # If query is valid
                        else:
                            print("SQL: ", sql)
                            sqlThing = sql[0]
                            sqlParams = sql[1]
                            reply = get_urls(sqlThing, sqlParams)

                            # Create and send the reply
                            if reply:
                                comment.reply(reply)
                                with open('logs/teamComments.txt', 'a+') as outfile:
                                    outfile.write(comment.id + '\n')

                                print("Sleep for 10...")
                                time.sleep(10)

                            # if query returned no results
                            else:
                                reply = 'Clip not found. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
                                comment.reply(reply)
                                with open('logs/teamComments.txt', 'a+') as outfile:
                                    outfile.write(comment.id + '\n')

                                print("Sleep for 10...")
                                time.sleep(10)
                    # else:
                    #     print('This clip has already been requested')

            # Get all new submissions from designated subreddit
            for submission in r.subreddit('juve_goal_bot').stream.submissions(pause_after=-1):
                if submission is None:
                    break

                with open("logs/matchThreadPosts.txt", "r") as f:
                    posts_replied_to = f.read()
                    posts_replied_to = posts_replied_to.split("\n")
                    posts_replied_to = list(filter(None, posts_replied_to))

                # If submission hasn't been replied to
                if submission.id not in posts_replied_to:

                    if re.search("Juventus vs", submission.title, re.IGNORECASE):
                        # Reply to the post
                        print("Bot replying to : ", submission.title)

                        title = submission.title.lower()
                        query = parse_thread_title(title)
                        sql = get_team_items(query)

                        print("SQL: ", sql)
                        sqlThing = sql[0]
                        sqlParams = sql[1]
                        reply = get_urls(sqlThing, sqlParams)

                        # Create and send the reply
                        if reply:
                            submission.reply(reply)

                            with open('logs/matchThreadPosts.txt', 'a+') as outfile:
                                for post_id in posts_replied_to:
                                    outfile.write(post_id + '\n')

                            print("Sleep for 10...")
                            time.sleep(10)

                            # Add submission id to list
                            posts_replied_to.append(submission.id)

                            # Write our updated list back to the file
                            with open("logs/matchThreadPosts.txt", "w") as f:
                                for post_id in posts_replied_to:
                                    f.write(post_id + "\n")

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
