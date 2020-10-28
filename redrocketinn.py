import praw
import prawcore
import time

def login():
    r = praw.Reddit('juvegoalbot')
    return r

def main():
    allLinks = ""
    r = login()
    while True:
        try:

            sticky1 = r.subreddit("hadtobeNZ").sticky(1)
            sticky2 = r.subreddit("TestSubForhadtobeNZ").sticky(2)

            if sticky1.author == "redrocketinn":
                for top_level_comment in sticky1.comments:
                    linkSubmissions = re.findall('(?<=)http.+?(?=[)\'\" ])', top_level_comment.body)
                    allLinks += linkSubmissions

                    print(top_level_comment.body)
                    print(allLinks)

            # for top_level_comment in sticky1:
            #     print(top_level_comment.body)

            # for top_level_comment in sticky2:
            #     print(top_level_comment.body)

        except prawcore.exceptions.ServerError as http_error:
            print(http_error)
            print('waiting 5 seconds')
            time.sleep(5)
        except prawcore.exceptions.ResponseException as response_error:
            print(response_error)
            print('waiting 5 seconds')
            time.sleep(5)
        except prawcore.exceptions.RequestException as request_error:
            print(request_error)
            print('waiting 5 seconds')
            time.sleep(5)
        except Exception as e:
            print('error: {}'.format(e))
            print('waiting 5 seconds')
            time.sleep(5)

if __name__ == '__main__':
    main()
