#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""歌词 -> 音素: 把歌词转成 ACES 文件里每个音符的 `phone` 数组。

中文不需要这个工具 —— 直接在音符上写 `syllable`(拼音或单个汉字), 服务端会转换。
本工具解决的是另外三种语言: 英语 / 日语 / 西班牙语, 它们必须自己给 `phone`。

    python lyrics2phone.py en "twinkle twinkle little star"
    python lyrics2phone.py jp "さくら さくら"
    python lyrics2phone.py spa "camino de la luz"
    python lyrics2phone.py en "let it go" --aces out.aces     # 直接生成可提交的 aces

输出是逐音符的音素列表, 一个音节一个音符:

    $ python lyrics2phone.py en "little star"
    [["l", "ih"], ["t", "ah", "l"], ["s", "t", "aa", "r"]]

把它填进 ACES 的 notes 即可(自己安排 start_time / end_time / pitch):

    {"start_time": 0.0, "end_time": 0.5, "type": "general",
     "language": "en", "pitch": 62, "phone": ["l", "ih"]}

依赖: 英语需要 `pip install cmudict`(离线词典); 日语与西语无依赖。

音素表以引擎为准, 每种语言各有一份合法音素集; 本工具产出的音素已逐一核对在表内。
词典查不到的词会抛 OutOfVocabulary 而不是按拼写猜 —— 猜错的发音比报错更难排查。
自己补词用 extra_dict={"word": ["音素", ...]}。

