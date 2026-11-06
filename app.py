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

st.set_page_config(page_title="VetSpeak 15 - 雙引擎特訓", page_icon="🩺", layout="centered")

# --- 設定 Gemini API ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-3.8-flash')
else:
    st.warning("尚未設定 GEMINI_API_KEY。目前僅可使用內建題庫。")

# --- 領域與任務設定 ---
specialties = [
    "小動物心臟學 (Cardiology)",
    "小動物眼科學 (Ophthalmology)",
    "小動物臨床營養學 (Clinical Nutrition)",
    "小動物內科學 (Internal Medicine)"
]

tasks = [
    {"name": "🗣️ 影子跟讀 (Shadowing)", "desc": "先聽一次發音。接著戴上耳機，按下播放，講者說什麼慢 0.5 秒跟著唸，注意換氣與斷句。"},
    {"name": "🎤 Q&A 實戰模擬", "desc": "聽完這段 1 分鐘的引言後，給自己 2 分鐘全英文口頭發表你的觀點。"},
    {"name": "📝 臨床口頭摘要", "desc": "聽完語音後，用自己的話將這 1 分鐘的內容濃縮，向學員做 30 秒的精華報告。"}
]

# --- 內建秒速題庫 (1分鐘演講版) ---
builtin_library = {
    "MMVD 分期與 MINE 評分": {
        "english_text": "Thank you all for being here. Today, I'd like to address a common clinical dilemma we face in veterinary cardiology: the precise timing to initiate pimobendan in dogs with Myxomatous Mitral Valve Disease. We all know that the transition from Stage B1 to Stage B2 is a critical decision point based on the ACVIM consensus guidelines. However, in routine practice, we frequently encounter 'grey-zone' cases where echocardiographic parameters, specifically the LA to Ao ratio and LVIDDN, are borderline. They might perfectly straddle the established cut-offs. This is precisely where integrating the MINE score becomes invaluable. Rather than relying solely on a rigid, binary classification, the MINE score provides granular prognostic stratification. By evaluating a combination of clinical and echocardiographic variables, it allows us to individualize pharmacological intervention. Ultimately, this multiparametric approach ensures we don't delay life-prolonging therapy in high-risk patients, while preventing premature medication in truly stable B1 dogs.",
        "vocab": "critical decision point (關鍵決策點), perfectly straddle the cut-offs (剛好卡在臨界值邊緣), granular prognostic stratification (細緻的預後分級), multiparametric approach (多參數評估法)",
        "chinese_translation": "各位好。今天我想探討獸醫心臟科常見的臨床難題：犬 MMVD 開始使用 pimobendan 的精確時機。我們都知道，根據 ACVIM 共識指南，從 B1 期進展到 B2 期是關鍵決策點。然而在常規實踐中，我們經常遇到「模糊地帶」病例，其超音波參數處於臨界值。這正是結合 MINE 評分發揮極大價值的地方。MINE 評分提供了更細緻的預後分層，使我們能為病患量身制定藥物介入時機，確保不延誤高風險病患的治療，同時避免對穩定的 B1 期犬隻過早投藥。",
        "sample_answer": "The MINE score provides granular prognostic stratification for borderline cases.\n(MINE 評分為了處於邊緣的病例提供了更細緻的預後分級。)",
        "quiz": {
            "question": "What is the primary value of the MINE score in 'grey-zone' MMVD cases?",
            "options": [
                "It completely replaces echocardiography.",
                "It provides granular prognostic stratification.",
                "It alters the ACVIM cut-offs permanently.",
                "It is specifically for Stage C patients."
            ],
            "answer": "It provides granular prognostic stratification.",
            "explanation": "正確！MINE 評分為處於邊緣的病例提供細緻的預後分層（granular prognostic stratification）。"
        }
    },
    "白內障手術 (Phacoemulsification) 術後併發症": {
        "english_text": "Moving on to postoperative care in veterinary ophthalmology, I want to emphasize the management of postoperative ocular hypertension, or POH. This is a frequent and potentially vision-threatening complication following phacoemulsification in dogs, particularly within the first 24 hours post-op. Despite our best prophylactic efforts, we still see patients developing acute spikes in intraocular pressure. My protocol for these critical hours involves hourly monitoring of IOP. When dealing with refractory POH—cases that do not respond to first-line topical anti-glaucoma medications—we must be prepared to escalate our therapy aggressively. This might involve adding systemic carbonic anhydrase inhibitors or administering hyperosmotic agents like intravenous mannitol, provided the patient’s cardiovascular and renal status permits. The key takeaway here is that early, aggressive intervention is paramount. If we fail to aggressively manage these refractory pressure spikes, we risk irreversible damage to the optic nerve and retina, ultimately compromising the entire surgical success.",
        "vocab": "vision-threatening complication (威脅視力的併發症), prophylactic efforts (預防措施), refractory POH (難以控制的高眼壓), escalate our therapy aggressively (積極升級治療)",
        "chinese_translation": "接下來我想強調術後高眼壓（POH）的管理。這是犬隻晶體乳化術後常見且可能威脅視力的併發症。儘管做了最完善的預防措施，仍會遇到病患出現急性眼壓飆升。我在這段關鍵時間的準則包含每小時監測眼壓。當處理難以控制的高眼壓時，我們必須準備好積極升級治療，這可能包含全身性碳酸酐酶抑制劑或高滲透壓藥物。重點是，早期且積極的介入至關重要，否則將面臨不可逆的視神經損傷。",
        "sample_answer": "My protocol includes hourly monitoring of IOP and escalating to systemic therapy if it remains refractory.\n(我的準則包含每小時監測眼壓，若眼壓仍難以控制則升級為全身性治療。)",
        "quiz": {
            "question": "In the context of postoperative ocular hypertension, what does 'refractory' mean?",
            "options": [
                "Resolving spontaneously.",
                "Responsive to first-line treatment.",
                "Resistant to normal treatment or difficult to control.",
                "Occurring before surgery."
            ],
            "answer": "Resistant to normal treatment or difficult to control.",
            "explanation": "正確！'Refractory' 指的是對一般治療沒有反應、頑固性的情況。"
        }
    },
    "犬貓 CKD 臨床營養與處方飼料": {
        "english_text": "Let’s shift our focus to clinical nutrition, specifically the dietary management of feline chronic kidney disease. We universally accept that dietary modification is the absolute cornerstone of managing CKD. However, in real-world clinical practice, we often face a significant hurdle: palatability frequently hinders patient compliance. This becomes especially challenging when transitioning a Stage 3 CKD cat to a heavily restricted renal diet. The clinical dilemma is how we balance essential phosphate restriction with the paramount importance of maintaining caloric intake and lean body mass. If a cat outright rejects the renal diet, forcing it can lead to starvation and muscle wasting, which dramatically worsens the prognosis. Therefore, my approach is pragmatic. I prioritize caloric intake and lean body mass above all. If traditional renal diets are rejected, I prefer to utilize a highly palatable senior diet combined with intestinal phosphate binders to achieve our target serum phosphorus levels.",
        "vocab": "cornerstone (基石/核心), hinder patient compliance (阻礙病患配合度), paramount importance (至關重要), pragmatic approach (務實的方法/策略)",
        "chinese_translation": "讓我們將焦點轉向貓慢性腎病（CKD）的飲食管理。飲食調整絕對是管理 CKD 的基石。然而，適口性往往會阻礙病患的配合度。臨床上的兩難在於，我們該如何平衡「限制磷攝取」以及「維持熱量攝取與瘦體重」這兩項至關重要的目標。如果貓咪拒絕處方飼料，強迫餵食可能導致飢餓與肌肉流失。因此，我的方法很務實：我將熱量攝取和維持瘦體重放在首位。如果處方飼料被拒絕，我傾向使用適口性極佳的高齡貓飼料，並搭配腸道磷結合劑。",
        "sample_answer": "I prioritize caloric intake and lean body mass, using a palatable senior diet with phosphate binders if needed.\n(我優先考量熱量攝取與維持瘦體重，必要時使用適口性佳的高齡貓飼料搭配磷結合劑。)",
        "quiz": {
            "question": "Why is transitioning a cat to a renal diet often challenging in practice?",
            "options": [
                "Renal diets cause severe gastrointestinal upset.",
                "Palatability issues frequently hinder patient compliance.",
                "Phosphate binders negate medication effects.",
                "Owners refuse the diet."
            ],
            "answer": "Palatability issues frequently hinder patient compliance.",
            "explanation": "正確！適口性不佳 (palatability) 是導致病患不配合的最大阻礙。"
        }
    }
}

