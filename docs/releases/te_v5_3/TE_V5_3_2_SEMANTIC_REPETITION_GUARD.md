# TE v5.3.2 Semantic Repetition Guard

Adds a conservative near-duplicate paragraph detector to the TE v5 runtime quality pipeline.

The detector:

- checks only substantial paragraphs;
- compares paragraphs within a local three-paragraph window;
- combines sequence similarity with Chinese bigram overlap;
- subtracts comparable repetition already present in the source;
- reports `semantic_duplicate_paragraph` as a high-severity retry issue;
- never rewrites or deletes translated text automatically;
- does not call the Provider.

This closes the gap where paraphrased duplicate paragraphs passed exact duplicate checks.
