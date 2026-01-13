import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI日報プロンプト・ハブ", layout="wide")

# --- 1. セッション状態の管理 ---
if 'columns' not in st.session_state:
    st.session_state.columns = ["業務内容", "成果と課題", "明日の予定"]
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""

# --- 2. サイドバー設定 ---
with st.sidebar:
    st.title("⚙️ 日報項目設定")
    new_cols = []
    for i, col in enumerate(st.session_state.columns):
        val = st.text_input(f"項目 {i+1}", value=col, key=f"col_input_{i}")
        new_cols.append(val)
    st.session_state.columns = new_cols
    if st.button("➕ 項目を追加"):
        st.session_state.columns.append(""); st.rerun()

# --- 3. メイン画面：音声入力パネル ---
st.title("🎙️ AI日報 & 資料構成ハブ")
st.header("Step 1: 音声入力（API不要）")

# JavaScript: ブラウザで音声認識し、結果をボタンに表示 & 自動コピーを促す
st_speech_html = """
<div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #ced4da; text-align: center;">
    <button id="start-btn" style="background-color: #ff4b4b; color: white; padding: 12px 24px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">🎤 録音開始</button>
    <button id="stop-btn" style="background-color: #4b4bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; margin-left: 10px;">⏹️ 停止・コピー</button>
    <p id="status" style="margin-top: 15px; font-weight: bold; color: #1f1f1f;">待機中...</p>
    <textarea id="temp-result" style="width: 100%; height: 60px; margin-top: 10px; border-radius: 5px; border: 1px solid #ddd; padding: 5px;" placeholder="ここに文字起こしがリアルタイムで表示されます..."></textarea>
    <p style="font-size: 0.8em; color: #666; margin-top: 5px;">停止すると自動でクリップボードにコピーされます</p>
</div>

<script>
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const status = document.getElementById('status');
    const textArea = document.getElementById('temp-result');

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'ja-JP';
    recognition.continuous = true;
    recognition.interimResults = true;

    startBtn.onclick = () => {
        recognition.start();
        status.innerText = "🎤 認識中... お話しください";
        textArea.value = "";
    };

    stopBtn.onclick = () => {
        recognition.stop();
        status.innerText = "✅ 完了！クリップボードにコピーしました。下の枠に貼り付けてください。";
        textArea.select();
        document.execCommand('copy'); // クリップボードにコピー
    };

    recognition.onresult = (event) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        textArea.value = transcript;
    };
</script>
"""

# JavaScriptコンポーネントを表示
components.html(st_speech_html, height=220)

# --- 4. 編集可能なテキストエリア ---
st.subheader("📝 文字起こし結果の確認・編集")
st.caption("録音を停止したら、この下の枠をクリックして「貼り付け（Ctrl+V）」をしてください。")

edited_text = st.text_area(
    "ここがAIに渡される「生の声」になります。自由に書き換えても消えません。",
    value=st.session_state.transcript_text,
    height=200,
    key="main_editor"
)
st.session_state.transcript_text = edited_text

if st.button("リセット"):
    st.session_state.transcript_text = ""
    st.rerun()

# --- 5. プロンプト生成 ---
if st.session_state.transcript_text:
    st.divider()
    st.header("Step 2: AIへの指示書（プロンプト）")
    
    fields_str = "、".join([f"「{c}」" for c in st.session_state.columns if c])
    master_prompt = f"""
あなたはプロのビジネスアシスタントです。以下の【生の声】を解析し、指定の【項目】に沿って日報を作成してください。

【項目】
{fields_str}

【生の声】
{st.session_state.transcript_text}

【出力ルール】
・「項目名：内容」の形式で出力。
・不足箇所は自然に補完し、ビジネス文書に整える。
    """
    st.code(master_prompt, language="markdown")
    st.info("↑これをコピーしてChatGPT/Geminiに貼り付けてください。")

    st.divider()
    st.header("Step 3: AIの回答貼付 & 資料構成")
    ai_report = st.text_area("AIが返した日報を貼り付け", key="ai_report_paster")
    
    if ai_report:
        st.subheader("会議スライド用プロンプト")
        st.code(f"以下の日報からスライド構成案を作って。\\n\\n{ai_report}", language="markdown")

st.markdown("---")
st.caption("Browser Recognition + Clipboard Sync | No-API Mode")
