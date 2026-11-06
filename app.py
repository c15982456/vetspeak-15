import io, json, os, random, re, time
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import streamlit as st
from gtts import gTTS
import google.generativeai as genai

st.set_page_config(page_title="VetSpeak 15 - 高階特訓", page_icon="🩺", layout="centered")

# ---------- 高階 C1 臨床內建題庫 ----------
builtin_library = {
    "MMVD 早期介入與 EPIC 試驗": {
        "english_text": "In the management of canine Myxomatous Mitral Valve Disease, the EPIC trial revolutionized our approach by demonstrating the clear efficacy of pimobendan in prolonging the preclinical phase. However, accurately identifying Stage B2 is paramount. We must rely on stringent echocardiographic criteria—specifically, an LA to Ao ratio greater than 1.6, and a normalized left ventricular internal dimension in diastole (LVIDDN) exceeding 1.7. Initiating positive inotropes prematurely in truly stable Stage B1 dogs offers no proven hemodynamic benefit and may unnecessarily burden the owners financially. Therefore, meticulous echocardiographic staging remains the absolute cornerstone of our clinical decision-making.",
        "vocab": [{"term": "preclinical phase", "zh": "臨床前期"}, {"term": "hemodynamic benefit", "zh": "血流動力學益處"}],
        "chinese_translation": "在管理犬 MMVD 時，EPIC 試驗證明 pimobendan 能延長臨床前期。然而準確識別 B2 期至關重要（LA:Ao>1.6, LVIDDN>1.7）。嚴謹的超音波分期是臨床決策的基石。",
        "sample_answer": "Accurate staging is essential to avoid premature initiation of pimobendan. (準確分期對於避免過早投藥至關重要。)",
        "qa_question": "How do you handle borderline echo parameters?",
        "quiz": {"question": "Which finding justifies pimobendan?", "options": ["LA:Ao < 1.5", "LVIDDN > 1.7", "Murmur alone", "Normal size"], "answer": "LVIDDN > 1.7", "explanation": "EPIC標準需要 LVIDDN > 1.7"}
    }
}

# ---------- 設定與初始化 ----------
def secret(k, default=None):
    try:
        return st.secrets[k]
    except Exception:
        return os.getenv(k, default)

API_KEY = secret("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-3.8-flash")
else:
    model = None

# 資料存取區
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)
LOG_F, VOC_F, CUSTOM_LIB_F = DATA / "log.csv", DATA / "vocab.json", DATA / "custom_library.json"
LOG_COLS = ["日期", "主題", "訓練方式", "分鐘", "自評"]

specialties = ["小動物心臟學", "小動物眼科學", "小動物臨床營養學", "小動物內科學", "小動物腫瘤學", "急診與重症", "麻醉與疼痛管理"]

tasks = [
    {"name": "🗣️ 影子跟讀 (Shadowing)", "desc": "聽懂發音後，比講者慢 0.5 秒跟著唸。最後可錄下自己版本。"},
    {"name": "🎤 Q&A 實戰模擬", "desc": "針對下方『聽眾提問』，給自己 2 分鐘全英文口頭回答並錄音。"},
    {"name": "📝 臨床口頭摘要", "desc": "用自己的話濃縮內容，做 30 秒精華報告並錄音。"},
]

def load_log():
    return pd.read_csv(LOG_F) if LOG_F.exists() else pd.DataFrame(columns=LOG_COLS)
def load_vocab():
    return json.loads(VOC_F.read_text("utf-8")) if VOC_F.exists() else {}
def save_vocab(v):
    VOC_F.write_text(json.dumps(v, ensure_ascii=False, indent=1), "utf-8")
def load_custom_lib():
    return json.loads(CUSTOM_LIB_F.read_text("utf-8")) if CUSTOM_LIB_F.exists() else {}

# 系統啟動時，合併「內建題庫」與「你的專屬題庫」
vocab, log, custom_library = load_vocab(), load_log(), load_custom_lib()
all_library = {**builtin_library, **custom_library}

# ---------- AI 與語音核心 ----------
@st.cache_data(show_spinner=False)
def tts(text, slow=False): 
    fp = io.BytesIO()
    gTTS(text=text, lang="en", tld="us", slow=slow).write_to_fp(fp)
    return fp.getvalue()

