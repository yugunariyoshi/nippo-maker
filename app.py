import streamlit as st

# アプリの設定
st.set_page_config(page_title="AI日報 & 資料構成ハブ", layout="wide")

# --- セッション状態の初期化 ---
if 'columns' not in st.session_state:
    st.session_state.columns = ["業務内容", "成果と課題", "明日の予定"]

# --- サイドバー：日報項目の設定 ---
with st.sidebar:
    st.title("⚙️ 日報テンプレート設定")
    st.write("会社や助成金に合わせて項目を調整してください。")
    
    new_columns = []
    for i, col in enumerate(st.session_state.columns):
        c = st.text_input(f"項目 {i+1}", value=col, key=f"col_input_{i}")
        new_columns.append(c)
    
    st.session_state.columns = new_columns

    if st.button("➕ 項目を追加"):
        st.session_state.columns.append("")
        st.rerun()
    
    if len(st.session_state.columns) > 1:
        if st.button("➖ 最後の項目を削除"):
            st.session_state.columns.pop()
            st.rerun()

# --- メイン画面 ---
st.title("🎙️ AI日報 & 会議資料構成アシスタント")
st.write("API課金なしで、あなたの声を最高の成果物に変えます。")

# --- STEP 1: 音声録音と初期プロンプト生成 ---
st.header("Step 1: 録音と指示書の作成")
col_audio, col_prompt = st.columns([1, 1])

with col_audio:
    st.subheader("1. 音声を録音")
    audio_value = st.audio_input("今日あったことを自由に話してください")
    if audio_value:
        st.audio(audio_value)
        st.info("💡 録音したファイルを右クリックで保存するか、そのまま外部AI（Gemini/ChatGPT）に音声ファイルとしてアップロードしてください。")

with col_prompt:
    st.subheader("2. AIへの指示書（プロンプト）")
    fields_str = "、".join([f"「{c}」" for c in st.session_state.columns if c])
    
    initial_prompt = f"""
今からアップロードする音声ファイルを聴いて、以下の項目に沿って日報を作成してください。
内容が不足している箇所は、前後の文脈から自然な内容を推論して補完してください。

【抽出項目】
{fields_str}

【出力形式】
必ず以下の形式で出力してください。
項目名：内容
---
    """
    st.code(initial_prompt, language="markdown")
    st.write("↑この指示文をコピーして、音声ファイルと一緒にGeminiやChatGPTに投げて下さい。")

# --- STEP 2: AI回答の取り込み ---
st.divider()
st.header("Step 2: AIの回答を取り込む")
ai_result = st.text_area("GeminiやChatGPTが返してきた日報内容をここに貼り付けてください", height=200)

# --- STEP 3: 資料化プロンプトの生成 ---
if ai_result:
    st.divider()
    st.header("Step 3: 会議資料の「種」を作る")
    
    col_slide1, col_slide2 = st.columns(2)
    
    with col_slide1:
        st.subheader("資料の味付けを選択")
        tpl = st.selectbox("資料の目的（構成案）", [
            "社内提案用（背景→課題→解決策→効果）", 
            "社内協議用（目的→論点→相談→決定事項）", 
            "報告用（実績→問題点→今後の対策）",
            "社外提案用（貴社の現状→解決案→メリット→事例）"
        ])
        tone = st.selectbox("トンマナ（口調）", [
            "コンサルフォーマル（論理的・簡潔）", 
            "社内カジュアル（前向き・スピード感）",
            "パッション系（ビジョン・熱意重視）"
        ])

    with col_slide2:
        st.subheader("スライド生成用プロンプト")
        
        slide_prompt = f"""
先ほど作成した日報の内容を元に、会議資料の構成案を作成してください。

【資料設定】
・目的：{tpl}
・トーン：{tone}

【元情報（日報内容）】
{ai_result}

【出力依頼】
・スライド5〜7枚程度の構成にしてください。
・各スライドの「タイトル」と「話す内容の要点（箇条書き）」を提示してください。
・スライド生成AIにそのまま流し込めるような、構造化されたMarkdown形式で出力してください。
        """
        st.code(slide_prompt, language="markdown")
        st.write("↑このプロンプトを再度AIに投げれば、資料の構成案が完成します。")
        
        if st.button("🚀 スライド生成アプリ（Gamma等）を開く"):
            st.write("（ここに外部サービスへのリンクなどを設定可能）")

st.markdown("---")
st.caption("Developed for High-Efficiency Reporting | No API Key Required")
