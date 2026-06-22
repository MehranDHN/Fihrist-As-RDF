# Fihrist-As-RDF

# Fihrist-As-RDF: Linked Open Data for the Fihrist Union Catalogue of Islamicate Manuscripts
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0--1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![Status](https://img.shields.io/badge/Status-Pilot%20%7C%20Ontology%20Draft-brightgreen)]()
[![Topics](https://img.shields.io/badge/Topics-RDF%20%7C%20TEI%20%7C%20CIDOC--CRM%20%7C%20Persian%20Manuscripts%20%7C%20IIIF-blue)]()

**Transforming distributed TEI XML from [fihristorg/fihrist-mss](https://github.com/fihristorg/fihrist-mss) into a richly interconnected Knowledge Graph.**

This project delivers a **minimal yet expandable RDF/OWL ontology**, harvesting pipelines, and reconciled datasets with strong bindings to LC Subjects, AAT, VIAF, and Wikidata.

**Key Focus Areas**:
- **Subjects**: Start with LCSH (already in TEI), map to AAT + Wikidata for robust cultural heritage interoperability.
- **Persons**: Extend existing VIAF mappings with Wikidata.
- **Visualizations**: Mind maps, relationship graphs, and dashboards for intuitive exploration.

**Vision**: A FAIR, queryable hub linking manuscripts, persons, works, and subjects — powering your MLDCH aggregator, IIIFDexir viewers, Shahnameh modeling, and the National Digital Collection.

## Project Structure (Visualization-First)

```
Fihrist-As-RDF/
├── README.md
├── LICENSE
├── ontology/                  # Core + alignments
├── data/
│   ├── samples/               # Pilot RDF + visualizations
│   ├── authorities/           # Reconciled Persons, Subjects, Works
│   └── full-kg/               # Aggregated, versioned dumps
├── processing/                # Scripts & notebooks
├── visualizations/            # High-res diagrams, Mermaid, Graphviz exports
│   ├── mindmaps/
│   ├── relationship-graphs/
│   └── dashboards/            # Example SPARQL → visualization
├── docs/                      # Reports & examples
└── CONTRIBUTING.md
```

**Interactive Overview** (Mermaid in repo):
```mermaid
graph TD
    A[Fihrist TEI Collections] --> B[mdhn:Manuscript]
    B --> C[mdhn:ManuscriptItem]
    C --> D[mdhn:Person <br>VIAF + Wikidata]
    C --> E[mdhn:Work]
    C --> F[mdhn:Subject <br>LCSH → AAT → Wikidata]
    F -.-> G[AAT Getty]
    D -.-> H[Wikidata]
    style F fill:#e1f5fe
```

## Minimal Ontology (First Draft)

**Namespace**: `mdhn:` (`https://MehranDHN.github.io/mdhn-ontology#`)

**Core Classes** (expandable per systematic plan):
- `mdhn:Manuscript` ⊑ `crm:E22_Manifestation`
- `mdhn:ManuscriptItem` ⊑ `frbr:Expression`
- `mdhn:Person` ⊑ `crm:E21_Person`
- `mdhn:Work` ⊑ `frbr:Work`
- `mdhn:Subject` ⊑ `skos:Concept`

### `ontology/mdhn-fihrist.ttl` (Minimal Ontology with Subjects/Person Focus)
```turtle
@prefix mdhn: <https://MehranDHN.github.io/mdhn-ontology#> .
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix frbr: <http://purl.org/vocab/frbr/core#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix viaf: <https://viaf.org/viaf/> .
@prefix wd: <http://www.wikidata.org/entity/> .
@prefix aat: <http://vocab.getty.edu/aat/> .
@prefix lcsh: <http://id.loc.gov/authorities/subjects/> .

# Ontology Metadata
mdhn: a owl:Ontology ;
    rdfs:label "mdhn: Fihrist-As-RDF Ontology" ;
    dct:description "Minimal expandable ontology for Fihrist TEI manuscripts with strong reconciliation." .

# Classes
mdhn:Manuscript a owl:Class ;
    rdfs:subClassOf crm:E22_Manifestation ;
    rdfs:label "Manuscript" .

mdhn:ManuscriptItem a owl:Class ;
    rdfs:subClassOf frbr:Expression ;
    rdfs:label "Manuscript Content Item" .

mdhn:Person a owl:Class ;
    rdfs:subClassOf crm:E21_Person ;
    rdfs:label "Person (with roles)" .

mdhn:Work a owl:Class ;
    rdfs:subClassOf frbr:Work ;
    rdfs:label "Literary/Artistic Work" .

mdhn:Subject a owl:Class ;
    rdfs:subClassOf skos:Concept ;
    rdfs:label "Subject Concept (LCSH + mappings)" .

# Properties
mdhn:hasManuscriptItem a owl:ObjectProperty ;
    rdfs:domain mdhn:Manuscript ;
    rdfs:range mdhn:ManuscriptItem .

mdhn:authoredBy a owl:ObjectProperty ;
    rdfs:domain mdhn:ManuscriptItem ;
    rdfs:range mdhn:Person .

mdhn:referencesWork a owl:ObjectProperty ;
    rdfs:domain mdhn:ManuscriptItem ;
    rdfs:range mdhn:Work .

mdhn:hasSubject a owl:ObjectProperty ;
    rdfs:domain mdhn:ManuscriptItem ;
    rdfs:range mdhn:Subject .

mdhn:reconciledTo a owl:ObjectProperty ;
    rdfs:label "Reconciled to external authority" .

# Example Instances (expand via pipeline)
lcsh:sh85055328 a mdhn:Subject ;
    skos:prefLabel "Glossaries, vocabularies, etc."@en ;
    mdhn:reconciledTo aat:300000000 ;  # Placeholder - refine with exact AAT
    mdhn:reconciledTo wd:Q12345 ;     # Placeholder Wikidata
    skos:exactMatch lcsh:sh85055328 .

# Person example (extend VIAF with Wikidata)
<mdhn:person_f3010> a mdhn:Person ;
    rdfs:label "Mīr Sayyid Ḥusayn" ;
    mdhn:reconciledTo viaf:123456 ;   # Existing style
    mdhn:reconciledTo wd:Q... .       # Wikidata extension
```

**Key Properties**:
- Linking: `mdhn:hasManuscriptItem`, `mdhn:authoredBy` (with roles), `mdhn:referencesWork`, `mdhn:hasSubject`
- Reconciliation: `mdhn:reconciledTo` (object property to external URIs)
- Provenance & IIIF-ready.

**Subjects Module** (Priority):
- Ingest LCSH from TEI `<keywords scheme="#LCSH">` and authority files.
- Mappings: LCSH → AAT (material/cultural terms) → Wikidata (stronger global bindings).
- Example Turtle (in `ontology/mdhn-fihrist.ttl`):

```turtle
mdhn:Subject a owl:Class ;
    rdfs:subClassOf skos:Concept .

<subject_sh85055328> a mdhn:Subject ;
    skos:prefLabel "Glossaries, vocabularies, etc."@en ;
    mdhn:reconciledTo <http://vocab.getty.edu/aat/300000000> ;  # Example AAT
    mdhn:reconciledTo <http://www.wikidata.org/entity/Q...> ;
    skos:exactMatch <http://id.loc.gov/authorities/subjects/sh85055328> .
```

**Persons Module** (Extension):
- Build on existing VIAF in `persons.xml`.
- Add Wikidata reconciliation (e.g., via your pipelines or tools like OpenRefine/KG reconciliation).
- Same pattern for strong bindings.

Full details + diagrams: [ontology/documentation.md](ontology/documentation.md)

## Reconciliation Strategy

- **Persons**: VIAF (existing) + Wikidata (new) — use labels, dates, roles for disambiguation.
- **Subjects**: LCSH base → AAT (for art/archaeology/iconography) → Wikidata (broader links, multilingual).
- Tools: Python (rdflib + SPARQL), OpenRefine, Wikidata API.
- Goal: High-confidence `skos:exactMatch` / `mdhn:reconciledTo` triples.

## Visualizations & Exploration

- **Mind Maps**: Hierarchical views (Manuscript → Items → Entities).
- **Relationship Graphs**: Network of persons-subjects-manuscripts.
- **Dashboards**: SPARQL → Mermaid / GraphDB visualizations.
- Examples in `/visualizations/` (high-resolution PNG/SVG + source).

## Pipeline & Data

(See `processing/` for scripts.)

1. Harvest TEI (ZIP → local folders).
2. Extract & reconcile (LC Subjects first, then Persons).
3. Generate RDF + visualizations.
4. Validate (SHACL) & enrich.

**Samples available** in `data/samples/`.

## Roadmap

- [x] Minimal ontology + Subjects/Person focus
- [ ] Full harvest & LCSH→AAT/Wikidata mappings
- [ ] Advanced visualizations & IIIF integration
- [ ] Community expansion

## Contributing

Prioritize ontology refinements, reconciliation mappings, or visualization improvements. See [CONTRIBUTING.md](CONTRIBUTING.md).

**Contact**: Mehran DHN (@Mehrandhn, Telegram channel)

## Ethics & Acknowledgments

Open, provenance-preserving, culturally sensitive. Built on Fihrist TEI community data. Aligns with FAIR/LOUD and your DCH portfolio.

---

**Next Actions Ready**:
- Full `ontology/mdhn-fihrist.ttl` file (minimal + Subjects/Person patterns).
- Sample LCSH extraction + mapping script.
- High-res Mermaid/Graphviz mind map for Subjects reconciliation.
- `ontology/documentation.md` expansion.
- Or proceed to processing script for LCSH pilot.

This keeps the visualization emphasis strong while prioritizing Subjects (LC → AAT/Wikidata) and extending Persons. Feedback on this draft? What to generate next (Turtle file, script, diagram)?

