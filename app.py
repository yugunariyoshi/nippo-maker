import streamlit as st

# アプリの基本設定
st.set_page_config(page_title="AI日報プロンプト・ハブ", layout="wide")

# --- 1. セッション状態の初期化 ---
# 日報の項目（カラム）管理
if 'columns' not in st.session_state:
    st.session_state.columns = ["業務内容", "成果と課題", "明日の予定"]

# 文字起こしテキストの保持用
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""

# AIからの回答（日報完成版）の保持用
if 'ai_report_result' not in st.session_state:
    st.session_state.ai_report_result = ""

# --- 2. サイドバー：日報項目の設定（動的カラム追加） ---
with st.sidebar:
    st.title("⚙️ 日報テンプレート設定")
    st.write("必要な項目を編集・追加してください。")
    
    current_cols = []
    for i, col in enumerate(st.session_state.columns):
        val = st.text_input(f"項目 {i+1}", value=col, key=f"col_input_{i}")
        current_cols.append(val)
    st.session_state.columns = current_cols

    if st.button("➕ 項目を追加"):
        st.session_state.columns.append("")
        st.rerun()
    
    if len(st.session_state.columns) > 1:
        if st.button("➖ 最後の項目を削除"):
            st.session_state.columns.pop()
            st.rerun()
    
    st.divider()
    st.caption("※ここで設定した項目が、AIへの指示書（プロンプト）に自動反映されます。")

# --- 3. メイン画面：Step 1 音声入力とプロンプト生成 ---
st.title("🎙️ AI日報 & 会議資料構成アシスタント")
st.write("「話す → プロンプトをコピー → 外部AIに貼る」の最短ルートを提供します。")

st.header("Step 1: 録音と内容確認")

col_a, col_b = st.columns([1, 1])

with col_a:
    st.subheader("1. 音声を録音")
    # Streamlit標準の音声入力
    audio_data = st.audio_input("ここを押して話してください")
    
    if audio_data:
        st.audio(audio_data)
        st.info("💡 録音したファイルをGeminiやChatGPTにアップロードして使用します。")
        # ※ブラウザの機能等で文字起こしが自動入力される想定の場合、
        # ここに文字起こし結果をsession_stateに入れるロジックを追加できます。

with col_b:
    st.subheader("2. 文字起こし内容（編集可能）")
    # セッション状態を直接 text_area の値として使う
    # keyを指定することで、リロードしても入力内容が保持される
    edited_text = st.text_area(
        "AIに渡す「話した内容」を確認・修正してください。クリックしても消えません。",
        value=st.session_state.transcript_text,
        height=200,
        key="transcript_editor" 
    )
    # 入力があるたびにセッション状態を更新
    st.session_state.transcript_text = edited_text

    if st.button("内容をリセット"):
        st.session_state.transcript_text = ""
        st.rerun()

# --- 4. Step 2 AI（Gemini/ChatGPT）への指示書 ---
st.divider()
st.header("Step 2: AIへの指示書（プロンプト）")

if not st.session_state.transcript_text:
    st.warning("まずは上の「文字起こし内容」に今日の内容を入力してください。")
else:
    fields_str = "、".join([f"「{c}」" for c in st.session_state.columns if c])
    
    master_prompt = f"""
あなたは優秀なビジネスアシスタントです。
以下の【生の声】を解析し、指定の【項目】に沿って日報を作成してください。

【項目】
{fields_str}

【生の声】
{st.session_state.transcript_text}

【出力ルール】
・「項目名：内容」の形式で出力してください。
・音声の内容が不足している項目は、前後の文脈から自然な推論で補完してください。
・ビジネス向けの丁寧な言葉遣いに整えてください。
---
    """
    
    st.code(master_prompt, language="markdown")
    st.write("↑このプロンプトをコピーして、録音ファイルと一緒にGeminiやChatGPTに貼り付けてください。")

# --- 5. Step 3 AIの回答を取り込んで資料化 ---
st.divider()
st.header("Step 3: 完成した日報の貼付 ＆ 資料構成案")

pasted_report = st.text_area(
    "AIが生成した日報テキストをここに貼り付けてください",
    value=st.session_state.ai_report_result,
    height=200,
    key="ai_result_paster"
)
st.session_state.ai_report_result = pasted_report

if st.session_state.ai_report_result:
    st.success("日報情報を読み込みました。資料構成案（プロンプト）を作成します。")
    
    col_sl1, col_sl2 = st.columns(2)
    
    with col_sl1:
        st.subheader("資料の味付け")
        tpl = st.selectbox("構成テンプレート", [
            "社内提案用（背景→課題→解決策→効果）", 
            "社内協議用（目的→論点→相談→決定事項）", 
            "報告用（実績→問題点→今後の対策）"
        ])
        tone = st.selectbox("トーン設定", ["コンバル風", "カジュアル", "パッション系"])

    with col_sl2:
        st.subheader("スライド用プロンプト")
        slide_prompt = f"""
以下の日報内容を元に、会議用のスライド構成案を作成してください。

【資料設定】
・目的：{tpl}
・トーン：{tone}

【日報内容】
{st.session_state.ai_report_result}

【出力依頼】
・スライド5〜7枚程度の構成。
・各スライドの「タイトル」と「内容の要点（箇条書き）」。
・Markdown形式で構造化して出力してください。
        """
        st.code(slide_prompt, language="markdown")
        st.write("↑このプロンプトを再度AIに投げれば、プレゼン資料の骨子が完成します。")

st.markdown("---")
st.caption("No API Key Mode | Session State Protected")
