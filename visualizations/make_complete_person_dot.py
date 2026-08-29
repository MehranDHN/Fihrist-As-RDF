# -*- coding: utf-8 -*-
"""Emit every RDF fact in a person's neighbourhood as Graphviz DOT (no sampling, no truncated labels)."""

from __future__ import print_function

import argparse
import hashlib
import json
import re
import ssl
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS

from fihrist_rdf.ns import CATALOG, MDHN, bind

CATALOG_RE = re.compile(
    r"/catalog/(person_[^/\s\"'#]+|subject_[^/\s\"'#]+|work_[^/\s\"'#]+|manuscript_[^/\s\"'#]+)"
)

EXPAND_PREDS = (
    MDHN.hasContribution,
    MDHN.contributor,
    MDHN.onItem,
    MDHN.hasItem,
    MDHN.hasPartItem,
    MDHN.referencesWork,
    MDHN.hasSubject,
    MDHN.heldBy,
    MDHN.heldAt,
    MDHN.digitallyPublishedBy,
    MDHN.role,
    SKOS.exactMatch,
    SKOS.closeMatch,
)

TYPE_FILL = {
    str(MDHN.Person): ("#D6EAF8", "#1A5276"),
    str(MDHN.Contribution): ("#E8DAEF", "#6C3483"),
    str(MDHN.Manuscript): ("#D5F5E3", "#196F3D"),
    str(MDHN.ManuscriptItem): ("#FDEBD0", "#B9770E"),
    str(MDHN.Work): ("#FADBD8", "#922B21"),
    str(MDHN.Heading): ("#F9E79F", "#9A7D0A"),
    str(MDHN.GLAM): ("#D4EFDF", "#1E8449"),
}


def nid(uri):
    return "n" + hashlib.md5(str(uri).encode("utf-8")).hexdigest()[:12]


def qname(g, node):
    try:
        return g.namespace_manager.qname(node)
    except Exception:
        s = str(node)
        if "#" in s:
            return s.rsplit("#", 1)[-1]
        return s.rsplit("/", 1)[-1]


def esc(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", " ")
        .replace("\n", "\\n")
    )


def expand(g, person):
    """Closed neighbourhood: person, contributions, mss, all items, works, subjects, GLAMs, matches, roles."""
    entities = set([person])
    for contrib in g.subjects(MDHN.contributor, person):
        entities.add(contrib)
        for ms in g.subjects(MDHN.hasContribution, contrib):
            entities.add(ms)
            stack = list(g.objects(ms, MDHN.hasItem))
            seen_items = set()
            while stack:
                item = stack.pop()
                if item in seen_items:
                    continue
                seen_items.add(item)
                entities.add(item)
                stack.extend(g.objects(item, MDHN.hasPartItem))
            for pred in (
                MDHN.hasSubject,
                MDHN.heldBy,
                MDHN.heldAt,
                MDHN.digitallyPublishedBy,
            ):
                entities.update(g.objects(ms, pred))
        entities.update(g.objects(contrib, MDHN.onItem))
        entities.update(g.objects(contrib, MDHN.role))
    extra = set()
    for e in list(entities):
        extra.update(g.objects(e, MDHN.referencesWork))
        extra.update(g.objects(e, SKOS.exactMatch))
        extra.update(g.objects(e, SKOS.closeMatch))
        extra.update(g.objects(e, MDHN.hasComponent))
        extra.update(g.objects(e, MDHN.facet))
    entities.update(extra)
    return entities


def literals_for(g, node):
    """Every literal triple, grouped by predicate, values unsorted-unique, nothing dropped."""
    grouped = defaultdict(list)
    types = []
    for p, o in g.predicate_objects(node):
        if p == RDF.type:
            types.append(qname(g, o))
            continue
        if isinstance(o, Literal):
            grouped[p].append(str(o))
    lines = []
    if types:
        lines.append("a " + ", ".join(sorted(set(types))))
    pred_order = [
        RDFS.label,
        SKOS.prefLabel,
        SKOS.altLabel,
        DCTERMS.identifier,
        MDHN.xmlId,
        MDHN.shelfmark,
        MDHN.roleCode,
        DCTERMS.date,
        DCTERMS.language,
        DCTERMS.spatial,
        DCTERMS.type,
        MDHN.inCollection,
        MDHN.material,
        MDHN.facetEvidence,
        MDHN.madsType,
        MDHN.teiPath,
        DCTERMS.description,
    ]
    seen_pred = set()
    for p in pred_order:
        if p in grouped:
            seen_pred.add(p)
            pname = qname(g, p)
            for val in grouped[p]:
                compact = " ".join(val.split())
                lines.append("%s: %s" % (pname, compact))
    for p, vals in sorted(grouped.items(), key=lambda kv: qname(g, kv[0])):
        if p in seen_pred:
            continue
        pname = qname(g, p)
        for val in vals:
            compact = " ".join(val.split())
            lines.append("%s: %s" % (pname, compact))
    return lines, types


