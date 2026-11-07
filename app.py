import io, json, os, random, re, time
import difflib
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote_plus
import pandas as pd
import streamlit as st
from gtts import gTTS
import google.generativeai as genai

st.set_page_config(page_title="VetSpeak 15 - 終極特訓", page_icon="🩺", layout="centered")

# ---------- 高階 C1 臨床題庫 (All-in-One 內建，免額外檔案) ----------
builtin_library = {
    "MMVD 早期介入與 EPIC 試驗": {
        "reference": "Keene BW, et al. ACVIM consensus guidelines. J Vet Intern Med. 2019.",
        "english_text": "In managing canine Myxomatous Mitral Valve Disease, the EPIC trial is a game-changer. It clearly proves that pimobendan prolongs the preclinical phase. But accurately identifying Stage B2 is vital. We must rely on strict echo criteria. Specifically, the LA to Ao ratio must be over 1.6. Also, the normalized left ventricular dimension must exceed 1.7. Starting inotropes in stable Stage B1 dogs offers no real benefit. It only adds financial stress to the owners. Thus, meticulous echo staging remains our absolute cornerstone.",
        "vocab": [
            {"term": "preclinical phase", "zh": "臨床前期/無症狀期"},
            {"term": "positive inotropes", "zh": "正性肌力藥物"},
            {"term": "meticulous echocardiographic staging", "zh": "嚴謹的超音波分期"}
        ],
        "chinese_translation": "在管理犬 MMVD 時，EPIC 試驗是個轉捩點。它明確證明 pimobendan 能延長臨床前期。但準確識別 B2 期至關重要。我們必須依賴嚴格的超音波標準。具體來說，LA:Ao 必須大於 1.6。同時，標準化左心室內徑必須超過 1.7。在穩定的 B1 期犬隻身上開始使用正性肌力藥物沒有實質益處。它只會增加飼主的財務壓力。因此，嚴謹的超音波分期仍然是我們的絕對基石。",
        "sample_answer": "Accurate staging using EPIC criteria is essential to avoid premature initiation of pimobendan in B1 dogs. (使用 EPIC 標準進行準確分期，對於避免在 B1 期過早投藥至關重要。)",
        "qa_question": "How do you handle cases where the LA:Ao is 1.65 but the LVIDDN is only 1.6?",
        "quiz": {
            "question": "Which echocardiographic finding justifies initiating pimobendan?",
            "options": ["LA:Ao ratio below 1.5", "LVIDDN exceeding 1.7", "Murmur alone", "Normal heart size"],
            "answer": "LVIDDN exceeding 1.7",
            "explanation": "根據 EPIC 試驗標準，進入 B2 期的條件包含 LA:Ao > 1.6 以及 LVIDDN > 1.7。"
        }
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

DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)
LOG_F, VOC_F, CUSTOM_LIB_F, VER_F = DATA / "log.csv", DATA / "vocab.json", DATA / "custom_library.json", DATA / "verified.json"
LOG_COLS = ["日期", "主題", "訓練方式", "分鐘", "自評"]
IV = [1, 3, 7, 14, 30] 

specialties = ["小動物心臟學", "小動物眼科學", "小動物臨床營養學", "小動物內科學", 
               "小動物腫瘤學", "急診與重症", "麻醉與疼痛管理", "皮膚科"]

tasks = [
    {"name": "🗣️ 影子跟讀 (Shadowing)", "desc": "先用慢速聽一次。戴上耳機比講者慢 0.5 秒跟著唸。最後可錄下自己版本。"},
    {"name": "🎤 Q&A 實戰模擬", "desc": "針對下方『聽眾提問』，給自己 2 分鐘全英文口頭回答並錄音。"},
    {"name": "📝 臨床口頭摘要", "desc": "不看稿，用自己的話濃縮內容，做 30 秒精華報告並錄音。"},
]

LEVELS = {
    "🌱 入門 (短句、白話)": "撰寫約 90-110 字的英文短講。每句絕對不可超過 15 個字。用極簡單句型與常見字，避免複雜子句。語氣像向剛畢業的學弟妹口頭說明。",
    "🔥 進階 (研討會TED風)": "撰寫約 130-150 字的英文研討會短講。【極度重要】為了聽力跟讀，請使用「TED Talk 演講風格」的短句。每句話盡量控制在 15-20 個英文字以內，多用主動語態，斷句要非常清晰。"
}

# ---------- 資料存取 ----------
def load_log(): return pd.read_csv(LOG_F) if LOG_F.exists() else pd.DataFrame(columns=LOG_COLS)
def load_vocab(): return json.loads(VOC_F.read_text("utf-8")) if VOC_F.exists() else {}
def save_vocab(v): VOC_F.write_text(json.dumps(v, ensure_ascii=False, indent=1), "utf-8")
def load_custom_lib(): return json.loads(CUSTOM_LIB_F.read_text("utf-8")) if CUSTOM_LIB_F.exists() else {}
def load_ver(): return json.loads(VER_F.read_text("utf-8")) if VER_F.exists() else []
def save_ver(v): VER_F.write_text(json.dumps(v, ensure_ascii=False), "utf-8")

# ---------- 核心功能 ----------
@st.cache_data(show_spinner=False)
def tts(text, slow=False): 
    fp = io.BytesIO()
    gTTS(text=text, lang="en", tld="us", slow=slow).write_to_fp(fp)
    return fp.getvalue()

def generate(specialty, topic, seen, level):
    prompt = f"""你是一位獸醫專科醫師，準備國際研討會英文口說教材。
領域：{specialty}。{"指定主題：" + topic if topic else "請自選一個臨床議題，避開最常見的基礎疾病。"}
避免重複主題：{seen[-10:] or "無"}。

{LEVELS[level]}
要求：開場要有帶入感，結尾要有 Take-home message。內容符合主流指引 (AAHA, ACVIM等)。

請務必以純 JSON 格式回傳 (不要加 markdown 標籤)：
{{
    "title": "繁中主題名",
    "reference": "文獻出處（如：第一作者, 期刊名, 年份）",
    "english_text": "英文講稿內容...",
    "vocab": [
        {{"term": "英文語塊", "zh": "繁中解釋"}},
        {{"term": "英文語塊", "zh": "繁中解釋"}},
        {{"term": "英文語塊", "zh": "繁中解釋"}}
    ],
    "chinese_translation": "精確繁中翻譯",
    "sample_answer": "一句高階總結，格式：English sentence. (中文翻譯。)",
    "qa_question": "一個進階的聽眾英文提問",
    "search_keywords": "3-5個可於PubMed搜尋的英文關鍵字(逗號分隔)",
    "verify_points": [
        {{"claim": "講稿中最需要查證的數字或絕對說法", "why": "為什麼要查證"}}
    ],
    "quiz": {{
        "question": "根據講稿出一題英文單選題",
        "options": ["選項 A", "選項 B", "選項 C", "選項 D"],
        "answer": "正確的選項文字（必須完全一致）",
        "explanation": "繁中詳解"
    }}
}}
"""
    r = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    return json.loads(r.text)

def coach(audio_bytes, c, task):
    prompt = f"""你是高階獸醫英文口說教練。學員目標是能流暢參與國際研討會。
參考講稿：{c['english_text']}
今天的訓練模式：{task['name']}；提問是：{c.get('qa_question', '')}
請聆聽學員的錄音，並用繁體中文 Markdown 格式回覆：
1. **🗣️ 學員逐字稿 (Transcript)**
2. **🌟 值得稱讚的 3 點**
3. **🛠️ 最該改進的 3 點** (明確指出錄音中哪裡講錯)
4. **🚀 教練升級版說法**
"""
    r = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_bytes}])
    return r.text

