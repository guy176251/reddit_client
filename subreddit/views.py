from django.shortcuts import render
from praw.models import MoreComments
from prawcore.exceptions import NotFound
from time import time as Time
import os
import praw

from .forms import SubredditForm
from .models import anon_user

from .view_helpers import (
    num_comma,
    parse_body,
    parse_date,
    parse_score,
    parse_url,
    parse_username,
    find_embed,
    find_img,
    find_vid,
    post_age,
    percent_upvoted,
    content_origin,
)

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
reddit = praw.Reddit(
    client_secret=os.environ["praw_client_secret"],
    client_id=os.environ["praw_client_id"],
    username=os.environ["reddit_user"],
    password=os.environ["reddit_pass"],
    user_agent=user_agent,
)

# these are just to pass to the page to generate urls
popular_subs = list(reddit.subreddits.popular())
sorting_types = ["hot", "new", "rising", "controversial", "top"]
sorting_intervals = {
    "all": "all time",
    "hour": "past hour",
    "day": "past day",
    "week": "past week",
    "month": "past month",
    "year": "past year",
}


def post_generator(sub, sorting, links_from):
    sub_by_sorting = sub[sorting]

    posts = []
    page_num = 0
    size = 25

    try:
        gen = sub_by_sorting(links_from, limit=None)
    except (ValueError, TypeError):
        gen = sub_by_sorting(limit=None)

    for post_num, post in enumerate(gen):
        if len(posts) == size:
            page_num += 1
            yield page_num, posts
            posts = []
        posts.append(post)

    yield page_num, posts


def about_view(request):
    context = {
        "popular_subs": popular_subs[:20],
        "search_field": SubredditForm(),
    }

    return render(request, "about.html", context)


def search_view(request):
    context = {
        "popular_subs": popular_subs[:20],
        "search_field": SubredditForm(),
    }

    if request.method != "POST":
        return render(request, "subreddit/search.html", context)

    search_field = SubredditForm(request.POST)

    if not search_field.is_valid():
        return render(request, "subreddit/search.html", context)

    search_name = search_field.cleaned_data["sub_name"]
    search_results = reddit.subreddits.search_by_name(search_name)
    print(search_results)

    context.update(
        {
            "search_field": search_field,
            "search_name": search_name,
            "search_results": search_results,
            "search_results_num": len(search_results),
            "search_success": len(search_results) > 0,
        }
    )

    return render(request, "search.html", context)


def post_view(request, sub_name, post_id):
    try:
        reddit.submission(post_id).title
    except NotFound:
        subreddit_view(request, sub_name)
        return

    post = get_post(post_id, True)

    start = Time()
    context = {
        "comments": get_all_cmts(post),
        "popular_subs": popular_subs[:20],
        "not_all": True,
        "post": post,
        "search_field": SubredditForm(),
        "subreddit": get_sub(sub_name),
    }
    print(f"{Time() - start:.2f} seconds")

    return render(request, "post.html", context)


def subreddit_view(request, sub_name="all", sorted_by="hot"):
    sub = get_sub(sub_name)
    sub_name = sub["display_name"].lower()
    user = anon_user(request)

    next_page = request.GET.get("next_page")
    links_from = request.GET.get("t", "0")

    # refresh post generator on new page get
    if not next_page:
        user["sub_posts"][sub_name] = {
            "sorted_by": sorted_by,
            "posts": post_generator(sub, sorted_by, links_from),
        }

    post_dict = user["sub_posts"][sub_name]

    print(f'\n  id: {user["id"]}\n  r/{sub_name}: {sorted_by}')

    # if not any(sub_name == n for n in ['all', 'popular']):
    #    sub_info = {
    #        'subscribers': num_comma(sub['subsc'])
    #    }

    try:
        page_num, posts = next(post_dict["posts"])
        posts = [get_post(p, False) for p in posts]
    except StopIteration:
        posts = []
        page_num = 0

    context = {
        "links_from": links_from,
        "links_from_label": sorting_intervals.get(links_from, "all time"),
        "not_all": True if sub["display_name"] in ["all", "popular"] else False,
        "page_num": page_num,
        "search_field": SubredditForm(),
        "sorted_by": sorted_by,
        "sub_dict_len": len(user["sub_posts"]),
        "subreddit": sub,
        "sorting_intervals": sorting_intervals,
        "submissions": posts,
        "sorting_types": sorting_types,
        "popular_subs": popular_subs[:20],
    }

    return render(request, "subreddit.html", context)


