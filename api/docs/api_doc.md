## API 说明文档

- [歌手信息列表](/api/docs/singer_info.md)
- [请求文件说明](/docs/aces_file.md)

### 1. 合成接口

- 请求方式：`POST`
- 请求地址（请使用对接时分配给您的那一个）：
  - 中国：`https://api.svsbusiness.com/engine/api/engine/2b_compose`
  - 海外：`https://api-lora-us.svsbusiness.com/engine/api/engine/2b_compose`

> 本文档描述**海外节点**的行为。中国节点所用的引擎版本请与对接人员确认。

#### 请求参数说明

| 参数名称       | 参数类型   | 是否必填 | 参数描述                                         |
|------------|--------|------|----------------------------------------------|
| ace_token  | string | 是    | 请求token(联系对接人员获得)                            |
| cooperator | string | 是    | 请求方名称(联系对接人员获得)                              |
| mix_info   | string | 否    | 声线混合功能，可以选择不同的歌手进行声线融合，见下方说明                 |
| speaker_id | string | 否    | 当mix_info未设置时有效。单一合成音源，参考歌手列表和特点说明，不填默认为"1"。 |
| extra      | string | 否    | 用户可以填入任意字符串，该字符串会填写到返回数据结构中                  |
| file       | file   | 是    | ACES 文件本身，multipart 字段名固定为 `file`。可重复该字段一次提交多个片段，见下方"多片提交" |

**注意**：每个请求文件对应的合成时长需不大于90秒，且上传files不可超过3条

#### 声线混合功能说明

通过接口，您可以混合多位歌手的音色来获得想要的声线。混合比例由 `mel` 维度给出，
数组中每一项是 `[歌手id, 权重]`，权重会自动归一化（无需自行保证和为 1）。

例如，想要 70% 像歌手 82、30% 像歌手 1：

```python
{
    "mel": [[82, 0.7], [1, 0.3]]
}
```

> `mel` 是 `mix_info` 里唯一的键，其余键一律返回 `400`。
>
> - 只需要单一歌手时，直接用 `speaker_id` 参数即可，无需构造 `mix_info`。
> - 声线混合调整的是**音色本身**。若想控制气息 / 假声 / 紧张度 / 力量的**强弱**，
>   那是另一件事，用 ACES 文件里 `piece_params` 的对应曲线
>   （见[请求文件说明](/docs/aces_file.md) 第 3 节）。


#### 请求示例

```python
import requests
import json

url = "https://api-lora-us.svsbusiness.com/engine/api/engine/2b_compose"

# 声线混合(可选)。只有 mel 维度生效, 权重自动归一化。
mix_str = json.dumps({
    "mel": [[82, 0.7], [1, 0.3]],
})
extra_str = json.dumps(
    {"request_id": "abcd1234"}
)

# 一次可提交多个片段: 重复 ('file', ...) 即可
files = [
    ('file', open("/path/to/piece_1.aces", 'rb')),
    ('file', open("/path/to/piece_2.aces", 'rb')),
]
data_dict = {
    "ace_token": "XXXXXXXXXXXXXXXX",
    "cooperator": "XXXXXXXXXXXX",
    # 单一歌手用 speaker_id(歌手id见歌手列表); 若同时给了 mix_info, 则以 mix_info 为准
    "speaker_id": "82",
    "mix_info": mix_str,
    "extra": extra_str,
}
resp = requests.request("POST", url=url, files=files, data=data_dict)
print(resp.status_code, resp.text)
```

#### 响应示例

data格式说明：

| 参数名称                  | 参数类型   | 参数描述                                       |
|-----------------------|--------|--------------------------------------------|
| audio                 | string | 返回音频的预签名下载地址，可直接 GET，无需鉴权头                 |
| pst                   | number | 该片音频**第 0 个采样点**在原工程时间轴上的绝对秒数（秒）            |
| output_format_suffix  | string | 音频文件后缀，默认 `ogg`                            |
| sequence_index        | number | 该片对应上传文件的顺序，从 0 开始，与 `file` 的提交顺序一一对应       |

**音频规格**：默认 Ogg/Opus 容器，**48kHz**，VBR 目标码率 64kbps（长音频实测约 70kbps）。

> 引擎内部按 44.1kHz 合成，但 Opus 原生只支持 48kHz，编码时会重采样到 48kHz，
> 因此下载到的文件采样率是 48000。如需 44.1kHz 素材请在您这一侧重采样。

