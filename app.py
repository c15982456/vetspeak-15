import io, json, os, random, re, time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from gtts import gTTS
import google.generativeai as genai

from library import builtin_library
from library_extra import extra_library
from refs import REFS

st.set_page_config(page_title="VetSpeak 15", page_icon="🩺", layout="centered")

# ---------- 設定 ----------
def secret(k, default=None):
    try:
        return st.secrets[k]
    except Exception:
        return os.getenv(k, default)

API_KEY = secret("GEMINI_API_KEY")
MODEL = secret("GEMINI_MODEL", "gemini-3.8-flash")  # 可在 secrets 改成你帳號可用的模型
model = None
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL)

DATA = Path(__file__).parent / "data"; DATA.mkdir(exist_ok=True)
LOG_F, VOC_F, BANK_F = DATA / "log.csv", DATA / "vocab.json", DATA / "bank.json"
LOG_COLS = ["日期", "主題", "訓練方式", "分鐘", "自評"]
IV = [1, 3, 7, 14, 30]  # 間隔複習天數

specialties = ["小動物心臟學 (Cardiology)", "小動物眼科學 (Ophthalmology)",
               "小動物臨床營養學 (Clinical Nutrition)", "小動物內科學 (Internal Medicine)",
               "小動物腫瘤學 (Oncology)", "急診與重症 (Emergency & Critical Care)",
               "麻醉與疼痛管理 (Anesthesia & Analgesia)", "皮膚科 (Dermatology)"]

tasks = [
    {"name": "🗣️ 影子跟讀 (Shadowing)", "desc": "先用慢速聽一次，再切正常速度，戴上耳機比講者慢 0.5 秒跟著唸，注意換氣與斷句。最後錄下自己的版本。"},
    {"name": "🎤 Q&A 實戰模擬", "desc": "聽完引言後，針對下方的聽眾提問，給自己 2 分鐘全英文口頭回答並錄音。"},
    {"name": "📝 臨床口頭摘要", "desc": "聽完後不看稿，用自己的話濃縮這 1 分鐘內容，做 30 秒精華報告並錄音。"},
]

SAY = ["跟著上面的講稿，一句一句大聲唸出來（可以看稿）。AI 會檢查你的發音與停頓。",
       "回答上面的「聽眾提問」，全英文講約 1–2 分鐘。不用完美，說出你的臨床想法就好。",
       "不看稿（可開盲聽模式），用自己的話把剛才聽到的重點濃縮成約 30 秒。"]

# ---------- 資料存取（存檔，重新整理也不會消失）----------
def load_log():
    return pd.read_csv(LOG_F) if LOG_F.exists() else pd.DataFrame(columns=LOG_COLS)

def load_vocab():
    return json.loads(VOC_F.read_text("utf-8")) if VOC_F.exists() else {}

def load_bank():  # AI 生成過的講稿會存起來，之後可免額度重複使用
    return json.loads(BANK_F.read_text("utf-8")) if BANK_F.exists() else {}

def save_bank(c):
    b = load_bank(); b[c["title"]] = c
    BANK_F.write_text(json.dumps(b, ensure_ascii=False, indent=1), "utf-8")

def ai_err(e):
    m = str(e)
    if any(x in m for x in ("429", "quota", "RESOURCE_EXHAUSTED")):
        return "⚠️ AI 額度暫時用完了。題庫與錄音回放不受影響，請先用「題庫」，稍後或明天再試 AI。"
    return f"AI 暫時無法使用：{m}"

def save_vocab(v):
    VOC_F.write_text(json.dumps(v, ensure_ascii=False, indent=1), "utf-8")

def streak(days):
    d = date.today()
    if str(d) not in days:
        d -= timedelta(days=1)
    n = 0
    while str(d) in days:
        n, d = n + 1, d - timedelta(days=1)
    return n

# ---------- 語音 / AI ----------
@st.cache_data(show_spinner=False)
def tts(text, slow=False):  # 快取：按任何按鈕都不會重新生成語音
    fp = io.BytesIO()
    gTTS(text=text, lang="en", tld="us", slow=slow).write_to_fp(fp)
    return fp.getvalue()

