# Fihrist-As-RDF — method and progress report

This file is the working log of the rewrite. Read it as the *method*, not as marketing.  
Update it whenever a decision, failure, or verification result changes the design.

Date started: 2026-08-28.

---

## 1. Why rewrite (not patch)

Two earlier Python attempts produced Turtle that looked like RDF but was not a knowledge graph:

| Failure | What the old scripts did | Why it is fatal |
|---|---|---|
| Cartesian joins | All `subject_*` IDs in an authority file × all `../collections/...` comments | Invents associations that are not in the catalogue |
| Comments as the join | Regex on `<!-- ../collections/... -->` | Those comments are a *generated reverse index*, not the encoding of the relation |
| Fake LCSH | Every authority id forced to `id.loc.gov/authorities/subjects/` | LC Names (`n…`) are not LCSH (`sh…`) |
| Namespace mix | `github.io/mdhn-ontology#` vs `github.com/.../ontology#` | Broken Linked Data identity |
| No HTML check | TEI (badly) parsed in isolation | The page a scholar sees can list inverse links the script never built |

**Method rule:** throw away `processing/*.py`. Keep Fihrist TEI + authority XML. Rebuild from a written spec.

---

## 2. What “done” means for this rewrite

Complete local corpus → explicit ontology-based RDF, with verification that associations match HTML (and TEI `@key`), and headings typed so Spatial / Agential / Temporal / Event / Topic / Genre / Technique are not one undifferentiated `Subject`.

Wikidata and AAT are **targets in this project** (match existing items). Minting new Wikidata items is a **later project**; this graph must leave stable URIs and an unmatched-heading dump for that work.

---

## 3. Method (how work is sequenced)

```
observe sources → write spec → implement parsers → emit RDF
       ↑                                                    ↓
       └──────── HTML / TEI / comment / RDF diff ←──────────┘
                         ↓
              classify headings (LC MADS → facet; LC→WD)
```

1. **Observe** real TEI, authority XQuery, and Fihrist XSLT (not the README draft ontology).
2. **Specify** classes, URI patterns, source priority, verification checks *before* emitting triples.
3. **Gold records first** (hand-checkable): AIIT Pers 1.01 (`manuscript_11855`) and Cambridge Add. 1064 (`manuscript_8976`).
4. **HTML is a witness**, not a second database. Disagreements are *reports*, then we decide which source is canonical for that fact.
5. **Type headings** only with provenance (TEI element, LC MADS, later AAT/WD). Unknown stays unknown.

---

## 4. Source model (three witnesses)

| Witness | What it actually is | Use in the pipeline |
|---|---|---|
| TEI `collections/**/*.xml` | Canonical *assertions* (`@key`, `@role`, `msIdentifier`, `keywords`) | Harvest RDF from here |
| Authority `persons_base.xml`, `subjects_base.xml`, `works_base.xml` (+ additions, minus deletions) | Identity, labels, VIAF/LC/ISNI. Comments = reverse-index snapshot | Labels + external links; comments only for *diff* |
| HTML | XSLT view of one manuscript; Solr person/subject pages = inverse graph | Integrity check. Local Saxon HTML for CI; live `fihrist.org.uk/catalog/{id}` optional |

Canonical for “this manuscript has this person/work/heading”: **TEI `@key`**.  
Canonical for “what the public page shows”: **HTML**.  
If they differ, RDF still encodes TEI, and the verifier lists the extra/missing keys so we can see where HTML is richer.

### Why HTML can look richer

- Person and subject **index pages** list every manuscript that uses that key. That list is assembled at Solr index time from the whole corpus, not stored as structured XML in one TEI file.
- Authority **comments** are Fihrist’s own XQuery (`update-*-authority-file.xquery`) writing those reverse links back into XML as comments. They can go stale.
- Manuscript HTML **rewrites** `viaf_123` → `person_123`, prints MARC role *labels* (“Former Owner”), and lists `profileDesc` terms in a Subjects block (see `customizations.xsl`).
- `orgName` is **not** linked on the website (Fihrist has no org index), even when TEI has a key — so TEI/RDF can be richer than HTML for GLAMs.

