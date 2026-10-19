"""Nội dung hướng dẫn công đoạn SEA — chỉ là lớp TRÌNH BÀY, không là workflow engine.

Gắn theo node ID có thật và mode SEA. KHÔNG đổi done, evidence, deadline,
state, assignee hay phạm vi dịch vụ; không suy trách nhiệm từ Incoterms.
"""
from __future__ import annotations

STAGE_GUIDANCE: dict[str, dict[str, str]] = {
    "booking": {
        "why": "Yêu cầu booking hoặc số booking chưa chứng minh hãng đã xác nhận.",
        "what_to_do": "Gửi booking, theo dõi xác nhận của hãng/đại lý; lưu số và lịch tàu khi có.",
        "who": "Điều vận hoặc bên đảm nhận booking theo phạm vi dịch vụ.",
        "when": "Theo lịch đặt chỗ và cutoff do hãng/đại lý xác nhận.",
        "needs": "Thông tin lô, hàng/số lượng, cảng đi-đến và lịch dự kiến.",
        "done_when": "Hãng đã xác nhận booking (booking_status=CONFIRMED).",
        "impact": "Chưa có booking xác nhận thì lịch vận tải chưa chắc chắn."
    },
    "pickup": {
        "why": "Có lịch lấy hàng chưa chứng minh xe đã rời điểm lấy.",
        "what_to_do": "Chốt xe, giờ lấy và đầu mối kho; đối chiếu bàn giao, ghi giờ xe rời thực tế.",
        "who": "Điều vận hoặc bên vận tải được phân công lấy hàng.",
        "when": "Theo lịch lấy hàng đã xác nhận với kho.",
        "needs": "Địa chỉ lấy hàng, liên hệ kho, xe và thông tin hàng.",
        "done_when": "Có giờ xe rời điểm lấy thực tế (pickup ATD).",
        "impact": "Thiếu mốc thực tế thì chưa thể xác nhận hàng đã rời kho."
    },
    "customs-export": {
        "why": "Đăng ký tờ khai xuất khác với đã được thông quan.",
        "what_to_do": "Chuẩn bị hồ sơ, khai xuất và theo dõi kết quả thông quan thực tế.",
        "who": "Chứng từ/hải quan hoặc bên được thuê khai xuất.",
        "when": "Theo hạn khai và cutoff thực tế; không mặc định phải sau gate-in.",
        "needs": "Invoice, packing list, thông tin HS và giấy tờ theo mặt hàng.",
        "done_when": "Có mốc thông quan xuất thực tế (export_clearance_at).",
        "impact": "Có số tờ khai mà chưa thông quan vẫn chưa xong việc xuất."
    },
    "si-vgm": {
        "why": "FCL cần cả SI và VGM được chấp nhận; gửi đi chưa có nghĩa là xong.",
        "what_to_do": "FCL: gửi SI/VGM, theo dõi từng mục được bên tiếp nhận chấp nhận.",
        "who": "Chứng từ hoặc bên chịu trách nhiệm SI/VGM theo phạm vi.",
        "when": "Trước SI cutoff và VGM cutoff đã được xác nhận.",
        "needs": "Chi tiết lô, hướng dẫn vận đơn và trọng lượng VGM FCL.",
        "done_when": "FCL: cả SI và VGM có trạng thái ACCEPTED.",
        "impact": "Trễ cutoff hoặc chưa được chấp nhận có thể ảnh hưởng chuyến."
    },
    "gate-in": {
        "why": "Cấp container/đóng hàng chưa chứng minh container đã vào bãi.",
        "what_to_do": "Theo dõi cấp rỗng, đóng hàng, seal/EIR và ghi gate-in thực tế.",
        "who": "Hiện trường/điều vận hoặc bên đảm trách giao bãi.",
        "when": "Trước hạn gate cutoff thực tế do cảng/hãng công bố.",
        "needs": "Container, seal, EIR và kế hoạch giao bãi theo lô.",
        "done_when": "Có giờ container vào bãi thực tế (gate_in_at).",
        "impact": "Chưa có gate-in thì chưa xác nhận được việc giao container."
    },
    "cfs-receipt": {
        "why": "Nhận hàng tại CFS chưa đồng nghĩa hàng đã ghép container.",
        "what_to_do": "Đối chiếu phiếu CFS, kiện/kg/CBM và ghi mốc đã ghép container.",
        "who": "CFS/đại lý gom hàng hoặc bên được giao theo dõi.",
        "when": "Theo lịch nhận CFS và hạn đóng hàng đã được xác nhận.",
        "needs": "Phiếu nhận hàng, số kiện, trọng lượng và CBM thực tế.",
        "done_when": "Hàng đã ghép vào container (consolidated_at), không chỉ nhận CFS.",
        "impact": "Chỉ nhận hàng mà chưa ghép thì công đoạn vẫn chưa hoàn thành."
    },
    "etd": {
        "why": "ETD là kế hoạch; ATD mới là mốc tàu rời cảng thực tế.",
        "what_to_do": "Theo dõi cập nhật lịch tàu; xác nhận và ghi ATD thực tế.",
        "who": "Điều vận hoặc hãng/đại lý cung cấp lịch vận chuyển.",
        "when": "Theo lịch ETD, cập nhật ATD khi tàu thực rời cảng.",
        "needs": "Tên tàu, chuyến và nguồn cập nhật ATD.",
        "done_when": "Có ATD thực tế của chặng chính (main_leg.atd).",
        "impact": "ETD đã qua mà chưa có ATD không được coi là tàu đã chạy."
    },
    "on-board": {
        "why": "ATD của tàu không chứng minh container của lô đã được xếp.",
        "what_to_do": "Lấy xác nhận on-board của đúng lô từ hãng hoặc vận đơn hợp lệ.",
        "who": "Chứng từ/điều vận hoặc đại lý chịu trách nhiệm vận đơn.",
        "when": "Khi hãng xác nhận hàng đã xếp tàu; không suy chỉ từ ATD.",
        "needs": "Thông tin lô/container và chứng từ xác nhận on-board.",
        "done_when": "Có mốc xác nhận hàng lên tàu thực tế (on_board_at).",
        "impact": "Tàu đã chạy nhưng lô vẫn có thể bị offload."
    },
    "transit": {
        "why": "ATD xác nhận tàu đã đi; ATA xác nhận chặng vận tải đã kết thúc.",
        "what_to_do": "Theo dõi tàu/chuyển tải, cập nhật ETA và ghi ATA khi chặng hoàn tất.",
        "who": "Điều vận hoặc đại lý theo dõi hành trình.",
        "when": "Trong suốt chặng vận tải; ETA là dự kiến, ATA là thực tế.",
        "needs": "Số B/L, tàu/chuyến và mốc ATD/ATA từ nguồn vận tải.",
        "done_when": "Có cả ATD và ATA của chặng chính; đang trên đường chưa phải xong.",
        "impact": "Chỉ có ATD là đang vận chuyển, không phải đã tới nơi."
    },
    "arrival": {
        "why": "ETA là dự kiến; ATA mới chứng minh tàu tới cảng đích.",
        "what_to_do": "Theo dõi tàu đến và ghi ATA thực tế; chuẩn bị chứng từ đầu đích nếu thuộc scope.",
        "who": "Điều vận hoặc đại lý tại cảng đích.",
        "when": "Khi hãng/cảng xác nhận tàu đến thực tế.",
        "needs": "Thông báo hàng đến và thông tin tàu/chuyến.",
        "done_when": "Có ATA thực tế của chặng chính (main_leg.ata).",
        "impact": "Thiếu ATA khó xác nhận hàng đến; free time phải kiểm từ hãng/cảng."
    },
    "customs-import": {
        "why": "Đã đăng ký tờ khai chưa phải có xác nhận thông quan nhập.",
        "what_to_do": "Kiểm tra bên đứng nhập, hồ sơ và theo dõi kết quả thông quan thực tế.",
        "who": "Chứng từ/hải quan hoặc đại lý đích theo phạm vi được giao.",
        "when": "Theo lịch đến và hạn làm thủ tục thực tế tại nước nhập.",
        "needs": "Chứng từ vận tải, invoice, packing list, C/O/giấy phép nếu có.",
        "done_when": "Có xác nhận thông quan nhập thực tế (customs_status=True).",
        "impact": "Chậm thông quan có thể phát sinh lưu bãi; D/O và các hold vẫn kiểm riêng."
    },
    "delivery": {
        "why": "Giao thực tế, POD và trả rỗng FCL là ba sự kiện riêng.",
        "what_to_do": "Giao hàng, ghi mốc giao thực tế; theo dõi D/O, POD, trả rỗng nếu thuộc scope.",
        "who": "Điều vận/giao nhận hoặc đại lý đích được phân công.",
        "when": "Khi đủ điều kiện giao theo tuyến và phạm vi dịch vụ.",
        "needs": "Điều kiện giao hàng, xe/đầu nhận và chứng từ bàn giao thực tế.",
        "done_when": "Mốc giao xong khi đã giao thật; POD/trả rỗng theo dõi riêng.",
        "impact": "Có POD trước khi ghi giao thực tế phải kiểm tra sai lệch."
    }
}