def parse_vocab(s):
    return [{"term": t.strip(), "zh": z.strip()}
            for t, z in re.findall(r"([^,()（）]+?)\s*[(（]([^)）]+)[)）]", s)]

def normalize(c, title):
    v = parse_vocab(c["vocab"]) if isinstance(c["vocab"], str) else c["vocab"]
    q = dict(c["quiz"]); opts = list(q["options"]); random.shuffle(opts)
    if q["answer"] not in opts:
        opts[0] = q["answer"]
    q["options"] = opts
    qa = c.get("qa_question") or "What is your own clinical approach to this issue, and why?"
    return {**c, "title": title, "vocab": v, "quiz": q, "qa_question": qa}

def generate(specialty, topic, seen, tick=None):
    prompt = f"""你是一位獸醫專科醫師，正在為台灣獸醫師準備國際研討會英文口說教材。
領域：{specialty}。{"指定主題：" + topic if topic else "請自選一個臨床議題，不要只講最常見的疾病。"}
請避免這些已出現過的主題：{seen[-10:] or "無"}。
撰寫約 1 分鐘（130-150 字）的口語化英文研討會短講，加入學術轉折語（signposting）。
依你所知的指引（AAHA、ACVIM 等）撰寫，但不要捏造具體數據、研究或引用；不確定的細節用保守說法。
只回傳 JSON，欄位如下：
title（繁中主題名）, english_text, vocab（3-4 個物件 {{"term":"英文語塊","zh":"中文"}}）,
chinese_translation（繁中翻譯）, sample_answer（一句高階總結，格式 English. (中文。)）,
qa_question（一個聽眾會問的英文問題）,
search_keywords（3-5 個可在 PubMed 查證此主題的英文關鍵字，逗號分隔；不要編造文獻或作者）,
quiz {{question, options（4 個英文選項）, answer（必須與其中一個選項完全相同）, explanation（繁中詳解）}}"""
    for attempt in range(2):  # JSON 格式偶爾出錯，自動重試一次
        buf = ""
        stream = model.generate_content(
            prompt, stream=True,
            generation_config={"response_mime_type": "application/json", "temperature": 1.0})
        for ch in stream:
            try:
                buf += ch.text
            except Exception:
                pass
            if tick:
                p = min(len(buf) / 3000, 0.95)
                tick(p, "撰寫英文講稿…" if p < .5 else "產生單字與測驗題…" if p < .85 else "整理格式…")
        try:
            return json.loads(buf)
        except json.JSONDecodeError:
            if tick:
                tick(0.1, "格式有誤，自動重試中…")
    raise ValueError("AI 回傳格式持續有誤，請再按一次。")

def coach(audio_bytes, c, task):
    prompt = f"""你是英文口說教練，學員是獸醫師，目標是國際研討會水準。
參考講稿：{c['english_text']}
今天的訓練：{task['name']}；Q&A 問題：{c['qa_question']}
請聆聽錄音，用繁體中文（Markdown）回覆：
1. 逐字稿（英文）
2. 做得好的 3 點
3. 最該改進的 3 點（發音、文法、用詞、流暢度、結構），每點引用錄音中的實例
4. 一段升級版說法（英文＋中文）
若錄音幾乎沒有內容，直接說明。"""
    for ch in model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_bytes}], stream=True):
        try:
            yield ch.text
        except Exception:
            pass

def show_refs(c):
    with st.expander("📚 參考文獻與查證"):
        refs = c.get("refs") or []
        if refs:
            st.markdown("\n".join(f"- {r}" for r in refs))
            st.caption("講稿為教學用改寫，非逐字引用；數值與建議請以原文為準。")
        else:
            st.warning("此講稿由 AI 生成，沒有經過驗證的文獻，請務必自行查證後再使用。")
        kw = c.get("search_keywords")
        if isinstance(kw, list):
            kw = ", ".join(kw)
        if kw:
            st.markdown(f"[🔎 在 PubMed 搜尋相關文獻](https://pubmed.ncbi.nlm.nih.gov/?term={quote_plus(kw)})")

# ---------- 狀態 ----------
S = st.session_state
for k, v in dict(content=None, task=None, fb=None, timer_end=None, seen=[], qn=0, rv=False).items():
    S.setdefault(k, v)
vocab, log = load_vocab(), load_log()
library = {**builtin_library, **extra_library, **load_bank()}

