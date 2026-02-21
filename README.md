# acsmcli_tool (prototype)

A lightweight command-line prototype for working with `.acsm` files without requiring Adobe desktop software.

## What this prototype does

- Reads ACSM metadata and prints fulfillment URL details.
- Requests the fulfillment payload from the URL embedded in the ACSM file.
- Saves the returned payload to disk (`.epub`, `.pdf`, or `.bin` inference based on content-type).

## What this prototype does **not** do

- No DRM removal/decryption.
- No Adobe account activation flow.
- No library management.

## Usage

```bash
python3 acsmcli.py info ./book.acsm
python3 acsmcli.py info ./book.acsm --json

# Preview request target without network traffic:
python3 acsmcli.py fulfill ./book.acsm --dry-run

# Perform fulfillment request and save payload:
python3 acsmcli.py fulfill ./book.acsm -o ./book.epub
```

## Notes

This is intended as a fair-use oriented prototype for content you are authorized to access.
Always verify local laws and your license terms.
