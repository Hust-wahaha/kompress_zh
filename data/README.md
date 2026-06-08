# Data Layout

- `raw/`: source documents and teacher-labeled pair files.
- `interim/`: chunked source pools and normalization outputs.
- `final/`: train/val/test JSONL files consumed by training and evaluation.

The new compressor project should only write dataset artifacts under this directory tree.

