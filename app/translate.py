import requests
import hashlib
import urllib
import random
import json
from flask import current_app


def translate(text, source_language, dest_language):
    app_key = current_app.config['APP_KEY']
    secret_key = current_app.config['APP_SECRET_KEY']
    print(app_key, secret_key, text, source_language, dest_language)
    url = 'http://openapi.youdao.com/api'
    salt = random.randint(1, 65536)
    sign = app_key + text + str(salt) + secret_key
    m1 = hashlib.md5()
    m1.update(sign.encode(encoding='utf-8'))
    sign = m1.hexdigest()
    url = url + '?appKey=' + app_key + '&q=' + urllib.parse.quote(text) + '&from=' \
          + source_language + '&to=' + dest_language + '&salt=' + str(salt) \
          + '&sign=' + sign
    print(url)
    r = requests.get(url)
    print('response is:')
    print(r.content.decode('utf-8-sig'))
    if r.status_code != 200:
        return 'Error: the translation service failed.'
    return json.loads(r.content.decode('utf-8-sig'))['translation'][0]
