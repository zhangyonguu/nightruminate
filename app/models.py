from app import db
from flask_login import UserMixin
from app import login
from datetime import datetime
from enum import Enum, unique


@unique
class MessageType(Enum):
    AddFriend = 0
    Accept = 1
    AskShare = 2
    OpenHeart = 3

    def __int__(self):
        return self.value


class User(UserMixin, db.Document):
    name = db.StringField(max_length=20, required=True)
    email = db.StringField(max_length=255)
    pw_hash = db.StringField(max_length=255)
    tags = db.ListField(db.StringField(max_length=20), default=[])
    friends = db.ListField(db.ObjectIdField(), default=[])
    last_seen = db.DateTimeField(default=datetime.utcnow())
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
                print(id(self), id(user))
                # user is just a internal variable, so do not need to reload
                self.reload()

    def delete_friend(self, name):
        user = User.objects(name=name).first()
        if user is not None:
            if user.id in self.friends:
                print(id(self), id(user))
                self.update(pull__friends=user.id)
                user.update(pull__friends=self.id)
                # user is just a internal variable, so do not need to reload
                self.reload()

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.objects(timestamp__gt=last_read_time).count()

    def send_message(self, message_type, recipient_id):
        message = Message(sender_id=self.id, recipient_id=recipient_id, type=message_type)
        message.save()

    def __repr__(self):
        return '<User: {}>'.format(self.name + ',friends: ' + str(self.friends))


@login.user_loader
def load_user(uid):
    return User.objects(id=uid).first()


class Message(db.Document):
    sender_id = db.ObjectIdField(required=True)
    recipient_id = db.ObjectIdField(required=True)
    type = db.IntField(max_length=140)
    timestamp = db.DateTimeField(default=datetime.utcnow())

    def __repr__(self):
        return '<Message: {}>'.format(self.body)
