from datetime import datetime
from django.urls import reverse
from urllib.parse import urlsplit
import markdown
import re

# import requests

md = markdown.Markdown()
url_pattern = (
    r"(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)"
)


def num_comma(num):
    return f"{num:,}"


# can move to frontend
def percent_upvoted(upvote_ratio):
    return int(upvote_ratio * 100)


# can move to frontend
def parse_date(created_utc):
    return datetime.fromtimestamp(created_utc).strftime("%d %b %Y")


# def streamable_embed(url):
#     return re.sub(r"(http.://streamable.com/)(.*)", r"\1/o/\2", url)
#
#
# def twitter_embed(url):
#     resp = requests.get(f"https://publish.twitter.com/oembed?url={url}")
#
#     if resp.status_code == 200:
#         return resp.json()["html"]
#     else:
#         return None


def content_origin(post):
    if post["selftext"]:
        return f'self.{post["subreddit"].display_name}'
    else:
        return urlsplit(post["url"]).netloc.strip("www.")


# can move to frontend
def parse_username(text):
    return text or "[deleted]"


def parse_body(text):
    html = md.convert(text)
    patterns = {
        r"https?://(www.)?reddit.com/?": reverse("subreddit:index"),
        r"<blockquote>": '<blockquote class="quote">',
    }

    for pat, rep in patterns.items():
        html = re.sub(pat, rep, html)

    return html


def parse_url(url):
    return re.sub(r"https?://(www.)?reddit.com/?", reverse("subreddit:index"), url)


# can move to frontend
def parse_score(comment):
    return f"{comment.score} pts" if not comment.score_hidden else "[score hidden]"


def find_vid(post):
    if "streamable" in post["url"]:
        return re.sub(r"(http.://streamable.com/)(.*)", r"\1/o/\2", post["url"])
    elif post["url"].endswith("gifv"):
        return post["url"].replace("gifv", "mp4")
    elif post["media"]:
        reddit_video = post["media"].get("reddit_video")
        if reddit_video:
            return reddit_video["fallback_url"]


def find_embed(post):
    if post["media"] and "twitter" not in post["url"]:
        embed_content = post["media"].get("oembed")
        if embed_content:
            return embed_content["html"].replace("autoplay;", "")


def find_img(post):
    if any(post["url"].endswith(ext) for ext in ("png", "jpg", "gif")):
        return post["url"]
    else:
        match = re.search(r"(http\S+\.(jpg|png))", post["selftext"])
        if match:
            return match.group(1)


# can move to frontend
def post_age(created_utc):
    delta = datetime.now() - datetime.fromtimestamp(int(created_utc))

    hours = int(delta.seconds / 3600)
    minutes = int(delta.seconds / 60)

    if delta.days >= 365:
        return f"{int(delta.days / 365)}y"
    elif delta.days >= 31:
        return f"{int(delta.days / 31)}mo"
    elif delta.days > 0:
        return f"{delta.days}d"
    elif hours:
        return f"{hours}h"
    elif minutes:
        return f"{minutes}m"
    else:
        return "Just now"