已知取舍与边界见文件末尾的 CAVEATS。
"""

import json
import re
import sys
import unicodedata


# ============================================================================
#  英语 (English) —— cmudict -> ARPAbet -> 引擎音素
# ============================================================================
__all__ = [
    "lyrics_to_notes_en", "lyrics_to_words_en", "phones_to_notes", "word_phones",
    "OutOfVocabulary", "VOWELS", "CONSONANTS", "PHONES", "VOCABLES",
]

# ---------------------------------------------------------------- phone sets
# Verbatim from en_plan_20240411.json: phon_class.tail / phon_class.head.
VOWELS = frozenset("""
aa ae ah ao aw ay eh er ey ih iy mv ngv nv ow oy uh uw
""".split())

CONSONANTS = frozenset("""
b ch d dh dr dx f g hh jh k l m n ng p r s sh t th tr v w y z zh
""".split())

PHONES = VOWELS | CONSONANTS            # == phon_id, the legal phone set

# Syllabic nasals: used only for vowel-less interjections ("hmm" -> hh mv),
# which would otherwise be a note with no vowel and get rejected by check_vowel.
SYLLABIC_NASAL = {"m": "mv", "n": "nv", "ng": "ngv"}

# --------------------------------------------------------------- onset table
# Legal syllable onsets, used to place intervocalic consonants (maximal onset
# principle). Harvested from every word-initial consonant cluster in cmudict,
# then restricted to native English onsets: singles (minus /ng/, which never
# starts a syllable), obstruent+{l,r}, C+w, and s-clusters. Loanword-only
# clusters (sh+l/m/n/w, "v l", "z w", "s v", "b w") and yod clusters ("k y",
# "l y", ...) are deliberately excluded: keeping them would pull the consonant
# off the previous note in words like "Ashley" or "value" ("val-ue" is the
# division wanted, not "va-lue"). /y/ alone is still a legal onset.
_ONSET_CLUSTERS = (
    # obstruent + l / r
    "p l", "b l", "k l", "g l", "f l", "s l",
    "p r", "b r", "t r", "d r", "k r", "g r", "f r", "th r", "sh r",
    # C + w
    "t w", "d w", "k w", "g w", "s w", "hh w",
    # s + stop / nasal
    "s p", "s t", "s k", "s m", "s n",
    # s + stop + liquid
    "s p l", "s p r", "s t r", "s k r", "s k l", "s k w",
)

_ONSETS = frozenset(
    [(c,) for c in CONSONANTS if c != "ng"] +          # singles, minus /ng/
    [tuple(c.split()) for c in _ONSET_CLUSTERS]
)
assert all(set(o) <= CONSONANTS for o in _ONSETS)

# ------------------------------------------------------------------ vocables
# Sung syllables cmudict either lacks or has only as a letter-name spelling
# ("ba" -> B IY EY, i.e. "bee-ay"). Values are engine phones. Extend freely.
# Others ("ooh", "ahh", "hmm", "la", "na", "yeah", "whoa", "oh") are already
# right in cmudict, including after the repeated-letter collapse below.
VOCABLES = {
    "ba": ["b", "aa"],        # cmudict: B IY EY ("bee-ay")
    "oo": ["uw"],             # cmudict: the letter O -> OW
    "aa": ["aa"],             # cmudict: the article "a" -> AH
    "eeh": ["iy"],
    "woah": ["w", "ow"],      # not in cmudict at all
    "whoah": ["w", "ow"],
    # "rock 'n' roll": the clipped "and" is /@n/. cmudict's entry for "n" is
    # the LETTER NAME (EH N, "en"), which is simply the wrong sound here.
    "'n'": ["ah", "n"],
    "'n": ["ah", "n"],
    "n'": ["ah", "n"],
    "n": ["ah", "n"],         # "rock n roll" written without apostrophes
}

# ---------------------------------------------------------------- letter runs
# A token that is one letter repeated ("aaa", "ooo", "zzz", "mmm") is a sung
# vocable, never a word -- but cmudict answers those spellings (directly, or
# after the repeated-letter collapse in _collapse) with LETTER NAMES, which is
# silently wrong in both phones and note count:
#     aaa -> "triple-A" (3 notes!)   www -> "double-you" (3 notes)
#     kkk -> 3 notes                 sss -> "es-es" (2 notes)
#     zzz -> "zee"   nnn -> "en"   rrr -> "ar"   lll -> "el"   uuu -> "you"
# So letter runs never reach cmudict at all. They resolve against extra_dict,
# then VOCABLES, then this table of sustained vowels. A run of a consonant that
# cannot carry a note ("zzz", "sss", "rrr", "www", "kkk") raises
# OutOfVocabulary instead of quietly singing the letter's name -- exactly like
# the vowel-less interjection "shh" already did.
_LETTER_RUN = {
    "a": ["aa"],              # "aaa"  (same as VOCABLES["aa"])
    "e": ["iy"],              # "eee"
    "i": ["ay"],              # "iii", as in the sung word "I"
    "o": ["uw"],              # "ooo"  (same as VOCABLES["oo"]; write "ohh" for /ow/)
    "u": ["uw"],              # "uuu"
    "m": ["mv"],              # "mmm" -> syllabic /m/
    "n": ["nv"],              # "nnn" -> syllabic /n/
}

_VOICELESS = frozenset("p t k f th".split())      # -s suffix -> /s/
_SIBILANT = frozenset("s z sh zh ch jh".split())  # -s suffix -> /ih z/


class OutOfVocabulary(ValueError):
    """A word is not in cmudict; the caller must supply its phones."""


# --------------------------------------------------------------- dictionary
_DICT = None


def _cmu():
    global _DICT
    if _DICT is None:
        try:
            import cmudict
        except ImportError:                       # pragma: no cover
            raise RuntimeError("lyrics2phone (en) needs the 'cmudict' package: "
                               "pip install cmudict")
        _DICT = cmudict.dict()
    return _DICT


def _arpa_to_phones(arpa):
    """['HH','AH0','L','OW1'] -> ['hh','ah','l','ow'] (validated)."""
    out = []
    for sym in arpa:
        p = re.sub(r"\d+$", "", sym).lower()
        if p not in PHONES:                       # pragma: no cover
            raise AssertionError("cmudict symbol %r maps to unknown phone %r"
                                 % (sym, p))
        out.append(p)
    return out


# -------------------------------------------------------------- syllabifier
def phones_to_notes(phones):
    """Split a flat engine-phone list into notes, one syllable (one vowel) each.

    >>> phones_to_notes(["s", "t", "r", "eh", "ng", "th"])
    [['s', 't', 'r', 'eh', 'ng', 'th']]

    The engine only requires *at least* one vowel per note; the one-vowel-per-
    note split done here is this module's own convention.

    Consonants between two vowels are divided by the maximal onset principle:
    as many as can legally start a syllable go with the following vowel, the
    rest close the preceding one. Word-initial and word-final consonants stay
    where they are. Raises ValueError if there is no vowel to build a note on.
    """
    if isinstance(phones, str):
        raise ValueError("phones must be a list of engine phones, e.g. "
                         "['hh','ah'], not the string %r" % (phones,))
    try:
        phones = list(phones)
    except TypeError:
        raise ValueError("phones must be an iterable of engine phones, got %s"
                         % type(phones).__name__)
    bad = [p for p in phones if not isinstance(p, str) or p not in PHONES]
    if bad:
        raise ValueError("not legal en phones: %s"
                         % ", ".join(sorted(set(map(str, bad)))))
    nuclei = [i for i, p in enumerate(phones) if p in VOWELS]
    if not nuclei:
        raise ValueError("no vowel in %s: cannot form a note" % (phones,))

    cuts = [0]
    for a, b in zip(nuclei, nuclei[1:]):
        cluster = phones[a + 1:b]                 # consonants between vowels
        split = len(cluster)                      # fallback: empty onset
        for k in range(len(cluster) + 1):         # longest legal onset wins
            if k == len(cluster) or tuple(cluster[k:]) in _ONSETS:
                split = k
                break
        cuts.append(a + 1 + split)
    cuts.append(len(phones))
    return [phones[s:e] for s, e in zip(cuts, cuts[1:])]


# ------------------------------------------------------------- word lookup
def _check_extra(extra):
    """Validate `extra_dict` up front.

    Without this, a typo'd phone surfaces much later as a misleading message:
    extra_dict={"w": ["QQ","xx"]} used to report "has no vowel (QQ xx)" from
    _fix_vowelless instead of "not a legal en phone", and a non-lowercase key
    was silently ignored (it can never match, since lookups are lowercased).
    """
    if extra is None:
        return
    if not hasattr(extra, "items"):
        raise ValueError("extra_dict must be a dict of {word: [phones]}, got %s"
                         % type(extra).__name__)
    for word, phones in extra.items():
        if not isinstance(word, str):
            raise ValueError("extra_dict keys must be str, got %r" % (word,))
        if word != word.lower():
            raise ValueError("extra_dict keys must be lowercase (lookups are "
                             "lowercased, so %r could never match); use %r"
                             % (word, word.lower()))
        if isinstance(phones, str) or not isinstance(phones, (list, tuple)):
            raise ValueError("extra_dict[%r] must be a list of engine phones, "
                             "e.g. ['b','aa']; got %r" % (word, phones))
        if not phones:
            raise ValueError("extra_dict[%r] is empty: give it at least one "
                             "phone" % (word,))
        bad = [p for p in phones if not isinstance(p, str) or p not in PHONES]
        if bad:
            raise ValueError("extra_dict[%r] contains things that are not legal "
                             "en phones: %s (legal phones are the 45 in "
                             "en_plan phon_id)"
                             % (word, ", ".join(repr(b) for b in bad)))


def _collapse(word):
    """"oooooh" -> ["oooh"(3+ -> 2), "oh"(all runs -> 1)] candidate spellings."""
    two = re.sub(r"(.)\1{2,}", r"\1\1", word)
    one = re.sub(r"(.)\1+", r"\1", word)
    return [c for c in (two, one) if c != word]


def _letter_run(word):
    """"aaa"/"zzz" -> its letter; anything else -> None (see _LETTER_RUN)."""
    if len(word) >= 2 and word[0].isalpha() and word == word[0] * len(word):
        return word[0]
    return None


def _raw_lookup(word, extra):
    if extra and word in extra:
        return list(extra[word])
    if word in VOCABLES:
        return list(VOCABLES[word])
    prons = _cmu().get(word)
    if prons:
        return _arpa_to_phones(prons[0])          # cmudict's primary variant
    return None


def _run_lookup(word, extra):
    """Phones for a letter run, from extra_dict / VOCABLES / _LETTER_RUN only.

    cmudict is deliberately skipped here: it answers "aaa"/"zzz"/"www" with the
    letter's *name*, which is wrong in phones and in note count.
    """
    if extra and word in extra:
        return list(extra[word])
    if word in VOCABLES:
        return list(VOCABLES[word])
    letter = _letter_run(word)
    if letter in _LETTER_RUN:
        return list(_LETTER_RUN[letter])
    return None


def _lookup(word, extra):
    """The one lookup every path goes through: extra_dict / VOCABLES / cmudict,
    except that a letter run ("aaa") never gets to ask cmudict."""
    if _letter_run(word):
        return _run_lookup(word, extra)
    return _raw_lookup(word, extra)


def word_phones(word, extra_dict=None):
    """Engine phones for one word, or raise OutOfVocabulary."""
    if not isinstance(word, str):
        raise ValueError("word must be a str, got %s" % type(word).__name__)
    _check_extra(extra_dict)
    w = word.lower()

    letter = _letter_run(w)
    if letter is not None:                         # "aaa"/"zzz": cmudict would
        got = _run_lookup(w, extra_dict)           # answer with a letter name
        if got:
            return _fix_vowelless(got, word)
        raise OutOfVocabulary(
            "%r is a run of the letter %r: cmudict only has the letter's name "
            "for it (e.g. 'zzz' -> \"zee\", 'www' -> \"double-you\"), which "
            "would be sung wrong, and /%s/ alone cannot carry a note. Drop it "
            "or pass phones yourself, e.g. extra_dict={%r: ['...']}"
            % (word, letter, letter, w))

    got = _lookup(w, extra_dict)
    if got:
        return _fix_vowelless(got, word)

    if w.endswith("in'"):                          # "lovin'" -> "loving", sung
        got = _lookup(w[:-1] + "g", extra_dict)
        if got:                                    # with /n/, not /ng/.  Tried
            if got[-1] == "ng":                    # before the bare "lovin",
                got = got[:-1] + ["n"]             # which is a surname entry.
            return _fix_vowelless(got, word)

    cands = []
    if w.strip("'") != w:                          # "'cause" -> "cause"
        cands.append(w.strip("'"))
    cands += _collapse(w)                          # "ohhhh" -> "ohh" -> "oh"
    for c in cands:                                # _lookup(), so that a
        got = _lookup(c, extra_dict)               # candidate can never
        if got:                                    # collapse into a letter name
            return _fix_vowelless(got, word)

    # last resort: regular -s / -'s inflection on a known base
    for cut, base in (("'s", w[:-2]), ("s", w[:-1])):
        if w.endswith(cut) and len(base) >= 2 and not base.endswith("s"):
            got = _lookup(base, extra_dict)
            if got:
                tail = got[-1]
                suf = (["ih", "z"] if tail in _SIBILANT else
                       ["s"] if tail in _VOICELESS else ["z"])
                return _fix_vowelless(got + suf, word)

    raise OutOfVocabulary(
        "%r is not in cmudict; pass its phones in yourself, e.g. "
        "lyrics_to_notes_en(text, extra_dict={%r: ['...']})" % (word, w))


def _fix_vowelless(phones, word):
    """"hmm" -> HH M -> hh mv, so the note has a nucleus."""
    if any(p in VOWELS for p in phones):
        return phones
    for i in range(len(phones) - 1, -1, -1):
        if phones[i] in SYLLABIC_NASAL:
            phones = list(phones)
            phones[i] = SYLLABIC_NASAL[phones[i]]
            return phones
    raise OutOfVocabulary(
        "%r has no vowel (%s) and cannot be sung on a note; drop it or pass "
        "phones yourself" % (word, " ".join(phones)))


# ---------------------------------------------------------------- tokenizer
_APOSTROPHES = dict.fromkeys(map(ord, u"‘’ʼ´`"), u"'")
_DASHES = dict.fromkeys(map(ord, u"‐‑‒–—―"), u"-")
# Latin letters that NFKD does *not* decompose, so they need spelling out by
# hand.  Everything else with a diacritic (é ï ñ à ...) is handled by the
# NFKD + strip-combining-marks step in _normalise().
_LIGATURES = dict((ord(k), v) for k, v in {
    u"ß": u"ss", u"æ": u"ae", u"Æ": u"AE", u"œ": u"oe",
    u"Œ": u"OE", u"ø": u"o", u"Ø": u"O", u"ł": u"l",
    u"Ł": u"L", u"đ": u"d", u"Đ": u"D", u"ı": u"i",
}.items())
_TOKEN = re.compile(r"[0-9]+|'?[A-Za-z][A-Za-z'\-]*")
_WORDISH = u"[^\\W\\d_]*"          # a run of letters, any script


def _normalise(text):
    """Fold the lyrics to ASCII letters before tokenizing.

    _TOKEN only knows [A-Za-z], so without this any accented letter used to cut
    the word in half *silently*: "naïve" -> "na"+"ve" -> "nah vee", "déjà vu" ->
    "dee jay voo".  Worse, the result depended on the caller's Unicode normal
    form: NFC "café" raised OOV on "caf" while NFD "café" came out right.

    NFKD + dropping combining marks makes both forms identical ("cafe") and
    keeps "naïve"/"jalapeño"/"Beyoncé" as single words.  Letters that survive
    the fold (Greek, Cyrillic, CJK, thorn, ...) raise OutOfVocabulary: this
    module never silently drops or splits what it cannot read.
    """
    if not isinstance(text, str):
        raise ValueError("lyrics text must be a str, got %s"
                         % type(text).__name__)
    text = text.translate(_APOSTROPHES).translate(_DASHES).translate(_LIGATURES)
    text = unicodedata.normalize("NFKD", text)
    text = u"".join(c for c in text if not unicodedata.combining(c))
    left = sorted(set(c for c in text if ord(c) > 127 and c.isalpha()))
    if left:
        m = re.search(_WORDISH + re.escape(left[0]) + _WORDISH, text, re.UNICODE)
        raise OutOfVocabulary(
            "%r contains letters this module cannot read (%s): only the Latin "
            "alphabet is supported. Transliterate the word, or pass its phones "
            "yourself via extra_dict / phones_to_notes()."
            % (m.group(0) if m else left[0], u" ".join(left)))
    return text


def _tokens(text):
    out = []
    for m in _TOKEN.finditer(_normalise(text)):
        tok = m.group(0)
        if tok[0].isdigit():
            raise OutOfVocabulary(
                "digits are not supported (%r): spell the number out, "
                "e.g. '17' -> 'seventeen'" % tok)
        out.append(tok.lower().strip("-"))
    return out


def lyrics_to_words_en(text, extra_dict=None):
    """[(word, [note_phones, ...]), ...] -- same notes as lyrics_to_notes_en,
    grouped per word so the caller can align words with note ranges."""
    _check_extra(extra_dict)
    out = []
    for tok in _tokens(text):
        if not tok:
            continue
        try:                                       # "x-ray", "t-shirt" first
            out.append((tok, phones_to_notes(word_phones(tok, extra_dict))))
            continue
        except OutOfVocabulary:
            if "-" not in tok:
                raise
        for part in tok.split("-"):                # then as a compound
            if part:
                out.append((part, phones_to_notes(word_phones(part, extra_dict))))
    return out


def lyrics_to_notes_en(text, extra_dict=None):
    """English lyrics -> one phone list per note (one syllable each).

    >>> lyrics_to_notes_en("Hello world")
    [['hh', 'ah'], ['l', 'ow'], ['w', 'er', 'l', 'd']]

    `extra_dict` maps a **lowercase** word to its engine phones, e.g.
    {"spotify": ["s", "p", "aa", "t", "ah", "f", "ay"]}; it overrides cmudict
    and is the escape hatch for names, slang and OOV words. Its phones are
    checked against the engine's phone set on the way in.

    Anything this module cannot read -- an unknown word, a digit, a non-Latin
    letter, a bad argument -- raises ValueError (OutOfVocabulary for words);
    it never returns a silently wrong or silently shortened result.
    """
    return [n for _, notes in lyrics_to_words_en(text, extra_dict) for n in notes]


# ============================================================================
#  日语 (Japanese) —— 假名 -> 罗马字音节 -> 引擎自带词典
# ============================================================================
# 假名 -> plan dict 的罗马字键(单假名)
KANA_SINGLE = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'ぁ': 'a', 'ぃ': 'i', 'ぅ': 'u', 'ぇ': 'e', 'ぉ': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'ゕ': 'ka', 'ゖ': 'ke', 'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu',
    'げ': 'ge', 'ご': 'go', 'さ': 'sa', 'し': 'shi', 'す': 'su',
    'せ': 'se', 'そ': 'so', 'ざ': 'za', 'じ': 'ji', 'ず': 'zu',
    'ぜ': 'ze', 'ぞ': 'zo', 'た': 'ta', 'ち': 'chi', 'つ': 'tsu',
    'て': 'te', 'と': 'to', 'だ': 'da', 'ぢ': 'ji', 'づ': 'zu',
    'で': 'de', 'ど': 'do', 'な': 'na', 'に': 'ni', 'ぬ': 'nu',
    'ね': 'ne', 'の': 'no', 'は': 'ha', 'ひ': 'hi', 'ふ': 'fu',
    'へ': 'he', 'ほ': 'ho', 'ば': 'ba', 'び': 'bi', 'ぶ': 'bu',
    'べ': 'be', 'ぼ': 'bo', 'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu',
    'ぺ': 'pe', 'ぽ': 'po', 'ま': 'ma', 'み': 'mi', 'む': 'mu',
    'め': 'me', 'も': 'mo', 'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo', 'ら': 'ra', 'り': 'ri',
    'る': 'ru', 'れ': 're', 'ろ': 'ro', 'わ': 'wa', 'ゎ': 'wa',
    'ゐ': 'wi', 'ゑ': 'we', 'を': 'o', 'ゔ': 'vu',
}

# 假名 -> plan dict 的罗马字键(拗音 / 外来音, 两个假名一组, 优先匹配)
KANA_DIGRAPH = {
    'きゃ': 'kya', 'きゅ': 'kyu', 'きぇ': 'kye', 'きょ': 'kyo',
    'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎぇ': 'gye', 'ぎょ': 'gyo',
    'しゃ': 'sha', 'しゅ': 'shu', 'しぇ': 'she', 'しょ': 'sho',
    'じゃ': 'ja', 'じゅ': 'ju', 'じぇ': 'je', 'じょ': 'jo',
    'ちゃ': 'cha', 'ちゅ': 'chu', 'ちぇ': 'che', 'ちょ': 'cho',
    'ぢゃ': 'ja', 'ぢゅ': 'ju', 'ぢぇ': 'je', 'ぢょ': 'jo',
    'にゃ': 'nya', 'にゅ': 'nyu', 'にぇ': 'nye', 'にょ': 'nyo',
    'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひぇ': 'hye', 'ひょ': 'hyo',
    'びゃ': 'bya', 'びゅ': 'byu', 'びぇ': 'bye', 'びょ': 'byo',
    'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴぇ': 'pye', 'ぴょ': 'pyo',
    'みゃ': 'mya', 'みゅ': 'myu', 'みぇ': 'mye', 'みょ': 'myo',
    'りゃ': 'rya', 'りゅ': 'ryu', 'りぇ': 'rye', 'りょ': 'ryo',
    'ふぁ': 'fa', 'ふぃ': 'fi', 'ふぇ': 'fe', 'ふぉ': 'fo',
    'ふゃ': 'fya', 'ふゅ': 'fyu', 'ふょ': 'fyo', 'ゔぁ': 'va',
    'ゔぃ': 'vi', 'ゔぇ': 've', 'ゔぉ': 'vo', 'ゔゃ': 'vya',
    'ゔゅ': 'vyu', 'ゔょ': 'vyo', 'てぃ': 'ti', 'てゃ': 'tya',
    'てゅ': 'tyu', 'てょ': 'tyo', 'とぅ': 'tu', 'でぃ': 'di',
    'でゃ': 'dya', 'でゅ': 'dyu', 'でょ': 'dyo', 'どぅ': 'du',
    'つぁ': 'tsa', 'つぃ': 'tsi', 'つぇ': 'tse', 'つぉ': 'tso',
    'すぃ': 'si', 'ずぃ': 'zi', 'うぃ': 'wi', 'うぇ': 'we',
    'うぉ': 'wo', 'いぇ': 'ye', 'くぁ': 'kwa', 'くぃ': 'kwi',
    'くぇ': 'kwe', 'くぉ': 'kwo', 'くゎ': 'kwa', 'ぐぁ': 'gwa',
    'ぐぃ': 'gwi', 'ぐぇ': 'gwe', 'ぐぉ': 'gwo', 'ぐゎ': 'gwa',
}

# plan dict 的子集: 罗马字音节 -> 音素。逐条等于 plan 的 dict, 未手抄。
SYLLABLE_PHONES = {
    'a': ['a'], 'ba': ['b', 'a'], 'be': ['b', 'e'],
    'bi': ['by', 'i'], 'bo': ['b', 'o'], 'bu': ['b', 'u'],
    'bya': ['by', 'a'], 'bye': ['by', 'e'], 'byo': ['by', 'o'],
    'byu': ['by', 'u'], 'cha': ['ch', 'a'], 'che': ['ch', 'e'],
    'chi': ['ch', 'i'], 'cho': ['ch', 'o'], 'chu': ['ch', 'u'],
    'da': ['d', 'a'], 'de': ['d', 'e'], 'di': ['dy', 'i'],
    'do': ['d', 'o'], 'du': ['d', 'u'], 'dya': ['dy', 'a'],
    'dyo': ['dy', 'o'], 'dyu': ['dy', 'u'], 'e': ['e'],
    'fa': ['f', 'a'], 'fe': ['f', 'e'], 'fi': ['fy', 'i'],
    'fo': ['f', 'o'], 'fu': ['f', 'u'], 'fya': ['fy', 'a'],
    'fyo': ['fy', 'o'], 'fyu': ['fy', 'u'], 'ga': ['g', 'a'],
    'ge': ['g', 'e'], 'gi': ['gy', 'i'], 'go': ['g', 'o'],
    'gu': ['gw', 'u'], 'gwa': ['gw', 'a'], 'gwe': ['gw', 'e'],
    'gwi': ['gw', 'i'], 'gwo': ['gw', 'o'], 'gya': ['gy', 'a'],
    'gye': ['gy', 'e'], 'gyo': ['gy', 'o'], 'gyu': ['gy', 'u'],
    'ha': ['h', 'a'], 'he': ['h', 'e'], 'hi': ['hy', 'i'],
    'ho': ['h', 'o'], 'hu': ['h', 'u'], 'hya': ['hy', 'a'],
    'hye': ['hy', 'e'], 'hyo': ['hy', 'o'], 'hyu': ['hy', 'u'],
    'i': ['i'], 'ja': ['j', 'a'], 'je': ['j', 'e'], 'ji': ['j', 'i'],
    'jo': ['j', 'o'], 'ju': ['j', 'u'], 'ka': ['k', 'a'],
    'ke': ['k', 'e'], 'ki': ['ky', 'i'], 'ko': ['k', 'o'],
    'ku': ['kw', 'u'], 'kwa': ['kw', 'a'], 'kwe': ['kw', 'e'],
    'kwi': ['kw', 'i'], 'kwo': ['kw', 'o'], 'kya': ['ky', 'a'],
    'kye': ['ky', 'e'], 'kyo': ['ky', 'o'], 'kyu': ['ky', 'u'],
    'ma': ['m', 'a'], 'me': ['m', 'e'], 'mi': ['my', 'i'],
    'mo': ['m', 'o'], 'mu': ['m', 'u'], 'mya': ['my', 'a'],
    'mye': ['my', 'e'], 'myo': ['my', 'o'], 'myu': ['my', 'u'],
    'na': ['n', 'a'], 'ne': ['n', 'e'], 'ni': ['ny', 'i'],
    'no': ['n', 'o'], 'nu': ['n', 'u'], 'nya': ['ny', 'a'],
    'nye': ['ny', 'e'], 'nyo': ['ny', 'o'], 'nyu': ['ny', 'u'],
    'o': ['o'], 'pa': ['p', 'a'], 'pe': ['p', 'e'],
    'pi': ['py', 'i'], 'po': ['p', 'o'], 'pu': ['p', 'u'],
    'pya': ['py', 'a'], 'pye': ['py', 'e'], 'pyo': ['py', 'o'],
    'pyu': ['py', 'u'], 'ra': ['r', 'a'], 're': ['r', 'e'],
    'ri': ['ry', 'i'], 'ro': ['r', 'o'], 'ru': ['r', 'u'],
    'rya': ['ry', 'a'], 'rye': ['ry', 'e'], 'ryo': ['ry', 'o'],
    'ryu': ['ry', 'u'], 'sa': ['s', 'a'], 'se': ['s', 'e'],
    'sha': ['sh', 'a'], 'she': ['sh', 'e'], 'shi': ['sh', 'i'],
    'sho': ['sh', 'o'], 'shu': ['sh', 'u'], 'si': ['s', 'i'],
    'so': ['s', 'o'], 'su': ['s', 'u'], 'ta': ['t', 'a'],
    'te': ['t', 'e'], 'ti': ['ty', 'i'], 'to': ['t', 'o'],
    'tsa': ['ts', 'a'], 'tse': ['ts', 'e'], 'tsi': ['ts', 'i'],
    'tso': ['ts', 'o'], 'tsu': ['ts', 'u'], 'tu': ['t', 'u'],
    'tya': ['ty', 'a'], 'tyo': ['ty', 'o'], 'tyu': ['ty', 'u'],
    'u': ['u'], 'va': ['v', 'a'], 've': ['v', 'e'],
    'vi': ['vy', 'i'], 'vo': ['v', 'o'], 'vu': ['v', 'u'],
    'vya': ['vy', 'a'], 'vyo': ['vy', 'o'], 'vyu': ['vy', 'u'],
    'wa': ['w', 'a'], 'we': ['w', 'e'], 'wi': ['w', 'i'],
    'wo': ['w', 'o'], 'ya': ['y', 'a'], 'ye': ['y', 'e'],
    'yo': ['y', 'o'], 'yu': ['y', 'u'], 'za': ['z', 'a'],
    'ze': ['z', 'e'], 'zi': ['z', 'i'], 'zo': ['z', 'o'],
    'zu': ['z', 'u'],
}

# ---------------------------------------------------------------------------
# 线上先例过滤(CAVEATS 第 1 条)
#
# 在 regression_check/dataset 的 4,716 个线上 jp note 上逐音素计数, 下面这 5 个
# 音素出现次数为 **0**:
#     f = 0, ty = 0, dy = 0, v = 0, vy = 0
# 而它们的日语传统近似音在同一语料里很常见:
#     h = 109 (('h','u') 38 次)、ch = 51、j = 25、b = 56、by = 16
# 也就是说 **ふ 在线上 100% 唱作 ['h','u'], 从没用过 ['f','u']**。
# 因此默认把这 5 个零先例音素替换成线上有先例的读法(替换目标全部仍是 plan
# dict 里的合法音节, 且都是外来音进日语时的传统近似: ヴァイオリン→バイオリン、
# ticket→チケット、radio→ラジオ、form→ホーム)。
#
# 想要"字面"读法的调用方传 allow_unattested=True —— 但那条路的音色**线上无
# 先例, 效果未经验证**。
#
# 注意 fy 不在替换表里: fy 线上出现过 2 次(都是 ('fy','i')), 属"有先例但极
# 罕见", 按"零次才替换"的规则保留。
# ---------------------------------------------------------------------------
UNATTESTED_PHONES = frozenset({'f', 'ty', 'dy', 'v', 'vy'})

ATTESTED_SUBSTITUTE = {
    # ふぁ行: f -> h (ファ→ハ, フ→ホ 型近似)
    'fa': 'ha', 'fe': 'he', 'fo': 'ho', 'fu': 'hu',
    # てぃ/てゃ行: ty -> ch (ティ→チ, ticket→チケット)
    'ti': 'chi', 'tya': 'cha', 'tyo': 'cho', 'tyu': 'chu',
    # でぃ/でゃ行: dy -> j (ディ→ジ, radio→ラジオ)
    'di': 'ji', 'dya': 'ja', 'dyo': 'jo', 'dyu': 'ju',
    # ゔ行: v/vy -> b/by (ヴァイオリン→バイオリン)
    'va': 'ba', 've': 'be', 'vi': 'bi', 'vo': 'bo', 'vu': 'bu',
    'vya': 'bya', 'vyo': 'byo', 'vyu': 'byu',
}

# plan 的 vowel_holding_dict: 长音 ー 该延续成哪个元音
VOWEL_HOLDING = {
    'a': 'a', 'i': 'i', 'u': 'u', 'e': 'e', 'o': 'o', 'nv': 'nv',
    'mv': 'mv', 'ax': 'ax', 'ix': 'ix', 'ux': 'ux', 'ex': 'ex', 'ox': 'ox',
}

SOKUON = 'っ'          # 促音
MORAIC_N = 'ん'        # 撥音
LONG_MARKS = 'ー〜~'   # 长音符 / 波浪线(NFKC 会把 ～ 变成 ~)

# 小假名单独出现时(没跟前一个假名组成 KANA_DIGRAPH)代表的元音。
# 它自成一个 note = 一个 mora, 跟 ー 等价: ねぇ 与 ねー 输出完全相同。
SMALL_VOWELS = {'ぁ': 'a', 'ぃ': 'i', 'ぅ': 'u', 'ぇ': 'e', 'ぉ': 'o'}

# 歌词里常见的标点与空白, 直接跳过不发音。
# 分隔符统一处理(修 J3): 中点 ・(U+30FB) 与 ASCII/全角连字符、各种破折号
# 一律当作分隔符跳过, 不再"・ 静默丢弃而 - 报错"。
# 注意长音符 ー(U+30FC) 与波浪线 〜/~ 不在这里, 它们在 LONG_MARKS 里发音。
_SEPARATORS = ('-'          # U+002D ASCII hyphen-minus(全角 － 经 NFKC 也变成它)
               '‐‑‒–—―'  # ‐ ‑ ‒ – — ―
               '−'     # − minus sign
               '·‧・')                   # · ‧ ・
IGNORED = set(' \t\r\n　、。，,．.…‥!！?？'
              '「」『』（）()［］[]｛｝{}〈〉《》'
              '"\'`“”‘’:;：；|｜/／\\＼*＊+＋=＝_＿') | set(_SEPARATORS)


def _to_hiragana(text):
    """NFKC 归一 + 片假名转平假名, 让后面只用管一套表。"""
    text = unicodedata.normalize('NFKC', str(text))
    # ヷヸヹヺ 不在常规片假名区间, 先展开成 ゔ + 小假名
    for src, dst in (('ヷ', 'ゔぁ'), ('ヸ', 'ゔぃ'),
                     ('ヹ', 'ゔぇ'), ('ヺ', 'ゔぉ')):
        text = text.replace(src, dst)
    out = []
    for ch in text:
        # 片假名 ァ(30A1) ~ ヶ(30F6) -> 平假名; ヴ(30F4) 会落到 ゔ(3094)
        out.append(chr(ord(ch) - 0x60) if 'ァ' <= ch <= 'ヶ' else ch)
    return ''.join(out)


def _phones_for(key, allow_unattested):
    """罗马字音节 -> 音素表。默认把线上零先例的音素换成有先例的读法。"""
    if not allow_unattested:
        key = ATTESTED_SUBSTITUTE.get(key, key)
    return list(SYLLABLE_PHONES[key])


def lyrics_to_notes_ja(text, allow_unattested=False):
    """假名歌词 -> [[phone, ...], ...], 一个内层 list 就是一个 note 的 phone。

    allow_unattested=False(默认): 只输出线上语料出现过的音素, ふ->['h','u']、
        ヴァ->['b','a']、ティ->['ch','i']、ディ->['j','i']。
    allow_unattested=True: 走 plan dict 的字面读法(f / v / vy / ty / dy)。
        **这些音素线上一次都没出现过, 音色效果未经验证。**

    >>> lyrics_to_notes_ja('こんにちは')
    [['k', 'o'], ['nv'], ['ny', 'i'], ['ch', 'i'], ['h', 'a']]
    >>> lyrics_to_notes_ja('ふ')
    [['h', 'u']]
    >>> lyrics_to_notes_ja('ふ', allow_unattested=True)
    [['f', 'u']]
    """
    kana = _to_hiragana(text)
    notes = []
    i, n = 0, len(kana)
    while i < n:
        ch = kana[i]
        if ch in IGNORED:
            i += 1
            continue
        if ch == SOKUON:
            notes.append(['cl'])            # 促音自成一个 note
            i += 1
            continue
        if ch == MORAIC_N:
            notes.append(['nv'])            # 撥音自成一个 note
            i += 1
            continue
        if ch in LONG_MARKS:
            held = VOWEL_HOLDING.get(notes[-1][-1]) if notes else None
            if held is None:
                raise ValueError(
                    "长音符 %r (第 %d 个字符)前面必须是一个带元音的假名音节" % (ch, i + 1))
            notes.append([held])            # 长音自成一个 note, 延续前一个元音
            i += 1
            continue
        key = KANA_DIGRAPH.get(kana[i:i + 2])
        if key is not None:
            # 组成了外来音音节: 两个假名 = 1 mora = 1 个 note
            notes.append(_phones_for(key, allow_unattested))
            i += 2
            continue
        if ch in SMALL_VOWELS and notes:
            # 没组成外来音音节的小假名(ねぇ / まぁ / ふぅ …): 它本身就是
            # 独立的一个 mora, 所以自成一个 note —— 与 ー 同一条路径。
            # 小元音跟前一个 note 的元音一致时按"延长"处理(ねぇ ≡ ねー),
            # 不一致时(ねぁ 这类非常规写法)就照字面发那个元音。
            held = VOWEL_HOLDING.get(notes[-1][-1])
            vowel = SMALL_VOWELS[ch]
            notes.append([held] if held == vowel else [vowel])
            i += 1
            continue
        key = KANA_SINGLE.get(ch)
        if key is None:
            raise ValueError(_unsupported_message(ch, i))
        notes.append(_phones_for(key, allow_unattested))
        i += 1
    return notes


def _unsupported_message(ch, idx):
    code = 'U+%04X' % ord(ch)
    if ('一' <= ch <= '鿿' or '㐀' <= ch <= '䶿'
            or ch in '々〆〻' or '豈' <= ch <= '﫿'):
        return ("第 %d 个字符是汉字 %r(%s): 本工具不做汉字注音, "
                "请先把歌词写成假名(如 '漢字' -> 'かんじ')" % (idx + 1, ch, code))
    if ch.isascii() and ch.isalpha():
        return ("第 %d 个字符是拉丁字母 %r: 日语通道只接受假名, "
                "英文歌词请用英语音素" % (idx + 1, ch))
    if ch in 'ゝゞヽヾ':
        return ("第 %d 个字符是叠字符 %r(%s): 请把它展开成实际假名"
                % (idx + 1, ch, code))
    return "第 %d 个字符 %r(%s) 不是本工具支持的假名" % (idx + 1, ch, code)


CAVEATS = """\
JA(日语)已知限制 —— 逐条都在 regression_check/dataset 的 4,716 个线上 jp note
上核对过。

