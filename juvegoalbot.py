# !/usr/bin/env python
# coding=utf-8

# import postgresConfig
import praw
import prawcore
import psycopg2
import time
import unidecode
import os
import config

def login():
    r = praw.Reddit('juvegoalbot')
    return r

FOOTER = '''___\n\n
^^[Wiki](https://www.reddit.com/r/juve_goal_bot/wiki/index)
^^| ^^[Feedback](/r/juve_goal_bot)
^^| ^^[Creator](/u/droidonomy)'''


def parse_body(body):
    # Find comments that start with the keyword and start indexing the characters
    start_index = body.find('!goal ')
    # Remove first 8 characters to pull request
    body = body[start_index + 5:]
    # End indexing at a new line
    end_index = body.find('\n')

    print('user query: {}'.format(body))
    # Split the query into different sections at each comma
    query = body.split(',')

    return query


def parse_body_assist(body):
    # Find comments that start with the keyword and start indexing the characters
    start_index = body.find('!assist ')
    # Remove first 8 characters to pull request
    body = body[start_index + 8:]
    # End indexing at a new line
    end_index = body.find('\n')

    print('user query: {}'.format(body))
    # Split the query into different sections at each comma
    query = body.split(',')

    return query


def get_sql_items(query):
    # Create an empty array for params to be added to
    params = []
    # Designate variable for first portion of the query
    player_name = query[0].strip()

    # Remove special characters
    player_name_string = unidecode.unidecode(player_name)
    # Add player_name to params array
    params.append(player_name_string)

    # If query is longer than one section..
    if 0 <= 1 < len(query):
        # Create a variable for the second portion of the query
        second_query = query[1].strip()
        # Search to see if the second portion is a competion specific query
        if second_query == "icc" or second_query == "serie a" or second_query == "allstars" or second_query == "ucl" or second_query == "coppa" or second_query == "friendly" or second_query == "supercoppa":

            # Add second portion to the params
            params.append(second_query)

            if 0 <= 2 < len(query):

                third_query = query[2].strip()
                params.append(third_query)
                sqlquery = '''SELECT opposition, competition, season, url FROM juve_goals WHERE scorer = %s AND competition = %s AND season = %s; '''
                return sqlquery, params

            # Build a query specific to search for player and competion
            sqlquery = '''SELECT opposition, competition, season, url FROM juve_goals WHERE scorer = %s AND competition = %s; '''
            print("Search via leagues")
            return sqlquery, params

        elif second_query is None:
            # TODO handle this better....
            print('No second query item')
            return("no item")

        elif second_query == "2018-19" or second_query == "2017-18":
            params.append(second_query)
            sqlquery = '''SELECT opposition, competition, season, url FROM juve_goals WHERE scorer = %s AND season = %s; '''
            return sqlquery, params

        # If the second section does not state a competition
        else:
            # add second section to params
            params.append(second_query)
            if 0 <= 2 < len(query):

                third_query = query[2].strip()
                params.append(third_query)
                sqlquery = '''SELECT opposition, competition, season, url FROM juve_goals WHERE scorer = %s AND opposition = %s AND season = %s; '''
                return sqlquery, params

            # Query specifically for player and opposition
            sqlquery = '''SELECT opposition, competition, season, url FROM juve_goals WHERE scorer = %s AND opposition = %s; '''
            print("No league specified")
            return sqlquery, params


def get_assist_items(query):
    # Create an empty array for params to be added to
    params = []
    # Designate variable for first portion of the query
    player_name = query[0].strip()
    # Add player_name to params array
    params.append(player_name)

    # If query is longer than one section..
    if 0 <= 1 < len(query):
        # Create a variable for the second portion of the query
        second_query = query[1].strip()
        # Search to see if the second portion is a competion specific query
        if second_query == "icc" or second_query == "serie a" or second_query == "allstars" or second_query == "ucl" or second_query == "coppa" or second_query == "friendly" or second_query == "supercoppa":

            # Add second portion to the params
            params.append(second_query)

            if 0 <= 2 < len(query):

                third_query = query[2].strip()
                params.append(third_query)
                sqlquery = '''SELECT opposition, competition, season, url FROM juve_goals WHERE assist = %s AND competition = %s AND season = %s; '''
                return sqlquery, params

            # Build a query specific to search for player and competion
            sqlquery = '''SELECT opposition, competition, season, url FROM juve_goals WHERE assist = %s AND competition = %s; '''
            print("Search via leagues")
            return sqlquery, params

        elif second_query == "2018-19" or second_query == "2017-18" or second_query == "2016-17" or second_query == "2015-16" or second_query == "2014-15" or second_query == "2013-14" or second_query == "2012-13" or second_query == "2011-12" or second_query == "2010-11" or second_query == "2009-10" or second_query == "2008-09" or second_query == "2007-08" or second_query == "2006-07" or second_query == "2005-06" or second_query == "2004-05" or second_query == "2003-04" or second_query == "2002-03" or second_query == "2001-02" or second_query == "2000-01":
            params.append(second_query)
            sqlquery = '''SELECT opposition, competition, season, url FROM juve_goals WHERE assist = %s AND season = %s; '''
            return sqlquery, params

        # If the second section does not state a competition
        else:
            # add second section to params
            params.append(second_query)
            if 0 <= 2 < len(query):

                third_query = query[2].strip()
                params.append(third_query)
                sqlquery = '''SELECT opposition, competition, season, url FROM juve_goals WHERE assist = %s AND opposition = %s AND season = %s; '''
                return sqlquery, params

            # Query specifically for player and opposition
            sqlquery = '''SELECT opposition, competition, season, url FROM juve_goals WHERE assist = %s AND opposition = %s; '''
            print("No league specified")
            return sqlquery, params


