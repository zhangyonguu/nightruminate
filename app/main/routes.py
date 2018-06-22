
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_user, logout_user, login_required

from datetime import datetime
from flask import jsonify
from app.translate import translate
from app.main import bp
from app.main.forms import EditProfileForm, SearchForm
from ..models import User, Message, MessageType, Notification

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        current_user.save()
        g.search_form = SearchForm()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', title='Home Page')


@bp.route('/username/<username>')
@login_required
def user(username):
    user = User.objects(name=username).first()
    return render_template('user.html', user=user)


@bp.route('/search_friend')
@login_required
def search_friend():
    username = request.args.get('username')
    user = User.objects(name=username).first()
    if user is not None:
        if user.id == current_user.id:
            return jsonify({'status': 0, 'search_result': "这是你的用户名"})
        elif user.id not in current_user.friends:
            return jsonify({'status': 1, 'search_result': '找到用户'})
        else:
            return jsonify({'status': 0, 'search_result': '该用户已经是你的好友'})
    else:
        return jsonify({'status': 0, 'search_result': '用户名不存在'})


@bp.route('/search')
@login_required
def search():
    pass


@bp.route('/request_add_friend')
@login_required
def request_add_friend():
    username = request.args.get('username')
    current_user.send_message(MessageType.AddFriend.fullname, username)
    return jsonify({'result_status': 'sent'})


@bp.route('/agree_add_friend')
@login_required
def agree_add_friend():
    message_id = request.args.get('message_id')
    message = Message.objects(id=message_id).first()
    message.update(set__dealed=True)
    current_user.send_message(MessageType.Accept.fullname, message.sender)
    current_user.add_friend(message.sender)
    return jsonify({'result_status': 'sent'})


@bp.route('/refuse_add_friend')
@login_required
def refuse_add_friend():
    message_id = request.args.get('message_id')
    message = Message.objects(id=message_id).first()
    message.update(set__dealed=True)
    current_user.send_message(MessageType.Refuse.fullname, message.sender)
    return jsonify({'result_status': 'sent'})


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)


@bp.route('/messages')
@login_required
def messages():
    current_user.update(set__last_message_read_time=datetime.utcnow())
    current_user.add_notification('unread_message_count', 0)
    current_user.reload()
    page = request.args.get('page', 1, type=int)
    messages = Message.objects(recipient=current_user.name).order_by('-timestamp').\
        paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = Notification.objects(timestamp__gt=since).\
        order_by('timestamp')
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