def start(c, choice):
    S.content, S.fb, S.timer_end, S.rv = c, None, None, False
    S.qn += 1
    S.task = random.choice(tasks) if choice == "隨機" else next(t for t in tasks if t["name"] == choice)
    S.seen.append(c["title"])

@st.fragment(run_every=1)
def timer_box():
    left = int(S.timer_end - time.time())
    if left > 0:
        st.progress(1 - left / 900, text=f"⏱️ 剩餘 {left // 60:02d}:{left % 60:02d}")
    else:
        st.success("⏰ 15 分鐘到了！")

# ---------- 介面 ----------
st.title("🩺 VetSpeak 15")
t1, t2, t3 = st.tabs(["🚀 今日特訓", "🔁 單字複習", "📈 學習紀錄"])

with t1:
    specialty = st.selectbox("領域（AI 模式使用）", specialties)
    topic = st.text_input("想講的主題（可留空，由 AI 挑選）", placeholder="例如：犬心房顫動的處置")
    choice = st.radio("訓練方式", ["隨機"] + [t["name"] for t in tasks], horizontal=True)
    c1, c2 = st.columns(2)
    if c1.button(f"🚀 題庫（{len(library)} 題，不耗 AI 額度）"):
        keys = [k for k in library if f"題庫：{k}" not in S.seen[-3:]] or list(library)
        k = random.choice(keys)
        info, cc = REFS.get(k, {}), normalize(library[k], f"題庫：{k}")
        cc["refs"] = info.get("refs", [])
        cc["search_keywords"] = info.get("kw") or cc.get("search_keywords")
        start(cc, choice)
    if c2.button("🤖 AI 生成新講稿", disabled=model is None,
                 help=None if model else "請先設定 GEMINI_API_KEY"):
        bar = st.progress(0.02, text="連線 AI 中…（約 10–30 秒）")
        try:
            r = generate(specialty, topic, S.seen, lambda p, t: bar.progress(p, text=f"{int(p * 100)}%　{t}"))
            bar.progress(1.0, text="100%　完成！")
            save_bank(r)
            start(normalize(r, f"AI：{r['title']}"), choice)
        except Exception as e:
            bar.empty()
            st.error(ai_err(e))

    c = S.content
    if c:
        st.divider()
        st.subheader(c["title"])
        st.markdown(f"**{S.task['name']}**")
        st.write(S.task["desc"])
        if "Q&A" in S.task["name"]:
            st.info(f"🙋 聽眾提問：{c['qa_question']}")

        speed = st.radio("語速", ["正常", "慢速"], horizontal=True)
        st.audio(tts(c["english_text"], speed == "慢速"), format="audio/mp3")
        if st.toggle("👂 盲聽模式（先不看講稿）", value=False):
            st.caption("先聽兩遍、試著抓重點，再關閉開關對照講稿。")
        else:
            st.info(c["english_text"])

        st.markdown("**💡 關鍵語塊（點 ＋ 加入單字本）**")
        for i, v in enumerate(c["vocab"]):
            a, b = st.columns([5, 1])
            a.markdown(f"**{v['term']}** — {v['zh']}")
            have = v["term"] in vocab
            if b.button("✓" if have else "＋", key=f"v{S.qn}_{i}", disabled=have):
                vocab[v["term"]] = {"zh": v["zh"], "box": 0, "due": str(date.today())}
                save_vocab(vocab)
                st.rerun()
        with st.expander("👁️ 中文翻譯與示範解答"):
            st.write(c["chinese_translation"])
            st.markdown(f"**示範摘要：** {c['sample_answer']}")

        show_refs(c)

        st.divider()
        st.markdown("### 🧠 隨堂小測驗")
        q = c["quiz"]
        pick = st.radio(q["question"], q["options"], index=None, key=f"quiz{S.qn}")
        if pick:
            ok = pick == q["answer"]
            (st.success if ok else st.error)(
                ("答對了 🎉" if ok else f"答錯了，正確答案：{q['answer']}") + f"\n\n{q['explanation']}")

        st.divider()
        st.markdown("### 🎙️ 錄下你的口說")
        st.info("**這一步要講什麼：** " + SAY[tasks.index(S.task)])
        st.caption("流程：① 按錄音鍵開始說 ② 說完按停止並回放 ③ 按「AI 教練給回饋」，會得到逐字稿、優缺點與升級版說法（需要 AI 額度；沒額度時可自己回放、對照講稿）。")
        rec = st.audio_input("按下錄音，完成後可回放")
        if rec:
            if model and st.button("🤖 請 AI 教練給回饋"):
                try:
                    with st.status("教練正在聆聽並撰寫回饋…", expanded=True) as stt:
                        S.fb = st.write_stream(coach(rec.getvalue(), c, S.task))
                        stt.update(label="回饋完成", state="complete")
                    st.rerun()
                except Exception as e:
                    st.error(ai_err(e))
        if S.fb:
            st.markdown(S.fb)
        with st.expander("✅ 自我檢查清單（不需要 AI）"):
            st.markdown("- 有沒有一直重複同一個字？\n- 關鍵語塊有沒有用上？\n- 句子有沒有講完整、中途沒有停住？\n- 回放時，重音與斷句和原音檔差多少？")

        st.divider()
        st.markdown("### ⏱️ 15 分鐘計時與打卡")
        if st.button("開始計時"):
            S.timer_end = time.time() + 900
        if S.timer_end:
            timer_box()
        rating = st.slider("今天口說表現自評", 1, 5, 3)
        if st.button("✅ 完成並打卡", type="primary"):
            mins = max(1, round((time.time() - (S.timer_end - 900)) / 60)) if S.timer_end else 0
            row = pd.DataFrame([[str(date.today()), c["title"], S.task["name"], mins, "⭐" * rating]],
                               columns=LOG_COLS)
            pd.concat([log, row], ignore_index=True).to_csv(LOG_F, index=False)
            S.timer_end = None
            log = load_log()  # 重新讀檔，學習紀錄分頁才會立刻顯示最新資料
            st.balloons()
            st.success("已記錄！")

