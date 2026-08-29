"""Fact-safe logistics sales enablement for human review."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .common import NEEDS_CUSTOMER_INPUT, READY_FOR_REVIEW, UNKNOWN, clone_mapping, is_present


OBJECTION_LIBRARY: dict[str, dict[str, Any]] = {
    "price_higher": {
        "customer_message": "Giá bên anh cao hơn.",
        "reply_draft": "Em hiểu băn khoăn của anh/chị. Mình cùng đối chiếu từng hạng mục, điều kiện giao nhận, chứng từ và các khoản chưa bao gồm để so sánh cùng phạm vi; nếu còn thiếu dữ liệu em sẽ cập nhật lại báo giá để anh/chị kiểm tra.",
        "sales_arguments": [
            "Giải thích theo từng service line và cost basis thay vì chỉ so tổng giá.",
            "Nêu rõ phần đã biết, phần ước tính và phần chưa có nguồn.",
        ],
        "assumptions": ["Phạm vi báo giá của hai bên có thể chưa giống nhau."],
        "next_action": "Xin báo giá đối chiếu và xác nhận cùng Incoterm, cargo, route và phạm vi dịch vụ.",
        "evidence_needed": ["báo giá đối chiếu", "phạm vi dịch vụ", "Incoterm và thông tin cargo"],
        "faq": "Báo giá cần được so sánh trên cùng phạm vi và cùng nguồn chi phí.",
        "service_differentiation": "Minh bạch từng dòng chi phí và nêu rõ exclusions/risk để người mua tự kiểm tra.",
    },
    "competitor_cheaper": {
        "customer_message": "Bên khác báo rẻ hơn.",
        "reply_draft": "Anh/chị gửi giúp em phạm vi và các điều kiện của báo giá bên kia. Em sẽ so sánh các hạng mục, điều kiện thanh toán, chứng từ, điểm nhận/giao và phần loại trừ; mình không nên kết luận chỉ từ một con số tổng.",
        "sales_arguments": [
            "Đối chiếu apples-to-apples theo route, cargo, Incoterm và service lines.",
            "Tách fact có nguồn khỏi phần cần xác nhận trước khi chốt.",
        ],
        "assumptions": ["Chưa có bản báo giá đối thủ để xác định phạm vi tương đương."],
        "next_action": "Nhận bản chụp hoặc bảng hạng mục đối chiếu rồi chuyển sales owner review.",
        "evidence_needed": ["báo giá đối thủ", "điều kiện giao nhận", "exclusions và validity"],
        "faq": "Giá thấp hơn có thể đang bao gồm phạm vi hoặc điều kiện khác; cần tài liệu đối chiếu.",
        "service_differentiation": "Handoff có cấu trúc giữa sales, China agent, factory và operations.",
    },
    "delivery_time": {
        "customer_message": "Bao lâu hàng về?",
        "reply_draft": "Em sẽ kiểm tra cargo-ready date, điểm lấy hàng, route, điều kiện biên và lịch vận hành hiện tại rồi gửi khoảng thời gian dự kiến kèm điều kiện áp dụng. Hiện em chưa thể xác nhận một mốc chắc chắn khi chưa đủ các dữ liệu đó.",
        "sales_arguments": [
            "Thời gian cần gắn với cargo-ready date, route và tình trạng vận hành được cập nhật.",
            "Mọi mốc gửi khách phải ghi rõ là dự kiến và nguồn kiểm tra.",
        ],
        "assumptions": ["Chưa có đủ dữ liệu route, cargo-ready date và border condition."],
        "next_action": "Xin cargo-ready date, pickup, destination và yêu cầu giao hàng để operations kiểm tra.",
        "evidence_needed": ["cargo-ready date", "route/pickup", "current operations or border source"],
        "faq": "Thời gian giao là dự kiến theo dữ liệu tại thời điểm kiểm tra và có thể chịu ảnh hưởng vận hành.",
        "service_differentiation": "Theo dõi điều kiện và cập nhật lại khi nguồn vận hành thay đổi.",
    },
    "customs_clearance": {
        "customer_message": "Có chắc thông quan được không?",
        "reply_draft": "Em sẽ rà soát loại hàng, chứng từ, importer và yêu cầu hiện hành với bộ phận phụ trách. Trước khi có hồ sơ và đánh giá có thẩm quyền, em không thể khẳng định kết quả thông quan; em sẽ nêu rõ điều kiện và rủi ro cần xử lý.",
        "sales_arguments": [
            "Bắt đầu bằng kiểm tra hồ sơ và điều kiện, không biến tư vấn bán hàng thành kết luận pháp lý.",
            "Nêu rõ phần cần customs/compliance review.",
        ],
        "assumptions": ["Kết quả thông quan chưa được cơ quan hoặc chuyên gia có thẩm quyền xác nhận."],
        "next_action": "Thu thập mô tả hàng, invoice/packing list, importer và hồ sơ liên quan để review.",
        "evidence_needed": ["goods description", "invoice/packing list", "importer and current rule source"],
        "faq": "Có thể hỗ trợ điều phối hồ sơ, nhưng không tự động bảo đảm kết quả thông quan.",
        "service_differentiation": "Tách hồ sơ, nguồn quy định và quyết định có thẩm quyền trong handoff.",
    },
    "delay": {
        "customer_message": "Nếu hàng bị chậm thì sao?",
        "reply_draft": "Nếu có dấu hiệu chậm, sales sẽ chuyển thông tin cho operations để xác định nguyên nhân, cập nhật trạng thái và thống nhất bước xử lý theo phạm vi dịch vụ. Em cần giữ lại nguồn cập nhật và điều kiện báo giá; hiện chưa thể hứa một kết quả bù trừ hay mốc mới khi chưa xem hợp đồng.",
        "sales_arguments": [
            "Có quy trình escalation và handoff theo nguồn trạng thái.",
            "Không biến kế hoạch xử lý thành cam kết bồi thường hoặc thời gian mới nếu chưa có điều khoản.",
        ],
        "assumptions": ["Điều khoản trách nhiệm/chậm giao của từng lô chưa được kiểm tra."],
        "next_action": "Xác nhận lô hàng, mốc trạng thái cuối và điều khoản dịch vụ để operations review.",
        "evidence_needed": ["shipment status source", "service scope", "applicable contract terms"],
        "faq": "Cách xử lý phụ thuộc nguyên nhân, nguồn trạng thái và điều khoản đã thỏa thuận.",
        "service_differentiation": "Escalation có ghi nhận nguồn, người phụ trách và bước tiếp theo.",
    },
    "why_information": {
        "customer_message": "Tại sao cần cung cấp nhiều thông tin như vậy?",
        "reply_draft": "Các thông tin về cargo, pickup, Incoterm, importer và chứng từ giúp tách đúng phạm vi dịch vụ và nhận diện dữ liệu còn thiếu. Nếu chưa có thông tin nào, em sẽ ghi là UNKNOWN/NEEDS_CUSTOMER_INPUT thay vì tự đoán làm sai báo giá hoặc hồ sơ.",
        "sales_arguments": [
            "Mỗi trường giúp kiểm tra một phần của cost, route hoặc document scope.",
            "Thu thập tối thiểu cần thiết và giải thích rõ mục đích sử dụng.",
        ],
        "assumptions": ["Thông tin khách cung cấp vẫn cần được xác nhận theo nguồn phù hợp."],
        "next_action": "Gửi checklist tối thiểu và đánh dấu trường nào bắt buộc cho bước quote hiện tại.",
        "evidence_needed": ["intake checklist", "cargo/factory details", "commercial requirements"],
        "faq": "Thiếu dữ liệu không phải là quyền tự động ước lượng; checklist giúp tránh sai phạm vi.",
        "service_differentiation": "Intake có cấu trúc và hiển thị missing information thay vì che khuất bất định.",
    },
    "factory_rmb": {
        "customer_message": "Factory chỉ nhận RMB.",
        "reply_draft": "Mình có thể lập một kịch bản tính RMB nếu có xác nhận flow China-side được ủy quyền, tỷ giá có thời điểm/nguồn và các khoản phí có nguồn. Kết quả chỉ là phép tính để review; em chưa thể coi đó là lệnh chuyển tiền hay xác nhận pháp lý.",
        "sales_arguments": [
            "Tách source USD, transfer/intermediary fee, tỷ giá và RMB nhận được thành từng bước.",
            "Dừng lại để review nếu chứng từ hoặc giá trị thương mại không nhất quán.",
        ],
        "assumptions": ["Flow thanh toán China-side và người nhận cần được xác nhận bằng tài liệu phù hợp."],
        "next_action": "Xin xác nhận flow được ủy quyền, currency, timestamped FX và fee sources để payment review.",
        "evidence_needed": ["authorized flow confirmation", "FX source/timestamp", "fee source", "commercial documents"],
        "faq": "RMB receipt scenario chỉ tính theo input được cung cấp và không tự thực hiện thanh toán.",
        "service_differentiation": "Calculation trace cho từng input/rate/fee/intermediate/final amount.",
    },
    "not_ready": {
        "customer_message": "Tôi chưa muốn quyết định.",
        "reply_draft": "Không sao ạ. Em có thể giữ lại checklist các điểm cần xác nhận, phần đã biết và phần còn thiếu để anh/chị xem khi thuận tiện. Khi có cargo-ready date hoặc thay đổi về phạm vi, mình cập nhật lại validity và nguồn chi phí trước khi quyết định.",
        "sales_arguments": [
            "Cho khách một next action nhỏ, có thể trì hoãn, thay vì gây áp lực chốt.",
            "Nhắc kiểm tra lại các dữ liệu động trước khi dùng báo giá.",
        ],
        "assumptions": ["Chưa có quyết định mua hoặc chấp nhận báo giá."],
        "next_action": "Hẹn ngày follow-up do khách chọn hoặc gửi checklist review không yêu cầu cam kết.",
        "evidence_needed": ["customer-selected follow-up date", "current quote validity when revisited"],
        "faq": "Báo giá vẫn cần được kiểm tra lại nếu dữ liệu động hoặc yêu cầu shipment thay đổi.",
        "service_differentiation": "Follow-up có next action rõ và không tự động gửi thông điệp.",
    },
}


def _fact_records(verified_facts: Mapping[str, Any] | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    facts: list[dict[str, Any]] = []
    assumptions: list[dict[str, Any]] = []
    if not isinstance(verified_facts, Mapping):
        return facts, assumptions
    for key, raw in verified_facts.items():
        if isinstance(raw, Mapping) and raw.get("verified") is True and is_present(raw.get("source")):
            facts.append(
                {
                    "key": key,
                    "value": raw.get("value", UNKNOWN),
                    "source": raw["source"],
                    "classification": "FACT",
                }
            )
        else:
            assumptions.append(
                {
                    "key": key,
                    "value": raw.get("value", UNKNOWN) if isinstance(raw, Mapping) else raw,
                    "classification": "ASSUMPTION",
                    "reason": "verification flag and source are both required",
                }
            )
    return facts, assumptions


def build_sales_response(
    objection_key: str | None, verified_facts: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Return a structured, human-review-only response for one objection."""

    case = OBJECTION_LIBRARY.get(str(objection_key)) if objection_key is not None else None
    if case is None:
        return {
            "status": NEEDS_CUSTOMER_INPUT,
            "objection_key": objection_key if objection_key is not None else UNKNOWN,
            "reply_draft": None,
            "missing_information": ["known objection key"],
            "can_send": False,
            "human_review_required": True,
            "authority": {"autonomous_messaging": False},
        }

    facts, supplied_assumptions = _fact_records(verified_facts)
    assumptions = supplied_assumptions + [
        {"text": text, "classification": "ASSUMPTION"} for text in case["assumptions"]
    ]
    sales_arguments = [
        {"text": text, "classification": "SALES_ARGUMENT"} for text in case["sales_arguments"]
    ]
    return {
        "status": READY_FOR_REVIEW,
        "objection_key": objection_key,
        "customer_message": case["customer_message"],
        "reply_draft": case["reply_draft"],
        "content_layers": {
            "facts": facts,
            "sales_arguments": sales_arguments,
            "assumptions": assumptions,
        },
        "quotation_explanation": case["faq"],
        "customer_follow_up": {
            "draft": case["reply_draft"],
            "human_review_required": True,
            "autonomous_send": False,
        },
        "objection_handling": {
            "customer_message": case["customer_message"],
            "reply": case["reply_draft"],
        },
        "faq": case["faq"],
        "sales_handoff": {
            "status": "HUMAN_REVIEW_REQUIRED",
            "owner": "sales_owner",
            "evidence_needed": case["evidence_needed"],
        },
        "service_differentiation": case["service_differentiation"],
        "next_action": case["next_action"],
        "evidence_needed": case["evidence_needed"],
        "can_send": False,
        "human_review_required": True,
        "authority": {
            "autonomous_messaging": False,
            "customs_clearance_promised": False,
            "delivery_time_promised": False,
            "tax_treatment_promised": False,
            "facts_require_source_and_verification": True,
        },
    }