def coach(audio_bytes, c, task):
    prompt = f"你是高階獸醫英文口說教練。講稿：{c['english_text']}\n請聽錄音並給予：1.逐字稿 2.優點3點 3.缺點3點 4.示範說法(含中文)。"
    r = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_bytes}])
    return r.text

# ---------- 狀態管理 ----------
S = st.session_state
for k in ["content", "task", "fb", "timer_end", "seen", "qn", "quiz_done", "rv"]:
    S.setdefault(k, None if k not in ["seen", "qn", "quiz_done", "rv"] else ([] if k == "seen" else (0 if k == "qn" else False)))

def start_training(c, choice):
    S.content, S.fb, S.timer_end, S.quiz_done = c, None, None, False
    S.qn += 1
    S.task = random.choice(tasks) if choice == "隨機" else next(t for t in tasks if t["name"] == choice)
    S.seen.append(c["title"])

# ---------- 介面區 ----------
st.title("🩺 VetSpeak 15 - 雙引擎高階版")

# 【亮點】多了一個「⚙️ 題庫管理」的分頁
t1, t2, t3, t4 = st.tabs(["🚀 今日特訓", "🔁 單字複習", "📈 學習紀錄", "⚙️ 題庫管理"])

with t1:
    choice = st.radio("訓練方式", ["隨機"] + [t["name"] for t in tasks], horizontal=True)
    
    # 修改為從合併後的 all_library 抽題
    if st.button(f"🚀 抽取本地題庫 (共 {len(all_library)} 題，秒開)", use_container_width=True, type="primary"):
        k = random.choice(list(all_library.keys()))
        data = all_library[k]
        data["title"] = f"本地：{k}"
        start_training(data, choice)

    # --- 渲染教材 ---
    c = S.content
    if c:
        st.divider()
        st.subheader(c["title"])
        st.markdown(f"**🎯 訓練任務：{S.task['name']}**")
        st.write(S.task["desc"])
        if "Q&A" in S.task["name"]:
            st.warning(f"**🙋 聽眾提問：** {c['qa_question']}")

        speed = st.radio("語音播放速度", ["正常速度", "慢速拆解"], horizontal=True)
        st.audio(tts(c["english_text"], speed == "慢速拆解"), format="audio/mp3")
        
        if st.toggle("👂 盲聽模式（開啟後隱藏講稿）", value=False):
            st.caption("建議先純聽兩次，試著抓出主旨與專有名詞，再關閉本開關對照講稿。")
        else:
            st.info(c["english_text"])

        st.markdown("**💡 關鍵語塊（Lexical Chunks）**")
        for i, v in enumerate(c["vocab"]):
            col_word, col_btn = st.columns([5, 1])
            col_word.markdown(f"**{v['term']}** — {v['zh']}")
            have = v["term"] in vocab
            if col_btn.button("✓ 已加入" if have else "➕", key=f"voc_{S.qn}_{i}", disabled=have):
                vocab[v["term"]] = {"zh": v["zh"], "box": 0, "due": str(date.today())}
                save_vocab(vocab)
                st.rerun()
                
        with st.expander("👁️ 點我核對中文翻譯與示範解答"):
            st.write(c["chinese_translation"])
            st.markdown(f"**示範摘要：** {c['sample_answer']}")

        st.divider()
        st.markdown("### 🧠 隨堂小測驗")
        q = c["quiz"]
        st.write(q["question"])
        if not S.quiz_done:
            opts = list(q["options"])
            random.shuffle(opts)
            for opt in opts:
                if st.button(opt, use_container_width=True, key=f"q_{S.qn}_{opt}"):
                    S.quiz_done = True
                    S.quiz_ans = opt
                    st.rerun()
        else:
            if S.quiz_ans == q["answer"]:
                st.success(f"**Correct! 🎉**\n\n{q['explanation']}")
            else:
                st.error(f"**Incorrect. 💡** (正確答案是: {q['answer']})\n\n{q['explanation']}")
            if st.button("🔄 重新測驗", use_container_width=True):
                S.quiz_done = False
                st.rerun()

        st.divider()
        st.markdown("### 🎙️ 錄下你的口說並取得 AI 評分")
        rec = st.audio_input("錄音完成後，可點擊下方按鈕呼叫 AI 教練")
        if rec:
            if model and st.button("🤖 呼叫 AI 教練講評", type="primary", use_container_width=True):
                with st.spinner("AI 教練正在仔細聆聽..."):
                    try:
                        S.fb = coach(rec.getvalue(), c, S.task)
                    except Exception as e:
                        st.error(f"分析失敗，請確認 API。（{e}）")
        if S.fb:
            with st.container(border=True):
                st.markdown(S.fb)

