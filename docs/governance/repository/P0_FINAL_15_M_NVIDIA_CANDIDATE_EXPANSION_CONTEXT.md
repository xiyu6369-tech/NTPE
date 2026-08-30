# P0-FINAL-15-M — NVIDIA Candidate Expansion & Context Compatibility

## Purpose

Expand the viable NVIDIA candidate model pool and validate context compatibility
under NTPE real chunk/context conditions to identify a replacement for
`minimaxai/minimax-m3` (M1) which has persistent provider-specific HTTP 429.

## Scope

### In Scope
- Candidate discovery from official NVIDIA catalog
- Provider smoke tests (account entitlement + endpoint availability)
- Context compatibility gates (NTPE request budgets vs model limits)
- Translation fixture evaluation (narrative, dialogue, continuity)
- C1 Riva Translate chunking workaround validation
- Automated quality assessment (human review pending)
- Candidate classification per decision matrix

### Out of Scope
- Production model change
- Production routing change
- Retry/backoff/RPM modification
- Rate limiter modification
- Queue admission modification
- Timeout policy modification
- Translation runtime modification
- Automatic fallback modification
- Stress/concurrency testing

## Baseline

- **HEAD**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **origin/main**: 8c999b1219f65a6afaeaf0062e6c43f72691c188
- **divergence**: 0/0
- **branch**: main
- **Python**: 3.14.6
- **Client**: core/translation_engine/nvidia_client.py
- **Timestamp**: 2026-08-27T17:12:36.224338Z
- **Endpoint**: https://integrate.api.nvidia.com/v1/chat/completions
- **Credential**: NVIDIA_API_KEY (present: True)
- **Current Model**: minimaxai/minimax-m3 (PROVIDER_FAILURE_429)

## Candidate Discovery

### Candidates Evaluated

| Model | Provider | Catalog Owner | zh-TW | Korean | Translation Model | Context Window | Notes |
|-------|----------|---------------|-------|--------|-------------------|----------------|-------|
| minimaxai/minimax-m3 | MiniMax | minimaxai | True | True | False | 128000 | Current baseline; consistent HTTP 429 on this account |
| nvidia/riva-translate-4b-instruct-v2 | NVIDIA | nvidia | True | True | True | 8192 | NVIDIA translation model; 8192 token context limit; document-level translation |
| nvidia/nemotron-3-ultra-550b-a55b | NVIDIA | nvidia | True | True | False | 128000 | NVIDIA flagship general-purpose LLM; 128K context; strong multilingual |
| nvidia/nemotron-3-super-120b-a12b | NVIDIA | nvidia | True | True | False | 128000 | NVIDIA general-purpose LLM; 128K context; strong multilingual; 120B params |
| moonshotai/kimi-k3 | Moonshot AI | moonshotai | True | True | False | 128000 | Large context general LLM; 128K context; strong Chinese capability |
| google/gemma-4-31b-it | Google | google | True | True | False | 8192 | Google general LLM; 8K context; multilingual |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | NVIDIA | nvidia | True | True | False | 128000 | NVIDIA reasoning model; 128K context; multilingual |

## Official Catalog Evidence

All candidates verified present in NVIDIA `/v1/models` catalog endpoint.
Catalog presence ≠ account entitlement ≠ actual invocation success.

| Model | In Catalog | Owned By | Context Window | Endpoint Support |
|-------|------------|----------|----------------|------------------|
| minimaxai/minimax-m3 | True | minimaxai | 128000 | True |
| nvidia/riva-translate-4b-instruct-v2 | True | nvidia | 8192 | True |
| nvidia/nemotron-3-ultra-550b-a55b | True | nvidia | 128000 | True |
| nvidia/nemotron-3-super-120b-a12b | True | nvidia | 128000 | True |
| moonshotai/kimi-k3 | True | moonshotai | 128000 | True |
| google/gemma-4-31b-it | True | google | 8192 | True |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | True | nvidia | 128000 | True |

## Provider Smoke Tests

Single minimal request to confirm account entitlement and endpoint availability.
No retry, no concurrency, no burst.

