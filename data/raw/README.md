# Raw Data Conventions

Supported inputs for the first scaffold:

- `*.md` / `*.txt`
  - Used by `scripts/build_dataset.py source-pool`
  - Produces chunked Chinese plain-text source blocks for later teacher labeling

- `*.jsonl`
  - Used by `scripts/build_dataset.py training`
  - Each line should already contain `original_text` and `compressed_text`

Recommended teacher-labeled JSONL fields:

- `sample_id`
- `source_type`
- `source_name`
- `split`
- `language`
- `original_text`
- `compressed_text`
- `style_tag`
- `contains_anchor`
- `quality_notes`

A small demo file is included as `labeled_pairs_demo_v1.jsonl`.

