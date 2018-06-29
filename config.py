import os
from dotenv import load_dotenv
base_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(base_dir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'DEFAULT_SECRET_KEY'

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['zhangyonguu@gmail.com']

    ITEMS_PER_PAGE = 3
    LANGUAGES = ['en', 'zh']

    APP_KEY = os.environ.get('APP_KEY')
    APP_SECRET_KEY = os.environ.get('APP_SECRET_KEY')

    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

    MONGODB_DB = 'ruminate'