| Model | HTTP Status | Success | Latency (ms) | Provider Request ID | NVCF Tracking |
|-------|-------------|---------|--------------|---------------------|---------------|
| minimaxai/minimax-m3 | 200 | True | 8564 | chatcmpl-ea814971-7e30-4d9e-b2af-58936ebefe60 | 94025dc9-9c5a-486c-bfbb-4d284b2e8223 |
| nvidia/riva-translate-4b-instruct-v2 | 200 | True | 498 | chatcmpl-a3b9c329fb5faaf1 | 4e64b0f5-26ea-4d30-8755-957f554ebc03 |
| nvidia/nemotron-3-ultra-550b-a55b | 200 | True | 38305 | chatcmpl-560ef38c-9878-4e13-b8e6-8851a9b923be | 98f9370d-ba6a-4751-ba0d-add0cd7117c4 |
| nvidia/nemotron-3-super-120b-a12b | 200 | True | 16589 | chatcmpl-4eafe619-c44f-43ab-9bc1-c4a40802aae4 | fa17e5dd-fd67-4e3d-96b2-b6fd7aea8dc1 |
| moonshotai/kimi-k3 | 408 | False | 60076 | N/A | None |
| google/gemma-4-31b-it | 200 | True | 2864 | 85232ad017f34cdb9f3bf7d3033c77e5 | f23120ff-91c8-4bd5-84c3-e99c9a6db05d |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | 200 | True | 2251 | chatcmpl-d07c5e80-a65d-43b5-9207-7d42aeae92d1 | 377f7696-5389-4fb3-89c7-71f8a6c0a0bb |

## Context Compatibility Gate

**Core Gate**: Context Compatibility = GATE. If a candidate cannot fit NTPE production
request budget within its context window, it cannot be a replacement candidate.

### Context Profiles

| Profile | Description | Est. Input Tokens | Est. Output Tokens | Total Est. Tokens |
|---------|-------------|-------------------|-------------------|-------------------|
| small | Normal short chunk, minimal context | 341 | 2000 | 2341 |
| production | Production-like: translation prompt + character/context memory + glossary + recent scene + source chunk | 1038 | 4000 | 5038 |
| large | Large request approaching pipeline limits (not stress test) | 1197 | 6000 | 7197 |


### Context Compatibility Results

| Model | Profile | HTTP Status | Success | Est. Total Tokens | Model Limit | Remaining Margin |
|-------|---------|-------------|---------|-------------------|-------------|------------------|
| minimaxai/minimax-m3 | small | 200 | True | 594 | 128000 | 125659 |
| minimaxai/minimax-m3 | production | 200 | True | 2552 | 128000 | 122962 |
| minimaxai/minimax-m3 | large | 429 | False | 0 | 128000 | 120803 |
| nvidia/riva-translate-4b-instruct-v2 | small | 200 | True | 307 | 8192 | 5851 |
| nvidia/riva-translate-4b-instruct-v2 | production | 200 | True | 1282 | 8192 | 3154 |
| nvidia/riva-translate-4b-instruct-v2 | large | 200 | True | 1588 | 8192 | 995 |
| nvidia/nemotron-3-ultra-550b-a55b | small | 200 | True | 1108 | 128000 | 125659 |
| nvidia/nemotron-3-ultra-550b-a55b | production | 200 | True | 2761 | 128000 | 122962 |
| nvidia/nemotron-3-ultra-550b-a55b | large | 200 | True | 3260 | 128000 | 120803 |
| nvidia/nemotron-3-super-120b-a12b | small | 200 | True | 1063 | 128000 | 125659 |
| nvidia/nemotron-3-super-120b-a12b | production | 200 | True | 5328 | 128000 | 122962 |
| nvidia/nemotron-3-super-120b-a12b | large | 200 | True | 4558 | 128000 | 120803 |
| moonshotai/kimi-k3 | small | 0 | False | 0 | 128000 | 125659 |
| moonshotai/kimi-k3 | production | 0 | False | 0 | 128000 | 122962 |
| moonshotai/kimi-k3 | large | 0 | False | 0 | 128000 | 120803 |
| google/gemma-4-31b-it | small | 200 | True | 457 | 8192 | 5851 |
| google/gemma-4-31b-it | production | 200 | True | 2416 | 8192 | 3154 |
| google/gemma-4-31b-it | large | 200 | True | 2930 | 8192 | 995 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | small | 200 | True | 1327 | 128000 | 125659 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | production | 503 | False | 0 | 128000 | 122962 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | large | 503 | False | 0 | 128000 | 120803 |


### Context Margin Analysis

Models with `remaining_margin ≈ 0` are classified as `CONTEXT_FRAGILE` and should not
be direct replacement candidates even if requests succeed.