1. **线上零先例音素已默认避开(默认行为, 会改变输出)。** ja plan 的 phon_id
   里有 f / ty / dy / v / vy, 但在线上语料里这 5 个音素出现次数都是 **0**;
   同期 h=109、ch=51、j=25、b=56、by=16。**ふ 在线上 100% 唱作 ['h','u'],
   ['f','u'] 一次都没出现过。** 所以默认输出走线上有先例的传统近似:
       ふ->['h','u']  ふぁ/ふぇ/ふぉ->['h','a']/['h','e']/['h','o']
       てぃ->['ch','i']  てゃ/てゅ/てょ->['ch','a']/['ch','u']/['ch','o']
       でぃ->['j','i']   でゃ/でゅ/でょ->['j','a']/['j','u']/['j','o']
       ゔ->['b','u']  ゔぁ/ゔぃ/ゔぇ/ゔぉ->['b','a']/['by','i']/['b','e']/['b','o']
       ゔゃ/ゔゅ/ゔょ->['by','a']/['by','u']/['by','o']
   代价是 ファイト 会唱成 "ハイト"、パーティー 唱成 "パーチー"、ヴァイオリン
   唱成 "バイオリン" —— 这正是这些外来音进日语时的传统写法, 但**跟片假名字面
   不一致**, 需要字面音的调用方传 `allow_unattested=True`。
