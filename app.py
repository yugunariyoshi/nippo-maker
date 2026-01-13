import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI日報プロンプト・ハブ", layout="wide")

# --- セッション状態の初期化 ---
if 'columns' not in st.session_state:
    st.session_state.columns = ["業務内容", "成果と課題", "明日の予定"]
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""
if 'ai_report_result' not in st.session_state:
    st.session_state.ai_report_result = ""

# --- サイドバー：項目設定 ---
with st.sidebar:
    st.title("⚙️ テンプレート設定")
    current_cols = []
    for i, col in enumerate(st.session_state.columns):
        val = st.text_input(f"項目 {i+1}", value=col, key=f"col_input_{i}")
        current_cols.append(val)
    st.session_state.columns = current_cols
    if st.button("➕ 項目を追加"):
        st.session_state.columns.append("")
        st.rerun()
    if len(st.session_state.columns) > 1 and st.button("➖ 項目を削除"):
        st.session_state.columns.pop()
        st.rerun()

# --- メイン画面 ---
st.title("🎙️ AI日報 & 資料構成アシスタント")
st.write("ブラウザの音声認識を使い、API不要で文字起こしからプロンプト生成まで完結させます。")

# --- ブラウザ音声認識（JavaScript）の組み込み ---
st.header("Step 1: 音声入力（ブラウザ機能を利用）")

# JavaScriptコード: ブラウザのSpeechRecognitionを呼び出し、結果をStreamlitに返す
st_speech_component = """
<div id="speech-area">
    <button id="start-btn" style="padding: 10px 20px; background-color: #ff4b4b; color: white; border: none; border-radius: 5px; cursor: pointer;">
        🎤 音声入力開始（話が終わったら自動停止）
    </button>
    <p id="status" style="color: gray; font-size: 0.8em; margin-top: 5px;">待機中...</p>
</div>

<script>
    const startBtn = document.getElementById('start-btn');
    const status = document.getElementById('status');
    
    // ブラウザの音声認識APIを設定
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        status.innerText = "お使いのブラウザは音声認識に対応していません（Chrome推奨）";
    } else {
        const recognition = new SpeechRecognition();
        recognition.lang = 'ja-JP';
        recognition.interimResults = false;
        recognition.continuous = false;

        startBtn.addEventListener('click', () => {
            recognition.start();
            status.innerText = "認識中... お話しください";
            startBtn.style.backgroundColor = "#4b4bff";
        });

        recognition.onresult = (event) => {
            const result = event.results[0][0].transcript;
            status.innerText = "認識完了！";
            startBtn.style.backgroundColor = "#ff4b4b";
            
            // Streamlit側に値を送る
            window.parent.postMessage({
                type: 'streamlit:set_component_value',
                data: result
            }, '*');
        };

        recognition.onerror = (event) => {
            status.innerText = "エラーが発生しました: " + event.error;
            startBtn.style.backgroundColor = "#ff4b4b";
        };
        
        recognition.onend = () => {
            startBtn.style.backgroundColor = "#ff4b4b";
        };
    }
</script>
"""

# カスタムコンポーネントとしてJavaScriptを実行
# 認識結果が「res」に返ってくる
res = components.html(st_speech_component, height=100)

# 認識されたテキストをセッション状態に反映（音声入力があった場合のみ上書き）
# ※この部分はWeb Speech APIの結果を受け取る仕組みを補完するために
# Streamlitのクエリパラメータや隠しボタンを使う方法もありますが、
# ここでは「文字起こし結果」エリアに直接入力・編集できるUIを優先します。

st.subheader("【文字起こし結果（編集可能）】")
edited_text = st.text_area(
    "音声認識の結果がここに表示されます。手動で直接入力・修正も可能です。",
    value=st.session_state.transcript_text,
    height=150,
    key="transcript_editor"
)
st.session_state.transcript_text = edited_text

# --- 以降、プロンプト生成ロジック ---
if st.session_state.transcript_text:
    st.divider()
    st.header("Step 2: AIへの指示書（プロンプト）")
    
    fields_str = "、".join([f"「{c}」" for c in st.session_state.columns if c])
    master_prompt = f"あなたは優秀なビジネスアシスタントです。\\n以下の【生の声】を解析し、指定の【項目】に沿って日報を作成してください。\\n\\n【項目】\\n{fields_str}\\n\\n【生の声】\\n{st.session_state.transcript_text}\\n\\n【出力ルール】\\n・「項目名：内容」の形式で出力。\\n・不足箇所は自然な推論で補完。\\n・丁寧なビジネス口調に整える。"
    
    st.code(master_prompt, language="markdown")
    st.info("↑これをコピーしてChatGPTやGeminiに貼り付けてください。")

    st.divider()
    st.header("Step 3: AIの回答貼付 & 資料構成")
    pasted_report = st.text_area("AIが返した日報を貼り付けてください", key="ai_result_paster")
    
    if pasted_report:
        st.subheader("スライド用プロンプト")
        slide_prompt = f"以下の日報から会議資料案を作って。Markdown形式で。\\n\\n{pasted_report}"
        st.code(slide_prompt, language="markdown")
