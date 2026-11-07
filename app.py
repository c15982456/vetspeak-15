import io, json, os, random, time
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import streamlit as st
from gtts import gTTS
import google.generativeai as genai

st.set_page_config(page_title="VetSpeak 15 - 高階特訓", page_icon="🩺", layout="centered")

# ---------- 高階 C1 臨床題庫 ----------
builtin_library = {
    "MMVD 早期介入與 EPIC 試驗": {
        "reference": "Keene BW, et al. ACVIM consensus guidelines for the diagnosis and treatment of myxomatous mitral valve disease in dogs. J Vet Intern Med. 2019;33(3):1127-1140.",
        "english_text": "In the management of canine Myxomatous Mitral Valve Disease, the EPIC trial revolutionized our approach by demonstrating the clear efficacy of pimobendan in prolonging the preclinical phase. However, accurately identifying Stage B2 is paramount. We must rely on stringent echocardiographic criteria—specifically, an LA to Ao ratio greater than 1.6, and a normalized left ventricular internal dimension in diastole (LVIDDN) exceeding 1.7. Initiating positive inotropes prematurely in truly stable Stage B1 dogs offers no proven hemodynamic benefit and may unnecessarily burden the owners financially. Therefore, meticulous echocardiographic staging remains the absolute cornerstone of our clinical decision-making.",
        "vocab": [
            {"term": "preclinical phase", "zh": "臨床前期/無症狀期"},
            {"term": "positive inotropes", "zh": "正性肌力藥物"},
            {"term": "hemodynamic benefit", "zh": "血流動力學上的益處"},
            {"term": "meticulous echocardiographic staging", "zh": "嚴謹的超音波分期"}
        ],
        "chinese_translation": "在管理犬 MMVD 時，EPIC 試驗證明了 pimobendan 能延長臨床前期，從而徹底改變了我們的治療方針。然而，準確識別 B2 期至關重要。我們必須依賴嚴格的超音波標準：特別是 LA:Ao 大於 1.6，以及標準化左心室舒張末期內徑 (LVIDDN) 超過 1.7。對真正穩定的 B1 期犬隻過早使用正性肌力藥物，並未證實有血流動力學上的益處，反而可能造成飼主不必要的經濟負擔。因此，嚴謹的超音波分期仍然是我們臨床決策的絕對基石。",
        "sample_answer": "Accurate staging using EPIC criteria is essential to avoid premature initiation of pimobendan in B1 dogs. (使用 EPIC 標準進行準確分期，對於避免在 B1 期犬隻過早使用 pimobendan 至關重要。)",
        "qa_question": "How do you handle cases where the LA:Ao is 1.65 but the LVIDDN is only 1.6?",
        "quiz": {
            "question": "According to the EPIC trial criteria mentioned, which echocardiographic finding justifies initiating pimobendan?",
            "options": [
                "LA:Ao ratio strictly below 1.5",
                "LVIDDN exceeding 1.7",
                "Presence of a grade 2/6 murmur alone",
                "Signs of active congestive heart failure"
            ],
            "answer": "LVIDDN exceeding 1.7",
            "explanation": "正確！根據文段中的 EPIC 試驗標準，進入 B2 期的條件包含 LA:Ao > 1.6 以及 LVIDDN > 1.7。"
        }
    },
    "貓三體炎 (Feline Triaditis) 的併發管理": {
        "reference": "Simpson KW. Pancreatitis and triaditis in cats: causes and treatment. J Small Anim Pract. 2015;56(1):40-49.",
        "english_text": "Feline triaditis represents a complex diagnostic and therapeutic challenge, involving concurrent cholangitis, pancreatitis, and inflammatory bowel disease. Due to the unique anatomy of the feline pancreaticobiliary duct, inflammation in one organ frequently cascades to the others. When managing these cases, nutritional support is absolutely critical, often requiring early placement of an esophageal feeding tube. Furthermore, we must not overlook the high prevalence of cobalamin deficiency associated with chronic enteropathies. Parenteral supplementation of Vitamin B12 is often necessary to break the cycle of malabsorption and chronic weight loss, significantly improving the overall prognosis.",
        "vocab": [
            {"term": "concurrent cholangitis", "zh": "併發的膽管炎"},
            {"term": "pancreaticobiliary duct", "zh": "胰膽管"},
            {"term": "parenteral supplementation", "zh": "腸胃外(注射)補充"},
            {"term": "malabsorption", "zh": "吸收不良"}
        ],
        "chinese_translation": "貓三體炎是一個複雜的診斷與治療挑戰，包含併發的膽管炎、胰臟炎和炎症性腸病 (IBD)。由於貓咪胰膽管的獨特解剖結構，一個器官的發炎經常會連鎖反應到其他器官。在管理這些病例時，營養支持絕對是關鍵，通常需要及早放置食道餵食管。此外，我們絕不能忽視與慢性腸病相關的高盛行率維生素 B12 (cobalamin) 缺乏。通常需要透過注射補充維生素 B12，以打破吸收不良和慢性體重減輕的惡性循環，從而顯著改善整體預後。",
        "sample_answer": "Comprehensive management of triaditis requires aggressive nutritional support and proactive cobalamin supplementation. (三體炎的綜合管理需要積極的營養支持和主動的 B12 補充。)",
        "qa_question": "What is your first-line choice of diet for a cat presenting with acute triaditis?",
        "quiz": {
            "question": "Why does inflammation frequently spread between the liver, pancreas, and intestines in cats?",
            "options": [
                "Due to the unique anatomy of their pancreaticobiliary duct.",
                "Because they lack a functional immune system.",
                "Due to a genetic mutation in domestic shorthairs.",
                "Because cobalamin deficiency causes systemic inflammation."
            ],
            "answer": "Due to the unique anatomy of their pancreaticobiliary duct.",
            "explanation": "正確！貓咪的胰管與膽管在進入十二指腸前會匯合成共用通道，這使得細菌或發炎物質容易互相波及。"
        }
    },
    "白內障術後難治性高眼壓 (Refractory POH)": {
        "reference": "Gelatt KN, et al. Veterinary Ophthalmology. 6th ed. Wiley-Blackwell; 2021.",
        "english_text": "In veterinary ophthalmology, postoperative ocular hypertension (POH) following phacoemulsification requires aggressive vigilance. Retained viscoelastic material and surgically induced uveitis are primary culprits. While prophylactic topical dorzolamide and timolol are standard, we frequently encounter refractory cases where the intraocular pressure remains dangerously elevated. In such scenarios, provided the patient is systemically stable and adequately hydrated, intravenous administration of hyperosmotic agents like mannitol is indicated to rapidly dehydrate the vitreous. Failure to aggressively manage these acute pressure spikes can lead to irreversible retinal ganglion cell apoptosis, blinding a patient despite a perfectly executed lenticular extraction.",
        "vocab": [
            {"term": "retained viscoelastic material", "zh": "殘留的黏彈劑"},
            {"term": "surgically induced uveitis", "zh": "手術引發的葡萄膜炎"},
            {"term": "hyperosmotic agents", "zh": "高滲透壓藥物"},
            {"term": "retinal ganglion cell apoptosis", "zh": "視網膜神經節細胞凋亡"}
        ],
        "chinese_translation": "在獸醫眼科中，晶體乳化術後的高眼壓 (POH) 需要極度積極的警戒。殘留的黏彈劑和手術引發的葡萄膜炎是主要元兇。雖然預防性使用局部 dorzolamide 和 timolol 是標準做法，但我們經常遇到眼壓仍危險地升高的難治性病例。在這些情況下，只要病患全身狀況穩定且水分充足，就有指徵靜脈注射如甘露醇等高滲透壓藥物，以迅速使玻璃體脫水。如果未能積極控制這些急性的眼壓飆升，可能會導致不可逆的視網膜神經節細胞凋亡，使得病患即便經歷了完美的晶狀體摘除術，最終仍面臨失明。",
        "sample_answer": "Refractory POH demands immediate intervention with hyperosmotic agents like mannitol to prevent irreversible retinal damage. (難治性 POH 需要立即使用如甘露醇等高滲透壓藥物介入，以防止不可逆的視網膜損傷。)",
        "qa_question": "Are there any specific contraindications for using IV mannitol in your clinical practice?",
        "quiz": {
            "question": "What is the primary mechanism of action for using intravenous mannitol in refractory POH?",
            "options": [
                "It reduces inflammation in the anterior chamber.",
                "It dissolves retained viscoelastic material.",
                "It rapidly dehydrates the vitreous humor.",
                "It paralyzes the ciliary body muscle."
            ],
            "answer": "It rapidly dehydrates the vitreous humor.",
            "explanation": "正確！甘露醇作為高滲透壓藥物，是藉由將水分從眼內（玻璃體）抽到血管中，迅速降低眼壓。"
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
LOG_F, VOC_F, CUSTOM_LIB_F = DATA / "log.csv", DATA / "vocab.json", DATA / "custom_library.json"
LOG_COLS = ["日期", "主題", "訓練方式", "分鐘", "自評"]

specialties = ["小動物心臟學 (Cardiology)", "小動物眼科學 (Ophthalmology)",
               "小動物臨床營養學 (Clinical Nutrition)", "小動物內科學 (Internal Medicine)",
               "小動物腫瘤學 (Oncology)", "急診與重症 (Emergency & Critical Care)",
               "麻醉與疼痛管理 (Anesthesia & Analgesia)"]

tasks = [
    {"name": "🗣️ 影子跟讀 (Shadowing)", "desc": "聽懂發音後，戴上耳機比講者慢 0.5 秒跟著唸。最後可錄下自己版本。"},
    {"name": "🎤 Q&A 實戰模擬", "desc": "聽完引言，針對下方『聽眾提問』，給自己 2 分鐘全英文口頭回答並錄音。"},
    {"name": "📝 臨床口頭摘要", "desc": "聽完後不看稿，用自己的話濃縮內容，做 30 秒精華報告並錄音。"},
]

def load_log():
    return pd.read_csv(LOG_F) if LOG_F.exists() else pd.DataFrame(columns=LOG_COLS)
def load_vocab():
    return json.loads(VOC_F.read_text("utf-8")) if VOC_F.exists() else {}
def save_vocab(v):
    VOC_F.write_text(json.dumps(v, ensure_ascii=False, indent=1), "utf-8")
def load_custom_lib():
    return json.loads(CUSTOM_LIB_F.read_text("utf-8")) if CUSTOM_LIB_F.exists() else {}

# ---------- AI 與語音核心 ----------
@st.cache_data(show_spinner=False)
def tts(text, slow=False): 
    fp = io.BytesIO()
    gTTS(text=text, lang="en", tld="us", slow=slow).write_to_fp(fp)
    return fp.getvalue()

def generate(specialty, topic, seen):
    prompt = f"""你是一位獸醫專科醫師，正在為台灣獸醫師準備國際研討會英文口說教材。
領域：{specialty}。{"指定主題：" + topic if topic else "請自選一個進階的臨床議題，不要只講最常見的基礎疾病。"}
避免出現過的主題：{seen[-10:] or "無"}。
要求：
1. 內容必須符合目前主流的獸醫權威指引（如 AAHA, ACVIM, JVIM 或 ISFM）。
2. 請給予講稿完整的「脈絡感」：開場請有真實研討會的帶入感（例如提及近期指引、回顧性研究或臨床痛點）；結尾請給出明確的 Take-home message。
3. 【極度重要】為了方便英文聽力與口說跟讀，請務必使用「TED Talk 演講風格」的短句。不要寫得像死板的教科書，每句話盡量控制在 15-20 個英文字以內，多用主動語態，斷句要清晰。總字數約 130-150 字。

請務必以純 JSON 格式回傳，格式必須嚴格如下：
{{
    "title": "繁中主題名",
    "reference": "真實文獻出處（如：第一作者, 期刊名, 年份, 標題等）",
    "english_text": "英文講稿內容 (務必全是短句)...",
    "vocab": [
        {{"term": "英文語塊", "zh": "繁中解釋"}},
        {{"term": "英文語塊", "zh": "繁中解釋"}},
        {{"term": "英文語塊", "zh": "繁中解釋"}}
    ],
    "chinese_translation": "精確繁中翻譯",
    "sample_answer": "一句高階總結，格式：English sentence. (中文翻譯。)",
    "qa_question": "一個進階的聽眾英文提問",
    "quiz": {{
        "question": "根據講稿出一題英文單選題",
        "options": ["選項 A", "選項 B", "選項 C", "選項 D"],
        "answer": "正確的選項文字（必須與選項完全一致）",
        "explanation": "繁中詳解"
    }}
}}
"""
    r = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    return json.loads(r.text)

def coach(audio_bytes, c, task):
    prompt = f"""你是高階獸醫英文口說教練。學員目標是能流暢參與國際研討會。
參考講稿：{c['english_text']}
今天的訓練模式：{task['name']}；（若為 Q&A，提問是：{c['qa_question']}）
請聆聽學員的錄音，並用繁體中文 Markdown 格式回覆：
1. **🗣️ 學員逐字稿 (Transcript)**：(列出你聽到的英文)
2. **🌟 值得稱讚的 3 點**：(語氣、專業字彙等)
3. **🛠️ 最該改進的 3 點**：(發音、文法或停頓，請明確指出錄音中哪裡講錯)
4. **🚀 教練升級版說法**：(提供一段道地的高階英文示範，附中文翻譯)
"""
    r = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_bytes}])
    return r.text

