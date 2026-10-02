# Ten sample rows from each base table

Each section contains the literal read-only command and output captured from FEVM.

## dim_product

```console
$ databricks experimental aitools tools query "SELECT * FROM nikks_fevm_workspace_7405607030687545.techsummit.dim_product LIMIT 10" -p FEVM
[
  {
    "category": "Powerful cordless combi drill with hammer function for masonry.",
    "name": "GSB 18V-90 C",
    "price_eur": "249.0",
    "product_id": "06f80d3f-2c18-5d0f-876b-d95f03eee4cc"
  },
  {
    "category": "18V cordless impact drill with two-speed gearbox.",
    "name": "PSB 1800 LI-2",
    "price_eur": "139.0",
    "product_id": "0895d282-3f1c-5c38-b465-25f70a5a4419"
  },
  {
    "category": "Entry-level 700W angle grinder with 115mm disc.",
    "name": "PWS 700-115",
    "price_eur": "59.0",
    "product_id": "1b7fb3fe-fcc0-5d5a-bcd2-160cf14763ce"
  },
  {
    "category": "Cordless 18V drill/driver with brushless motor for everyday tasks.",
    "name": "GSR 18V-55",
    "price_eur": "189.0",
    "product_id": "30adc6e1-f618-557e-8e36-391eec224083"
  },
  {
    "category": "Brushless cordless rotary hammer with SDS-plus quick-change.",
    "name": "GBH 18V-26 F",
    "price_eur": "379.0",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d"
  },
  {
    "category": "Lightweight 10.8V drill driver for home DIY projects.",
    "name": "PSR 1080 LI",
    "price_eur": "79.0",
    "product_id": "5bbcd7cd-2271-52cb-9327-6ae3897f2401"
  },
  {
    "category": "Compact 12V cordless drill/driver for tight workspaces.",
    "name": "GSR 12V-35",
    "price_eur": "129.0",
    "product_id": "9a3adcc6-eb63-523d-9c63-561ed62922ca"
  },
  {
    "category": "Brushless 125mm cordless angle grinder with anti-kickback.",
    "name": "GWS 18V-10",
    "price_eur": "199.0",
    "product_id": "9e78bc6f-3ec5-5e97-9cc1-14b91ed47f73"
  },
  {
    "category": "Heavy-duty 2200W angle grinder with 230mm disc.",
    "name": "GWS 22-230 JH",
    "price_eur": "189.0",
    "product_id": "ae063860-45ae-5d05-b070-ebbe7072d0ae"
  },
  {
    "category": "Compact corded rotary hammer for occasional masonry work.",
    "name": "PBH 2100 RE",
    "price_eur": "99.0",
    "product_id": "cc8a934a-9b64-5ce8-8736-ad5999614b51"
  }
]
```

## dim_customer

```console
$ databricks experimental aitools tools query "SELECT * FROM nikks_fevm_workspace_7405607030687545.techsummit.dim_customer LIMIT 10" -p FEVM
[
  {
    "city": "Gerlingen",
    "country": "Germany",
    "customer_id": "00000000-0000-0000-0000-000000000001",
    "signup_date": ""
  },
  {
    "city": "Stuttgart",
    "country": "Netherlands",
    "customer_id": "1f8c6991-78ad-423a-ad46-921e5229bd9d",
    "signup_date": ""
  },
  {
    "city": "Munich",
    "country": "Germany",
    "customer_id": "26fca1ed-57ce-5911-82a6-f2f604e27428",
    "signup_date": ""
  },
  {
    "city": "Cologne",
    "country": "Germany",
    "customer_id": "449b6a60-08fd-5042-ac0b-ff9113504eb1",
    "signup_date": ""
  },
  {
    "city": "Frankfurt",
    "country": "Germany",
    "customer_id": "510bf637-ab36-5eb2-8744-126aac1cf1b6",
    "signup_date": ""
  },
  {
    "city": "Zurich",
    "country": "Switzerland",
    "customer_id": "85f36055-1d35-5fc4-831c-99fe72e20bfe",
    "signup_date": ""
  },
  {
    "city": "Vienna",
    "country": "Austria",
    "customer_id": "8ded1555-7699-5519-a121-5f0207f2819b",
    "signup_date": ""
  },
  {
    "city": "Graz",
    "country": "Austria",
    "customer_id": "accff6f3-73da-5fc8-a5bd-8d44754394c5",
    "signup_date": ""
  },
  {
    "city": "Amsterdam",
    "country": "Netherlands",
    "customer_id": "ae71ea9f-560e-56ca-8449-4ed19bd762b3",
    "signup_date": ""
  },
  {
    "city": "Berlin",
    "country": "Germany",
    "customer_id": "bdc27dc0-100d-5f38-9a0a-1eaae4169d9d",
    "signup_date": ""
  }
]
```

