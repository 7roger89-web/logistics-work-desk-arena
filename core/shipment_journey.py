"""Issue #160: visual index, never a workflow authority or persisted stage store.

Relevance comes from the already-built execution profile. Occurrence comes
only from canonical facts; coarse ``done`` can mean scope/configuration and
must never be interpreted as proof that customs or a vessel departed.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Mapping

SEA_FACT_FIELDS = frozenset({'si_status', 'vgm_status', 'si_cutoff', 'vgm_cutoff', 'gate_in_at', 'export_declaration_no',
                             # Completion proofs added with the node-truth fix:
                             # 'booking_status' = hãng tàu đã xác nhận (not just a
                             # booking number); 'on_board_at' = hàng đã lên tàu
                             # (ATD != loaded-on-board). Both ride the existing
                             # normalize_sea_facts + shipment_sea_facts_save writer.
                             'booking_status', 'on_board_at'})
SUBMISSION_STATES = ('UNKNOWN', 'RECEIVED', 'SUBMITTED', 'ACCEPTED')
# LOGI-199 — only project the fields supported by normalize_sea_facts and the
# existing shipment_sea_facts_save writer. These labels describe facts, not
# clearance/completion, and the per-node owned/scope gate remains authoritative.
SEA_STAGE_FACT_FIELDS = {
    'si-vgm': (
        {'key': 'si_status', 'label': 'Trạng thái SI', 'kind': 'status'},
        {'key': 'vgm_status', 'label': 'Trạng thái VGM', 'kind': 'status'},
        {'key': 'si_cutoff', 'label': 'Hạn SI', 'kind': 'datetime', 'secondary': True},
        {'key': 'vgm_cutoff', 'label': 'Hạn VGM', 'kind': 'datetime', 'secondary': True},
    ),
    'gate-in': (
        {'key': 'gate_in_at', 'label': 'Thời điểm Gate-in thực tế', 'kind': 'datetime'},
    ),
    'customs-export': (
        {'key': 'export_declaration_no', 'label': 'Số tờ khai xuất (không đồng nghĩa thông quan)', 'kind': 'text'},
    ),
}
SEA_STATUS_LABELS = {'UNKNOWN': 'Chưa xác nhận', 'RECEIVED': 'Đã nhận',
                     'SUBMITTED': 'Đã gửi', 'ACCEPTED': 'Đã được chấp nhận'}
JOURNEY_STAGE_IDS = frozenset({'booking', 'pickup', 'customs-export', 'si-vgm', 'gate-in', 'etd', 'on-board', 'transit', 'arrival', 'customs-import', 'delivery', 'ORIGIN_HANDOFF', 'CROSS_BORDER', 'MAIN_CARRIAGE', 'SEA_DOCUMENTS', 'AIR_DOCUMENTS', 'RAIL_CARRIAGE', 'SEA_EQUIPMENT', 'SEA_CONSOLIDATION', 'ROAD_TRUCK_PROFILE', 'ROAD_CONSOLIDATION', 'INSURANCE_EVIDENCE'})


def normalize_sea_facts(fields: Mapping[str, Any]) -> dict[str, str]:
    if not fields or set(fields) - SEA_FACT_FIELDS:
        raise ValueError('Trường Sea Export không được phép ghi.')
    out = {}
    for key, value in fields.items():
        raw = str(value or '').strip()
        if key == 'export_declaration_no':
            if len(raw) > 120: raise ValueError('Số tờ khai xuất dài quá 120 ký tự.')
        elif key.endswith('_status'):
            raw = raw or 'UNKNOWN'
            if raw not in SUBMISSION_STATES:
                raise ValueError('Trạng thái SI/VGM phải là UNKNOWN, RECEIVED, SUBMITTED hoặc ACCEPTED.')
        elif raw:
            try:
                parsed = datetime.fromisoformat(raw)
                raw = parsed.isoformat(timespec='minutes') if 'T' in raw else parsed.date().isoformat()
            except ValueError as exc:
                raise ValueError('Mốc thời gian phải là ISO YYYY-MM-DD hoặc YYYY-MM-DDTHH:mm.') from exc
        out[key] = raw
    return out


def build_journey(shipment: Mapping[str, Any], *, profile: Mapping[str, Any],
                  operational: Mapping[str, Any], primary: Mapping[str, Any],
                  dashboard: Mapping[str, Any], attachments: list[dict],
                  work_modules: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Base journey, plus (Issue #162) any attached Work Module instances.

    ``work_modules`` carries the already-loaded ``templates`` + this shipment's
    ``instances``. Composition is ADDITIVE and happens before the single visual
    overlay loop below, so base nodes, base completion facts, current position
    and the primary action keep exactly one authority. With no instances the
    returned payload is identical to the pre-#162 projection.
    """
    data = shipment.get('data') or {}
    transport = data.get('1.2') or {}
    sea = transport.get('sea_export') or {}
    customs = data.get('2.4') or {}
    delivery = data.get('2.7') or {}
    main = operational.get('main_leg') or {}
    pickup = operational.get('pickup_leg') or {}
    codes = {s.get('code') for s in profile.get('stages') or []}
    scope = set(profile.get('serviceScope') or []) if profile.get('serviceScopeConfirmed') else set()
    nodes: list[dict] = []

    def add(id, label, family, tab, *, done=False, evidence='', deadline='', categories=(), owned=False):
        nodes.append({'id': id, 'label': label, 'family': family, 'targetTab': tab,
                      # Derived occurrence truth; visual overlays never erase it.
                      'completed': bool(done),
                      'state': 'COMPLETED' if done else 'UPCOMING',
                      'factState': 'KNOWN' if evidence else 'UNKNOWN', 'evidence': str(evidence or ''),
                      'deadline': str(deadline or ''), 'owned': owned,
                      'current': False, 'blockers': [], 'dependencies': [],
                      'documentCategories': list(categories),
                      'documentIds': []})

    is_sea = profile.get('mode') == 'SEA'
    if is_sea and {'MAIN_CARRIAGE', 'SEA_DOCUMENTS'} & codes:
        owns_main = 'MAIN_CARRIAGE' in scope
        booking = main.get('booking_no')
        # CHỜ XÁC NHẬN khác với có số: a booking NUMBER is not a completion.
        # Done only when a fact proves the carrier confirmed (booking_status).
        booking_status = sea.get('booking_status') or 'UNKNOWN'
        add('booking', 'BOOKING', 'MAIN_CARRIAGE', 'van-tai',
            done=bool(booking) and booking_status == 'ACCEPTED',
            evidence=f"Booking: {booking} · Xác nhận: {booking_status}" if booking else '',
            categories=('booking', 'transport'), owned=owns_main)
    if 'ORIGIN_PICKUP' in codes:
        add('pickup', 'PICKUP' if is_sea else 'Lấy hàng', 'ORIGIN_PICKUP', 'lay-hang',
            done=bool(pickup.get('atd')), evidence=pickup.get('atd'), deadline=pickup.get('etd'),
            categories=('transport',), owned='ORIGIN_PICKUP' in scope)
    if 'EXPORT_HANDLING' in codes:
        decl = shipment.get('china_export_decl_no')
        # A declaration number proves registration, not clearance completion.
        add('customs-export', 'CUSTOMS EXPORT' if is_sea else 'Hải quan xuất', 'EXPORT_HANDLING', 'lay-hang',
            evidence=f"Tờ khai: {decl}" if decl else '', categories=('customs',),
            owned=bool({'EXPORT_HANDLING', 'EXPORT_CUSTOMS'} & scope))
    has_main = is_sea and 'booking' in {n['id'] for n in nodes}
    if has_main:
        # LCL has no shipment-level VGM: the si-vgm node is FCL-only, exactly
        # symmetric with the gate-in FCL gate below.
        if 'MAIN_CARRIAGE' in scope and profile.get('loadModel') == 'FCL':
            si, vgm = sea.get('si_status', 'UNKNOWN'), sea.get('vgm_status', 'UNKNOWN')
            add('si-vgm', 'SI / VGM', 'SEA_DOCUMENTS', 'van-tai',
                done=si == vgm == 'ACCEPTED', evidence=f'SI: {si} · VGM: {vgm}' if si != 'UNKNOWN' or vgm != 'UNKNOWN' else '',
                deadline=' · '.join(x for x in (sea.get('si_cutoff'), sea.get('vgm_cutoff')) if x),
                categories=('si', 'vgm'), owned=True)
        if 'ORIGIN_HANDOFF' in codes and profile.get('loadModel') == 'FCL':
            add('gate-in', 'GATE-IN', 'ORIGIN_HANDOFF', 'van-tai', done=bool(sea.get('gate_in_at')),
                evidence=sea.get('gate_in_at'), categories=('transport',), owned='ORIGIN_TERMINAL_OR_BORDER' in scope)
        atd, ata = main.get('atd'), main.get('ata')
        add('etd', 'ETD', 'MAIN_CARRIAGE', 'van-tai', done=bool(atd),
            evidence=f"ATD: {atd}" if atd else '', deadline=main.get('etd'), owned='MAIN_CARRIAGE' in scope)
        # ATD != loaded-on-board: departure time is never proof the cargo was
        # loaded. Done needs the separate on-board fact (on_board_at) as well.
        on_board = sea.get('on_board_at')
        add('on-board', 'ON BOARD / ATD', 'MAIN_CARRIAGE', 'van-tai',
            done=bool(atd) and bool(on_board),
            evidence=' · '.join(x for x in (f"Khởi hành thực tế: {atd}" if atd else '',
                                            f"Lên tàu: {on_board}" if on_board else '') if x),
            categories=('transport',), owned='MAIN_CARRIAGE' in scope)
        add('transit', 'TRANSIT', 'MAIN_CARRIAGE', 'van-tai', done=bool(atd and ata),
            evidence=f"ATD: {atd}" if atd else '', deadline=main.get('eta'), owned='MAIN_CARRIAGE' in scope)
        add('arrival', 'ARRIVAL', 'MAIN_CARRIAGE', 'van-tai', done=bool(ata),
            evidence=f"ATA: {ata}" if ata else '', deadline=main.get('eta'), categories=('transport',), owned='MAIN_CARRIAGE' in scope)
        # Position is separate from unresolved earlier work. ETA/past ETD are
        # NEVER evidence that a ship departed or arrived. ATD != loaded-on-board.
        current = 'arrival' if ata else 'transit' if atd else ''
    else:
        current = ''
        for stage in profile.get('stages') or []:
            code = stage['code']
            if code in {'ORIGIN_PICKUP', 'EXPORT_HANDLING', 'IMPORT_CUSTOMS', 'DELIVERY'}:
                continue
            add(code, stage['label'], code, 'van-tai',
                owned=stage.get('reason') == 'SERVICE_SCOPE')
    if 'IMPORT_CUSTOMS' in codes:
        add('customs-import', 'CUSTOMS IMPORT' if is_sea else 'Hải quan nhập', 'IMPORT_CUSTOMS', 'nhap',
            done=bool(customs.get('customs_status')), evidence=customs.get('clearance_date') if customs.get('customs_status') else customs.get('tk_no'),
            categories=('customs',), owned='IMPORT_CUSTOMS' in scope)
    if 'DELIVERY' in codes:
        add('delivery', 'DELIVERY' if is_sea else 'Giao hàng', 'DELIVERY', 'nhap',
            done=bool(delivery.get('is_delivered')), evidence=delivery.get('delivered_at') if delivery.get('is_delivered') else '',
            deadline=delivery.get('delivery_date'), categories=('transport',),
            owned=bool({'DESTINATION_TRUCKING', 'FINAL_DELIVERY'} & scope))
    # Issue #199 — the UI already owns the typed short forms, but an absent
    # factFields projection leaves the stage popup read-only. Send only fields
    # from the existing server-side writer's strict whitelist; no fake values
    # and no write permission granted by rendering this metadata.
    for node in nodes:
        if not is_sea or not node['owned'] or node['id'] not in SEA_STAGE_FACT_FIELDS:
            continue
        if node['id'] == 'si-vgm' and profile.get('loadModel') != 'FCL':
            continue  # LCL has no mandatory shipment-level container VGM
        node_fields = []
        for spec in SEA_STAGE_FACT_FIELDS[node['id']]:
            assert spec['key'] in SEA_FACT_FIELDS
            field = dict(spec)
            if field['kind'] == 'status':
                field['options'] = [{'value': value, 'label': SEA_STATUS_LABELS[value]}
                                    for value in SUBMISSION_STATES]
            node_fields.append(field)
        node['factFields'] = node_fields

    # LOGI-199: category-only attachment metadata is NOT an explicit stage
    # association. A transport record could be booking, pickup or delivery;
    # a customs file could be import or export. Fail closed on shared categories
    # so a stage popup never attributes a whole-lot file to the wrong node.
    category_nodes: dict[str, set[str]] = {}
    for node in nodes:
        for category in node['documentCategories']:
            category_nodes.setdefault(category, set()).add(node['id'])
    for node in nodes:
        uniquely_owned = {cat for cat in node['documentCategories']
                          if len(category_nodes.get(cat, ())) == 1}
        node['documentIds'] = [
            a['id'] for a in attachments
            if a.get('id') and a.get('category') in uniquely_owned
        ]
    by_id = {n['id']: n for n in nodes}
    edges = []
    previous = None
    branch = []
    for n in nodes:
        if n['id'] in {'si-vgm', 'gate-in'}:
            if previous: edges.append({'from': previous, 'to': n['id']})
            branch.append(n['id'])
            continue
        parents = branch or ([previous] if previous else [])
        for parent in parents: edges.append({'from': parent, 'to': n['id']})
        branch = []
        previous = n['id']
    for edge in edges: by_id[edge['to']]['dependencies'].append(edge['from'])
    # The same final action can expose a granular missing-fact blocker. Do not
    # turn every future UNKNOWN into an independent task/alert.
    if 'stage=si-vgm' in str(primary.get('route') or '') and 'si-vgm' in by_id:
        by_id['si-vgm']['blockers'].append(str(primary.get('text') or ''))
    if 'stage=gate-in' in str(primary.get('route') or '') and 'gate-in' in by_id:
        by_id['gate-in']['blockers'].append(str(primary.get('text') or ''))
    # Existing profile gaps and dashboard alerts, not a client alert engine.
    for stage in profile.get('stages') or []:
        if stage.get('missing'):
            target = next((n for n in nodes if n['family'] == stage['code']), None)
            if target: target['blockers'].append(stage['missing'])
    for alert in dashboard.get('alerts') or []:
        code = str(alert.get('code', '')).upper()
        targets = ['arrival'] if any(k in code for k in ('ETA', 'FREE_TIME', 'DEADLINE')) else ['pickup'] if 'FACTORY' in code else []
        for id in targets:
            if id in by_id: by_id[id]['blockers'].append(str(alert.get('label') or alert.get('detail') or code))
    # Issue #162 — attached Work Modules join the SAME journey here, before the
    # one overlay loop, so module step nodes obey the same completion-vs-visual
    # rules as base nodes and a blocking module can only ADD attention to a base
    # stage (never rewrite its facts).
    modules = []
    if work_modules and (work_modules.get('instances') or []):
        from core.work_modules import compose_journey_modules
        modules = compose_journey_modules(
            nodes, edges, by_id,
            templates=work_modules.get('templates') or [],
            instances=work_modules.get('instances') or [],
            attachments=attachments,
            target_tab='nhap',
        )
    for n in nodes:
        if n['blockers']: n['state'] = 'PROBLEM'
        elif n['id'] == current: n['state'] = 'CURRENT'
        elif not n['completed'] and n['dependencies'] and all(by_id[p]['completed'] for p in n['dependencies']): n['state'] = 'WAITING'
        n['current'] = n['id'] == current
    journey = {'nodes': nodes, 'edges': edges, 'currentStageId': current,
            'owner': str(dashboard.get('owner') or ''),
            'primaryAction': dict(primary), 'seaFacts': {k: (shipment.get('china_export_decl_no') or '') if k == 'export_declaration_no' else sea.get(k, 'UNKNOWN' if k.endswith('_status') else '') for k in SEA_FACT_FIELDS},
            'positionNote': '' if current else 'Chưa đủ mốc thực tế để xác định vị trí vận hành.'}
    # Rollups exist only when modules do: a shipment without modules keeps the
    # exact pre-#162 payload shape.
    if modules:
        journey['modules'] = modules
    return journey


