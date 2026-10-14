# Lexicon of the dialect of Rögn (Arogno)

This folder is the **CLDF dataset** for the dialect material in this repository: every dialect word, its
Italian and English meanings, example sentences, verb conjugations, the sources each one comes from, and
the decisions made about variants and typos. It is plain text (CSV and JSON), so every change can be
reviewed with `git diff`.

**Do not edit these files by hand.** Following the [cldfbench](https://github.com/cldf/cldfbench)
workflow, the dataset is regenerated on every build from the source documents in [`../raw/`](https://github.com/michaelmaguire/languages-dialett-raw)
and the curation in [`../etc/`](../etc/). The documents are read only by the first two steps, whose output
is saved in `../pipeline/data/`, so the dataset can also be rebuilt (with every decision applied) when
`../raw/` is not available. To change something, change it there (a typo or a rejected
entry goes in [`../etc/decisions.csv`](../etc/decisions.csv)) and run `../pipeline/build_all.sh`.

It follows the **[CLDF](https://cldf.clld.org/) (Cross-Linguistic Data Formats) specification, version
1.x, Dictionary module**, at the level the specification calls *extended conformance*: a metadata file
describes every table and column, and the dataset is validated against the specification on every build.

## The CLDF specification

| Document | Link |
|---|---|
| CLDF home page | <https://cldf.clld.org/> |
| The specification | <https://github.com/cldf/cldf/blob/master/README.md> |
| Dictionary module (what a CLDF dictionary must contain) | <https://github.com/cldf/cldf/tree/master/modules/Dictionary> |
| Components used here: entries, senses, examples, languages | <https://github.com/cldf/cldf/tree/master/components> |
| The CLDF ontology (meaning of every `propertyUrl`) | <https://cldf.clld.org/v1.0/terms.html> |
| CSV on the Web (CSVW), which the metadata file uses | <https://www.w3.org/TR/tabular-metadata/> |
| pycldf, the reference software used to validate and query | <https://github.com/cldf/pycldf> |
| cldfbench, the tool used to build this dataset | <https://github.com/cldf/cldfbench> |
| Glottolog, for the language codes | <https://glottolog.org/> |

## What is in it

| File | CLDF role | One row per |
|---|---|---|
| [`Dictionary-metadata.json`](Dictionary-metadata.json) | Metadata (declares `dc:conformsTo` the Dictionary module) | |
| [`entries.csv`](entries.csv) | EntryTable (required) | dialect headword, in one variety |
| [`senses.csv`](senses.csv) | SenseTable (required) | meaning of an entry: `Description` is the Italian, `Description_English` the English |
| [`examples.csv`](examples.csv) | ExampleTable | sentence or saying: `Primary_Text` is the dialect, `Translated_Text` the Italian, `Translated_Text_English` the English |
| [`languages.csv`](languages.csv) | LanguageTable | variety (Rögn, Basso Ceresio, Mendrisiotto…), plus Italian and English as meta-languages |
| [`variants.csv`](variants.csv) | additional table | other spelling of an entry, including known typos and OCR errors |
| [`paradigms.csv`](paradigms.csv) | additional table | cell of a verb's conjugation chart |
| [`sources.bib`](sources.bib) | Sources (BibTeX) | lesson, handout, published text, or the owner's own notes |

The specification allows additional columns and tables as long as the metadata describes them. The
additions here are the English columns, `Status`, `Variant_Of`, `Conjugation_Class`, `Auxiliary`, and
the `variants.csv` and `paradigms.csv` tables. Verb paradigms have no CLDF component of their own.

## How the data is recorded

- **Varieties.** Each Ticinese variety is a row in `languages.csv`, all with Glottocode `lomb1257`
  (Lombard) and ISO 639-3 `lmo`; Glottolog has no finer codes for them. An entry belongs to exactly one
  variety. A regional form of a Rögn word is its own entry, linked by `Variant_Of`.
- **Sources.** Every row cites where it was found, in the `Source` column, as `key[l.N]`: the BibTeX key
  of the document and the line in its extracted text (`pipeline/cache/lesson_text/`).
- **Decisions.** Every table has a `Status` column whose allowed values are fixed in the metadata, so the
  validator rejects anything else (`pending` rows are the ones marked ⚠ on the pages):

  | Table | Status values |
  |---|---|
  | entries | `accepted`, `pending` (needs review), `inferred` (infinitive worked out, not stated), `rejected` |
  | senses | `attested`, `supplied` (Italian added because the lesson gives only the dialect), `pending`, `rejected` |
  | examples | `accepted`, `pending`, `rejected` |
  | variants | `accepted`, `pending`, `typo`, `rejected` |
  | paradigms | `attested` (found in a document), `inferred` (predicted from the patterns), `rejected` |

  The reason goes in `Comment`. Nothing is deleted: a typo or a wrong entry is marked `rejected` or
  `typo`, keeps its sources, and stops appearing in the pages. For example, the owner's spreadsheet has
  `semper` for *sempre*; [`../etc/decisions.csv`](../etc/decisions.csv) records it as a typo, so the
  dataset has the entry `sempru` and the variant `sempru-semper` with kind and status `typo`.
- **IDs** use only letters, digits and hyphens, as CLDF requires, and are made from the headword
  (`sempru`), with the variety appended outside Rögn (`semper-ticinese`) and a number for homographs
  (the verb `vert` and the colour `vert` are separate entries). As the dataset is regenerated, an ID stays
  the same as long as the data it comes from does.

## Working with it

```sh
cd pipeline
.venv/bin/cldf validate ../cldf/Dictionary-metadata.json                       # check conformance
.venv/bin/cldf createdb ../cldf/Dictionary-metadata.json cache/cldf.sqlite  # query it with SQL
```

`build_all.sh` builds the dataset with cldfbench, validates it, and stops if it is not valid, before any
page is written from it. The SQLite file is a disposable copy and not kept in git. cldfbench also records
provenance in the metadata and lists the Python packages used in `requirements.txt`.

---

The section below is generated from the metadata by `cldf markdown` on every build.

# Lexicon of the dialect of Rögn (Arogno), Ticino

**CLDF Metadata**: [Dictionary-metadata.json](./Dictionary-metadata.json)

**Sources**: [sources.bib](./sources.bib)

Dialect entries, senses (Italian with English), examples and verb paradigms from the course Cors da dialett da Rögn and related texts. See README.md.

property | value
 --- | ---
[dc:bibliographicCitation](http://purl.org/dc/terms/bibliographicCitation) | Maguire, Michael. Lexicon of the dialect of Rögn (Arogno), Ticino. Based on the course Cors da dialett da Rögn taught by Guido Casellini. https://github.com/michaelmaguire/languages-dialett
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF Dictionary](http://cldf.clld.org/v1.0/terms.rdf#Dictionary)
[dc:contributor](http://purl.org/dc/terms/contributor) | Guido Casellini (course material) and the other authors listed in ATTRIBUTIONS.md
[dc:creator](http://purl.org/dc/terms/creator) | Michael Maguire
[dc:identifier](http://purl.org/dc/terms/identifier) | https://github.com/michaelmaguire/languages-dialett
[dc:license](http://purl.org/dc/terms/license) | https://creativecommons.org/licenses/by/4.0/
[dcat:accessURL](http://www.w3.org/ns/dcat#accessURL) | git@github.com:michaelmaguire/languages
[prov:wasDerivedFrom](http://www.w3.org/ns/prov#wasDerivedFrom) | <ol><li><a href="git@github.com:michaelmaguire/languages/tree/c8548d2">git@github.com:michaelmaguire/languages  c8548d2</a></li></ol>
[prov:wasGeneratedBy](http://www.w3.org/ns/prov#wasGeneratedBy) | <ol><li><strong>python</strong>: 3.12.3</li><li><strong>python-packages</strong>: <a href="./requirements.txt">requirements.txt</a></li></ol>
[rdf:ID](http://www.w3.org/1999/02/22-rdf-syntax-ns#ID) | rogn
[rdf:type](http://www.w3.org/1999/02/22-rdf-syntax-ns#type) | http://www.w3.org/ns/dcat#Distribution


## <a name="table-entriescsv"></a>Table [entries.csv](./entries.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF EntryTable](http://cldf.clld.org/v1.0/terms.rdf#EntryTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1082


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[Headword](http://cldf.clld.org/v1.0/terms.rdf#headword) | `string` | 
[Part_Of_Speech](http://cldf.clld.org/v1.0/terms.rdf#partOfSpeech) | `string` | 
`Variant_Of` | `string` | ID of the main entry when this entry is a regional variant of it<br>References [entries.csv::ID](#table-entriescsv)
`Conjugation_Class` | `string` | 
`Auxiliary` | `string`<br>Valid choices:<br> `ves` `vegh` | 
`Status` | `string`<br>Valid choices:<br> `accepted` `pending` `inferred` `rejected` | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-sensescsv"></a>Table [senses.csv](./senses.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF SenseTable](http://cldf.clld.org/v1.0/terms.rdf#SenseTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1103


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Entry_ID](http://cldf.clld.org/v1.0/terms.rdf#entryReference) | `string` | References [entries.csv::ID](#table-entriescsv)
`Description_English` | `string` | English translation of the Description, which is in Italian
`Status` | `string`<br>Valid choices:<br> `attested` `supplied` `pending` `rejected` | 
`Unsure_About` | `string`<br>Valid choices:<br> `direction` `split` `pairing` `meaning` | What the extraction was unsure about when it marked the row pending
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-languagescsv"></a>Table [languages.csv](./languages.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF LanguageTable](http://cldf.clld.org/v1.0/terms.rdf#LanguageTable)
[dc:extent](http://purl.org/dc/terms/extent) | 9


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Macroarea](http://cldf.clld.org/v1.0/terms.rdf#macroarea) | `string` | 
[Latitude](http://cldf.clld.org/v1.0/terms.rdf#latitude) | `decimal`<br>&ge; -90<br>&le; 90 | 
[Longitude](http://cldf.clld.org/v1.0/terms.rdf#longitude) | `decimal`<br>&ge; -180<br>&le; 180 | 
[Glottocode](http://cldf.clld.org/v1.0/terms.rdf#glottocode) | `string`<br>Regex: `[a-z0-9]{4}[1-9][0-9]{3}` | 
[ISO639P3code](http://cldf.clld.org/v1.0/terms.rdf#iso639P3code) | `string`<br>Regex: `[a-z]{3}` | 
`Description` | `string` | 

## <a name="table-examplescsv"></a>Table [examples.csv](./examples.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ExampleTable](http://cldf.clld.org/v1.0/terms.rdf#ExampleTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1314


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[Primary_Text](http://cldf.clld.org/v1.0/terms.rdf#primaryText) | `string` | The example text in the source language.
[Analyzed_Word](http://cldf.clld.org/v1.0/terms.rdf#analyzedWord) | list of `string` (separated by `	`) | The sequence of words of the primary text to be aligned with glosses
[Gloss](http://cldf.clld.org/v1.0/terms.rdf#gloss) | list of `string` (separated by `	`) | The sequence of glosses aligned with the words of the primary text
[Translated_Text](http://cldf.clld.org/v1.0/terms.rdf#translatedText) | `string` | The translation of the example text in a meta language
[Meta_Language_ID](http://cldf.clld.org/v1.0/terms.rdf#metaLanguageReference) | `string` | References the language of the translated text<br>References [languages.csv::ID](#table-languagescsv)
[LGR_Conformance](http://cldf.clld.org/v1.0/terms.rdf#lgrConformance) | `string`<br>Valid choices:<br> `WORD_ALIGNED` `MORPHEME_ALIGNED` | The level of conformance of the example with the Leipzig Glossing Rules
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
`Translated_Text_English` | `string` | English translation, added; Translated_Text is the Italian
`Status` | `string`<br>Valid choices:<br> `accepted` `pending` `rejected` | 
`Unsure_About` | `string`<br>Valid choices:<br> `direction` `split` `pairing` `meaning` | What the extraction was unsure about when it marked the row pending
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-variantscsv"></a>Table [variants.csv](./variants.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 36


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
`ID` | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
`Entry_ID` | `string` | References [entries.csv::ID](#table-entriescsv)
`Form` | `string` | 
`Kind` | `string`<br>Regex: `spelling\|typo\|ocr-error` | 
`Status` | `string`<br>Valid choices:<br> `accepted` `pending` `typo` `rejected` | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)

## <a name="table-paradigmscsv"></a>Table [paradigms.csv](./paradigms.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 4816


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
`ID` | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
`Entry_ID` | `string` | References [entries.csv::ID](#table-entriescsv)
`Tense` | `string` | 
`Person` | `string`<br>Valid choices:<br> `1s` `2s` `3s` `1p` `2p` `3p` | 
`Form` | `string` | 
`Status` | `string`<br>Valid choices:<br> `attested` `inferred` `rejected` | 
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
