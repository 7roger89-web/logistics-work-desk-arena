"""Bounded publication negative tests; no network or production database."""
import json
import unittest
from core.hexa_customer_publication import (build_customer_publication, authorize_document_download,
                                            PublicationDenied)

SENTINELS = ["TT_INTERNAL_COST_8451", "TT_PRIVATE_SUPPLIER_323",
             "TT_MARGIN_818", "FOREIGN_CUSTOMER_912", "TT_HIDDEN_ETA_773"]


def sample():
    principal = {"authenticated": True, "kind": "customer", "customer_id": "LG"}
    shipment = {"id": "ROAD-001", "customer_id": "LG", "transport_mode": "ROAD",
                "quote_id": "Q001", "internal_cost": SENTINELS[0],
                "supplier": SENTINELS[1], "margin": SENTINELS[2],
                "status": "COMPLETED", "eta": SENTINELS[4]}
    publication = {"state": "PUBLISHED", "customer_id": "LG", "shipment_id": "ROAD-001",
                   "approved_by": "tt-operator", "approved_at": "2026-10-22T10:00:00Z",
                   "event_versions": {"E1": "v1", "E2": "v2"},
                   "document_versions": {"D1": "v2", "D2": "v1", "D3": "v1"},
                   "quote": {"id": "Q001", "version": "3"}}
    events = [
        {"id": "E1", "version": "v1", "customer_id": "LG", "shipment_id": "ROAD-001",
         "verified": True, "verified_at": "now", "occurred_at": "2026-10-20T12:00:00Z",
         "visibility": "CUSTOMER", "public_title": "Đã lấy hàng", "stage_id": "pickup",
         "private_notes": SENTINELS[0]},
        {"id": "E2", "version": "v2", "customer_id": "LG", "shipment_id": "ROAD-001",
         "verified": False, "verified_at": "", "occurred_at": "2026-10-22T12:00:00Z",
         "visibility": "CUSTOMER", "public_title": "Chưa xác minh", "stage_id": "delivery"},
        {"id": "E3", "version": "v1", "customer_id": "LG", "shipment_id": "ROAD-001",
         "verified": True, "verified_at": "now", "occurred_at": "2026-10-23T12:00:00Z",
         "visibility": "TT", "public_title": SENTINELS[4], "stage_id": "delivery"},
        {"id": "E4", "version": "v1", "customer_id": "OTHER", "shipment_id": "ROAD-001",
         "verified": True, "verified_at": "now", "occurred_at": "2026-10-22T12:00:00Z",
         "visibility": "CUSTOMER", "public_title": SENTINELS[3], "stage_id": "pickup"},
    ]
    documents = [
        {"id": "D1", "version": "v2", "customer_id": "LG", "shipment_id": "ROAD-001",
         "kind": "PL", "status": "AVAILABLE", "visibility": "CUSTOMER", "verified": True,
         "public_title": "Packing List v2", "raw_gridfs_id": SENTINELS[0]},
        {"id": "D2", "version": "v1", "customer_id": "LG", "shipment_id": "ROAD-001",
         "kind": "COST", "status": "AVAILABLE", "visibility": "CUSTOMER", "verified": True,
         "public_title": SENTINELS[1]},
        {"id": "D3", "version": "v1", "customer_id": "OTHER", "shipment_id": "ROAD-001",
         "kind": "PL", "status": "AVAILABLE", "visibility": "CUSTOMER", "verified": True,
         "public_title": SENTINELS[3]},
    ]
    quote = {"id": "Q001", "version": 3, "customer_id": "LG", "status": "SENT",
             "calculation": {"selling_price_total_vnd": 7500000, "buy_total": SENTINELS[0]},
             "margin": SENTINELS[2], "supplier": SENTINELS[1],
             "excel_quote": {"goods": [{"internal": SENTINELS[0]}]}}
    return dict(principal=principal, shipment=shipment, publication=publication,
                events=events, documents=documents, quote=quote)


