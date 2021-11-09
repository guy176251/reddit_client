from datetime import datetime
from django import template
from django.urls import reverse
from random import choice
from urllib.parse import urlsplit
import markdown
import re
import requests

md = markdown.Markdown()
register = template.Library()
url_pattern = '(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'


@register.simple_tag
def num_with_comma(num):
    return f'{num:,}'


@register.simple_tag
def percent_upvoted(post):
    return int(post.upvote_ratio * 100)


@register.simple_tag
def parse_date(post_or_sub):
    return datetime.fromtimestamp(post_or_sub.created_utc).strftime('%d %b %Y')


@register.simple_tag
def streamable_embed(url):
    return re.sub(r'(http.://streamable.com/)(.*)', r'\1/o/\2', url)


@register.simple_tag
def twitter_embed(url):
    resp = requests.get(f'https://publish.twitter.com/oembed?url={url}')

    if resp.status_code == 200:
        return resp.json()['html']
    else:
        return None


@register.simple_tag
def content_origin(post):
    if post.selftext:
        return f'self.{post.subreddit.display_name}'
    else:
        return urlsplit(post.url).netloc.strip('www.')


@register.simple_tag
def parse_username(text):
    return text or '[deleted]'


@register.simple_tag
def parse_body(text):
    html = md.convert(text)
    patterns = {
        'https?://(www.)?reddit.com/?': reverse('subreddit:index'),
        '<blockquote>': '<blockquote class="quote">',
    }

    for pat, rep in patterns.items():
        html = re.sub(pat, rep, html)

    return html


@register.simple_tag
def parse_url(url):
    return re.sub(r'https?://(www.)?reddit.com/?', reverse('subreddit:index'), url)


@register.simple_tag
def parse_score(comment):
    return f'{comment.score} pts' if not comment.score_hidden else '[score hidden]'


#@register.simple_tag
#def find_vid(post):
#    if 'streamable' in post.url:
#        return re.sub(r'(http.://streamable.com/)(.*)', r'\1/o/\2', post.url)
#    elif post.url.endswith('gifv'):
#        return post.url.replace('gifv', 'mp4')
#    elif post.media and (reddit_video := post.media.get('reddit_video')):
#        return reddit_video['fallback_url']
#
#
#@register.simple_tag
#def find_embed(post):
#    if post.media and (embed_content := post.media.get('oembed')) and 'twitter' not in post.url:
#        #return embed_content['html'].replace('autoplay;', '')
#        return re.sub(r'(iframe class=")', r'\1embed-responsive-item ', embed_content['html'])
#
#
#@register.simple_tag
#def find_img(post):
#    if any(post.url.endswith(ext) for ext in ('png', 'jpg', 'gif')):
#        return post.url
#    elif (match := re.search(r'(http\S+\.(jpg|png))', post.selftext)):
#        return match.group(1)
#    else:
#        return None
#
#
#@register.simple_tag
#def post_age(post):
#    delta = datetime.now() - datetime.fromtimestamp(int(post.created_utc))
#
#    if delta.days >= 365:
#        return f'{int(delta.days / 365)}y'
#    elif delta.days >= 31:
#        return f'{int(delta.days / 31)}mo'
#    elif delta.days > 0:
#        return f'{delta.days}d'
#    elif (hours := int(delta.seconds / 3600)):
#        return f'{hours}h'
#    elif (minutes := int(delta.seconds / 60)):
#        return f'{minutes}m'
#    else:
#        return 'Just now'


@register.simple_tag
def get_replies(cmt):
    try:
        return cmt.replies[:]
    except AttributeError:
        return []


@register.simple_tag
def get_comments(post):
    return post.comments[:]


@register.simple_tag
def get_post_body(post):
    try:
        return post.body
    except AttributeError:
        return None


@register.simple_tag
def get_true():
    return True


@register.simple_tag
def get_false():
    return False


@register.simple_tag
def change_bool(boolean):
    return not boolean


@register.simple_tag
def instantiate(thing):
    return thing


@register.simple_tag
def top_five(subs):
    temp = set()

    while len(temp) < 5:
        temp.add(choice(subs))

    return temp