def get_sub(sub_name: str) -> dict:
    sub_obj = reddit.subreddit(sub_name)

    try:
        sub_obj.id
    except NotFound:
        sub_obj = reddit.subreddit("all")

    attrs = [
        "icon_img",
        "title",
        "description_html",
        "display_name",
        "subscribers",
        "accounts_active",
        "description_html",
        "created_utc",
    ]
    attrs.extend(sorting_types)

    sub = get_attrs(sub_obj, attrs)

    set_attr(sub, num_comma, "subscribers", "accounts_active")
    set_attr(sub, parse_date, "created_utc")
    set_attr(sub, parse_url, "description_html")

    set_defaults = {
        "icon_img": "/static/img/default_sub_icon.png",
        "title": f'r/{sub["display_name"]}',
    }

    for attr, value in set_defaults.items():
        sub[attr] = sub[attr] or value

    sub["show_media"] = "show"

    return sub


def get_post(post_or_id, is_post: bool) -> dict:
    try:
        post_or_id.id
    except AttributeError:
        post_obj = reddit.submission(post_or_id)
        attrs = [
            "id",
            "url",
            "is_self",
            "selftext_html",
            "title",
            "subreddit",
            "comments",
            "author",
            "media",
            "selftext",
            "created_utc",
            "thumbnail",
            "score",
            "num_comments",
            "upvote_ratio",
        ]
        post = get_attrs(post_obj, attrs)
    else:
        post = vars(post_or_id)

    post["embed"] = find_embed(post)
    post["img"] = find_img(post)
    post["vid"] = find_vid(post)
    # post["show_media"] = "show" if not is_post else ""
    post["show_media"] = ""
    post["age"] = post_age(post["created_utc"])
    post["url"] = post["url"] if "/gallery/" in post["url"] else parse_url(post["url"])
    post["author_name"] = (
        parse_username(post["author"].name) if post.get("author") else "[deleted]"
    )
    post["content_origin"] = content_origin(post)
    post["show_selftext"] = (
        "show" if post["is_self"] and is_post and post["selftext"] else ""
    )
    post["date"] = parse_date(post["created_utc"])
    post["fullscore"] = num_comma(post["score"])
    post["percent_upvoted"] = percent_upvoted(post["upvote_ratio"])

    return post


def get_all_cmts(post):
    start = Time()
    root_cmts = post["comments"][:]
    all_cmts = [get_cmt(c, True) for c in root_cmts]
    print(f"get_all_cmts: {Time() - start:.2f} secs")

    return all_cmts


_n = "\n"
_s = " " * 3


def get_cmt(cmt, color_switch, depth=0):
    if type(cmt) == MoreComments:
        return ""

    color = f'solarized-dark{"" if color_switch else "-2"}'
    edited_text = "(edited)" if cmt.edited else ""
    age = post_age(cmt.created_utc)
    score = parse_score(cmt)
    author_info = (
        f"•{ _s }{ score }{ _s }•{ _s }{ age }{ edited_text }" if cmt.author else ""
    )

    cmt_dict = {
        "color": color,
        "edited_text": edited_text,
        "age": age,
        "score": score,
        "author_info": author_info,
        "shadow": "shadow" if cmt.is_root else "",
        "author_name": parse_username(cmt.author.name) if cmt.author else "[deleted]",
        "op_color": "orange"
        if cmt.author and cmt.author.name == cmt.submission.author.name
        else color,
        "body": parse_body(cmt.body_html),
        "id": cmt.id,
        "replies": [get_cmt(c, not color_switch, depth + 1) for c in cmt.replies],
    }

    return cmt_dict


#    if depth == 3:
#        return ''
#    else:
#        return f'''
# <div class="card { cmt_dict["shadow"] } { cmt_dict["color"] } mt-3">
#  <div class="card-body text-wrap">
#    <p>
#      <a class="btn btn-dark rounded-circle { cmt_dict["color"] }" href="#comment-{ cmt_dict["id"] }" data-toggle="collapse" aria-expanded="true">
#        <i class="fa fa-minus-circle" aria-hidden="true"></i>
#      </a>
#      <a class="{ cmt_dict["op_color"] } btn rounded" href="#">
#        <b>{ cmt_dict["author_name"] }</b>
#      </a>
#      { author_info }
#    </p>
#    <div id="comment-{ cmt_dict["id"] }" class="collapse gray-text">
#      Content hidden
#    </div>
#    <div id="comment-{ cmt_dict["id"] }" class="collapse show">
#      { cmt_dict["body"] }
#      { _n.join(get_cmt(c, not color_switch, depth + 1) for c in cmt.replies) }
#    </div>
#  </div>
# </div>
# '''

# if cmt.replies:
#    setattr(cmt, 'replies_list', [result for c in cmt.replies if (result := get_cmt(c, not color_switch))])

# return cmt


def set_attr(dictionary, func, *attrs):
    for attr in attrs:
        if dictionary[attr]:
            dictionary[attr] = func(dictionary[attr])


def get_attrs(obj, attrs) -> dict:
    obj_dict = {}
    for attr in attrs:
        try:
            obj_dict[attr] = getattr(obj, attr)
        except NotFound:
            obj_dict[attr] = ""

    return obj_dict
