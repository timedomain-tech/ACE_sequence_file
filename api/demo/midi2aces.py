# 此文档展示了如何将midi文件转换为aces文件， 目前仅支持拼音歌词

import mido
import os
from acel_svs_example import rendering_ace_list


# 多轨默认获取第一个有效轨道
def midi2json(mid_path, json_track_id=0):

    mid = mido.MidiFile(mid_path)
    tempo = -1
 
    for item in mid.tracks[0]:
        if item.type == 'set_tempo':
            tempo = item.tempo
    if tempo == -1:
        print("tempo not found!")
        return
 
    bpm = int(60000000/tempo  + 0.5 ) 

    note_json_tracks = []

    for track_id, track in enumerate(mid.tracks):
        # if track_id == 0:
        #     continue

        lyric_list = []
        note_list = []
        time_sum = 0
        
        for item_id, item in enumerate(track):
            if item.is_meta:
                if item.type == 'lyrics':
                    
                    word = item.text
                    lyric_list.append(word)
                    
                    # lyric 事件的时间也要算进去，后续所有的都是相对时间
                    time_sum = time_sum + item.time

            else:  
                if item.type == 'note_on':
                    time_sum = time_sum + item.time
                elif item.type == 'note_off':
                    start_time = time_sum
                    time_sum = time_sum + item.time
                    abs_start_time = mido.tick2second(start_time, mid.ticks_per_beat, tempo)
                    abs_end_time = mido.tick2second(time_sum, mid.ticks_per_beat, tempo)
                    note = dict()
                    note['start_time'] = abs_start_time
                    note['end_time'] = abs_end_time
                    note['pitch'] = item.note
                    note_list.append(note)

        if len(lyric_list) != len(note_list):
            print("lyrics and notes not match!")

        note_json = []
        for i in range(len(note_list)):
            note_item = note_list[i]
            lyric = "la"
            if i < len(lyric_list):
                lyric = lyric_list[i]

            note_item["word"] = lyric

            note_json.append(note_item)
        if len(note_json) > 0:
            note_json_tracks.append(note_json)

    if len(note_json_tracks) == 0:
        print("no tracks found!")
        return

    if json_track_id >= len(note_json_tracks):
        print("track id out of range!")
        return
    
    return note_json_tracks[json_track_id]


def midi2aces(mid_path):
    
    note_json = midi2json(mid_path)

    ace_note_list = []
    for note in note_json:
        print(note)

        start_time = note["start_time"]
        end_time = note["end_time"]
        pitch = note["pitch"]
        word = note["word"]


        ace_note = dict()
        ace_note.update({"start_time": start_time})
        ace_note.update({"end_time": end_time})  
        ace_note.update({"pitch": pitch })

        if word == "-":
            ace_note.update({"type": "slur"})
        else:
            ace_note.update({"language": "ch"})
            ace_note.update({"type": "general"})
            ace_note.update({"syllable": word})

        ace_note_list.append(ace_note)
    
    aces = {}
    aces.update({"version": 1.1})
    aces.update({"notes": ace_note_list})
   
    return aces


def cut_aces(aces):

    version = aces["version"]
    original_note_list = aces["notes"]

    MAX_LENGTH = 18  # Maximum length is 18 seconds
    CORASE_SPACE = 1.2  # 空隙大于1.2s则分割

    # 先过滤一下超长的note
    filtered_list = []
    for note in original_note_list:
        if note["end_time"] - note["start_time"] > MAX_LENGTH:
            print("note too long, ignore!")
        else:
            filtered_list.append(note)
    
    # note之间大于1.2s直接切分，返回分割后的list
    def corase_cut(list_to_cut):
        corase_result = []
        temp_list = []
        for i in range(len(list_to_cut)):
            note = list_to_cut[i]
            if i == 0:
                temp_list.append(note)
            else:
                last_note = list_to_cut[i-1]
                if note["start_time"] - last_note["end_time"] > CORASE_SPACE:
                    corase_result.append(temp_list)
                    temp_list = []
                temp_list.append(note)

        return corase_result
         
    
    # 寻找中间位置切分，返回分割后的list
    def simple_cut(list_to_cut):
        middle_time = (float(list_to_cut[0]["start_time"]) + float(list_to_cut[-1]["end_time"]))/2
        
        cut_index = 0
        distance = 1000000
        for i in range(len(list_to_cut)):
            note = list_to_cut[i]
            start_time = float(note["start_time"])
            if abs(start_time - middle_time) < distance:
                distance = abs(start_time - middle_time)
                cut_index = i
        
        half_1 = list_to_cut[:cut_index]
        half_2 = list_to_cut[cut_index:]

        return [half_1, half_2]
    

    # 最简实现，list生成长度大于18s则从中间切分，建议根据自己的业务需求来切分
    # todo 切分后添加pad_notes 加上效果更佳
    def fine_cut(list_to_cut, max_length):
        list_end = float(list_to_cut[-1].get("end_time"))
        list_start = float(list_to_cut[0].get("start_time"))
        list_length = list_end - list_start
        if list_length <= max_length:
            return [list_to_cut]
        else:
            halves = simple_cut(list_to_cut)
            result = []
            for half in halves:
                if half: 
                    result.extend(fine_cut(half, max_length))
            return result


    corase_list = corase_cut(filtered_list)
    fine_list = []
    for corase in corase_list:
        fine_list.extend(fine_cut(corase, MAX_LENGTH))

    aces_list = []
    for piece in fine_list:
        aces_piece = aces.copy()
        aces_piece.update({"notes": piece})
        aces_piece.update({"version": version})
        aces_list.append(aces_piece)
    
    return aces_list


if __name__ == "__main__":

    current_file_path = os.path.abspath(__file__)
    current_folder_path = os.path.dirname(current_file_path)

    mid_path = os.path.join(current_folder_path, "红昭愿.mid")

    long_aces = midi2aces(mid_path)
    cutted_aces = cut_aces(long_aces)

    rendering_ace_list(cutted_aces, "midi_test_output.wav")


    