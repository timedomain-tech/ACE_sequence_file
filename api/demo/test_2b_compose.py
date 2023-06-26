import json

import requests

url = "https://api.svsbusiness.com/engine/api/engine/2b_compose"
mix_str = json.dumps({
    "duration": [[82, 0.7], [1, 0.3]],
    "pitch": [[82, 0.7], [1, 0.3]],
    "air": [[82, 0.7], [1, 0.3]],
    "falsetto": [[82, 0.7], [1, 0.3]],
    "tension": [[82, 0.7], [1, 0.3]],
    "energy": [[82, 0.7], [1, 0.3]],
    "mel": [[82, 0.7], [1, 0.3]],
})
file_url = "twinkletwinkle.aces"
files = [('file', open(file_url, 'rb')), ('file', open(file_url, 'rb'))]
ace_token = "XXXXXXXXXXXXXXXXXXX"
cooperator = "XXXXXXX"
data_dict = {
    "ace_token": ace_token,
    "cooperator": cooperator,
    "speaker_id": "3",
    "mix_info": mix_str,

}
resp = requests.request("POST", url=url, files=files, data=data_dict)
print(resp.text)