# ----------------- 單字與紀錄區 -----------------
with t2:
    today = str(date.today())
    due = [k for k, v in vocab.items() if v["due"] <= today]
    st.subheader(f"📖 待複習字彙：{len(due)} 個")
    if not due:
        st.success("🎉 太棒了！今天沒有要複習的單字。")
    else:
        w = due[0]
        v = vocab[w]
        with st.container(border=True):
            st.markdown(f"<h2 style='text-align:center;'>{w}</h2>", unsafe_allow_html=True)
            st.audio(tts(w), format="audio/mp3")
            if not S.rv:
                if st.button("👁️ 顯示中文意思", use_container_width=True):
                    S.rv = True
                    st.rerun()
            else:
                st.markdown(f"<h3 style='text-align:center;'>{v['zh']}</h3>", unsafe_allow_html=True)
                a, b = st.columns(2)
                if a.button("😵 忘記了", use_container_width=True):
                    v["box"] = 0; v["due"] = str(date.today() + timedelta(days=1))
                    save_vocab(vocab); S.rv = False; st.rerun()
                if b.button("😎 記得很熟", type="primary", use_container_width=True):
                    v["box"] = min(v["box"] + 1, 4)
                    IV = [1, 3, 7, 14, 30]
                    v["due"] = str(date.today() + timedelta(days=IV[v["box"]]))
                    save_vocab(vocab); S.rv = False; st.rerun()

with t3:
    st.subheader("📊 我的學習履歷")
    st.dataframe(log.iloc[::-1], use_container_width=True, hide_index=True)

# ----------------- 全新：題庫管理後台 -----------------
with t4:
    st.subheader("⚙️ 專屬題庫管理後台")
    st.info("從 Gemini Advanced 產生的 JSON 直接貼在下方，系統會自動抓取並擴充你的專屬題庫！")
    
    new_json_text = st.text_area("📥 貼上 AI 產生的 JSON 內容：", height=200, placeholder='{\n  "新題目名稱": {\n    "english_text": "...",\n    ...\n  }\n}')

    if st.button("➕ 解析並新增至題庫", type="primary", use_container_width=True):
        if not new_json_text.strip():
            st.warning("請先貼上內容！")
        else:
            match = re.search(r'\{.*\}', new_json_text, re.DOTALL)
            if match:
                try:
                    new_data = json.loads(match.group(0))
                    custom_library.update(new_data)
                    CUSTOM_LIB_F.write_text(json.dumps(custom_library, ensure_ascii=False, indent=2), "utf-8")
                    st.success(f"🎉 成功新增！目前自訂題庫共 {len(custom_library)} 題。")
                    time.sleep(1)
                    st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"解析失敗，請確認格式。細節：{e}")
            else:
                st.error("找不到有效的 JSON 格式。")

    st.divider()
    st.markdown(f"**當前自訂題庫數量：{len(custom_library)} 題**")
    st.caption("⚠️ 雲端主機休眠時可能會清空自訂題庫，請務必定期下載備份，需要時再匯入即可。")
    
    col1, col2 = st.columns(2)
    with col1:
        if custom_library:
            st.download_button(
                label="💾 下載題庫備份",
                data=json.dumps(custom_library, ensure_ascii=False, indent=2).encode('utf-8'),
                file_name="my_vetspeak_library.json",
                mime="application/json",
                use_container_width=True
            )
    with col2:
        uploaded_file = st.file_uploader("📂 匯入題庫備份檔", type=['json'], label_visibility="collapsed")
        if uploaded_file is not None and st.button("開始匯入", use_container_width=True):
            try:
                uploaded_data = json.loads(uploaded_file.getvalue().decode("utf-8"))
                custom_library.update(uploaded_data)
                CUSTOM_LIB_F.write_text(json.dumps(custom_library, ensure_ascii=False, indent=2), "utf-8")
                st.success("✅ 備份匯入成功！")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error("匯入失敗，檔案格式不符。")
