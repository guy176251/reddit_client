#from django.db import models
from random import choice
from string import digits
from time import time

users = {}


def anon_user(request):
    user_id = request.session.setdefault('id',
                f'{"".join(choice(digits) for _ in range(4))}{int(time())}')
    user = users.setdefault(user_id, {'id': user_id,
                                      'sub_posts': {},})

    return user


class AnonUser:
    sub_posts = {}
    sub_sorting = {}
    id = None

    def __init__(self, id):
        self.id = id


class AnonUserMgr:
    users = {}

    def __getitem__(self, request):
        user_id = request.session.setdefault('id',
                f'{"".join(choice(digits) for _ in range(4))}{int(time())}')
        user = self.users.setdefault(user_id, AnonUser(user_id))

        return user
