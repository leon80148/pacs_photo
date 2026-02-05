# Packaging + Config.ini Spec

## Problem
Non-developers need a simple installable package and a simple settings file they can edit.

## Goals
- Provide a Windows package that users can download and run without Python or Docker.
- Support a `config.ini` file for key settings.
- Keep environment variables and `.env` support for advanced use and dev.
- Document how to install and edit settings.

## Non-goals
- A full MSI installer with registry integration.
- Auto-update or auto-run as a Windows service.
- Changing the runtime settings API behavior.

## User Flow
1. User downloads a zip package.
2. User extracts it to a folder.
3. User edits `config.ini`.
4. User runs `PhotoPacs.exe`.
5. User opens `http://<PC IP>:9470` on their phone.

## API / Contract
- No API changes.
- New config file lookup order:
  1) Environment variables
  2) `config.ini`
  3) `.env`

## Data Model
- `config.ini` key/value pairs map to existing settings fields.
- Optional `[photo_pacs]` section name.

## Error Handling
- Missing `config.ini` should not break startup.
- Invalid values should keep existing Pydantic validation errors.

## Security / Privacy
- `config.ini` may contain PHI-related settings; do not log its contents.
- Keep current PHI logging rules unchanged.

## Acceptance Criteria
- Build script creates a Windows release zip with `PhotoPacs.exe` and `config.ini`.
- `config.ini` values override `.env`.
- Environment variables override `config.ini`.
- App still serves the web UI correctly in packaged form.

## Test Plan
- Unit tests for `config.ini` precedence.
- Manual smoke test: run `PhotoPacs.exe`, load `/healthz`, open UI.