2. **`allow_unattested=True` 的读法线上无先例, 效果未经验证。** 打开开关后
   会输出 f / ty / dy / v / vy。这些音素在 plan 的 phon_id 里合法, 引擎不会
   报 453, 但线上 4,716 个 note 里一次都没出现过, 声学模型在这些音素上的表现
   **我们没有任何线上样本可以佐证**, 音色可能不稳定。请自行试听后再用。
3. **fy 保留但极罕见。** ふぃ 仍输出 ['fy','i'](fy 线上出现 2 次, 都是
   ('fy','i')); ふゃ/ふゅ/ふょ 仍输出 ['fy',*]。按"零次才替换"的规则它有先例
   所以保留, 但 2/4716 的样本量意味着效果同样谈不上验证充分。
4. **note 数 = mora 数, 不等于假名数。** 促音 っ -> ['cl']、撥音 ん -> ['nv']、
   长音 ー -> 延续前一元音, 三者各占一个独立 note; 而拗音/外来音两个假名
   (きゃ、てぃ、ゔぁ …)只占一个 note。所以 ちょっと = 3 个 note,
   ぱーてぃー = 4 个 note。
5. **小假名的两个方向都要注意。**
   - 跟前一个假名能组成 KANA_DIGRAPH 的(てぃ、しゃ、ゔぁ …): 2 个假名 = 1
     个 note, 因为它是 1 个 mora。
   - 组不成的(ねぇ、まぁ、ふぅ、ちぃ …): 小假名**自成一个 note**, 因为它就是
     第 2 个 mora。ねぇ -> [['n','e'],['e']], 与 ねー 输出完全相同;
     ふぅ -> [['h','u'],['u']]。
   这不是不一致, 是按 mora 切分的必然结果; 但如果客户曲谱把 ねぇ 当作 1 个
   note, 音节数就会对不上, 需要调用方自己合并。
   非常规写法(ねぁ 这种小元音跟前一个元音对不上的)按字面发该元音: [['n','e'],['a']]。
