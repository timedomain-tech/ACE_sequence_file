## API Documentation

- [List of Singers](/api/docs/singer_info.md)
- [Request File Explanation](/docs/aces_file_en.md)

### 1. Synthesis API

- Request Method: `POST`
- Request URL (use the one assigned to you during onboarding):
  - Overseas: `https://api-lora-us.svsbusiness.com/engine/api/engine/2b_compose`
  - China: `https://api.svsbusiness.com/engine/api/engine/2b_compose`

> **This document describes the behaviour of the current engine version, which is fully rolled out
> on the overseas node.** The China node will be upgraded separately; until then, the items marked
> "current engine" in this document (blending using `mel` only, which `piece_params` layers take
> effect, `consonant_time_*` no longer being used) still behave the earlier way there.
> Contact your onboarding representative if you are unsure which version your node runs.

#### Request Parameters

| Parameter Name | Type   | Required | Description                                                                                                                             |
|----------------|--------|----------|-----------------------------------------------------------------------------------------------------------------------------------------|
| ace_token      | string | Yes      | Request token (Contact the liaison to obtain)                                                                                           |
| cooperator     | string | Yes      | Requester name (Contact the liaison to obtain)                                                                                          |
| mix_info       | string | No       | Parameters for mixed tuning, selecting the sources you want to mix. Must be on the singer list and feature description                  |
| speaker_id     | string | No       | Effective when `mix_info` is not set. Single source of synthesis, refer to the list of singers and feature description. Default is "1". |
| extra          | string | No       | Users can input any string, which will be filled into the returned data structure                                                       |
| file           | file   | Yes      | The ACES file itself; the multipart field name must be `file`. Repeat the field to submit several pieces in one request                  |

**Note**: Each request file must have a synthesis duration of at most 90 seconds, and the number of uploaded files should not exceed 3.

#### Voice Blending Feature Explanation

You can blend the timbres of several singers to obtain the voice you want. The blending ratio is
given by the `mel` dimension; each item is `[singer_id, weight]` and the weights are normalised
automatically (you do not have to make them sum to 1).

For example, to sound 70% like singer 82 and 30% like singer 1:

```python
{
    "mel": [[82, 0.7], [1, 0.3]]
}
```

> **`mel` is the only blending dimension.**
>
> Earlier versions let you set a different blending ratio for each of the 7 dimensions
> `duration` / `pitch` / `air` / `falsetto` / `tension` / `energy` / `mel`. The current engine
> uses a single unified timbre representation with only one voice vector, so **only `mel`
> is kept**; supplying any of the other six returns `400`.
>
> Why an error rather than silently ignoring it: silence would hand you a `200` and audio
> with the wrong timbre, with no way to tell from the response what went wrong.
>
> - If you only need a single singer, just use the `speaker_id` parameter — no `mix_info` needed.
> - To control **how much** breath / falsetto / tension / intensity the voice has, use the
>   `air` / `falsetto` / `tension` / `energy` curves in `piece_params` inside the ACES file
>   (see [ACES file specification](/docs/aces_file_en.md), section 3). Note this is not the
>   same as "borrowing another singer's characteristic in that dimension" — the former draws
>   a 0~1 intensity curve, the latter is not supported by the current engine.

#### Request Example

```python
import requests
import json

url = "https://api-lora-us.svsbusiness.com/engine/api/engine/2b_compose"

# Voice blending (optional). Only the mel dimension takes effect; weights are normalised.
mix_str = json.dumps({
    "mel": [[82, 0.7], [1, 0.3]],
})
extra_str = json.dumps(
    {"request_id": "abcd1234"}
)
# Submit several pieces at once by repeating ('file', ...)
files = [
    ('file', open("/path/to/piece_1.aces", 'rb')),
    ('file', open("/path/to/piece_2.aces", 'rb')),
]
data_dict = {
    "ace_token": "XXXXXXXXXXXXXXXX",
    "cooperator": "XXXXXXXXXXXX",
    # Single singer via speaker_id (see the singer list); mix_info takes precedence if both are given
    "speaker_id": "82",
    "mix_info": mix_str,
    "extra": extra_str,
}
resp = requests.request("POST", url=url, files=files, data=data_dict)
```

