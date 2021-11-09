from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.subreddit_view, name='index'),
    path('search/', views.search_view, name='search'),
    path('r/<sub_name>/', views.subreddit_view, name='subreddit'),
    re_path(r'r/(?P<sub_name>\w+)/(?P<sorted_by>\w+)/$', views.subreddit_view, name='subreddit'),
    path('r/<sub_name>/comments/<post_id>/', views.post_view, name='post'),
    re_path(r'r/(?P<sub_name>\w+)/comments/(?P<post_id>(\w|\d)+)/\w*/?$', views.post_view, name='post'),
    path('about/', views.about_view, name='about'),
]