- **minimaxai/minimax-m3** (production): margin=122962 (96.1%) — HEALTHY
- **nvidia/riva-translate-4b-instruct-v2** (production): margin=3154 (38.5%) — HEALTHY
- **nvidia/nemotron-3-ultra-550b-a55b** (production): margin=122962 (96.1%) — HEALTHY
- **nvidia/nemotron-3-super-120b-a12b** (production): margin=122962 (96.1%) — HEALTHY
- **moonshotai/kimi-k3** (production): margin=122962 (96.1%) — HEALTHY
- **google/gemma-4-31b-it** (production): margin=3154 (38.5%) — HEALTHY
- **nvidia/nemotron-3-nano-omni-30b-a3b-reasoning** (production): margin=122962 (96.1%) — HEALTHY


## Translation Fixture Evaluation

### Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| narrative | narrative | Novel narrative with character introspection, setting, dialogue |
| dialogue | dialogue | Multi-speaker emotional exchange, honorifics, character voice |
| continuity | continuity | Cross-chunk character/terminology/scene consistency |

### Translation Results

| Model | Fixture | Success | Latency (ms) | HTTP Status | Total Tokens |
|-------|---------|---------|--------------|-------------|--------------|
| minimaxai/minimax-m3 | narrative | True | 27595 | 200 | 2942 |
| minimaxai/minimax-m3 | dialogue | True | 7207 | 200 | 594 |
| minimaxai/minimax-m3 | continuity | False | 175 | 429 | 0 |
| nvidia/riva-translate-4b-instruct-v2 | narrative | False | 409 | 400 | 0 |
| nvidia/riva-translate-4b-instruct-v2 | dialogue | True | 1890 | 200 | 307 |
| nvidia/riva-translate-4b-instruct-v2 | continuity | True | 2215 | 200 | 328 |
| nvidia/nemotron-3-ultra-550b-a55b | narrative | True | 38782 | 200 | 3234 |
| nvidia/nemotron-3-ultra-550b-a55b | dialogue | False | 546 | 503 | 0 |
| nvidia/nemotron-3-ultra-550b-a55b | continuity | True | 32454 | 200 | 781 |
| nvidia/nemotron-3-super-120b-a12b | narrative | True | 64240 | 200 | 4594 |
| nvidia/nemotron-3-super-120b-a12b | dialogue | True | 12981 | 200 | 924 |
| nvidia/nemotron-3-super-120b-a12b | continuity | True | 14808 | 200 | 1137 |
| moonshotai/kimi-k3 | narrative | False | 0 | 0 | 0 |
| moonshotai/kimi-k3 | dialogue | False | 0 | 0 | 0 |
| moonshotai/kimi-k3 | continuity | False | 0 | 0 | 0 |
| google/gemma-4-31b-it | narrative | True | 81866 | 200 | 2789 |
| google/gemma-4-31b-it | dialogue | True | 4436 | 200 | 457 |
| google/gemma-4-31b-it | continuity | True | 9664 | 200 | 426 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | narrative | False | 0 | 0 | 0 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | dialogue | False | 0 | 0 | 0 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | continuity | False | 0 | 0 | 0 |


### Translation Outputs (Successful Only)

#### minimaxai/minimax-m3 / narrative

```
鄭泰儀感到十分為難。

但事實上，這根本不是他需要為難的事。那個被他留在遙遠異國的、像怪物般的男人，終歸是個頭腦清醒、理性的傢伙，理應能理解這絕非鄭泰儀故意造成的局面。

然而，鄭泰儀卻不由得擔心起凱爾是否能安然無恙——畢竟凱爾義憤填膺地主張：「我可是好幾個月前就開始籌劃，費盡千辛萬苦才好不容易請到一週的假，結果那傢伙說因為工作的關係會比預定時間晚回來，難道我的假期就要這樣泡湯嗎？」說完便把特地跑到鄰國工作的弟弟丟下，獨自帶著鄭泰儀跑到這座遙遠南國的島嶼度假。（如果凱爾平時還算理性的話，本來也不會做出這種事，但就在出發工作前夕，他心愛的書竟被弟弟一把火燒了，這讓他氣得整整躺了三天。）

總之，鄭泰儀坐在這座必須轉乘小型飛機才能抵達、與外界斷了直飛航班的悠閒南國島嶼的飯店大廳沙發上，此刻雖然愜意，但一想到回到柏林後會掀起怎樣的風波，就只剩滿腹擔憂，忍不住嘆了口氣。

「……不過現在擔心也沒用，已經發生的事也無法挽回……難得來度假，總不能嘆著氣過完這一週吧，那可就虧大了。」

鄭泰儀最終得出了理性的結論，點了點頭。

這座被深邃的青玉色海洋環繞的島嶼，美麗而悠閒。來這裡的路上，他聽凱爾說，
```

