import streamlit as st
import random
import time
from gtts import gTTS
import io

st.set_page_config(page_title="VetSpeak 15", page_icon="🩺", layout="centered")

# 終極版：加入隨堂小測驗的題庫
content_library = {
    "MMVD 分期與 MINE 評分": {
        "english_text": "We know the transition from Stage B1 to B2 is a critical decision point for initiating pimobendan based on the ACVIM consensus guidelines. In your clinical experience, how does integrating the MINE score help in those grey-zone cases where echocardiographic parameters like LA to Ao and LVIDDN are borderline?",
        "vocab": "critical decision point (關鍵決策點), borderline (處於邊緣的), grey-zone cases (模糊地帶案例)",
        "chinese_translation": "根據 ACVIM 共識指南，我們知道從 B1 期進展到 B2 期是開始使用 pimobendan 的關鍵決策點。就您的臨床經驗來看，在 LA:Ao 和 LVIDDN 等超音波參數處於臨界值（borderline）的『模糊地帶』病例中，結合 MINE 評分能提供什麼幫助？",
        "sample_answer": "The MINE score provides granular prognostic stratification, helping us decide if early intervention is justified despite borderline echo indices.\n(MINE 評分提供了更細緻的預後分級，幫助我們判斷即使超音波指標處於邊緣，是否仍有理由進行早期介入。)",
        "quiz": {
            "question": "What is the primary value of the MINE score in 'grey-zone' MMVD cases according to the context?",
            "options": [
                "It replaces the need for echocardiography completely.",
                "It provides granular prognostic stratification for borderline cases.",
                "It lowers the ACVIM cut-offs for LA:Ao ratio.",
                "It is only used when pimobendan is contraindicated."
            ],
            "answer": "It provides granular prognostic stratification for borderline cases.",
            "explanation": "正確！MINE 評分最大的價值在於為那些處於邊緣（borderline）的病例提供更細緻的預後分層（granular prognostic stratification），輔助臨床決策。"
        }
    },
    "白內障手術 (Phacoemulsification) 術後併發症": {
        "english_text": "Postoperative ocular hypertension is a frequent and potentially vision-threatening complication following phacoemulsification in dogs. What is your protocol for monitoring and managing refractory ocular hypertension in the first 24 hours post-op?",
        "vocab": "vision-threatening complication (威脅視力的併發症), prophylactic (預防性的), refractory (難以控制的/頑固性的)",
        "chinese_translation": "術後高眼壓（POH）是犬隻晶體乳化術後常見且可能威脅視力的併發症。對於術後前 24 小時內難以控制的（refractory）高眼壓，您的監測和處置準則是什麼？",
        "sample_answer": "My protocol includes hourly monitoring of IOP and aggressive use of topical anti-glaucoma medications, sometimes adding systemic carbonic anhydrase inhibitors if it remains refractory.\n(我的準則包含每小時監測眼壓，並積極使用局部抗青光眼藥物，若眼壓仍難以控制，則有時會加入全身性碳酸酐酶抑制劑。)",
        "quiz": {
            "question": "In the context of postoperative ocular hypertension, what does the term 'refractory' mean?",
            "options": [
                "Resolving spontaneously without intervention.",
                "Responsive to the first line of prophylactic treatment.",
                "Resistant to normal treatment or difficult to control.",
                "Occurring strictly before the surgery."
            ],
            "answer": "Resistant to normal treatment or difficult to control.",
            "explanation": "正確！'Refractory' 在醫學上指的是對一般治療沒有反應、難以控制或頑固性的情況。"
        }
    },
    "犬貓 CKD 臨床營養與處方飼料": {
        "english_text": "Dietary modification is the cornerstone of managing feline chronic kidney disease. However, palatability often hinders compliance. When transitioning a stage 3 CKD cat to a renal diet, how do you balance phosphate restriction with the paramount importance of maintaining lean body mass?",
        "vocab": "cornerstone (基石/核心), hinder compliance (阻礙配合度), paramount importance (至關重要)",
        "chinese_translation": "飲食調整是管理貓慢性腎病（CKD）的基石。然而，適口性往往會影響配合度。在將第三期 CKD 的貓咪轉換為腎臟處方飼料時，您如何平衡『限制磷攝取』與『維持瘦體重（肌肉量）』這兩項至關重要的目標？",
        "sample_answer": "I prioritize caloric intake and lean body mass; if renal diets are rejected, I prefer a highly palatable senior diet combined with intestinal phosphate binders.\n(我優先考量熱量攝取與維持瘦體重；如果貓咪排斥腎臟處方飼料，我會選擇適口性佳的高齡貓飼料搭配腸道磷結合劑。)",
        "quiz": {
            "question": "Why is transitioning a cat to a renal diet often challenging in clinical practice?",
            "options": [
                "Renal diets typically cause severe gastrointestinal upset.",
                "Palatability issues frequently hinder patient compliance.",
                "Phosphate binders in the diet negate the effects of medication.",
                "Owners usually refuse to change the diet."
            ],
            "answer": "Palatability issues frequently hinder patient compliance.",
            "explanation": "正確！文段中提到 'palatability often hinders compliance'，適口性不佳是導致病患不配合（拒食）的最大阻礙。"
        }
    }
}

