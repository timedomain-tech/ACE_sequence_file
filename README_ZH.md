<h1 align="center">ACE Sequence File Format (aces)</h1>

<a href="README.md"><img src="https://img.shields.io/badge/document-English-white.svg" alt="Eng doc"/></a>
<img src="https://img.shields.io/static/v1?label=license&message=MIT&color=white&style=flat" alt="License"/>
<br><br>
<b>一个为高质量、可定制的歌声合成而设计的开源文件格式。

</b></p>

## 简介
Aces 是一个专为歌声合成设计的文件格式，它简单、开放、用户友好、并且功能强大。它已经被广泛用于我们的歌声合成API，并且满足绝大多数用户需求。该格式具有高度的可扩展性，并且有很高的可读性。

## 特点
- 基于JSON格式，易于阅读编辑
- 多语言支持
- 引入片段参数，允许使用曲线来表示整个片段的音高和能量


## 快速开始

四步听到第一句歌声。

### 1. 取得凭据

开通服务后，对接人员会提供两个值：`cooperator`（请求方名称）与 `ace_token`（请求令牌）。
下面示例中留空，填入即可运行。

### 2. 选一个歌手

歌手 id 见 [歌手信息列表](/api/docs/singer_info.md)。示例用 `82`。

### 3. 准备一个 aces 文件

最省事的办法是直接用 `examples/xiaoxingxing_syllable.aces` —— 中文拼音歌词，不必查音素。
手里是 MIDI 的话见下面「从 MIDI 生成 aces」。

### 4. 提交并下载音频

```python
import json, requests

URL = "https://api-lora-us.svsbusiness.com/engine/api/engine/2b_compose"  # 请用对接时分配给您的地址
COOPERATOR = ""   # 开通后填入
ACE_TOKEN = ""    # 开通后填入

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
    print(name, "起始时间", piece["pst"], "秒")
```

`pst` 是这段音频第 0 个采样点在原工程时间轴上的绝对秒数——按它把音频摆到时间轴上，
就能与伴奏对齐。接口的完整说明见 [api_doc](/api/docs/api_doc.md)。

## 文件格式规范
有关文件格式的具体信息，请参考 [文件描述](docs/aces_file.md)。`./examples/` 目录下的示例都可以直接提交给合成接口：

| 文件                            | 演示内容                                            |
|-------------------------------|-------------------------------------------------|
| `xiaoxingxing_syllable.aces`  | 最简形态：中文音节（拼音）输入，不必自己查音素                         |
| `xiaoxingxing.aces`           | 中文音素输入，并用多段 `pitch.user` 编辑整句音高                 |
| `Iwannafly.aces`              | 英文音素输入，含 `br`（换气）与 `slur`（延音）音符                 |
| `はるをあい cl するひと_2b.aces`       | 日文音素输入                                          |
| `vibrato_example.aces`        | 用 `pitch` 的 `user` + `delta` 做可控颤音              |
| `param_example.aces`          | `energy` / `air` / `falsetto` / `tension` 参数曲线  |


## 歌词转音素

中文不需要额外工具——直接在音符上写 `syllable`（拼音或单个汉字），服务端会转换。
**英语 / 日语 / 西班牙语必须自己给 `phone`**，`api/demo/lyrics2phone.py` 就是干这个的：

```bash
cd api/demo
pip install -r requirements.txt        # 英语需要 cmudict；日语与西语无依赖
python lyrics2phone.py en  "twinkle twinkle little star"
python lyrics2phone.py jp  "さくら さくら"
python lyrics2phone.py spa "camino de la luz"
```

输出是逐音符的音素列表，一个音节一个音符，直接填进 `notes` 即可：

```
[["t","w","ih","ng"], ["k","ah","l"], ["l","ih"], ["t","ah","l"], ["s","t","aa","r"]]
```

加 `--aces out.aces` 可以直接生成一个可提交的 ACES 骨架（时值与音高是等分占位值，
请按您的曲谱调整）。

各语言的做法与边界：

| 语言 | 做法 | 主要限制 |
|----|----|----|
| 英语 `en` | CMUdict 查词 → ARPAbet → 引擎音素（1:1），按最大起首原则切音节 | 词典查不到的词（新词、专名、数字）会报错而不是猜，需自己用 `extra_dict` 补 |
| 日语 `jp` | 假名 → 罗马字音节 → 引擎自带词典（内嵌五十音表，无依赖） | 只认假名，汉字请先注音；助词 `は`/`へ` 按字面读 |
| 西语 `spa` | 正字法规则 → 音素，按重音与强弱元音判定二合元音 | 固定 seseo（`z`/`ce`/`ci` 一律读 `s`），不支持半岛 distinción 与阿根廷读法 |

> **查不到的词一律报错，不按拼写猜。** 猜错的发音客户很难排查，报错至少能立刻定位。
> 需要自己补词时传 `extra_dict={"word": ["音素", ...]}`。
>
> 音素表以引擎为准，工具产出的音素已逐一核对在表内。完整的已知取舍见脚本内的
> `CAVEATS` 说明。

## 从 MIDI 生成 aces

`api/demo/midi2aces.py` 能把带歌词的 MIDI 转成 aces 并直接合成。仓库自带 `红昭愿.mid`：

```bash
cd api/demo
pip install -r requirements.txt
python midi2aces.py          # 凭据填在 acel_svs_example.py 里
```

对 MIDI 的要求：

- 轨道 0 必须含 `set_tempo` 事件，脚本据此把 tick 换算成绝对秒
- 歌词写在 `lyrics` 元事件里，且**必须是拼音**（脚本按 `syllable` 提交，因此目前只支持中文）
- 拖腔（一个字唱过多个音）把歌词写成 `-`，脚本会转成 `slur` 音符
- 歌词事件数量应与音符数一致；没有对应歌词的音符会退化成 `la`
- 多轨时默认取第一个含音符的轨道，需要指定用 `midi2json(path, json_track_id=N)`

脚本还会替你做三件事：

1. 丢掉短于 0.02s 的音符（太短装不下音素）
2. 在超过 1.2s 的空隙处切片，仍超过 90s 的片段再对半切
3. 逐片提交，并按各片的 `pst` 拼成一个完整 wav

以自带的 `红昭愿.mid` 为例：232 个音符、跨度 139.3 秒，切成 4 片。
注意脚本是**一片一个请求**，各扣 1 个额度；若要省额度，可改为一次请求提交多片
（上限见 [api_doc](/api/docs/api_doc.md) 第 4 节）。

## 贡献

欢迎提出贡献和修改建议。你可以开启一个问题或发送电子邮件到 sean.z@timedomain.ai。

## 额外信息
我们提供歌声合成的 API 服务，请参考 [api_doc](/api/docs/api_doc.md)。如果您有兴趣测试或与我们合作，请发送电子邮件到 sean.z@timedomain.ai。

## 许可证

该项目在 MIT 许可证下授权 - 有关详细信息，请参阅 [LICENCE](LICENCE) 文件。