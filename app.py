import streamlit as st
import random
import time
from gtts import gTTS
import io
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="VetSpeak 15", page_icon="🩺", layout="centered")

# --- 1分鐘演講長度題庫區 ---
content_library = {
    "MMVD 分期與 MINE 評分": {
        "english_text": "Thank you all for being here. Today, I'd like to address a common clinical dilemma we face in veterinary cardiology: the precise timing to initiate pimobendan in dogs with Myxomatous Mitral Valve Disease. We all know that the transition from Stage B1 to Stage B2 is a critical decision point based on the ACVIM consensus guidelines. However, in routine practice, we frequently encounter 'grey-zone' cases where echocardiographic parameters, specifically the LA to Ao ratio and LVIDDN, are borderline. They might perfectly straddle the established cut-offs. This is precisely where integrating the MINE score becomes invaluable. Rather than relying solely on a rigid, binary classification, the MINE score provides granular prognostic stratification. By evaluating a combination of clinical and echocardiographic variables, it allows us to individualize pharmacological intervention. Ultimately, this multiparametric approach ensures we don't delay life-prolonging therapy in high-risk patients, while preventing premature medication in truly stable B1 dogs.",
        "vocab": "critical decision point (關鍵決策點), perfectly straddle the cut-offs (剛好卡在臨界值邊緣), granular prognostic stratification (細緻的預後分級), multiparametric approach (多參數評估法)",
        "chinese_translation": "各位好，感謝參與。今天我想探討獸醫心臟科常見的臨床難題：犬黏液瘤性二尖瓣疾病（MMVD）開始使用 pimobendan 的精確時機。我們都知道，根據 ACVIM 共識指南，從 B1 期進展到 B2 期是開始投藥的關鍵決策點。然而在常規臨床實踐中，我們經常遇到「模糊地帶」的病例，其超音波參數（特別是 LA:Ao 和 LVIDDN）處於臨界值，甚至剛好卡在標準的邊緣。這正是結合 MINE 評分發揮極大價值的地方。與其單純依賴僵化的二分法，MINE 評分提供了更細緻的預後分層。透過評估多項臨床與超音波變數的組合，它使我們能為病患量身制定藥物介入時機。最終，這種多參數的評估方法能確保我們不會延誤高風險病患的延長壽命治療，同時避免對真正穩定的 B1 期犬隻過早投藥。",
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
        "english_text": "Moving on to postoperative care in veterinary ophthalmology, I want to emphasize the management of postoperative ocular hypertension, or POH. This is a frequent and potentially vision-threatening complication following phacoemulsification in dogs, particularly within the first 24 hours post-op. Despite our best prophylactic efforts, we still see patients developing acute spikes in intraocular pressure. My protocol for these critical hours involves hourly monitoring of IOP. When dealing with refractory POH—cases that do not respond to first-line topical anti-glaucoma medications—we must be prepared to escalate our therapy aggressively. This might involve adding systemic carbonic anhydrase inhibitors or administering hyperosmotic agents like intravenous mannitol, provided the patient’s cardiovascular and renal status permits. The key takeaway here is that early, aggressive intervention is paramount. If we fail to aggressively manage these refractory pressure spikes, we risk irreversible damage to the optic nerve and retina, ultimately compromising the entire surgical success.",
        "vocab": "vision-threatening complication (威脅視力的併發症), prophylactic efforts (預防措施), refractory POH (難以控制的高眼壓), escalate our therapy aggressively (積極升級治療)",
        "chinese_translation": "接下來談到獸醫眼科的術後照護，我想強調術後高眼壓（POH）的管理。這是犬隻晶體乳化術後常見且可能威脅視力的併發症，特別是在術後前 24 小時內。儘管我們做了最完善的預防措施，仍會遇到病患出現急性眼壓飆升。我在這段關鍵時間的準則包含每小時監測眼壓。當處理難以控制（refractory）的高眼壓——也就是對第一線局部抗青光眼藥物無反應的病例時，我們必須準備好積極升級治療。這可能包含加入全身性碳酸酐酶抑制劑，或是給予高滲透壓藥物如靜脈注射甘露醇，前提是病患的心血管與腎臟狀況允許。這裡的重點是，早期且積極的介入至關重要。如果我們未能積極控制這些頑固性的眼壓飆升，將面臨視神經與視網膜不可逆損傷的風險，最終破壞整個手術的成功。",
        "sample_answer": "My protocol includes hourly monitoring of IOP and aggressive use of topical medications, escalating to systemic therapy if it remains refractory.\n(我的準則包含每小時監測眼壓並積極使用局部藥物，若眼壓仍難以控制則升級為全身性治療。)",
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
        "english_text": "Let’s shift our focus to clinical nutrition, specifically the dietary management of feline chronic kidney disease. We universally accept that dietary modification is the absolute cornerstone of managing CKD. However, in real-world clinical practice, we often face a significant hurdle: palatability frequently hinders patient compliance. This becomes especially challenging when transitioning a Stage 3 CKD cat to a heavily restricted renal diet. The clinical dilemma is how we balance essential phosphate restriction with the paramount importance of maintaining caloric intake and lean body mass. If a cat outright rejects the renal diet, forcing it can lead to starvation and muscle wasting, which dramatically worsens the prognosis. Therefore, my approach is pragmatic. I prioritize caloric intake and lean body mass above all. If traditional renal diets are rejected, I prefer to utilize a highly palatable senior diet combined with intestinal phosphate binders to achieve our target serum phosphorus levels.",
        "vocab": "cornerstone (基石/核心), hinder patient compliance (阻礙病患配合度), paramount importance (至關重要), pragmatic approach (務實的方法/策略)",
        "chinese_translation": "讓我們將焦點轉向臨床營養，特別是貓慢性腎病（CKD）的飲食管理。我們都認同，飲食調整絕對是管理 CKD 的基石。然而，在真實的臨床實踐中，我們常面臨一個重大障礙：適口性往往會阻礙病患的配合度。當我們試圖將第三期 CKD 的貓咪轉換為嚴格限制的腎臟處方飼料時，這項挑戰變得格外艱鉅。臨床上的兩難在於，我們該如何平衡「限制磷攝取」以及「維持熱量攝取與瘦體重（肌肉量）」這兩項至關重要的目標。如果貓咪完全拒絕處方飼料，強迫餵食可能導致飢餓與肌肉流失，這會大幅惡化預後。因此，我的方法很務實：我將熱量攝取和維持瘦體重放在首位。如果傳統腎臟處方飼料被拒絕，我傾向使用適口性極佳的高齡貓飼料，並搭配腸道磷結合劑，來達到我們目標的血清磷濃度。",
        "sample_answer": "I prioritize caloric intake and lean body mass; if renal diets are rejected, I adopt a pragmatic approach using a palatable senior diet with phosphate binders.\n(我優先考量熱量攝取與維持瘦體重；如果處方飼料被拒絕，我會採取務實的方法，使用適口性佳的高齡貓飼料搭配磷結合劑。)",
        "quiz": {
            "question": "Why is transitioning a cat to a renal diet often challenging in clinical practice?",
            "options": [
                "Renal diets typically cause severe gastrointestinal upset.",
                "Palatability issues frequently hinder patient compliance.",
                "Phosphate binders in the diet negate the effects of medication.",
                "Owners usually refuse to change the diet."
            ],
            "answer": "Palatability issues frequently hinder patient compliance.",
            "explanation": "正確！文段中提到 'palatability frequently hinders patient compliance'，適口性不佳是導致病患不配合（拒食）的最大阻礙。"
        }
    }
}