6. **分隔符统一跳过, 且不会被当成长音。** ・(U+30FB)、·、‧、ASCII `-`、
   全角 －、‐ ‑ ‒ – — ―、− 全部当分隔符静默跳过(ハーフ・タイム 与
   ハーフ-タイム 输出一致)。**如果你想要长音, 必须写 ー(U+30FC) 或 〜/~**,
   写成 `-` 会被丢掉、少一个 mora, 而且不会报错。
7. **汉字一律报错, 不猜读音。** 汉字、々〆〻、叠字符 ゝゞヽヾ、拉丁字母都抛
   ValueError, 请调用方先把歌词转成假名。本工具没有词典, 也不做形态分析,
   所以像 は 读 wa、へ 读 e 这类**助词音变一概不做** —— こんにちは 输出的是
   ['h','a'] 而不是 ['w','a']。を 是唯一的例外, 按惯例直接映射成 ['o']。
8. **引擎只要求每个 note 至少一个元音, 不是恰好一个。** (twob/validators.py
   的 check_vowel; 线上 spa 数据里就有 119 个 note 含 2 个以上元音。)
   "一个 note 恰好一个元音"是**本工具的自我约束**, 不是引擎硬限制。后果:
   客户曲谱若把整个词放进一个 note, 本工具切出的 note 数会更多。