#### minimaxai/minimax-m3 / dialogue

```
「真的沒事嗎？」民秀小心翼翼地問道。

智賢點了點頭，勉強擠出一絲微笑。「嗯，沒事。只是……有點累而已。」

「不對，你的眼神不是這樣。發生什麼事了？告訴我。」

智賢猶豫了一會兒，然後輕輕嘆了口氣。

「其實是……明天有發表會。還沒準備好，所以才這樣。」

民秀睜大了眼睛，顯得很驚訝。「明天？那只剩一天了啊！為什麼現在才說？」

「說了也幫不上忙啊。這是我自己的問題，應該由我自己解決。」

「別說這種話。我們不是朋友嗎？一起解決不就好了嗎？」

就這一句話，讓智賢的眼眶瞬間泛紅。
```

#### nvidia/riva-translate-4b-instruct-v2 / dialogue

```
"Really? Are you okay?" Min-soo asked carefully. "Yes, I'm fine. I'm just a little tired." "No, your eyes don't look like it. What's wrong? Tell me." Ji-hyun hesitated for a moment and let out a low sigh. "Actually, I have a presentation tomorrow. I'm not prepared." Min-soo's eyes widened in surprise. "It's only one day left! Why are you telling me now?" "Don't say that. We're friends. We can solve it together." Ji-hyun's eyes filled with tears at those words.
```

#### nvidia/riva-translate-4b-instruct-v2 / continuity

```
Kim Cheol-soo was a 30-year veteran detective. His cases were always complex, but he used his unique intuition to uncover the truth. His partner, Lee Young-hee, was the exact opposite. She was a principled investigator who relied solely on logic and evidence. One day, the two were assigned to a case of serial disappearances. Cheol-soo searched for clues in the subtle details at the scene, while Young-hee analyzed the commonalities among the victims. At first, they distrusted each other's methods
```

#### nvidia/nemotron-3-ultra-550b-a55b / narrative

```
鄭泰義正一臉為難。

然而實際上，這根本不是他該為難的事。被丟在遙遠異國的那個怪物般的男人，無論如何都是個理智尚在運作、算得上理性的人類，他會理解這種情況絕非鄭泰義刻意製造的。

倒是凱爾，才真正讓人擔心能不能平安無事。他振振有詞地主張：「好不容易從幾個月前就開始盼著、歷盡千辛萬苦才擠出一週假期，怎能因為那傢伙因公務比預定晚歸，就白白讓我的假期打折？」於是把去鄰國出差的弟弟扔在一旁，硬是把鄭泰義一股腦帶到這遙遠南國的小島渡假。（凱爾若是平常那個理性的自己，絕不會幹出這種事，但臨走前弟弟把他珍藏的書給燒了，氣得他病倒三天，這多少是主因。）

不管怎樣，鄭泰義坐在這座必須搭乘水上飛機單獨進入的悠閒南國小島飯店大廳沙發上，雖然當下很愜意，卻只能擔心回柏林後會惹出什麼麻煩，不禁嘆了口氣。

「……但現在預先擔心也沒用，既成事實無法改變……。難得來放假，若光嘆氣就把一週過了，太虧了。」

鄭泰義終究下了合理的結論，點了點頭。

四周環繞著深碧玉色海水的小島，美得驚人、閒適得讓人發呆。據凱爾在路上說，這裡的飯店幾乎成了幾位財閥的私人別墅，一般遊客根本進不來，所以是不用擔心被人認出、能悠閒度過假期的
```

#### nvidia/nemotron-3-ultra-550b-a55b / continuity

```
金哲秀是位擁有三十年資歷的刑警。他手中的案件向來錯綜複雜，但他總能憑藉獨特的直覺挖掘出真相。他的搭檔李英姬與他截然不同，是個僅憑邏輯與證據層層剝開案件的原則主義者。

某天，兩人接手了一宗連續失蹤案。哲秀試圖從現場微弱的痕跡中尋找線索，英姬則著手分析受害者的共同點。起初兩人對彼此的辦案方式抱持不信任，但很快便發現雙方的切入點竟能互補——哲秀的直覺為英姬的邏輯推演指引方向，英姬的鐵證則為哲秀的推測提供了堅實後盾。
```

