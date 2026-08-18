import json
import os

import requests

EndPoint_China = "https://api.svsbusiness.com/engine/api/engine/2b_compose"
EndPoint_US = "https://api-lora-us.svsbusiness.com/engine/api/engine/2b_compose"

EndPoint = EndPoint_China

ACE_TOEKN = "xxxxx"
FLAG = "xxxx"


# 声线混合: 只有 mel 维度会生效, 权重会自动归一化。详见 api_doc 的说明。
# mix_str = json.dumps({
#     "mel": [[82, 0.7], [1, 0.3]],
# })

# 按脚本自身位置定位样例文件, 这样在任意工作目录下都能运行
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
file_url = os.path.join(REPO_ROOT, "examples", "Iwannafly.aces")
files = [('file', open(file_url, 'rb'))]

ace_token = ACE_TOEKN
cooperator = FLAG
extra_str = json.dumps(
    {"request_id": "abcd1234"}
)
data_dict = {
    "ace_token": ace_token,
    "cooperator": cooperator,
    "speaker_id": "82",
    "mix_info": None,  # or you can also use mix_str
    "extra": extra_str,

}
resp = requests.request("POST", url=EndPoint, files=files, data=data_dict)
print(resp.text)
