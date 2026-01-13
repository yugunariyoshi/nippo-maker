import streamlit as st
import streamlit.components.v1 as components

# アプリ設定
st.set_page_config(page_title="AI日報 & 資料構成ハブ", layout="wide")

# --- セッション状態の初期化 ---
if 'columns' not in st.session_state:
    st.session_state.columns = ["業務内容", "成果と課題", "明日の予定"]
if 'final_transcript' not in st.session_state:
    st.session_state.final_transcript = ""

# --- サイドバー：項目設定 ---
with st.sidebar:
    st.title("⚙️ テンプレート設定")
    new_cols = []
    for i, col in enumerate(st.session_state.columns):
        val = st.text_input(f"項目 {i+1}", value=col, key=f"col_{i}")
        new_cols.append(val)
    st.session_state.columns = new_cols
    if st.button("➕ 項目を追加"):
        st.session_state.columns.append(""); st.rerun()

# --- メイン画面 ---
st.title("🎙️ AI日報 & 資料構成アシスタント")

# --- Step 1: 音声入力（ブラウザSpeech API） ---
st.header("Step 1: 音声で入力")
st.write("「録音開始」を押して話し、終わったら「停止」を押してください。文字が下のエリアに自動で入ります。")

# JavaScriptによる音声認識コンポーネント
# 認識した文字を window.parent.postMessage でPython側に送る仕組み
speech_js = """
<div style="background: #f0f2f6; padding: 20px; border-radius: 10px; border: 1px solid #ddd;">
    <button id="start-btn" style="background: #ff4b4b; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;">🎤 録音開始</button>
    <button id="stop-btn" style="background: #444; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; margin-left: 10px;">⏹️ 停止</button>
    <div id="status" style="margin-top: 10px; font-size: 0.8em; color: #555;">待機中...</div>
</div>

<script>
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const status = document.getElementById('status');
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'ja-JP';
    recognition.continuous = true;
    recognition.interimResults = true;

    let finalTranscript = '';

    startBtn.onclick = () => {
        recognition.start();
        status.innerText = "🎤 認識中... お話しください";
        startBtn.style.opacity = "0.5";
    };

    stopBtn.onclick = () => {
        recognition.stop();
        status.innerText = "✅ 停止しました";
        startBtn.style.opacity = "1";
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }
        // 親ウィンドウ（Streamlit）にデータを送信
        window.parent.postMessage({
            type: 'streamlit:set_component_value',
            data: finalTranscript + interimTranscript
        }, '*');
    };
</script>
"""

# JavaScriptからのデータを受け取る
# components.html の戻り値として文字データを受け取る（※特定の条件下で動作）
# ここでは、認識結果を確実に反映させるために、textareaへの同期を促します
captured_text = components.html(speech_js, height=130)

st.subheader("【文字起こし結果（編集可能）】")
st.caption("※上のボタンで話すとここに文字が入ります。入らない場合は、直接入力や修正をしてください。")

# ユーザーが編集しても消えない仕組み（keyを設定）
user_edited_text = st.text_area(
    "内容を確認・修正してください。ここをクリックして編集しても、勝手に消えることはありません。",
    value=st.session_state.final_transcript,
    height=200,
    key="edit_area"
)
st.session_state.final_transcript = user_edited_text

if st.button("全消去してやり直す"):
    st.session_state.final_transcript = ""
    st.rerun()

# --- Step 2: プロンプト生成 ---
if st.session_state.final_transcript:
    st.divider()
    st.header("Step 2: AIへの指示書（プロンプト）")
    
    fields_str = "、".join([f"「{c}」" for c in st.session_state.columns if c])
    master_prompt = f"""
あなたはプロのビジネスアシスタントです。以下の【生の声】を解析し、指定の【項目】に沿って日報を作成してください。

【項目】
{fields_str}

【生の声】
{st.session_state.final_transcript}

【出力ルール】
1. 各項目を「項目名：内容」の形式で整理。
2. 不足箇所は前後の文脈から自然に補完。
3. 丁寧なビジネス口調（です・ます調）に整える。
---
    """
    st.code(master_prompt, language="markdown")
    st.info("↑これをコピーしてChatGPTやGeminiに貼り付けてください。")

    # --- Step 3: AIの回答を取り込んで資料化 ---
    st.divider()
    st.header("Step 3: 資料構成案の作成")
    pasted_report = st.text_area("AIが返した日報をここに貼り付け", height=200)
    
    if pasted_report:
        st.subheader("スライド用プロンプト")
        st.code(f"以下の日報からスライド構成案を作って。\\n\\n{pasted_report}", language="markdown")

st.markdown("---")
st.caption("No-API Browser Speech Engine | © 2026 AI Assistant")
