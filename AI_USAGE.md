# AI Usage Documentation - TradeLens Project

During the development of the TradeLens assignment, an AI assistant (Gemini) was utilized as a collaborative coding partner to accelerate the development lifecycle.

### Key Areas of Collaboration:
1. **Data Ingestion & Parsing:** Designing robust data pipelines using `pandas` to handle multi-format MT5 CSV exports (handling various delimiters like tabs and commas) and unstructured broker Excel files.
2. **Error Handling & Edge Cases:** Resolving real-world Windows environment issues, including file encoding mismatches (`utf-8-sig`, `latin-1`, `cp1252`), `NaT` timestamp validations, and currency symbol character encoding (`₹`).
3. **Automated Testing:** Structuring `pytest` scripts with absolute path resolution and temporary directories (`tmp_path`) to verify script execution, output generation, and idempotency.