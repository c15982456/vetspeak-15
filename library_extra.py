# 新增內建題庫。內容為一般臨床共識的口說教材，使用前請以你的專業判斷為準。
# 格式與 library.py 相同：想再加題目，複製一組貼在最後即可。
extra_library = {
    "犬急性胰臟炎：止痛與早期營養": {
        "english_text": "In canine acute pancreatitis, pain control and nutrition are often undertreated. Abdominal pain is frequently severe, so multimodal analgesia, usually built around opioids, should start early rather than waiting for the patient to deteriorate. Traditionally, we fasted these dogs for days. However, current evidence supports early enteral nutrition, ideally within twenty-four to forty-eight hours, as it preserves gut barrier integrity and reduces complications. If vomiting persists despite antiemetics such as maropitant, a feeding tube becomes a reasonable option. Ultimately, treating the patient, not the cPLI result, should guide every decision we make.",
        "vocab": "multimodal analgesia (多模式止痛), early enteral nutrition (早期腸道營養), gut barrier integrity (腸道屏障完整性), antiemetics (止吐藥)",
        "chinese_translation": "犬急性胰臟炎中，疼痛控制與營養支持常被忽略。腹痛往往很嚴重，因此應及早開始以鴉片類為基礎的多模式止痛，而不是等到病況惡化。傳統上我們會讓這些犬隻禁食數天，但目前證據支持早期腸道營養，最好在二十四至四十八小時內開始，因為這能維持腸道屏障完整並減少併發症。若使用 maropitant 等止吐藥後仍持續嘔吐，放置餵食管是合理的選擇。最終，應以病患本身而非 cPLI 數值來引導每個決定。",
        "sample_answer": "Early enteral nutrition and multimodal analgesia improve outcomes in canine pancreatitis. (早期腸道營養與多模式止痛可改善犬胰臟炎的預後。)",
        "qa_question": "How do you decide when a feeding tube is justified in a vomiting dog?",
        "quiz": {
            "question": "According to the talk, what is the current recommendation for nutrition in acute canine pancreatitis?",
            "options": ["Fast the patient for several days", "Start early enteral nutrition within 24 to 48 hours", "Use only parenteral nutrition", "Wait until cPLI normalizes"],
            "answer": "Start early enteral nutrition within 24 to 48 hours",
            "explanation": "正確！講稿指出目前證據支持在 24–48 小時內開始早期腸道營養，而非長時間禁食。"
        }
    },
    "貓慢性腎臟病：IRIS 分期與副分期": {
        "english_text": "In feline chronic kidney disease, the IRIS staging system relies on fasting creatinine and SDMA, ideally confirmed on at least two occasions in a stable, hydrated patient. However, staging alone is insufficient. We must also substage by proteinuria and blood pressure, because both independently influence progression and prognosis. Persistent hypertension warrants treatment, commonly with amlodipine, while significant proteinuria may justify an angiotensin receptor blocker such as telmisartan. Alongside a renal diet, which has been shown to prolong survival, these targeted interventions can meaningfully slow the decline in function.",
        "vocab": "IRIS staging (IRIS 分期), substage (副分期), proteinuria (蛋白尿), angiotensin receptor blocker (血管張力素受體阻斷劑)",
        "chinese_translation": "在貓慢性腎臟病中，IRIS 分期依據空腹肌酸酐與 SDMA，最好在穩定且水分充足的病患身上至少確認兩次。然而，單靠分期並不足夠。我們還必須依蛋白尿與血壓做副分期，因為兩者都會獨立影響疾病進展與預後。持續性高血壓需要治療，常用 amlodipine；顯著蛋白尿則可考慮使用 telmisartan 等血管張力素受體阻斷劑。搭配已證實能延長存活期的腎臟病處方飲食，這些針對性介入可有效減緩腎功能下降。",
        "sample_answer": "Staging by creatinine and SDMA must be complemented by proteinuria and blood pressure substaging. (以肌酸酐與 SDMA 分期後，仍須搭配蛋白尿與血壓副分期。)",
        "qa_question": "At what blood pressure threshold do you start amlodipine in a calm, hydrated cat?",
        "quiz": {
            "question": "Why does the speaker say staging alone is insufficient?",
            "options": ["Because creatinine is unreliable in all cats", "Because proteinuria and blood pressure independently affect progression", "Because SDMA cannot be measured in cats", "Because a renal diet replaces staging"],
            "answer": "Because proteinuria and blood pressure independently affect progression",
            "explanation": "正確！蛋白尿與血壓都會獨立影響進展與預後，所以要做副分期。"
        }
    },
    "犬皮膚肥大細胞瘤：組織學分級": {
        "english_text": "In canine cutaneous mast cell tumors, histologic grading remains our most important prognostic tool. The two-tier Kiupel system classifies tumors as low or high grade, and high-grade tumors are associated with a significantly shorter survival time. Surgical excision is the cornerstone of treatment, and wide margins are recommended, commonly around two centimeters laterally and one fascial plane deep. For high-grade or incompletely excised tumors, we should consider adjuvant therapy and assess the regional lymph nodes. Importantly, grading must always be interpreted alongside clinical stage and the owner’s goals.",
        "vocab": "histologic grading (組織學分級), prognostic tool (預後工具), wide margins (廣泛切除邊界), adjuvant therapy (輔助治療)",
        "chinese_translation": "在犬皮膚肥大細胞瘤中，組織學分級仍是最重要的預後工具。Kiupel 二級分類系統將腫瘤分為低級別與高級別，高級別腫瘤的存活時間明顯較短。手術切除是治療基石，建議廣泛邊界，常見做法是側向約兩公分、深層一個筋膜層。對於高級別或切除不完全的腫瘤，應考慮輔助治療並評估區域淋巴結。重要的是，分級必須搭配臨床分期與飼主的目標一併解讀。",
        "sample_answer": "Grading guides prognosis, but surgery with wide margins remains the cornerstone. (分級可指引預後，但廣泛邊界手術仍是治療基石。)",
        "qa_question": "How do you counsel owners when the margins come back incomplete on a low-grade tumor?",
        "quiz": {
            "question": "Which tumors does the speaker say should prompt consideration of adjuvant therapy?",
            "options": ["Only low-grade tumors", "High-grade or incompletely excised tumors", "Any tumor smaller than two centimeters", "Tumors with no lymph node involvement"],
            "answer": "High-grade or incompletely excised tumors",
            "explanation": "正確！講稿指出高級別或切除不完全的腫瘤應考慮輔助治療並評估區域淋巴結。"
        }
    },
    "休克的分次輸液與重複評估": {
        "english_text": "When resuscitating a hypovolemic patient, I avoid giving the entire calculated shock dose as a single bolus. Instead, we administer fluids in smaller aliquots, typically a quarter to a third of the shock dose, and reassess perfusion after each one. We look at heart rate, mucous membrane color, capillary refill time, pulse quality and blood pressure. This stepwise approach allows us to restore perfusion while minimizing the risk of volume overload, which is particularly important in cats and in patients with cardiac or renal disease. Reassessment, not the arithmetic, is what makes fluid therapy safe.",
        "vocab": "hypovolemic (低血容的), aliquots (分次小劑量), perfusion (組織灌流), volume overload (容量過載)",
        "chinese_translation": "復甦低血容病患時，我不會把計算出的休克劑量一次推完。我們會分成較小的劑量給予，通常是休克劑量的四分之一到三分之一，並在每一次後重新評估灌流狀況。我們觀察心跳、黏膜顏色、微血管再充填時間、脈搏品質與血壓。這種逐步的方式能在恢復灌流的同時，降低容量過載的風險，對貓以及有心臟或腎臟疾病的病患尤其重要。讓輸液治療安全的是重複評估，而不是計算本身。",
        "sample_answer": "Fluids in aliquots with reassessment restore perfusion while limiting volume overload. (分次輸液並重複評估，可恢復灌流並限制容量過載。)",
        "qa_question": "Which perfusion parameter do you trust most when you reassess a cat after a bolus?",
        "quiz": {
            "question": "Why are fluids given in aliquots with reassessment?",
            "options": ["To save fluids", "To restore perfusion while limiting volume overload", "Because boluses are never effective", "To avoid measuring blood pressure"],
            "answer": "To restore perfusion while limiting volume overload",
            "explanation": "正確！分次給予並重複評估，能在恢復灌流的同時降低容量過載風險。"
        }
    },
    "多模式止痛與局部麻醉": {
        "english_text": "Multimodal analgesia targets different points along the nociceptive pathway, allowing us to use lower doses of each drug with fewer side effects. By giving analgesics preemptively, we help prevent central sensitization, often called wind-up, which makes postoperative pain harder to control. Locoregional techniques, such as dental or intercostal blocks with bupivacaine, also reduce inhalant requirements and therefore dose-dependent hypotension. However, we must calculate the maximum local anesthetic dose carefully, particularly in cats and small patients.",
        "vocab": "nociceptive pathway (痛覺傳導路徑), central sensitization (中樞敏感化), locoregional techniques (局部區域麻醉技術), inhalant requirements (吸入麻醉劑需求量)",
        "chinese_translation": "多模式止痛針對痛覺傳導路徑上的不同位置，讓我們每種藥物都能用較低劑量，副作用也較少。預先給予止痛藥，有助於預防中樞敏感化（常稱為 wind-up），否則術後疼痛會更難控制。以 bupivacaine 進行的牙科或肋間神經阻斷等局部區域技術，還能減少吸入麻醉劑的需求，進而降低劑量依賴性低血壓。不過，我們必須仔細計算局部麻醉藥的最大劑量，尤其是貓和小型病患。",
        "sample_answer": "Preemptive multimodal analgesia and local blocks reduce pain and anesthetic requirements. (預先的多模式止痛與局部阻斷可減少疼痛與麻醉需求。)",
        "qa_question": "Which local blocks do you routinely perform in your dental patients, and why?",
        "quiz": {
            "question": "What is one benefit of locoregional blocks mentioned in the talk?",
            "options": ["They eliminate the need for monitoring", "They reduce inhalant requirements and hypotension", "They remove the need for opioids entirely", "They work only in large dogs"],
            "answer": "They reduce inhalant requirements and hypotension",
            "explanation": "正確！局部區域阻斷能減少吸入麻醉劑需求，因此降低劑量依賴性低血壓。"
        }
    },
}
