## API 说明文档

- [歌手信息列表](/api/docs/singer_info.md)
- [请求文件说明](/docs/aces_filie.md)

### 1. 合成接口

- 请求地址：`https://api.svsbusiness.com/engine/api/engine/2b_compose`
- 请求方式：`POST`

#### 请求参数说明

参数名称 | 参数类型 | 是否必填 | 参数描述
--------|----------|---------|--------
ace_token | string | 是 | 请求token(联系对接人员获得)
cooperator | string | 是 | 请求方名称(联系对接人员获得)
mix_info | string | 否 | 可混合调参，选取想混合的音源进行混音操作。混音音源必须在歌手列表和特点说明
speaker_id | string | 否 | 当mix_info未设置时有效。单一合成音源，参考歌手列表和特点说明，不填默认为"1"。

**注意**：每个请求文件对应的合成时长需小于15秒，且上传files不可超过4条

#### 请求示例

```python
url = url_string
mix_str = json.dumps({
    "duration": [[82, 0.7],[1, 0.3]],
    "pitch": [[82, 0.7],[1, 0.3]],
    "air": [[82, 0.7],[1, 0.3]],
    "falsetto": [[82, 0.7],[1, 0.3]],
    "tension": [[82, 0.7],[1, 0.3]],
    "energy": [[82, 0.7],[1, 0.3]],
    "mel": [[82, 0.7],[1, 0.3]],
})
file_url = "/Users/root/demo/xiaoxingxing.aces"
files = [('file', open(file_url, 'rb')), ('file', open(file_url, 'rb'))]
data_dict = {
    "ace_token": "XXXXXXXXXXXXXXXX",
    "cooperator": "XXXXXXXXXXXX",
    "speaker_id": "3",
    "mix_info": mix_str,
    
}
resp = requests.request("POST", url=url, files=files, data=data_dict)
```

#### 响应示例

data格式说明：

参数名称 | 参数类型 | 参数描述
--------|----------|--------
audio | string | 返回音频地址
pst | number | 返回音频的开始时间(根据文件内note时间计算)

```json
{
  "data": [
    {
      "audio": "http://engine-ai.oss-cn-beijing.aliyuncs.com/svs%2Fv5%2Fprod%2Fv3%2Fcompose%2Frun_piece_v2023_1681297283190164.ogg?OSSAccessKeyId=LTAI5tF1JfTsJxdtaAb4Scdw&Expires=1681470083&Signature=Hv8tHgYELsVKRvb9n4qjI4c53P4%3D",
      "pst": 2.803809523809524
    },
    {
      "audio": "http://engine-ai.oss-cn-beijing.aliyuncs.com/svs%2Fv5%2Fprod%2Fv3%2Fcompose%2Frun_piece_v2023_1681297283776864.ogg?OSSAccessKeyId=LTAI5tF1JfTsJxdtaAb4Scdw&Expires=1681470083&Signature=YFWau7XPHMNwF2vlC%2BVa0M%2FuNI0%3D",
      "pst": 2.803809523809524
    }
  ],
  "code": 200,
  "error": null,
  "timestamp": 1681297283983
}
```

### 2. websocket接口

websocket接口可以允许用户上传一个总长度5分钟之内且最后一个note结束时间小于10分钟的aces文件，在连接维持过程中会持续发送合成完成的音频给用户，直到最后一片合成结束服务端会主动断开连接。

- 请求地址：`https://api.svsbusiness.com/socket.io`
- 请求方式：`socket io`

#### 请求参数说明

参数名称 | 参数类型 | 是否必填 | 参数描述
--------|----------|---------|--------
ace_token | string | 是 | 请求token(联系对接人员获得)
cooperator | string | 是 | 请求方名称(联系对接人员获得)
mix_info | string | 否 | 可混合调参，选取想混合的音源进行混音操作。混音音源必须在歌手列表和特点说明
speaker_id | string | 否 | 当mix_info未设置时有效。单一合成音源，参考歌手列表和特点说明，不填默认为"1"。

#### 请求示例

```python

import time
import socketio

sio = socketio.Client()


@sio.on('disconnect')
def disconnect():
    print('disconnect ', sio.sid)


@sio.on('connect')
def on_connect():
    print("I'm connected to the /compose namespace!")


@sio.on('message')
def on_message(data):
    print('收到服务器消息: ', data)

mix_str = json.dumps({
    "duration": [[82, 0.7], [1, 0.3]],
    "pitch": [[82, 0.7], [1, 0.3]],
    "air": [[82, 0.7], [1, 0.3]],
    "falsetto": [[82, 0.7], [1, 0.3]],
    "tension": [[82, 0.7], [1, 0.3]],
    "energy": [[82, 0.7], [1, 0.3]],
    "mel": [[82, 0.7], [1, 0.3]],
})
file_url = "/path_to_ace/tts_request_ace1.ace"
with open(file_url, 'r') as load_f:
    file = json.load(load_f)
data_dict = {
    "ace_token": "XXXXXXXXXXXXXXXX",
    "cooperator": "XXXXXXXXXXXX",
    "speaker_id": "3",
    "mix_info": mix_str,
    "file_date": file,
}


data = json.dumps(data_dict)
print('listen task channel')
ip = "api.svsbusiness.com"
sio.connect(f'https://{ip}/socket.io',
            auth={
                "ace_token": "XXXXXXXXXX",
            })
sio.emit('compose', data)
print("消息发送成功！")

sio.wait()
sleep(5)
sio.disconnect()
```

#### 响应示例

data格式说明：

参数名称 | 参数类型 | 参数描述
--------|----------|--------
audio | string | 返回音频地址
pst | number | 返回音频的开始时间(根据文件内note时间计算)

```json
{
  "data": [
    {
      "audio": "http://engine-ai.oss-cn-beijing.aliyuncs.com/svs%2Fv5%2Fprod%2Fv3%2Fcompose%2Frun_piece_v2023_1681297283190164.ogg?OSSAccessKeyId=LTAI5tF1JfTsJxdtaAb4Scdw&Expires=1681470083&Signature=Hv8tHgYELsVKRvb9n4qjI4c53P4%3D",
      "pst": 2.803809523809524
    },
    {
      "audio": "http://engine-ai.oss-cn-beijing.aliyuncs.com/svs%2Fv5%2Fprod%2Fv3%2Fcompose%2Frun_piece_v2023_1681297283776864.ogg?OSSAccessKeyId=LTAI5tF1JfTsJxdtaAb4Scdw&Expires=1681470083&Signature=YFWau7XPHMNwF2vlC%2BVa0M%2FuNI0%3D",
      "pst": 2.803809523809524
    }
  ],
  "code": 200,
  "error": null,
  "timestamp": 1681297283983
}