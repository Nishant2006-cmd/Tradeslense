# AI Usage Documentation - TradeLens Project

During the development of the TradeLens assignment, an AI assistant was utilized as a collaborative coding partner.

### Key Areas of Collaboration:
1. **Data Ingestion & Parsing:** Designing robust data pipelines using `pandas` to handle multi-format MT5 CSV exports and unstructured broker Excel files.
2. **Error Handling & Edge Cases:** Resolving Windows environment issues, file encoding mismatches (`utf-8-sig`, `latin-1`, `cp1252`), and dynamic rule evaluation from `rules.json`.
3. **Automated Testing:** Structuring `pytest` scripts to verify script execution, output validation, and idempotency.

### What the AI Got Wrong & How It Was Fixed:
Initially, the AI suggested generating the `.gitignore` file using PowerShell's `echo "venv/" > .gitignore`, which saved the file in **UTF-16 encoding**. Git failed to read this encoding, causing `venv/` and `__pycache__/` to be tracked and pushed. This was caught during review, corrected by saving `.gitignore` as clean plain UTF-8 text, and untracking the cached directories via git.