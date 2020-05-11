#!/Users/justin/.pyenv/shims/python

import praw
import json
import datetime as dt


def convert_time(object):
    return dt.datetime.fromtimestamp(object).strftime("%m-%d-%Y %H:%M:%S")


def today():
    return dt.date.today().isoformat()


Reddit = praw.Reddit(client_id="KoMi6u2CY6Mnfg",
                     client_secret="QaqFg2U6ARDxLN-n7G7ayq5_kaY",
                     user_agent="propaganda by u/the_vermi",
                     username="the_vermi",
                     password="g,UNzDAwLg9u")

Reddit.read_only = True

sub = Reddit.subreddit("Coronavirus")

posts = {}

print('Gathering data, please be patient.')
for post in sub.new(limit=1):
    print('Gathering post', post.id, end=' ... ')
    posts[post.id] = {
        'title': post.title,
        'flair': post.link_flair_text,
        'date_created': convert_time(post.created),
        'author': post.author.name if post.author else '[deleted]',
        'upvotes': post.score,
        'upvote_ratio': post.upvote_ratio,
        'edited': post.edited if str(post.edited).isalpha() else convert_time(post.edited),
        'locked': post.locked,
        'nsfw': post.over_18,
        'spoiler': post.spoiler,
        'sticky': post.stickied,
        'url': post.url,
        'comment_count': post.num_comments,
        'text': post.selftext,
        'comments': {}
    }

    post.comment_sort = 'controversial'
    post.comments.replace_more(limit=None)

    comments_dict = {}
    print('Gathering comments', end=' ... ')
    for comment in post.comments.list():
        comments_dict[comment.id] = {
            'date_created': convert_time(comment.created),
            'author': comment.author.name if comment.author else '[deleted]',
            'upvotes': comment.score,
            'edited': comment.edited if str(comment.edited).isalpha() else convert_time(comment.edited),
            'is_op': comment.is_submitter,
            'sticky': comment.stickied,
            'text': comment.body
        }
    print('Post gathered successfully.')
    posts[post.id]['comments'] = comments_dict

filename = './data/reddit_coronavirus_' + today() + '.json'
print('Data gathered, writing to file', filename, end=' ... ')
with open(filename, 'w') as fp:
    fp.write(json.dumps(posts, indent=4))

print('Write complete.\n')
