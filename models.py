from app import login, db
from datetime import datetime
from flask import current_app
import jwt
import json
from sqlalchemy.dialects.postgresql import ARRAY

friendship = db.Table('friendship',
                      db.Column('user_id', db.Integer, db.ForeignKey('user.id'),  primary_key=True),
                      db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
                      )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.Column(ARRAY(db.String(20)))

    friends = db.relationship('User',
                               secondary=friendship,
                               primaryjoin=(friendship.c.user_id == id),
                               secondaryjoin=(friendship.c.friend_id == id),
                               backref=db.backref('friends', lazy='dynamic'),
                               lazy='dynamic')
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='author',
                                   lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id',
                                       backref='recipient', lazy='dynamic')
    load_message_read_time = db.Column(db.DateTime)
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed_post = Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id)
        own_posted = Post.query.filter_by(user_id=self.id)
        print(followed_post.union(own_posted).order_by(Post.timestamp.desc()).all())
        return followed_post.union(own_posted).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in},
                          current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms='HS256')['reset_password']
        except:
            return
        return User.query.get(id)

    def __repr__(self):
        return '<User {}>'.format(self.username)


@login.user_loader
def load_user(uid):
    return User.query.get(int(uid))


class Wisdom(db.Model):
    # __searchable__ = ['body']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20))
    body = db.Column(db.Text())
    tags = db.Column(ARRAY(db.String))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

