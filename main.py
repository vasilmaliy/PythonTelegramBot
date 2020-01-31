import re
import os
import requests
import io
from flask import jsonify
from flask import Flask
from PIL import Image
import json
from flask import request
from flask_sslify import SSLify
app = Flask(__name__)
sslify = SSLify(app)

BOT_TOKEN = '758726920:AAExIAC13DJpo8JWZ0CSu3BbIjW_Arr8BLE'

def download_latest_photo(file_id, chat_id, choise, message_id):
    photo = get_json('getFile', params={'chat_id': chat_id, 'file_id': file_id})
    file_path = photo['result']['file_path']
    # Download photo
    file_name = os.path.basename(file_path)
    response = requests.get('https://api.telegram.org/file/bot%s/%s' % (BOT_TOKEN, file_path))
    #image = response.content
    image = Image.open(io.BytesIO(response.content))
    #image = image.crop((0, 0, image.size[0], image.size[0]*0.975))
    if choise == '1':
            image = image.rotate(90, expand=True)
            send_photo(chat_id, image)
    if choise == '2':
            image = image.rotate(-90, expand=True)
            send_photo(chat_id, image)
    if choise == '3':
            image = image.convert('1')
            send_photo(chat_id, image)
    if choise == '4':
            width = 2592
            hight = 3888
            image = image.resize((width, hight))
            send_photo(chat_id, image)
    if choise == '5':
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
            send_photo(chat_id, image)
    dellete_message(chat_id, message_id)

def send_photo(user_id, image):
    image_content = io.BytesIO()
    image.save(image_content, format='JPEG')
    image.name = 'unload.jpg'
    image_content.seek(0)
    data = {'chat_id': user_id}
    files = {'photo':  image_content} #Here, the ,"rb" thing
    requests.post('https://api.telegram.org/bot%s/%s' % (BOT_TOKEN, 'sendPhoto'), data=data, files=files)


@app.route('/', methods=['POST', 'GET'])
def send_button():
    if request.method == 'POST':
        r = request.get_json()
        try:
            chat_id = r['message']['chat']['id']
        except KeyError:
            chat_id = r['callback_query']['from']['id']

        try:
            if 'document' or 'photo' in  r['message']:
                if 'photo' in  r['message'] or r['message']['document']['mime_type'].split('/')[0] == 'image':
                    params = {'chat_id': chat_id,'text':"File successfully downloaded. Select what to do with the image: \n 1 - Rotating left an Image\n 2 - Rotating right an Image\n 3 - Black and white images\n 4 - Make 3x4\n 5 - Transposing an Image (mirror image)", 'reply_markup': json.dumps({'inline_keyboard': [[{'text': ' 1 ', 'callback_data': '1'},
                    {'text': ' 2 ', 'callback_data': '2'},{'text': ' 3 ', 'callback_data': '3'}, {'text': ' 4 ', 'callback_data': '4'},  {'text': ' 5 ', 'callback_data': '5'}]]})}
                    rect = requests.post('https://api.telegram.org/bot%s/%s' % (BOT_TOKEN, 'sendMessage'), data=params )#, files=files)
                    button_id = rect.json()['result']['message_id']
                    if 'document' in  r['message']:
                        file_id = r['message']['document']['thumb']['file_id']
                    elif "photo" in  r['message']:
                        file_id = r['message']['photo'][-1]['file_id']
                    try:
                        data =  json.load(open('answer.json'))
                    except:
                        data = [{'user_id':[]}]

                    if chat_id in data[0]['user_id']:
                        for user_id in data:
                            try:
                                if user_id['chat_id'] == chat_id:
                                    user_id['message'].append({'button_id': button_id,'file_id':file_id})
                            except:
                                pass
                    else:
                        data.append({'chat_id':chat_id, 'message':[{'button_id': button_id,'file_id':file_id}]})
                        data[0]['user_id'].append(chat_id)
                    with open('answer.json', 'w') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
        except KeyError :
            pass
        if 'callback_query' in r:
            message_id = r['callback_query']['message']['message_id']
            ans = r['callback_query']['data']
            data_file =  json.load(open('answer.json'))
            for user_id in data_file:
                if 'chat_id' in user_id:
                    if user_id['chat_id'] == chat_id:
                        for id in user_id['message']:
                            if id['button_id'] == message_id:
                                file_id = id['file_id']
                                button_id = id['button_id']
            try:
                download_latest_photo(file_id, chat_id = chat_id, choise = ans, message_id = button_id)
            except:
                pass
        if 'text' in r['message']:
            pattern= r'^/start|[^\w]/start\b'
            message = r['message']['text']
            answer = {'chat_id':chat_id, 'text':'Hello, I am PhotoBot. Simply send\nme an photo'}
            if re.search(pattern,message):
                requests.post('https://api.telegram.org/bot%s/%s' % (BOT_TOKEN, 'sendMessage'), json=answer)

        return jsonify(r)

    return '<h1>{}</h1>'.format('WORK')


def dellete_message(chat_id, message_id):
    params = {'chat_id': chat_id, 'message_id': message_id}
    resp = requests.Session()
    resp.get('https://api.telegram.org/bot%s/%s' % (BOT_TOKEN, 'deleteMessage'), data=params )
    data =  json.load(open('answer.json'))
    for all_user in data[1:]:
        if all_user['chat_id'] == chat_id:
            for message in all_user['message']:
                if message['button_id'] == message_id:
                    all_user['message'].remove(message)
                    with open('answer.json', 'w') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)



def get_json(method_name, *args, **kwargs):
    return make_request('get', method_name, *args, **kwargs)

def make_request(method, method_name, *args, **kwargs):
    response = getattr(requests, method)(
        'https://api.telegram.org/bot%s/%s' % (BOT_TOKEN, method_name),
        *args, **kwargs
    )
    if response.status_code > 200:
        raise DownloadError(response)
    return response.json()

class DownloadError(Exception):
    pass

if __name__ == '__main__':
    app.run()
