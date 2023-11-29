# ACES File Description v1.0

## 1. Overview

| Field Name   | Field Type | Required | Description                                                                 |
|--------------|------------|----------|-----------------------------------------------------------------------------|
| version      | number     | Yes      | Version information                                                         |
| notes        | Array      | Yes      | Note sequence, see `note` object                                            |
| piece_params | Object     | No       | See `piece_params` object                                                   |
| pad          | Object     | No       | Pad notes at the beginning and end of the current segment, see `pad` object |

*Example:*

```
{
    "version": 1.0, 
    "notes":[NOTE],
    "piece_params": PIECE_PARAMS,
    "pad": PAD
}
```

## 2. NOTE: Note Representation

| Field Name | Field Type | Required                 | Description                                                    |
|------------|------------|--------------------------|----------------------------------------------------------------|
| start_time | number     | Yes                      | Note start time, in seconds                                    |
| end_time   | number     | Yes                      | Note end time, in seconds                                      |
| type       | string     | No, default is "general" | Note type, see Note Type Description                           |
| pitch      | number     | No                       | Pitch value, see Pitch Value Description                       |
| language   | string     | No, default is "ch"      | Note language: Chinese "ch", English "en", Japanese "jp"       |
| phone      | Array      | No                       | List of phonemes for the current note, see Phoneme Description |
| syllable   | string     | No                       | Syllable for the current note, see Syllable Description        |

### 2.1 Note Type Description

Available note types:

+ "general"  General pronunciation note
+ "br" Breath note
+ "sp" Silent note, not required
+ "slur" Slur note, must be preceded by a pronunciation note

### 2.2 Pitch Value Description

The standard pitch of 440hz corresponds to a pitch value of 69

### 2.3 Phoneme Description

Each "general" type note must contain and can only contain one vowel: For specific phoneme information, please refer
to: https://github.com/timedomain-tech/ACE_phonemes

### 2.4 Syllable Description

Only can be used when language is Chinese or Japanese, syllable can be used instead of phoneme lists

*Example:*

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

## 3. PIECE_PARAMS: Segment Parameters (Experimental Feature)

| Field Name | Field Type | Required | Description        |
|------------|------------|----------|--------------------|
| pitch      | Object     | No       | See `pitch` object |
| energy     | Object     | No       | See `param` object |

### 3.1 PITCH: Pitch Representation

| Field Name | Field Type | Required | Description                                                           |
|------------|------------|----------|-----------------------------------------------------------------------|
| user       | Array(PIECE_VALUE)     | No       | User-defined pitch curve, see `piece_value` object, value range 30-90 |

Example:

```
{
    "user": [PIECE_VALUE]
}
```

### 3.2 PARAM: Parameter Representation

| Field Name | Field Type          | Required | Description                                                                             |
|------------|---------------------|----------|-----------------------------------------------------------------------------------------|
| user       | Array(PIECE_VALUE) | No       | Custom parameter curve, see `piece_value` object, value range depends on parameter type |
| envelope   | Array(PIECE_VALUE) | No       | Parameter envelope curve, see `piece_value` object, value range 0-2                     |

Example:

```
{
    "user": [PIECE_VALUE],
    "envelope": [PIECE_VALUE]
}
```

### 3.3 PIECE_VALUE: Piecewise Value Representation

| Field Name       | Field Type | Required | Description                                                                                    |
|------------------|------------|----------|------------------------------------------------------------------------------------------------|
| start_time       | number     | Yes      | The actual starting time of the values array                                                   |
| hop_time         | number     | Yes      | The interval between every two consecutive data frames in the values array                     |
| values           | Array      | Yes      | An array of values with different ranges depending on the value type                           |

Example:

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

| Field Name | Field Type | Required | Description                   |
|------------|------------|----------|-------------------------------|
| begin      | Object     | No       | See `note` object for details |
| end        | Object     | No       | See `note` object for details |

Description:  
PAD is additional information that is usually not required. When the ACES file is used for deep learning model synthesis
of singing voices, the note information before and after this segment can be added to obtain better synthesis results.

Example:

```
{
    "begin": NOTE,
    "end": NOTE
}
```