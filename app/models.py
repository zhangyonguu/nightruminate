# -*- coding: utf-8 -*-
from app import db
from flask_login import UserMixin
from app import login
from datetime import datetime
from enum import Enum, unique
from mongoengine.queryset.visitor import Q
import json
from flask_mongoengine.wtf import model_form
from wtforms import validators


@unique
class MessageType(Enum):
    AddFriend = 0, '请求加你为好友'
    AskShare = 1, '请求分享'
    Share = 2, '向你分享'
    OpenHeart = 3, '对你敞开心扉'
    CloseHeart = 4, '关闭心扉'
    Accept = 5, '接受你的请求'
    Refuse = 6, '拒绝你的请求'

    def __new__(cls, value, name):
        member = object.__new__(cls)
        member._value_ = value
        member.fullname = name
        return member

    def __int__(self):
        return self.value


class User(UserMixin, db.Document):
    name = db.StringField(max_length=20, required=True)
    email = db.StringField(max_length=255)
    pw_hash = db.StringField(max_length=255)
    friends = db.ListField(db.ObjectIdField(), default=[])
    beloved = db.ListField(db.ObjectIdField(), default=[])
    be_beloved = db.ListField(db.ObjectIdField(), default=[])
    last_seen = db.DateTimeField(default=datetime.utcnow)
    last_message_read_time = db.DateTimeField()
    message_received = db.ListField(db.StringField(), default=[])
    message_sent = db.ListField(db.StringField(), default=[])

    def add_friend(self, name):
        user = User.objects(name=name).first()
        if user is not None:
            if user.id in self.friends:
                return
            else:
                self.update(push__friends=user.id)
                user.update(push__friends=self.id)
                # user is just a internal variable, so do not need to reload
                self.reload()

    def delete_friend(self, name):
        user = User.objects(name=name).first()
        if user is not None:
            if user.id in self.friends:
                self.update(pull__friends=user.id)
                user.update(pull__friends=self.id)
                # user is just a internal variable, so do not need to reload
                self.reload()

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.objects(Q(timestamp__gt=last_read_time) & Q(recipient=self.name)).count()

    def send_message(self, message_content, recipient, pay_load={}):
        message = Message(sender=self.name, recipient=recipient,
                          content=message_content, pay_load=pay_load)
        message.save()
        user = User.objects(name=recipient).first()
        user.add_notification('unread_message_count', user.new_messages())

    def add_notification(self, name, data):
        Notification.objects(name=name, recipient=self.name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), recipient=self.name)
        n.save()

    def __repr__(self):
        return '<User: {}>'.format(self.name + ',friends: ' + str(self.friends))


@login.user_loader
def load_user(uid):
    return User.objects(id=uid).first()


class Comment(db.EmbeddedDocument):
    author = db.StringField(required=True)
    body = db.StringField(required=True, max_length=140)
    timestamp = db.DateTimeField(default=datetime.utcnow)


class Story(db.Document):
    title = db.StringField(required=True)
    author = db.LazyReferenceField(User)
    comments = db.ListField(db.EmbeddedDocumentField(Comment), default=[])
    body = db.StringField(required=True)
    timestamp = db.DateTimeField(default=datetime.utcnow)
    tags = db.ListField(db.StringField(max_length=20), default=[])

    meta = {'indexes': [
        {
            'fields': ['$title', '$body'],
            'default_language': 'chinese',
            'weights': {'title': 10, 'body': 2}
        }
    ]}


class Message(db.Document):
    sender = db.StringField(required=True)
    recipient = db.StringField(required=True)
    content = db.StringField(required=True)
    pay_load = db.DictField(default={})
    dealed = db.BooleanField(default=False)
    timestamp = db.DateTimeField(default=datetime.utcnow)

    def __repr__(self):
        return '<Message: {}>'.format(self.body)


class Notification(db.Document):
    name = db.StringField(required=True)
    recipient = db.StringField(required=True)
    timestamp = db.DateTimeField(default=datetime.utcnow)
    payload_json = db.StringField(required=True)

    def get_data(self):
        return json.loads(self.payload_json)
