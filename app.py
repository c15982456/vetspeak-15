import streamlit as st
import random
import time
from gtts import gTTS
import io
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import json
import re

st.set_page_config(page_title="VetSpeak 15 - AI 讀文獻", page_icon="🩺", layout="centered")

# --- 設定 Gemini API ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 讓系統自動抓取你的 API 金鑰目前支援的所有模型
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # 直接選取清單中第一個確定可用的模型來生成內容，徹底避開 404 錯誤
    model = genai.GenerativeModel(available_models[0])
else:
    st.error("請先在 Streamlit Secrets 中設定 GEMINI_API_KEY！")
    st.stop()

# --- 領域與任務設定 ---
specialties = [
    "小動物心臟科 (重點包含 MMVD, MINE 評分, 心衰竭)",
    "小動物眼科 (重點包含 白內障手術併發症, 青光眼, 葡萄膜炎)",
    "小動物臨床營養學 (重點包含 CKD 處方飼料, 腸胃道疾病, 肥胖管理)"
]

sources = ["AAHA Guidelines", "ACVIM Consensus Statements", "JVIM 最新發表文獻"]

tasks = [
    {"name": "🗣️ 影子跟讀 (Shadowing)", "desc": "先聽一次發音。接著戴上耳機，按下播放，講者說什麼慢 0.5 秒跟著唸，注意換氣與斷句。"},
    {"name": "🎤 Q&A 實戰模擬", "desc": "聽完這段 1 分鐘的引言後，給自己 2 分鐘全英文口頭發表你的觀點。"},
    {"name": "📝 臨床口頭摘要", "desc": "聽完語音後，用自己的話將這 1 分鐘的內容濃縮，向學員做 30 秒的精華報告。"}
]

# --- 狀態管理區 ---
if "specialty" not in st.session_state:
    st.session_state.specialty = None
if "source" not in st.session_state:
    st.session_state.source = None
if "task" not in st.session_state:
    st.session_state.task = None
if "generated_content" not in st.session_state:
    st.session_state.generated_content = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "learning_log" not in st.session_state:
    st.session_state.learning_log = pd.DataFrame(columns=["日期", "來源與領域", "訓練方式", "自我評分"])

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

# --- UI 介面區 ---
st.title("🏃 VetSpeak 15 - 最新文獻特訓")

tab1, tab2 = st.tabs(["🚀 今日特訓", "📈 學習紀錄"])

with tab1:
    if st.button("🚀 呼叫 AI 擷取最新文獻並生成任務"):
        st.session_state.specialty = random.choice(specialties)
        st.session_state.source = random.choice(sources)
        st.session_state.task = random.choice(tasks)
        st.session_state.quiz_submitted = False
        st.session_state.generated_content = None 
        
        with st.spinner(f"正在分析 {st.session_state.source} 中關於 {st.session_state.specialty} 的文獻..."):
            result = generate_medical_content(st.session_state.specialty, st.session_state.source)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.generated_content = result

    if st.session_state.generated_content:
        st.success("任務與文獻短講生成成功！")
        st.subheader(f"📌 來源：{st.session_state.source}")
