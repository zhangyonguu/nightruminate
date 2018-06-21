
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_user, logout_user, login_required

from datetime import datetime
from flask import jsonify
from app.translate import translate
from app.main import bp
from app.main.forms import EditProfileForm, SearchForm
from ..models import User, Message, MessageType

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        print(current_user)
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


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('your changes have saved'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/search_friend')
@login_required
def search_friend():
    print('search friend')
    username = request.args.get('username')
    user = User.objects(name=username).first()
    if user is not None:
        if user.id not in current_user.friends:
            return jsonify({'result_status': 'found', 'name': username, })
        else:
            return jsonify({'result_status': 'existed'})


@bp.route('/request_add_friend')
@login_required
def request_add_friend():
    print('request add friend')
    username = request.args.get('username')
    user = User.objects(name=username).first()
    current_user.send_message(int(MessageType.AddFriend), user.id)
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
    current_user.reload()
    page = request.args.get('page', 1, type=int)
    messages = Message.objects(recipient_id=current_user.id).order_by('-timestamp').\
        paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(Notification.timestamp > since).\
        order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
