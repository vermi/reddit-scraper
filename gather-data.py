#!/Users/justin/.pyenv/shims/python

import argparse
import datetime as dt
import json
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


def convert_time(object):
    return dt.datetime.fromtimestamp(object).strftime("%m-%d-%Y %H:%M:%S")


def today():
    return dt.date.today().isoformat()


def writeJson():
    filename = "./data/reddit_{0}_{1}.json"
    filename = filename.format(sub_name, today())

    print("Data gathered, writing to file", filename, end=" ... ", flush=True)
    with open(filename, "w") as fp:
        fp.write(json.dumps(posts, indent=4))

    print("Write complete.\n")


def sigintHandler(signal, frame):
    print("\nSIGINT RECEIVED -- dumping to file.\n")
    writeJson()
    sys.exit(0)


def gather(p_sort, c_sort, num):
    Reddit = praw.Reddit(
        client_id="KoMi6u2CY6Mnfg",
        client_secret="QaqFg2U6ARDxLN-n7G7ayq5_kaY",
        user_agent="propaganda by u/the_vermi",
        username="the_vermi",
        password="g,UNzDAwLg9u",
    )

    Reddit.read_only = True

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
            "\nGathering {0} {1} {2}, and comments sorted by {3}, from r/{4}. Please be patient.".format(
                "all" if not num else num,
                p_sort,
                "posts" if num != 1 else "post",
                c_sort,
                sub_name,
            )
        )

        global posts

        for post in sub_actions[p_sort](limit=num):
            print("Gathering post", post.id, end=" ... ", flush=True)
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

        writeJson()

    except prawcore.PrawcoreException:
        print("Access to r/{0} is not currently possible. Bailing.\n".format(sub_name))
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="A tool to gather some data from reddit."
    )
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

    args = parser.parse_args()

    global sub_name
    sub_name = args.subreddit

    gather(
        args.p if args.p else "hot",
        args.c if args.c else "controversial",
        args.n if args.n else None,
    )


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigintHandler)
    main()