def sents(t): return [x for x in re.split(r"(?<=[.?!])\s+", t.strip()) if x]
def toks(t): return re.findall(r"[a-z0-9']+", t.lower().replace("’", "'"))

def listening_lab(c):
    en = sents(c["english_text"])
    zh = [x for x in re.split(r"(?<=[。！？])", c["chinese_translation"]) if x.strip()]
    with st.expander("🎧 逐句精聽與聽寫（聽不懂先從這裡開始）"):
        i = st.select_slider("選擇句號", options=list(range(1, len(en) + 1)), key=f"sl{S.qn}") - 1
        st.caption("慢速聽寫"); st.audio(tts(en[i], True), format="audio/mp3")
        if st.toggle("👁️ 顯示這句英文", key=f"en{S.qn}_{i}"):
            st.write(en[i])
        typed = st.text_input("✍️ 聽寫：把聽到的打在這裡", key=f"dic{S.qn}_{i}")
        if typed:
            a, b = toks(en[i]), toks(typed)
            acc = difflib.SequenceMatcher(None, a, b).ratio()
            (st.success if acc >= .9 else st.warning)(f"正確率 {acc:.0%}")

# ---------- 狀態與合併題庫 ----------
S = st.session_state
for k in ["content", "task", "fb", "timer_end", "seen", "qn", "quiz_done", "rv"]:
    S.setdefault(k, None if k not in ["seen", "qn", "quiz_done", "rv"] else ([] if k == "seen" else (0 if k == "qn" else False)))

