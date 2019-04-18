# Used for local testing of Juve goal bot
# Author: /u/droidonomy

import psycopg2
import unidecode
import credentials


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

            # Query specifically for assister and scorer
            sqlquery = '''SELECT date, opposition, result, competition, season, scorer, assist, url FROM juve_goals WHERE assist = %s AND scorer = %s; '''
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

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()
    print("Connected!\n")

    # Execute query to db for data
    cursor.execute(sqlquery, params)
    reply = ''

    if cursor:
        # For each record that comes back, loop through and build the reply
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
            reply += '\n'
            reply = reply.replace("Ucl", "UCL")
            reply = reply.replace("Icc", "ICC")
            reply = reply.replace("Spal", "SPAL")

        return reply


def main():
    # Get keyboard input
    body = input("Enter query: ")

    # Pull in gifs of goals
    if "!goal" in body:

        body = body.lower()
        query = parse_body_goal(body)
        sql = get_goal_items(query)

        # If query is invalid
        if sql is None:
            reply = 'It looks like your request is in a format I do not understand. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
            print(reply)

        # If query is valid
        else:
            print("SQL: ", sql)
            sqlThing = sql[0]
            sqlParams = sql[1]
            reply = get_urls(sqlThing, sqlParams)

            # Create and send the reply
            if reply:
                print(reply)

            # Query returned no results
            else:
                reply = 'Clip not found. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
                print(reply)

    # Pull in gifs of assists
    if "!assist" in body:

        body = body.lower()
        query = parse_body_assist(body)
        sql = get_assist_items(query)

        # Query not in correct format
        if sql is None:
            reply = 'It looks like your request is in a format I do not understand. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
            print(reply)

        # If query is valid
        else:
            print("SQL: ", sql)
            sqlThing = sql[0]
            sqlParams = sql[1]
            reply = get_urls(sqlThing, sqlParams)

            # Create and send the reply
            if reply:
                print(reply)

            # Query returned no results
            else:
                reply = 'Clip not found. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
                print(reply)

    # Pull in gifs of all goals against specific team
    if "!team" in body:

        body = body.lower()
        query = parse_body_team(body)
        sql = get_team_items(query)

        # Query not in correct format
        if sql is None:
            reply = 'It looks like your request is in a format I do not understand. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
            print(reply)

        # If query is valid
        else:
            print("SQL: ", sql)
            sqlThing = sql[0]
            sqlParams = sql[1]
            reply = get_urls(sqlThing, sqlParams)

            # Create and send the reply
            if reply:
                print(reply)

            # if query returned no results
            else:
                reply = 'Clip not found. [Check out this thread for the correct format](https://www.reddit.com/r/Juve/comments/9quyaa/i_created_a_bot_to_show_juve_goals_on_demand/)'
                print(reply)

if __name__ == '__main__':
    main()
