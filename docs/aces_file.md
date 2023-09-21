# ACES 文件说明 v1.0

## 1. 总览

| 字段名          | 字段类型   | 是否必传 | 说明                     |
|--------------|--------|------|------------------------|
| version      | number | 是    | 版本信息                   |
| notes        | Array  | 是    | 音符序列，详见 `note` 对象      |
| piece_params | Object | 否    | 见 `piece_params` 对象    |
| pad          | Object | 否    | 当前片段头尾pad音符，见 `pad` 对象 |

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
| pitch      | number | 否              | 音高值，详见音高值说明               |
| language   | string | 否，默认为ch        | 音符语言：中文"ch"，英语"en"，日语"jp" |
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

语言为中文或者日语时才可以使用，可以直接使用音节而无需传音素列表

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

| 字段名    | 字段类型   | 是否必传 | 说明            |
|--------|--------|------|---------------|
| pitch  | Object | 否    | 详见 `pitch` 对象 |
| energy | Object | 否    | 详见 `param` 对象 |

### 3.1 PITCH: 音高表示

| 字段名  | 字段类型   | 是否必传 | 说明                                     |
|------|--------|------|----------------------------------------|
| user | Object | 否    | 用户自定义音高线, 见 `piece_value` 对象，取值范围30-90 |

示例：

```
{
    "user": PIECE_VALUE
}
```

### 3.2 PARAM: 参数表示

| 字段名      | 字段类型                | 是否必传 | 说明                                       |
|----------|---------------------|------|------------------------------------------|
| user     | Object(PIECE_VALUE) | 否    | 自定义参数线, 见 `piece_value` 对象， 取值范围根据参数类型决定 |
| envelope | Object(PIECE_VALUE) | 否    | 参数包络线, 见 `piece_value` 对象，取值范围0-2        |

示例：

```
{
    "user": PIECE_VALUE,
    "envelope": PIECE_VALUE
}
```

### 3.3 PIECE_VALUE: 片段取值表示

| 字段名              | 字段类型   | 是否必传 | 说明                           |
|------------------|--------|------|------------------------------|
| start_time       | number | 是    | values数组真实起始时间               |
| hop_time         | number | 是    | values数组中每两个数据帧之间的间隔         |
| values           | Array  | 是    | 取值数组，根据不同的值类型具有不同的取值范围       |
| enable_intervals | Array  | 是    | 指values数组中，有效数据的索引区间, 包含左右边界 |

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

    ],
    "enable_intervals": [
        {
            "start_index": 1,
            "end_index": 5
        },
        {
            "start_index": 2,
            "end_index": 4
        }
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

示例：

```
{
    "begin": NOTE,
    "end": NOTE
}
```