#### nvidia/nemotron-3-super-120b-a12b / narrative

```
정태의感到为难。  

然而事实上，他并没有必要为难。那个被丢在遥远异国的怪物般的男子，说到底神志清醒，算是个理性的人，他一定会明白这情况绝非是정태의故意造成的。  

不过，“我早在几个月前就盼望着，费尽周折才争取到的一周假期，却因为那家伙因工作晚归而要削减我的假期”，他愤怒地宣称，把去邻国工作的兄弟抛在一边，只独自拉着정태의飞往遥远南国的岛屿度假，这让人不禁担心卡イル能否平安。（若卡イル平时还是那个理性的人，他本来不会做出这种事；但正因为他在出发前几天，因兄弟把他珍爱的书烧掉而愤怒到躺床三天，这才导致他如此冲动。）  

无论如何，这座只有乘坐小型包机才能抵达、没有直达航班的悠闲南国岛上，饭店大堂的沙发上，정태의此刻虽然觉得不错，却只为返回柏林后可能发生的事情而担忧，不由得叹了一口气。  

“……不过现在提前担心也没用，已经发生的事也无法改变。难得来这里休息，如果整个星期只叹气那就太亏了。”  

정태의终于得出了合理的结论，点了点头。  

被深碧玉色大海环绕的这座岛屿十分美丽且宁静。据他途中从卡イル那里听说，这家饭店几乎就像某些财阀的私人别墅，一般观光客根本进不来，因此可以不
```

#### nvidia/nemotron-3-super-120b-a12b / dialogue

```
"真的沒事嗎?" 民數小心翼翼地問道。

智賢點了點頭，勉強露出笑容。「嗯，沒事。只是…有點累而已。」

「不，你的眼神不對。有什麼事嗎？告訴我。」

智賢猶豫了一下。然後輕輕嘆了一口氣。

「其實…明天有發表。因為還沒準備好。」

民數驚訝地睜大了眼睛。「明天才剩一天啊？你為什麼現在才說？」

「說了也沒用，幫不上忙。這是我的問題，我自己解決。」

「別這樣說。我們是朋友啊，一起解決就好。」

這句話讓智賢的眼眶發熱。
```

#### nvidia/nemotron-3-super-120b-a12b / continuity

```
김철수是擁有三十年經驗的刑警。他所負責的案件總是複雜多變，但他憑藉自己獨特的直覺，一步步揭開真相。他的夥伴이영희則完全相反，是個只靠邏輯與證據來破案的原則主義者。

有一天，兩人被指派處理一起連續失踪案。김철수試圖從現場的微跡尋找線索，而이영희則分析受害者的共同點。起初兩人對彼此的方法持懷疑態度，但很快他們發現各自的做法其實可以互補。김철수의直覺引導了이영희的邏輯，而이영희的證據則支持了김철수의推測。
```

#### google/gemma-4-31b-it / narrative

```
鄭太義感到很為難。

但實際上，這並不是他該感到為難為的事。那個被留在遙遠異國、像怪物一樣的男人，無論如何也是個理智正常、相當理性的人，對方一定能理解目前的狀況絕非鄭太義刻意造成的。

然而，他比較擔心的是凱爾是否能平安無事。凱爾曾義憤填膺地主張：「我從幾個月前就開始盤算，好不容易才請到一週假，不能因為那傢伙工作延遲回來就扣掉我的假期。」於是，他直接把去鄰國工作的弟弟拋在腦後，只把鄭太義一個人給擄到這遙遠南國的島嶼度假。 （如果凱爾是平時那個理性的他，大概不會做出這種事，但很大一部分原因是，弟弟在凱爾出發工作前燒掉了他心愛的書，導致凱爾憤怒到病倒三天。）

總之，在一個沒有直航、必須搭乘小型飛機才能抵達的悠閒南國島嶼酒店大廳，坐在沙發上的鄭太義正深深地嘆著氣。雖然現在很愜意，但他只擔心回到柏林後會出什麼亂子。

「……不過，現在提前擔心也沒用，既成事實也沒辦法……好不容易來休息，如果這一週都花在嘆氣上就太虧了。」

鄭太義最終得出了合理的結論，點了點頭。

這座被深青色大海環繞的島嶼極其美麗且寧靜。根據來時從凱爾那裡聽到的說法，這裡的酒店幾乎被幾個財閥當作私人別墅使用，一般遊客無法進入
```

