"""Build the CLDF dataset (../cldf) from raw/ and etc/, and read it back for the pages.

Called by cldfbench (../cldfbench_rogn.py, `cldfbench makecldf`) on every build, so the dataset is always
regenerated from the sources plus the curation in etc/. It is never edited by hand: a decision about a
row goes in etc/decisions.csv (see apply_decisions below and etc/README.md).
"""
import csv, re, unicodedata
from collections import defaultdict

from pycldf import Dataset, Source

import step4_build_pages as pages
from paths import RAW, ETC, CLDF, DATA

METADATA = CLDF / "Dictionary-metadata.json"
DAGGER = " †"
TERMS = "http://cldf.clld.org/v1.0/terms.rdf#"

LOMBARD = ("lomb1257", "lmo")
LANGUAGES = [  # ID, Name, Glottocode, ISO 639-3, description, short label used on the pages
    ("rogn", "Lombard: Rögn (Arogno)", *LOMBARD, "The dialect of the course, Lugano district", "Rögn"),
    ("basso-ceresio", "Lombard: Basso Ceresio", *LOMBARD, "Gaggini's glossary", "Basso Ceresio"),
    ("mendrisiotto", "Lombard: Mendrisiotto", *LOMBARD, "", "Mendrisiotto"),
    ("lumino", "Lombard: Lumino (Bellinzonese)", *LOMBARD, "", "Lumino (Bellinzonese)"),
    ("giubiasco", "Lombard: Giubiasco", *LOMBARD, "", "Giubiasco"),
    ("lugano-old", "Lombard: Lugano, older printed texts", *LOMBARD, "Paul e Ghita a Lügan", "Lugano (old printed play)"),
    ("ticinese", "Lombard: Ticino, variety not identified", *LOMBARD, "Sources whose variety is not yet known", ""),
    ("ita", "Italian", "ital1282", "ita", "Meta-language: sense descriptions and translations", None),
    ("eng", "English", "stan1293", "eng", "Meta-language: added translations", None),
]
LABEL = {l[0]: l[5] for l in LANGUAGES}
VARIETY_OF = {"Rögn": "rogn", "Rögn (Arogno)": "rogn", "Basso Ceresio": "basso-ceresio",
              "Mendrisiotto": "mendrisiotto", "Lumino (Bellinzonese)": "lumino", "Giubiasco": "giubiasco",
              "Lugano (old printed play)": "lugano-old"}
AUTHORS = {  # as in ATTRIBUTIONS.md
    "Dizionario con filastrocche di R. Gaggini.docx": "Gaggini, Raffaele",
    "dialett-poesia-Spartaco-Arigoni.pdf": "Arigoni, Spartaco",
    "NUVANT'ANN.pdf": "Tantardini, Celso",
    "2025-02-19-Piove governo ladro di Fausto Boffi.docx": "Boffi, Fausto",
    "Filatrocca di Carlino.docx": "Delucchi, Mario",
    "GP Lavelli 2x.docx": "Lavelli, G. P.",
    "CDE_come_si_scrive_in_dialetto.pdf": "{Centro di dialettologia e di etnografia}",
}
STATUS = {
    "entries": "accepted|pending|inferred|rejected",
    "senses": "attested|supplied|pending|rejected",
    "examples": "accepted|pending|rejected",
    "variants": "accepted|pending|typo|rejected",
    "paradigms": "attested|inferred|rejected",
}
UNSURE = {"direction?": "direction", "split?": "split", "pairing?": "pairing", "meaning?": "meaning"}
SUPPLIED_NOTE = "Italian and English supplied; the lesson gives the dialect only"
NO_ITALIAN_NOTE = "the source gives no Italian; the English is shown in brackets"
TABLE_OF = {"entries.csv": "EntryTable", "senses.csv": "SenseTable", "examples.csv": "ExampleTable",
            "languages.csv": "LanguageTable"}


