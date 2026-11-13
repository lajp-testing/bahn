"""The note reader: a dealer's note, in Finnish, Swedish or English, to the facts it states.

A note is a few sentences. Each sentence is about one thing: when the car is ready, a handover after
payment, the pickup site's hours, the delivery site's hours, a deadline at the destination, the
gearbox, the plates, the tyres on the car, or nothing that matters (greetings, references, keys,
tyres in the boot). The reader names each sentence's subject from its words and reads its day and
time. It is sure about a note when it knows the subject of every sentence that holds a time.

RULES.md says how days and times read: a time without a day is on the day the request arrives, a
weekday name is 2 to 6 days later, an hour in words is a working hour ("two" is 14:00, "half three"
14:30), a correction counts and a denied time does not.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

DAY = 24 * 60


@dataclass
class Facts:
    """What a note states. None and False mean: the note does not change it."""
    ready: Optional[int] = None  # the first minute the car can be collected: ready, or handed over after payment
    pickup_hours: Optional[tuple[Optional[int], Optional[int]]] = None  # (opens, closes) as minutes of the day; None keeps the stated one
    delivery_hours: Optional[tuple[Optional[int], Optional[int]]] = None
    deadline: Optional[int] = None  # the car must be at the destination by this minute
    manual: bool = False
    plates: bool = False
    summer_tyres: bool = False
    sure: bool = True  # False when a sentence holds a time whose subject the reader does not know


# --- words ---

_ACCENTS = str.maketrans("äöåé", "aoae")

# Words the reader decides on. A longer word one typo away from one of these reads as that word.
_LEXICON = set("""
tanaan huomenna ylihuomenna today tomorrow imorgon morgon overmorgon idag arkisin weekdays vardagar
maanantai maanantaina tiistai tiistaina keskiviikko keskiviikkona torstai torstaina perjantai perjantaina lauantai lauantaina sunnuntai sunnuntaina
monday tuesday wednesday thursday friday saturday sunday mandag tisdag onsdag torsdag fredag lordag sondag
valmis valmistuu noudettavissa aikaisintaan alkaen jalkeen vasta ready earliest tidigast forst framat hamtas noutaa hakea haettava nouto pickup collect
before ennen after until klockan kello
maksun maksettu maksu maksaa payment betalning luovutus luovutetaan released ostaja buyer
liike kiinni sulkee aukioloajat close closes oppet stanger kohde kohteen vastaanotto vastaanottava vastaanottaja perilla toimitusosoite
destination receiving mottagning mottagaren toimitus saakka onnistuu
mennessa viimeistaan latest senast framme oltava
manuaali manuaalia manuaalivaihteinen manuaalivaihteet manuaalikortin manual manuell kasivaihteet automaatti
kilvet kilpia rekisterikilvet siirtokilvet koekilvet rekkareita plates unregistered skyltar provskyltar rekisterista
kesarenkaat kesarenkailla talvirenkaita summer winters sommardack tyres
korjaus correction rattelse paikalla kotona tavattavissa omistaja deliver delivery vastaanotetaan toimitukset plats platsen luovutuksia opening kasivaihteinen
""".split())


def _one_typo(a: str, b: str) -> bool:
    """True when `a` becomes `b` by one changed, added, dropped or swapped letter."""
    if abs(len(a) - len(b)) > 1:
        return False
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    if len(a) == len(b):
        return a[i + 1:] == b[i + 1:] or (a[i:i + 2] == b[i:i + 2][::-1] and a[i + 2:] == b[i + 2:])
    longer, shorter = (a, b) if len(a) > len(b) else (b, a)
    return longer[i + 1:] == shorter[i:]


def _word(word: str) -> str:
    if word in _LEXICON or len(word) < 5:
        return word
    near = [known for known in _LEXICON if len(known) >= 5 and _one_typo(word, known)]
    return near[0] if len(near) == 1 else word


_WEEKDAYS = {
    0: "maanantai maanantaina monday mandag", 1: "tiistai tiistaina tuesday tisdag", 2: "keskiviikko keskiviikkona wednesday onsdag",
    3: "torstai torstaina thursday torsdag", 4: "perjantai perjantaina friday fredag", 5: "lauantai lauantaina saturday lordag",
    6: "sunnuntai sunnuntaina sunday sondag",
}
_SHORT_DAYS = {  # short forms, by the note's language: "to" is Thursday in Finnish and a word in English
    "fi": {"ma": 0, "ti": 1, "ke": 2, "to": 3, "pe": 4, "la": 5, "su": 6},
    "sv": {"man": 0, "tis": 1, "ons": 2, "tors": 3, "tor": 3, "fre": 4, "lor": 5, "son": 6},
    "en": {"mon": 0, "tue": 1, "tues": 1, "wed": 2, "thu": 3, "thur": 3, "thurs": 3, "fri": 4, "sat": 5, "sun": 6},
}
_DAY_WORD = {word: day for day, words in _WEEKDAYS.items() for word in words.split()}

# An hour in words. The stem decides; the ending says it is a time ("kahdelta", "neljästä alkaen", "viiteen mennessä").
_HOUR_WORDS = [
    (12, r"kahde\w*toista|kaksitoista|tolv|twelve"), (11, r"yhde\w*toista|yksitoista|elva|eleven"), (10, r"kymmene\w*|tio|ten"),
    (9, r"yhdeksa\w*|nio|nine"), (8, r"kahdeksa\w*|atta|eight"), (1, r"yhde\w*|yhte\w*|yhta|yksi|ett|one"), (2, r"kahde\w*|kahte\w*|kaksi|tva|two"),
    (3, r"kolme\w*|tre|three"), (4, r"nelja\w*|nelje\w*|fyra|four"), (5, r"viide\w*|viite\w*|viitt\w*|viisi|fem|five"),
]
_HALF = {"puoli", "puolta", "halv", "half"}
_TIME_BEFORE = {"klo", "kl", "kello", "klockan", "at", "by", "before", "until", "from", "after", "ennen", "senast", "tidigast", "till", "than", "pickup"} | _HALF
_TIME_AFTER = {"alkaen", "jalkeen", "mennessa", "asti", "saakka", "latest", "een", "aan", "sta", "valilla"}


def _hour_word(word: str) -> Optional[int]:
    for hour, pattern in _HOUR_WORDS:
        if re.fullmatch(pattern, word):
            # A working hour, 9 to 17: "two" is 14:00. Eight has no working hour.
            return hour if hour >= 9 else hour + 12 if hour <= 5 else None
    return None


# --- one sentence to tokens ---

_CLOCK = r"(\d{1,2})(?:[.:](\d{2}))?\s*(am|pm)?"


def _minutes(hour: str, minute: Optional[str], half: Optional[str]) -> Optional[int]:
    h, m = int(hour), int(minute or 0)
    if half == "pm" and h < 12:
        h += 12
    if half == "am" and h == 12:
        h = 0
    return h * 60 + m if h <= 24 and m < 60 else None


def _tokens(sentence: str, language: str) -> list[str]:
    """The sentence as words, with each time as `T<minutes>`, each range as `R<opens>_<closes>`, each day as
    `D<days from the arrival day>` or `W<weekday>`, and numbers that are not times taken out."""
    s = sentence
    s = re.sub(r"\b\d{5,}\b", " ", s)  # references and order numbers
    s = re.sub(r"\b(koodi|code|kod|ruudussa|ruutu|bay|plats|paikka|nro|no|nr|ref|viite)\s*:?\s*\d+", " ", s)
    s = re.sub(r"\b\d+\s*(min|sarjaa|srajaa|kesarengasta|talvirengasta|rengasta|tkm|km|set|sets|kpl|st)\b", " ", s)
    s = re.sub(r"\b(ma|mon|man)\s*-\s*(pe|fri|fre)\b", " arkisin ", s)
    s = re.sub(r"\bday after tomorrow\b", " ylihuomenna ", s)
    s = re.sub(r"\bi (over)?morgon\b", r" \1morgon ", s)
    s = re.sub(r"(\d):(sta|een|aan|ksi|lta)\b", r"\1 \2", s)  # "10:stä 16:een"

    def span(match: "re.Match[str]") -> str:
        a = _minutes(match[1], match[2], match[3] or match[6])
        b = _minutes(match[4], match[5], match[6])
        return f" R{a}_{b} " if a is not None and b is not None and a < b else match[0]

    s = re.sub(_CLOCK + r"\s*(?:-|to|till|sta)\s*" + _CLOCK + r"(?:\s*(?:een|aan)\b)?", span, s)
    s = re.sub(r"\b(noon|midday|keskipaivalla|keskipaiva)\b", " T720 ", s)
    s = re.sub(r"\b(?:klo|kl|kello|klockan)\s*(\d{2})(\d{2})\b", lambda m: f" T{int(m[1]) * 60 + int(m[2])} " if int(m[1]) <= 24 and int(m[2]) < 60 else m[0], s)

    def clock(match: "re.Match[str]") -> str:
        minutes = _minutes(match[1], match[2], match[3])
        return f" T{minutes} " if minutes is not None else match[0]

    s = re.sub(r"\b(\d{1,2})[.:](\d{2})\s*(am|pm)?\b", clock, s)
    s = re.sub(r"\b(\d{1,2})()\s*(am|pm)\b", clock, s)
    s = re.sub(r"\b(?:klo|kl|kello|klockan|at)\s*(\d{1,2})()()\b", clock, s)

    words = [word if word[0] in "TR," else _word(word) for word in re.findall(r"[TR]\d+(?:_\d+)?|[a-z]+|\d+|,", s)]
    short = _SHORT_DAYS.get(language, {})
    out: list[str] = []
    for i, word in enumerate(words):
        before, after = (words[i - 1] if i else ""), (words[i + 1] if i + 1 < len(words) else "")
        timely = before in _TIME_BEFORE or after in _TIME_AFTER or before[:1] in ("D", "W") and before[1:].isdigit() or before in _DAY_WORD or before in short
        if word in ("tanaan", "today", "idag"):
            out.append("D0")
        elif word in ("huomenna", "tomorrow", "morgon", "imorgon", "tmrw", "tmr", "tmw"):
            out.append("D1")
        elif word in ("ylihuomenna", "overmorgon"):
            out.append("D2")
        elif word in _DAY_WORD:
            out.append(f"W{_DAY_WORD[word]}")
        elif word in short and (after[:1] in ("T", "k") or after.isdigit() or _hour_word(after) is not None or not after or before in ("korjaus", "correction", "rattelse", "kun", "eikun")):
            out.append(f"W{short[word]}")
        elif word.isdigit():
            if len(word) <= 2 and int(word) <= 24 and timely:
                out.append(f"T{int(word) * 60}")
            # any other number is not a time: a count, a code
        elif _hour_word(word) is not None and (timely or word.endswith(("lta", "ltatoista"))):
            minutes = _hour_word(word) * 60
            if before in _HALF:  # half an hour before the hour
                minutes -= 30
            out.append(f"T{minutes}")
        else:
            out.append(word)
    return out


# --- subjects ---

_PAYMENT = {"maksun", "maksettu", "maksu", "maksaa", "payment", "pays", "betalning"}
_DESTINATION = {"kohde", "kohteen", "vastaanotto", "vastaanottava", "vastaanottaja", "vastaanotetaan", "perilla", "toimitusosoite", "toimitus", "toimitukset",
                "destination", "receiving", "deliver", "delivery", "mottagning", "mottagaren", "framme"}
_BY = {"mennessa", "viim", "viimeistaan", "latest", "later", "senast", "by", "oltava", "must"}
_HOURS = {"auki", "open", "opening", "oppet", "aukioloajat", "kiinni", "sulkee", "close", "closes", "stanger", "arkisin", "weekdays", "vardagar", "asti",
          "saakka", "only", "vain", "till", "until", "onnistuu"}
_READY = {"valmis", "valmistuu", "ready", "klar", "aikaisintaan", "earliest", "tidigast", "forst", "framat", "alkaen", "jalkeen", "vasta", "from"}
_PICKUP = {"nouto", "noudettavissa", "noutaa", "haettava", "hakea", "haku", "pickup", "pick", "collect", "hamtas", "hamtning", "liike", "we", "vi", "auton", "luovutuksia"}
_OWNER = {"myyja", "seller", "saljaren", "omistaja", "owner", "agaren", "asiakas", "customer", "kunden"}  # a private address
_AT_HOME = {"paikalla", "home", "hemma", "kotona", "tavattavissa"}
_COLLECTS = {"hakemaan", "hakee", "noutaa", "picks", "collects", "hamtar"}
_UNTIL = {"ennen", "before", "fore", "kiinni", "sulkee", "close", "closes", "stanger", "asti", "saakka", "till", "until", "ketaan", "enaa"}
_CORRECTIONS = ("korjaus", "correction", "rattelse", "ei kun", "eikun", "eiku", "no wait", "sorry", "nej")


def _is(token: str, kinds: str) -> bool:
    return token[:1] in kinds and token[1:2].isdigit()


def _when(tokens: list[str], arrived: int, base: tuple[Optional[int], Optional[int]] = (None, None)) -> tuple[Optional[int], Optional[int]]:
    """The last day and the last time in the tokens: (days from the arrival day, minutes of the day)."""
    day, minute = base
    for token in tokens:
        if _is(token, "D"):
            day = int(token[1:])
        elif _is(token, "W"):
            ahead = (int(token[1:]) - arrived // DAY) % 7
            day = ahead if ahead >= 2 else ahead + 7  # a weekday name is 2 to 6 days after the arrival day
        elif _is(token, "T"):
            minute = int(token[1:])
    return day, minute


def _span(tokens: list[str], base: tuple[Optional[int], Optional[int]] = (None, None)) -> tuple[Optional[int], Optional[int]]:
    """Opening hours in the tokens: a range, or one closing time."""
    opens, closes = base
    for token in tokens:
        if _is(token, "R"):
            opens, closes = (int(part) for part in token[1:].split("_"))
        elif _is(token, "T"):
            closes = int(token[1:])
    return opens, closes


def _subject(bag: set[str], sentence: str, ranged: bool) -> Optional[str]:
    """What a clause with a time is about, from its words."""
    not_before = bool(re.search(r" (ei|not|inte|ej) (ready )?(ennen|before|fore) ", sentence))
    until = bool(bag & _UNTIL) and not not_before
    if bag & _PAYMENT or {"ostaja", "ensin"} <= bag or {"buyer", "first"} <= bag:
        return "ready"
    if bag & _OWNER and bag & _AT_HOME:
        return "slot"  # the booked hour of a private address, which the request states
    if bag & _DESTINATION and bag & _BY or bag & _OWNER and bag & _COLLECTS or "there" in bag and "by" in bag:
        return "deadline"
    if bag & _DESTINATION:
        return "delivery_hours"
    if bag & _PICKUP and bag & _BY:
        return "pickup_hours"  # "pickup by 7pm at the latest"
    if bag & {"valmis", "valmistuu", "ready", "klar"} and not ranged:
        return "ready"  # also "won't be ready until Friday 15.30"
    if bag & _BY and not bag & _HOURS:
        return "deadline"  # "viimeistään maanantai klo 18"
    if (bag & _READY or not_before) and not until and not ranged:
        return "ready"
    if bag & (_PICKUP | _HOURS) or until:
        return "pickup_hours"
    return None


def read(text: str, language: str, arrived: int) -> Facts:
    """Reads a note that arrived at the minute `arrived`."""
    facts = Facts()
    s = text.lower().translate(_ACCENTS).replace("–", "-").replace("—", "-").replace("−", "-")
    words = [_word(word) for word in re.findall(r"[a-z]+", s)]
    known, spelled = set(words), " ".join(words)

    # The car itself: gearbox, plates, tyres. "Kesärenkaat takakontissa" is luggage; "kesärenkaat alla" is on the car.
    manual = known & {"manuaali", "manuaalia", "manuaalivaihteinen", "manuaalivaihteet", "manuaalikortin", "manual", "manuell", "kasivaihteet", "kasivaihteinen"}
    facts.manual = bool(manual or re.search(r"stick shift", spelled)) and not re.search(r"\b(not a manual|ei manuaali|inte manuell|ej manuell)", spelled)
    facts.plates = bool(known & {"kilvet", "kilpia", "rekisterikilvet", "siirtokilvet", "koekilvet", "rekkareita", "plates", "unregistered", "skyltar",
                                 "provskyltar", "rekisterista"})
    facts.summer_tyres = bool(re.search(r"(kesarenkaat|sommardack\w*|summer (tyres|tires))( viela| fortfarande)? (alla|on|pa)\b|\bon summer (tyres|tires)|kesarenkailla|ei talvirenk|talvirenkaita ei|no winters|winter (tyres|tires) not|inga vinterdack|vinterdack\w* (inte|ej)", spelled))

    s = re.sub(r"\((?:ei|not|inte|ej)\b[^)]*\)", " ", s)  # a denied time, in brackets
    s = re.sub(r"\b(viim|klo|kl|min|nro|t|n|mvh|esim|huom|obs)\.", r"\1 ", s)  # a full stop that ends no sentence
    s = re.sub(r"\b(ma|ti|ke|to|pe|la|su|mon|tue|wed|thu|fri|man|tis|ons|tors|fre)\.(?=\s*(klo|kl|\d))", r"\1 ", s)
    found: list[list] = []  # [subject, day, minute] or [subject, opens, closes], in the order read
    for sentence in re.split(r"[.!?;]+(?:\s+|$)|\s/\s|\n", s):
        tokens = _tokens(sentence, language)
        # A denied day or time: "ready friday 14:30, not tomorrow", "sulkee klo 15, ei klo 16".
        kept: list[str] = []
        i = 0
        while i < len(tokens):
            if tokens[i] in ("not", "ei", "inte", "ej") and tokens[i + 1:i + 2] not in (["ennen"], ["before"], ["fore"], ["kun"]):
                j = i + 1
                while j < len(tokens) and (tokens[j] in ("klo", "kl", "kello", "at") or _is(tokens[j], "TDW")):
                    j += 1
                if j > i + 1:
                    i = j
                    continue
            kept.append(tokens[i])
            i += 1
        tokens = kept
        if not any(_is(token, "TRDW") for token in tokens):
            continue

        # A correction: what follows it replaces what came before, in this sentence or in the last fact.
        joined = " " + " ".join(token for token in tokens if token != ",") + " "
        mark = next((m for m in _CORRECTIONS if f" {m} " in joined), None)
        correction: list[str] = []
        if mark:
            before, _, after = joined.partition(f" {mark} ")
            correction = after.split()
            if not any(_is(token, "TRDW") for token in before.split()):
                if found:  # "Korjaus: klo 19" corrects the sentence before
                    last = found[-1]
                    last[1], last[2] = (_span if last[0].endswith("hours") else lambda t, b: _when(t, arrived, b))(correction, (last[1], last[2]))
                continue
            cut = tokens.index(mark.split()[0]) if mark.split()[0] in tokens else len(tokens)
            tokens = tokens[:cut]

        # Each clause with a time is about one thing. A clause that does not say what, takes the sentence's words.
        clauses: list[list[str]] = [[]]
        for token in tokens:
            if token == ",":
                clauses.append([])
            else:
                clauses[-1].append(token)
        everything = [token for clause in clauses for token in clause]
        timed = [clause for clause in clauses if any(_is(token, "TR") for token in clause)]
        if not timed:
            continue  # a day without a time changes nothing
        for clause in timed:
            ranged = any(_is(token, "R") for token in clause)
            subject = _subject(set(clause), " " + " ".join(clause) + " ", ranged) or _subject(set(everything), " " + " ".join(everything) + " ", ranged)
            if subject == "slot":
                continue
            if subject is None:
                facts.sure = False
                continue
            # The day can stand in another clause of the sentence: "valmis huomenna, klo 12".
            if subject.endswith("hours"):
                value = _span(clause)
                if correction:
                    value = _span(correction, value)
            else:
                value = _when(clause, arrived, (_when(everything, arrived)[0] if len(timed) == 1 else None, None))
                if correction:
                    value = _when(correction, arrived, value)
            found.append([subject, value[0], value[1]])

    for subject, a, b in found:
        if subject.endswith("hours"):
            setattr(facts, subject, (a, b))
        elif b is None:
            facts.sure = False
        else:
            at = (arrived // DAY + (a or 0)) * DAY + b
            if subject == "ready":
                facts.ready = at if facts.ready is None else max(facts.ready, at)
            else:
                facts.deadline = at if facts.deadline is None else min(facts.deadline, at)
    return facts