_LCL_SI_GUIDANCE: dict[str, str] = {
    "why": "LCL chỉ cần SI của lô; không đòi VGM container riêng của shipper.",
    "what_to_do": "Gửi SI cho bên gom hàng/đơn vị nhận SI và theo dõi chấp nhận.",
    "when": "Trước cutoff SI đã được bên nhận thông báo.",
    "needs": "Chi tiết lô và hướng dẫn SI của bên gom hàng.",
    "done_when": "SI có trạng thái ACCEPTED; không yêu cầu VGM riêng cho LCL.",
    "impact": "Chưa được chấp nhận SI có thể làm chậm chứng từ/hàng gom."
}


def guidance_for_node(
    node_id: str, *, load_model: str = "", owned: bool = False, completed: bool = False
) -> dict[str, str] | None:
    """Trả bản sao để chỉnh câu chữ theo FCL/LCL và quyền thực hiện; không ghi dữ liệu."""
    template = STAGE_GUIDANCE.get(node_id)
    if template is None:
        return None
    result = dict(template)
    if node_id == "si-vgm" and load_model == "LCL":
        result.update(_LCL_SI_GUIDANCE)
    # Mặt tiền Journey không được giao việc Trường Thành chưa nhận làm.
    if not owned:
        result["who"] = "Bên đảm trách thực tế; chưa xác nhận Trường Thành phụ trách."
        result["what_to_do"] = (
            "Theo dõi chứng cứ từ bên đảm trách; Trường Thành chưa xác nhận nhận việc này."
        )
    elif completed:
        result["what_to_do"] = (
            "Đã ghi nhận mốc giao; kiểm tra POD/trả rỗng riêng nếu thuộc trách nhiệm."
            if node_id == "delivery"
            else "Đã có bằng chứng mốc này; rà công việc liên quan còn mở nếu có."
        )
    return result