def slug(text, limit=48):
    s = unicodedata.normalize("NFD", str(text).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:limit].strip("-") or "x"


class Ids:
    """Readable, unique IDs matching CLDF's [a-zA-Z0-9_-]+."""
    def __init__(self, used=()):
        self.used = set(used)

    def make(self, base):
        base, n = slug(base), 2
        out = base
        while out in self.used:
            out, n = f"{base}-{n}", n + 1
        self.used.add(out)
        return out


# ------------------------------------------------------------------ sources
def source_key(name):
    if name == "notes_added_by_hand.csv":
        return "owner-notes"
    if name.startswith("Rosetta Stone"):
        return "owner-spreadsheet"
    return slug(re.sub(r"\.(docx|pdf)$", "", name), 60)


def bib_entry(name, lesson_meta):
    meta = lesson_meta.get(name, {})
    fields = {"title": re.sub(r"\.(docx|pdf)$", "", name), "note": f"raw/{name}"}
    if name.startswith("Rosetta Stone"):
        fields["title"] = "Rosetta Stone: English, Italian, Ticino dialect (owner's own spreadsheet)"
    elif name == "notes_added_by_hand.csv":
        fields["title"] = "Vocabulary from the owner's handwritten course notes"
    elif meta.get("canonical") == "yes":
        fields.update(author="Casellini, Guido", howpublished="Cors da dialett da Rögn, course material")
    if name in AUTHORS:
        fields["author"] = AUTHORS[name]
    year = re.match(r"(20\d\d)-", name)
    if year:
        fields["year"] = year.group(1)
    return Source("misc", source_key(name), **fields)


def cite(name, line=None):
    k = source_key(name)
    return f"{k}[l.{line}]" if line not in (None, "", "0", 0) else k