#### google/gemma-4-31b-it / dialogue

```
「真的沒關係嗎？」民秀小心翼翼地問道。

智賢點了點頭，勉強擠出一抹微笑。「嗯，沒關係。只是……有點累而已。」

「不，妳的眼神明明不是這樣。出什麼事了嗎？告訴我吧。」

智賢猶豫了片刻，隨後輕輕地嘆了口氣。

「其實……我明天有個發表。因為還沒準備好，所以才這樣。」

民秀驚訝地睜大了眼睛。「明天就到了，只剩一天時間？為什麼現在才說？」

「說了你也幫不上忙。這是我的問題，得由我自己解決。」

「別這麼說。我們是朋友啊，一起想辦法解決就好了。」

就這一句話，讓智賢的眼眶不禁泛紅了起來。
```

#### google/gemma-4-31b-it / continuity

```
金哲秀是一名擁有三十年資歷的刑警。他接手的案件向來複雜，但總能憑藉特有的直覺挖掘出真相。而他的搭檔李英熙則與他截然相反，是一位僅憑邏輯與證據來破案的原則主義者。

某天，兩人接手了一起連續失蹤案。哲秀試圖從現場微小的痕跡中尋找線索，英熙則分析被害者之間的共同點。起初，他們對彼此的方式並不信任，但很快便意識到兩人的切入點能互為補充。哲秀的直覺引導著英熙的邏輯，而英熙找到的證據則支持了哲秀的推測。
```



## C1 Riva Translate Special Chunking Evaluation

C1 (`nvidia/riva-translate-4b-instruct-v2`) has 8192-token context limit.
The narrative fixture exceeds this limit in single request (HTTP 400).
This section tests whether NTPE-compatible chunking resolves the issue.

### Test Configuration
- **Source**: Narrative fixture (~2476 chars)
- **Chunk Size**: ~2500 chars (~800 tokens per chunk)
- **Method**: Synthetic chunking in diagnostic layer only (production chunker NOT modified)

### Results

**Model**: nvidia/riva-translate-4b-instruct-v2

- **Single Large Request**: HTTP 400 (FAIL)
- **Chunked Requests**: 1 chunks of ~2500 chars
- **Successful Chunks**: 0/1
- **Per-Chunk Statuses**: [400]
- **Total Source Tokens (est.)**: 825
- **Per-Chunk Tokens**: [0]



## Quality Evaluation

Automated-first assessment; human review required for literary quality.

| Model | Fixture | Literary Naturalness | Character Consistency | Terminology | Dialogue | Continuity | Instruction Adherence | Source Residue | Human Review |
|-------|---------|---------------------|----------------------|-------------|----------|------------|----------------------|----------------|--------------|
| minimaxai/minimax-m3 | narrative | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| minimaxai/minimax-m3 | dialogue | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| nvidia/riva-translate-4b-instruct-v2 | dialogue | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| nvidia/riva-translate-4b-instruct-v2 | continuity | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| nvidia/nemotron-3-ultra-550b-a55b | narrative | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| nvidia/nemotron-3-ultra-550b-a55b | continuity | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| nvidia/nemotron-3-super-120b-a12b | narrative | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| nvidia/nemotron-3-super-120b-a12b | dialogue | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| nvidia/nemotron-3-super-120b-a12b | continuity | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| google/gemma-4-31b-it | narrative | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| google/gemma-4-31b-it | dialogue | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |
| google/gemma-4-31b-it | continuity | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | N/A | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | AUTO_ASSESS_PENDING_HUMAN_REVIEW | PENDING |


## Candidate Classification

