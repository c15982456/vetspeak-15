import json, re

PROMPT_TEMPLATE = """你是獸醫專科醫師，請為台灣獸醫師產生 3 篇國際研討會英文口說教材。
領域：＿＿＿　主題（可留空）：＿＿＿
只輸出純 JSON，不要 markdown 標籤。格式（以「題目名稱」為 key）：
{
  "題目名稱": {
    "reference": "第一作者, 期刊, 年份（必須是真實存在的文獻；不確定請寫「待查證」，不可編造）",
    "english_text": "約 130 字，TED 風格短句，每句 15-20 字內，開場有帶入感，結尾有 take-home message",
    "vocab": [{"term": "英文語塊", "zh": "中文"}],
    "chinese_translation": "繁中翻譯，句數須與英文完全相同、逐句對應",
    "sample_answer": "English sentence. (中文。)",
    "qa_question": "一個聽眾會問的英文問題",
    "search_keywords": "3-5 個 PubMed 關鍵字，逗號分隔",
    "verify_points": [{"claim": "最需查證的數字或絕對說法", "why": "原因"}],
    "quiz": {"question": "英文單選題", "options": ["A", "B", "C", "D"], "answer": "必須與其中一個選項完全相同", "explanation": "繁中詳解"}
  }
}"""

REQ = ["english_text", "vocab", "chinese_translation", "quiz"]
QREQ = ["question", "options", "answer", "explanation"]


def parse_pasted(txt):
    """把貼上的 AI 內容轉成題庫 dict；格式不對時丟出看得懂的 ValueError，而不是讓整個 App 當掉。"""
    m = re.search(r"[\[{].*[\]}]", txt or "", re.DOTALL)
    if not m:
        raise ValueError("找不到 JSON，請貼上 AI 回傳的完整內容。")
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 格式有誤（約第 {e.lineno} 行）：{e.msg}。可把這段錯誤貼回 AI，請它修正後重貼。")
    if isinstance(data, list):
        data = {d.get("title", f"自訂題 {i + 1}"): d for i, d in enumerate(data) if isinstance(d, dict)}
    elif isinstance(data, dict) and "english_text" in data:
        data = {data.get("title", "自訂題"): data}
    if not isinstance(data, dict) or not data:
        raise ValueError("內容必須是「題目名稱 → 內容」的 JSON。")
    for k, d in data.items():
        if not isinstance(d, dict):
            raise ValueError(f"「{k}」的內容不是物件。")
        miss = [f for f in REQ if f not in d]
        if miss:
            raise ValueError(f"「{k}」缺少欄位：{', '.join(miss)}")
        if not isinstance(d["quiz"], dict) or [f for f in QREQ if f not in d["quiz"]]:
            raise ValueError(f"「{k}」的 quiz 缺少欄位（需要 {', '.join(QREQ)}）")
        if not isinstance(d["quiz"]["options"], list) or len(d["quiz"]["options"]) < 2:
            raise ValueError(f"「{k}」的 quiz.options 需要至少 2 個選項")
    return data
