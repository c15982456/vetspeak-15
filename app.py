import io, json, os, random, re, time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from gtts import gTTS
from google import genai
from google.genai import types

from library import builtin_library

st.set_page_config(page_title="VetSpeak 15", page_icon="🩺", layout="centered")

# ---------- 設定 ----------
def secret(k, default=None):
    try:
        return st.secrets[k]
    except Exception:
        return os.getenv(k, default)

API_KEY = secret("GEMINI_API_KEY")
MODEL = secret("GEMINI_MODEL", "gemini-2.5-flash")  # 可在 secrets 改成你帳號可用的模型
client = genai.Client(api_key=API_KEY) if API_KEY else None

DATA = Path("data"); DATA.mkdir(exist_ok=True)
LOG_F, VOC_F = DATA / "log.csv", DATA / "vocab.json"
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

# ---------- 資料存取（存檔，重新整理也不會消失）----------
def load_log():
    return pd.read_csv(LOG_F) if LOG_F.exists() else pd.DataFrame(columns=LOG_COLS)

def load_vocab():
    return json.loads(VOC_F.read_text("utf-8")) if VOC_F.exists() else {}

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

def generate(specialty, topic, seen):
    prompt = f"""你是一位獸醫專科醫師，正在為台灣獸醫師準備國際研討會英文口說教材。
領域：{specialty}。{"指定主題：" + topic if topic else "請自選一個臨床議題，不要只講最常見的疾病。"}
請避免這些已出現過的主題：{seen[-10:] or "無"}。
撰寫約 1 分鐘（130-150 字）的口語化英文研討會短講，加入學術轉折語（signposting）。
依你所知的指引（AAHA、ACVIM 等）撰寫，但不要捏造具體數據、研究或引用；不確定的細節用保守說法。
只回傳 JSON，欄位如下：
title（繁中主題名）, english_text, vocab（3-4 個物件 {{"term":"英文語塊","zh":"中文"}}）,
chinese_translation（繁中翻譯）, sample_answer（一句高階總結，格式 English. (中文。)）,
qa_question（一個聽眾會問的英文問題）,
quiz {{question, options（4 個英文選項）, answer（必須與其中一個選項完全相同）, explanation（繁中詳解）}}"""
    r = client.models.generate_content(
        model=MODEL, contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=1.0))
    return json.loads(r.text)

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
    r = client.models.generate_content(model=MODEL, contents=[
        prompt, types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")])
    return r.text

# ---------- 狀態 ----------
S = st.session_state
for k, v in dict(content=None, task=None, fb=None, timer_end=None, seen=[], qn=0, rv=False).items():
    S.setdefault(k, v)
vocab, log = load_vocab(), load_log()

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
    if c1.button("🚀 內建題庫（秒開）"):
        pool = [k for k in builtin_library if k not in S.seen[-1:]]
        k = random.choice(pool or list(builtin_library))
        start(normalize(builtin_library[k], f"內建：{k}"), choice)
    if c2.button("🤖 AI 生成新講稿", disabled=client is None,
                 help=None if client else "請先設定 GEMINI_API_KEY"):
        with st.spinner("AI 正在撰寫講稿…"):
            try:
                r = generate(specialty, topic, S.seen)
                start(normalize(r, f"AI：{r['title']}"), choice)
            except Exception as e:
                st.error(f"生成失敗，請再試一次。（{e}）")

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
        rec = st.audio_input("按下錄音，完成後可回放")
        if rec:
            if client and st.button("🤖 請 AI 教練給回饋"):
                with st.spinner("教練正在聆聽…"):
                    try:
                        S.fb = coach(rec.getvalue(), c, S.task)
                    except Exception as e:
                        st.error(f"回饋失敗：{e}")
        if S.fb:
            st.markdown(S.fb)

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
    st.caption("紀錄存在伺服器的 data/ 資料夾。若部署在 Streamlit Cloud，重啟後可能清空，請定期下載備份。")
