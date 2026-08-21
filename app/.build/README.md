# Placeholder — generated build output

This directory is the app's `source_code_path` (see `resources/app.yml`) and is
normally produced by `apx build`, which compiles the React UI and copies the
Python backend + `app.yml` here.

It is intentionally kept (with a placeholder) so `databricks bundle validate`
succeeds on a fresh checkout without a full toolchain install. **Before
deploying the app bundle, run `apx build` from `app/` to populate it for real.**