---

## 5. Entity model (locked)

| Entity | Local identity | Notes |
|---|---|---|
| Manuscript | `https://www.fihrist.org.uk/catalog/{TEI/@xml:id}` | Same as HTML `/catalog/manuscript_*` |
| Person | `.../catalog/person_*` (`viaf_*` normalised to `person_*`) | Roles are MARC relators + Fihrist extras (`cataloguer`) |
| GLAM | `mdhn:glam/{slug}` | **Holding** (`institution`/`repository`) ≠ **digital publisher** (`publicationStmt/publisher`). `orgName` with a `person_` key is still a GLAM referent |
| Heading | `.../catalog/subject_*` | SKOS concept (catalogue term). Not the real-world thing |
| Work | `.../catalog/work_*` | Fifth class: required so author-of-work ≠ copy-in-manuscript |

Heading **denotes** a referent. Facets: Spatial, Agential, Temporal, Event, Topical, Genre, Technique, Unknown.

Classification stack: TEI element → LC MADS `rdf:type` → split `ComplexSubject` → AAT facet → Wikidata `P31`. Never invent a type.

---

## 6. Task log

| When | Task | Status | Result |
|---|---|---|---|
| 2026-08-28 | Align goals with user (entities, HTML verify, AAT/WD, heading types) | done | Lock in conversation + this file + `docs/SPEC.md` |
| 2026-08-28 | Inspect TEI, authority comments, XSLT, Solr XQuery | done | Comments are reverse index; HTML Footer only links `profileDesc/term/@key` |
| 2026-08-28 | Discard old `processing/*.py` | done | Replaced by `src/fihrist_rdf/` |
| 2026-08-28 | Ontology + SHACL | done | `ontology/mdhn-fihrist.ttl`, `ontology/shacl.ttl` |
| 2026-08-28 | TEI + authority harvest | done | Gold + Hertford collection CLI |
| 2026-08-28 | HTML generate (Saxon) + parse + diff | done | Local XSLT succeeded; `--live` optional |
| 2026-08-28 | LC MADS classify + Wikidata from LC closeMatch | done | Cached under `data/cache/lc/`; components split |
| 2026-08-28 | Gold run + integrity report | done | See §11 |

---

## 7. How to run (as implemented)

From the repo root, Python 3.8+:

```text
python -m fihrist_rdf gold
python -m fihrist_rdf harvest --collection "ancient india and iran trust"
python -m fihrist_rdf verify --gold
python -m fihrist_rdf classify --gold
```

Outputs:

- `data/rdf/` — Turtle / N-Triples
- `data/html/` — Saxon-generated manuscript pages (when Java+Saxon succeed)
- `data/reports/` — JSON/Markdown integrity reports (this is the study artefact for associations)
- `data/cache/lc/` — Library of Congress JSON (do not re-fetch blindly)

---

## 8. Integrity report (what to study)

For each gold manuscript the verifier writes:

- **TEI keys** — person / work / heading from `@key` in `msDesc` (not `revisionDesc`)
- **Predicted HTML keys** — same rules as `customizations.xsl` (what the XSLT *should* link)
- **Actual HTML keys** — `/catalog/` links parsed from generated or live HTML
- **Authority comments** — reverse index mentioning this file
- **RDF keys** — what we actually emitted

Expected, documented mismatches (not treated as harvest bugs):

- Cataloguers in `revisionDesc` appear in TEI, usually **not** as catalogue links in the manuscript HTML.
- `orgName` keys in RDF, **not** in HTML (XSLT explicitly does not link orgs).
- Person/subject **web pages** list other manuscripts; a single manuscript HTML will not.

Unexpected mismatches (must fix or explain):

- HTML has `/catalog/person_*` that TEI parse missed (nested `@key`, `viaf_`, `author/@key` vs `persName/@key`).
- HTML Subjects list a `subject_*` not in RDF.
- RDF has a manuscript–heading link that neither TEI `@key` nor HTML supports (the old cartesian bug).

