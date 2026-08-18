# ACES File Description v1.0

## 1. Overview

| Field Name   | Field Type | Required | Description                                                                 |
|--------------|------------|----------|-----------------------------------------------------------------------------|
| version      | number     | Yes      | Version information                                                         |
| notes        | Array      | Yes      | Note sequence, see `note` object                                            |
| piece_params | Object     | No       | See `piece_params` object                                                   |
| pad          | Object     | No       | Pad notes at the beginning and end of the current segment, see `pad` object |
| random_seed  | number     | No       | Random seed number, used for random fine-tuning of timbre                   |

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
| pitch      | number     | Required when type is "general" | Pitch value, see Pitch Value Description. Optional for "slur" (inherits the pitch of the note it extends); ignored for "br"/"sp" |
| language   | string     | No, defaults to ch | Note language, see 5.3 (`ch`/`en`/`jp`/`spa`, plus `ko`/`fr`/`it`/`pt`) |
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

**Only Chinese (`language` = `ch`) supports syllable input.** You may give either pinyin
(e.g. `"la"`, `"shan"`) or a single Chinese character (e.g. `"星"`); the service converts it to
phonemes automatically, so `phone` is not required.

- If the character has multiple readings, or the pinyin is invalid, `400` is returned — use
  pinyin or supply `phone` directly instead.
- **For other languages (English / Japanese / Spanish etc.) please supply the `phone` list.**
  These languages have no syllable conversion; supplying only `syllable` yields a default
  pronunciation rather than your intended lyric.

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

| Field Name | Field Type | Required | Description                              |
|------------|------------|----------|------------------------------------------|
| pitch      | Object     | No       | See `pitch` object                       |
| energy     | Object     | No       | See `param` object                       |
| air        | Object     | No       | See `param` object, breathiness          |
| falsetto   | Object     | No       | See `param` object, falsetto amount      |
| tension    | Object     | No       | See `param` object, vocal cord tension   |

> Effective on the current engine: the `user` / `delta` layers of `pitch`, and the
> `user` layer of `energy` / `air` / `falsetto` / `tension`.
> Other layers (such as `envelope`) are ignored, see 3.2.

Ready-to-submit examples:

- `examples/vibrato_example.aces` — the `user` + `delta` layers of `pitch` (vibrato)
- `examples/param_example.aces` — `user` curves for `energy` / `air` / `falsetto` / `tension`

### 3.1 PITCH: Pitch Representation

| Field Name | Field Type         | Required | Description                                                            |
|------------|--------------------|----------|------------------------------------------------------------------------|
| user       | Array(PIECE_VALUE) | No       | User-defined pitch curve, see `piece_value` object, value range 30-90  |
| delta      | Array(PIECE_VALUE) | No       | User-defined pitch shift, see `piece_value` object, value range [-4,4] |

> **`delta` must be supplied together with `user`.** `delta` is an offset applied on top
> of the `user` pitch curve; if you supply `delta` without `user`, that layer is ignored
> (no error is returned, but effects such as vibrato will not take effect).
> Time ranges not covered by `user` are predicted by the model.

> **Wherever `user` covers, it takes over the pitch completely**; only the uncovered
> ranges are left to the model. We therefore recommend letting `user` span the whole
> note: if it only covers the tail where the vibrato sits, the boundary between the
> model-predicted range and the `user` range produces a pitch step of nearly a
> semitone (about 100 cents, measured), which is audible as a sudden jump.

> **Sustained notes already carry a model-generated natural vibrato** (measured at
> roughly 5–6 Hz with a depth of about ±0.5 semitones). You only need to supply
> `pitch` when you want precise control over when the vibrato starts and over its
> rate and depth; if you just want "some vibrato", leave `pitch` out. This also
> means that if you supply
> `delta` but forget `user`, the vibrato you hear is the model's default behaviour,
> not the curve you wrote.

`examples/vibrato_example.aces` is a complete example: a single note from 4.75s to
6.00s, whose `user` layer lays down a flat pitch line at 63 across the whole note
using 25 points, while `delta` adds a 6 Hz sine starting at 5.29s — so it sounds
like a straight tone followed by vibrato. To make the effect obvious, that example
uses a vibrato depth of ±1.8 semitones; real singing is usually within ±0.3~0.7.

Example:

```
{
    "user": [PIECE_VALUE]
    "delta": [PIECE_VALUE]
}
```

### 3.2 PARAM: Parameter Representation

| Field Name | Field Type          | Required | Description                                                                             |
|------------|---------------------|----------|-----------------------------------------------------------------------------------------|
| user       | Array(PIECE_VALUE) | No       | Custom parameter curve, see `piece_value` object, value range depends on parameter type |
| envelope   | Array(PIECE_VALUE) | No       | Parameter envelope curve. **No longer supported by the current engine; ignored if supplied** |

Value ranges of the `user` layer: 0~5.2 for `energy`, 0~1 for `air` / `falsetto` / `tension`.
A negative value means "unspecified here, let the model predict it".