# ---------- 狀態管理 ----------
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
    with st.expander("⚙️ 訓練設定 (AI 模式適用)", expanded=False):
        specialty = st.selectbox("專科領域", specialties)
        topic = st.text_input("想指定的主題（可留空交給 AI）", placeholder="例如：犬心房顫動的處置")
    
    choice = st.radio("訓練方式", ["隨機"] + [t["name"] for t in tasks], horizontal=True)
    
    c1, c2 = st.columns(2)
    if c1.button(f"🚀 抽取本地題庫 (共 {len(all_library)} 題，秒開)", use_container_width=True, type="primary"):
        k = random.choice(list(all_library.keys()))
        data = all_library[k]
        data["title"] = f"經典：{k}"
        start_training(data, choice)
        
    if c2.button("🤖 AI 寫新講稿 (需等候)", use_container_width=True):
        if not model:
            st.error("請先在 Streamlit Secrets 設定 GEMINI_API_KEY！")
        else:
            with st.spinner("AI 正在查閱文獻並撰寫講稿... (若卡住超過20秒，建議改用『題庫管理』手動擴充)"):
                try:
                    r = generate(specialty, topic, S.seen)
                    r["title"] = f"AI：{r['title']}"
                    start_training(r, choice)
                except Exception as e:
                    st.error(f"API 生成逾時或失敗。建議前往「⚙️ 題庫管理」使用 Gemini 網頁版手動擴充。 (錯誤: {e})")

    # --- 渲染教材 ---
    c = S.content
    if c:
        st.divider()
        st.subheader(c["title"])
        
        if c.get("reference"):
            st.markdown(f"📚 **文獻來源：** *{c['reference']}*")
            
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
                with st.spinner("AI 教練正在仔細聆聽你的發音與用字..."):
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
            st.success("🎉 已成功記錄到學習履歷中！")

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
                    v["box"] = 0
                    v["due"] = str(date.today() + timedelta(days=1))
                    save_vocab(vocab)
                    S.rv = False
                    st.rerun()
                if b.button("😎 記得很熟", type="primary", use_container_width=True):
                    v["box"] = min(v["box"] + 1, 4)
                    IV = [1, 3, 7, 14, 30]
                    v["due"] = str(date.today() + timedelta(days=IV[v["box"]]))
                    save_vocab(vocab)
                    S.rv = False
                    st.rerun()

with t3:
    st.subheader("📊 我的學習履歷")
    if log.empty:
        st.info("目前還沒有紀錄，趕快去完成今天的任務吧！")
    else:
        st.dataframe(log.iloc[::-1], use_container_width=True, hide_index=True)

with t4:
    st.subheader("⚙️ 專屬題庫管理後台")
    st.info("💡 提示：使用 Gemini Advanced 產生題庫會比直接按 API 寫稿快非常多！貼在下方即可擴充。")
    
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
