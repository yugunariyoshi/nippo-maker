import streamlit as st
import streamlit.components.v1 as components
import yaml

# アプリの設定
st.set_page_config(page_title="AI日報 & 資料構成ハブ", layout="wide")

# --- スライドタイプのYAML設定 ---
SLIDE_TYPES_YAML = """
コンサル・ロジカル:
  style: "結論ファースト、定量的、ロジカル構造"
  visual_density: "中（図解の余白を残す）"
  max_slides: 7
  format: "Executive Summary -> Analysis -> Proposal -> ROI"

ビジュアル・プレゼン:
  style: "1スライド1メッセージ、キャッチコピー重視"
  visual_density: "低（文字を極限まで減らす）"
  max_slides: 10
  format: "Vision -> Problem -> Solution -> Impact"

社内スピード報告:
  style: "事実中心、アクションプラン重視"
  visual_density: "高（1枚に情報を集約）"
  max_slides: 4
  format: "Status -> Issues -> Next Actions"
"""
slide_configs = yaml.safe_load(SLIDE_TYPES_YAML)

# --- セッション状態の初期化 ---
if 'columns' not in st.session_state:
    st.session_state.columns = ["業務内容", "成果と課題", "明日の予定"]
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""

# --- サイドバー：設定 ---
with st.sidebar:
    st.title("⚙️ 設定")
    st.subheader("日報項目の設定")
    for i, col in enumerate(st.session_state.columns):
        st.session_state.columns[i] = st.text_input(f"項目 {i+1}", value=col, key=f"col_{i}")
    if st.button("➕ 項目を追加"):
        st.session_state.columns.append("")
        st.rerun()

# --- メイン画面 ---
st.title("🎙️ AI日報 & 資料構成ハブ")

st.header("Step 1: 今日あったことを話す")

# ブラウザの音声認識（Web Speech API）を呼び出すJavaScript
# 認識した結果をStreamlitのテキストエリアに反映させる仕組み
st.markdown("### 🎙️ 音声入力")
st.write("「音声認識スタート」を押して話し、終わったら「停止」してください。")

# JavaScriptコード
st_components_html = """
<div style="padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
    <button id="start-btn" style="padding: 10px 20px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">🎤 音声認識スタート</button>
    <button id="stop-btn" style="padding: 10px 20px; background-color: #f44336; color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;">🛑 停止</button>
    <p id="status" style="color: gray; font-size: 0.8em; margin-top: 10px;">待機中...</p>
</div>

<script>
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const status = document.getElementById('status');
    
    let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'ja-JP';
    recognition.interimResults = true;
    recognition.continuous = true;

    startBtn.onclick = () => {
        recognition.start();
        status.innerText = "認識中... お話しください。";
        status.style.color = "red";
    };

    stopBtn.onclick = () => {
        recognition.stop();
        status.innerText = "停止しました。";
        status.style.color = "gray";
    };

    recognition.onresult = (event) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            }
        }
        if (finalTranscript) {
            // StreamlitのSession Stateに値を送るためのハック（隠し入力フィールドを使用）
            const textArea = window.parent.document.querySelector('textarea[aria-label="【文字起こし結果（編集可能）】"]');
            if (textArea) {
                textArea.value += finalTranscript;
                textArea.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    };
</script>
"""

components.html(st_components_html, height=120)

# 文字起こし結果の表示・編集エリア
st.session_state.transcript = st.text_area("【文字起こし結果（編集可能）】", value=st.session_state.transcript, height=150)

# --- プロンプト生成 ---
if st.session_state.transcript:
    st.subheader("2. AIへの指示（プロンプト）")
    fields_str = "、".join([f"「{c}」" for c in st.session_state.columns if c])
    
    # 認識されたテキストが最初からプロンプトに組み込まれる
    initial_prompt = f"""
以下の【生の声】を解析して、指定の項目に沿って日報を作成してください。
内容が足りない部分は、文脈から推論して補完してください。

【抽出項目】
{fields_str}

【生の声】
{st.session_state.transcript}

【出力形式】
項目名：内容
---
    """
    st.code(initial_prompt, language="markdown")
    st.info("↑このプロンプトをコピーしてGemini/ChatGPTに投げて下さい。音声ファイルをアップロードする必要もありません。")

# STEP 2: AI回答の取り込み
st.divider()
st.header("Step 2: AIの回答を取り込む")
ai_result = st.text_area("Gemini/ChatGPTからの回答をここに貼り付けてください", height=150)

# STEP 3: スライド生成用プロンプト作成
if ai_result:
    st.divider()
    st.header("Step 3: スライド作成AI用プロンプト生成")
    
    c1, c2 = st.columns(2)
    with c1:
        purpose = st.selectbox("使用目的", ["社内提案", "社内協議", "社外提案", "定例報告"])
    with c2:
        st_type = st.selectbox("スライドタイプ", list(slide_configs.keys()))

    config = slide_configs[st_type]
    
    final_slide_prompt = f"""
以下の日報データを元に、スライド構成案を作成してください。

【制約】
- スタイル: {config['style']}
- 枚数: 最大{config['max_slides']}
- 構成: {config['format']}
- 目的: {purpose}

【日報データ】
{ai_result}

出力はMarkdown形式で、各スライドのタイトルと要点を箇条書きでお願いします。
    """
    st.code(final_slide_prompt, language="markdown")
