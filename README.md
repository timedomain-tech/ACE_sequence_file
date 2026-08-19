<h1 align="center">ACE Sequence File Format (aces)</h1>

<a href="README_ZH.md"><img src="https://img.shields.io/badge/文档-中文版-white.svg" alt="ZH doc"/></a>
<img src="https://img.shields.io/static/v1?label=license&message=MIT&color=white&style=flat" alt="License"/>
<br><br>
<b>Open-source file format designed for high-quality, customizable singing voice synthesis.

</p>

## Introduction
Aces is a file format specifically designed for vocal synthesis that is simple, open, user-friendly, and powerful. It has been widely used in our vocal synthesis API to meet the vast majority of user requirements. It offers high extensibility and is also highly readable.

## Features
- Easy-to-read, human-editable JSON-based format
- Multi-language support
- Introduce piece parameters that allow for the use of curves to represent pitch and energy across the entire piece


## Quick Start

Four steps to your first line of singing.

### 1. Get your credentials

Once your service is activated, your contact provides two values: `cooperator` (your caller name)
and `ace_token` (your request token). They are left blank in the sample below — fill them in and
it runs.

### 2. Pick a singer

Singer ids are listed in [Singer Information](/api/docs/singer_info.md). The sample uses `82`.

### 3. Prepare an aces file

The quickest option is `examples/xiaoxingxing_syllable.aces` — Chinese lyrics written as pinyin
syllables, so you do not have to look up phonemes. If you have a MIDI file, see
"Generating aces from MIDI" below.

### 4. Submit and download the audio

```python
import json, requests

URL = "https://api-lora-us.svsbusiness.com/engine/api/engine/2b_compose"  # use the address assigned to you
COOPERATOR = ""   # fill in after activation
ACE_TOKEN = ""    # fill in after activation

resp = requests.post(
    URL,
    files=[("file", open("examples/xiaoxingxing_syllable.aces", "rb"))],
    data={"cooperator": COOPERATOR, "ace_token": ACE_TOKEN, "speaker_id": "82"},
    timeout=300,
)
body = resp.json()
assert body["code"] == 200, body["error"]

for piece in body["data"]:
    audio = requests.get(piece["audio"], timeout=120).content
    name = "piece_{}.{}".format(piece["sequence_index"], piece["output_format_suffix"])
    open(name, "wb").write(audio)
    print(name, "starts at", piece["pst"], "seconds")
```

`pst` is the absolute time, in seconds on your original project timeline, of sample 0 of that
audio — place the audio at that time and it lines up with your backing track. The full interface
reference is in [api_doc](/api/docs/api_doc_en.md).

## File Format Specification
For specifics regarding the file format please refer to  [File Description](docs/aces_file_en.md). Every example under `./examples/` can be submitted to the synthesis API as-is:

| File                          | What it demonstrates                                                     |
|-------------------------------|--------------------------------------------------------------------------|
| `xiaoxingxing_syllable.aces`  | The simplest form: Chinese syllable (pinyin) input, no phonemes needed    |
| `xiaoxingxing.aces`           | Chinese phoneme input, with multi-segment `pitch.user` editing the melody |
| `Iwannafly.aces`              | English phoneme input, including `br` (breath) and `slur` notes           |
| `はるをあい cl するひと_2b.aces`       | Japanese phoneme input                                                   |
| `vibrato_example.aces`        | Controlled vibrato via the `user` + `delta` layers of `pitch`             |
| `param_example.aces`          | `energy` / `air` / `falsetto` / `tension` parameter curves                |


## Generating aces from MIDI

`api/demo/midi2aces.py` converts a MIDI file with lyrics into aces and synthesizes it directly.
The repository ships `红昭愿.mid` as an example:

```bash
cd api/demo
pip install -r requirements.txt
python midi2aces.py          # put your credentials in acel_svs_example.py
```

What the MIDI must provide:

- Track 0 must contain a `set_tempo` event; the script uses it to convert ticks to absolute seconds
- Lyrics go in `lyrics` meta events and **must be pinyin** (the script submits them as `syllable`,
  so Chinese only for now)
- For a syllable held across several notes, write the lyric as `-` and the script emits a `slur` note
- The number of lyric events should match the number of notes; notes without a lyric fall back to `la`
- With multiple tracks the first one containing notes is used; pass
  `midi2json(path, json_track_id=N)` to choose another

The script also does three things for you:

1. Drops notes shorter than 0.02s (too short to hold their phonemes)
2. Splits at gaps longer than 1.2s, then halves any piece still longer than 90s
3. Submits each piece and stitches the results into one wav using each piece's `pst`

With the bundled `红昭愿.mid`: 232 notes spanning 139.3 seconds, split into 4 pieces.
Note the script sends **one request per piece**, each consuming one credit; to spend fewer
credits, submit several pieces in a single request (see section 4 of
[api_doc](/api/docs/api_doc_en.md)).

## Contributing

Contributions and suggestions for modification are welcome. You can open an issue or send an email to sean.z@timedomain.ai.


## Extra
We offer an API service for singing voice synthesis, please refer to the [api_doc](/api/docs/api_doc_en.md). If you're interested in testing or collaborating with us, please send an email to sean.z@timedomain.ai

## License

This project is licensed under the MIT License - see the [LICENCE](LICENCE) file for details.