**下载地址有效期 48 小时**（172800 秒），请在有效期内取回并自行存储。
服务端**不缓存合成结果**，同样的请求重新提交会重新合成（并重新计费），音频不保证逐字节相同。

**多片提交**：重复 multipart 的 `file` 字段即可一次提交多个片段，返回的 `data` 数组按
`sequence_index` 与提交顺序对应。一次请求中**任意一片失败则整个请求失败**（不计费，
已合成的片也不返回），需整体重试。

```json
{
  "data": [
    {
      "audio": "https://<bucket>.<endpoint>/svs/v5/pro/v3/compose/run_piece_mamba_1681297283190164.ogg?<signature>",
      "output_format_suffix": "ogg",
      "pst": 1.334760032455542,
      "sequence_index": 0
    },
    {
      "audio": "https://<bucket>.<endpoint>/svs/v5/pro/v3/compose/run_piece_mamba_1681297283776864.ogg?<signature>",
      "output_format_suffix": "ogg",
      "pst": 2.803809523809524,
      "sequence_index": 1
    }
  ],
  "code": 200,
  "error": null,
  "timestamp": 1681297283983,
  "extra": "{\"request_id\": \"abcd1234\"}"
}
```


### 2. 调用额度统计

- 请求地址：`https://gateway.svsbusiness.com/bill/quota`
- 请求方式：`GET`

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

| 参数名称                 | 参数类型   | 参数描述               |
|----------------------|--------|--------------------|
| service              | string | 业务类型，通常为2b         |
| flag                 | string | 请求方名称              |
| token                | string | 请求token            |
| charging_strategy    | number | 计费策略，1为按量计费；2为包时计费 |
| charging_expire_time | string | 包时计费的超时时间          |
| billing_balance      | number | 按量计费的总额度           |
| used_amount          | number | 该token已经使用的额度      |
| qps                  | number | 该token的合成每秒数量限制    |

**计费口径**

- 一次**成功**的合成请求固定消耗 **1 个额度**，与本次提交的片数、每片时长、混合的歌手数量都无关。
- 返回非 200 的请求**不计费**（400 / 429 / 453 / 503 均不消耗额度）。
- `charging_strategy = 1`（按量计费）：每次成功请求 `used_amount` 加 1，达到 `billing_balance` 后合成接口返回 400。
- `charging_strategy = 2`（包时计费）：不按次扣减，只校验 `charging_expire_time`，超期后返回 400。

因此降低额度消耗的做法有两层，按优先级：

1. **先把内容装进尽量少的文件**。单文件上限是 90 秒（见"4. 合成限制条件"）。
   引擎按固定长度画布推理，合成 5 秒与合成 90 秒消耗的算力基本相同，
   人为切碎只会让同一段音频被反复推理。
2. **再把多个文件合并到一次请求**（最多 3 个）。代价是任一片失败需要整体重试。

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

### 3. 返回状态码

| 状态码 | 说明                                                            |
|-----|---------------------------------------------------------------|
| 200 | 请求成功                                                          |
| 400 | 请求参数或文件内容不合文档规范；额度不足；超过 qps 限制                                |
| 429 | token 不合法（无法解密）                                               |
| 453 | 数据体检未通过（合成文件包含极端数据）或合成引擎异常                                    |
| 503 | 并行请求数量超过上限                                                    |

HTTP 状态码与响应体中的 `code` 字段始终一致。失败时 `data` 为 `null`，
具体原因在 `error` 字段中，通常包含出问题的音符时间与字段名，可据此定位。

> **例外**：`503` 由网关在请求进入服务之前直接拒绝，响应体不是 JSON（可能是 HTML）。
> 客户端解析响应前请先判断 HTTP 状态码，不要假定 503 也能 `resp.json()`。


### 4. 合成限制条件

| 限制参数              | 数值        | 说明                                                    |
|-------------------|-----------|-------------------------------------------------------|
| 限制piece数量         | 3片        | 每次请求的piece数量不能超过限定数值                                  |
| 限制piece合成的长度      | 90s       | 按 notes 时间跨度计算；另有音素总数 1200 的上限，见[请求文件说明](/docs/aces_file.md) 5.8 |
| 并行请求数量            | 20        | **节点级**上限(所有客户共享)，超过后网关直接返回 503，需退避重试              |
| 每个token的qps限制     | 默认3，可联系调整 | 按 **60 秒滚动窗口的平均值**判定(窗口内请求数 > qps×60 即拒绝)，超限返回 400 |