vocab, log, custom_library = load_vocab(), load_log(), load_custom_lib()
all_library = {**builtin_library, **custom_library}

def start_training(c, choice):
    S.content, S.fb, S.timer_end = c, None, None
    S.quiz_done = False
    S.qn += 1
    S.task = random.choice(tasks) if choice == "隨機" else next(t for t in tasks if t["name"] == choice)
    S.seen.append(c.get("title", ""))

# ---------- 介面區 ----------
st.title("🩺 VetSpeak 15 - 雙引擎高階版")
t1, t2, t3, t4 = st.tabs(["🚀 今日特訓", "🔁 單字複習", "📈 學習紀錄", "⚙️ 題庫管理"])

with t1:
    with st.expander("⚙️ 訓練設定 (AI 生成模式適用)", expanded=False):
        specialty = st.selectbox("專科領域", specialties)
        topic = st.text_input("指定主題 (留空交由AI隨機)", placeholder="例如：犬心房顫動")
        level = st.radio("講稿難度", list(LEVELS.keys()), index=1, horizontal=True)
    
    choice = st.radio("訓練方式", ["隨機"] + [t["name"] for t in tasks], horizontal=True)
    
    c1, c2 = st.columns(2)
    if c1.button(f"🚀 抽取本地題庫 (共 {len(all_library)} 題，秒開)", use_container_width=True, type="primary"):
        k = random.choice(list(all_library.keys()))
        data = all_library[k]
        data["title"] = f"經典：{k}"
        start_training(data, choice)
        
    if c2.button("🤖 AI 寫新講稿 (需稍候)", use_container_width=True):
        if not model:
            st.error("請先設定 GEMINI_API_KEY！")
        else:
            with st.spinner("AI 正在查閱文獻並撰寫講稿... (若轉圈卡住，強烈建議使用『題庫管理』手動擴充)"):
                try:
                    r = generate(specialty, topic, S.seen, level)
                    r["title"] = f"AI：{r['title']}"
                    start_training(r, choice)
                except Exception as e:
                    st.error(f"API 生成失敗。可能遇到免費額度限制 (429)，請至「⚙️ 題庫管理」手動貼上。 (錯誤: {e})")

    # --- 渲染教材 ---
    c = S.content
    if c:
        st.divider()
        st.subheader(c["title"])
        
        if c.get("reference"):
            st.markdown(f"📚 **文獻來源：** *{c['reference']}*")
            
        st.markdown(f"**🎯 訓練任務：{S.task['name']}**")
        if "Q&A" in S.task["name"]:
            st.warning(f"**🙋 聽眾提問：** {c.get('qa_question', '')}")

        speed = st.radio("語音播放速度", ["正常速度", "慢速拆解"], horizontal=True)
        st.audio(tts(c["english_text"], speed == "慢速拆解"), format="audio/mp3")
        
        if st.toggle("👂 盲聽模式（開啟後隱藏講稿）", value=False):
            st.caption("建議先純聽兩次，抓出主旨再關閉開關對照講稿。")
        else:
            st.info(c["english_text"])

        # Claude's 逐句精聽功能
        listening_lab(c)

        st.markdown("**💡 關鍵語塊（Lexical Chunks）**")
        for i, v in enumerate(c["vocab"]):
            col_word, col_btn = st.columns([5, 1])
            col_word.markdown(f"**{v['term']}** — {v['zh']}")
            have = v["term"] in vocab
            if col_btn.button("✓ 已加入" if have else "➕", key=f"voc_{S.qn}_{i}", disabled=have):
                vocab[v["term"]] = {"zh": v["zh"], "box": 0, "due": str(date.today())}
                save_vocab(vocab)
                st.rerun()
                
        with st.expander("👁️ 中文翻譯與查證"):
            st.write(c["chinese_translation"])
            st.markdown(f"**示範摘要：** {c.get('sample_answer', '')}")
            if c.get("search_keywords"):
                kw = c["search_keywords"]
                st.markdown(f"[🔎 在 PubMed 搜尋驗證此主題](https://pubmed.ncbi.nlm.nih.gov/?term={quote_plus(kw)})")

        # 恢復滿版大按鈕測驗區
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
        st.markdown("### 🎙️ 錄下你的口說並取得教練評分")
        rec = st.audio_input("錄音完成後，可點擊下方按鈕呼叫 AI 教練")
        if rec:
            if model and st.button("🤖 呼叫 AI 教練講評", type="primary", use_container_width=True):
                with st.spinner("AI 教練正在仔細聆聽..."):
                    try:
                        S.fb = coach(rec.getvalue(), c, S.task)
                    except Exception as e:
                        st.error(f"分析失敗，請確認錄音或 API。（{e}）")
        if S.fb:
            with st.container(border=True):
                st.markdown(S.fb)

        st.divider()
        st.markdown("### ⏱️ 15 分鐘專注計時與打卡")
        if st.button("開始計時", use_container_width=True):
            S.timer_end = time.time() + 900
            
        if S.timer_end:
            left = int(S.timer_end - time.time())
            if left > 0:
                st.progress(1 - left / 900, text=f"⏱️ 訓練進行中... 剩餘 {left // 60:02d}:{left % 60:02d}")
                time.sleep(1)
                st.rerun()
            else:
                st.success("⏰ 15 分鐘專注訓練達成！")
                
        rating = st.slider("今天口說表現給自己打幾分？", 1, 5, 3)
        if st.button("✅ 結束今日任務並打卡", type="primary", use_container_width=True):
            mins = max(1, round((time.time() - (S.timer_end - 900)) / 60)) if S.timer_end else 0
            row = pd.DataFrame([[str(date.today()), c["title"], S.task["name"], mins, "⭐" * rating]], columns=LOG_COLS)
            pd.concat([log, row], ignore_index=True).to_csv(LOG_F, index=False)
            S.timer_end = None
            log = load_log()
            st.balloons()
            st.success("🎉 已成功記錄！")

