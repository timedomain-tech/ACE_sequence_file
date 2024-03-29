## API Documentation

- [List of Singers](/api/docs/singer_info.md)
- [Request File Explanation](/docs/aces_file.md)

### 1. Synthesis API

- Request URL: `https://api.svsbusiness.com/engine/api/engine/2b_compose`
- Request Method: `POST`

#### Request Parameters

| Parameter Name | Type   | Required | Description                                                                 |
| -------------- | ------ | -------- | --------------------------------------------------------------------------- |
| ace_token      | string | Yes      | Request token (Contact the liaison to obtain)                                |
| cooperator     | string | Yes      | Requester name (Contact the liaison to obtain)                               |
| mix_info       | string | No       | Parameters for mixed tuning, selecting the sources you want to mix. Must be on the singer list and feature description |
| speaker_id     | string | No       | Effective when `mix_info` is not set. Single source of synthesis, refer to the list of singers and feature description. Default is "1". |

**Note**: Each request file must have a synthesis duration shorter than 18 seconds, and the number of uploaded files should not exceed 4.

#### Voice Blending Feature Explanation
Through the interface, you can achieve the desired voice by more nuanced tone blending. You can control the different blending ratios based on the following 7 dimensions:

- <font color=#0099ff>duration</font> mainly controls the articulation
- <font color=#0099ff>pitch</font> mainly controls the singing style, and it also affects some aspects of articulation
- <font color=#0099ff>air</font> controls the amount of breathiness in singing
- <font color=#0099ff>falsetto</font> controls the amount of falsetto in singing
- <font color=#0099ff>tension</font> controls the tension/relaxation of the vocal cords during singing
- <font color=#0099ff>energy</font> controls the intensity of singing
- <font color=#0099ff>mel</font> primarily controls the basic timbre

To understand the tone blending more intuitively, here's an example: currently, there are two singers with IDs 1 and 82. If we want to sound 30% like singer 1 and 70% like singer 82 in the above dimensions, then we can create a mix_info with the following JSON string to achieve this function:
```python
{
    "duration": [[82, 0.7], [1, 0.3]],
    "pitch": [[82, 0.7], [1, 0.3]],
    "air": [[82, 0.7], [1, 0.3]],
    "falsetto": [[82, 0.7], [1, 0.3]],
    "tension": [[82, 0.7], [1, 0.3]],
    "energy": [[82, 0.7], [1, 0.3]],
    "mel": [[82, 0.7], [1, 0.3]],
}
```

#### Request Example

```python
import requests
import json

url = "XXXXXXXXXXX"
mix_str = json.dumps({
    "duration": [[82, 0.7], [1, 0.3]],
    "pitch": [[82, 0.7], [1, 0.3]],
    "air": [[82, 0.7], [1, 0.3]],
    "falsetto": [[82, 0.7], [1, 0.3]],
    "tension": [[82, 0.7], [1, 0.3]],
    "energy": [[82, 0.7], [1, 0.3]],
    "mel": [[82, 0.7], [1, 0.3]],
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

#### Response Example

Data format explanation:

| Parameter Name | Type    | Description                              |
| -------------- | ------- | ---------------------------------------- |
| audio          | string  | Audio URL returned                       |
| pst            | number  | Start time of the audio (calculated based on the notes in the file) |

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

### 2. Websocket API （Deprecated）

The Websocket API allows users to upload an aces file with a total length of less than 5 minutes and the last note ending time less than 10 minutes. During the connection, synthesized audio will be continuously sent to the user until the last piece is synthesized, after which the server will disconnect.

- Request URL: `https://api.svsbusiness.com/socket.io`
- Request Method: `socket io`

#### Request Parameters

| Parameter Name | Type   | Required | Description                                                                 |
| -------------- | ------ | -------- | --------------------------------------------------------------------------- |
| ace_token      | string | Yes      | Request token (Contact the liaison to obtain)                                |
| cooperator     | string | Yes      | Requester name (Contact the liaison to obtain)                               |
| mix_info       | string | No       | Voice blending feature, which allows the selection of different singers for voice fusion, as explained below. |
| speaker_id     | string | No       | Effective when `mix_info` is not set. Single source of synthesis, refer to the list of singers and feature description. Default is "1". |
| file_data      | string | Yes      | Data of the aces file                                                        |