## fact_purchase

```console
$ databricks experimental aitools tools query "SELECT * FROM nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase LIMIT 10" -p FEVM
[
  {
    "cart_id": "866b7005-dbce-568a-b2ae-e9d322464010",
    "created_at": "2026-07-23T21:05:26.024Z",
    "customer_id": "accff6f3-73da-5fc8-a5bd-8d44754394c5",
    "purchase_id": "09efd3ca-5146-5ab4-8427-3933d8cb045a",
    "total_eur": "758.0"
  },
  {
    "cart_id": "15a6ce25-6ecd-5483-9674-2d02c90594ea",
    "created_at": "2026-08-17T13:05:26.024Z",
    "customer_id": "8ded1555-7699-5519-a121-5f0207f2819b",
    "purchase_id": "1310a208-2dd2-5e3c-9c34-22f8924e79a2",
    "total_eur": "189.0"
  },
  {
    "cart_id": "5281fe0d-939a-5f75-a4b6-832f39b57c34",
    "created_at": "2026-07-14T03:05:26.024Z",
    "customer_id": "510bf637-ab36-5eb2-8744-126aac1cf1b6",
    "purchase_id": "294c3346-4f9c-57e6-9407-c2b4f7f0cdd3",
    "total_eur": "896.0"
  },
  {
    "cart_id": "3c709874-0aa8-5970-9808-74db142e7d6d",
    "created_at": "2026-07-22T04:05:26.024Z",
    "customer_id": "d7afa5b2-258b-5c84-bc45-1b69180dcf97",
    "purchase_id": "32d3c0be-d59d-505b-8b4a-61c4df3fa385",
    "total_eur": "587.0"
  },
  {
    "cart_id": "1b3455a1-8621-5df9-bb85-cf24ba40667c",
    "created_at": "2026-08-03T14:05:26.024Z",
    "customer_id": "d10038b3-f3d6-584c-bd24-1ba8060d37d8",
    "purchase_id": "356ee000-07a6-5365-9d56-1be7cbef07bd",
    "total_eur": "118.0"
  },
  {
    "cart_id": "df5a9100-e310-5e26-9556-4f40817ef30a",
    "created_at": "2026-07-27T08:05:26.024Z",
    "customer_id": "00000000-0000-0000-0000-000000000001",
    "purchase_id": "5716e432-2701-543c-93e8-3b425788ff90",
    "total_eur": "627.0"
  },
  {
    "cart_id": "31e10a0f-72c0-50d9-88bd-9b00b35dda5c",
    "created_at": "2026-08-17T09:05:26.024Z",
    "customer_id": "26fca1ed-57ce-5911-82a6-f2f604e27428",
    "purchase_id": "90561597-40fd-54fb-a3b8-d590c80d541f",
    "total_eur": "438.0"
  },
  {
    "cart_id": "f6ed92f4-d342-5a54-b8ed-50d7ef7a2f01",
    "created_at": "2026-08-06T20:05:26.024Z",
    "customer_id": "bdc27dc0-100d-5f38-9a0a-1eaae4169d9d",
    "purchase_id": "955e4221-5b69-5e6c-aedf-6d22a1e12619",
    "total_eur": "947.0"
  },
  {
    "cart_id": "905fa076-8262-5157-91fe-f4c5ffb5dd0e",
    "created_at": "2026-07-29T10:05:26.024Z",
    "customer_id": "1f8c6991-78ad-423a-ad46-921e5229bd9d",
    "purchase_id": "a458a6d0-8936-5528-be6c-33ef4539a52d",
    "total_eur": "577.0"
  },
  {
    "cart_id": "ceeea8b0-9090-484f-9cf0-f5932b92da7c",
    "created_at": "2026-08-21T19:52:34.792Z",
    "customer_id": "d7afa5b2-258b-5c84-bc45-1b69180dcf97",
    "purchase_id": "d36067d0-f65a-475c-b392-640b72bae478",
    "total_eur": "379.0"
  }
]
```

