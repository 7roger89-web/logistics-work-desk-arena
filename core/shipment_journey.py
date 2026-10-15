"""Issue #160: visual index, never a workflow authority or persisted stage store.

Relevance comes from the already-built execution profile. Occurrence comes
only from canonical facts; coarse ``done`` can mean scope/configuration and
must never be interpreted as proof that customs or a vessel departed.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Mapping

SEA_FACT_FIELDS = frozenset({'si_status', 'vgm_status', 'si_cutoff', 'vgm_cutoff', 'gate_in_at', 'export_declaration_no',
                             # LOGI-199 T1 — SEA FCL lifecycle evidence. Each is its OWN fact:
                             # a booking request is not a confirmation, a declaration is not
                             # clearance, ATD is not on-board proof, delivery is not POD.
                             'booking_status', 'empty_pickup_at', 'stuffing_at', 'eir_no',
                             'export_clearance_at', 'on_board_at', 'do_released_at',
                             'pod_received_at', 'empty_return_at'})
SUBMISSION_STATES = ('UNKNOWN', 'RECEIVED', 'SUBMITTED', 'ACCEPTED')
BOOKING_STATES = ('UNKNOWN', 'REQUESTED', 'CONFIRMED')
_TEXT_FACTS = {'export_declaration_no': ('Số tờ khai xuất', 120), 'eir_no': ('Số EIR', 120)}
_STATUS_OPTIONS = [{'value': k, 'label': v} for k, v in zip(SUBMISSION_STATES, ('Chưa biết', 'Đã nhận hồ sơ', 'Đã gửi hãng tàu', 'Hãng tàu đã chấp nhận'))]
_BOOKING_OPTIONS = [{'value': k, 'label': v} for k, v in zip(BOOKING_STATES, ('Chưa biết', 'Đã gửi yêu cầu booking', 'Hãng tàu đã xác nhận booking'))]


def _fact_field(key: str, label: str) -> dict[str, Any]:
    if key == 'booking_status':
        return {'key': key, 'label': label, 'kind': 'status', 'options': _BOOKING_OPTIONS}
    if key.endswith('_status'):
        return {'key': key, 'label': label, 'kind': 'status', 'options': _STATUS_OPTIONS}
    return {'key': key, 'label': label, 'kind': 'text' if key in _TEXT_FACTS else 'datetime'}
JOURNEY_STAGE_IDS = frozenset({'booking', 'pickup', 'customs-export', 'si-vgm', 'gate-in', 'etd', 'on-board', 'transit', 'arrival', 'customs-import', 'delivery', 'ORIGIN_HANDOFF', 'CROSS_BORDER', 'MAIN_CARRIAGE', 'SEA_DOCUMENTS', 'AIR_DOCUMENTS', 'RAIL_CARRIAGE', 'SEA_EQUIPMENT', 'SEA_CONSOLIDATION', 'ROAD_TRUCK_PROFILE', 'ROAD_CONSOLIDATION', 'INSURANCE_EVIDENCE'})


def normalize_sea_facts(fields: Mapping[str, Any]) -> dict[str, str]:
    if not fields or set(fields) - SEA_FACT_FIELDS:
        raise ValueError('Trường Sea Export không được phép ghi.')
    out = {}
    for key, value in fields.items():
        raw = str(value or '').strip()
        if key in _TEXT_FACTS:
            label, maximum = _TEXT_FACTS[key]
            if len(raw) > maximum: raise ValueError(f'{label} dài quá {maximum} ký tự.')
        elif key == 'booking_status':
            raw = raw or 'UNKNOWN'
            if raw not in BOOKING_STATES:
                raise ValueError('Trạng thái booking phải là UNKNOWN, REQUESTED hoặc CONFIRMED.')
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

    def add(id, label, family, tab, *, done=False, evidence='', deadline='', categories=(), owned=False, fields=()):
        nodes.append({'factFields': [_fact_field(k, l) for k, l in fields],'id': id, 'label': label, 'family': family, 'targetTab': tab,
                      # Derived occurrence truth; visual overlays never erase it.
                      'completed': bool(done),
                      'state': 'COMPLETED' if done else 'UPCOMING',
                      'factState': 'KNOWN' if evidence else 'UNKNOWN', 'evidence': str(evidence or ''),
                      'deadline': str(deadline or ''), 'owned': owned,
                      'current': False, 'blockers': [], 'dependencies': [],
                      'documentCategories': list(categories),
                      'documentIds': [a['id'] for a in attachments if a.get('category') in categories]})

    is_sea = profile.get('mode') == 'SEA'
    if is_sea and {'MAIN_CARRIAGE', 'SEA_DOCUMENTS'} & codes:
        owns_main = 'MAIN_CARRIAGE' in scope
        booking = main.get('booking_no')
        booking_status = sea.get('booking_status') or 'UNKNOWN'
        # LOGI-199 T1: a booking number/request is not the carrier's
        # confirmation. Only an explicit CONFIRMED fact completes the node.
        booking_evidence = ' · '.join(x for x in (
            f"Booking: {booking}" if booking else '',
            {'REQUESTED': 'Đã gửi yêu cầu, chưa có xác nhận', 'CONFIRMED': 'Hãng tàu đã xác nhận'}.get(booking_status, '')) if x)
        add('booking', 'BOOKING', 'MAIN_CARRIAGE', 'van-tai', done=booking_status == 'CONFIRMED',
            evidence=booking_evidence, categories=('booking', 'transport'), owned=owns_main,
            fields=(('booking_status', 'Trạng thái booking'),))
    if 'ORIGIN_PICKUP' in codes:
        add('pickup', 'PICKUP' if is_sea else 'Lấy hàng', 'ORIGIN_PICKUP', 'lay-hang',
            done=bool(pickup.get('atd')), evidence=pickup.get('atd'), deadline=pickup.get('etd'),
            categories=('transport',), owned='ORIGIN_PICKUP' in scope)
    if 'EXPORT_HANDLING' in codes:
        decl = shipment.get('china_export_decl_no')
        # A declaration number proves registration, not clearance completion.
        cleared = sea.get('export_clearance_at') if is_sea else ''
        add('customs-export', 'CUSTOMS EXPORT' if is_sea else 'Hải quan xuất', 'EXPORT_HANDLING', 'lay-hang',
            done=bool(cleared),
            evidence=' · '.join(x for x in (f"Tờ khai: {decl}" if decl else '', f"Thông quan: {cleared}" if cleared else '') if x),
            categories=('customs',), owned=bool({'EXPORT_HANDLING', 'EXPORT_CUSTOMS'} & scope),
            fields=(('export_declaration_no', 'Số tờ khai xuất (đã đăng ký)'), ('export_clearance_at', 'Thông quan xuất thực tế')) if is_sea else ())
    has_main = is_sea and 'booking' in {n['id'] for n in nodes}
    if has_main:
        if 'MAIN_CARRIAGE' in scope:
            si, vgm = sea.get('si_status', 'UNKNOWN'), sea.get('vgm_status', 'UNKNOWN')
            add('si-vgm', 'SI / VGM', 'SEA_DOCUMENTS', 'van-tai',
                done=si == vgm == 'ACCEPTED', evidence=f'SI: {si} · VGM: {vgm}' if si != 'UNKNOWN' or vgm != 'UNKNOWN' else '',
                deadline=' · '.join(x for x in (sea.get('si_cutoff'), sea.get('vgm_cutoff')) if x),
                categories=('si', 'vgm'), owned=True,
                fields=(('si_status', 'Trạng thái SI'), ('vgm_status', 'Trạng thái VGM'), ('si_cutoff', 'SI cutoff'), ('vgm_cutoff', 'VGM cutoff')))
        if 'ORIGIN_HANDOFF' in codes and profile.get('loadModel') == 'FCL':
            # FCL container chain: empty pickup -> stuffing -> seal/EIR -> gate-in.
            # Each step is its own recorded fact; only the actual gate-in
            # completes the node, and no step is inferred from another.
            units = [u for leg in (transport.get('transport_legs') or []) if isinstance(leg, Mapping) and leg.get('mode') == 'Sea'
                     for u in (leg.get('units') or []) if isinstance(u, Mapping) and u.get('kind') == 'container']
            sealed = sum(1 for u in units if str(u.get('seal_no') or '').strip())
            gate_evidence = ' · '.join(x for x in (
                f"Cấp rỗng: {sea['empty_pickup_at']}" if sea.get('empty_pickup_at') else '',
                f"Đóng hàng: {sea['stuffing_at']}" if sea.get('stuffing_at') else '',
                f"Seal: {sealed}/{len(units)} container" if units and sealed else '',
                f"EIR: {sea['eir_no']}" if sea.get('eir_no') else '',
                f"Gate-in: {sea['gate_in_at']}" if sea.get('gate_in_at') else '') if x)
            add('gate-in', 'GATE-IN', 'ORIGIN_HANDOFF', 'van-tai', done=bool(sea.get('gate_in_at')),
                evidence=gate_evidence, categories=('transport',), owned='ORIGIN_TERMINAL_OR_BORDER' in scope,
                fields=(('empty_pickup_at', 'Cấp container rỗng'), ('stuffing_at', 'Đóng hàng xong'),
                        ('eir_no', 'Số EIR'), ('gate_in_at', 'Gate-in thực tế')))
        atd, ata = main.get('atd'), main.get('ata')
        add('etd', 'ETD', 'MAIN_CARRIAGE', 'van-tai', done=bool(atd),
            evidence=f"ATD: {atd}" if atd else '', deadline=main.get('etd'), owned='MAIN_CARRIAGE' in scope)
        # LOGI-199 T1: ATD is the vessel's departure, NOT proof that this
        # shipment's container was loaded on board. Only on-board evidence
        # (on-board B/L date / carrier loading confirmation) completes it.
        on_board = sea.get('on_board_at')
        add('on-board', 'ON BOARD / ATD', 'MAIN_CARRIAGE', 'van-tai', done=bool(on_board),
            evidence=f"Xếp lên tàu: {on_board}" if on_board else '', categories=('transport',), owned='MAIN_CARRIAGE' in scope,
            fields=(('on_board_at', 'Ngày xếp hàng lên tàu (on-board)'),))
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
        delivered = bool(delivery.get('is_delivered'))
        delivery_fields: tuple = ()
        delivery_evidence = delivery.get('delivered_at') if delivered else ''
        pod_before_delivery = False
        if is_sea:
            # D/O release, actual delivery, POD and empty return are separate
            # facts. Delivery occurrence stays the 2.7 truth; POD never
            # substitutes for it and a POD recorded before delivery is flagged.
            delivery_fields = (('do_released_at', 'D/O / EDO đã phát hành'), ('pod_received_at', 'POD đã nhận'))
            if profile.get('loadModel') == 'FCL':
                delivery_fields += (('empty_return_at', 'Trả container rỗng'),)
            pod_before_delivery = bool(sea.get('pod_received_at')) and not delivered
            delivery_evidence = ' · '.join(x for x in (
                f"D/O: {sea['do_released_at']}" if sea.get('do_released_at') else '',
                f"Đã giao: {delivery.get('delivered_at') or 'có'}" if delivered else '',
                f"POD: {sea['pod_received_at']}" if sea.get('pod_received_at') else '',
                f"Trả rỗng: {sea['empty_return_at']}" if sea.get('empty_return_at') and profile.get('loadModel') == 'FCL' else '') if x)
        add('delivery', 'DELIVERY' if is_sea else 'Giao hàng', 'DELIVERY', 'nhap',
            done=delivered, evidence=delivery_evidence,
            deadline=delivery.get('delivery_date'), categories=('transport',),
            owned=bool({'DESTINATION_TRUCKING', 'FINAL_DELIVERY'} & scope), fields=delivery_fields)
        if pod_before_delivery:
            nodes[-1]['blockers'].append('POD đã ghi nhưng lô chưa xác nhận giao thực tế — kiểm tra lại mốc giao hàng.')
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
    for key, label in (('si_status', 'SI'), ('vgm_status', 'VGM')):
        if facts.get(key) != 'ACCEPTED':
            return {'text': f'Kiểm tra và ghi nhận trạng thái {label}', 'detail': 'Chưa có bằng chứng hãng tàu chấp nhận; tệp đính kèm không tự xác nhận submission.', 'stage': 'si-vgm'}
    if 'ORIGIN_TERMINAL_OR_BORDER' in scope and profile.get('loadModel') == 'FCL' and not facts.get('gate_in_at'):
        return {'text': 'Ghi nhận gate-in thực tế', 'detail': 'Chưa có mốc container vào bãi.', 'stage': 'gate-in'}
    return None