# ------------------------------------------------------------------ candidates: what the lessons say today
def candidates():
    """Rows in CLDF shape, with provisional IDs, from everything steps 1-2 and etc/ provide."""
    uniq, tables, eng = pages.assemble()
    lesson_meta = {r["file"]: r for r in pages.read(ETC / "lesson_sources.csv")}
    files = set()
    ids = {t: Ids() for t in ("entries", "senses", "examples", "variants", "paradigms")}
    entries, senses, examples, variants, paradigms = {}, [], [], [], []
    by_key = {}

    def entry_for(headword, language, verb=False, **extra):
        # homographs stay apart: the verb `vert` (to open) is not the colour `vert` (green)
        k = (pages.key(headword), language, "verb" if verb else "")
        if k not in by_key:
            eid = ids["entries"].make(headword if language == "rogn" else f"{headword}-{language}")
            by_key[k] = eid
            entries[eid] = {"ID": eid, "Language_ID": language, "Headword": headword, "Part_Of_Speech": None,
                            "Variant_Of": None, "Conjugation_Class": None, "Auxiliary": None, "Status": "accepted",
                            "Comment": None, "Source": []}
        e = entries[by_key[k]]
        for f, v in extra.items():
            if v:
                e[f] = v
        return e

    def add_source(row, ref):
        if ref not in row["Source"]:
            row["Source"].append(ref)

    # verbs first: they own their headwords
    verb_rows = pages.read(DATA / "extracted_verb_forms.csv")
    seen_at = defaultdict(list)
    for v in verb_rows:
        seen_at[(v["tense"], v["person"], pages.key(v["form"]))].append(cite(v["source"], v["line"]))
        files.add(v["source"])
    for name in sorted(tables):
        t = tables[name]
        head = t["dialect"][0] if t["dialect"] else name
        grid = t["grid"]
        aux = "ves" if re.match(r"(ma )?(sum|ta se|l’è)\b", grid["passato prossimo"]["1s"][0]) else "vegh"
        e = entry_for(head, "rogn", verb=True, Part_Of_Speech="verb", Conjugation_Class=t["class"].split(":")[0],
                      Auxiliary=aux, Status="inferred" if t["basis"] == "inferred" else "accepted",
                      Comment=t.get("evidence") or None)
        for f in t["sources"]:
            add_source(e, cite(f))
            files.add(f)
        for form in t["dialect"][1:]:
            variants.append({"ID": ids["variants"].make(f"{e['ID']}-{form}"), "Entry_ID": e["ID"], "Form": form,
                             "Kind": "spelling", "Status": "accepted", "Comment": None, "Source": list(e["Source"])})
        for i, italian in enumerate([name] + t["aliases"]):
            en = eng.get(pages.key(italian))
            senses.append({"ID": ids["senses"].make(f"{e['ID']}-{italian}"), "Entry_ID": e["ID"],
                           "Description": italian, "Description_English": f"to {en}" if en else None,
                           "Status": "attested", "Unsure_About": None,
                           "Comment": f"Italian synonym of {name}" if i else None, "Source": list(e["Source"])})
        for tense in pages.ALL_TENSES:
            for person, (form, inferred) in grid[tense].items():
                if form == "–":
                    continue
                src = [] if inferred else sorted(set(seen_at.get((tense, person, pages.key(form)), [])))[:4]
                paradigms.append({"ID": ids["paradigms"].make(f"{e['ID']}-{tense}-{person}"), "Entry_ID": e["ID"],
                                  "Tense": tense, "Person": person if person != "-" else None, "Form": form,
                                  "Status": "inferred" if inferred else "attested", "Comment": None, "Source": src})

    for p in uniq:
        files.add(p["source"])
        language = VARIETY_OF.get(p.get("variety") or "") or \
            VARIETY_OF.get(lesson_meta.get(p["source"], {}).get("variety", "")) or "ticinese"
        ref = cite(p["source"], p["line"])
        unsure = UNSURE.get(p["check"]) if p["check"] else None
        if p["kind"] == "expression":
            examples.append({"ID": ids["examples"].make(f"{p['source'][:24]}-{p['line']}"), "Language_ID": language,
                             "Primary_Text": p["dialect"], "Translated_Text": p["italian"], "Meta_Language_ID": "ita",
                             "Translated_Text_English": p["english"] or None,
                             "Status": "pending" if unsure else "accepted", "Unsure_About": unsure,
                             "Comment": p["note"] or None, "Source": [ref]})
            continue
        # a word pair whose Italian is one of a verb's infinitives belongs to that verb ("andare = na")
        vk = (pages.key(p["dialect"]), language, "verb")
        verb_entry = entries.get(by_key.get(vk))
        is_verb_sense = verb_entry and any(s["Entry_ID"] == verb_entry["ID"] and pages.key(s["Description"]) ==
                                           pages.key(p["italian"]) for s in senses)
        e = verb_entry if is_verb_sense else entry_for(p["dialect"], language)
        if unsure:
            e["Status"] = "pending"
        add_source(e, ref)
        italian, missing = p["italian"], not p["italian"].strip()
        if missing:
            italian = f"[{p['english'] or '?'}]"             # "[?]": neither Italian nor English is known
        if any(s["Entry_ID"] == e["ID"] and pages.key(s["Description"]) == pages.key(italian) for s in senses):
            continue
        senses.append({"ID": ids["senses"].make(f"{e['ID']}-{italian}"), "Entry_ID": e["ID"], "Description": italian,
                       "Description_English": p["english"] or None,
                       "Status": "supplied" if p.get("supplied") else ("pending" if unsure or missing else "attested"),
                       "Unsure_About": unsure or ("meaning" if missing else None),     # meaning: no Italian given
                       "Comment": SUPPLIED_NOTE if p.get("supplied") else (p["note"] or NO_ITALIAN_NOTE) if missing else (p["note"] or None),
                       "Source": [ref]})
    bib = [bib_entry(f, lesson_meta) for f in sorted(files)]
    return {"entries.csv": list(entries.values()), "senses.csv": senses, "examples.csv": examples,
            "variants.csv": variants, "paradigms.csv": paradigms}, bib