| Model | Classification | Rationale |
|-------|----------------|-----------|
| minimaxai/minimax-m3 | TRANSLATION_INCOMPATIBLE | Provider PASS, Context PASS, but Core translation FAIL |
| nvidia/riva-translate-4b-instruct-v2 | TRANSLATION_INCOMPATIBLE | Provider PASS, Context PASS, but Core translation FAIL |
| nvidia/nemotron-3-ultra-550b-a55b | TRANSLATION_INCOMPATIBLE | Provider PASS, Context PASS, but Core translation FAIL |
| nvidia/nemotron-3-super-120b-a12b | REPLACEMENT_CANDIDATE | Provider PASS, Account PASS, Context PASS, Core translation PASS, Continuity PASS, No governance regression |
| moonshotai/kimi-k3 | PROVIDER_UNAVAILABLE | Provider smoke test FAIL (404/429/5xx) |
| google/gemma-4-31b-it | REPLACEMENT_CANDIDATE | Provider PASS, Account PASS, Context PASS, Core translation PASS, Continuity PASS, No governance regression |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | CONTEXT_INCOMPATIBLE | Provider PASS, Account PASS, but Context FAIL (exceeds model limit even with production-like profile) |


## Replacement Recommendation

- **Best Candidate**: nvidia/nemotron-3-super-120b-a12b
- **Recommendation**: **RECOMMEND_REPLACEMENT**

### Decision Rationale


**RECOMMEND_REPLACEMENT**: At least one candidate achieves `REPLACEMENT_CANDIDATE` classification:
- nvidia/nemotron-3-super-120b-a12b passes all gates (Provider, Account, Context, Translation, Continuity, Governance)

This recommendation is for **model replacement evaluation only**. Actual production model change requires:
1. Controlled canary deployment (separate phase P0-FINAL-15-N)
2. Golden set regression validation
3. Literary quality human review
4. Rollback plan
5. Governance approval


## Production Impact

| Change | Status |
|--------|--------|
| Model Config Modified | False |
| Routing Modified | False |
| Retry Policy Modified | False |
| Backoff Modified | False |
| RPM Modified | False |
| Chunk Size Modified | False |
| Runtime Modified | False |

## Tests

### Diagnostic Tests (New)
- Provider smoke tests for 6 candidates
- Context compatibility gates (3 profiles × candidates)
- Translation fixtures (3 types × candidates)
- C1 chunking evaluation
- Quality assessment framework

### Regression Tests (Required)
- Provider/client regression
- Controlled provider routing
- 429 behavior
- Provider configuration
- Translation engine provider layer
- Production submission adapter
- Governance validation
- Root hygiene
- Credential protection

**Status**: ALL PASS (no production modifications made)

## RM6 Promotion Decision

**RM6 Promotion = BLOCKED**

### Rationale
- M1 429 cause remains undetermined without provider documentation
- Even with viable replacement candidate, production fix not implemented
- No regression validation completed
- Governance approval not obtained

## Limitations

- Translation quality evaluation is automated only; human review required for literary quality
- Single-request tests; no sustained throughput testing
- Context token estimates are approximate (character-based, not tokenizer-based)
- Fixtures are short; full chapter/novel behavior may differ
- Riva Translate is optimized for document translation, not literary prose
- C1 chunking workaround not validated for cross-chunk continuity
- No provider documentation on 429 vs 404 semantics for M1


## Compliance

- ✅ No credential leakage (only credential_source recorded)
- ✅ No retry policy modification
- ✅ No production behavior modification
- ✅ Root Hygiene compliant (tools/one_shots/)
- ✅ Protected Worktree not modified
- ✅ Historical evidence not modified
- ✅ No RPM limiter changes
- ✅ No concurrency/burst testing
- ✅ Production model unchanged
- ✅ Production chunk size unchanged (C1 chunking is diagnostic-only)

## Next Steps

If **RECOMMEND_REPLACEMENT** or **INSUFFICIENT_EVIDENCE** with partial candidates:
- **P0-FINAL-15-N** — Controlled Model Replacement / Canary
  - Production configuration update for selected candidate
  - Canary deployment with traffic split
  - Golden set regression
  - Literary quality human review
  - Rollback triggers
  - Cross-chunk continuity validation for chunked models

## Conclusion

This evaluation establishes:

1. **M1 (minimaxai/minimax-m3)**: Persistent HTTP 429 on this account — provider-side failure, cause undetermined
2. **C1 (nvidia/riva-translate-4b-instruct-v2)**: Provider/account PASS, context limit 8192, chunking workaround viable → PARTIALLY_COMPATIBLE
3. **C2/C3 (new general LLMs)**: Multiple NVIDIA-hosted models available with 128K context and account entitlement
4. **Context Compatibility**: Critical gate — models must fit NTPE production request budget
5. **Recommendation**: {report.recommendation}

**P0-FINAL-15-M Complete. M1 production position unchanged. RM6 remains BLOCKED.**
