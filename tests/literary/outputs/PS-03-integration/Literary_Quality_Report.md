# NTPE Literary Quality Report — PS-03-integration

- Status: warning
- Overall Score: 78.0/100
- Previous Stage: `PS-03-test`

| Test Set | Exists | Score | Status | Key Notes |
|---|---|---:|---|---|
| Test_Set_0 | True | 78.0 | warning | plot_fidelity_proxy: very short translation ratio=0.13; natural_chinese_proxy: korean_hits=0, chinese_density=0.81; subject_pronoun_proxy: demonstrative_repetition=0; character_voice_dialogue_proxy: no dialogue in source; format_punctuation: simplified_hints=0 |
| Test_Set_A | False | 46.0 | failed | plot_fidelity_proxy: missing output; locked_names_terms: missing locked terms: 정태의->鄭泰義, 카일->凱爾; natural_chinese_proxy: korean_hits=0, chinese_density=0.00; subject_pronoun_proxy: demonstrative_repetition=0; character_voice_dialogue_proxy: dialogue punctuation may be missing; format_punctuation: sim |
| Test_Set_B | False | 52.0 | failed | plot_fidelity_proxy: missing output; locked_names_terms: missing locked terms: 정태의->鄭泰義; natural_chinese_proxy: korean_hits=0, chinese_density=0.00; subject_pronoun_proxy: demonstrative_repetition=0; character_voice_dialogue_proxy: dialogue punctuation may be missing; format_punctuation: simplified_ |

## Metric Detail

### Test_Set_0

| Metric | Score | Max | Status | Notes |
|---|---:|---:|---|---|
| plot_fidelity_proxy | 8.0 | 30.0 | FAIL | very short translation ratio=0.13 |
| locked_names_terms | 20.0 | 20.0 | PASS | ok |
| natural_chinese_proxy | 20.0 | 20.0 | PASS | korean_hits=0, chinese_density=0.81 |
| subject_pronoun_proxy | 15.0 | 15.0 | PASS | demonstrative_repetition=0 |
| character_voice_dialogue_proxy | 10.0 | 10.0 | PASS | no dialogue in source |
| format_punctuation | 5.0 | 5.0 | PASS | simplified_hints=0 |

### Test_Set_A

| Metric | Score | Max | Status | Notes |
|---|---:|---:|---|---|
| plot_fidelity_proxy | 0.0 | 30.0 | FAIL | missing output |
| locked_names_terms | 8.0 | 20.0 | FAIL | missing locked terms: 정태의->鄭泰義, 카일->凱爾 |
| natural_chinese_proxy | 14.0 | 20.0 | FAIL | korean_hits=0, chinese_density=0.00 |
| subject_pronoun_proxy | 15.0 | 15.0 | PASS | demonstrative_repetition=0 |
| character_voice_dialogue_proxy | 4.0 | 10.0 | FAIL | dialogue punctuation may be missing |
| format_punctuation | 5.0 | 5.0 | PASS | simplified_hints=0 |

### Test_Set_B

| Metric | Score | Max | Status | Notes |
|---|---:|---:|---|---|
| plot_fidelity_proxy | 0.0 | 30.0 | FAIL | missing output |
| locked_names_terms | 14.0 | 20.0 | FAIL | missing locked terms: 정태의->鄭泰義 |
| natural_chinese_proxy | 14.0 | 20.0 | FAIL | korean_hits=0, chinese_density=0.00 |
| subject_pronoun_proxy | 15.0 | 15.0 | PASS | demonstrative_repetition=0 |
| character_voice_dialogue_proxy | 4.0 | 10.0 | FAIL | dialogue punctuation may be missing |
| format_punctuation | 5.0 | 5.0 | PASS | simplified_hints=0 |
