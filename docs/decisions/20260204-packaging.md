# Decision: Windows Packaging + INI Config

Date: 2026-02-04

## Decision
Use PyInstaller to build a Windows executable and ship it as a zip package. Add `config.ini` support for key settings with the following precedence:
1) Environment variables
2) `config.ini`
3) `.env`

## Rationale
- PyInstaller provides a single executable without requiring Python on the target PC.
- INI is simple to edit for non-technical users.
- Keeping `.env` and env vars preserves current dev workflows.

## Consequences
- Build requires Python + PyInstaller on the build machine.
- A true MSI installer is out of scope; zip distribution is used.