topics = list(content_library.keys())

tasks = [
    {"name": "🗣️ 影子跟讀 (Shadowing)", "desc": "先聽一次發音。接著戴上耳機，按下播放，講者說什麼慢 0.5 秒跟著唸，模仿語氣。"},
    {"name": "🎤 Q&A 實戰模擬", "desc": "聽完問題後，給自己 2 分鐘全英文口頭回答。回答完再點開下方解答核對。"},
    {"name": "📝 臨床口頭摘要", "desc": "聽完語音後，用自己的話將這段內容濃縮，向學員做 3 分鐘精華報告。"}
]

st.title("🏃 VetSpeak 15 每日研討會特訓")

if "topic" not in st.session_state:
    st.session_state.topic = None
if "task" not in st.session_state:
    st.session_state.task = None
# 加入一個狀態來記住測驗是否已作答
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if st.button("🚀 抽取今日特訓任務"):
    st.session_state.topic = random.choice(topics)
    st.session_state.task = random.choice(tasks)
    st.session_state.quiz_submitted = False # 重新抽題時重置作答狀態

if st.session_state.topic and st.session_state.task:
    st.success("任務生成成功！")
    st.subheader(f"📌 今日主題：{st.session_state.topic}")
    st.markdown(f"**🎯 訓練方式：{st.session_state.task['name']}**")
    st.write(st.session_state.task["desc"])
    
    st.divider()
    st.markdown("### 📖 今日特訓內容")
    
    text_to_read = content_library[st.session_state.topic]["english_text"]
    
    with st.spinner("🎧 正在生成專業講者語音..."):
        tts = gTTS(text=text_to_read, lang='en', tld='us') 
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')
        
    st.info(text_to_read)
    st.markdown("**💡 關鍵語塊 (Lexical Chunks)：**")
    st.write(content_library[st.session_state.topic]["vocab"])
    
    with st.expander("👁️ 點我核對中文翻譯與示範解答"):
        st.markdown("**【中文翻譯】**")
        st.write(content_library[st.session_state.topic]["chinese_translation"])
        st.markdown("**【C1 程度示範解答 / 摘要】**")
        st.write(content_library[st.session_state.topic]["sample_answer"])
        
    st.divider()
    st.markdown("### 🧠 隨堂小測驗 (Pop Quiz)")
    quiz_data = content_library[st.session_state.topic]["quiz"]
    st.write(quiz_data["question"])
    
    # 建立選擇題 UI
    user_choice = st.radio("請選擇最適合的答案：", quiz_data["options"], index=None, key=f"quiz_{st.session_state.topic}")
    
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
    st.write("⏱️ **15 分鐘專注計時器**")
    
    if st.button("開始計時"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        for percent_complete in range(100):
            time.sleep(9) 
            progress_bar.progress(percent_complete + 1)
            status_text.text(f"特訓進行中... {percent_complete + 1}%")
        st.balloons()
        st.success("🎉 今日 15 分鐘特訓完成！")