def write_dot(g, person, entities, out_path):
    lines = [
        "digraph person_complete {",
        "    rankdir=TB;",
        "    splines=true;",
        "    overlap=false;",
        "    concentrate=false;",
        '    fontname="Segoe UI, Helvetica, Arial, sans-serif";',
        "    fontsize=11;",
        '    label="Complete RDF neighbourhood of %s\\n%d entities — no facts omitted";'
        % (esc(qname(g, person)), len(entities)),
        '    node [fontname="Segoe UI, Helvetica, Arial, sans-serif", fontsize=8, shape=box, style="rounded,filled"];',
        '    edge [fontname="Segoe UI, Helvetica, Arial, sans-serif", fontsize=7, color="#7F8C8D"];',
        "",
    ]

    clusters = defaultdict(list)
    for e in sorted(entities, key=lambda x: str(x)):
        types = set(str(t) for t in g.objects(e, RDF.type))
        if str(MDHN.Person) in types:
            clusters["01_person"].append(e)
        elif str(MDHN.Work) in types:
            clusters["02_works"].append(e)
        elif str(MDHN.Manuscript) in types:
            clusters["03_manuscripts"].append(e)
        elif str(MDHN.Contribution) in types:
            clusters["04_contributions"].append(e)
        elif str(MDHN.ManuscriptItem) in types:
            clusters["05_items"].append(e)
        elif str(MDHN.Heading) in types:
            clusters["06_subjects"].append(e)
        elif str(MDHN.GLAM) in types:
            clusters["07_glams"].append(e)
        else:
            clusters["08_other"].append(e)

    cluster_titles = {
        "01_person": "Person",
        "02_works": "Works",
        "03_manuscripts": "Manuscripts",
        "04_contributions": "Contributions (roles)",
        "05_items": "Manuscript items (including nested)",
        "06_subjects": "Subjects",
        "07_glams": "GLAMs",
        "08_other": "External matches, roles, facets",
    }

    for key in sorted(clusters):
        members = clusters[key]
        if not members:
            continue
        lines.append("    subgraph cluster_%s {" % key)
        lines.append('        label="%s (%d)";' % (cluster_titles[key], len(members)))
        lines.append('        style="rounded"; color="#BFC9CA";')
        for e in members:
            lit_lines, types = literals_for(g, e)
            fill, stroke = "#F4F6F7", "#5D6D7E"
            for t in g.objects(e, RDF.type):
                if str(t) in TYPE_FILL:
                    fill, stroke = TYPE_FILL[str(t)]
                    break
            header = qname(g, e)
            body = "\\n".join(esc(x) for x in ([header] + lit_lines))
            pen = "2" if e == person else "1"
            lines.append(
                '        %s [label="%s", fillcolor="%s", color="%s", penwidth=%s];'
                % (nid(e), body, fill, stroke, pen)
            )
        lines.append("    }")
        lines.append("")

    edge_seen = set()
    for s in entities:
        for p, o in g.predicate_objects(s):
            if p == RDF.type:
                continue
            if not isinstance(o, URIRef):
                continue
            if o not in entities:
                continue
            ek = (s, p, o)
            if ek in edge_seen:
                continue
            edge_seen.add(ek)
            lines.append(
                '    %s -> %s [label="%s"];' % (nid(s), nid(o), esc(qname(g, p)))
            )

    lines.append("}")
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {k: len(v) for k, v in clusters.items()}, len(edge_seen)


def keys_of_type(g, entities, cls):
    out = []
    for e in entities:
        if (e, RDF.type, cls) in g:
            out.append(str(e).rsplit("/", 1)[-1])
    return sorted(out)


