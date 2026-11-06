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
    # 【修正 1】換回你專屬的 3.8-flash 模型，避免 404 報錯
    model = genai.GenerativeModel("gemini-3.8-flash")
else:
    model = None

DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)
LOG_F, VOC_F = DATA / "log.csv", DATA / "vocab.json"
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

# ---------- AI 與語音核心 ----------
@st.cache_data
