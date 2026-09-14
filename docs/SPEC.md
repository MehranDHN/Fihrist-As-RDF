# Fihrist-As-RDF specification (rewrite)

Namespace `mdhn:` = `https://MehranDHN.github.io/mdhn-ontology#`  
Instance base = `https://www.fihrist.org.uk/catalog/`

This document is the conversion contract. Implementation lives in `src/fihrist_rdf/`. Method log: `docs/PROGRESS.md`.

## Sources (priority)

1. **TEI** `data/fihrist-mss/collections/**/*.xml` — associations (`@key`, `@role`).
2. **Authority** `persons_base.xml` / `_additions.xml` (and subjects, works), minus `_deletions.xml` — labels and LC/VIAF/ISNI.
3. **HTML** — verification only (local Saxon and/or live catalogue).
4. **Authority comments** — verification only (stale reverse index).

Never join “all subjects in a file” to “all comments in a file”.

## Classes

| Class | Prefix | IRI local name | Source id (data, not IRI) |
|---|---|---|---|
| `mdhn:Manuscript` | `fihrist:` | catalogue key (`manuscript_11855`) | `mdhn:xmlId` / `dct:identifier` |
| `mdhn:Person` / Work / Heading | `fihrist:` | `person_*` `work_*` `subject_*` | `mdhn:xmlId` (original `@key`) |
| `mdhn:ManuscriptItem` | `item:` | `{ms}_{slug(xml:id)}` | `mdhn:xmlId` = TEI `msItem/@xml:id` including hyphens |
| `mdhn:Contribution` | `contrib:` | `{ms}_{person}_{role}_{item?}` | contributor + `mdhn:roleCode` |
| `mdhn:GLAM` | `glam:` | slug of institution name | `rdfs:label` |

IRI slugs: only `A–Z a–z 0–9` and single `_`. Hyphens and other punctuation are **not** copied into IRIs. Double underscores are not used as delimiters; entity type is the prefix.
| Facets | `mdhn:Spatial` `mdhn:Agential` `mdhn:Temporal` `mdhn:Event` `mdhn:Topical` `mdhn:Genre` `mdhn:Technique` `mdhn:Unknown` | typed on heading and/or referent |

## Properties (minimum)

- `mdhn:hasItem` manuscript → item  
- `mdhn:heldBy` manuscript → GLAM (institution)  
- `mdhn:heldAt` manuscript → GLAM (repository, if distinct)  
- `mdhn:inCollection`  
- `mdhn:digitallyPublishedBy` manuscript → GLAM  
- `mdhn:hasContribution` → `mdhn:contributor` + `mdhn:role` + optional `mdhn:onItem`  
- `mdhn:referencesWork` item or manuscript → work  
- `mdhn:hasSubject` manuscript → heading  
- `mdhn:denotes` heading → referent (when typed as RWO)  
- `mdhn:facet` heading → facet class  
- `mdhn:extractedFrom` entity → TEI file URI  
- `skos:exactMatch` / `skos:closeMatch` → LC, VIAF, ISNI, AAT, Wikidata  

## Heading classification

| Layer | Evidence | Facet |
|---|---|---|
| TEI | `placeName`, `settlement`, `region`, `country`, `origPlace` | Spatial |
| TEI | `persName` / personal LCNAF used as subject | Agential |
| LC MADS | Geographic, City, Country, HierarchicalGeographic | Spatial |
| LC MADS | PersonalName, FamilyName, CorporateName | Agential |
| LC MADS | ConferenceName | Event |
| LC MADS | Temporal | Temporal |
| LC MADS | GenreForm | Genre |
| LC MADS | Topic | Topical (may be refined by AAT/WD) |
| LC MADS | ComplexSubject | keep heading; decompose components |
| AAT / Wikidata | facet / P31 | refine; never overwrite TEI+MADS without provenance |

Unmatched type → `mdhn:Unknown` + report row.

## HTML verification

Extract `/catalog/(person_|subject_|work_|manuscript_)` from HTML. Compare to TEI keys and RDF.

Gold files:

- `collections/ancient india and iran trust/AIIT_Pers_1-01.xml`
- `collections/cambridge university/Add_1064.xml`

## Out of scope for conversion (hooks only)

- Inventing Wikidata Q-ids  
- IIIF viewer apps  
- Dashboards as the primary product  
