## API 说明文档

- [歌手信息列表](/api/docs/singer_info.md)
- [请求文件说明](/docs/aces_filie.md)

### 1. 合成接口

- 请求地址：`https://api.svsbusiness.com/engine/api/engine/2b_compose`
- 请求方式：`POST`

#### 请求参数说明

| 参数名称       | 参数类型   | 是否必填 | 参数描述                                         |
|------------|--------|------|----------------------------------------------|
| ace_token  | string | 是    | 请求token(联系对接人员获得)                            |
| cooperator | string | 是    | 请求方名称(联系对接人员获得)                              |
| mix_info   | string | 否    | 声线混合功能，可以选择不同的歌手进行声线融合，见下方说明      |
| speaker_id | string | 否    | 当mix_info未设置时有效。单一合成音源，参考歌手列表和特点说明，不填默认为"1"。 |

**注意**：每个请求文件对应的合成时长需小于18秒，且上传files不可超过4条

#### 声线混合功能说明
通过接口，您可以通过更细致的音色混合来获得想要的声线。您可以针对一下7个维度来控制不同的混合比例：

- <font color=#0099ff>duration</font> 主要控制咬字方式
- <font color=#0099ff>pitch</font> 主要控制唱法，也会影响部分咬字
- <font color=#0099ff>air</font> 控制演唱时的气息含量
- <font color=#0099ff>falsetto</font> 控制演唱时假声含量
- <font color=#0099ff>tension</font> 控制演唱时声带的紧张/松弛程度
- <font color=#0099ff>energy</font> 控制演唱时力量大小
- <font color=#0099ff>mel</font> 主要控制基础音色

为了更直观的理解音色混合，举个例子说明，目前有两位歌手id分别为1和82，如果我们想要在以上维度30%像歌手而70%像歌手82，那么我们可以通过如下的json字符串来创造一个mix_info从而实现这个功能：
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


#### 请求示例

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
file_xiaoxingxing = "/Users/root/demo/xiaoxingxing.aces"
file_twinkletwinkle = "/Users/root/demo/twinkletwinkle.aces"
files = [
    ('file', open(file_xiaoxingxing, 'rb')),
    ('file', open(file_twinkletwinkle, 'rb'))
]
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

| 参数名称  | 参数类型   | 参数描述                     |
|-------|--------|--------------------------|
| audio | string | 返回音频地址                   |
| pst   | number | 返回音频的开始时间(根据文件内note时间计算) |

```json
{
  "data": [
    {
      "audio": "http://engine-ai.oss-cn-beijing.aliyuncs.com/svs%2Fv5%2Fprod%2Fv3%2Fcompose%2Frun_piece_v2023_1681297283190164.ogg?OSSAccessKeyId=LTAI5tF1JfTsJxdtaAb4Scdw&Expires=1681470083&Signature=Hv8tHgYELsVKRvb9n4qjI4c53P4%3D",
      "pst": 1.334760032455542
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

### 2. websocket接口（不再支持）

websocket接口可以允许用户上传一个总长度5分钟之内且最后一个note结束时间小于10分钟的aces文件，在连接维持过程中会持续发送合成完成的音频给用户，直到最后一片合成结束服务端会主动断开连接。

- 请求地址：`https://api.svsbusiness.com/socket.io`
- 请求方式：`socket io`

#### 请求参数说明

| 参数名称       | 参数类型   | 是否必填 | 参数描述                                         |
|------------|--------|------|----------------------------------------------|
| ace_token  | string | 是    | 请求token(联系对接人员获得)                            |
| cooperator | string | 是    | 请求方名称(联系对接人员获得)                              |
| mix_info   | string | 否    | 可混合调参，选取想混合的音源进行混音操作。混音音源必须在歌手列表和特点说明        |
| speaker_id | string | 否    | 当mix_info未设置时有效。单一合成音源，参考歌手列表和特点说明，不填默认为"1"。 |
| file_date  | string | 是    | aces文件数据                                     |

#### 请求示例

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
        print('建立连接成功')
    else:
        print('建立连接失败')


@sio.on('connect_response', namespace='/api')
def on_connect_response(data):
    print(data)
    global connect_success
    if data.get('code') and data.get('code') != 200:
        connect_success = False
        sio.disconnect()
        print(f'连接异常：{data.get("data")} 主动断开连接')
    else:
        connect_success = True


@sio.on('disconnect', namespace='/api')
def on_disconnect():
    print('服务器断开连接')


