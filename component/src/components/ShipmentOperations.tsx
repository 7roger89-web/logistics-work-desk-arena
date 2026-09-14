import { useEffect, useState } from "react";
import { Package, Plane, Save, Ship, TrainFront, Trash2, Truck } from "lucide-react";
import { Field, GhostBtn, PrimaryBtn, inputCls } from "./ui";
import type { Cargo, Shipment, TransportLeg, TransportMode, TransportUnit } from "../lib/viewmodel";
import type { LogiEventName } from "../lib/dispatcher";

interface Props {
  shipment: Shipment;
  dispatch: (event: LogiEventName, payload: unknown) => boolean;
  toast: (title: string, desc?: string, tone?: "green" | "red" | "amber" | "blue") => void;
}

type CargoDraft = {
  goodsDescription: string;
  packageCount: string;
  packageType: string;
  grossWeightKg: string;
  cbm: string;
  dimensions: string;
  note: string;
};

const MODES: TransportMode[] = ["Truck", "Sea", "Air", "Rail"];

const uid = (prefix: string) => {
  const random = typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${random}`;
};

const blankLeg = (sequence: number, mode: TransportMode = "Truck"): TransportLeg => ({
  id: uid("leg"),
  sequence,
  mode,
  origin: "",
  destination: "",
  carrier: "",
  etd: "",
  eta: "",
  atd: "",
  ata: "",
  bookingNo: "",
  mbl: "",
  hbl: "",
  vessel: "",
  voyage: "",
  mawb: "",
  hawb: "",
  flightNo: "",
  units: [],
});

const blankUnit = (kind: "truck" | "container"): TransportUnit => ({
  id: uid(kind),
  kind,
  number: "",
  typeSize: "",
  sealNo: "",
  driverName: "",
  driverPhone: "",
});

const cargoDraft = (cargo: Cargo): CargoDraft => ({
  goodsDescription: cargo?.goodsDescription ?? "",
  packageCount: cargo?.packs == null ? "" : String(cargo.packs),
  packageType: cargo?.type ?? "",
  grossWeightKg: cargo?.weight == null ? "" : String(cargo.weight),
  cbm: cargo?.cbm == null ? "" : String(cargo.cbm),
  dimensions: cargo?.dims ?? "",
  note: cargo?.note ?? "",
});

const modeIcon = (mode: TransportMode) => {
  if (mode === "Sea") return <Ship size={18} />;
  if (mode === "Air") return <Plane size={18} />;
  if (mode === "Rail") return <TrainFront size={18} />;
  return <Truck size={18} />;
};

export default function ShipmentOperations({ shipment, dispatch, toast }: Props) {
  const [legs, setLegs] = useState<TransportLeg[]>(() =>
    (shipment.transportLegs ?? []).map((leg) => ({ ...leg, units: (leg.units ?? []).map((unit) => ({ ...unit })) }))
  );
  const [cargo, setCargo] = useState<CargoDraft>(() => cargoDraft(shipment.cargo));

  // The two editors are intentionally independent. A generic shipment version
  // bump may come from saving the other editor (or from a rejected write's
  // unchanged readback), so only that editor's canonical content may reset its
  // local draft.
  const transportRevision = JSON.stringify(shipment.transportLegs ?? []);
  const cargoRevision = JSON.stringify(cargoDraft(shipment.cargo));

  useEffect(() => {
    setLegs((shipment.transportLegs ?? []).map((leg) => ({
      ...leg,
      units: (leg.units ?? []).map((unit) => ({ ...unit })),
    })));
  }, [shipment.id, transportRevision]);

  useEffect(() => {
    setCargo(cargoDraft(shipment.cargo));
  }, [shipment.id, cargoRevision]);

  const updateLeg = <K extends keyof TransportLeg>(id: string, key: K, value: TransportLeg[K]) => {
    setLegs((rows) => rows.map((leg) => leg.id === id ? { ...leg, [key]: value } : leg));
  };

  const updateUnit = (legId: string, unitId: string, key: keyof TransportUnit, value: string) => {
    setLegs((rows) => rows.map((leg) => leg.id !== legId ? leg : {
      ...leg,
      units: leg.units.map((unit) => unit.id === unitId ? { ...unit, [key]: value } : unit),
    }));
  };

  const changeMode = (leg: TransportLeg, mode: TransportMode) => {
    if (mode === leg.mode) return;
    if (leg.units.length > 0 && !window.confirm("Đổi mode sẽ xóa xe/container trong bản nháp của chặng này. Tiếp tục?")) return;
    setLegs((rows) => rows.map((row) => row.id === leg.id ? { ...row, mode, units: [] } : row));
  };

  const resequence = (rows: TransportLeg[]) => rows.map((leg, index) => ({ ...leg, sequence: index + 1 }));

  const moveLeg = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= legs.length) return;
    const next = [...legs];
    [next[index], next[target]] = [next[target], next[index]];
    setLegs(resequence(next));
  };

  const removeLeg = (leg: TransportLeg) => {
    if (!window.confirm(`Xóa chặng ${leg.sequence} (${leg.mode}) khỏi bản nháp?`)) return;
    setLegs((rows) => resequence(rows.filter((row) => row.id !== leg.id)));
  };

  const addUnit = (legId: string, kind: "truck" | "container") => {
    setLegs((rows) => rows.map((leg) => leg.id === legId
      ? { ...leg, units: [...leg.units, blankUnit(kind)] }
      : leg));
  };

  const removeUnit = (legId: string, unit: TransportUnit) => {
    const label = unit.number || (unit.kind === "truck" ? "xe chưa có biển số" : "container chưa có số");
    if (!window.confirm(`Xóa ${label} khỏi bản nháp?`)) return;
    setLegs((rows) => rows.map((leg) => leg.id !== legId ? leg : {
      ...leg,
      units: leg.units.filter((row) => row.id !== unit.id),
    }));
  };

  const saveLegs = () => {
    const transportLegs = resequence(legs).map((leg) => ({
      id: leg.id,
      sequence: leg.sequence,
      mode: leg.mode,
      origin: leg.origin.trim(),
      destination: leg.destination.trim(),
      carrier: leg.carrier.trim(),
      etd: leg.etd.trim(),
      eta: leg.eta.trim(),
      atd: leg.atd.trim(),
      ata: leg.ata.trim(),
      booking_no: leg.bookingNo.trim(),
      mbl: leg.mbl.trim(),
      hbl: leg.hbl.trim(),
      vessel: leg.vessel.trim(),
      voyage: leg.voyage.trim(),
      mawb: leg.mawb.trim(),
      hawb: leg.hawb.trim(),
      flight_no: leg.flightNo.trim(),
      units: leg.units.map((unit) => ({
        id: unit.id,
        kind: unit.kind,
        number: unit.number.trim(),
        type_size: unit.typeSize.trim(),
        seal_no: unit.sealNo.trim(),
        driver_name: unit.driverName.trim(),
        driver_phone: unit.driverPhone.trim(),
      })),
    }));
    const sent = dispatch("shipment_transport_save", { shipmentId: shipment.id, transportLegs });
    if (sent) toast("Đã gửi các chặng vận chuyển", "Backend kiểm tra ID/thứ tự/mode rồi ghi atomic và đọc lại.", "green");
    else toast("Không gửi được", "Component chưa kết nối backend.", "red");
  };

  const saveCargo = () => {
    const sent = dispatch("shipment_transport_save", {
      shipmentId: shipment.id,
      cargoSummary: {
        goods_description: cargo.goodsDescription.trim(),
        package_count: cargo.packageCount.trim(),
        package_type: cargo.packageType.trim(),
        gross_weight_kg: cargo.grossWeightKg.trim(),
        cbm: cargo.cbm.trim(),
        dimensions: cargo.dimensions.trim(),
        note: cargo.note.trim(),
      },
    });
    if (sent) toast("Đã gửi thông tin hàng hóa", "Ô số để trống được lưu là chưa biết, không đổi thành 0.", "green");
    else toast("Không gửi được", "Component chưa kết nối backend.", "red");
  };

  return (
    <div className="space-y-4" id="missing-anchor">
      {!shipment.transportLegsStructured && (
        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-[13.5px] text-amber-950">
          <p className="font-extrabold">Lô cũ · đang đọc dữ liệu tương thích</p>
          <p className="mt-0.5">Các giá trị xe/container đơn hiện có được hiển thị thành các chặng riêng. Chỉ khi bấm “Lưu các chặng”, danh sách đang thấy mới trở thành dữ liệu structured; trường cũ vẫn được giữ nguyên.</p>
        </div>
      )}

      <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <div className="flex flex-wrap items-start gap-2 mb-4">
          <div>
            <h2 className="font-extrabold text-[18px] text-[#0f2a4a] flex items-center gap-2"><Package size={20} className="text-[#1e5aa8]" /> HÀNG HÓA</h2>
            <p className="text-[13px] text-slate-500 mt-0.5">Tóm tắt hàng của cả lô; không phải SKU/WMS. Để trống nghĩa là chưa biết.</p>
          </div>
          {!shipment.cargoStructured && shipment.cargo?.qtyPkg && (
            <span className="ml-auto rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-[12px] font-bold text-amber-800">Dữ liệu cũ: {shipment.cargo.qtyPkg}</span>
          )}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="sm:col-span-2 lg:col-span-4">
            <Field label="Mô tả hàng"><input data-field="cargo-goods-description" value={cargo.goodsDescription} onChange={(e) => setCargo((v) => ({ ...v, goodsDescription: e.target.value }))} placeholder="Tên/mô tả hàng thực tế" className={inputCls()} /></Field>
          </div>
          <Field label="Số kiện"><input value={cargo.packageCount} onChange={(e) => setCargo((v) => ({ ...v, packageCount: e.target.value }))} inputMode="numeric" placeholder="Bỏ trống = chưa biết" className={inputCls()} /></Field>
          <Field label="Loại kiện"><input value={cargo.packageType} onChange={(e) => setCargo((v) => ({ ...v, packageType: e.target.value }))} placeholder="Thùng / pallet / bao…" className={inputCls()} /></Field>
          <Field label="GW (kg)"><input value={cargo.grossWeightKg} onChange={(e) => setCargo((v) => ({ ...v, grossWeightKg: e.target.value }))} inputMode="decimal" placeholder="Bỏ trống = chưa biết" className={inputCls()} /></Field>
          <Field label="CBM"><input value={cargo.cbm} onChange={(e) => setCargo((v) => ({ ...v, cbm: e.target.value }))} inputMode="decimal" placeholder="Bỏ trống = chưa biết" className={inputCls()} /></Field>
          <div className="sm:col-span-2">
            <Field label="Kích thước"><input value={cargo.dimensions} onChange={(e) => setCargo((v) => ({ ...v, dimensions: e.target.value }))} placeholder="VD: 120 × 80 × 100 cm / pallet" className={inputCls()} /></Field>
          </div>
          <div className="sm:col-span-2">
            <Field label="Ghi chú"><input value={cargo.note} onChange={(e) => setCargo((v) => ({ ...v, note: e.target.value }))} placeholder="Ghi chú vận hành về hàng" className={inputCls()} /></Field>
          </div>
        </div>
        <PrimaryBtn onClick={saveCargo} className="w-full sm:w-auto mt-4"><Save size={16} /> LƯU HÀNG HÓA</PrimaryBtn>
      </section>

      <section className="rounded-2xl bg-white border border-slate-200 p-4 md:p-5">
        <div className="flex flex-col sm:flex-row sm:items-start gap-3 mb-4">
          <div>
            <h2 className="font-extrabold text-[18px] text-[#0f2a4a] flex items-center gap-2"><Truck size={20} className="text-[#1e5aa8]" /> CÁC CHẶNG VẬN CHUYỂN</h2>
            <p className="text-[13px] text-slate-500 mt-0.5">Mỗi chặng là một fact riêng; xe lấy hàng và xe giao không bị gộp.</p>
          </div>
          <button onClick={() => setLegs((rows) => [...rows, blankLeg(rows.length + 1)])} className="btn-press touch-target sm:ml-auto rounded-xl border-2 border-[#1e5aa8] text-[#1e5aa8] font-extrabold px-4 min-h-[46px]">+ THÊM CHẶNG</button>
        </div>

        {legs.length === 0 && (
          <div className="rounded-xl border-2 border-dashed border-slate-300 p-6 text-center">
            <p className="font-bold text-slate-600">Chưa có chặng vận chuyển.</p>
            <p className="text-[13px] text-slate-500">Có thể lưu lô trước và bổ sung chặng khi điều phối có dữ liệu.</p>
          </div>
        )}

        <div className="space-y-3">
          {legs.map((leg, index) => (
            <details key={leg.id} className="group rounded-2xl border-2 border-slate-200 bg-slate-50/60 overflow-hidden">
              <summary className="cursor-pointer list-none p-3.5 md:p-4 flex flex-wrap items-center gap-2 bg-white">
                <span className="w-9 h-9 rounded-xl bg-[#0f2a4a] text-white grid place-items-center">{modeIcon(leg.mode)}</span>
                <span className="font-extrabold text-[#0f2a4a]">Chặng {leg.sequence} · {leg.mode}</span>
                <span className="text-[13px] text-slate-500 min-w-0 truncate">{leg.origin || "Chưa có nơi đi"} → {leg.destination || "chưa có nơi đến"}</span>
                <span className="ml-auto text-[12px] font-bold text-slate-400 group-open:hidden">Mở để nhập</span>
              </summary>

              <div className="p-3.5 md:p-4 border-t border-slate-200 space-y-4">
                <div className="flex flex-wrap gap-2">
                  <button onClick={() => moveLeg(index, -1)} disabled={index === 0} className="touch-target rounded-lg border bg-white px-3 text-[13px] font-bold disabled:opacity-40">↑ Lên</button>
                  <button onClick={() => moveLeg(index, 1)} disabled={index === legs.length - 1} className="touch-target rounded-lg border bg-white px-3 text-[13px] font-bold disabled:opacity-40">↓ Xuống</button>
                  <button onClick={() => removeLeg(leg)} className="touch-target ml-auto rounded-lg border border-red-200 bg-white px-3 text-[13px] font-bold text-red-700 inline-flex items-center gap-1"><Trash2 size={14} /> Xóa chặng</button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  <Field label="Mode"><select value={leg.mode} onChange={(e) => changeMode(leg, e.target.value as TransportMode)} className={inputCls()}>{MODES.map((mode) => <option key={mode}>{mode}</option>)}</select></Field>
                  <Field label="Hãng vận chuyển"><input value={leg.carrier} onChange={(e) => updateLeg(leg.id, "carrier", e.target.value)} placeholder={leg.mode === "Air" ? "Airline" : "Carrier / nhà xe"} className={inputCls()} /></Field>
                  <Field label={leg.mode === "Air" ? "Sân bay đi" : "Nơi đi"}><input value={leg.origin} onChange={(e) => updateLeg(leg.id, "origin", e.target.value)} className={inputCls()} /></Field>
                  <Field label={leg.mode === "Air" ? "Sân bay đến" : "Nơi đến"}><input value={leg.destination} onChange={(e) => updateLeg(leg.id, "destination", e.target.value)} className={inputCls()} /></Field>
                  <Field label="ETD"><input value={leg.etd} onChange={(e) => updateLeg(leg.id, "etd", e.target.value)} placeholder="YYYY-MM-DD" className={inputCls()} /></Field>
                  <Field label="ETA"><input value={leg.eta} onChange={(e) => updateLeg(leg.id, "eta", e.target.value)} placeholder="YYYY-MM-DD" className={inputCls()} /></Field>
                  <Field label="ATD"><input value={leg.atd} onChange={(e) => updateLeg(leg.id, "atd", e.target.value)} placeholder="YYYY-MM-DD" className={inputCls()} /></Field>
                  <Field label="ATA"><input value={leg.ata} onChange={(e) => updateLeg(leg.id, "ata", e.target.value)} placeholder="YYYY-MM-DD" className={inputCls()} /></Field>
                </div>

                {leg.mode === "Sea" && (
                  <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-3.5">
                    <p className="font-extrabold text-[14px] text-blue-900 mb-3">Thông tin đường biển</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      <Field label="Booking"><input value={leg.bookingNo} onChange={(e) => updateLeg(leg.id, "bookingNo", e.target.value)} className={inputCls()} /></Field>
                      <Field label="Vessel"><input value={leg.vessel} onChange={(e) => updateLeg(leg.id, "vessel", e.target.value)} className={inputCls()} /></Field>
                      <Field label="Voyage"><input value={leg.voyage} onChange={(e) => updateLeg(leg.id, "voyage", e.target.value)} className={inputCls()} /></Field>
                      <Field label="MBL"><input value={leg.mbl} onChange={(e) => updateLeg(leg.id, "mbl", e.target.value)} className={inputCls()} /></Field>
                      <Field label="HBL"><input value={leg.hbl} onChange={(e) => updateLeg(leg.id, "hbl", e.target.value)} className={inputCls()} /></Field>
                    </div>
                  </div>
                )}

                {leg.mode === "Air" && (
                  <div className="rounded-xl border border-sky-200 bg-sky-50/60 p-3.5">
                    <p className="font-extrabold text-[14px] text-sky-900 mb-3">Thông tin hàng không</p>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <Field label="Flight no"><input value={leg.flightNo} onChange={(e) => updateLeg(leg.id, "flightNo", e.target.value)} className={inputCls()} /></Field>
                      <Field label="MAWB"><input value={leg.mawb} onChange={(e) => updateLeg(leg.id, "mawb", e.target.value)} className={inputCls()} /></Field>
                      <Field label="HAWB"><input value={leg.hawb} onChange={(e) => updateLeg(leg.id, "hawb", e.target.value)} className={inputCls()} /></Field>
                    </div>
                  </div>
                )}

                {(leg.mode === "Truck" || leg.mode === "Sea") && (
                  <div className="space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-extrabold text-[14px] text-[#0f2a4a]">{leg.mode === "Truck" ? "Xe tải" : "Container"}</p>
                      <button onClick={() => addUnit(leg.id, leg.mode === "Truck" ? "truck" : "container")} className="btn-press touch-target ml-auto rounded-xl bg-[#1e5aa8] text-white font-bold px-4 min-h-[44px]">+ {leg.mode === "Truck" ? "Thêm xe" : "Thêm container"}</button>
                    </div>
                    {leg.units.map((unit, unitIndex) => (
                      <div key={unit.id} className="rounded-xl bg-white border border-slate-200 p-3.5">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="font-extrabold text-[13.5px] text-[#0f2a4a]">{unit.kind === "truck" ? "Xe" : "Container"} {unitIndex + 1}</span>
                          <button onClick={() => removeUnit(leg.id, unit)} className="touch-target ml-auto text-red-700 text-[12.5px] font-bold inline-flex items-center gap-1"><Trash2 size={13} /> Xóa</button>
                        </div>
                        {unit.kind === "truck" ? (
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                            <Field label="Loại / kích thước"><input data-field="unit-type-size" value={unit.typeSize} onChange={(e) => updateUnit(leg.id, unit.id, "typeSize", e.target.value)} placeholder="VD: 17.5m / tải 30t" className={inputCls()} /></Field>
                            <Field label="Biển số"><input data-field="unit-number" value={unit.number} onChange={(e) => updateUnit(leg.id, unit.id, "number", e.target.value)} className={inputCls()} /></Field>
                            <Field label="Tài xế"><input value={unit.driverName} onChange={(e) => updateUnit(leg.id, unit.id, "driverName", e.target.value)} className={inputCls()} /></Field>
                            <Field label="SĐT tài xế"><input value={unit.driverPhone} onChange={(e) => updateUnit(leg.id, unit.id, "driverPhone", e.target.value)} className={inputCls()} /></Field>
                          </div>
                        ) : (
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <Field label="Số container"><input value={unit.number} onChange={(e) => updateUnit(leg.id, unit.id, "number", e.target.value)} className={inputCls()} /></Field>
                            <Field label="Loại / kích thước"><input value={unit.typeSize} onChange={(e) => updateUnit(leg.id, unit.id, "typeSize", e.target.value)} placeholder="20GP / 40HC" className={inputCls()} /></Field>
                            <Field label="Seal"><input value={unit.sealNo} onChange={(e) => updateUnit(leg.id, unit.id, "sealNo", e.target.value)} className={inputCls()} /></Field>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {leg.mode === "Rail" && <p className="rounded-xl bg-slate-100 border p-3 text-[13px] text-slate-600">Rail V1 chỉ lưu tuyến, hãng và mốc ngày chung; chưa tạo subsystem đường sắt riêng.</p>}
              </div>
            </details>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-2.5 mt-4">
          <PrimaryBtn onClick={saveLegs} className="flex-1"><Save size={16} /> LƯU CÁC CHẶNG</PrimaryBtn>
          <GhostBtn onClick={() => setLegs((shipment.transportLegs ?? []).map((leg) => ({ ...leg, units: (leg.units ?? []).map((unit) => ({ ...unit })) })))}>Hoàn tác bản nháp</GhostBtn>
        </div>
      </section>
    </div>
  );
}
