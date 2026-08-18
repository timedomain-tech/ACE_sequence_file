# ACES 文件说明 v1.0

## 1. 总览

| 字段名          | 字段类型   | 是否必传 | 说明                     |
|--------------|--------|------|------------------------|
| version      | number | 是    | 版本信息                   |
| notes        | Array  | 是    | 音符序列，详见 `note` 对象      |
| piece_params | Object | 否    | 见 `piece_params` 对象    |
| pad          | Object | 否    | 当前片段头尾pad音符，见 `pad` 对象 |
| random_seed  | number | 否    | 随机种子数，用来对音色进行随机微调      |

*示例：*

```
{
    "version": 1.0, 
    "notes":[NOTE],
    "piece_params": PIECE_PARAMS,
    "pad": PAD
}
```

## 2. NOTE：音符表示

| 字段名        | 字段类型   | 是否必传           | 说明                        |
|------------|--------|----------------|---------------------------|
| start_time | number | 是              | 音符开始时间，以秒为单位              |
| end_time   | number | 是              | 音符结束时间，以秒为单位              |
| type       | string | 否，默认为"general" | 音符类型，详见音符类型说明             |
| pitch      | number | type 为 general 时必传 | 音高值，详见音高值说明。`slur` 可省略（继承前一个发音音符的音高）；`br`/`sp` 忽略该字段 |
| language   | string | 否，默认为ch        | 音符语言，取值见 5.3（`ch`/`en`/`jp`/`spa`，另支持 `ko`/`fr`/`it`/`pt`） |
| phone      | Array  | 否              | 当前note音素列表，详见音素说明         |
| syllable   | string | 否              | 当前note音节，详见音节说明           |

### 2.1 音符类型说明

可选音符类型有:

+ "general"  一般发音音符
+ "br" 呼吸音符
+ "sp" 静音音符，静音音符可以不传
+ "slur" 延音音符，延音音符前面必须要存在发音音符

### 2.2 音高值说明

440hz标准音对应音高值为69

### 2.3 音素说明

每个"general"类型的note内必须包含且只能包含一个元音：具体音素信息请参考：https://github.com/timedomain-tech/ACE_phonemes

### 2.4 音节说明

**仅中文（`language` 为 `ch`）支持音节输入**，可以直接给拼音（如 `"la"`、`"shan"`）
或单个汉字（如 `"星"`），服务会自动转换成音素，无需传 `phone`。

- 汉字为多音字、或拼音不合法时会返回 `400`，请改用拼音或直接给 `phone`。
- **其它语言（英语/日语/西班牙语等）请直接给 `phone` 列表**。这些语言不做音节转换，
  只传 `syllable` 会得到一个默认发音（不是您期望的歌词）。

*示例：*

```
{
    "start_time": 1.0,
    "end_time": 2.0,
    "type": "general",
    "pitch":65,
    "language":"ch",
    "syllable": "la"
}
```

```
{
    "start_time": 1.4,
    "end_time": 2.8,
    "type": "general",
    "pitch":65,
    "language":"en",
    "phone":[
        "d",
        "r",
        "iy"
    ]
}
```

## 3. PIECE_PARAMS: 片段参数(实验性功能)

| 字段名      | 字段类型   | 是否必传 | 说明            |
|----------|--------|------|---------------|
| pitch    | Object | 否    | 详见 `pitch` 对象 |
| energy   | Object | 否    | 详见 `param` 对象 |
| air      | Object | 否    | 详见 `param` 对象，气息含量 |
| falsetto | Object | 否    | 详见 `param` 对象，假声含量 |
| tension  | Object | 否    | 详见 `param` 对象，声带紧张度 |

> 当前引擎生效范围：`pitch` 的 `user` / `delta` 层，以及
> `energy` / `air` / `falsetto` / `tension` 的 `user` 层。
> 其余层（如 `envelope`）会被忽略，见 3.2。

可直接提交的样例：

- `examples/vibrato_example.aces` —— `pitch` 的 `user` + `delta`（颤音）
- `examples/param_example.aces` —— `energy` / `air` / `falsetto` / `tension` 的 `user` 曲线

### 3.1 PITCH: 音高表示