# --- AI 生成邏輯 (廣泛領域版) ---
def generate_medical_content(specialty):
    prompt = f"""
    你現在是一位獸醫專科醫師。請根據全部獸醫相關文獻（最偏重參考 AAHA, ACVIM, JVIM 的權威指引或近期發表），
    隨機挑選一個關於「{specialty}」的臨床主題進行探討。
    要求：
    1. 不要太侷限在常見單一疾病（例如心臟科不要只講 MMVD，可以講心律不整、肺高壓等），請自由發揮多元臨床議題。
    2. 撰寫一段長度約 1 分鐘（約 130-150 字）的英文研討會短講講稿。這是一段口語化的演講內容，請加入學術轉折語（Signposting）。
    
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
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            return {"error": "生成失敗，AI 未回傳正確的格式，請再試一次。"}
    except Exception as e:
        return {"error": f"發生錯誤，請再試一次。詳細錯誤訊息：{e}"}

# --- 狀態管理區 ---
if "current_content" not in st.session_state:
    st.session_state.current_content = None
if "task" not in st.session_state:
    st.session_state.task = None
# 將原本的 quiz_submitted 改為記錄作答結果，方便大按鈕判定
if "quiz_result" not in st.session_state:
    st.session_state.quiz_result = None
if "learning_log" not in st.session_state:
    st.session_state.learning_log = pd.DataFrame(columns=["日期", "來源與領域", "訓練方式", "自我評分"])

# --- UI 介面區 ---
st.title("🏃 VetSpeak 15 - 雙引擎特訓")

tab1, tab2 = st.tabs(["🚀 今日特訓", "📈 學習紀錄"])

with tab1:
    st.markdown("請選擇你要使用**秒速內建題庫**，還是花 15 秒請 **AI 讀新文獻**：")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 抽取內建特訓 (秒速)"):
            topic = random.choice(list(builtin_library.keys()))
            data = builtin_library[topic]
            st.session_state.task = random.choice(tasks)
            st.session_state.quiz_result = None # 重新抽題時清空測驗結果
            
            st.session_state.current_content = {
                "title": f"內建經典題庫：{topic}",
                "english_text": data["english_text"],
                "vocab": data["vocab"],
                "chinese_translation": data["chinese_translation"],
                "sample_answer": data["sample_answer"],
                "quiz": data["quiz"]
            }

    with col2:
        if st.button("🤖 AI 讀最新文獻 (約15秒)"):
            if "GEMINI_API_KEY" not in st.secrets:
                st.error("需先設定 API 金鑰才能使用此功能！")
            else:
                specialty = random.choice(specialties)
                st.session_state.task = random.choice(tasks)
                st.session_state.quiz_result = None # 重新抽題時清空測驗結果
                st.session_state.current_content = None 
                
                with st.spinner(f"正在搜尋 AAHA/ACVIM/JVIM 關於 {specialty} 的多元文獻，請稍候..."):
                    result = generate_medical_content(specialty)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state.current_content = {
                            "title": f"AI 生成文獻特訓：{specialty}",
                            "english_text": result["english_text"],
                            "vocab": result["vocab"],
                            "chinese_translation": result["chinese_translation"],
                            "sample_answer": result["sample_answer"],
                            "quiz": result["quiz"]
                        }

    # --- 渲染內容區 ---
    if st.session_state.current_content:
        content = st.session_state.current_content
        
        st.success("任務與文獻短講準備完畢！")
        st.subheader(f"📌 主題：{content['title']}")
        st.markdown(f"**🎯 訓練方式：{st.session_state.task['name']}**")
        st.write(st.session_state.task["desc"])
        
        st.divider()
        st.markdown("### 📖 今日特訓內容")
        
        text_to_read = content["english_text"]
        
        with st.spinner("🎧 正在生成 1 分鐘講者語音，請稍候..."):
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
        
        # --- 全新改版：觸控友善大按鈕 ---
        if st.session_state.quiz_result is None:
            # 如果還沒作答，顯示選項大按鈕
            for option in quiz_data["options"]:
                # use_container_width=True 讓按鈕填滿手機螢幕寬度，超級好點！
                if st.button(option, use_container_width=True, key=option):
                    if option == quiz_data["answer"]:
                        st.session_state.quiz_result = ("correct", quiz_data['explanation'])
                    else:
                        st.session_state.quiz_result = ("incorrect", quiz_data['explanation'])
                    st.rerun() # 點擊後立即重新整理畫面顯示結果
        else:
            # 如果已經作答，顯示結果與詳解
            status, explanation = st.session_state.quiz_result
            if status == "correct":
                st.success(f"**Correct! 🎉**\n\n{explanation}")
            else:
                st.error(f"**Incorrect. 💡**\n\n{explanation}")
                
            # 給予重新挑戰的機會
            if st.button("🔄 重新作答", use_container_width=True):
                st.session_state.quiz_result = None
                st.rerun()
        
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
                "來源與領域": content["title"],
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