def fetch_html(person_key):
    import requests
    from lxml import html as lhtml

    url = "https://www.fihrist.org.uk/catalog/" + person_key
    ctx = ssl._create_unverified_context()
    try:
        r = requests.get(
            url,
            timeout=60,
            headers={"User-Agent": "Fihrist-As-RDF/2.0"},
            verify=False,
        )
        r.raise_for_status()
    except Exception as exc:
        return {"error": str(exc), "url": url, "manuscripts": [], "works": [], "subjects": [], "persons": []}
    keys = {"manuscripts": set(), "works": set(), "subjects": set(), "persons": set()}
    doc = lhtml.fromstring(r.content)
    for href in doc.xpath("//a/@href"):
        for m in CATALOG_RE.findall(href or ""):
            if m.startswith("manuscript_"):
                keys["manuscripts"].add(m)
            elif m.startswith("work_"):
                keys["works"].add(m)
            elif m.startswith("subject_"):
                keys["subjects"].add(m)
            elif m.startswith("person_"):
                keys["persons"].add(m)
    title = " ".join(" ".join(doc.xpath("//h1//text() | //title//text()")).split())
    return {
        "error": None,
        "url": url,
        "title": title,
        "status": r.status_code,
        "manuscripts": sorted(keys["manuscripts"]),
        "works": sorted(keys["works"]),
        "subjects": sorted(keys["subjects"]),
        "persons": sorted(keys["persons"]),
    }


def write_compare(rdf_keys, html, path):
    def diff(a, b):
        sa, sb = set(a), set(b)
        return sorted(sa - sb), sorted(sb - sa), sorted(sa & sb)

    lines = [
        "# Complete RDF vs Fihrist HTML — `person_100206721` (Saʿdī)",
        "",
        "RDF source: Cambridge harvest only. HTML: " + str(html.get("url")),
        "",
    ]
    if html.get("error"):
        lines.append("**HTML fetch error:** " + html["error"])
        lines.append("")
    if html.get("title"):
        lines.append("HTML title: **" + html["title"] + "**")
        lines.append("")
    lines += [
        "| kind | RDF | HTML | both | only RDF (Cambridge) | only HTML (other libraries / page extras) |",
        "|---|---|---|---|---|---|",
    ]
    cmp = {}
    for kind in ("manuscripts", "works", "subjects"):
        only_r, only_h, both = diff(rdf_keys[kind], html.get(kind) or [])
        cmp[kind] = {"only_rdf": only_r, "only_html": only_h, "both": both}
        lines.append(
            "| %s | %d | %d | %d | %d | %d |"
            % (kind, len(rdf_keys[kind]), len(html.get(kind) or []), len(both), len(only_r), len(only_h))
        )
    lines.append("")
    lines.append(
        "HTML is the **union catalogue**. RDF here is **Cambridge only**, so HTML-only manuscripts are expected (Bodleian, BL, …)."
    )
    lines.append("Subjects on HTML person pages may be absent: Fihrist indexes subjects on manuscript records.")
    lines.append("")
    for kind in ("manuscripts", "works", "subjects"):
        d = cmp[kind]
        lines.append("## " + kind)
        lines.append("")
        lines.append("Both: `" + ("`, `".join(d["both"]) or "—") + "`")
        lines.append("")
        lines.append("Only RDF: `" + ("`, `".join(d["only_rdf"]) or "—") + "`")
        lines.append("")
        lines.append("Only HTML: `" + ("`, `".join(d["only_html"]) or "—") + "`")
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    return cmp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttl", default="data/rdf/harvest_cambridge_university.ttl")
    ap.add_argument("--person", default="person_100206721")
    ap.add_argument("--out", default="visualizations/cambridge_person_100206721.dot")
    args = ap.parse_args()

    g = bind(Graph())
    g.parse(args.ttl, format="turtle")
    person = CATALOG[args.person]
    entities = expand(g, person)
    counts, nedges = write_dot(g, person, entities, args.out)
    rdf_keys = {
        "manuscripts": keys_of_type(g, entities, MDHN.Manuscript),
        "works": keys_of_type(g, entities, MDHN.Work),
        "subjects": keys_of_type(g, entities, MDHN.Heading),
        "items": keys_of_type(g, entities, MDHN.ManuscriptItem),
        "contributions": keys_of_type(g, entities, MDHN.Contribution),
    }
    import urllib3

    urllib3.disable_warnings()
    html = fetch_html(args.person)
    report = Path("data/reports") / (args.person + ".rdf_vs_html.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    cmp = write_compare(rdf_keys, html, report)
    js = Path("data/reports") / (args.person + ".rdf_vs_html.json")
    js.write_text(
        json.dumps({"rdf_keys": rdf_keys, "html": html, "compare": cmp, "dot_clusters": counts, "edges": nedges}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    sys.stdout.write(
        "entities=%d edges=%d clusters=%s\nDOT %s\nHTML error=%s mss_html=%d\n%s\n"
        % (len(entities), nedges, counts, args.out, html.get("error"), len(html.get("manuscripts") or []), report)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