topics = list(content_library.keys())
tasks = [
    {"name": "🗣️ 影子跟讀 (Shadowing)", "desc": "先聽一次發音。接著戴上耳機，按下播放，講者說什麼慢 0.5 秒跟著唸，注意換氣與斷句。"},
    {"name": "🎤 Q&A 實戰模擬", "desc": "聽完這段 1 分鐘的引言後，給自己 2 分鐘全英文口頭發表你的觀點。"},
    {"name": "📝 臨床口頭摘要", "desc": "聽完語音後，用自己的話將這 1 分鐘的內容濃縮，向學員做 30 秒的精華報告。"}
]

# --- 狀態管理區 ---
if "topic" not in st.session_state:
    st.session_state.topic = None
if "task" not in st.session_state:
    st.session_state.task = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "learning_log" not in st.session_state:
    st.session_state.learning_log = pd.DataFrame(columns=["日期", "主題", "訓練方式", "自我評分"])

# --- UI 介面區 ---
st.title("🏃 VetSpeak 15 每日研討會特訓")

tab1, tab2 = st.tabs(["🚀 今日特訓", "📈 學習紀錄"])

with tab1:
    if st.button("🚀 抽取今日特訓任務"):
        st.session_state.topic = random.choice(topics)
        st.session_state.task = random.choice(tasks)
        st.session_state.quiz_submitted = False

    if st.session_state.topic and st.session_state.task:
        st.success("任務生成成功！")
        st.subheader(f"📌 今日主題：{st.session_state.topic}")
        st.markdown(f"**🎯 訓練方式：{st.session_state.task['name']}**")
        st.write(st.session_state.task["desc"])
        
        st.divider()
        st.markdown("### 📖 今日特訓內容")
        
        text_to_read = content_library[st.session_state.topic]["english_text"]
        
        # 產生 1 分鐘的語音 (載入可能需要稍等幾秒)
        with st.spinner("🎧 正在生成 1 分鐘專業講者語音，請稍候..."):
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
                "主題": st.session_state.topic,
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