---

## 9. Decisions log

| Decision | Choice | Why |
|---|---|---|
| Instance URIs | Fihrist catalogue URLs | HTML and RDF then share identity; Linked Data should not mint a second id for the same record |
| Ontology URIs | `https://MehranDHN.github.io/mdhn-ontology#` | Single namespace; alignments to CRM/FRBR/SKOS, not a mash-up of parent classes as the only model |
| Roles | Reified `mdhn:Contribution` + MARC relator URI | Many roles per person; `authoredBy` alone loses former owners, scribes, cataloguers |
| Subjects | `mdhn:Heading` + `mdhn:denotes` + facet | Catalogue fidelity **and** explicit types |
| Wikidata minting | Out of this repo | Match-only; export unmatched for the later project |
| HTML in CI | Saxon + `previewManuscript.xsl` / `customizations.xsl` | Same transform the catalogue uses; live site is an extra audit |
| Gold before 15k | Two records, then one collection, then full harvest | 15 512 TEI files; wrong join at scale is worse than slow |

---

## 10. Next after gold is green

1. Harvest one collection; read the integrity report (HTML vs TEI).
2. Harvest full corpus to N-Triples.
3. Classify all unique LC headings (cached).
4. AAT match pass (Getty) for headings still Unknown or Topical-that-look-like-technique/genre.
5. Direct Wikidata match for persons via VIAF (in addition to LC `skos:closeMatch`).

If a later experiment disagrees with this file, **change this file**, then the code.

---

## 11a. Compact entity namespaces (2026-08-28, revised)

Hyphens are legal in Turtle local names but are a poor IRI character here (SPARQL `-` token, XML NCName, source punctuation leaking into identity). Double underscores were a fake path (`__item__`) and are not needed if **type is a prefix**.

Rule now:

- IRI local name = `slug_id`: only `A–Za–z0–9` and **single** `_`
- Original TEI `@xml:id` / `@key` stored as `mdhn:xmlId` and `dct:identifier`
- `item:manuscript_11855_AIIT_Pers_1_01_item1_item4` ← source id `AIIT_Pers_1-01-item1-item4`
- `contrib:…` `glam:…` `fihrist:manuscript_11855` (catalogue keys already match HTML)

---

## 11. Gold run (2026-08-28) — what the method proved

Command: `python fihrist.py gold --classify`  
Then: `python fihrist.py harvest --collection "hertford college (university of oxford)"`

### Numbers

- Authority load: 9 745 persons, 2 240 headings, 12 352 works (labels only; comments not used as joins).
- Gold RDF: 249 triples in `data/rdf/gold.ttl`.
- Hertford harvest: 10 TEI files → 766 triples.
- Saxon HTML: **succeeded** for both gold records (`data/html/manuscript_*.html`).

### AIIT Pers 1.01 (`manuscript_11855`) — HTML vs TEI vs comments

| Key | TEI | Saxon HTML | Authority comments | RDF |
|---|---|---|---|---|
| `person_175393012` author | yes | yes | **no** | yes |
| `work_273` | yes | yes | **no** | yes |
| `subject_sh85068446` / `sh85148202` | yes | yes | **no** | yes |
| former owners `f8420`, `f8421`, `79044686` | yes | yes | yes | yes |
| cataloguer `105712` | yes (`recordHist`) | yes | yes | yes |
| `person_153752518` St Augustine’s (`orgName`) | yes | **no** (XSLT does not link orgs) | **no** | yes (typed GLAM) |

**This is the HTML-richness problem, measured:**

- On a *manuscript* page, HTML was **not** richer than TEI for associations. It missed the GLAM `orgName`.
- Authority **comments were poorer** than both: they omitted the author, the work, and both LC headings. Using comments as the join (the old scripts) would have dropped the most important links.
- Where HTML *is* richer is the **person/subject index page** (Solr inverse list). That is why `verify` also compares comments (stale inverse index) and why `--live` exists for `/catalog/person_*` pages.