def sea_requirement(shipment: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, str] | None:
    """Small factual refinement consumed by compose_primary_action, never a
    second final-action authority. Profile gaps/critical alerts still win.
    """
    scope = set(profile.get('serviceScope') or []) if profile.get('serviceScopeConfirmed') else set()
    if profile.get('mode') != 'SEA' or 'MAIN_CARRIAGE' not in scope:
        return None
    facts = ((shipment.get('data') or {}).get('1.2') or {}).get('sea_export') or {}
    # LCL has no shipment-level VGM node (see build_journey): never point the
    # action at a missing si-vgm node — FCL gate mirrors gate-in's below.
    if profile.get('loadModel') == 'FCL':
        for key, label in (('si_status', 'SI'), ('vgm_status', 'VGM')):
            if facts.get(key) != 'ACCEPTED':
                return {'text': f'Kiểm tra và ghi nhận trạng thái {label}', 'detail': 'Chưa có bằng chứng hãng tàu chấp nhận; tệp đính kèm không tự xác nhận submission.', 'stage': 'si-vgm'}
    if 'ORIGIN_TERMINAL_OR_BORDER' in scope and profile.get('loadModel') == 'FCL' and not facts.get('gate_in_at'):
        return {'text': 'Ghi nhận gate-in thực tế', 'detail': 'Chưa có mốc container vào bãi.', 'stage': 'gate-in'}
    return None
