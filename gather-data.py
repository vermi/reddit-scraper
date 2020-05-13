#!/Users/justin/.pyenv/shims/python
"""Reddit Data Gatherer:

This script allows the user to scrape up to 1024 posts, and associated comments, from
 the specified subreddit.

The 'praw' module and valid reddit API credentials are required for the script to
 function correctly.

The subreddit name is required; all other command-line arguments are optional.

A keyboard interrupt (Ctrl-C) can be used to stop the gathering process and immediately
 write any collected information to disk.
"""

import argparse
import configparser
import datetime as dt
import json
import os.path
import signal
import sys

import praw
import prawcore

# Uncomment for debugging.
# from logging import basicConfig, DEBUG
# basicConfig(level=DEBUG)

# globals
posts = {}
comments_dict = {}
sub_name = ""
stdoutOnly = False


def convert_time(object):
    return dt.datetime.fromtimestamp(object).strftime("%m-%d-%Y %H:%M:%S")


def today():
    return dt.date.today().isoformat()


def writeJson():
    if stdoutOnly:
        print("\n! No JSON file will be written.\n")
        print(json.dumps(posts, indent=4), "\n")
    else:
        filename = "./data/reddit_{0}_{1}.json"
        filename = filename.format(sub_name, today())

        print("\n* Writing to file", filename, end=" ... ", flush=True)
        with open(filename, "w") as fp:
            fp.write(json.dumps(posts, indent=4))

        print("Write complete.\n")


def sigintHandler(signal, frame):
    print("\n\n! SIGINT RECEIVED -- dumping to file.")
    writeJson()
    sys.exit(0)


def gather(p_sort, c_sort, num):
    config = configparser.ConfigParser()
    if os.path.isfile("config.ini"):
        config.read("config.ini")
    else:
        print("\n! Unable to find config.ini. Bailing.\n")
        sys.exit(0)
    try:
        Reddit = praw.Reddit(
            client_id=config["APP"]["client_id"],
            client_secret=config["APP"]["client_secret"],
            user_agent=config["APP"]["agent"],
            username=config["USER"]["username"],
            password=config["USER"]["password"],
        )

        if Reddit.user.me():
            print("\n* You are currently logged in as u/{0}".format(Reddit.user.me()))
        else:
            print("\n* You are not currently logged in.")

        Reddit.read_only = True

    except prawcore.exceptions.ResponseException:
        print("\nUnable to authenticate API access. Check credentials and try again.\n")
        sys.exit(0)
    sub = Reddit.subreddit(sub_name)

    try:
        sub_actions = {
            "hot": sub.hot,
            "new": sub.new,
            "top": sub.top,
            "controversial": sub.controversial,
            "rising": sub.rising,
        }

        print(
            "\n| Gathering {0} {1} {2}, and comments sorted by {3}, from r/{4}. Please be patient.".format(
                "all" if not num else num,
                p_sort,
                "posts" if num != 1 else "post",
                c_sort,
                sub_name,
            )
        )

        global posts

        for post in sub_actions[p_sort](limit=num):
            print("|- Gathering post", post.id, end=" ... ", flush=True)
            posts[post.id] = {
                "title": post.title,
                "flair": post.link_flair_text,
                "date_created": convert_time(post.created),
                "author": post.author.name if post.author else "[deleted]",
                "upvotes": post.score,
                "upvote_ratio": post.upvote_ratio,
                "edited": post.edited
                if str(post.edited).isalpha()
                else convert_time(post.edited),
                "locked": post.locked,
                "nsfw": post.over_18,
                "spoiler": post.spoiler,
                "sticky": post.stickied,
                "url": post.url,
                "comment_count": post.num_comments,
                "text": post.selftext,
                "comments": {},
            }

            print("Gathering comments", end=" ... ", flush=True)
            post.comment_sort = c_sort
            post.comments.replace_more(limit=None)

            global comments_dict

            for comment in post.comments.list():
                comments_dict[comment.id] = {
                    "date_created": convert_time(comment.created),
                    "author": comment.author.name if comment.author else "[deleted]",
                    "upvotes": comment.score,
                    "edited": comment.edited
                    if str(comment.edited).isalpha()
                    else convert_time(comment.edited),
                    "is_op": comment.is_submitter,
                    "sticky": comment.stickied,
                    "text": comment.body,
                }
            print("Post gathered successfully.")
            posts[post.id]["comments"] = comments_dict

        print("\n* Successfully gathered {0} posts.".format(num))
        writeJson()

    except prawcore.PrawcoreException:
        print("\nAccess to r/{0} is not currently possible. Bailing.\n".format(sub_name))
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subreddit", help="Choose the subreddit to scrape.")
    parser.add_argument(
        "-p",
        choices=["hot", "new", "top", "controversial", "rising"],
        help="Post sort order. Default = hot",
    )
    parser.add_argument(
        "-c",
        choices=["confidence", "controversial", "new", "old", "q&a", "top"],
        help="Comment sort order. Default = controversial",
    )
    parser.add_argument("-n", type=int, help="Number of posts to scrape. Default = all")
    parser.add_argument(
        "--stdout",
        dest="stdoutOnly",
        action="store_true",
        help="Specify this option to print gathered data to STDOUT instead of a JSON file.",
    )

    args = parser.parse_args()

    global sub_name
    global stdoutOnly

    sub_name = args.subreddit
    stdoutOnly = args.stdoutOnly

    gather(
        args.p if args.p else "hot",
        args.c if args.c else "controversial",
        args.n if args.n else None,
    )


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigintHandler)
    main()