with t2:
    today = str(date.today())
    due = [k for k, v in vocab.items() if v["due"] <= today]
    st.caption(f"單字本共 {len(vocab)} 個，今天待複習 {len(due)} 個（間隔 1／3／7／14／30 天）")
    if not due:
        st.success("🎉 今天沒有要複習的單字。" if vocab else "先在特訓頁把語塊加入單字本吧！")
    else:
        w = due[0]; v = vocab[w]
        with st.container(border=True):
            st.markdown(f"## {w}")
            st.audio(tts(w), format="audio/mp3")
            if not S.rv:
                if st.button("顯示意思"):
                    S.rv = True; st.rerun()
            else:
                st.markdown(f"### {v['zh']}")
                a, b = st.columns(2)
                for col, label, ok in ((a, "😵 忘了", False), (b, "😎 記得", True)):
                    if col.button(label, key=label):
                        v["box"] = min(v["box"] + 1, 4) if ok else 0
                        v["due"] = str(date.today() + timedelta(days=IV[v["box"]]))
                        save_vocab(vocab); S.rv = False; st.rerun()

with t3:
    if log.empty:
        st.info("還沒有紀錄，完成今天的特訓吧！")
    else:
        days = set(log["日期"])
        m1, m2, m3 = st.columns(3)
        m1.metric("連續天數", streak(days))
        m2.metric("累計次數", len(log))
        m3.metric("累計分鐘", int(log["分鐘"].sum()))
        last14 = pd.Series(list(log["日期"])).value_counts()
        idx = [str(date.today() - timedelta(days=i)) for i in range(13, -1, -1)]
        st.bar_chart(last14.reindex(idx, fill_value=0))
        st.dataframe(log.iloc[::-1], hide_index=True)
        st.download_button("⬇️ 下載紀錄 CSV", log.to_csv(index=False).encode("utf-8-sig"), "vetspeak_log.csv")
    up = st.file_uploader("📥 匯入先前備份的 CSV", type="csv")
    if up and st.button("匯入並合併"):
        merged = pd.concat([log, pd.read_csv(up)], ignore_index=True).drop_duplicates()
        merged.to_csv(LOG_F, index=False)
        st.rerun()
    st.caption("紀錄存在伺服器的 data/ 資料夾。若部署在 Streamlit Cloud，重啟後可能清空，請定期下載備份。")
