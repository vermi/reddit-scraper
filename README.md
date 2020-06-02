# Reddit Data Gatherer

## About

This script allows the user to scrape up to 1024 posts, and associated comments, from
 the specified subreddit.

The 'praw' module and valid reddit API credentials are required for the script to
 function correctly.

The subreddit name is required; all other command-line arguments are optional.

A keyboard interrupt (Ctrl-C) can be used to stop the gathering process and immediately
 write any collected information to disk.

## Installation

1. Clone this repository.
2. `pip install -r requirements.txt`
3. `./reddit-scraper.py --help`

## References

For a more detailed explanation of how PRAW works, please visit [the PRAW documentation][1].

[1]: https://praw.readthedocs.io/en/latest/index.html