### Heading typing (the undifferentiated-subject fix)

LC MADS on the three gold headings:

| Heading | LC type | Components (facets) |
|---|---|---|
| Islamic Empire--History | ComplexSubject | Geographic (**spatial**) + History (**topical**) |
| World history--Early works to 1800 | ComplexSubject | Topic + GenreForm (**genre**) |
| Arabic poetry--To 622 | ComplexSubject | Topic + Temporal (**temporal**) |

The catalogue still has one heading triple (`mdhn:hasSubject`). The graph now also has `mdhn:hasComponent` and extra `mdhn:facet` values. That is ontology-based explicitness without throwing away the pre-coordinated LC string.

Wikidata `closeMatch` was empty on these three LC records (LC did not attach WD here). Next: VIAF→Wikidata for persons; Getty AAT for topical leftovers.

### Unit tests

`python tests/test_gold.py` — 2 passed (keys, roles, GLAMs, works, subjects on both gold files).

## Usage

Run everything from the **repo root**. The usual entry point is `python fihrist.py` (same as `python -m fihrist_rdf` if `src` is on `PYTHONPATH`).

### Harvest

```text
python fihrist.py harvest
python fihrist.py harvest --collection "FOLDER NAME"
python fihrist.py harvest --collection "FOLDER NAME" --limit N
```

| Flag | Meaning |
|---|---|
| *(none)* | All TEI under `data/fihrist-mss/collections/` |
| `--collection` | Exact folder name under `collections/` (spaces and parentheses included) |
| `--limit N` | Stop after N XML files |

Output:

- `data/rdf/harvest.ttl` + `.nt` — full corpus
- `data/rdf/harvest_<collection>.ttl` + `.nt` — one collection (spaces → `_`)
- `data/rdf/harvest_<collection>_nN.ttl` — if `--limit` is set
- parse errors (if any) → `data/reports/harvest_….parse_errors.json`

Examples that already match folders in this repo:

```text
python fihrist.py harvest --collection "ancient india and iran trust"
python fihrist.py harvest --collection "hertford college (university of oxford)"
python fihrist.py harvest --collection "cambridge university"
python fihrist.py harvest --collection "british library"
python fihrist.py harvest --collection "cambridge university" --limit 50
```

`--collection` is a **directory name**, not a manuscript id. It is joined as `collections/<name>` and then walks `*.xml` (skips `*.bak`).

## Other commands (same CLI)

```text
python fihrist.py gold
python fihrist.py gold --classify
python fihrist.py gold --live
python fihrist.py gold --skip-html

python fihrist.py verify --gold
python fihrist.py verify --file path\to\file.xml
python fihrist.py verify --collection "cambridge university" --limit 10
python fihrist.py verify --gold --live

python fihrist.py classify
python fihrist.py classify --graph data/rdf/harvest_cambridge_university.ttl
python fihrist.py classify --graph data/rdf/harvest_cambridge_university.ttl --max 20
```

| Command | What it does |
|---|---|
| `gold` | Harvest + integrity-check the two gold MSS (`manuscript_11855`, `manuscript_8976`) → `data/rdf/gold.ttl` |
| `verify` | TEI / HTML / RDF report for `--gold`, `--file`, or `--collection` → `data/reports/` |
| `classify` | Type headings from LC MADS on an existing Turtle graph (default `gold.ttl`) |

`gold --classify` is harvest+verify+LC typing in one go. `harvest` itself does **not** classify headings; run `classify --graph …` on the harvest Turtle afterwards if you want that.


### Visualization
Visualization is **not** a `fihrist.py` subcommand. It lives in `visualizations/` and needs a harvest Turtle first. The “report” is RDF vs HTML markdown plus a Graphviz neighbourhood.

## 1. Sample neighbourhood (capped)

```text
python visualizations/make_person_dot.py --ttl data/rdf/harvest_cambridge_university.ttl --person person_175393012 --out visualizations/person_175393012.dot
python visualizations/make_person_dot.py --ttl data/rdf/harvest_cambridge_university.ttl --person person_100206721 --out visualizations/cambridge_person_100206721.dot --max-ms 8
```