def get_urls(sqlquery, params):
    is_prod = os.environ.get('IS_HEROKU', None)

    print("is prod?? ", is_prod)

    if is_prod:
        # Define our connection string
        host = "localhost"
        dbname = "juve_bot"
        user = "graham"
        password = "moses40"
        conn_string = "host='localhost' dbname='juve_bot' user='graham' password ='moses40'"
        # print the connection string we will use to connect
        print("Connecting to database\n	->%s" % (conn_string))

        # get a connection, if a connect cannot be made an exception will be raised here
        conn = psycopg2.connect(conn_string)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cursor = conn.cursor()
        print("Connected!\n")

    else:
        # Define our connection string
        # conn_string = "host='{}' dbname='{}' user='{}' password='{}'".format(host,dbname,user,password)
        # Define our connection string
        host = "localhost"
        dbname = "juve_bot"
        user = "graham"
        password = "moses40"
        conn_string = "host='localhost' dbname='juve_bot' user='graham' password ='moses40'"

        # print the connection string we will use to connect
        print("Connecting to database\n	->%s" % (conn_string))

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
        for record in cursor:
            reply += '[{}: {} ({})](https://imgur.com/{})'.format(record[0], record[1], record[2], record[3])
            reply += '\n\n'

        reply += FOOTER
        return reply


def run(r):
    # Get all comments from designated subreddits
    for comment in r.subreddit('juve+juve_goal_bot').stream.comments():
        body = comment.body
        # listen for any comments that contain the keyword
        if "!goal" in body:
            with open('goalComments.txt', 'r') as outfile:
                seen_comments = outfile.read().splitlines()
            print(comment.id)
            # See if the comment in the subreddit has not already been answered.
            if comment.id not in seen_comments:

                body = comment.body.lower()
                query = parse_body(body)
                sql = get_sql_items(query)
                # If a query the individual tried to use is not in the correct format
                # mark it as helped and let the individual know where to get help.
                if sql is None:
                    reply = 'It looks like your request is in a format I do not understand.  Feel free to [post a question in the help thread.](https://www.reddit.com/r/juve_goal_bot/comments/9qpxjh/juve_goal_bot_questionsbug_reports)'
                    comment.reply(reply)
                    with open('goalComments.txt', 'a+') as outfile:
                        outfile.write(comment.id + '\n')

                    print("not valid query..")
                    time.sleep(10)
                # If the comment uses the correct format find the results
                else:
                    print("SQL: ", sql)
                    sqlThing = sql[0]
                    sqlParams = sql[1]
                    reply = get_urls(sqlThing, sqlParams)

                    # Create and send the reply
                    if reply:
                        comment.reply(reply)
                        with open('goalComments.txt', 'a+') as outfile:
                            outfile.write(comment.id + '\n')

                        print("Sleep for 10...")
                        time.sleep(10)
                    # If the reply comes back with no results. Let individual know
                    else:
                        reply = 'Clip not found. Only 2018/19 clips are currently available. Feel free to [post a question in the help thread.](https://www.reddit.com/r/juve_goal_bot/comments/9qpxjh/juve_goal_bot_questionsbug_reports)'
                        comment.reply(reply)
                        with open('goalComments.txt', 'a+') as outfile:
                            outfile.write(comment.id + '\n')

                        print("Sleep for 10...")
                        time.sleep(10)
            else:
                # print out when comment was already addressed
                print('This clip has already been requested')

        # Pull in Gifs of Assists
        if "!assist" in body:
            print("Juventus assist command")
            # store list of existing comments associated with assists
            with open('assistComments.txt', 'r') as outfile:
                seen_comments = outfile.read().splitlines()
            print(comment.id)
            # See if the comment in the subreddit has not already been answered.
            if comment.id not in seen_comments:

                body = comment.body.lower()
                query = parse_body_assist(body)
                sql = get_assist_items(query)
                # If a query the individual tried to use is not in the correct format
                # mark it as helped and let the individual know where to get help.
                if sql is None:
                    reply = 'It looks like your request is in a format I do not understand.  Feel free to [post a question in the help thread.](https://www.reddit.com/r/juve_goal_bot/comments/9qpxjh/juve_goal_bot_questionsbug_reports)'
                    comment.reply(reply)
                    with open('assistComments.txt', 'a+') as outfile:
                        outfile.write(comment.id + '\n')

                    print("not valid query..")
                    time.sleep(10)
                # If the comment uses the correct format find the results
                else:
                    print("SQL: ", sql)
                    sqlThing = sql[0]
                    sqlParams = sql[1]
                    reply = get_urls(sqlThing, sqlParams)

                    # Create and send the reply
                    if reply:
                        comment.reply(reply)
                        with open('assistComments.txt', 'a+') as outfile:
                            outfile.write(comment.id + '\n')

                        print("Sleep for 10...")
                        time.sleep(10)
                    # If the reply comes back with no results. Let individual know
                    else:
                        reply = 'Clip not found. Only 2018/19 clips are currently available. Feel free to [post a question in the help thread.](https://www.reddit.com/r/juve_goal_bot/comments/9qpxjh/juve_goal_bot_questionsbug_reports)'
                        comment.reply(reply)
                        with open('assistComments.txt', 'a+') as outfile:
                            outfile.write(comment.id + '\n')

                        print("Sleep for 10...")
                        time.sleep(10)
            else:
                # print out when comment was already addressed
                print('This clip has already been requested')
                # print("Sleep for 10...")
                # time.sleep(10)


def main():
    # Authenticate the user
    r = login()
    while True:
        # When authenticated...run the bot
        try:
            run(r)
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