## fact_purchase_line

```console
$ databricks experimental aitools tools query "SELECT * FROM nikks_fevm_workspace_7405607030687545.techsummit.fact_purchase_line LIMIT 10" -p FEVM
[
  {
    "name_snapshot": "GST 18V-LI S",
    "product_id": "e5b18e53-b97b-5d22-95e7-6cb691bf3f48",
    "purchase_id": "44e6b020-ede4-4ae8-a5ea-7b825a799cd6",
    "purchase_line_id": "9698e8b9-5a3e-47aa-a7f3-d10cfb2802ba",
    "quantity": "2",
    "unit_price_eur": "169.0"
  },
  {
    "name_snapshot": "GBH 18V-26 F",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "purchase_id": "1fed5208-527f-410b-b071-3f03bd48a603",
    "purchase_line_id": "23c2f94e-efa5-431e-8fc9-4c1a3305572e",
    "quantity": "1",
    "unit_price_eur": "379.0"
  },
  {
    "name_snapshot": "GBH 18V-26 F",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "purchase_id": "08e20c88-6789-4038-af9a-b1e091c5127a",
    "purchase_line_id": "80001d68-8b6d-4394-aec6-4a96071d8673",
    "quantity": "3",
    "unit_price_eur": "379.0"
  },
  {
    "name_snapshot": "GSB 18V-90 C",
    "product_id": "06f80d3f-2c18-5d0f-876b-d95f03eee4cc",
    "purchase_id": "08e20c88-6789-4038-af9a-b1e091c5127a",
    "purchase_line_id": "b0629fdc-e388-4ea0-8b3c-d4bd962b871a",
    "quantity": "2",
    "unit_price_eur": "249.0"
  },
  {
    "name_snapshot": "GWS 18V-10",
    "product_id": "9e78bc6f-3ec5-5e97-9cc1-14b91ed47f73",
    "purchase_id": "db0093be-985c-48f8-a628-76ca4bfd25a9",
    "purchase_line_id": "a9a1468e-53d3-4a2d-86c7-a31546bb5cc6",
    "quantity": "1",
    "unit_price_eur": "199.0"
  },
  {
    "name_snapshot": "GBH 18V-26 F",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "purchase_id": "db0093be-985c-48f8-a628-76ca4bfd25a9",
    "purchase_line_id": "f5657091-bf37-406c-939b-d3cc9e4b838a",
    "quantity": "2",
    "unit_price_eur": "379.0"
  },
  {
    "name_snapshot": "PSR 1080 LI",
    "product_id": "5bbcd7cd-2271-52cb-9327-6ae3897f2401",
    "purchase_id": "294c3346-4f9c-57e6-9407-c2b4f7f0cdd3",
    "purchase_line_id": "000b1bdd-ca86-527a-a4fa-95e5a3f15828",
    "quantity": "1",
    "unit_price_eur": "79.0"
  },
  {
    "name_snapshot": "PSB 1800 LI-2",
    "product_id": "0895d282-3f1c-5c38-b465-25f70a5a4419",
    "purchase_id": "a458a6d0-8936-5528-be6c-33ef4539a52d",
    "purchase_line_id": "12e51864-9824-517b-9cc6-d50c0f313485",
    "quantity": "1",
    "unit_price_eur": "139.0"
  },
  {
    "name_snapshot": "GST 18V-LI S",
    "product_id": "e5b18e53-b97b-5d22-95e7-6cb691bf3f48",
    "purchase_id": "f494bbf5-342a-5f5a-8059-ba668659e7e0",
    "purchase_line_id": "1430e4ac-a846-5d65-80f5-529c3323a3d3",
    "quantity": "2",
    "unit_price_eur": "169.0"
  },
  {
    "name_snapshot": "GBH 18V-26 F",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "purchase_id": "294c3346-4f9c-57e6-9407-c2b4f7f0cdd3",
    "purchase_line_id": "2e279749-7adf-523a-ac69-18b787466422",
    "quantity": "1",
    "unit_price_eur": "379.0"
  }
]
```

