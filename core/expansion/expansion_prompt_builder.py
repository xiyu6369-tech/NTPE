from __future__ import annotations


class ExpansionPromptBuilder:
    """
    建立局部段落補足 Prompt。

    注意：
    這不是全文重翻，而是只針對偏短段落做補足式再翻譯。
    """

    def build(self, task: dict, *, file_name: str, chunk_index: int) -> dict:
        hints = "\n".join(f"- {h}" for h in task.get("hints", []))

        system_prompt = (
            "你是 NTPE 的出版級韓文小說譯文補足編輯。"
            "你的任務不是重寫整章，而是根據原文補足目前偏短的繁體中文譯文。"
            "你必須保留既有正確資訊，補回被省略的動作、心理、場景、比喻與停頓。"
            "不可新增原文沒有的劇情，不可改變人名與術語。"
            "只輸出補足後的完整繁體中文段落，不要解釋。"
        )

        user_prompt = f"""【任務】
這是段落級補足，不是全文重翻。

【檔案】
{file_name}

【Chunk】
{chunk_index}

【段落編號】
P{task['paragraph_index']:03d}

【原文段落】
{task['source']}

【目前譯文】
{task['current_translation']}

【問題】
目前譯文偏短，可能省略原文資訊。
source_length={task['source_length']}
translation_length={task['translation_length']}
ratio={task['ratio']}

【補足重點】
{hints}

【輸出要求】
- 只輸出補足後的完整繁體中文段落。
- 不要輸出段落編號。
- 不要輸出說明。
- 不可摘要。
- 不可新增原文沒有的劇情。
- 譯文需自然、流暢、有台灣繁體中文出版小說語感。
"""

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "prompt_mode": "paragraph_expansion",
        }