# ------------------------------------------------------------------ the dataset
def configure(ds):
    """Declare everything beyond the Dictionary module's defaults in the metadata: components, added
    columns, the allowed Status values and the foreign keys. ds is the writer's pycldf Dataset."""
    source = {"name": "Source", "propertyUrl": TERMS + "source", "separator": ";", "datatype": "string"}
    comment = {"name": "Comment", "propertyUrl": TERMS + "comment", "datatype": "string"}
    status = lambda t: {"name": "Status", "datatype": {"base": "string", "format": STATUS[t]}}
    unsure = {"name": "Unsure_About", "datatype": {"base": "string", "format": "direction|split|pairing|meaning"},
              "dc:description": "What the extraction was unsure about when it marked the row pending"}
    rid = {"name": "ID", "required": True, "datatype": {"base": "string", "format": "[a-zA-Z0-9_\\-]+"}}
    ds.properties.update({
        "dc:title": "Lexicon of the dialect of Rögn (Arogno), Ticino",
        "dc:description": "Dialect entries, senses (Italian with English), examples and verb paradigms from "
                          "the course Cors da dialett da Rögn and related texts. See README.md.",
        "dc:creator": "Michael Maguire",
        "dc:contributor": "Guido Casellini (course material) and the other authors listed in ATTRIBUTIONS.md",
    })
    ds.add_component("LanguageTable", {"name": "Description", "datatype": "string"})
    ds.add_component("ExampleTable",
                     {"name": "Translated_Text_English", "datatype": "string",
                      "dc:description": "English translation, added; Translated_Text is the Italian"},
                     status("examples"), unsure, source)
    ds.add_columns("EntryTable",
                   {"name": "Variant_Of", "datatype": "string",
                    "dc:description": "ID of the main entry when this entry is a regional variant of it"},
                   {"name": "Conjugation_Class", "datatype": "string"},
                   {"name": "Auxiliary", "datatype": {"base": "string", "format": "ves|vegh"}},
                   status("entries"), comment, source)
    ds.add_columns("SenseTable",
                   {"name": "Description_English", "datatype": "string",
                    "dc:description": "English translation of the Description, which is in Italian"},
                   status("senses"), unsure, comment, source)
    ds.add_foreign_key("EntryTable", "Variant_Of", "EntryTable", "ID")
    ds.add_table("variants.csv", rid, {"name": "Entry_ID", "required": True}, {"name": "Form", "required": True},
                 {"name": "Kind", "datatype": {"base": "string", "format": "spelling|typo|ocr-error"}},
                 status("variants"), comment, source, primaryKey=["ID"])
    ds.add_foreign_key("variants.csv", "Entry_ID", "EntryTable", "ID")
    ds.add_table("paradigms.csv", rid, {"name": "Entry_ID", "required": True}, {"name": "Tense", "required": True},
                 {"name": "Person", "datatype": {"base": "string", "format": "1s|2s|3s|1p|2p|3p"}},
                 {"name": "Form", "required": True}, status("paradigms"), comment, source, primaryKey=["ID"])
    ds.add_foreign_key("paradigms.csv", "Entry_ID", "EntryTable", "ID")