## event_view_item

```console
$ databricks experimental aitools tools query "SELECT * FROM nikks_fevm_workspace_7405607030687545.techsummit.event_view_item LIMIT 10" -p FEVM
[
  {
    "ga_session_id": "c3b5c8eb-d710-493a-a2c6-f872b1089e50",
    "ingest_timestamp": "2026-09-29T09:09:45.934Z",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "user_id": "dbcfeeaa-f0f4-5523-b879-05acc7aa0845"
  },
  {
    "ga_session_id": "d91ee17e-1593-4f09-ab68-c83a2d32624b",
    "ingest_timestamp": "2026-10-02T11:34:24.251Z",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "user_id": "dbcfeeaa-f0f4-5523-b879-05acc7aa0845"
  },
  {
    "ga_session_id": "1790458536",
    "ingest_timestamp": "2026-09-26T21:35:36.354Z",
    "product_id": "product-live-proof-20260926T213534Z",
    "user_id": "user-live-proof-20260926T213534Z"
  },
  {
    "ga_session_id": "",
    "ingest_timestamp": "2026-08-12T09:28:04.599Z",
    "product_id": "ae063860-45ae-5d05-b070-ebbe7072d0ae",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  },
  {
    "ga_session_id": "",
    "ingest_timestamp": "2026-07-16T16:47:38.599Z",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  },
  {
    "ga_session_id": "",
    "ingest_timestamp": "2026-08-21T13:53:44.599Z",
    "product_id": "0895d282-3f1c-5c38-b465-25f70a5a4419",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  },
  {
    "ga_session_id": "",
    "ingest_timestamp": "2026-07-24T07:24:46.599Z",
    "product_id": "cc8a934a-9b64-5ce8-8736-ad5999614b51",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  },
  {
    "ga_session_id": "",
    "ingest_timestamp": "2026-07-21T15:57:13.599Z",
    "product_id": "0895d282-3f1c-5c38-b465-25f70a5a4419",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  },
  {
    "ga_session_id": "",
    "ingest_timestamp": "2026-08-11T17:49:36.599Z",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  },
  {
    "ga_session_id": "",
    "ingest_timestamp": "2026-08-25T02:40:32.599Z",
    "product_id": "1b7fb3fe-fcc0-5d5a-bcd2-160cf14763ce",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  }
]
```

## event_add_to_cart

