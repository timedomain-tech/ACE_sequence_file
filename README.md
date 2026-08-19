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


## Contributing

Contributions and suggestions for modification are welcome. You can open an issue or send an email to sean.z@timedomain.ai.


## Extra
We offer an API service for singing voice synthesis, please refer to the [api_doc](/api/docs/api_doc_en.md). If you're interested in testing or collaborating with us, please send an email to sean.z@timedomain.ai

## License

This project is licensed under the MIT License - see the [LICENCE](LICENCE) file for details.
