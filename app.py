import streamlit as st
import random
import time

st.set_page_config(page_title="VetSpeak 15", page_icon="🩺", layout="centered")

# 專屬專業資料庫
topics = [
    "Myxomatous Mitral Valve Disease (MMVD) 分期與 MINE 評分",
    "小動物白內障手術 (Phacoemulsification) 術後併發症",
    "犬貓慢性腎病的臨床營養介入與處方飼料解析",
    "心臟超音波 (Echocardiography) 測量指標與預後評估",
    "貓慢性齒齦炎 (FCGS) 的疼痛管理"
]

tasks = [
    {"name": "高密度泛聽 (Extensive Listening)", "desc": "專注聽講者的開場、轉折語與結論，不需查單字。"},
    {"name": "影子跟讀 (Shadowing)", "desc": "戴上耳機，講者說什麼，慢 0.5 秒跟著唸，模仿語氣與連音。"},
    {"name": "Q&A 實戰模擬", "desc": "聽一段問題，按暫停，給自己 1 分鐘口頭全英文回答。"},
    {"name": "3分鐘口頭摘要", "desc": "假裝自己是講者，用英文總結這個主題的核心臨床處置邏輯。"}
]

st.title("🏃 VetSpeak 15 每日研討會特訓")
st.write("每天 15 分鐘，無障礙征服國際獸醫研討會。")

if st.button("🚀 抽取今日特訓任務"):
    today_topic = random.choice(topics)
    today_task = random.choice(tasks)
    
    st.success("任務生成成功！")
    st.subheader(f"📌 今日主題：{today_topic}")
    st.markdown(f"**🎯 訓練方式：{today_task['name']}**")
    st.write(today_task["desc"])
    
    st.divider()
    st.write("⏱️ **15 分鐘專注計時器**")
    
    # 簡單的進度條計時器 (網頁版示意)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    if st.button("開始計時"):
        for percent_complete in range(100):
            time.sleep(9) # 15分鐘 = 900秒，每次推進 1% 約 9 秒
            progress_bar.progress(percent_complete + 1)
            status_text.text(f"特訓進行中... {percent_complete + 1}%")
        st.balloons()
        st.success("🎉 今日 15 分鐘特訓完成！臨床實力又提升了一點。")