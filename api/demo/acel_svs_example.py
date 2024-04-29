import json
import requests

import soundfile as sf
from io import BytesIO


EndPoint_China = "https://api.svsbusiness.com/engine/api/engine/2b_compose"
EndPoint_US = "https://api-lora-us.svsbusiness.com/engine/api/engine/2b_compose"

EndPoint = EndPoint_China

ACE_TOEKN = "xxxxx"
FLAG = "xxxx"

 
def download_and_open_audio(url):
 
    response = requests.get(url)
    response.raise_for_status()   

    with BytesIO(response.content) as file:
        data, samplerate = sf.read(file)
        return data, samplerate

def one_piece_compose(aces_json):

    # mix_str = json.dumps({
    #     "duration": [[82, 0.7], [1, 0.3]],
    #     "pitch": [[82, 0.7], [1, 0.3]],
    #     "air": [[82, 0.7], [1, 0.3]],
    #     "falsetto": [[82, 0.7], [1, 0.3]],
    #     "tension": [[82, 0.7], [1, 0.3]],
    #     "energy": [[82, 0.7], [1, 0.3]],
    #     "mel": [[82, 0.7], [1, 0.3]],
    # })

    with open('./temp_file.aces', 'w') as f:
        f.write(json.dumps(aces_json))
    files = [('file', open('./temp_file.aces', 'rb'))]
 
    ace_token = ACE_TOEKN
    cooperator = FLAG
    data_dict = {
        "ace_token": ace_token,
        "cooperator": cooperator,
        "speaker_id": "3",
        "mix_info": None,

    }
    resp = requests.request("POST", url=EndPoint, files=files, data=data_dict)
    
    result = json.loads(resp.text)

    print(result)
    if result.get('code') == 200:
        print('Compose success')
        audio_url = result.get('data')[0].get('audio')
        audio_data, samplerate = download_and_open_audio(audio_url)
        pst = result.get('data')[0].get('pst')
    else:
        print('Compose failed')
        print(result)
    
    return pst, audio_data, samplerate


if __name__ == '__main__':
     
    acel = json.loads(open('api/demo/test.acel', 'r').read())
    
    vocal_offset = None
    concat_audio = []
    for aces in acel:
        pst, audio_data, samplerate = one_piece_compose(aces)

        if vocal_offset is None:
            vocal_offset = pst
            concat_audio.extend(audio_data)
        else:
            start_index = int((pst-vocal_offset) * samplerate)

            if(len(concat_audio) < start_index):
                concat_audio.extend([0] * (start_index - len(concat_audio)))
            else:
                concat_audio = concat_audio[:start_index]
            
            concat_audio.extend(audio_data)

    sf.write('api/demo/concat.wav', concat_audio, samplerate)

    print("In relation to the accompaniment, the vocal offset is: ", vocal_offset)


            
        