def apply_decisions(rows, decisions):
    """Apply etc/decisions.csv. One row per decision:

      Decision        typo | reject | accept | variant | correct
      Language_ID     variety of the form the decision is about (e.g. rogn, ticinese)
      Form            the headword as it appears in the data, or for an expression its dialect text
      Sense           optional: the Italian of one sense of the entry, to limit the decision to it
      Target_Form     typo/variant: the correct or main headword; correct: the corrected dialect
      Target_Language_ID   typo/variant: the variety the target belongs to, if different
      Italian, English     correct: the corrected Italian and English (blank = unchanged)
      Reason, Date    recorded in the Comment of the rows affected ("Claude inferred: …" when the
                      decision came from Claude's review rather than from the owner)

    typo     the form's entry is folded into the target entry (created if needed), and the form is kept
             in variants.csv with Kind and Status `typo`, so it is recognised but never shown.
    reject   the entry (or with Sense, that sense; or the expression) gets Status `rejected` and the
             reason; the pages leave it out.
    accept   a `pending` entry and its pending senses (or the expression) become accepted / attested.
    variant  same variety: the form becomes an accepted spelling in variants.csv of the target entry;
             other variety: the form's entry gets Variant_Of = the target entry, or if the target does
             not exist yet, is folded into a new target entry with the form kept as a spelling.
    correct  replaces the dialect, Italian and/or English of an entry's sense (all of them, or the one
             named in Sense) or of an expression, and marks it accepted.
    Expressions (examples.csv) can be rejected, accepted or corrected; Form is then their dialect text.
    Returns the decisions that matched nothing, so they can be reported.
    """
    E, S, V, X = rows["entries.csv"], rows["senses.csv"], rows["variants.csv"], rows["examples.csv"]
    ids = Ids(e["ID"] for e in E)
    vids = Ids(v["ID"] for v in V)
    unmatched = []
    key = pages.key

    def find(form, language):
        return next((e for e in E if key(e["Headword"]) == key(form) and e["Language_ID"] == language), None)

    def find_example(form, language):
        return next((x for x in X if key(x["Primary_Text"]) == key(form) and x["Language_ID"] == language), None)

    for d in decisions:
        note = "; ".join(x for x in (d.get("Reason"), d.get("Date") and f"decided {d['Date']}") if x)
        kind = d["Decision"].strip().lower()
        e = find(d["Form"], d["Language_ID"])
        if e is None:
            x = find_example(d["Form"], d["Language_ID"]) if kind in ("reject", "accept", "correct") else None
            if x is None:
                unmatched.append(d)
            elif kind == "reject":
                x["Status"], x["Comment"] = "rejected", note
            else:                                         # the expression's own note stays as the page note
                x["Status"], x["Unsure_About"] = "accepted", None
                if kind == "correct":
                    for field, col in (("Primary_Text", "Target_Form"), ("Translated_Text", "Italian"),
                                       ("Translated_Text_English", "English")):
                        if (d.get(col) or "").strip():
                            x[field] = d[col].strip()
            continue
        mine = [s for s in S if s["Entry_ID"] == e["ID"]]
        if (d.get("Sense") or "").strip():
            mine = [s for s in mine if key(s["Description"]) == key(d["Sense"])]
            if not mine:
                unmatched.append(d)
                continue
        if kind == "reject" and (d.get("Sense") or "").strip():
            for s in mine:
                s["Status"], s["Comment"] = "rejected", note
        elif kind == "reject":
            e["Status"], e["Comment"] = "rejected", note
        elif kind == "accept":
            e["Status"], e["Comment"] = "accepted", note or e["Comment"]
            for s in mine:
                if s["Status"] == "pending":
                    s["Status"] = "attested"
        elif kind == "correct":
            if (d.get("Target_Form") or "").strip():
                e["Headword"] = d["Target_Form"].strip()
            e["Status"], e["Comment"] = "accepted", note
            for s in mine:
                if (d.get("Italian") or "").strip():
                    s["Description"] = d["Italian"].strip()
                    if s["Comment"] == NO_ITALIAN_NOTE:
                        s["Comment"] = None
                if (d.get("English") or "").strip():
                    s["Description_English"] = d["English"].strip()
                s["Status"], s["Unsure_About"] = "attested", None
        elif kind in ("typo", "variant"):
            language = d.get("Target_Language_ID") or d["Language_ID"]
            target = find(d["Target_Form"], language)
            if kind == "variant" and target and language != d["Language_ID"]:
                e["Variant_Of"], e["Comment"] = target["ID"], note
                continue
            if target is None:
                target = dict(e, ID=ids.make(d["Target_Form"] if language == "rogn" else f"{d['Target_Form']}-{language}"),
                              Headword=d["Target_Form"], Language_ID=language, Source=[], Comment=None)
                E.append(target)
            target["Source"] = list(dict.fromkeys((target["Source"] or []) + (e["Source"] or [])))
            have = {key(s["Description"]) for s in S if s["Entry_ID"] == target["ID"]}
            for s in S:
                if s["Entry_ID"] == e["ID"]:
                    if key(s["Description"]) in have:
                        s["Status"], s["Comment"] = "rejected", f"duplicate of a sense of {target['ID']}"
                    else:
                        s["Entry_ID"] = target["ID"]
            for v in V:
                if v["Entry_ID"] == e["ID"]:
                    v["Entry_ID"] = target["ID"]
            V.append({"ID": vids.make(f"{target['ID']}-{d['Form']}"), "Entry_ID": target["ID"], "Form": e["Headword"],
                      "Kind": "typo" if kind == "typo" else "spelling", "Status": "typo" if kind == "typo" else "accepted",
                      "Comment": note, "Source": e["Source"]})
            E.remove(e)
            for s in S:                                   # senses left on the folded entry (duplicates)
                if s["Entry_ID"] == e["ID"]:
                    s["Entry_ID"] = target["ID"]
        else:
            unmatched.append(d)
    return unmatched


