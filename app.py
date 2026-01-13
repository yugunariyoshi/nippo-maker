import streamlit as st

# 1. アプリの設定
st.set_page_config(page_title="AI日報プロンプト・ハブ", layout="wide", page_icon="🎙️")

# --- セッション状態の初期化（入力内容を保護するため） ---
if 'columns' not in st.session_state:
    st.session_state.columns = ["業務内容", "成果と課題", "明日の予定"]
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""
if 'ai_report_result' not in st.session_state:
    st.session_state.ai_report_result = ""

# --- 2. サイドバー：日報項目の設定 ---
with st.sidebar:
    st.title("⚙️ テンプレート設定")
    st.info("会社や助成金で必要な項目を追加してください。")
    
    current_cols = []
    for i, col in enumerate(st.session_state.columns):
        val = st.text_input(f"項目 {i+1}", value=col, key=f"col_input_{i}")
        current_cols.append(val)
    st.session_state.columns = current_cols

    if st.button("➕ 項目を追加"):
        st.session_state.columns.append("")
        st.rerun()
    
    if len(st.session_state.columns) > 1 and st.button("➖ 最後の項目を削除"):
        st.session_state.columns.pop()
        st.rerun()

# --- 3. メイン画面：入力セクション ---
st.title("🎙️ AI日報 & 資料構成アシスタント")
st.markdown("""
### Step 1: 今日あったことを話す
下のテキストエリアをクリックして、**PCやスマホの音声入力機能**を使って話してください。
- **Windows:** `Win + H` / **Mac:** `Fn 2回` / **スマホ:** `マイクボタン`
""")

# 編集可能なテキストエリア（session_stateで保護）
edited_text = st.text_area(
    "【入力エリア】話した内容がここにリアルタイムで入ります（編集も自由）",
    value=st.session_state.transcript_text,
    height=250,
    key="main_transcript_area",
    help="音声入力ショートカットを使って入力してください。クリックしても消えません。"
)
st.session_state.transcript_text = edited_text

if st.button("入力をリセット"):
    st.session_state.transcript_text = ""
    st.rerun()

# --- 4. Step 2: AIへの指示書（プロンプト）生成 ---
if st.session_state.transcript_text:
    st.divider()
    st.header("Step 2: AIへの指示書（プロンプト）")
    st.write("この内容をコピーして、ChatGPTやGeminiに貼り付けてください。")

    fields_str = "、".join([f"「{c}」" for c in st.session_state.columns if c])
    
    # 最高の回答を引き出すためのプロンプト設計
    master_prompt = f"""
あなたはプロのビジネスアシスタントです。以下の【生の声】を解析し、指定の【項目】に沿って日報を作成してください。

【項目】
{fields_str}

【生の声（文字起こしデータ）】
{st.session_state.transcript_text}

【出力ルール】
1. 各項目を「項目名：内容」の形式で整理してください。
2. 音声で語られていない項目は、前後の文脈から自然な内容を推論して補完するか、一般的な事務作業として埋めてください。
3. 文体は丁寧なビジネス文書（です・ます調）に整えてください。
---
    """
    
    st.code(master_prompt, language="markdown")
    st.success("プロンプトが作成されました！コピーしてAIに投げて下さい。")

    # --- 5. Step 3: AIの回答を取り込んで資料化 ---
    st.divider()
    st.header("Step 3: AIの回答を貼り付けて資料化へ")
    
    pasted_report = st.text_area(
        "AIが返してきた日報テキストをここに貼り付けてください",
        value=st.session_state.ai_report_result,
        height=200,
        key="ai_paster"
    )
    st.session_state.ai_report_result = pasted_report

    if st.session_state.ai_report_result:
        st.info("日報を読み込みました。次に「会議資料用」の指示書を生成します。")
        
        col1, col2 = st.columns(2)
        with col1:
            tpl = st.selectbox("資料の構成", ["社内提案用", "社内協議用", "進捗報告用", "社外提案用"])
            tone = st.selectbox("トーン", ["コンサルフォーマル", "社内カジュアル", "情熱的"])
        
        with col2:
            slide_prompt = f"""
以下の日報内容に基づき、会議用スライドの構成案を作成してください。
目的：{tpl}
トーン：{tone}

【日報内容】
{st.session_state.ai_report_result}

【出力形式】
スライド5〜8枚構成で、各スライドの「タイトル」と「箇条書きの要点」をMarkdown形式で出力してください。
そのままスライド生成AI（Gammaなど）に流し込める形式にしてください。
            """
            st.code(slide_prompt, language="markdown")
            st.write("↑このプロンプトをAIに投げれば、資料の骨子が完成します。")

st.markdown("---")
st.caption("No-API / No-Glitch Design | © AI Nippo Assistant")
