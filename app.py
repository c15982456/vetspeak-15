import streamlit as st
import random
import time

st.set_page_config(page_title="VetSpeak 15", page_icon="🩺", layout="centered")

# 建立真實的臨床英文題庫
content_library = {
    "MMVD 分期與 MINE 評分": {
        "english_text": "We know the transition from Stage B1 to B2 is a critical decision point for initiating pimobendan based on the ACVIM consensus guidelines. In your clinical experience, how does integrating the MINE score help in those 'grey-zone' cases where echocardiographic parameters like LA:Ao and LVIDDN are borderline?",
        "vocab": "critical decision point (關鍵決策點), borderline (處於邊緣的), grey-zone cases (模糊地帶案例)"
    },
    "白內障手術 (Phacoemulsification) 術後併發症": {
        "english_text": "Postoperative ocular hypertension (POH) is a frequent and potentially vision-threatening complication following phacoemulsification in dogs. What is your protocol for monitoring and managing refractory POH in the first 24 hours post-op?",
        "vocab": "vision-threatening complication (威脅視力的併發症), prophylactic (預防性的), refractory (難以控制的/頑固性的)"
    },
    "犬貓 CKD 臨床營養與處方飼料": {
        "english_text": "Dietary modification is the cornerstone of managing feline chronic kidney disease. However, palatability often hinders compliance. When transitioning a stage 3 CKD cat to a renal diet, how do you balance phosphate restriction with the paramount importance of maintaining lean body mass?",
        "vocab": "cornerstone (基石/核心), hinder compliance (阻礙配合度), paramount importance (至關重要)"
    }
}

topics = list(content_library.keys())

tasks = [
    {"name": "🗣️ 影子跟讀 (Shadowing)", "desc": "大聲朗讀下方內容，注意專業術語的發音與學術語氣。"},
    {"name": "🎤 Q&A 實戰模擬", "desc": "將下方內容視為聽眾的發問，不寫草稿，給自己 2 分鐘全英文回答。"},
    {"name": "📝 臨床口頭摘要", "desc": "假裝你是講者，用自己的話將下方內容濃縮，向家屬或學員做 3 分鐘精華報告。"}
]

st.title("🏃 VetSpeak 15 每日研討會特訓")

if "topic" not in st.session_state:
    st.session_state.topic = None
if "task" not in st.session_state:
    st.session_state.task = None

if st.button("🚀 抽取今日特訓任務"):
    st.session_state.topic = random.choice(topics)
    st.session_state.task = random.choice(tasks)

if st.session_state.topic and st.session_state.task:
    st.success("任務生成成功！")
    st.subheader(f"📌 今日主題：{st.session_state.topic}")
    st.markdown(f"**🎯 訓練方式：{st.session_state.task['name']}**")
    st.write(st.session_state.task["desc"])
    
    # 顯示真正的英文訓練內容！
    st.divider()
    st.markdown("### 📖 今日特訓內容")
    st.info(content_library[st.session_state.topic]["english_text"])
    st.markdown("**💡 關鍵語塊 (Lexical Chunks)：**")
    st.write(content_library[st.session_state.topic]["vocab"])
    
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
