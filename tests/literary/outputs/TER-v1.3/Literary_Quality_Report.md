# NTPE Literary Quality Report — TER-v1.3

- Status: success
- Overall Score: 100.0/100
- Previous Stage: `TER-v1.2`

| Test Set | Exists | Score | Status | Key Notes |
|---|---|---:|---|---|
| Smoke_Set | True | 100.0 | success | plot_fidelity_proxy: length ratio=0.66; natural_chinese_proxy: korean_hits=0, chinese_density=0.83; subject_pronoun_proxy: demonstrative_repetition=0; character_voice_dialogue_proxy: no dialogue in source; format_punctuation: simplified_hints=0 |
| Golden_Set | False | 46.0 | failed | plot_fidelity_proxy: missing output; locked_names_terms: missing locked terms: 정태의->鄭泰義, 카일->凱爾; natural_chinese_proxy: korean_hits=0, chinese_density=0.00; subject_pronoun_proxy: demonstrative_repetition=0; character_voice_dialogue_proxy: dialogue punctuation may be missing; format_punctuation: sim |
| Regression_Set | False | 52.0 | failed | plot_fidelity_proxy: missing output; locked_names_terms: missing locked terms: 정태의->鄭泰義; natural_chinese_proxy: korean_hits=0, chinese_density=0.00; subject_pronoun_proxy: demonstrative_repetition=0; character_voice_dialogue_proxy: dialogue punctuation may be missing; format_punctuation: simplified_ |

## Metric Detail

### Smoke_Set

| Metric | Score | Max | Status | Notes |
|---|---:|---:|---|---|
| plot_fidelity_proxy | 30.0 | 30.0 | PASS | length ratio=0.66 |
| locked_names_terms | 20.0 | 20.0 | PASS | ok |
| natural_chinese_proxy | 20.0 | 20.0 | PASS | korean_hits=0, chinese_density=0.83 |
| subject_pronoun_proxy | 15.0 | 15.0 | PASS | demonstrative_repetition=0 |
| character_voice_dialogue_proxy | 10.0 | 10.0 | PASS | no dialogue in source |
| format_punctuation | 5.0 | 5.0 | PASS | simplified_hints=0 |

### Golden_Set

| Metric | Score | Max | Status | Notes |
|---|---:|---:|---|---|
| plot_fidelity_proxy | 0.0 | 30.0 | FAIL | missing output |
| locked_names_terms | 8.0 | 20.0 | FAIL | missing locked terms: 정태의->鄭泰義, 카일->凱爾 |
| natural_chinese_proxy | 14.0 | 20.0 | FAIL | korean_hits=0, chinese_density=0.00 |
| subject_pronoun_proxy | 15.0 | 15.0 | PASS | demonstrative_repetition=0 |
| character_voice_dialogue_proxy | 4.0 | 10.0 | FAIL | dialogue punctuation may be missing |
| format_punctuation | 5.0 | 5.0 | PASS | simplified_hints=0 |

### Regression_Set

| Metric | Score | Max | Status | Notes |
|---|---:|---:|---|---|
| plot_fidelity_proxy | 0.0 | 30.0 | FAIL | missing output |
| locked_names_terms | 14.0 | 20.0 | FAIL | missing locked terms: 정태의->鄭泰義 |
| natural_chinese_proxy | 14.0 | 20.0 | FAIL | korean_hits=0, chinese_density=0.00 |
| subject_pronoun_proxy | 15.0 | 15.0 | PASS | demonstrative_repetition=0 |
| character_voice_dialogue_proxy | 4.0 | 10.0 | FAIL | dialogue punctuation may be missing |
| format_punctuation | 5.0 | 5.0 | PASS | simplified_hints=0 |