```console
$ databricks experimental aitools tools query "SELECT * FROM nikks_fevm_workspace_7405607030687545.techsummit.event_add_to_cart LIMIT 10" -p FEVM
[
  {
    "cart_action": "added",
    "cart_id": "7ed76590-a732-4ab0-9348-2f42408c7d77",
    "currency": "EUR",
    "item_name": "GBH 18V-26 F",
    "new_quantity": "1",
    "previous_quantity": "0",
    "price": "379.0",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "quantity_delta": "1",
    "source_timestamp": "2026-10-02T11:34:25.863Z",
    "user_id": "dbcfeeaa-f0f4-5523-b879-05acc7aa0845"
  },
  {
    "cart_action": "added",
    "cart_id": "33aebd42-b45c-40b0-bfa2-db9de4372f23",
    "currency": "EUR",
    "item_name": "GBH 18V-26 F",
    "new_quantity": "1",
    "previous_quantity": "0",
    "price": "379.0",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "quantity_delta": "1",
    "source_timestamp": "2026-09-29T04:49:33.062Z",
    "user_id": "dbcfeeaa-f0f4-5523-b879-05acc7aa0845"
  },
  {
    "cart_action": "added",
    "cart_id": "a55694ff-bf14-4995-90d9-5ffea0d64bec",
    "currency": "EUR",
    "item_name": "GWS 18V-10",
    "new_quantity": "1",
    "previous_quantity": "0",
    "price": "199.0",
    "product_id": "9e78bc6f-3ec5-5e97-9cc1-14b91ed47f73",
    "quantity_delta": "1",
    "source_timestamp": "2026-09-28T18:45:01.330Z",
    "user_id": "dbcfeeaa-f0f4-5523-b879-05acc7aa0845"
  },
  {
    "cart_action": "add",
    "cart_id": "cart-live-proof-20260926T213534Z",
    "currency": "EUR",
    "item_name": "LIVE PROOF product live-proof-20260926T213534Z",
    "new_quantity": "1",
    "previous_quantity": "0",
    "price": "99.99",
    "product_id": "product-live-proof-20260926T213534Z",
    "quantity_delta": "1",
    "source_timestamp": "2026-09-26T21:35:37.452Z",
    "user_id": "user-live-proof-20260926T213534Z"
  },
  {
    "cart_action": "added",
    "cart_id": "233adb67-4dc2-4f80-9f62-c81fb791b7cb",
    "currency": "EUR",
    "item_name": "GSB 18V-90 C",
    "new_quantity": "2",
    "previous_quantity": "0",
    "price": "249.0",
    "product_id": "06f80d3f-2c18-5d0f-876b-d95f03eee4cc",
    "quantity_delta": "2",
    "source_timestamp": "2026-09-27T14:59:36.885Z",
    "user_id": "dbcfeeaa-f0f4-5523-b879-05acc7aa0845"
  },
  {
    "cart_action": "added",
    "cart_id": "233adb67-4dc2-4f80-9f62-c81fb791b7cb",
    "currency": "EUR",
    "item_name": "GBH 18V-26 F",
    "new_quantity": "1",
    "previous_quantity": "0",
    "price": "379.0",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "quantity_delta": "1",
    "source_timestamp": "2026-09-26T21:38:35.719Z",
    "user_id": "dbcfeeaa-f0f4-5523-b879-05acc7aa0845"
  },
  {
    "cart_action": "add",
    "cart_id": "413557d9-c913-4572-8a4e-64e4dc54d2a4",
    "currency": "EUR",
    "item_name": "GWS 22-230 JH",
    "new_quantity": "1",
    "previous_quantity": "0",
    "price": "189.0",
    "product_id": "ae063860-45ae-5d05-b070-ebbe7072d0ae",
    "quantity_delta": "1",
    "source_timestamp": "2026-08-12T09:58:04.599Z",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  },
  {
    "cart_action": "add",
    "cart_id": "35f53515-1922-42fe-831d-aea1c5c21428",
    "currency": "EUR",
    "item_name": "GBH 18V-26 F",
    "new_quantity": "3",
    "previous_quantity": "0",
    "price": "379.0",
    "product_id": "35ad77dd-1a36-5c08-a86c-79a164bd549d",
    "quantity_delta": "3",
    "source_timestamp": "2026-07-16T16:48:38.599Z",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  },
  {
    "cart_action": "add",
    "cart_id": "3a3da61f-780d-4797-b675-849f086d86bc",
    "currency": "EUR",
    "item_name": "PSB 1800 LI-2",
    "new_quantity": "3",
    "previous_quantity": "0",
    "price": "139.0",
    "product_id": "0895d282-3f1c-5c38-b465-25f70a5a4419",
    "quantity_delta": "3",
    "source_timestamp": "2026-08-21T14:00:44.599Z",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  },
  {
    "cart_action": "add",
    "cart_id": "dbff0df4-c434-4e92-b123-abb65b791973",
    "currency": "EUR",
    "item_name": "PBH 2100 RE",
    "new_quantity": "2",
    "previous_quantity": "0",
    "price": "99.0",
    "product_id": "cc8a934a-9b64-5ce8-8736-ad5999614b51",
    "quantity_delta": "2",
    "source_timestamp": "2026-07-24T07:25:46.599Z",
    "user_id": "7e1edb8d-6d55-458f-864a-6921a501b1f6"
  }
]
```

