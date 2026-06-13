# Fihrist-As-RDF

**Transforming FIHRIST TEI Manuscript Catalogues into Ontology-Based RDF**

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0--1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![Status](https://img.shields.io/badge/Status-Pilot%20%7C%20Ontology%20Draft-brightgreen)]()
[![Topics](https://img.shields.io/badge/Topics-RDF%20%7C%20TEI%20%7C%20CIDOC--CRM%20%7C%20Persian%20Manuscripts%20%7C%20IIIF-blue)]()

A standalone, production-ready, **FAIR/LOUD-compliant** knowledge graph pipeline that converts the [fihristorg/fihrist-mss](https://github.com/fihristorg/fihrist-mss) TEI P5 `msDesc` files into rich RDF.

Built for seamless integration into the **III FDexir** aggregator and MLDCH platform, with full preservation of relations, Wikidata reconciliation, and clean role modeling via object properties.

## Vision & Goals

- Transform all TEI XML data and their relations into a clean, ontology-based RDF graph.
- Preserve **100% of the original relations** between manuscripts, persons, works, provenance, and physical descriptions.
- Provide a minimal but systematically expandable core ontology (`mdhn:` namespace).
- Enable **exact matching** and merging with existing data (e.g. `PersonsRDFData.ttl`) using `owl:sameAs` and `skos:exactMatch`.
- Model **roles** (author, scribe, former owner, etc.) as first-class object properties.
- Support IIIF deep linking, SPARQL querying, GraphRAG, and community contributions.
- Serve as a reusable, well-documented module that can be merged into larger Persian/Islamicate cultural heritage projects.

## Data Model (Ontology Draft v0.1)

The ontology is the **foundation** of the entire pipeline. It is deliberately minimal and aligned with:

- **CIDOC-CRM** (events, objects, persons, places, time-spans)
- **FRBRoo** (works, expressions, manifestations, items)
- Custom `mdhn:` extensions for Persian/Islamicate specifics and role modeling

### Core Classes

| Class                  | Parent Classes                          | Description |
|------------------------|-----------------------------------------|-----------|
| `mdhn:Manuscript`      | `crm:E22_Manuscript`, `frbroo:F4_Manifestation` | Physical manuscript or codex |
| `mdhn:ManuscriptItem`  | `frbroo:F5_Item`                        | Content unit / msItem inside a manuscript |
| `mdhn:Work`            | `frbroo:F1_Work`                        | Abstract literary work |
| `mdhn:Person`          | `crm:E21_Person`                        | Person (author, scribe, owner, etc.) |
| `mdhn:Place`           | `crm:E53_Place`                         | Geographic or institutional location |
| `mdhn:ProductionEvent` | `crm:E12_Production`                    | Creation / writing event |
| `mdhn:AcquisitionEvent`| `crm:E8_Acquisition`                    | Acquisition / transfer of custody event |
| `mdhn:Role`            | `crm:E55_Type`                          | Role played by a person in relation to a manuscript |

### Key Properties (Relations)

**Manuscript & Content**
- `mdhn:hasContentItem`
- `mdhn:refersToWork`
- `mdhn:hasIdentifier`
- `mdhn:repository`

**Roles (Object Properties)**
- `mdhn:hasAuthor`
- `mdhn:hasRoleAsScribe`
- `mdhn:hasRoleAsFormerOwner`
- `mdhn:hasRoleAsPatron`
- (extendable pattern for any role)

**Physical & Codicological**
- `mdhn:hasSupport`
- `mdhn:hasDimension`
- `mdhn:hasScript`
- `mdhn:hasLayout`

**History & Provenance**
- `mdhn:wasProducedBy`
- `mdhn:wasAcquiredBy`

**Reconciliation & Provenance**
- `mdhn:localFihristID`
- `mdhn:derivedFromTEI` (links back to source TEI)
- `owl:sameAs` / `skos:exactMatch` for merging with Wikidata and `PersonsRDFData.ttl`

**Qualified Relations** (recommended pattern using RDF-star)
```turtle
<< ex:Person_f3466 mdhn:hasRoleAsFormerOwner ex:Add_580 >>
    crm:P4_has_time-span "1869"^^xsd:gYear ;
    prov:wasDerivedFrom ex:TEI_Add_580 .
```

### Full Ontology (Turtle)

```turtle
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix frbroo: <http://www.cidoc-crm.org/frbroo/> .
@prefix mdhn: <http://mdhn.org/ontology/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

mdhn: a owl:Ontology ;
    rdfs:label "Fihrist Manuscript RDF Ontology Alignment"@en ;
    rdfs:comment "Minimal core ontology for Fihrist TEI msDesc → CIDOC-CRM/FRBRoo + mdhn: extensions. Designed for IIIFDexir integration." ;
    owl:versionInfo "0.1 - Pilot Draft (2026-06)" .

mdhn:Manuscript a owl:Class ;
    rdfs:subClassOf crm:E22_Manuscript, frbroo:F4_Manifestation ;
    rdfs:label "Manuscript"@en, "نسخه خطی"@fa .

mdhn:ManuscriptItem a owl:Class ;
    rdfs:subClassOf frbroo:F5_Item ;
    rdfs:label "Manuscript Item / Content Unit"@en .

mdhn:Work a owl:Class ;
    rdfs:subClassOf frbroo:F1_Work ;
    rdfs:label "Literary Work"@en, "اثر ادبی"@fa .

mdhn:Person a owl:Class ;
    rdfs:subClassOf crm:E21_Person ;
    rdfs:label "Person"@en, "شخص"@fa .

mdhn:Place a owl:Class ;
    rdfs:subClassOf crm:E53_Place .

mdhn:ProductionEvent a owl:Class ;
    rdfs:subClassOf crm:E12_Production .

mdhn:AcquisitionEvent a owl:Class ;
    rdfs:subClassOf crm:E8_Acquisition .

mdhn:Role a owl:Class ;
    rdfs:subClassOf crm:E55_Type ;
    rdfs:label "Role in Manuscript Context"@en .

# Properties
mdhn:hasContentItem a owl:ObjectProperty ;
    rdfs:domain mdhn:Manuscript ;
    rdfs:range mdhn:ManuscriptItem .

mdhn:refersToWork a owl:ObjectProperty ;
    rdfs:domain mdhn:ManuscriptItem ;
    rdfs:range mdhn:Work ;
    rdfs:subPropertyOf crm:P67_refers_to .

mdhn:hasAuthor a owl:ObjectProperty ;
    rdfs:domain mdhn:ManuscriptItem ;
    rdfs:range mdhn:Person ;
    rdfs:label "has author (role)"@en .

mdhn:hasRoleAsScribe a owl:ObjectProperty ;
    rdfs:subPropertyOf crm:P14_carried_out_by ;
    rdfs:domain mdhn:Manuscript ;
    rdfs:range mdhn:Person .

mdhn:hasRoleAsFormerOwner a owl:ObjectProperty ;
    rdfs:subPropertyOf crm:P14_carried_out_by ;
    rdfs:range mdhn:Person .

mdhn:wasProducedBy a owl:ObjectProperty ;
    rdfs:domain mdhn:Manuscript ;
    rdfs:range mdhn:ProductionEvent .

mdhn:wasAcquiredBy a owl:ObjectProperty ;
    rdfs:domain mdhn:Manuscript ;
    rdfs:range mdhn:AcquisitionEvent .

mdhn:localFihristID a owl:DatatypeProperty ;
    rdfs:domain mdhn:Person, mdhn:Work ;
    rdfs:range xsd:string .

mdhn:derivedFromTEI a owl:ObjectProperty ;
    rdfs:subPropertyOf prov:wasDerivedFrom .
```
## Mapping Strategy & Real Sample

### Mapping Principles
- **Direct & Faithful**: Every major TEI element maps to one or more ontology classes/properties.
- **Relations First**: `@key`, `@target`, and structural nesting become RDF object properties.
- **Roles**: Dedicated `mdhn:has*` properties for clarity and easy merging.
- **Reconciliation**: Use `mdhn:localFihristID` + `owl:sameAs`.
- **Provenance**: All generated triples link back via `mdhn:derivedFromTEI`.
- **Bilingual**: Persian/Arabic/English labels preserved.

### Real Example: Add_580.xml (Cambridge University Library)

**Source TEI** (excerpts): [Add_580.xml](https://raw.githubusercontent.com/fihristorg/fihrist-mss/master/collections/cambridge%20university/Add_580.xml)

#### 1. Manuscript Identifier & Repository
**TEI**
```xml
<msDesc xml:id="Add_580">
  <msIdentifier>
    <repository>University Library</repository>
    <idno>Add. 580</idno>
  </msIdentifier>
```

**RDF Turtle**

```turtle
ex:Add_580 a mdhn:Manuscript ;
    rdfs:label "Add. 580 - al-Miṣbāḥ fī al-naḥw"@en ;
    mdhn:hasIdentifier "Add. 580" ;
    mdhn:repository ex:Cambridge_University_Library ;
    mdhn:derivedFromTEI <https://github.com/fihristorg/fihrist-mss/.../Add_580.xml> .
```
#### 2. Content, Work & Author (Core Relation)
**TEI**

```xml
<msItem xml:id="Add_580-item1">
  <author key="person_90040229">
    <persName xml:lang="ar">المطرزي، ناصر بن عبد السيد</persName>
  </author>
  <title xml:lang="ar" key="work_2024">المصباح في النحو</title>
  <textLang mainLang="ar">Arabic</textLang>
</msItem>
```

**RDF Turtle**

```turtle
ex:Add_580 mdhn:hasContentItem ex:Item_Add580_1 .

ex:Item_Add580_1 a mdhn:ManuscriptItem ;
    mdhn:refersToWork ex:Work_2024 ;
    mdhn:hasAuthor ex:Person_90040229 .

ex:Person_90040229 a mdhn:Person ;
    rdfs:label "المطرزي، ناصر بن عبد السيد"@ar ;
    mdhn:localFihristID "person_90040229" ;
    owl:sameAs <https://www.wikidata.org/wiki/Q...> .   # after reconciliation

ex:Work_2024 a mdhn:Work ;
    rdfs:label "المصباح في النحو"@ar ;
    mdhn:localFihristID "work_2024" .
```

#### 3. Provenance & Roles
**TEI**

```xml
<acquisition>Bequest of <persName key="person_f3466" role="fmo">R.E. Lofft</persName> in 1869.</acquisition>
```

**RDF Turtle**

```turtle
ex:Add_580 mdhn:hasRoleAsFormerOwner ex:Person_f3466 .

ex:Person_f3466 mdhn:hasRoleAsFormerOwner ex:Add_580 >>
    crm:P4_has_time-span "1869"^^xsd:gYear .
```


#### 4. Physical Description (Codicology)
**TEI**

```xml
<physDesc>
  <objectDesc form="codex">
    <supportDesc material="chart">...</supportDesc>
  </objectDesc>
</physDesc>
```

**RDF Turtle**

```turtle
ex:Add_580 mdhn:hasSupport [ a crm:E57_Material ; crm:P2_has_type "chart" ] ;
    crm:P2_has_type "codex" .
```

## Project Structure

```
Fihrist-As-RDF/
├── ontology/
│   └── fihrist-crm-alignment.ttl     # Core ontology (embedded above)
├── scripts/
│   ├── transform.py                  # TEI → RDF harvester (next step)
│   ├── reconcile.py                  # Wikidata + PersonsRDFData integration
│   └── batch_process.sh
├── data/
│   ├── input/                        # Fihrist collections (git submodule)
│   └── rdf/                          # Generated Turtle files + full graph
├── docs/
│   ├── workflow.md
│   ├── sparql-examples.md
│   ├── integration-iiifdexir.md
│   └── mappings/
├── requirements.txt
├── Dockerfile
└── README.md
```

## Quick Start

```bash
git clone https://github.com/MehranDHN/Fihrist-As-RDF.git
cd Fihrist-As-RDF

# Add Fihrist data as submodule
git submodule add https://github.com/fihristorg/fihrist-mss.git data/input

pip install -r requirements.txt
./scripts/batch_process.sh   # (will be implemented next)
```

## Workflow (Step-by-Step)

We will implement the pipeline together iteratively:

1. **Ontology** (current – completed and embedded)
2. **Harvester** (`transform.py`) – TEI parsing + RDF generation according to the ontology
3. **Reconciliation** (`reconcile.py`) – Match persons/works against Wikidata and your `PersonsRDFData.ttl`
4. **Validation & Quality** – SHACL + SPARQL tests
5. **Aggregation & Publication**
6. **Integration into IIIFDexir** – Graph merge using `owl:sameAs`

## Integration with IIIFDexir & Existing Data

The ontology is specifically designed to make merging easy:

- Use `mdhn:localFihristID` + labels for initial matching.
- Assert `owl:sameAs` or `skos:exactMatch` for confirmed identities.
- Role properties allow clean conflict resolution.
- All triples carry `prov:wasDerivedFrom` for provenance tracking.

## Contributing

We welcome contributions! Please open an issue or pull request.  
Especially welcome: additional role properties, Persian label improvements, and IIIF manifest linking.

## License

This project is released under the [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) license.

## Contact & Related Projects

- **Maintainer**: Mehran DHN (@Mehrandhn)
- Telegram: [t.me/MehranDHNResources](https://t.me/MehranDHNResources)
- Related work: IIIFDexir, MLDCH, Khaleghi_Motlagh_Shahname, ghani-persian-kg, and other repositories under [MehranDHN](https://github.com/MehranDHN)

---

**Status**: Ontology draft ready.  

**Next milestone**: Implementation of the `transform.py` harvester (based exactly on this ontology).