| 字段名   | 字段类型               | 是否必传 | 说明                                        |
|-------|--------------------|------|-------------------------------------------|
| user  | Array(PIECE_VALUE) | 否    | 用户自定义音高线, 见 `piece_value` 对象，取值范围30-90    |
| delta | Array(PIECE_VALUE) | 否    | 用户自定义音高线偏移, 见 `piece_value` 对象，取值范围[-4,4] |

> **`delta` 必须与 `user` 同时给出。** `delta` 是叠加在 `user` 音高线之上的修正量，
> 只给 `delta` 而不给 `user` 时该层会被忽略（不会报错，但颤音等效果不会生效）。
> 未被 `user` 覆盖的时间段由模型自行预测音高。

> **`user` 覆盖到的时间段，音高完全由您接管**，未覆盖处才交给模型预测。因此建议让
> `user` 覆盖整个音符：如果只覆盖颤音所在的后半段，模型预测段与 `user` 段的交界处
> 会出现接近一个半音的音高台阶（实测约 100 cent），听上去是一声突跳。

> **长音默认就带模型生成的自然颤音**（实测约 5~6Hz、深度约 ±0.5 半音）。只有需要精确
> 控制颤音的起振时刻、频率和深度时才需要传 `pitch`；只是想"有颤音"的话不传即可。
> 这也意味着：只给 `delta` 而漏了 `user` 时，您听到的颤音是模型的默认行为，
> 并不是您写入的那条曲线。

`examples/vibrato_example.aces` 是一个完整例子：一个 4.75~6.00s 的音符，`user` 用
25 个点铺一条恒为 63 的水平音高线覆盖整个音符，`delta` 从 5.29s 起叠加一条 6Hz 的
正弦，于是听感上是"先直音、后颤音"。为了让效果足够明显，该样例的颤音深度取到了
±1.8 半音，实际歌唱通常在 ±0.3~0.7 半音。

示例：

```
{
    "user": [PIECE_VALUE]
    "delta": [PIECE_VALUE]
}
```

### 3.2 PARAM: 参数表示

| 字段名      | 字段类型                | 是否必传 | 说明                                       |
|----------|---------------------|------|------------------------------------------|
| user     | Array(PIECE_VALUE)  | 否    | 自定义参数线, 见 `piece_value` 对象， 取值范围根据参数类型决定 |
| envelope | Array(PIECE_VALUE)  | 否    | 参数包络线，**当前引擎已不支持，传入会被忽略**                |

`user` 层的取值范围：`energy` 为 0~5.2，`air` / `falsetto` / `tension` 为 0~1。
数组中的负值表示"该处不指定，交给模型预测"。

四个参数在听感上的作用：`energy` 音量与力度；`air` 气声成分；`falsetto` 假声含量
（会削弱高次谐波，声音变柔）；`tension` 声带紧张度（拉高亮度，四者中效果最明显）。

`examples/param_example.aces` 演示了这四条曲线的写法：4 个同音高的长音，每个音符上
只给一个参数做"低→高"的渐变，方便逐个试听单一参数的作用。

示例：

```
{
    "user": [PIECE_VALUE],
    "envelope": [PIECE_VALUE]
}
```

### 3.3 PIECE_VALUE: 片段取值表示

| 字段名              | 字段类型   | 是否必传 | 说明                           |
|------------------|--------|------|------------------------------|
| start_time       | number | 是    | values数组真实起始时间               |
| hop_time         | number | 是    | values数组中每两个数据帧之间的间隔         |
| values           | Array  | 是    | 取值数组，根据不同的值类型具有不同的取值范围       |

该段覆盖的时间范围是 `start_time` 到 `start_time + len(values) * hop_time`。

> `values` 会被重采样到引擎内部帧率（约 5.8ms 一帧），因此 `hop_time` 由您自行决定：
> 变化平缓的曲线用粗栅格（如 0.05s）就够了，不必逐帧给点。同一个 `piece_params`
> 下的不同层（如 `pitch` 的 `user` 与 `delta`）也不要求使用相同的 `hop_time`，
> 各层按各自的 `start_time` / `hop_time` 独立对齐到时间轴后再叠加。

示例：

```
{
    "start_time": 0.01,
    "hop_time": 0.01,
    "values": [
        0.3,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,

    ]
}
```

## 4. PAD:

| 字段名   | 字段类型   | 是否必传 | 说明           |
|-------|--------|------|--------------|
| begin | Object | 否    | 详见 `note` 对象 |
| end   | Object | 否    | 详见 `note` 对象 |