@sio.on('message', namespace='/api')
def on_message(data):
    print('收到服务器消息: ', data)
    if data.get('code') and data.get('code') != 200:
        print(f'合成异常退出合成')
        sio.disconnect()


@sio.on('compose_response', namespace='/api')
def on_compose_response(data):
    print('收到合成消息: ', data)
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
```

#### 响应示例

| 参数名称     | 参数类型   | 参数描述                                                                                                        |
|----------|--------|-------------------------------------------------------------------------------------------------------------|
| code     | number | 返回的状态码，200表示正常返回。                                                                                           |
| error    | string | 如果接口返回错误，则会有一个错误信息字符串。                                                                                      |
| data     | list   | 音频数据，list中的结构为： ["audio" : {string}, "pst" : {number}]<br> audio: 返回音频地址 <br> pst: 返回音频的开始时间(根据文件内note时间计算) |
| finished | number | 表示数据是否传输完成，0表示未完成，1表示已完成。                                                                                   |
| progress | string | 表示数据传输的进度，可能是一个百分比字符串或者其它形式的表示。                                                                             |

连接成功

```json
{
  "code": 200,
  "error": "",
  "data": "connected",
  "timestamp": 1684835389559,
  "finished": 0
}
```

正常返回

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

异常返回

```json
{
  "code": 400,
  "error": "请求错误，cooperator必须存在",
  "data": "请求错误，cooperator必须存在",
  "timestamp": 1684835389559,
  "finished": 0
}
```

### 3. 调用额度统计

- 请求地址：`https://gateway.svsbusiness.com/bill/quota`
- 请求方式：`POST`

#### 请求参数说明

| 参数名称       | 参数类型   | 是否必填 | 参数描述                                         |
|------------|--------|------|----------------------------------------------|
| ace_token  | string | 是    | 请求token(联系对接人员获得)                            |
| cooperator | string | 是    | 请求方名称(联系对接人员获得)                              |


#### 请求示例

```python

import requests

if __name__ == '__main__':
    cooperator = "XXXXXXXXXX"
    ace_token = "XXXXXXXXXXXXXXXXXXXXXX"
    ip = "gateway.svsbusiness.com"
    url = "https://{}/bill/quota/".format(ip)
    data_dict = {
        "cooperator": cooperator,
        "ace_token": ace_token,
    }
    resp = requests.get(url=url, params=data_dict).text
    print(resp)
```

#### 响应示例

data格式说明：

| 参数名称  | 参数类型   | 参数描述               |
|---------|-----------|----------------------------------------|
| service | string | 业务类型，通常为2b         |
| flag | string | 请求方名称              |
| token | string | 请求token            |
| charging_strategy | number | 计费策略，1为按量计费；2为包时计费 |
| charging_expire_time  | string | 包时计费的超时时间          |
| billing_balance  | number | 按量计费的总额度           |
| used_amount  | number | 该token已经使用的额度      |
| qps   | number | 该token的合成每秒数量限制    |

```json
{
  "data": [
    {
      "service": "XXXXXXXXXXXX",
      "flag": "XXXXXXXXXXXXXXXXXXXXX",
      "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
      "charging_strategy": 2,
      "charging_expire_time": "2024-06-30T18:47:59",
      "billing_balance": 1000,
      "used_amount": 13,
      "qps": 3
    }
  ],
  "code": 200,
  "error": null,
  "timestamp": 1689241416585
}

```

### 4. 返回状态码

| 状态码 | 说明                     |
|-----|------------------------|
| 200 | 请求成功                   |
| 503 | 并行请求数量超过上限             |
| 400 | 请求参数不合文档规范             |
| 429 | token不合法               |
| 402 | 合成引擎异常，多数情况为合成文件包含极端数据 |
| 500 | 服务器内部未知错误              |

### 5. 合成限制条件

| 限制参数              | 数值        | 说明                                                    |
|-------------------|-----------|-------------------------------------------------------|
| 限制piece数量         | 4片        | 每次请求的piece数量不能超过限定数值                                  |
| 限制piece合成的长度      | 18s       | 每个piece的长度不能超过限定时间                                    |
| socket接口限制整歌合成的长度 | 300s/600s | 最后一个note的结束时间减去第一个note的开始时间小于300s；最后一个note的结束时间小于600s |
| 并行请求数量            | 20        | 并行请求数量超过限度后会直接返回503                                   |
| 每个token的qps限制     | 默认3，可联系调整 | 针对每个token限制对算力的占用                                     |