## idp_product_specs

```console
$ databricks experimental aitools tools query "SELECT * FROM nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs LIMIT 10" -p FEVM
[
  {
    "battery_platform": "18V",
    "chuck_capacity_mm": "",
    "max_torque_nm": "2.0",
    "model_name": "GBH 18V-26 F",
    "no_load_rpm": "3600",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/gbh-18v-26-f.pdf",
    "voltage_v": "18.0",
    "weight_kg": "2.2"
  },
  {
    "battery_platform": "18V",
    "chuck_capacity_mm": "",
    "max_torque_nm": "",
    "model_name": "GWS 18V-10",
    "no_load_rpm": "12000",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/gws-18v-10.pdf",
    "voltage_v": "18.0",
    "weight_kg": "1.9"
  },
  {
    "battery_platform": "10.8V",
    "chuck_capacity_mm": "10.0",
    "max_torque_nm": "21.0",
    "model_name": "PSR 1080 LI",
    "no_load_rpm": "1200",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/psr-1080-li.pdf",
    "voltage_v": "10.8",
    "weight_kg": "0.9"
  },
  {
    "battery_platform": "corded",
    "chuck_capacity_mm": "",
    "max_torque_nm": "",
    "model_name": "PWS 700-115",
    "no_load_rpm": "10000",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/pws-700-115.pdf",
    "voltage_v": "",
    "weight_kg": "2.0"
  },
  {
    "battery_platform": "18V",
    "chuck_capacity_mm": "",
    "max_torque_nm": "",
    "model_name": "GST 18V-LI S",
    "no_load_rpm": "",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/gst-18v-li-s.pdf",
    "voltage_v": "18.0",
    "weight_kg": "2.3"
  },
  {
    "battery_platform": "corded",
    "chuck_capacity_mm": "",
    "max_torque_nm": "",
    "model_name": "GWS 22-230 JH",
    "no_load_rpm": "6400",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/gws-22-230-jh.pdf",
    "voltage_v": "",
    "weight_kg": "6.2"
  },
  {
    "battery_platform": "18V",
    "chuck_capacity_mm": "16.0",
    "max_torque_nm": "63.0",
    "model_name": "GSR 18V-55",
    "no_load_rpm": "1500",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/gsr-18v-55.pdf",
    "voltage_v": "18.0",
    "weight_kg": "2.2"
  },
  {
    "battery_platform": "corded",
    "chuck_capacity_mm": "",
    "max_torque_nm": "2.7",
    "model_name": "GBH 2-26",
    "no_load_rpm": "3600",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/gbh-2-26.pdf",
    "voltage_v": "",
    "weight_kg": "2.6"
  },
  {
    "battery_platform": "18V",
    "chuck_capacity_mm": "13.0",
    "max_torque_nm": "106.0",
    "model_name": "GSB 18V-90 C",
    "no_load_rpm": "3000",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/gsb-18v-90-c.pdf",
    "voltage_v": "18.0",
    "weight_kg": "2.8"
  },
  {
    "battery_platform": "18V Li-Ion",
    "chuck_capacity_mm": "12.7",
    "max_torque_nm": "150.0",
    "model_name": "PSB 1800 LI-2",
    "no_load_rpm": "3000",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/psb-1800-li-2.pdf",
    "voltage_v": "18.0",
    "weight_kg": "1.9"
  }
]
```

