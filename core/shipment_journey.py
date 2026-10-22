"""Issue #160: visual index, never a workflow authority or persisted stage store.

Relevance comes from the already-built execution profile. Occurrence comes
only from canonical facts; coarse ``done`` can mean scope/configuration and
must never be interpreted as proof that customs or a vessel departed.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Mapping

from core.customs_truth import customs_clearance_confirmed
from core.stage_guidance import guidance_for_node

SEA_FACT_FIELDS = frozenset({'si_status', 'vgm_status', 'si_cutoff', 'vgm_cutoff', 'gate_in_at', 'export_declaration_no',
                             # LOGI-199 T1 — SEA FCL lifecycle evidence. Each is its OWN fact:
                             # a booking request is not a confirmation, a declaration is not
                             # clearance, ATD is not on-board proof, delivery is not POD.
                             'booking_status', 'empty_pickup_at', 'stuffing_at', 'eir_no',
                             'export_clearance_at', 'on_board_at', 'do_released_at',
                             'pod_received_at', 'empty_return_at',
                             # LOGI-199 T2 — SEA LCL: CFS receipt (count/weight/CBM),
                             # consolidation and destination deconsolidation. Choosing
                             # LCL is never evidence that cargo was received/consolidated.
                             'cfs_received_at', 'cfs_receipt_no', 'cfs_package_count',
                             'cfs_weight_kg', 'cfs_cbm', 'consolidated_at', 'deconsolidated_at'})
# LOGI-199 T3/T4 — AIR and ROAD evidence live in their own existing-style
# blocks next to ``sea_export`` (``data.1.2.air_facts`` / ``data.1.2.road_facts``)
# and go through the SAME writer. No sea field can complete an air/road node.
AIR_FACT_FIELDS = frozenset({'export_declaration_no', 'export_clearance_at', 'air_acceptance_at', 'air_gross_kg',
                             'air_chargeable_kg', 'air_screened_at', 'air_uplifted_at', 'do_released_at', 'pod_received_at'})
ROAD_FACT_FIELDS = frozenset({'export_declaration_no', 'export_clearance_at', 'ltl_received_at', 'ltl_package_count',
                              'ltl_weight_kg', 'ltl_consolidated_at', 'border_crossed_at', 'handover_doc_no', 'pod_received_at'})
MODE_FACT_FIELDS = {'SEA': SEA_FACT_FIELDS, 'AIR': AIR_FACT_FIELDS, 'ROAD': ROAD_FACT_FIELDS}
MODE_FACT_BLOCK = {'SEA': 'sea_export', 'AIR': 'air_facts', 'ROAD': 'road_facts'}
_NUMBER_FACTS = {'air_gross_kg': ('Trọng lượng cân tại kho (kg)', False), 'air_chargeable_kg': ('Trọng lượng tính cước (kg)', False),
                 'ltl_package_count': ('Số kiện nhận (LTL)', True), 'ltl_weight_kg': ('Trọng lượng nhận (kg)', False),
                 'cfs_package_count': ('Số kiện nhận tại CFS', True), 'cfs_weight_kg': ('Trọng lượng nhận (kg)', False),
                 'cfs_cbm': ('Thể tích nhận (CBM)', False)}
SUBMISSION_STATES = ('UNKNOWN', 'RECEIVED', 'SUBMITTED', 'ACCEPTED')
BOOKING_STATES = ('UNKNOWN', 'REQUESTED', 'CONFIRMED')
_SECONDARY_FACTS = frozenset({'cfs_receipt_no', 'cfs_weight_kg'})
_TEXT_FACTS = {'export_declaration_no': ('Số tờ khai xuất', 120), 'eir_no': ('Số EIR', 120),
               'cfs_receipt_no': ('Số phiếu nhận hàng CFS', 120), 'handover_doc_no': ('Số biên bản giao nhận', 120)}
_STATUS_OPTIONS = [{'value': k, 'label': v} for k, v in zip(SUBMISSION_STATES, ('Chưa biết', 'Đã nhận hồ sơ', 'Đã gửi hãng tàu', 'Hãng tàu đã chấp nhận'))]
_BOOKING_OPTIONS = [{'value': k, 'label': v} for k, v in zip(BOOKING_STATES, ('Chưa biết', 'Đã gửi yêu cầu booking', 'Hãng tàu đã xác nhận booking'))]


def _fact_field(key: str, label: str) -> dict[str, Any]:
    if key == 'booking_status':
        return {'key': key, 'label': label, 'kind': 'status', 'options': _BOOKING_OPTIONS}
    if key.endswith('_status'):
        return {'key': key, 'label': label, 'kind': 'status', 'options': _STATUS_OPTIONS}
    if key in _NUMBER_FACTS:
        return {'key': key, 'label': label, 'kind': 'number'}
    return {'key': key, 'label': label, 'kind': 'text' if key in _TEXT_FACTS else 'datetime'}
# Bước (3B) — the ONLY two extra stages approved for TT_ENTRUSTED_SUB.
# They are real journey vocabulary (finance attribution + module anchors),
# but they are only ever EMITTED for that one commercial flow.
ENTRUSTMENT_READY_ID = 'entrustment-ready'
ENTRUSTMENT_HANDOVER_ID = 'tt-warehouse-handover'
ENTRUSTMENT_STAGE_IDS = (ENTRUSTMENT_READY_ID, ENTRUSTMENT_HANDOVER_ID)
JOURNEY_STAGE_IDS = frozenset({'cfs-receipt', 'booking', 'pickup', 'customs-export', 'si-vgm', 'gate-in', 'etd', 'on-board', 'transit', 'arrival', 'customs-import', 'delivery', 'ORIGIN_HANDOFF', 'CROSS_BORDER', 'MAIN_CARRIAGE', 'SEA_DOCUMENTS', 'AIR_DOCUMENTS', 'RAIL_CARRIAGE', 'SEA_EQUIPMENT', 'SEA_CONSOLIDATION', 'ROAD_TRUCK_PROFILE', 'ROAD_CONSOLIDATION', 'INSURANCE_EVIDENCE',
                             'entrustment-ready', 'tt-warehouse-handover'})


def normalize_sea_facts(fields: Mapping[str, Any]) -> dict[str, str]:
    return normalize_mode_facts(fields, 'SEA')


def normalize_mode_facts(fields: Mapping[str, Any], mode: str) -> dict[str, str]:
    allowed = MODE_FACT_FIELDS.get(mode)
    if allowed is None:
        raise ValueError('Phương thức này chưa có mốc bằng chứng được phép ghi.')
    if not fields or set(fields) - allowed:
        raise ValueError('Trường Sea Export không được phép ghi.' if mode == 'SEA' else 'Trường không thuộc phương thức của lô.')
    out = {}
    for key, value in fields.items():
        raw = str(value or '').strip()
        if key in _NUMBER_FACTS:
            label, integer = _NUMBER_FACTS[key]
            if raw:  # blank stays UNKNOWN — never coerced to 0
                try:
                    number = float(raw.replace(',', ''))
                except ValueError as exc:
                    raise ValueError(f'{label} phải là số không âm hoặc để trống.') from exc
                if number < 0 or number != number or number in (float('inf'),) or (integer and number != int(number)):
                    raise ValueError(f'{label} phải là số {"nguyên " if integer else ""}không âm hoặc để trống.')
                raw = str(int(number)) if integer else (f'{number:g}')
        elif key in _TEXT_FACTS:
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
                  work_modules: Mapping[str, Any] | None = None,
                  entrustment_stages: Mapping[str, Any] | None = None) -> dict[str, Any]:
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
    mode = str(profile.get('mode') or '')
    # The evidence block of THIS shipment's mode (sea_export / air_facts /
    # road_facts). An AIR or ROAD node never reads the sea block.
    mf = (transport.get(MODE_FACT_BLOCK[mode]) or {}) if mode in MODE_FACT_BLOCK else {}
    customs = data.get('2.4') or {}
    delivery = data.get('2.7') or {}
    main = operational.get('main_leg') or {}
    pickup = operational.get('pickup_leg') or {}
    codes = {s.get('code') for s in profile.get('stages') or []}
    scope = set(profile.get('serviceScope') or []) if profile.get('serviceScopeConfirmed') else set()
    nodes: list[dict] = []

    def add(id, label, family, tab, *, done=False, evidence='', deadline='', categories=(), owned=False, fields=()):
        # #199 inv.: a stage popup shows at most 5 primary fields; the rest are
        # marked secondary and folded (still editable, never hidden).
        declared = [_fact_field(k, l) for k, l in fields]
        for f in declared[:]:
            if f['key'] in _SECONDARY_FACTS and len(declared) > 5:
                f['secondary'] = True
        nodes.append({'factFields': declared,'id': id, 'label': label, 'family': family, 'targetTab': tab,
                      # Derived occurrence truth; visual overlays never erase it.
                      'completed': bool(done),
                      'state': 'COMPLETED' if done else 'UPCOMING',
                      'factState': 'KNOWN' if evidence else 'UNKNOWN', 'evidence': str(evidence or ''),
                      'deadline': str(deadline or ''), 'owned': owned,
                      'current': False, 'blockers': [], 'dependencies': [],
                      'documentCategories': list(categories),
                      # #210 da3f05b: category-only metadata is NOT a stage
                      # association — attribution is fail-closed AFTER all nodes
                      # exist (unique-owner check below), never inline here.
                      'documentIds': []})
        if mode == 'SEA' or id in ENTRUSTMENT_STAGE_IDS:
            guidance = guidance_for_node(
                id, load_model=str(profile.get('loadModel') or ''),
                owned=bool(owned), completed=bool(done),
            )
            if guidance is not None:
                nodes[-1]['guidance'] = guidance

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
        cleared = mf.get('export_clearance_at')
        add('customs-export', 'CUSTOMS EXPORT' if is_sea else 'Hải quan xuất', 'EXPORT_HANDLING', 'lay-hang',
            done=bool(cleared),
            evidence=' · '.join(x for x in (f"Tờ khai: {decl}" if decl else '', f"Thông quan: {cleared}" if cleared else '') if x),
            categories=('customs',), owned=bool({'EXPORT_HANDLING', 'EXPORT_CUSTOMS'} & scope),
            fields=(('export_declaration_no', 'Số tờ khai xuất (đã đăng ký)'), ('export_clearance_at', 'Thông quan xuất thực tế')) if mode in MODE_FACT_BLOCK else ())
    has_main = is_sea and 'booking' in {n['id'] for n in nodes}
    if has_main:
        lcl = profile.get('loadModel') == 'LCL'
        if 'MAIN_CARRIAGE' in scope and lcl:
            # LCL: the consolidator owns the container VGM; only the SI for
            # this shipment is Trường Thành's evidence.
            si = sea.get('si_status', 'UNKNOWN')
            add('si-vgm', 'SI', 'SEA_DOCUMENTS', 'van-tai', done=si == 'ACCEPTED',
                evidence=f'SI: {si}' if si != 'UNKNOWN' else '', deadline=sea.get('si_cutoff') or '',
                categories=('si',), owned=True, fields=(('si_status', 'Trạng thái SI'), ('si_cutoff', 'SI cutoff')))
        elif 'MAIN_CARRIAGE' in scope:
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
        cfs_keys = ('cfs_received_at', 'cfs_receipt_no', 'cfs_package_count', 'cfs_weight_kg', 'cfs_cbm', 'consolidated_at')
        if lcl and ({'MAIN_CARRIAGE', 'ORIGIN_TERMINAL_OR_BORDER'} & scope or any(sea.get(k) for k in cfs_keys)):
            # CFS receipt and consolidation are separate facts; receipt alone
            # never completes the node and blank quantities stay UNKNOWN.
            qty = ' / '.join(x for x in (
                f"{sea['cfs_package_count']} kiện" if sea.get('cfs_package_count') else '',
                f"{sea['cfs_weight_kg']} kg" if sea.get('cfs_weight_kg') else '',
                f"{sea['cfs_cbm']} CBM" if sea.get('cfs_cbm') else '') if x)
            cfs_evidence = ' · '.join(x for x in (
                f"Nhận CFS: {sea['cfs_received_at']}" if sea.get('cfs_received_at') else '',
                f"Phiếu: {sea['cfs_receipt_no']}" if sea.get('cfs_receipt_no') else '', qty,
                f"Đã ghép: {sea['consolidated_at']}" if sea.get('consolidated_at') else '') if x)
            add('cfs-receipt', 'CFS / GHÉP HÀNG', 'SEA_CONSOLIDATION', 'van-tai', done=bool(sea.get('consolidated_at')),
                evidence=cfs_evidence, categories=('transport',),
                owned=bool({'MAIN_CARRIAGE', 'ORIGIN_TERMINAL_OR_BORDER'} & scope),
                fields=(('cfs_received_at', 'Nhận hàng tại CFS'), ('cfs_receipt_no', 'Số phiếu nhận hàng'),
                        ('cfs_package_count', 'Số kiện'), ('cfs_weight_kg', 'Trọng lượng (kg)'), ('cfs_cbm', 'CBM'),
                        ('consolidated_at', 'Đã ghép vào container')))
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
        legs = [l for l in (transport.get('transport_legs') or []) if isinstance(l, Mapping)]
        air_legs = sorted((l for l in legs if l.get('mode') == 'Air'), key=lambda l: int(l.get('sequence') or 0))
        truck_legs = [l for l in legs if l.get('mode') == 'Truck']
        replaced: set[str] = set()
        chain_after: list = []
        if mode == 'AIR' and ({'MAIN_CARRIAGE', 'AIR_DOCUMENTS'} & codes):
            # LOGI-199 T3 — AIR occurrence chain from AIR facts only.
            owns_main = 'MAIN_CARRIAGE' in scope
            first, last = (air_legs[0] if air_legs else {}), (air_legs[-1] if air_legs else {})
            awb = ' / '.join(x for x in (f"MAWB {first.get('mawb')}" if first.get('mawb') else '',
                                         f"HAWB {first.get('hawb')}" if first.get('hawb') else '') if x)
            flights = ', '.join(str(l.get('flight_no')) for l in air_legs if l.get('flight_no'))
            replaced |= {'MAIN_CARRIAGE', 'AIR_DOCUMENTS'}
            chain_after = [
                ('air-booking', 'AWB / CHUYẾN BAY', 'AIR_DOCUMENTS', dict(
                    done=bool(awb and flights), evidence=' · '.join(x for x in (awb, f"Chuyến: {flights}" if flights else '') if x),
                    categories=('booking', 'transport'), owned=owns_main)),
                ('air-acceptance', 'NHẬN HÀNG KHO / SOI CHIẾU', 'AIR_DOCUMENTS', dict(
                    done=bool(mf.get('air_acceptance_at')),
                    evidence=' · '.join(x for x in (
                        f"Kho nhận: {mf['air_acceptance_at']}" if mf.get('air_acceptance_at') else '',
                        f"GW {mf['air_gross_kg']} kg" if mf.get('air_gross_kg') else '',
                        f"CW {mf['air_chargeable_kg']} kg" if mf.get('air_chargeable_kg') else '',
                        f"Soi chiếu: {mf['air_screened_at']}" if mf.get('air_screened_at') else '') if x),
                    categories=('transport',), owned=owns_main or bool({'EXPORT_HANDLING', 'ORIGIN_TERMINAL_OR_BORDER'} & scope),
                    fields=(('air_acceptance_at', 'Kho hàng không nhận hàng'), ('air_gross_kg', 'Cân thực tế (kg)'),
                            ('air_chargeable_kg', 'Trọng lượng tính cước (kg)'), ('air_screened_at', 'Soi chiếu an ninh (nếu áp dụng)')))),
                # Flight ATD is not proof THIS cargo flew (offload happens):
                # only an uplift confirmation completes the node.
                ('uplift', 'CẤT CÁNH / UPLIFT', 'MAIN_CARRIAGE', dict(
                    done=bool(mf.get('air_uplifted_at')),
                    evidence=' · '.join(x for x in (f"ATD: {first.get('atd')}" if first.get('atd') else '',
                                                    f"Uplift: {mf['air_uplifted_at']}" if mf.get('air_uplifted_at') else '') if x),
                    deadline=first.get('etd') or '', owned=owns_main,
                    fields=(('air_uplifted_at', 'Xác nhận hàng đã bay (uplift)'),))),
            ]
            if len(air_legs) > 1:
                chain_after.append(('air-transit', 'TRUNG CHUYỂN', 'MAIN_CARRIAGE', dict(
                    done=bool(last.get('atd')), evidence=f"Chặng cuối ATD: {last.get('atd')}" if last.get('atd') else '',
                    deadline=last.get('etd') or '', owned=owns_main)))
            chain_after.append(('air-arrival', 'HẠ CÁNH / ATA', 'MAIN_CARRIAGE', dict(
                done=bool(last.get('ata')), evidence=f"ATA: {last.get('ata')}" if last.get('ata') else '',
                deadline=last.get('eta') or '', categories=('transport',), owned=owns_main)))
            current = 'air-arrival' if last.get('ata') else ('uplift' if mf.get('air_uplifted_at') else '')
        if mode == 'ROAD':
            # LOGI-199 T4 — ROAD: vehicle/driver, LTL receipt+consolidation,
            # border only for cross-border scope. Maritime fields never apply.
            trucks = [u for l in truck_legs for u in (l.get('units') or []) if isinstance(u, Mapping) and u.get('kind') == 'truck']
            if 'ROAD_TRUCK_PROFILE' in codes or trucks:
                ready = [u for u in trucks if str(u.get('number') or '').strip() and str(u.get('driver_name') or '').strip()]
                replaced.add('ROAD_TRUCK_PROFILE')
                chain_after.append(('road-vehicle', 'XE / TÀI XẾ', 'ROAD_TRUCK_PROFILE', dict(
                    done=bool(trucks) and len(ready) == len(trucks),
                    evidence=' · '.join(' '.join(x for x in (str(u.get('number') or ''), str(u.get('type_size') or ''), str(u.get('driver_name') or '')) if x) for u in trucks),
                    categories=('transport',), owned=bool({'ORIGIN_PICKUP', 'MAIN_CARRIAGE'} & scope))))
            if 'ROAD_CONSOLIDATION' in codes:
                replaced.add('ROAD_CONSOLIDATION')
                chain_after.append(('road-ltl', 'NHẬN & GHÉP HÀNG (LTL)', 'ROAD_CONSOLIDATION', dict(
                    done=bool(mf.get('ltl_consolidated_at')),
                    evidence=' · '.join(x for x in (
                        f"Nhận: {mf['ltl_received_at']}" if mf.get('ltl_received_at') else '',
                        f"{mf['ltl_package_count']} kiện" if mf.get('ltl_package_count') else '',
                        f"{mf['ltl_weight_kg']} kg" if mf.get('ltl_weight_kg') else '',
                        f"Đã ghép xe: {mf['ltl_consolidated_at']}" if mf.get('ltl_consolidated_at') else '') if x),
                    categories=('transport',), owned=bool({'ORIGIN_PICKUP', 'MAIN_CARRIAGE'} & scope),
                    fields=(('ltl_received_at', 'Nhận hàng lẻ'), ('ltl_package_count', 'Số kiện'),
                            ('ltl_weight_kg', 'Trọng lượng (kg)'), ('ltl_consolidated_at', 'Đã ghép lên xe')))))
            if 'CROSS_BORDER' in codes:
                replaced.add('CROSS_BORDER')
                chain_after.append(('road-border', 'QUA CỬA KHẨU', 'CROSS_BORDER', dict(
                    done=bool(mf.get('border_crossed_at')),
                    evidence=f"Qua cửa khẩu: {mf['border_crossed_at']}" if mf.get('border_crossed_at') else '',
                    categories=('customs', 'transport'), owned='CROSS_BORDER_COORDINATION' in scope,
                    fields=(('border_crossed_at', 'Thời điểm qua cửa khẩu'),))))
        for stage in profile.get('stages') or []:
            code = stage['code']
            if code in {'ORIGIN_PICKUP', 'EXPORT_HANDLING', 'IMPORT_CUSTOMS', 'DELIVERY'} | replaced:
                continue
            add(code, stage['label'], code, 'van-tai',
                owned=stage.get('reason') == 'SERVICE_SCOPE')
        for node_id, label, family, kwargs in chain_after:
            add(node_id, label, family, 'van-tai', **kwargs)
    if 'IMPORT_CUSTOMS' in codes:
        # The canonical form/writer stores an explicit boolean clearance flag.
        # Legacy strings ('false', 'REGISTERED') are not proof of clearance.
        cleared_import = customs_clearance_confirmed(customs.get('customs_status'))
        add('customs-import', 'CUSTOMS IMPORT' if is_sea else 'Hải quan nhập', 'IMPORT_CUSTOMS', 'nhap',
            done=cleared_import, evidence=customs.get('clearance_date') if cleared_import else customs.get('tk_no'),
            categories=('customs',), owned='IMPORT_CUSTOMS' in scope)
    if 'DELIVERY' in codes:
        delivered = bool(delivery.get('is_delivered'))
        delivery_fields: tuple = ()
        delivery_evidence = delivery.get('delivered_at') if delivered else ''
        if mode in MODE_FACT_BLOCK:
            # D/O release, actual delivery, POD and (FCL) empty return are
            # separate facts. Delivery occurrence stays the 2.7 truth; POD never
            # substitutes for it and a POD recorded before delivery is flagged.
            load = profile.get('loadModel')
            if mode == 'SEA':
                delivery_fields = ((('deconsolidated_at', 'Tách hàng tại CFS đích'),) if load == 'LCL' else ()) + (
                    ('do_released_at', 'D/O / EDO đã phát hành'), ('pod_received_at', 'POD đã nhận')) + (
                    (('empty_return_at', 'Trả container rỗng'),) if load == 'FCL' else ())
            elif mode == 'AIR':
                delivery_fields = (('do_released_at', 'Lệnh giao hàng sân bay (D/O)'), ('pod_received_at', 'POD đã nhận'))
            else:
                delivery_fields = (('handover_doc_no', 'Số biên bản giao nhận'), ('pod_received_at', 'POD đã nhận'))
            keys = {k for k, _ in delivery_fields}
            delivery_evidence = ' · '.join(x for x in (
                f"Tách hàng: {mf['deconsolidated_at']}" if 'deconsolidated_at' in keys and mf.get('deconsolidated_at') else '',
                f"D/O: {mf['do_released_at']}" if 'do_released_at' in keys and mf.get('do_released_at') else '',
                f"Biên bản: {mf['handover_doc_no']}" if 'handover_doc_no' in keys and mf.get('handover_doc_no') else '',
                f"Đã giao: {delivery.get('delivered_at') or 'có'}" if delivered else '',
                f"POD: {mf['pod_received_at']}" if mf.get('pod_received_at') else '',
                f"Trả rỗng: {mf['empty_return_at']}" if 'empty_return_at' in keys and mf.get('empty_return_at') else '') if x)
        add('delivery', 'DELIVERY' if is_sea else 'Giao hàng', 'DELIVERY', 'nhap',
            done=delivered, evidence=delivery_evidence,
            deadline=delivery.get('delivery_date'), categories=('transport',),
            owned=bool({'DESTINATION_TRUCKING', 'FINAL_DELIVERY'} & scope), fields=delivery_fields)
        if mf.get('pod_received_at') and not delivered and mode in MODE_FACT_BLOCK:
            nodes[-1]['blockers'].append('POD đã ghi nhưng lô chưa xác nhận giao thực tế — kiểm tra lại mốc giao hàng.')

    # LOGI-199: category-only attachment metadata is NOT an explicit stage
    # association. A transport record could be booking, pickup or delivery;
    # a customs file could be import or export. Fail closed on shared categories
    # so a stage popup never attributes a whole-lot file to the wrong node.
    # (#210 da3f05b — GIỮ NGUYÊN khi tích hợp chuỗi T1–T5.)
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
        if n['id'] in {'si-vgm', 'gate-in', 'cfs-receipt'}:
            if previous: edges.append({'from': previous, 'to': n['id']})
            branch.append(n['id'])
            continue
        parents = branch or ([previous] if previous else [])
        for parent in parents: edges.append({'from': parent, 'to': n['id']})
        branch = []
        previous = n['id']
    for edge in edges: by_id[edge['to']]['dependencies'].append(edge['from'])

    # ------------------------------------------------------------------
    # Bước (3B) — exactly TWO extra stages, ONLY for TT_ENTRUSTED_SUB.
    # They are appended AFTER the base chain and deliberately get NO journey
    # edge: nothing in the repository records where the handover happens in
    # the transport chain, so drawing an edge (or moving the CURRENT marker)
    # would invent a direction. Completion is proven by the recorded
    # evidence block alone — never by the flow, contract status, an upload,
    # customs, D/O, PXK, partner selection or another leg's DELIVERY.
    # ------------------------------------------------------------------
    entrustment = entrustment_stages if isinstance(entrustment_stages, Mapping) else {}
    if entrustment.get('applicable'):
        parties = [row for row in (entrustment.get('parties') or []) if isinstance(row, Mapping)]
        party_options = [
            {'value': str(row.get('id') or ''), 'label': str(row.get('label') or '')}
            for row in parties if str(row.get('id') or '')
        ]
        values = dict(entrustment.get('values') or {})
        ready = dict(entrustment.get('ready') or {})
        handover = dict(entrustment.get('handover') or {})
        ready_fields = [
            {'key': 'entrustment_ready_at', 'label': 'Ngày xác nhận đủ điều kiện thực hiện', 'kind': 'datetime'},
            {'key': 'entrustment_ready_ref', 'label': 'Căn cứ xác nhận (số hợp đồng / biên bản phạm vi ủy thác)', 'kind': 'text'},
        ]
        handover_fields = [
            {'key': 'warehouse_handover_at', 'label': 'Thời điểm bàn giao thực tế', 'kind': 'datetime'},
            {'key': 'warehouse_handover_from', 'label': 'Bên giao (ghi nhận thực tế)', 'kind': 'status', 'options': party_options},
            {'key': 'warehouse_handover_from_label', 'label': 'Tên hiển thị bên giao (nếu tên danh mục chưa đúng)', 'kind': 'text', 'secondary': True},
            {'key': 'warehouse_handover_to', 'label': 'Bên nhận (ghi nhận thực tế)', 'kind': 'status', 'options': party_options},
            {'key': 'warehouse_handover_to_label', 'label': 'Tên hiển thị bên nhận (nếu tên danh mục chưa đúng)', 'kind': 'text', 'secondary': True},
            {'key': 'warehouse_handover_doc_no', 'label': 'Số biên bản giao nhận', 'kind': 'text'},
        ]
        for node_id, label, node_fields, block in (
            (ENTRUSTMENT_READY_ID, 'Nhận ủy thác — đủ điều kiện thực hiện', ready_fields, ready),
            (ENTRUSTMENT_HANDOVER_ID, 'Bàn giao hàng tại kho', handover_fields, handover),
        ):
            add(node_id, label, node_id.upper().replace('-', '_'), 'nhap',
                done=bool(block.get('done')), evidence=str(block.get('evidence') or ''),
                owned=True)
            nodes[-1]['factFields'] = node_fields
            nodes[-1]['factValues'] = {key: str(values.get(key) or '') for key in values}
            nodes[-1]['factSource'] = 'entrustment_evidence'
            nodes[-1]['missingEvidence'] = [str(item) for item in (block.get('missing') or [])]
            by_id[node_id] = nodes[-1]
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
            'primaryAction': dict(primary),
            # Name kept for client compatibility: the CURRENT mode's evidence values.
            'seaFacts': {k: (shipment.get('china_export_decl_no') or '') if k == 'export_declaration_no' else mf.get(k, 'UNKNOWN' if k.endswith('_status') else '')
                         for k in MODE_FACT_FIELDS.get(mode, SEA_FACT_FIELDS)},
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
    # LCL does not require a dedicated container VGM — only SI matters.
    # FCL and other sea load models require both SI and VGM acceptance.
    # (Batch 2, f5171b0 — Owner chốt 2026-10-19: LCL SI-only là ĐÚNG.)
    required = (('si_status', 'SI'),) if profile.get('loadModel') == 'LCL' else (('si_status', 'SI'), ('vgm_status', 'VGM'))
    for key, label in required:
        if facts.get(key) != 'ACCEPTED':
            return {'text': f'Kiểm tra và ghi nhận trạng thái {label}', 'detail': 'Chưa có bằng chứng hãng tàu chấp nhận; tệp đính kèm không tự xác nhận submission.', 'stage': 'si-vgm'}
    if 'ORIGIN_TERMINAL_OR_BORDER' in scope and profile.get('loadModel') == 'FCL' and not facts.get('gate_in_at'):
        return {'text': 'Ghi nhận gate-in thực tế', 'detail': 'Chưa có mốc container vào bãi.', 'stage': 'gate-in'}
    return None