class PublicationTests(unittest.TestCase):
    def test_known_good_and_secrets(self):
        a = sample(); r = build_customer_publication(**a)
        self.assertEqual(r["reference"], "ROAD-001")
        self.assertEqual([e["id"] for e in r["timeline"]], ["E1"])
        self.assertEqual([d["id"] for d in r["documents"]], ["D1"])
        self.assertEqual(r["quote"]["selling_total_vnd"], 7500000)
        self.assertFalse(any(s in json.dumps(r) for s in SENTINELS))
        self.assertNotIn("customer_id", r)
        self.assertFalse(any("url" in k for d in r["documents"] for k in d))

    def test_foreign_customer_denied(self):
        a = sample(); a["principal"]["customer_id"] = "OTHER"
        with self.assertRaises(PublicationDenied): build_customer_publication(**a)

    def test_guessed_shipment_denied(self):
        a = sample(); a["publication"]["shipment_id"] = "OTHER-SHIPMENT"
        with self.assertRaises(PublicationDenied): build_customer_publication(**a)

    def test_customer_cannot_be_internal_viewer(self):
        a = sample(); a["principal"]["kind"] = "viewer"
        with self.assertRaises(PublicationDenied): build_customer_publication(**a)

    def test_anonymous_denied(self):
        a = sample(); a["principal"]["authenticated"] = False
        with self.assertRaises(PublicationDenied): build_customer_publication(**a)

    def test_manifest_requires_tt_approval(self):
        a = sample(); a["publication"]["approved_by"] = ""
        with self.assertRaises(PublicationDenied): build_customer_publication(**a)

    def test_manifest_not_published_denied(self):
        a = sample(); a["publication"]["state"] = "DRAFT"
        with self.assertRaises(PublicationDenied): build_customer_publication(**a)

    def test_unpublished_event_stays_hidden(self):
        a = sample(); a["publication"]["event_versions"] = {}
        self.assertEqual(build_customer_publication(**a)["timeline"], [])

    def test_unverified_event_stays_hidden(self):
        a = sample(); a["events"][0]["verified"] = False
        self.assertEqual(build_customer_publication(**a)["timeline"], [])

    def test_document_version_stale(self):
        a = sample(); a["documents"][0]["version"] = "v3"
        self.assertEqual(build_customer_publication(**a)["documents"], [])
        with self.assertRaises(PublicationDenied):
            authorize_document_download(shipment=a["shipment"], principal=a["principal"],
                                        publication=a["publication"], document=a["documents"][0],
                                        requested_id="D1", requested_version="v2")

    def test_document_download_requires_exact_version(self):
        a = sample(); args={k:a[k] for k in ("shipment", "principal", "publication")}
        authorize_document_download(**args, document=a["documents"][0], requested_id="D1", requested_version="v2")
        with self.assertRaises(PublicationDenied):
            authorize_document_download(**args, document=a["documents"][0], requested_id="D1", requested_version="v1")

    def test_foreign_document_download_denied(self):
        a = sample(); args={k:a[k] for k in ("shipment", "principal", "publication")}
        with self.assertRaises(PublicationDenied):
            authorize_document_download(**args, document=a["documents"][2], requested_id="D3", requested_version="v1")

    def test_internal_cost_doc_denied_even_if_release_listed(self):
        a = sample(); args={k:a[k] for k in ("shipment", "principal", "publication")}
        with self.assertRaises(PublicationDenied):
            authorize_document_download(**args, document=a["documents"][1], requested_id="D2", requested_version="v1")

    def test_unsent_quote_hidden(self):
        a = sample(); a["quote"]["status"] = "DRAFT"
        self.assertIsNone(build_customer_publication(**a)["quote"])

    def test_quote_wrong_version_hidden(self):
        a = sample(); a["publication"]["quote"]["version"] = "2"
        self.assertIsNone(build_customer_publication(**a)["quote"])

    def test_quote_other_tenant_hidden(self):
        a = sample(); a["quote"]["customer_id"] = "OTHER"
        self.assertIsNone(build_customer_publication(**a)["quote"])

    def test_missing_price_stays_unknown(self):
        a = sample(); a["quote"]["calculation"]["selling_price_total_vnd"] = None
        self.assertIsNone(build_customer_publication(**a)["quote"]["selling_total_vnd"])

    def test_negative_price_stays_unknown(self):
        a = sample(); a["quote"]["calculation"]["selling_price_total_vnd"] = -300
        self.assertIsNone(build_customer_publication(**a)["quote"]["selling_total_vnd"])

    def test_no_internal_stage_status_leak(self):
        a = sample(); r=build_customer_publication(**a)
        self.assertNotIn("COMPLETED", json.dumps(r))
        self.assertNotIn("eta", json.dumps(r).lower())


if __name__ == "__main__":
    unittest.main()
