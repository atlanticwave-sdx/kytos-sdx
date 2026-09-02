# VLAN `"any"` support

## Introduction

An L2VPN request sent to the Kytos SDX NApp describes each endpoint with a
`port_id` and a `vlan` attribute. Normally the `vlan` carries a concrete
choice made by the user: a specific VLAN ID (`"100"`), an untagged endpoint
(`"untagged"`), a VLAN range (`"1:100"`), or every VLAN on the port (`"all"`).

This document adds support for a new value: **`vlan: "any"`**.

When a user requests the `vlan` attribute with the value `"any"`, they are
explicitly stating that they do **not** need a specific VLAN ID and are
delegating the choice to the SDX Controller. This is useful whenever the user
only needs *a* working L2VPN and does not care which VLAN carries it — for
example, automated provisioning where any free VLAN is acceptable.

In that case the Kytos SDX NApp must **choose an available VLAN ID on behalf of
the user**. The choice is made from the network interface's advertised
`vlan_range` — the same range the NApp already publishes in the converted
topology (`_converted_topo`) under the port identified by `port_id`
(`nodes[].ports[].services["l2vpn-ptp"]["vlan_range"]`). The advertised range is
the authoritative pool of VLANs the operator is willing to expose through SDX on
that port, so the candidate VLAN is always drawn from it.

