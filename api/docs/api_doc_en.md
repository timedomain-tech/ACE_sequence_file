## API Documentation

- [List of Singers](/api/docs/singer_info.md)
- [Request File Explanation](/docs/aces_file_en.md)

### 1. Synthesis API

- Request URL: `https://api-lora-us.svsbusiness.com/engine/api/engine/2b_compose`
- Request Method: `POST`

#### Request Parameters

| Parameter Name | Type   | Required | Description                                                                                                                             |
|----------------|--------|----------|-----------------------------------------------------------------------------------------------------------------------------------------|
| ace_token      | string | Yes      | Request token (Contact the liaison to obtain)                                                                                           |
| cooperator     | string | Yes      | Requester name (Contact the liaison to obtain)                                                                                          |
| mix_info       | string | No       | Parameters for mixed tuning, selecting the sources you want to mix. Must be on the singer list and feature description                  |
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
files = [('file', open(file_url, 'rb'))]
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

| Parameter Name | Type   | Description                                                         |
|----------------|--------|---------------------------------------------------------------------|
| audio          | string | Audio URL returned                                                  |
| pst            | number | Start time of the audio (calculated based on the notes in the file) |

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


### 2. Quota statistics

- Request：`https://gateway.svsbusiness.com/bill/quota`
- Request Method：`POST`

#### Request Parameters

| Parameter Name | Type   | Required | Description                                    |
|----------------|--------|----------|------------------------------------------------|
| ace_token      | string | Yes      | Request token (Contact the liaison to obtain)  |
| cooperator     | string | Yes      | Requester name (Contact the liaison to obtain) |


#### Request Example

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

#### Response Example

Data format explanation:

| Parameter Name       | Type   | Description                                                                                  |
|----------------------|--------|----------------------------------------------------------------------------------------------|
| service              | string | Business type, usually 2b                                                                    |
| flag                 | string | request flag                                                                                 |
| token                | string | request token                                                                                |
| charging_strategy    | number | billing strategy, where 1 is based on quantity billing; 2 is the hourly billing for packages |
| charging_expire_time | string | The timeout period for charging during package time                                          |
| billing_balance      | number | The total amount of billing based on quantity                                                |
| used_amount          | number | The amount already used by this token                                                        |
| qps                  | number | The limit on the number of tokens synthesized per second for this token                      |

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
### 3. Response Status Codes

| Status Code | Description                                                        |
|-------------|--------------------------------------------------------------------|
| 200         | Request successful                                                 |
| 503         | Number of concurrent requests exceeds limit                        |
| 400         | Request parameters do not conform to the documentation             |
| 429         | Invalid token                                                      |
| 402         | Synthesis engine exception, mostly due to extreme data in the file |
| 500         | Internal server error                                              |

### 4. Synthesis Constraints

| Constraint                        | Value                          | Description                                                   |
|-----------------------------------|--------------------------------|---------------------------------------------------------------|
| Limit on the number of pieces     | 4                              | The number of pieces in each request cannot exceed this limit |
| Limit on the length of each piece | 18s                            | The length of each piece cannot exceed this time limit        |
| Concurrent request limit          | 20                             | Exceeding this limit will result in a 503 error               |
| query per second for single token | default 3，contact us to adjust | Exceeding this limit will not be allowed                      |
