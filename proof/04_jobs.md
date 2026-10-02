# Build job run

Latest run returned by `jobs list-runs`: run 11230604920571. These are the actual deployed task names and statuses; they differ from the current checked-in bundle definition.

```console
$ databricks jobs get-run 11230604920571 -p FEVM -o json | jq '{job_id, run_id, run_name, start_time, end_time, state, tasks: [.tasks[] | {task_key, start_time, end_time, state}]}'
{
  "job_id": 919820514950394,
  "run_id": 11230604920571,
  "run_name": "powertools-build",
  "start_time": 1787343493168,
  "end_time": 1787343778901,
  "state": {
    "life_cycle_state": "TERMINATED",
    "result_state": "SUCCESS",
    "state_message": "",
    "user_cancelled_or_timedout": false
  },
  "tasks": [
    {
      "task_key": "wait_for_cdc",
      "start_time": 1787343493237,
      "end_time": 1787343547627,
      "state": {
        "life_cycle_state": "TERMINATED",
        "result_state": "SUCCESS",
        "state_message": "",
        "user_cancelled_or_timedout": false
      }
    },
    {
      "task_key": "key_normalize",
      "start_time": 1787343642073,
      "end_time": 1787343649950,
      "state": {
        "life_cycle_state": "TERMINATED",
        "result_state": "SUCCESS",
        "state_message": "",
        "user_cancelled_or_timedout": false
      }
    },
    {
      "task_key": "idp_product_specs",
      "start_time": 1787343650444,
      "end_time": 1787343778543,
      "state": {
        "life_cycle_state": "TERMINATED",
        "result_state": "SUCCESS",
        "state_message": "",
        "user_cancelled_or_timedout": false
      }
    },
    {
      "task_key": "run_silver_pipeline",
      "start_time": 1787343564077,
      "end_time": 1787343616812,
      "state": {
        "life_cycle_state": "TERMINATED",
        "result_state": "SUCCESS",
        "state_message": "",
        "user_cancelled_or_timedout": false
      }
    },
    {
      "task_key": "cdc_to_current",
      "start_time": 1787343617224,
      "end_time": 1787343641777,
      "state": {
        "life_cycle_state": "TERMINATED",
        "result_state": "SUCCESS",
        "state_message": "",
        "user_cancelled_or_timedout": false
      }
    },
    {
      "task_key": "seed_gtm_events",
      "start_time": 1787343548190,
      "end_time": 1787343563651,
      "state": {
        "life_cycle_state": "TERMINATED",
        "result_state": "SUCCESS",
        "state_message": "",
        "user_cancelled_or_timedout": false
      }
    }
  ]
}
```

