// ============================================================================
// GENERATED FILE — DO NOT EDIT BY HAND.
//
// Source of truth: core/shipment_execution_profile.py::projection_options()
// Regenerate with:  python3 scripts/gen_execution_profile_catalog.py
//
// The component needs these matrices locally (it filters the Incoterm list on
// every keystroke); the payload below is byte-identical to the Python
// authority, and the Python test suite fails if this file drifts from it.
// ============================================================================

export const EXECUTION_PROFILE_CATALOG = {
  "versions": [
    {
      "code": "2020",
      "label": "Incoterms 2020"
    },
    {
      "code": "2010",
      "label": "Incoterms 2010"
    },
    {
      "code": "2000_LEGACY",
      "label": "Incoterms 2000 (legacy — DAF/DDU)"
    }
  ],
  "currentVersion": "2020",
  "newProfileCodes": {
    "": [
      "EXW",
      "FCA",
      "CPT",
      "CIP",
      "DAP",
      "DPU",
      "DDP",
      "FAS",
      "FOB",
      "CFR",
      "CIF"
    ],
    "ROAD": [
      "EXW",
      "FCA",
      "CPT",
      "CIP",
      "DAP",
      "DPU",
      "DDP"
    ],
    "SEA": [
      "EXW",
      "FCA",
      "CPT",
      "CIP",
      "DAP",
      "DPU",
      "DDP",
      "FAS",
      "FOB",
      "CFR",
      "CIF"
    ],
    "AIR": [
      "EXW",
      "FCA",
      "CPT",
      "CIP",
      "DAP",
      "DPU",
      "DDP"
    ],
    "RAIL": [
      "EXW",
      "FCA",
      "CPT",
      "CIP",
      "DAP",
      "DPU",
      "DDP"
    ]
  },
  "rules": {
    "2020": [
      {
        "code": "EXW",
        "scope": "ANY_MODE"
      },
      {
        "code": "FCA",
        "scope": "ANY_MODE"
      },
      {
        "code": "CPT",
        "scope": "ANY_MODE"
      },
      {
        "code": "CIP",
        "scope": "ANY_MODE"
      },
      {
        "code": "DAP",
        "scope": "ANY_MODE"
      },
      {
        "code": "DPU",
        "scope": "ANY_MODE"
      },
      {
        "code": "DDP",
        "scope": "ANY_MODE"
      },
      {
        "code": "FAS",
        "scope": "SEA_ONLY"
      },
      {
        "code": "FOB",
        "scope": "SEA_ONLY"
      },
      {
        "code": "CFR",
        "scope": "SEA_ONLY"
      },
      {
        "code": "CIF",
        "scope": "SEA_ONLY"
      }
    ],
    "2010": [
      {
        "code": "EXW",
        "scope": "ANY_MODE"
      },
      {
        "code": "FCA",
        "scope": "ANY_MODE"
      },
      {
        "code": "CPT",
        "scope": "ANY_MODE"
      },
      {
        "code": "CIP",
        "scope": "ANY_MODE"
      },
      {
        "code": "DAT",
        "scope": "ANY_MODE"
      },
      {
        "code": "DAP",
        "scope": "ANY_MODE"
      },
      {
        "code": "DDP",
        "scope": "ANY_MODE"
      },
      {
        "code": "FAS",
        "scope": "SEA_ONLY"
      },
      {
        "code": "FOB",
        "scope": "SEA_ONLY"
      },
      {
        "code": "CFR",
        "scope": "SEA_ONLY"
      },
      {
        "code": "CIF",
        "scope": "SEA_ONLY"
      }
    ],
    "2000_LEGACY": [
      {
        "code": "DAF",
        "scope": "ANY_MODE"
      },
      {
        "code": "DDU",
        "scope": "ANY_MODE"
      }
    ]
  },
  "codes": [
    "EXW",
    "FCA",
    "CPT",
    "CIP",
    "DAP",
    "DPU",
    "DDP",
    "FAS",
    "FOB",
    "CFR",
    "CIF",
    "DAT",
    "DAF",
    "DDU"
  ],
  "aliases": {
    "CNF": "CFR",
    "CANDF": "CFR",
    "CNFR": "CFR",
    "COSTANDFREIGHT": "CFR"
  },
  "modes": [
    {
      "code": "ROAD",
      "label": "Đường bộ",
      "stored": "Truck"
    },
    {
      "code": "SEA",
      "label": "Đường biển",
      "stored": "Sea"
    },
    {
      "code": "AIR",
      "label": "Hàng không",
      "stored": "Air"
    },
    {
      "code": "RAIL",
      "label": "Đường sắt",
      "stored": "Rail"
    }
  ],
  "loadModels": {
    "SEA": [
      {
        "code": "FCL",
        "label": "FCL — nguyên container"
      },
      {
        "code": "LCL",
        "label": "LCL — hàng lẻ / ghép container"
      },
      {
        "code": "OTHER",
        "label": "Khác / chưa xác định"
      }
    ],
    "ROAD": [
      {
        "code": "FTL",
        "label": "FTL — nguyên xe"
      },
      {
        "code": "LTL",
        "label": "LTL — hàng lẻ / ghép xe"
      }
    ],
    "AIR": [
      {
        "code": "DIRECT",
        "label": "Hàng nguyên / chuyến trực tiếp"
      },
      {
        "code": "CONSOLIDATED",
        "label": "Hàng lẻ / ghép lô"
      },
      {
        "code": "OTHER",
        "label": "Khác / chưa xác định"
      }
    ],
    "RAIL": []
  },
  "truckPresets": [
    {
      "code": "17.5m",
      "label": "17,5 m"
    },
    {
      "code": "13.5m",
      "label": "13,5 m"
    },
    {
      "code": "9.6m",
      "label": "9,6 m"
    },
    {
      "code": "6.8m",
      "label": "6,8 m"
    },
    {
      "code": "OTHER",
      "label": "Khác (tự nhập)"
    }
  ],
  "containerPresets": [
    {
      "code": "20GP",
      "label": "20' GP (khô)"
    },
    {
      "code": "40GP",
      "label": "40' GP (khô)"
    },
    {
      "code": "40HC",
      "label": "40' HC (cao)"
    },
    {
      "code": "OTHER",
      "label": "Khác (tự nhập)"
    }
  ],
  "serviceScope": [
    {
      "code": "ORIGIN_PICKUP",
      "label": "Lấy hàng tại kho / nhà máy",
      "short": "Lấy hàng"
    },
    {
      "code": "EXPORT_HANDLING",
      "label": "Xử lý hàng xuất (đóng gói, bãi, chứng từ)",
      "short": "Xử lý xuất"
    },
    {
      "code": "EXPORT_CUSTOMS",
      "label": "Khai báo hải quan xuất",
      "short": "HQ xuất"
    },
    {
      "code": "ORIGIN_TERMINAL_OR_BORDER",
      "label": "Giao hàng tại bãi / cửa khẩu đi",
      "short": "Cửa khẩu đi"
    },
    {
      "code": "MAIN_CARRIAGE",
      "label": "Thu xếp chặng chính (biển / bay / sắt / bộ)",
      "short": "Chặng chính"
    },
    {
      "code": "CROSS_BORDER_COORDINATION",
      "label": "Điều phối qua biên giới / chuyển tải",
      "short": "Qua biên giới"
    },
    {
      "code": "IMPORT_CUSTOMS",
      "label": "Khai báo hải quan nhập",
      "short": "HQ nhập"
    },
    {
      "code": "DESTINATION_TRUCKING",
      "label": "Vận chuyển nội địa đến điểm giao",
      "short": "Chạy nội địa"
    },
    {
      "code": "FINAL_DELIVERY",
      "label": "Giao hàng tận nơi",
      "short": "Giao hàng"
    },
    {
      "code": "CARGO_INSURANCE_ARRANGEMENT",
      "label": "Thu xếp bảo hiểm hàng hóa",
      "short": "Bảo hiểm"
    }
  ],
  "insuranceStatuses": [
    {
      "code": "UNKNOWN",
      "label": "Chưa xác nhận"
    },
    {
      "code": "YES",
      "label": "Đã có bảo hiểm"
    },
    {
      "code": "NO",
      "label": "Không có bảo hiểm"
    }
  ]
} as const;

export type ExecutionProfileCatalog = typeof EXECUTION_PROFILE_CATALOG;