#### Request Example

```python
# coding=utf-8
import socketio
import json

url = "https://api.svsbusiness.com/socket.io/"
ace_token = "XXXXXXXXXXXXXXXXX"
cooperator = "XXXXXXXXX"
speaker_id = "3"
file_url = "path_to_aces"

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

connect_success = False


@sio.on('connect', namespace='/api')
def on_connect():
    if connect_success:
        print('connection success')
    else:
        print('connection failed')


@sio.on('connect_response', namespace='/api')
def on_connect_response(data):
    print(data)
    global connect_success
    if data.get('code') and data.get('code') != 200:
        connect_success = False
        sio.disconnect()
        print(f'connection error：{data.get("data")} disconnected')
    else:
        connect_success = True


@sio.on('disconnect', namespace='/api')
def on_disconnect():
    print('server disconnected')


@sio.on('message', namespace='/api')
def on_message(data):
    print('message received: ', data)
    if data.get('code') and data.get('code') != 200:
        print(f'synthesis failed and exit')
        sio.disconnect()


@sio.on('compose_response', namespace='/api')
def on_compose_response(data):
    print('synthesis response: ', data)
    if data.get('code') and data.get('code') == 200:
        print(f'synthesis progress：{data.get("progress")}')
    if data.get('finished') and data.get('finished') == 1:
        print(f'synthesis end')
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
```

#### Response Example

| Parameter Name | Type    | Description                                                                          |
| -------------- | ------- | ------------------------------------------------------------------------------------ |
| code           | number  | Status code returned, 200 indicates normal return.                                   |
| error          | string  | If the API returns an error, there will be an error message string.                  |
| data           | list    | Audio data, the structure within the list is: ["audio": {string}, "pst": {number}]   |
| finished       | number  | Indicates whether the data transmission is complete, 0 for incomplete, 1 for complete |
| progress       | string  | Indicates the progress of data transmission, could be a percentage string or other forms. |

connection established
```json
{
  "code": 200,
  "error": "",
  "data": "connected",
  "timestamp": 1684835389559,
  "finished": 0
}
```

request success

```json
{
  "code": 200,
  "error": "",
  "data": [
    {
      "audio": "http://engine-ai.oss-cn-beijing.aliyuncs.com/svs%2Fv5%2Fprod%2Fv3%2Fcompose%2Frun_piece_v2023ckpt_1684835388316222.ogg?OSSAccessKeyId=LTAI5tF1JfTsJxdtaAb4Scdw&Expires=1685008188&Signature=n%2FIMCi25xDzMuWmx3h8wF51N1rc%3D",
      "pst": 2.803809523809524
    }
  ],
  "finished": 0,
  "progress": "1/1"
}
```

request failed

```json
{
  "code": 400,
  "error": "request error，cooperator has to be filled",
  "data": "request error，cooperator has to be filled",
  "timestamp": 1684835389559,
  "finished": 0
}
```

### 3. Response Status Codes

| Status Code | Description                                                       |
| ----------- | ----------------------------------------------------------------- |
| 200         | Request successful                                                |
| 503         | Number of concurrent requests exceeds limit                       |
| 400         | Request parameters do not conform to the documentation            |
| 429         | Invalid token                                                     |
| 402         | Synthesis engine exception, mostly due to extreme data in the file |
| 500         | Internal server error                                             |

### 4. Synthesis Constraints

| Constraint               | Value      | Description                                                                       |
| ------------------------ | ---------- | --------------------------------------------------------------------------------- |
| Limit on the number of pieces | 4        | The number of pieces in each request cannot exceed this limit                     |
| Limit on the length of each piece | 18s    | The length of each piece cannot exceed this time limit                            |
| Socket API length constraint | 300s/600s | The last note's end time minus the first note's start time must be less than 300s; the last note's end time must be less than 600s |
| Concurrent request limit  | 20        | Exceeding this limit will result in a