Picking a VLAN from the advertised range is necessary but not sufficient: a VLAN
that is *within range* may already be in use by another circuit. Therefore, on
top of restricting candidates to the advertised `vlan_range`, the NApp also
validates that each candidate is genuinely free by consulting the live,
in-memory Kytos core `Interface` object through
[`is_tag_available()`](https://github.com/kytos-ng/kytos/blob/master/kytos/core/interface.py),
the read-only counterpart of
[`use_tags()`](https://github.com/kytos-ng/kytos/blob/master/kytos/core/interface.py#L350).
The first VLAN that is both in range and available (scanning from the lowest) is
selected, embedded into the EVC request as a concrete value, and handed to
mef_eline, which performs the actual, authoritative tag reservation when it
creates the circuit.

### Why check-only (and not reserve) in this NApp

EVC creation is delegated to the Kytos **mef_eline** NApp via its REST API, and
mef_eline reserves the endpoint tags itself (via `use_tags()`) while it builds
the circuit. If the SDX NApp were to *reserve* the candidate VLAN with
`use_tags()` before posting to mef_eline, mef_eline would then try to reserve the
same tag again and fail with `KytosTagsAreNotAvailable` (double reservation).

To avoid that, the SDX NApp uses the read-only `is_tag_available()` to pick a
free VLAN and lets mef_eline own the reservation. This leaves a narrow
time-of-check/time-of-use (TOCTOU) window between "checked as available" and
"reserved by mef_eline"; a concurrent request could grab the VLAN in between.
That window is closed with a bounded retry: if mef_eline rejects the POST because
the tag is no longer available, the NApp excludes the failed VLAN, re-resolves
the `"any"` endpoint(s), and retries.

## Design decisions

- **Validation model:** check-only via `Interface.is_tag_available()`; mef_eline
  performs the real reservation on EVC creation.
- **Selection order:** lowest available VLAN first (deterministic, easy to test).
- **Scope:** every request path that parses endpoint VLANs — `create_l2vpn`
  (`l2vpn/1.0` POST), `update_l2vpn` (`l2vpn/1.0/{id}` PATCH), and
  `create_l2vpn_ptp` (`v1/l2vpn_ptp` POST).
- **Both endpoints `"any"`:** each endpoint is resolved independently against its
  own port's advertised range.
- **TOCTOU:** bounded retry (default 3 attempts) around resolve + mef_eline POST,
  excluding VLANs that mef_eline rejected as unavailable.

## Data model relied upon

- Candidate pool: `_converted_topo["nodes"][i]["ports"][j]["services"]["l2vpn-ptp"]["vlan_range"]`,
  matched by the port `id` (the SDX URN, equal to the request `port_id`).
  Shape is a list of ranges, e.g. `[[1, 4094]]` or fragmented `[[1, 10], [20, 30]]`.
- `port_id -> kytos interface_id` via `self.sdx2kytos`.
- Live availability: `self.controller.get_interface_by_id(kytos_id).is_tag_available(vlan)`
  — authoritative in-memory free-tag state that the REST topology does not expose.

## Implementation steps

### 1. `_get_port_vlan_range(port_id)`
Under `self._topo_lock`, scan `self._converted_topo.get("nodes", [])` for a port
whose `id == port_id`; return its `services["l2vpn-ptp"]["vlan_range"]` or `None`
when the port or the `l2vpn-ptp` service is absent. Normalize a flat
`[start, end]` into `[[start, end]]` so callers always get a list of ranges.

### 2. `choose_available_vlan(kytos_id, port_id, exclude=())`
Returns `(vlan_int, None)` on success or `(None, msg)` on failure:

```
vlan_range = self._get_port_vlan_range(port_id)
    -> if falsy (None or []): return None, "No l2vpn-ptp vlan_range available for port {port_id}"
iface = self.controller.get_interface_by_id(kytos_id)
    -> if None: return None, "Interface not found for {port_id}"
for [start, end] in vlan_range:            # ascending
    for vlan in range(start, end + 1):
        if vlan in exclude:
            continue
        if iface.is_tag_available(vlan):
            return vlan, None
return None, "No VLAN available for 'any' on port {port_id}"
```

### 3. `parse_evc()` — resolve `"any"` where port context exists
In the endpoint loop, when `endpoint["vlan"] == "any"`, call
`choose_available_vlan(kytos_id, sdx_id)` and set a concrete
`{"tag_type": "vlan", "value": vlan}`; otherwise keep the existing `parse_vlan`
path.

### 4. `create_l2vpn_ptp()` — same branch
When `content[attr]["tag"]["value"] == "any"`, resolve via
`choose_available_vlan(kytos_id, sdx_id)`; otherwise keep `parse_vlan`.

### 5. `parse_vlan()` — comment + defensive behavior
Keep the `"any"` rejection branch as a safety net (callers now intercept `"any"`
before reaching it) and update the comment: `"any"` is resolved by the caller via
`choose_available_vlan` using port context; reaching `parse_vlan` with `"any"`
means the port context was missing.

### 6. Bounded retry (TOCTOU)
In `create_l2vpn` and `create_l2vpn_ptp`, wrap resolve + mef_eline POST in a loop
(<= 3 attempts). Track which endpoints were `"any"` and the VLANs tried per
endpoint; if mef_eline rejects the POST because a tag is unavailable, add the
tried VLAN(s) to the per-endpoint `exclude` set, re-resolve, and retry. Any other
failure fails immediately, as today.

The conflict is detected from the mef_eline 400 body, which looks like:

```json
{"description":"KytosTagsAreNotAvailable, The tags 101 are not available in aa:00:00:00:00:00:00:01:50","code":400}
```

`_is_tag_conflict()` parses the body as JSON and inspects the `description`
field for the `KytosTagsAreNotAvailable` exception name (or `not available`),
falling back to a raw-text substring check when the body is not JSON.

## Tests (`tests/unit/test_main.py`)

- `choose_available_vlan`: lowest available picked; used tags skipped; respects a
  restricted `vlan_range` subset; error when interface missing; `exclude` honored.
- **Empty range:** `vlan_range == []` returns `(None, msg)` and never calls
  `is_tag_available`.
- **Fragmented range:** `vlan_range == [[1, 10], [20, 30]]` where the whole first
  fragment `[1, 10]` is unavailable forces iteration into the second fragment and
  returns `20`; assert 1..10 were probed before `20` is chosen.
- `_get_port_vlan_range`: found / not-found / flat-vs-nested normalization.
- `parse_evc` with `vlan: "any"` on one and on both endpoints (independent
  resolution).
- `create_l2vpn_ptp` with `"any"`.
- `test_parse_vlan`: defensive `"any"` rejection message unchanged.
- Retry: first mef_eline POST returns a tag-conflict, second succeeds with the
  next VLAN.

## Docs

- `openapi.yml` and `README.rst`: document `"any"` as an accepted `vlan` value
  and its "SDX chooses a free VLAN from the advertised range" semantics.
- `CHANGELOG.rst`: add the feature entry.