#### Response Example

Data format explanation:

| Parameter Name       | Type   | Description                                                                                      |
|----------------------|--------|--------------------------------------------------------------------------------------------------|
| audio                | string | Pre-signed download URL for the audio; GET it directly, no auth header needed                    |
| pst                  | number | Absolute time (seconds) of **sample 0** of this audio on the original project timeline           |
| output_format_suffix | string | Audio file suffix, `ogg` by default                                                              |
| sequence_index       | number | Index of the corresponding uploaded file, starting at 0, matching the order of the `file` fields  |

**Audio format**: Ogg/Opus container by default, 44.1kHz, about 64kbps.

**The download URL is valid for 48 hours** (172800 seconds); fetch and store the audio within that
window. The service does **not** cache synthesis results — resubmitting the same request
synthesises again (and bills again), and the audio is not guaranteed to be byte-identical.

**Submitting several pieces**: repeat the multipart `file` field; the returned `data` array maps to
the submission order via `sequence_index`. If **any single piece fails the whole request fails**
(not billed, and successfully rendered pieces are not returned) — retry the request as a whole.

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
  "timestamp": 1681297283983,
  "extra": "{\"request_id\": \"abcd1234\"}"

}
```


### 2. Quota statistics

- Request：`https://gateway-us.svsbusiness.com/bill/quota`
- Request Method：`GET`

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
    ip = "gateway-us.svsbusiness.com"
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

**Billing granularity**

- One **successful** synthesis request consumes exactly **1 credit**, regardless of the number of
  pieces submitted, the duration of each piece, or how many singers are blended.
- Requests returning a non-200 code are **not billed** (400 / 429 / 453 / 503 consume no credit).
- `charging_strategy = 1` (quantity-based): each successful request increments `used_amount` by 1;
  once it reaches `billing_balance` the synthesis endpoint returns 400.
- `charging_strategy = 2` (time-package): credits are not decremented per call; only
  `charging_expire_time` is checked, after which the endpoint returns 400.

There are therefore two ways to reduce credit consumption, in order of importance:

1. **First, fit the content into as few files as possible.** The per-file limit is 90 seconds
   (see "4. Synthesis Constraints"). Do not slice content up to satisfy the earlier 18-second
   limit — the engine infers on a fixed-length canvas, so synthesizing 5 seconds and 90 seconds
   cost about the same, and slicing only makes the same audio go through inference repeatedly.
2. **Then batch several files into one request** (up to 3). The trade-off is that a single
   failing piece requires retrying the whole request.

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

| Status Code | Description                                                                          |
|-------------|--------------------------------------------------------------------------------------|
| 200         | Request successful                                                                   |
| 400         | Request parameters or file content do not conform to the documentation; insufficient quota; qps limit exceeded |
| 429         | Invalid token (cannot be decrypted)                                                  |
| 453         | Data validation failed (the file contains extreme data) or synthesis engine exception |
| 503         | Number of concurrent requests exceeds limit                                          |

The HTTP status code always matches the `code` field in the response body. On failure `data`
is `null` and the reason is in `error`, which usually contains the timestamp of the offending
note and the field name so you can locate the problem.

> **Exception**: `503` is returned by the gateway before the request reaches the service, so its
> body is **not** JSON (it may be HTML). Check the HTTP status code before parsing the body —
> do not assume `resp.json()` works for 503.

> The `402` code from earlier documentation is no longer used; data-related errors now
> return `453`.

### 4. Synthesis Constraints

| Constraint                        | Value                          | Description                                                   |
|-----------------------------------|--------------------------------|---------------------------------------------------------------|
| Limit on the number of pieces     | 3                              | The number of pieces in each request cannot exceed this limit |
| Limit on the length of each piece | 90s                            | Measured as the notes time span; a 1200-phoneme cap also applies, see [ACES file specification](/docs/aces_file_en.md) 5.8 |
| Concurrent request limit          | 20                             | **Node-level** cap shared by all customers; the gateway returns 503 beyond it — back off and retry |
| Queries per second per token      | 3 by default, contact us to adjust | Enforced as an average over a **60-second rolling window** (rejected when requests in the window exceed qps x 60); returns 400 |
