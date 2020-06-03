#!/usr/bin/env python3
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
import os.path
import signal
import sys

import praw
import prawcore
import ujson as json
from tinydb import TinyDB

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


def sigintHandler(signal, frame):
    print("\n\n! SIGINT RECEIVED -- bailing")
    if stdoutOnly:
        print("\n! No file has been written.\n")
        print(json.dumps(posts, indent=4), "\n")
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

    if not stdoutOnly:
        filename = "./data/reddit_{0}_{1}.json"
        filename = filename.format(sub_name, today())
        db = TinyDB(filename, indent=4)
        db.table("posts")
        db.table("comments")

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

        if stdoutOnly:
            global posts
            posts["subreddit"] = sub_name
            posts["version"] = 7
            posts["posts"] = {}
        else:
            db.insert({"subreddit": sub_name})

        i = 1
        for p in sub_actions[p_sort](limit=num):
            print("|- {0} Gathering post".format(i), p.id, end=" ... ", flush=True)
            post = {
                "title": p.title,
                "flair": p.link_flair_text,
                "date_created": convert_time(p.created),
                "author": p.author.name if p.author else "[deleted]",
                "upvotes": p.score,
                "upvote_ratio": p.upvote_ratio,
                "edited": p.edited
                if str(p.edited).isalpha()
                else convert_time(p.edited),
                "locked": p.locked,
                "nsfw": p.over_18,
                "spoiler": p.spoiler,
                "sticky": p.stickied,
                "url": p.url,
                "comment_count": p.num_comments,
                "text": p.selftext,
                "comments": {},
            }

            if stdoutOnly:
                posts["posts"][p.id] = post
            else:
                post["id"] = p.id
                db.table("posts").insert(post)

            print("Gathering comments", end=" ... ", flush=True)
            p.comment_sort = c_sort
            p.comments.replace_more(limit=None)

            for c in p.comments.list():
                comment = {
                    "parent": c.parent_id,
                    "date_created": convert_time(c.created),
                    "author": c.author.name if c.author else "[deleted]",
                    "upvotes": c.score,
                    "edited": c.edited
                    if str(c.edited).isalpha()
                    else convert_time(c.edited),
                    "is_op": c.is_submitter,
                    "sticky": c.stickied,
                    "text": c.body,
                }

                if stdoutOnly:
                    global comments_dict
                    comments_dict[c.id] = comment
                else:
                    comment["id"] = c.id
                    db.table("comments").insert(comment)

            print("Post gathered successfully.")

            if stdoutOnly:
                posts["posts"][post.id]["comments"] = comments_dict

            i += 1

        print("\n* Successfully gathered {0} posts.".format("all" if not num else num))

        if stdoutOnly:
            print("\n! No file has been written.\n")
            print(json.dumps(posts, indent=4), "\n")

    except prawcore.PrawcoreException:
        print(
            "\nAccess to r/{0} is not currently possible. Bailing.\n".format(sub_name)
        )
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
