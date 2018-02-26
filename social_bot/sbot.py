import base64
import random
import string

import requests
from rest_framework import status
from rest_framework.utils import json
import username_generator

from social_bot.exceptions import BotLikeException, BotCreatePostException, BotLoginExcpetion, BotSignUpException


class SocialBot(object):
    HEADERS = {
        "content-type": "application/json",
        "Authorization": ""
    }

    SIGN_UP_URL = 'http://localhost:8000/sign-up/'
    LOGIN_URL = 'http://localhost:8000/login/'
    CREATE_POST_URL = 'http://localhost:8000/api/posts/'

    PWD_GEN_CHARS = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"

    def __init__(self, json_data=None, file_path=None):
        if json_data:
            self.json = json_data
        elif file_path:
            self.json = json.load(open(file_path,'r'))
        else:
            # TODO: make custom exception
            raise Exception

        self.number_of_users = self.json['number_of_users'] if self.json['number_of_users'] else 1
        self.max_posts_per_user = self.json['max_posts_per_user'] if self.json['max_posts_per_user'] else 1
        self.max_likes_per_user = self.json['max_likes_per_user'] if self.json['max_likes_per_user'] else 1


    @staticmethod
    def _pw_gen(size=8, chars=string.ascii_letters + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def signup_users(self):
        """
            Sign up random generated  and let signup view know that it is bot
        """
        self.signed_up_users = []
        number_of_users = self.json['number_of_users']
        while number_of_users:
            username = username_generator.get_uname(min_size=4, max_size=12, underscores=True)

            payload = {
                "bot": base64.b64encode(b'botcuga').decode('utf-8'),
                "username": username,
                "password": self._pw_gen(),
                "email": username + '@bot.com'
            }

            response = requests.post(url=self.SIGN_UP_URL, data=json.dumps(payload), headers=self.HEADERS)

            if not response.status_code == status.HTTP_201_CREATED:
                raise BotSignUpException(response.content)

            self.signed_up_users.append(payload)

            number_of_users -=1

    def login_users(self):
        """
            Login all singed up users and store them in "logged_users"
        """
        self.logged_users = []
        for user in self.signed_up_users:
            response = requests.post(url=self.LOGIN_URL, data=json.dumps(user), headers=self.HEADERS)

            if not response.status_code == status.HTTP_200_OK:
                raise BotLoginExcpetion(response.content)

            self.logged_users.append(json.loads(response.content))

    def create_posts(self):
        """
            Create random number , no greater then max_posts_per_user, for every user. Every post will be
            stored on logged_users data as "posts".
        """
        for user in self.logged_users:

            rand_posts = random.randint(1,self.max_posts_per_user)
            user['posts'] = []

            while rand_posts:
                self.HEADERS['Authorization'] = 'Bearer '+ user['token']

                payload = {
                    "title": user['user']['username'] + " post number " + str(rand_posts),
                    "text": "They see me botting :D"
                }

                response = requests.post(url=self.CREATE_POST_URL, data=json.dumps(payload), headers=self.HEADERS)

                if not response.status_code == status.HTTP_201_CREATED:
                    raise BotCreatePostException(response.content)

                user['posts'].append(json.loads(response.content))

                rand_posts -= 1

    def like_posts(self, post_id, user):
        self.HEADERS['Authorization'] = user['token']
        user['likes'] = 0
        response = \
            requests.post(url='http://localhost:8000/posts/{}/like'.format(post_id), headers=self.HEADERS)
        if not response.status_code == status.HTTP_201_CREATED:
            raise BotLikeException(response.content)
        user['likes'] += 1

    def like_logic(self):
        max_posts_user = self.logged_users