说明：  
pad属于额外信息，一般情况下可不填。当ACES文件用于深度学习模型合成歌声时，可以加入此片段外前后的音符信息，用来获得更佳的合成效果

> **当前引擎的实际行为**：`pad` 完全可以不传 —— 服务会根据 notes 的首尾时间自动补齐，
> 并按内部帧栅格对齐。若传了 `pad`，其中的 `type`（`sp` / `br` / `sil` 等）会被采用，
> 但 `start_time` / `end_time` 会被重新计算。
> 部分早期客户端使用 `pad_notes` 作为字段名，同样被接受。

示例：

```
{
    "begin": NOTE,
    "end": NOTE
}
```

## 5. note规则:
*定义：*
每个note只有唯一的元音，本note内该元音之前的辅音都称为pre_consonant，本note内该元音之后的辅音都称为post_consonant

### 5.1 每个note必须有足够的长度容纳它的音素
音素时长的最小单位是一帧（约 5.8ms）。**一个 note 的音素个数不能超过它的时长所对应的帧数**，
例如 16ms 的 note（约 2 帧）最多只能有 2 个音素，塞 3 个会返回 `453` 并指出该音符的时间。
一般建议每个 note 不短于 0.05s。

### 5.2 pitch必须在30到90的区间
这是**建议的音乐可用区间**（440Hz 标准音 = 69）。服务的硬校验区间是 `[1, 99]`，
超出硬区间返回 `453`；在 30~90 之外但仍在硬区间内不会报错，但音质通常不可用。
### 5.3 language字段支持 ch / en / jp / spa，另外也支持 ko / fr / it / pt
不在列表内的取值会返回 `400`。
### 5.4 每个note的每个phone是必须是合法的，不同语言的合法phone列表是不一样的
音素表见 https://github.com/timedomain-tech/ACE_phonemes 。
表外的音素会返回 `453` 并列出无法识别的音素名。
### 5.5 每个note必须正好有一个元音
没有元音的 note 会返回 `453`（否则该字会不发音）。
### 5.6 `slur`（延音）必须与它所延长的音符严格首尾相接
`slur.start_time` 必须等于前一个发音音符（`general` 或 `slur`）的 `end_time`（容差 1ms），
两者之间**不能留空隙，也不能插入任何音符**：

- 留空隙 → `400`，提示 `slur starts <x>s after the previous note ends`
- 中间插 `sp` / `sil` → 同样是上面这个 `400`（`sp` 会被服务端剔除，等价于留空隙）
- 中间插 `br` → `400`，提示 `slur must follow a general/slur note`
- `slur` 也不能是 notes 里的第一个音符 → `400` `first note can not be slur`

需要在拖腔之后断开，请把 `sp` / `br` 放在 `slur` **结束之后**，例如
`general[0,1] + slur[1,2] + br[2,2.5]`。

> 普通（非 slur）音符之间不需要显式 `sp`，直接留时间空隙即可，引擎会自动补静音，上限见 5.11。
### 5.7 `consonant_time_head` / `consonant_time_tail` 当前引擎已不再使用
传入不会报错，但不会产生效果，辅音时长由模型自行决定。
### 5.8 每个aces文件只能合成不大于18s的notes列表
按 notes 的实际时间跨度（最大 `end_time` 减最小 `start_time`）计算。
### 5.9 必须提供speaker信息
通过接口的 `speaker_id` 或 `mix_info` 参数提供，歌手需在歌手列表内。
### 5.10 如果要使用piece_params，需要认真核对piece_params的时间范围不能超过note列表的时间范围
超出范围的部分会被自动裁掉，不会报错。
### 5.11 音符之间的静音间隔不应超过10s
超过会返回 `453`。若整首歌有长间隔，请拆成多个片段分别请求。

### 5.12 音符之间不能时间重叠
服务会先把 notes 按 `start_time` 排序，再要求相邻音符满足
`后一个的 start_time >= 前一个的 end_time`。重叠返回 `453`，并给出具体时间，例如
`note at 0.8000s overlaps the previous note ending at 1.0000s`。
该规则对 `general` / `slur` / `br` 一律生效（`sp` / `sil` 已被提前剔除，不参与）。
notes 数组本身**不要求**按时间排序。

> 从 MIDI / DAW 导出时请注意关闭 legato、检查叠轨，这是该错误最常见的来源。