with t2:
    today = str(date.today())
    due = [k for k, v in vocab.items() if v["due"] <= today]
    st.subheader(f"📖 待複習字彙：{len(due)} 個")
    if not due:
        st.success("🎉 太棒了！今天沒有要複習的單字。")
    else:
        w = due[0]; v = vocab[w]
        with st.container(border=True):
            st.markdown(f"<h2 style='text-align:center;'>{w}</h2>", unsafe_allow_html=True)
            st.audio(tts(w), format="audio/mp3")
            if not S.rv:
                if st.button("👁️ 顯示中文意思", use_container_width=True):
                    S.rv = True; st.rerun()
            else:
                st.markdown(f"<h3 style='text-align:center;'>{v['zh']}</h3>", unsafe_allow_html=True)
                a, b = st.columns(2)
                if a.button("😵 忘記了", use_container_width=True):
                    v["box"] = 0; v["due"] = str(date.today() + timedelta(days=1))
                    save_vocab(vocab); S.rv = False; st.rerun()
                if b.button("😎 記得很熟", type="primary", use_container_width=True):
                    v["box"] = min(v["box"] + 1, 4)
                    v["due"] = str(date.today() + timedelta(days=IV[v["box"]]))
                    save_vocab(vocab); S.rv = False; st.rerun()

with t3:
    st.subheader("📊 我的學習履歷")
    if log.empty:
        st.info("目前還沒有紀錄，趕快去完成今天的任務吧！")
    else:
        st.dataframe(log.iloc[::-1], use_container_width=True, hide_index=True)

with t4:
    st.subheader("⚙️ 專屬題庫管理後台 (推薦使用)")
    st.info("💡 解決 AI 跑不動的秘訣：在電腦用 Gemini Advanced 產生題庫，直接貼在這裡！免等待、免消耗免費 API 額度。")
    
    new_json_text = st.text_area(
        "📥 貼上 AI 產生的 JSON 內容：", 
        height=200, 
        placeholder='{
  "新題目名稱": {
    "reference": "文獻來源...",
    "english_text": "...",
    ...
  }
}'
    )

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
    
    col1, col2 = st.columns(2)
    with col1:
        if custom_library:
            st.download_button("💾 下載題庫備份", data=json.dumps(custom_library, ensure_ascii=False, indent=2).encode('utf-8'), file_name="my_vetspeak_library.json", mime="application/json", use_container_width=True)
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
