import streamlit as st

# --- サイドバー：初期設定 ---
with st.sidebar:
    st.title("⚙️ テンプレート設定")
    report_items = st.text_area("日報の項目", "業務内容, 成果と課題, 明日の予定")
    
    st.divider()
    st.subheader("スライド設定")
    slide_tpl = st.selectbox("テンプレート", ["社内提案用", "報告用", "社外協議用"])
    tone = st.selectbox("トンマナ", ["コンサルフォーマル", "社内カジュアル"])

# --- メイン画面 ---
st.title("🎙️ AI日報プロンプト生成器")

# 音声入力（ブラウザの機能を利用）
# ※ st.audio_inputは現在録音のみ。文字起こしには別途JavaScript連携か
#   スマホのキーボードの音声入力を使ってもらうのが一番「API不要」に近いです。
raw_text = st.text_area("ここに話した内容を入力（音声入力ボタンを活用してください）", height=200)

if st.button("AIへのプロンプトを生成する"):
    # プロンプトの組み立て
    master_prompt = f"""
あなたは優秀な秘書です。以下の【生の声】を解析し、指定の形式で出力してください。

### 1. 日報作成
以下の項目に沿って、ビジネス文章として整理してください。
項目：{report_items}

### 2. 会議資料構成（オプション）
目的：{slide_tpl}
トーン：{tone}
これに基づいたスライド構成案も作成してください。

---
【生の声】
{raw_text}
---
    """
    
    st.subheader("📋 生成されたプロンプト")
    st.code(master_prompt, language="markdown")
    st.info("↑これをコピーして、ChatGPTやGeminiに貼り付けてください。")