def make(writer):
    """cldfbench's cmd_makecldf: fill the writer with the whole dataset."""
    configure(writer.cldf)
    rows, bib = candidates()
    unmatched = apply_decisions(rows, pages.read(ETC / "decisions.csv"))
    writer.cldf.add_sources(*bib)
    writer.objects["LanguageTable"] = [{"ID": i, "Name": n, "Glottocode": g, "ISO639P3code": iso, "Description": d}
                                       for i, n, g, iso, d, _ in LANGUAGES]
    for url, rs in rows.items():
        writer.objects[TABLE_OF.get(url, url)] = sorted(rs, key=lambda r: r["ID"])
    print(f"cldf: {len(rows['entries.csv'])} entries, {len(rows['senses.csv'])} senses, "
          f"{len(rows['examples.csv'])} examples, {len(rows['variants.csv'])} variants, "
          f"{len(rows['paradigms.csv'])} paradigm cells, {len(bib)} sources")
    for d in unmatched:
        print(f"  WARNING: decision matched nothing: {d['Decision']} {d['Language_ID']} {d['Form']!r}")


def load():
    ds = Dataset.from_metadata(METADATA)
    return ds, {t.url.string: [dict(r) for r in t] for t in ds.tables}


# ------------------------------------------------------------------ reading it back for the pages
def for_pages():
    """(uniq, tables, eng) in the shapes step4_build_pages.render() expects, from the lexicon only.
    Rows marked rejected, and variants marked typo, are left out."""
    _, rows = load()
    bib_file = {}
    for line in (CLDF / "sources.bib").read_text().split("@misc{")[1:]:
        k = line.split(",", 1)[0].strip()
        m = re.search(r"note = \{(?:Dialect/)?(?:raw/)?(.+?)\}", line)
        bib_file[k] = m.group(1) if m else k

    def origin(refs):
        if not refs:
            return "", ""
        m = re.match(r"([^\[]+)(?:\[l\.(\d+)\])?", refs[0])
        return bib_file.get(m.group(1), m.group(1)), m.group(2) or "0"

    entries = {e["ID"]: e for e in rows["entries.csv"] if e["Status"] != "rejected"}
    uniq = []
    for s in rows["senses.csv"]:
        e = entries.get(s["Entry_ID"])
        if not e or s["Status"] == "rejected" or (e["Part_Of_Speech"] == "verb" and not _in_word_list(s)):
            continue
        src, line = origin(s["Source"] or e["Source"])
        pending = "pending" in (s["Status"], e["Status"])
        uniq.append({"italian": s["Description"], "dialect": e["Headword"], "english": s["Description_English"] or "",
                     "kind": "word", "variety": LABEL.get(e["Language_ID"]) or "",
                     "canonical": "yes" if e["Language_ID"] == "rogn" else "no", "source": src, "line": line,
                     "check": ((s["Unsure_About"] or "direction") + "?") if pending else "",
                     "note": "" if s["Comment"] in (SUPPLIED_NOTE, NO_ITALIAN_NOTE) else
                             (s["Comment"] or ("verb" if e["Part_Of_Speech"] == "verb" else "")),
                     "supplied": s["Status"] == "supplied"})
    for x in rows["examples.csv"]:
        if x["Status"] == "rejected":
            continue
        src, line = origin(x["Source"])
        uniq.append({"italian": x["Translated_Text"] or "", "dialect": x["Primary_Text"],
                     "english": x["Translated_Text_English"] or "", "kind": "expression",
                     "variety": LABEL.get(x["Language_ID"]) or "",
                     "canonical": "yes" if x["Language_ID"] == "rogn" else "no", "source": src, "line": line,
                     "check": ((x["Unsure_About"] or "direction") + "?") if x["Status"] == "pending" else "",
                     "note": x["Comment"] or ""})

    variants = defaultdict(list)
    for v in rows["variants.csv"]:
        if v["Status"] == "accepted" and v["Kind"] == "spelling":
            variants[v["Entry_ID"]].append(v["Form"])
    cells = defaultdict(list)
    for p in rows["paradigms.csv"]:
        if p["Status"] != "rejected":
            cells[p["Entry_ID"]].append(p)
    senses_of = defaultdict(list)
    for s in rows["senses.csv"]:
        if s["Status"] != "rejected":
            senses_of[s["Entry_ID"]].append(s)
    tables, eng = {}, {}
    for e in entries.values():
        if e["Part_Of_Speech"] != "verb":
            continue
        ss = sorted(senses_of[e["ID"]], key=lambda s: (bool(s["Comment"]), s["ID"]))
        if not ss:
            continue
        name = ss[0]["Description"]
        for s in ss:
            if s["Description_English"]:
                eng[pages.key(s["Description"])] = re.sub(r"^to ", "", s["Description_English"])
        grid = {t: {} for t in pages.ALL_TENSES}
        forms = defaultdict(lambda: defaultdict(list))
        for p in cells[e["ID"]]:
            person = p["Person"] or "-"
            grid[p["Tense"]][person] = (p["Form"], p["Status"] == "inferred")
            if p["Status"] == "attested":
                forms[p["Tense"]][person].append(p["Form"])
        for t in pages.ALL_TENSES:
            persons = ["-"] if t in ("gerundio", "participio passato") else \
                ["2s", "1p", "2p"] if t.startswith("imperativo") else [s for s, _ in pages.PERSONS]
            for person in persons:
                grid[t].setdefault(person, ("–", False))
            grid[t] = {person: grid[t][person] for person in persons}      # mi, ti, lü … order
        cls = e["Conjugation_Class"] or ""
        full = next((v for k, v in pages.CLASSES.items() if v.startswith(cls + ":")), cls) if cls else ""
        tables[name] = {"dialect": [e["Headword"]] + variants[e["ID"]], "class": full,
                        "basis": "inferred" if e["Status"] == "inferred" else ("attested" if e["Comment"] else ""),
                        "evidence": e["Comment"] or "", "aliases": [s["Description"] for s in ss[1:]],
                        "grid": grid, "forms": forms, "aux": e["Auxiliary"],
                        "sources": list(dict.fromkeys(bib_file.get(re.sub(r"\[.*", "", r), r) for r in e["Source"] or []))}
    return uniq, tables, eng


def _in_word_list(sense):
    """Verb senses appear in the dictionary too, like any other word."""
    return True
