"""Build a Graphviz DOT neighbourhood for one person from a Turtle harvest."""

from __future__ import print_function

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rdflib import Graph
from rdflib.namespace import RDFS, SKOS

from fihrist_rdf.ns import CATALOG, MDHN, bind


def lab(g, node):
    vals = list(g.objects(node, SKOS.prefLabel)) or list(g.objects(node, RDFS.label))
    if not vals:
        return str(node).rsplit("/", 1)[-1]
    return " ".join(str(vals[0]).split())


def qname(g, node):
    try:
        return g.namespace_manager.qname(node)
    except Exception:
        return str(node).rsplit("/", 1)[-1]


def esc(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
    )


def neighbourhood(g, person):
    q = """
    PREFIX mdhn: <https://MehranDHN.github.io/mdhn-ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT DISTINCT ?c ?role ?ms ?item ?work ?subject
    WHERE {
      ?c mdhn:contributor ?person ;
         mdhn:roleCode ?role .
      ?ms mdhn:hasContribution ?c .
      OPTIONAL { ?c mdhn:onItem ?item }
      OPTIONAL { ?item mdhn:referencesWork ?work }
      OPTIONAL { ?ms mdhn:hasSubject ?subject }
    }
    """
    rows = list(g.query(q, initBindings={"person": person}))
    return rows


def to_dot(g, person, rows, max_ms=8):
    ms_roles = defaultdict(set)
    ms_items = defaultdict(set)
    ms_works = defaultdict(set)
    ms_subjects = defaultdict(set)
    for r in rows:
        ms_roles[r.ms].add(str(r.role))
        if r.item:
            ms_items[r.ms].add(r.item)
        if r.work:
            ms_works[r.ms].add(r.work)
        if r.subject:
            ms_subjects[r.ms].add(r.subject)

    # Prefer manuscripts that carry subjects; keep a stable sample.
    ranked = sorted(
        ms_roles.keys(),
        key=lambda m: (-len(ms_subjects[m]), lab(g, m)),
    )
    chosen = ranked[:max_ms]
    omitted = max(0, len(ranked) - len(chosen))

    all_subjects = []
    seen_s = set()
    for m in chosen:
        for s in sorted(ms_subjects[m], key=lambda x: lab(g, x)):
            if s not in seen_s:
                seen_s.add(s)
                all_subjects.append(s)

    all_works = []
    seen_w = set()
    for m in chosen:
        for w in ms_works[m]:
            if w not in seen_w:
                seen_w.add(w)
                all_works.append(w)

    lines = [
        "// Auto-generated from harvest Turtle",
        "digraph person_neighbourhood {",
        "    rankdir=LR;",
        '    fontname="Segoe UI, Helvetica, Arial, sans-serif";',
        '    node [fontname="Segoe UI, Helvetica, Arial, sans-serif", fontsize=11, shape=box, style="rounded,filled"];',
        '    edge [fontname="Segoe UI, Helvetica, Arial, sans-serif", fontsize=9, color="#555555"];',
        "",
        "    person [",
        '        label="%s\\n%s",' % (esc(qname(g, person)), esc(lab(g, person)[:80])),
        '        fillcolor="#D6EAF8", color="#1A5276", penwidth=2',
        "    ];",
        "",
        "    subgraph cluster_mss {",
        '        label="Cambridge manuscripts (sample)";',
        '        color="#D5D8DC"; style="rounded";',
    ]
    for i, m in enumerate(chosen):
        nid = "ms%d" % i
        roles = ",".join(sorted(ms_roles[m]))
        lines.append(
            '        %s [label="%s\\n%s\\nrole=%s", fillcolor="#D5F5E3", color="#196F3D"];'
            % (nid, esc(qname(g, m)), esc(lab(g, m)), esc(roles))
        )
        lines.append('        person -> %s [label="contributor"];' % nid)
    if omitted:
        lines.append(
            '        more [label="+ %d further Cambridge copies\\nnot drawn", fillcolor="#EAFAF1", style="rounded,dashed"];'
            % omitted
        )
        lines.append("        person -> more [style=dashed];")
    lines.append("    }")
    lines.append("")

    if all_works:
        lines.append("    subgraph cluster_works {")
        lines.append('        label="works"; color="#F5B7B1"; style="rounded";')
        for i, w in enumerate(all_works):
            nid = "w%d" % i
            lines.append(
                '        %s [label="%s\\n%s", fillcolor="#FADBD8", color="#922B21"];'
                % (nid, esc(qname(g, w)), esc(lab(g, w)[:60]))
            )
        lines.append("    }")
        for i, m in enumerate(chosen):
            for w in ms_works[m]:
                wi = all_works.index(w)
                lines.append('    ms%d -> w%d [label="referencesWork"];' % (i, wi))
        lines.append("")

    if all_subjects:
        lines.append("    subgraph cluster_subjects {")
        lines.append('        label="subjects of those manuscripts"; color="#F9E79F"; style="rounded";')
        for i, s in enumerate(all_subjects):
            nid = "s%d" % i
            lines.append(
                '        %s [label="%s\\n%s", fillcolor="#F9E79F", color="#9A7D0A"];'
                % (nid, esc(qname(g, s)), esc(lab(g, s)[:70]))
            )
        lines.append("    }")
        for i, m in enumerate(chosen):
            for s in ms_subjects[m]:
                si = all_subjects.index(s)
                lines.append('    ms%d -> s%d [label="hasSubject"];' % (i, si))

    lines.append("}")
    return "\n".join(lines) + "\n", len(ranked), len(chosen), len(all_subjects)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttl", required=True)
    ap.add_argument("--person", default="person_175393012")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-ms", type=int, default=8)
    args = ap.parse_args()

    g = bind(Graph())
    g.parse(args.ttl, format="turtle")
    person = CATALOG[args.person]
    rows = neighbourhood(g, person)
    if not rows:
        sys.stderr.write("No contributions for %s in %s\n" % (args.person, args.ttl))
        return 2
    dot, nms, shown, nsubj = to_dot(g, person, rows, max_ms=args.max_ms)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dot, encoding="utf-8")
    sys.stdout.write(
        "Wrote %s  manuscripts=%d drawn=%d subjects=%d\n" % (out, nms, shown, nsubj)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