| Flag | Meaning |
|---|---|
| `--ttl` | Harvest Turtle (required) |
| `--person` | Catalogue key, e.g. `person_100206721` (default `person_175393012`) |
| `--out` | DOT path (required) |
| `--max-ms` | Max manuscripts to draw (default 8) |

Then render:

```text
dot -Tsvg visualizations/person_175393012.dot -o visualizations/person_175393012.svg
dot -Tpng visualizations/person_175393012.dot -o visualizations/person_175393012.png
```

This is the small graph: person → sample of manuscripts → works/subjects.

## 2. Complete neighbourhood + RDF vs HTML report

This is the one that writes the visualization **report** (the file next to the integrity reports you have open):

```text
python visualizations/make_complete_person_dot.py --ttl data/rdf/harvest_cambridge_university.ttl --person person_100206721 --out visualizations/cambridge_person_100206721.dot
```

| Flag | Default |
|---|---|
| `--ttl` | `data/rdf/harvest_cambridge_university.ttl` |
| `--person` | `person_100206721` |
| `--out` | `visualizations/cambridge_person_100206721.dot` |

Outputs:

| File | What it is |
|---|---|
| `visualizations/<person>.dot` | Full neighbourhood (no sampling) |
| `data/reports/<person>.rdf_vs_html.md` | RDF vs live Fihrist HTML (manuscripts / works / subjects) |
| `data/reports/<person>.rdf_vs_html.json` | Same comparison as JSON |

That markdown is the visualization report: counts of keys in RDF, on the HTML person page, both, only-RDF, only-HTML. Live fetch can hit a bot-check; then the script still writes DOT, and the report notes the HTML error.

Example already in the repo: `data/reports/person_100206721.rdf_vs_html.md`.

## 3. High-DPI PNG (optional, Graphviz + Pillow)

Hard-wired to Saʿdī’s Cambridge DOT:

```text
python visualizations/_render_highdpi.py
```

Needs `dot` on PATH. Writes tiled 300 dpi PNGs under `visualizations/`.

## Typical sequence

```text
python fihrist.py harvest --collection "cambridge university"
python visualizations/make_complete_person_dot.py --ttl data/rdf/harvest_cambridge_university.ttl --person person_100206721 --out visualizations/cambridge_person_100206721.dot
dot -Tsvg visualizations/cambridge_person_100206721.dot -o visualizations/cambridge_person_100206721.svg
```

`--person` must appear as a contributor in that Turtle. If you harvested another collection, point `--ttl` at that harvest file.

Integrity reports (`verify --gold` → `data/reports/manuscript_*.integrity.md`) are a different artefact: TEI vs HTML vs RDF for one **manuscript**. Visualization reports are person-centred graphs plus RDF vs HTML key diffs.

## Collections based on Fihrist Advanced Search
- Oxford University 9,059
- British Library 6,260
- Cambridge University 6,074
- The University of Manchester 2,633
- School of Oriental and African Studies 2,292
- Royal Asiatic Society of Great Britain and Ireland 1,145
- University of Birmingham 784
- King's College Cambridge 559
- Eton College 500
- Wellcome Trust 454
- Wadham College (University of Oxford) 390
- Trinity College Cambridge 270
- University of St Andrews 113
- Arabic Commentaries on the Hippocratic Aphorisms project 91
- The Fitzwilliam Museum 71
- Jesus College (Cambridge) 45
- Wigan Council Archives: Wigan & Leigh 41
- Hertford College (University of Oxford) 23
- Queens' College (Cambridge) 23
- The Blackburn Museum & Art Gallery 17
- Keble College (University of Oxford) 13
- Trinity Hall (Cambridge) 13
- Trinity College (University of Oxford) 8
- Trinity College Dublin, the University of Dublin 6
- Ancient India and Iran Trust 2
- New College (University of Oxford) 2
- St Antony's College (Oxford) 2 