What the four parameters do perceptually: `energy` is loudness and intensity; `air` is
the amount of breath; `falsetto` is the falsetto ratio (it weakens the upper harmonics,
making the voice softer); `tension` is vocal cord tension (it raises brightness, and is
the most pronounced of the four).

`examples/param_example.aces` demonstrates how to write these four curves: four
sustained notes at the same pitch, each carrying a low-to-high ramp on exactly one
parameter, so you can audition one parameter at a time.

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

The time range covered by one segment is `start_time` through
`start_time + len(values) * hop_time`.

> `values` is resampled to the engine's internal frame rate (about one frame every
> 5.8ms), so `hop_time` is yours to choose: a coarse grid (0.05s, say) is plenty for a
> slowly varying curve, and there is no need to supply one point per frame. Different
> layers under the same `piece_params` (for instance the `user` and `delta` layers of
> `pitch`) are not required to share a `hop_time` either — each layer is aligned to the
> timeline independently using its own `start_time` / `hop_time`, and the layers are
> then combined.

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

> **Actual behaviour of the current engine**: `pad` can be omitted entirely — the service fills it
> in from the first/last note times and aligns it to the internal frame grid. If you do supply
> `pad`, its `type` (`sp` / `br` / `sil` etc.) is honoured, but `start_time` / `end_time` are
> recomputed. Some earlier clients use `pad_notes` as the field name; that is accepted as well.

Example:

```
{
    "begin": NOTE,
    "end": NOTE
}
```

## 5. note rules:
*definition：*
Each note has only a unique vowel, and the consonants before the vowel in this note are called pre consonants. The consonants after the vowel in this note are called post consonants

### 5.1 Each note must be long enough to hold its phonemes
The minimum unit of phoneme duration is one frame (about 5.8ms). **The number of phonemes in a
note must not exceed the number of frames its duration spans** — e.g. a 16ms note (about 2 frames)
can hold at most 2 phonemes; a third one returns `453` together with the timestamp of that note.
As a rule of thumb, keep each note at least 0.05s long.

### 5.2 Pitch must be in the range of 30 to 90
This is the **recommended musical range** (440Hz reference = 69). The hard validation range is
`[1, 99]`; values outside the hard range return `453`. Values between the hard range and the
recommended range are accepted without error but usually sound unusable.
### 5.3 The language field supports ch / en / jp / spa, and also ko / fr / it / pt
Any other value returns `400`.
### 5.4 Each note's phone must be legal, and the list of legal phones varies for different languages
See https://github.com/timedomain-tech/ACE_phonemes . Phonemes outside the table return `453`
together with the unrecognised phoneme names.
### 5.5 Each note must have exactly one vowel
A note without a vowel returns `453` (otherwise that syllable would be silent).
### 5.6 A `slur` must be exactly adjacent to the note it extends
`slur.start_time` must equal the `end_time` of the preceding sounding note (`general` or `slur`),
with a 1ms tolerance. **No gap may be left and no note may be inserted in between**:

- Leaving a gap returns `400`: `slur starts <x>s after the previous note ends`
- Inserting `sp` / `sil` returns the same `400` (`sp` is stripped by the server, which is
  equivalent to leaving a gap)
- Inserting `br` returns `400`: `slur must follow a general/slur note`
- A `slur` also cannot be the first note in `notes` → `400` `first note can not be slur`

To break the sound after a sustained note, place the `sp` / `br` **after** the `slur` ends, e.g.
`general[0,1] + slur[1,2] + br[2,2.5]`.

> Between ordinary (non-slur) notes you do not need an explicit `sp` — just leave a time gap and
> the engine inserts the silence; see 5.11 for the limit.
### 5.7 `consonant_time_head` / `consonant_time_tail` are no longer used by the current engine
Supplying them causes no error but has no effect; consonant durations are decided by the model.
### 5.8 Each aces file can only synthesize a notes list of no more than 18 seconds
Measured as the actual time span of the notes (largest `end_time` minus smallest `start_time`).
### 5.9 Speaker information must be provided
Supply it via the `speaker_id` or `mix_info` request parameter; the singer must be in the singer list.
### 5.10 If you want to use piece_params field, you need to carefully check that the time range of piece_params cannot exceed the time range of the note list
Parts outside the range are clipped automatically without an error.
### 5.11 Silence between notes should not exceed 10s
Exceeding it returns `453`. If a song contains long gaps, split it into several pieces and
request them separately.

### 5.12 Notes must not overlap in time
The service first sorts the notes by `start_time`, then requires every adjacent pair to satisfy
`start_time of the later note >= end_time of the earlier note`. An overlap returns `453` with the
exact position, e.g. `note at 0.8000s overlaps the previous note ending at 1.0000s`.
The rule applies to `general` / `slur` / `br` alike (`sp` / `sil` are stripped beforehand and do
not participate). The notes array itself does **not** need to be sorted by time.

> When exporting from MIDI or a DAW, turn off legato and check for stacked tracks — that is by
> far the most common cause of this error.