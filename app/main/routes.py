from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flask import jsonify
from app.translate import translate
from app.main import bp
from app.main.forms import EditProfileForm, SearchForm
from ..models import User, Message, MessageType, Notification, Story
from .forms import StoryForm
from mongoengine.queryset.visitor import Q
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch
from elasticsearch_dsl import Q as EQ


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
    friends = current_user.friends
    friends = [User.objects(id=friend).first() for friend in friends]
    return render_template('index.html', title='Home Page', friends=friends)


@bp.route('/username/<username>')
@login_required
def user(username):
    user = User.objects(name=username).first()
    storys = Story.objects(author=user.id).order_by('-timestamp')
    return render_template('user.html', user=user, storys=storys)


@bp.route('/edit_profile')
@login_required
def edit_profile():
    return render_template('')


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


@bp.route('/write_story', methods=['GET', 'POST'])
@login_required
def write_story():
    form = StoryForm()
    if form.validate_on_submit():
        story = Story(title=form.title.data,
                      author=current_user.id,
                      body=form.body.data,
                      tags=form.tags.data)
        story.save()
        return redirect(url_for('main.storys'))
    return render_template('write_story.html', form=form)


@bp.route('/my_story')
@login_required
def storys():
    redirect = request.args.get('redirect')
    next = request.args.get('next')
    message = request.args.get('message')
    recipient = request.args.get('recipient')
    storys = Story.objects(author=current_user.id).order_by('-timestamp')
    return render_template('storys.html', storys=storys, redirect=redirect,
                           next=next, message=message, recipient=recipient)


@bp.route('/story_detail/<story_id>')
@login_required
def story_detail(story_id):
    story = Story.objects(id=story_id).first()
    return render_template('story_detail.html', story=story)


@bp.route('/ask_share', methods=['GET', 'POST'])
@login_required
def ask_share():
    name = request.form['username']
    print(name)
    user = User.objects(name=name).first()
    current_user.send_message(MessageType.AskShare.fullname, user.name)
    return jsonify({'status': 1, 'result': '发送成功'})


@bp.route('/open_heart', methods=['GET', 'POST'])
@login_required
def open_heart():
    name = request.form['username']
    user = User.objects(name=name).first()
    if user is None:
        return jsonify({'status': 0, 'result': '用户不存在或非好友'})
    else:
        if user.id in current_user.friends:
            if user.id not in current_user.beloved:
                current_user.send_message(MessageType.OpenHeart.fullname, user.name)
                current_user.update(push__beloved=user.id)
                current_user.save()
                user.update(push__be_beloved=current_user.id)
            return jsonify({'status': 1, 'result': '存在好友'})
        elif user.id == current_user.id:
            return jsonify({'status': 0, 'result': '这是你啊'})
        else:
            return jsonify({'status': 0, 'result': '用户不存在或非好友'})


@bp.route('/search')
@login_required
def search():
    user_id = request.args.get('user')
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '', type=str)
    if q == '':
        if not g.search_form.validate():
            return jsonify({'search_status': 0, "search_result": '输入无效'})
        else:
            q = g.search_form.q.data

    per_page = current_app.config['ITEMS_PER_PAGE']
    start = (page - 1) * per_page
    end = page * per_page
    print(start, end, per_page, page)
    eq = EQ('multi_match', query=q, fields=['title^3', 'body.cnw'])
    s = Search(using=current_app.elasticsearch, index='ruminate.story').filter('term', author=user_id).query(eq)
    response = s[start: end].execute()
    print("response")
    print(response)
    print('response.hits')
    print(response.hits)
    print('response.hits.hits')
    print(response.hits.hits)
    print('response.hits.total')
    print(response.hits.total)


    # storys = current_app.elasticsearch.search(index='ruminate.story',
    #                                           body={'query': {"bool": {"filter": {'term': {"author": user_id}},
    #                                                                    "must": {'multi_match': {'query': q, 'fields':
    #                                                                        ['title^3', 'body.cnw']}}}}}, sort='_score')
    # print(storys)
    # storys = Story.objects(author=user_id).search_text(q).order_by('$text_score').\
    #     paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    next_url = url_for('main.search', page=page + 1, q=q, user=user_id) if response.hits.total > end + 1 else None
    prev_url = url_for('main.search', page=page - 1, q=q, user=user_id) if page > 1 else None
    return render_template('storys.html', storys=response.hits,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/request_add_friend')
@login_required
def request_add_friend():
    username = request.args.get('username')
    current_user.send_message(MessageType.AddFriend.fullname, username)
    return jsonify({'result_status': 'sent'})


@bp.route('/share', methods=['GET', 'POST'])
@login_required
def share():
    story_title = request.form['title']
    story_url = request.form['url']

    recipient = request.form['recipient']
    message_id = request.form['message']

    if message_id != 'None':
        message = Message.objects(id=message_id).first()
        current_user.send_message(MessageType.Accept.fullname,
                              message.sender, {'url': story_url, 'title': story_title})
        message.update(set__dealed=True)
    else:
        recipient = User.objects(id=recipient).first()
        current_user.send_message(MessageType.Share.fullname, recipient.name,
                                  {'url': story_url, 'title': story_title})
    next = request.form['next']

    if next:
        return redirect(next)
    else:
        return redirect('main.index')


@bp.route('/agree_request')
@login_required
def agree_request():
    message_id = request.args.get('message_id')
    message = Message.objects(id=message_id).first()
    if message.content == MessageType.AddFriend.fullname:
        current_user.add_friend(message.sender)
    elif message.content == MessageType.AskShare.fullname:
        return redirect(url_for('main.storys', redirect=1,
                                next=url_for('main.messages'),
                                message=message_id))
    current_user.send_message(MessageType.Accept.fullname, message.sender)
    message.update(set__dealed=True)
    return jsonify({'result_status': 'sent'})


@bp.route('/refuse_request')
@login_required
def refuse_request():
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
        paginate(page=page, per_page=current_app.config['ITEMS_PER_PAGE'])
    next_url = url_for('main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since')
    notifications = Notification.objects(Q(timestamp__gt=since) & Q(recipient=current_user.name)).\
        order_by('timestamp')
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
