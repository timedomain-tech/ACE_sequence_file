# coding=utf-8
import json

import socketio

url = "https://api.svsbusiness.com/socket.io/"
ace_token = "XXXXXXXXXXXXXXXXX"
cooperator = "XXXXXx"
speaker_id = "3"
file_url = "twinkletwinkle.aces"

with open(file_url, 'r') as load_f:
    aces_file = json.load(load_f)

mix_str = json.dumps({
    "duration": [[82, 0.7], [1, 0.3]],
    "pitch": [[82, 0.7], [1, 0.3]],
    "air": [[82, 0.7], [1, 0.3]],
    "falsetto": [[82, 0.7], [1, 0.3]],
    "tension": [[82, 0.7], [1, 0.3]],
    "energy": [[82, 0.7], [1, 0.3]],
    "mel": [[82, 0.7], [1, 0.3]],
})

sio = socketio.Client()


@sio.on('connect_response', namespace='/api')
def on_connect_response(data):
    print(data)
    if data.get('code') and data.get('code') != 200:
        sio.disconnect()
        print(f'连接异常：{data.get("data")} 主动断开连接')
    else:
        print('建立连接成功')


@sio.on('disconnect', namespace='/api')
def on_disconnect():
    print('断开连接')


@sio.on('message', namespace='/api')
def on_message(data):
    print('收到服务器消息: ', data)
    if data.get('code') and data.get('code') != 200:
        print(f'合成异常退出合成')
        sio.disconnect()


@sio.on('compose_response', namespace='/api')
def on_compose_response(data):
    print('收到合成: ', data)
    if data.get('code') and data.get('code') == 200:
        print(f'合成进度：{data.get("progress")}')
    if data.get('finished') and data.get('finished') == 1:
        print(f'本次合成结束')
        sio.disconnect()


sio.connect(url,
            auth={
                "ace_token": ace_token,
            },
            namespaces='/api')

socket_data = {
    'ace_token': ace_token,
    'cooperator': cooperator,
    'speaker_id': speaker_id,
    'mix_info': mix_str,
    'file_date': aces_file,
}
sio.emit('compose', json.dumps(socket_data), namespace='/api')
sio.wait()
