import json

import requests

EndPoint_China = "https://api.svsbusiness.com/engine/api/engine/2b_compose"
EndPoint_US = "https://api-lora-us.svsbusiness.com/engine/api/engine/2b_compose"

EndPoint = EndPoint_China

ACE_TOEKN = "xxxxxx"
FLAG = "xxxx"


# mix_str = json.dumps({
#     "duration": [[82, 0.7], [1, 0.3]],
#     "pitch": [[82, 0.7], [1, 0.3]],
#     "air": [[82, 0.7], [1, 0.3]],
#     "falsetto": [[82, 0.7], [1, 0.3]],
#     "tension": [[82, 0.7], [1, 0.3]],
#     "energy": [[82, 0.7], [1, 0.3]],
#     "mel": [[82, 0.7], [1, 0.3]],
# })

file_url = "examples/Iwannafly.aces"
files = [('file', open(file_url, 'rb'))]

ace_token = ACE_TOEKN
cooperator = FLAG

data_dict = {
    "ace_token": ace_token,
    "cooperator": cooperator,
    "speaker_id": "82",
    "mix_info": None,  # or you can also use mix_str

}
resp = requests.request("POST", url=EndPoint, files=files, data=data_dict)
print(resp.text)
