"""Comprehensive unit and integration tests for donor_app navigation architecture."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from donor_app import store, shell, ui, pages_core, pages_more, pages_finance, home_page

LAUNCHER_PATH = str((Path(__file__).parent.parent / "donor_launcher.py").resolve())


def test_store_session_state_defaults_and_setters():
    """Verify session state defaults, getters, setters, and persistence without reset."""
    store.init_session_state()
    
    assert store.get_active_page() == "home"
    assert store.get_active_route() == "/"
    assert store.get_shipment_id() == "LO-0306"
    assert store.get_contract_id() == "HDMB-PA-2026-031"
    assert store.get_active_tab() == "lay-hang"
    assert store.get_active_contract_tab() == "hang-hoa"
    
    # Update active page and verify persistence
    store.set_active_page("shipments", route="/lo-hang")
    assert store.get_active_page() == "shipments"
    assert store.get_active_route() == "/lo-hang"
    
    # Update active shipment and tab
    store.set_shipment_id("LO-0307", tab="tai-chinh")
    assert store.get_shipment_id() == "LO-0307"
    assert store.get_active_tab() == "tai-chinh"
    
    # Update active contract and tab
    store.set_contract_id("HDMB-PA-2026-032", tab="thong-tin")
    assert store.get_contract_id() == "HDMB-PA-2026-032"
    assert store.get_active_contract_tab() == "thong-tin"


def test_shell_route_mapping_coverage():
    """Verify all 18 sidebar routes and common aliases resolve to valid page keys."""
    routes_to_test = [
        ("/", "home"),
        ("/home", "home"),
        ("/trang-chu", "home"),
        ("/viec-can-xu-ly", "tasks"),
        ("/lo-hang", "shipments"),
        ("/lo-hang-detail", "shipment_detail"),
        ("/tao-lo-moi", "new_shipment"),
        ("/khach-hang", "customers"),
        ("/kinh-doanh-bao-gia", "quotes"),
        ("/thoa-thuan-ban-giao", "agreements"),
        ("/hop-dong", "contracts"),
        ("/hop-dong-detail", "contract_detail"),
        ("/hop-dong/moi", "new_contract"),
        ("/tai-chinh/thu-tien", "collect"),
        ("/tai-chinh/doi-soat", "reconcile"),
        ("/tai-chinh/cong-no-doi-tac", "partner_debt"),
        ("/bao-cao-ceo", "ceo"),
        ("/cong-cu/hs", "hs_lookup"),
        ("/tra-cuu-thue", "hs_lookup"),
        ("/cong-cu/so-tay", "handbook"),
        ("/so-tay", "handbook"),
        ("/cong-cu/dich-thuat", "translate"),
        ("/dich-thuat", "translate"),
        ("/theo-doi", "tracking"),
        ("/ngu-canh-doi-tac", "partner_context"),
        ("/admin/users", "users"),
        ("/nguoi-dung", "users"),
    ]
    
    for route, expected_page in routes_to_test:
        page_key = shell.PAGE_ROUTES.get(route)
        assert page_key == expected_page, f"Route {route} expected {expected_page}, got {page_key}"


def test_all_pages_render_without_exception():
    """Verify every single route page in PAGE_ROUTES mounts and renders without errors."""
    for route in set(shell.PAGE_ROUTES.keys()):
        at = AppTest.from_file(LAUNCHER_PATH, default_timeout=30)
        at.query_params["p"] = route
        at.run()
        assert not at.exception, f"Failed rendering route: {route}"
        assert len(at.markdown) > 0, f"No markdown produced for route: {route}"


def test_shipment_detail_all_five_tabs():
    """Verify all 5 tabs of ShipmentDetail render completely."""
    tabs = ["lay-hang", "nhap", "tai-chinh", "chung-tu", "lich-su"]
    for tab in tabs:
        at = AppTest.from_file(LAUNCHER_PATH, default_timeout=30)
        at.query_params["p"] = "/lo-hang-detail"
        at.query_params["id"] = "LO-0306"
        at.query_params["tab"] = tab
        at.run()
        assert not at.exception, f"Failed rendering shipment tab: {tab}"
        assert any("LO-0306" in m.value for m in at.markdown)


def test_contract_detail_all_five_tabs():
    """Verify all 5 tabs of ContractDetail render completely."""
    tabs = ["thong-tin", "hang-hoa", "lo-lien-ket", "tai-chinh", "lich-su"]
    for tab in tabs:
        at = AppTest.from_file(LAUNCHER_PATH, default_timeout=30)
        at.query_params["p"] = "/hop-dong-detail"
        at.query_params["id"] = "HDMB-PA-2026-031"
        at.query_params["tab"] = tab
        at.run()
        assert not at.exception, f"Failed rendering contract tab: {tab}"
        assert any("HDMB-PA-2026-031" in m.value for m in at.markdown)


def test_action_dispatchers():
    """Verify action dispatchers like search dropdown, quick add, notifications, and pay dialog."""
    at = AppTest.from_file(LAUNCHER_PATH, default_timeout=30)
    
    # Open Quick Add Sheet
    at.query_params["action"] = "open_quick_add"
    at.run()
    assert not at.exception
    assert at.session_state["donor_quick_add"] is True

    # Close Quick Add Sheet
    at.query_params["action"] = "close_quick_add"
    at.run()
    assert not at.exception
    assert at.session_state["donor_quick_add"] is False

    # Open Notification Drawer
    at.query_params["action"] = "notif_drawer"
    at.run()
    assert not at.exception
    assert at.session_state["donor_notif_open"] is True

    # Close Notification Drawer
    at.query_params["action"] = "close_notif"
    at.run()
    assert not at.exception
    assert at.session_state["donor_notif_open"] is False

    # Open Search Dropdown
    at.query_params["action"] = "search_dropdown"
    at.run()
    assert not at.exception
    assert at.session_state["donor_search_open"] is True

    # Open Pay Dialog
    at.query_params["action"] = "pay_dialog"
    at.query_params["sid"] = "LO-0306"
    at.run()
    assert not at.exception
    assert at.session_state["pay_dialog_open"] is True
    assert at.session_state["pay_sid"] == "LO-0306"

    # Role toggle
    at.query_params["action"] = "set_role"
    at.query_params["role"] = "SUPPORT"
    at.run()
    assert not at.exception
    assert at.session_state["donor_role"] == "SUPPORT"


def test_rerun_preserves_page_without_query_params():
    """Verify that when query params are absent on subsequent reruns, active_page does NOT reset to home."""
    at = AppTest.from_file(LAUNCHER_PATH, default_timeout=30)
    # First navigate to quotes
    at.query_params["p"] = "/kinh-doanh-bao-gia"
    at.run()
    assert not at.exception
    assert at.session_state["active_page"] == "quotes"

    # Clear query params and rerun
    at.query_params.clear()
    at.run()
    assert not at.exception
    # Page must still be quotes, not reset to home!
    assert at.session_state["active_page"] == "quotes"


def test_no_broken_postmessage_bridges_in_codebase():
    """Verify that no broken window.parent.postMessage or _install_goto_bridge remains in donor_app."""
    import inspect
    import donor_app.shell
    import donor_app.ui
    import donor_app.pages_core
    import donor_app.pages_more
    import donor_app.pages_finance

    for module in [donor_app.shell, donor_app.ui, donor_app.pages_core, donor_app.pages_more, donor_app.pages_finance]:
        source = inspect.getsource(module)
        assert "_install_goto_bridge" not in source, f"Found _install_goto_bridge in {module.__name__}"
        assert "postMessage" not in source, f"Found postMessage in {module.__name__}"
