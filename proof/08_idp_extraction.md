# IDP typed extraction from datasheet PDFs

The result contains every row and the typed `DOUBLE` voltage/torque columns and `INT` RPM column produced downstream of `ai_extract`. Empty JSON strings below represent SQL NULL in this CLI renderer.

```console
$ databricks experimental aitools tools query "SELECT source_path, model_name, voltage_v, max_torque_nm, no_load_rpm, chuck_capacity_mm, weight_kg, battery_platform FROM nikks_fevm_workspace_7405607030687545.techsummit.idp_product_specs ORDER BY model_name" -p FEVM
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
    "battery_platform": "12V",
    "chuck_capacity_mm": "10.0",
    "max_torque_nm": "35.0",
    "model_name": "GSR 12V-35",
    "no_load_rpm": "1500",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/gsr-12v-35.pdf",
    "voltage_v": "12.0",
    "weight_kg": "1.3"
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
    "battery_platform": "corded",
    "chuck_capacity_mm": "",
    "max_torque_nm": "2.2",
    "model_name": "PBH 2100 RE",
    "no_load_rpm": "",
    "source_path": "/Volumes/nikks_fevm_workspace_7405607030687545/techsummit/datasheets/pbh-2100-re.pdf",
    "voltage_v": "",
    "weight_kg": "2.5"
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
  }
]
```

