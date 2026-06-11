# Deferred Items — Phase 14

## From 14-02 execution (2026-06-11)

- **DeprecationWarning in src/llm_client.py:27** — `invalid escape sequence '\d'` inside the `system_prompt` triple-quoted string. Pre-existing, unrelated to 14-02 changes (test backfill only). Fix is to make the string raw or escape the backslash. Out of scope per executor scope boundary.