9. **っ 后面不能直接跟长音符。** っー 会抛 ValueError(cl 不在
   vowel_holding_dict 里)。ん 后面可以(んー -> [['nv'],['nv']])。
   开头就是长音符也会抛 ValueError。
10. **输入非字符串时按 str() 处理。** lyrics_to_notes_ja(None) 会因为 'N'
    是拉丁字母而抛 ValueError(而不是 TypeError); 空串返回 []。
"""


# ============================================================================
#  西班牙语 (Spanish) —— 正字法规则 -> 引擎音素
# ============================================================================
# ------------------------------------------------------------------ 本工具会用到的音素
# 元音(tail): 5 个单元音 + 上升二合元音 + 下降二合元音 + 成音节 m
_TAILS = frozenset([
    "a", "e", "i", "o", "u",
    "ja", "je", "jo", "ju", "wa", "we", "wi", "wo",
    "aj", "ej", "oj", "uj", "aw", "ew", "ow",
    "mv",
])

_FRONT = frozenset("eiéí")            # c / g / qu / gu 的前元音环境
_GLIDE = {"i": "j", "u": "w"}         # 滑音字母 -> 滑音符号

# 元音字母 -> (基本元音, 能否充当滑音)。带锐音符的 í/ú 破坏二合元音(río / país)
_VOWELS = {
    "a": ("a", False), "e": ("e", False), "i": ("i", True),
    "o": ("o", False), "u": ("u", True), "ü": ("u", True),
    "á": ("a", False), "é": ("e", False), "í": ("i", False),
    "ó": ("o", False), "ú": ("u", False),
}
# 混排他语言时的变音符号容错: 一律去符号
_FOLD = {"à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
         "â": "a", "ê": "e", "î": "i", "ô": "o", "û": "u",
         "ä": "a", "ë": "e", "ï": "i", "ö": "o", "ü": "ü",
         "ã": "a", "õ": "o", "ç": "s"}

_CONS = {
    "b": "b", "d": "d", "f": "f", "k": "k", "l": "l", "m": "m",
    "n": "n", "p": "p", "s": "s", "t": "t",
    "v": "b",      # 西语 b / v 同音
    # seseo: z / ce / ci 一律读 s。音素表里**有** θ(tt, 按"双写 = 大写 X-SAMPA"
    # 的解码规则 tt = X-SAMPA T = θ), 不用它是因为 tt 在线上 6338 个西语 note 里
    # 出现 0 次, 属于"合法但无训练先例", 与 caveat 4 同一条理由 —— 不是因为
    # 音素表缺 θ。半岛 distinción 若要做, 音素是够的, 缺的是线上先例。
    "z": "s",
    "j": "x",      # jugar
    "ñ": "jj",     # ɲ
    "w": "w",      # 外来词
}
_LETTERS = frozenset(list(_VOWELS) + list(_CONS) + list("cghqrxy"))
_JOINERS = frozenset(["-", "­", "_", "·"])   # 字母间的连字符视为同一个词
_NASALS = frozenset(["m", "n", "nn", "jj"])
_CL_L = frozenset(["p", "b", "f", "g", "k"])      # 合法起首丛 C + l
_CL_R = frozenset(["p", "b", "f", "g", "k", "t", "d"])   # C + ɾ


def _words(text):
    """切词。字母之间的连字符不算分词点, 这样 co-ra-zón 与 corazón 同结果。"""
    text = unicodedata.normalize("NFC", text or "").lower()
    text = "".join(_FOLD.get(ch, ch) for ch in text)
    out, buf, n = [], [], len(text)
    for i, ch in enumerate(text):
        if ch in _LETTERS:
            buf.append(ch)
        elif ch in ("'", "’"):            # pa'l -> pal
            continue
        elif ch in _JOINERS and buf and i + 1 < n and text[i + 1] in _LETTERS:
            continue
        elif buf:
            out.append("".join(buf)); buf = []
    if buf:
        out.append("".join(buf))
    return out


def _degeminate(segs):
    """相邻的同一个辅音音素塌缩成一个。

    西语没有音位性长辅音, 双写只是正字法: 外来词 ro-ck / ja-zz / ha-ppy 以及
    西语自身的 sc(a-scensor) / nn(i-nnato) 都不该在输出里出现叠辅音。
    只塌缩**音素**相同的相邻辅音, 所以 acción(k + s)、carro(rr -> r)不受影响。
    中间只隔着不发音的 h 也算相邻(h 没有音, 挡不住塌缩)。
    """
    out, last_c = [], None
    for seg in segs:
        if seg[0] == "C":
            if seg[1] == last_c:
                continue
            last_c = seg[1]
        elif seg[0] == "V":
            last_c = None
        out.append(seg)
    return out


def _segment(word):
    """词 -> [('C', 音素) | ('V', (基本元音, 能否滑音)) | ('H', None)]。

    'H' 是不发音的 h 留下的隔断标记: 它自己不产生音素, 只用来阻止 _nuclei
    把它两侧的元音合成二合元音(a-hu-mar 而不是 *au-mar)。
    """
    segs, i, n = [], 0, len(word)
    while i < n:
        c = word[i]
        nx = word[i + 1] if i + 1 < n else ""
        nx2 = word[i + 2] if i + 2 < n else ""
        if c in _VOWELS:
            segs.append(("V", _VOWELS[c])); i += 1
        elif c == "c":
            if nx == "h":
                segs.append(("C", "tss")); i += 2          # ch -> tʃ
            else:
                segs.append(("C", "s" if nx in _FRONT else "k")); i += 1
        elif c == "l" and nx == "l":
            # ll 只有在起首(后面跟元音)才是 ʝ; 词尾/韵尾的 ll 只可能来自外来词
            # (roll / bill / full), 腭擦音不能作韵尾, 读 /l/。
            segs.append(("C", "jsl" if nx2 in _VOWELS else "l")); i += 2
        elif c == "r":
            if nx == "r":
                segs.append(("C", "r")); i += 2            # rr -> 颤音
            else:
                segs.append(("C", "for")); i += 1          # 单 r 先按闪音, 后按环境改
        elif c == "q":
            # que / qui 的 u 不发音; quá 之类保留 u 作滑音
            segs.append(("C", "k")); i += 2 if (nx == "u" and nx2 in _FRONT) else 1
        elif c == "g":
            if nx in _FRONT:
                segs.append(("C", "x")); i += 1            # gente / gitano
            elif nx == "u" and nx2 in _FRONT:
                segs.append(("C", "g")); i += 2            # gue / gui
            else:
                segs.append(("C", "g")); i += 1            # gato / güe(ü 留作滑音)
        elif c == "h":
            segs.append(("H", None)); i += 1               # 不发音, 但阻断二合元音
        elif c == "x":
            if not segs:
                segs.append(("C", "s"))                    # xilófono
            elif nx in _VOWELS:
                segs.extend([("C", "k"), ("C", "s")])      # examen -> ek-sa-men
            else:
                segs.append(("C", "s"))                    # extra -> es-tra
            i += 1
        elif c == "y":
            segs.append(("C", "jsl") if nx in _VOWELS      # yo / mayo
                        else ("V", ("i", True)))           # soy / muy / y
            i += 1
        elif c in _CONS:
            segs.append(("C", _CONS[c])); i += 1
        else:
            i += 1
    return _degeminate(segs)


def _nuclei(run):
    """一串相邻元音字母 -> 若干核, 每核恰好一个 tail(本工具的自我约束)。

    ia/ie/ue -> ja/je/we(上升); ai/ei -> aj/ej(下降);
    三合元音拆成"滑音辅音 + 下降二合元音": buey -> w + ej。
    """
    out, i, n = [], 0, len(run)
    while i < n:
        base, glidecap = run[i]
        glide, j = None, i
        if glidecap and i + 1 < n and run[i + 1][0] != base:
            glide, base, j = _GLIDE[base], run[i + 1][0], i + 1
        off = None
        if j + 1 < n and run[j + 1][1] and run[j + 1][0] != base:
            off, j = _GLIDE[run[j + 1][0]], j + 1
        if off and (base + off) in _TAILS:
            core = [base + off]
        elif off:
            core = [base, off]                     # 兜底: 后滑音降级为辅音
        else:
            core = [base]
        if glide:
            fused = glide + base
            core = [fused] if (off is None and fused in _TAILS) else [glide] + core
        out.append(core)
        i = j + 1
    return out


def _items(word):
    """把元音串折叠成核: [('C', ph) | ('N', [ph, ...])]。

    'H'(不发音的 h)在这里被消费掉: 它不产生任何音素, 但会把元音串截断,
    因此 a-h-u 是两个核, 不是一个 aw。
    """
    items, run = [], []
    for kind, val in _segment(word):
        if kind == "V":
            run.append(val)
            continue
        if run:
            items.extend(("N", nu) for nu in _nuclei(run)); run = []
        if kind == "C":
            items.append(("C", val))
    if run:
        items.extend(("N", nu) for nu in _nuclei(run))
    return items


def _onset_len(cluster):
    """辅音丛里有几个归下一音节的起首: 只有 C+l / C+ɾ 能带走两个。"""
    if not cluster:
        return 0
    if len(cluster) >= 2:
        a, b = cluster[-2], cluster[-1]
        if (b == "l" and a in _CL_L) or (b == "for" and a in _CL_R):
            return 2
    return 1


def _syllabify(items):
    """起首最大化 + 合法辅音丛, 返回逐音节音素列表。"""
    pos = [i for i, (k, _) in enumerate(items) if k == "N"]
    if not pos:
        return []
    sylls = []
    for k, p in enumerate(pos):
        if k == 0:
            onset = [v for kk, v in items[:p] if kk == "C"]
        else:
            cluster = [v for kk, v in items[pos[k - 1] + 1:p] if kk == "C"]
            take = _onset_len(cluster)
            sylls[-1].extend(cluster[:len(cluster) - take])      # 余下的做上一音节韵尾
            onset = cluster[len(cluster) - take:] if take else []
        sylls.append(list(onset) + list(items[p][1]))
    sylls[-1].extend(v for kk, v in items[pos[-1] + 1:] if kk == "C")
    return sylls


def _allophones(sylls):
    """词内环境修正: b/d/g 近音化、r 颤音/闪音、n 在软腭音前。

    环境一律只看词内(与线上客户端一致), 不做跨词连音。
    """
    flat, owner = [], []
    for si, s in enumerate(sylls):
        flat.extend(s); owner.extend([si] * len(s))
    src = list(flat)
    for i, ph in enumerate(src):
        left = src[i - 1] if i > 0 else None        # None = 词首(等价于停顿后)
        right = src[i + 1] if i + 1 < len(src) else None
        if ph in ("b", "d", "g"):
            # 停顿后、鼻音后(d 还有 l 后)是塞音, 其余位置是近音 β / ð / ɣ
            if left is None or left in _NASALS or (ph == "d" and left == "l"):
                continue
            flat[i] = {"b": "bb", "d": "dd", "g": "gg"}[ph]
        elif ph == "for":
            # rosa / honra / alrededor / israel 用颤音, 其余(caro, tren, amor)用闪音
            if left is None or left in ("n", "l", "s"):
                flat[i] = "r"
        elif ph == "n" and right in ("k", "g"):
            flat[i] = "nn"                          # cinco / tengo -> ŋ
    out = [[] for _ in sylls]
    for ph, si in zip(flat, owner):
        if out[si] and out[si][-1] == ph:
            continue        # 音变(bb bb)或滑音兜底(w w)也不留叠音
        out[si].append(ph)
    return out


def lyrics_to_notes_es(text):
    """西语歌词 -> 逐音符音素; 每个内层 list 是一个音节(一个 note)。"""
    notes = []
    for word in _words(text):
        items = _items(word)
        sylls = _syllabify(items)
        if not sylls:
            # 纯辅音的哼唱: mmm / hmm -> 成音节 m; 其余(sh 之类)不产生 note
            cons = [v for k, v in items if k == "C"]
            if cons and all(v == "m" for v in cons):
                notes.append(["mv"])
            continue
        notes.extend(_allophones(sylls))
    return notes


# ============================================================================
#  统一入口与命令行
# ============================================================================

# 对外文档里的语言代号 -> 本模块的转换函数
_DISPATCH = {
    "en": lyrics_to_notes_en,
    "jp": lyrics_to_notes_ja,
    "ja": lyrics_to_notes_ja,
    "spa": lyrics_to_notes_es,
    "es": lyrics_to_notes_es,
}

SUPPORTED = ("en", "jp", "spa")


def lyrics_to_notes(language, text, **kwargs):
    """按对外语言代号分发。中文请改用音符的 `syllable` 字段, 不走这里。"""
    if language in ("ch", "cn", "zh"):
        raise ValueError(
            "Chinese does not need this tool: put the pinyin (or a single Chinese "
            "character) in the note's `syllable` field and the service converts it."
        )
    fn = _DISPATCH.get(language)
    if fn is None:
        raise ValueError("unsupported language %r; supported: %s"
                         % (language, ", ".join(SUPPORTED)))
    return fn(text, **kwargs)


def notes_to_aces(notes, language, start=0.0, seconds_per_note=0.5, pitch=62):
    """把音素列表铺成一个最简 ACES 骨架, 便于直接提交试听。

    时值与音高是等分的占位值 —— 真实工程里应当按您的曲谱来填。
    """
    out = []
    t = start
    for phones in notes:
        out.append({
            "start_time": round(t, 4),
            "end_time": round(t + seconds_per_note, 4),
            "type": "general",
            "language": language,
            "pitch": pitch,
            "phone": list(phones),
        })
        t += seconds_per_note
    return {"version": 1.0, "notes": out}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    language, text = argv[0], argv[1]
    aces_path = None
    if "--aces" in argv:
        i = argv.index("--aces")
        aces_path = argv[i + 1] if i + 1 < len(argv) else "out.aces"
    try:
        notes = lyrics_to_notes(language, text)
    except ValueError as ex:
        print("转换失败: %s" % ex, file=sys.stderr)
        return 1
    print(json.dumps(notes, ensure_ascii=False))
    if aces_path:
        with open(aces_path, "w", encoding="utf-8") as fp:
            json.dump(notes_to_aces(notes, language), fp, ensure_ascii=False, indent=2)
        print("已写出 %s (%d 个音符, 时值与音高是占位值, 请按您的曲谱调整)"
              % (aces_path, len(notes)), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
