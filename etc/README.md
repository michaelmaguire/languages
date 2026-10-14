# Curation: `etc/`

In [cldfbench](https://github.com/cldf/cldfbench) terms this is the configuration directory: the data
that guides the conversion of the raw sources in [`../raw/`](https://github.com/michaelmaguire/languages-dialett-raw) into the CLDF dataset in
[`../cldf/`](../cldf/). **Every decision about the data lives here.** The dataset and all the pages are
regenerated from `raw/` + `etc/` on every build (`../pipeline/build_all.sh`), so this is the only place
to make a correction that lasts. Decisions here can be applied even without `raw/`: the build then uses
the extraction saved in `../pipeline/data/` (see the pipeline README).

| File | One row per | What it decides |
|---|---|---|
| [`decisions.csv`](decisions.csv) | decision about a dictionary entry or an expression | Typos, rejections, corrections, acceptance of uncertain (⚠) rows, variants. Format below. |
| [`pair_corrections.csv`](pair_corrections.csv) | extracted pair | Delete, replace or add a pair found by the parser: `source,line,action,italian,dialect,english,note`, where `source` and `line` come from `../pipeline/data/extracted_pairs.csv` and `action` is `delete`, `replace` or `add`. |
| [`lesson_sources.csv`](lesson_sources.csv) | document in `raw/` | Its dialect variety, whether it is canonical Rögn course material, how to parse it (`layout`: `auto`, `skip`, `text_only`, `gerund`, `imperative`, `bullets`) and whether to include it. New documents are added automatically with `?` to fill in. |
| [`english_translations.csv`](english_translations.csv) | Italian text | Its English. Every translation is made once and kept here. |
| [`verb_details.csv`](verb_details.csv) | verb needing help | Dialect infinitive (attested or inferred, with the evidence), merges of duplicate verbs, class, stems, participle, auxiliary, tenses to ignore. |
| [`verb_forms_from_texts.csv`](verb_forms_from_texts.csv) | verb form | A form found in running text (`basis` = `attested`), or supplied by hand (`inferred`). |
| [`dialect_lists_italian_supplied.csv`](dialect_lists_italian_supplied.csv) | word | Words a lesson lists in dialect only (colours, numbers, the house, the calendar), with the Italian and English supplied. Shown with † on the Italian. |

## `decisions.csv`

```
Decision,Language_ID,Form,Sense,Target_Form,Target_Language_ID,Italian,English,Reason,Date
typo,ticinese,semper,,sempru,rogn,,,"Typo in the owner's spreadsheet; the course writes sempru …",2026-10-14
correct,ticinese,böcc,,,,buco,hole,"Claude inferred: Italian misspelt ""bucco"" in the spreadsheet",2026-10-14
```

| Column | Meaning |
|---|---|
| `Decision` | `typo`, `reject`, `accept` or `variant` |
| `Language_ID` | the variety of the entry the decision is about, as in `../cldf/languages.csv` (`rogn`, `basso-ceresio`, `ticinese` …) |
| `Form` | the entry's headword, or for an expression its dialect text, as it appears in the data |
| `Sense` | optional: the Italian of one sense of the entry, to limit `reject`, `accept` or `correct` to that sense |
| `Target_Form` | for `typo` and `variant`: the correct or main headword; for `correct`: the corrected dialect |
| `Target_Language_ID` | for `typo` and `variant`: the variety of the target, if it differs |
| `Italian`, `English` | for `correct`: the corrected Italian and English (blank = unchanged) |
| `Reason`, `Date` | recorded in the `Comment` of the rows affected. A reason that starts **"Claude inferred:"** comes from Claude's review of the whole dataset (2026-10-14), not from the owner: check it, and delete or change the row if it is wrong |

| Decision | Effect |
|---|---|
| `typo` | The entry is folded into `Target_Form`; the mistaken form is kept in `variants.csv` as a `typo` so it is recognised but never shown. |
| `reject` | The entry is kept with status `rejected` and the reason, and left off the pages. |
| `accept` | A `pending` (⚠) entry becomes accepted and its pending senses attested. |
| `variant` | Same variety: the form becomes an accepted spelling of the target entry. Another variety: the entry is linked to the target with `Variant_Of`, or, if the target does not exist yet, folded into a new target entry (how `avech pagüra` became the Rögn `vegh pagüra`). |
| `correct` | Replaces the dialect, Italian and/or English of the entry's senses (or the one named in `Sense`), or of an expression, and marks it accepted. |

`reject`, `accept` and `correct` also work on expressions (`examples.csv`): `Form` is then the dialect
text. A decision that matches nothing is reported as a warning when the dataset is built.
