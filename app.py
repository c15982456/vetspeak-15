import streamlit as st
import random
import time
from gtts import gTTS
import io
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import json

st.set_page_config(page_title="VetSpeak 15 - AI 讀文獻", page_icon="🩺", layout="centered")

# 設定 Gemini API
# 確保你在 Streamlit Cloud 的 Secrets 設定了 GEMINI_API_KEY
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
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

# --- AI 生成邏輯 ---
def generate_medical_content(specialty, source):
    prompt = f"""
    你現在是一位獸醫內科專科醫師。請根據「{source}」中關於「{specialty}」的最新文獻或指引（如果不確定最新，請依據過去的經典發表模擬），
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
        # 嘗試清理可能的回傳格式，確保是乾淨的 JSON
        json_str = response.text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        return json.loads(json_str.strip())
    except Exception as e:
        return {"error": f"生成失敗，請再試一次。錯誤訊息：{e}"}

# --- UI 介面區 ---
st.title("🏃 VetSpeak 15 - 最新文獻特訓")

tab1, tab2 = st.tabs(["🚀 今日特訓", "📈 學習紀錄"])

with tab1:
    if st.button("🚀 呼叫 AI 擷取最新文獻並生成任務"):
        st.session_state.specialty = random.choice(specialties)
        st.session_state.source = random.choice(sources)
        st.session_state.task = random.choice(tasks)
        st.session_state.quiz_submitted = False
        st.session_state.generated_content = None # 清空舊內容
        
        with st.spinner(f"正在分析 {st.session_state.source} 中關於 {st.session_state.specialty} 的文獻..."):
            result = generate_medical_content(st.session_state.specialty, st.session_state.source)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.generated_content = result

    if st.session_state.generated_content:
        st.success("任務與文獻短講生成成功！")
        st.subheader(f"📌 來源：{st.session_state.source}")
        st.subheader(f"📌 領域：{st.session_state.specialty}")
        st.markdown(f"**🎯 訓練方式：{st.session_state.task['name']}**")
        st.write(st.session_state.task["desc"])
        
        st.divider()
        st.markdown("### 📖 今日特訓內容")
        
        content = st.session_state.generated_content
        text_to_read = content["english_text"]
        
        # 產生語音
        with st.spinner("🎧 正在生成講者語音，請稍候..."):
            tts = gTTS(text=text_to_read, lang='en', tld='us') 
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format='audio/mp3')
            
        st.info(text_to_read)
        st.markdown("**💡 關鍵語塊 (Lexical Chunks)：**")
        st.write(content["vocab"])
        
        with st.expander("👁️ 點我核對中文翻譯與示範解答"):
            st.markdown("**【中文翻譯】**")
            st.write(content["chinese_translation"])
            st.markdown("**【C1 程度示範解答 / 摘要】**")
            st.write(content["sample_answer"])
            
        st.divider()
        st.markdown("### 🧠 隨堂小測驗 (Pop Quiz)")
        quiz_data = content["quiz"]
        st.write(quiz_data["question"])
        
        user_choice = st.radio("請選擇最適合的答案：", quiz_data["options"], index=None, key=f"quiz_{st.session_state.specialty}")
        
        if st.button("📝 送出答案"):
            st.session_state.quiz_submitted = True
            
        if st.session_state.quiz_submitted:
            if user_choice == quiz_data["answer"]:
                st.success(f"**Correct! 🎉**\n\n{quiz_data['explanation']}")
            elif user_choice is not None:
                st.error(f"**Incorrect. 💡**\n\n{quiz_data['explanation']}")
            else:
                st.warning("請先選擇一個選項再送出喔！")
        
        st.divider()
        st.write("⏱️ **15 分鐘專注計時與打卡**")
        
        self_rating = st.slider("今天口說表現給自己打幾分？(1-5分)", min_value=1, max_value=5, value=3)
        
        if st.button("開始計時並記錄打卡"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            for percent_complete in range(100):
                time.sleep(9) 
                progress_bar.progress(percent_complete + 1)
                status_text.text(f"特訓進行中... {percent_complete + 1}%")
            
            st.balloons()
            st.success("🎉 今日 15 分鐘特訓完成！")
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            new_record = pd.DataFrame([{
                "日期": today_str,
                "來源與領域": f"{st.session_state.source} - {st.session_state.specialty}",
                "訓練方式": st.session_state.task["name"],
                "自我評分": f"{'⭐' * self_rating}"
            }])
            st.session_state.learning_log = pd.concat([st.session_state.learning_log, new_record], ignore_index=True)

with tab2:
    st.subheader("📊 我的學習履歷")
    if len(st.session_state.learning_log) == 0:
        st.info("目前還沒有紀錄，趕快去完成今天的任務吧！")
    else:
        st.dataframe(st.session_state.learning_log, use_container_width=True, hide_index=True)
