from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, \
    ValidationError, TextAreaField, SelectMultipleField, SelectField
from wtforms.validators import DataRequired, Length
from flask import request

tag_choices = [('1', '家庭'),
               ('2', '为人'),
               ('3', '认知'),
               ('4', '生活'),
               ('5', '处事'),
               ('6', '育儿')]


class StoryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=140)])
    tags = SelectMultipleField('Tags', choices=tag_choices,
                               validators=[DataRequired()])
    body = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('发表')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('please input a different username')


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super().__init__(*args, **kwargs)
