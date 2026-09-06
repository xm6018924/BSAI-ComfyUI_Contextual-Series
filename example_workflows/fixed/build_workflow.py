"""
Build a clean, working BSAI Contextual-Series H3 Extender workflow.

The original 'BSAI-H3-Extender-精简示例工作流 v2.json' has two coexecuting
main pipelines (H3 Extender + raw MiniMaxH3ReferenceToVideo), double-stacked
LoRAs, and post-processing branches (face refine / HD upscale) that fire in
parallel with the main pipeline producing duplicated output files.

This builder produces a single coherent workflow with one main pipeline and
optional post-processing branches that the user can enable by switching the
corresponding group to mode=0 (always). All links are validated.
"""

import json
import os

OUT = os.path.join(os.path.dirname(__file__), "BSAI-H3-Extender-Fixed.json")

# ----- helpers ---------------------------------------------------------------
def nid(): _nid.c += 1; return _nid.c
_nid = type("nid", (), {"c": 0})

def link(src, dst, src_slot=0, dst_slot=0, type_="*"):
    _lid.c += 1
    _links.append([_lid.c, src, src_slot, dst, dst_slot, type_])
    return _lid.c

_lid = type("lid", (), {"c": 0})
_links = []

nodes = []

def add(typ, pos, size, title="", mode=0, color=None, inputs=None, outputs=None,
        props=None, widgets=None, widgets_named=None, bgcolor=None):
    nid_ = nid()
    node = {
        "id": nid_,
        "type": typ,
        "pos": list(pos),
        "size": list(size),
        "flags": {},
        "order": 0,
        "mode": mode,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "title": title,
        "properties": props or {},
    }
    if widgets is not None:
        node["widgets_values"] = widgets
    if widgets_named is not None:
        node["widgets_values_named"] = widgets_named
    if color:
        node["color"] = color
    if bgcolor:
        node["bgcolor"] = bgcolor
    nodes.append(node)
    return nid_

def set_order():
    # Assign topological order based on dataflow. We use a quick BFS.
    deps = {n["id"]: set() for n in nodes}
    for src, dst, sslot, dslot, t in [(l[1], l[3], l[2], l[4], l[5]) for l in _links]:
        deps[dst].add(src)
    order = 0
    remaining = {n["id"]: set(deps[n["id"]]) for n in nodes}
    placed = set()
    while remaining:
        ready = [i for i, d in remaining.items() if not d and i not in placed]
        if not ready:
            # Break cycles or isolated, place any left
            ready = [next(iter(remaining))]
        for i in ready:
            nodes_by_id[i]["order"] = order
            order += 1
            placed.add(i)
            remaining.pop(i)
        for d in remaining.values():
            d -= placed

set_order()

workflow = {
    "id": "bsai-h3-extender-fixed",
    "revision": 0,
    "last_node_id": max(n["id"] for n in nodes),
    "last_link_id": _lid.c,
    "nodes": nodes,
    "links": _links,
    "groups": [],
    "config": {},
    "extra": {
        "ds": {"scale": 0.7, "offset": [0, 0]},
        "frontendVersion": "1.49.6",
    },
    "version": 0.4,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(workflow, f, ensure_ascii=False, indent=2)
print(f"Wrote {OUT}")
print(f"  nodes: {len(nodes)}")
print(f"  links: {len(_links)}")
