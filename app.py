import re # 請確認程式碼最上方有 import re，如果沒有請加上去

# --- AI 生成邏輯 (強化過濾版) ---
def generate_medical_content(specialty, source):
    prompt = f"""
    你現在是一位獸醫內科專科醫師。請根據「{source}」中關於「{specialty}」的最新文獻或指引，
    撰寫一段長度約 1 分鐘（約 130-150 字）的英文研討會短講講稿。這是一段口語化的演講內容，請加入學術轉折語（Signposting）。
    
    請務必以純 JSON 格式回傳，格式必須嚴格如下，不要加入任何 Markdown 標記或額外說明：
    {{
        "english_text": "英文講稿內容...",
        "vocab": "挑出 3-4 個高階醫學單字或學術語塊，格式如：word (中文), word (中文)",
        "chinese_translation": "英文講稿的精確繁體中文翻譯",
        "sample_answer": "針對此講稿的一句話高階總結，包含英文與繁體中文，格式如：English sentence. (中文翻譯。)",
        "quiz": {{
            "question": "根據講稿內容出一題英文單選題",
            "options": ["選項 A", "選項 B", "選項 C", "選項 D"],
            "answer": "正確的選項文字",
            "explanation": "繁體中文的詳解"
        }}
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        # 使用正規表達式強制抓取 {} 包住的 JSON 內容，忽略前後多餘文字
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            return {"error": "生成失敗，AI 未回傳正確的格式，請再點擊一次按鈕。"}
    except Exception as e:
        return {"error": f"發生錯誤，請再試一次。詳細錯誤訊息：{e}"}
