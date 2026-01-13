import streamlit as st
import streamlit.components.v1 as components

# 1. アプリの設定
st.set_page_config(page_title="AI日報プロンプト・ハブ", layout="wide", page_icon="🎙️")

# --- セッション状態の管理 ---
if 'columns' not in st.session_state:
    st.session_state.columns = ["業務内容", "成果と課題", "明日の予定"]
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""

# カラムのプレースホルダー例文
examples = [
    "例：今日は午前中にA社へ訪問、午後は資料作成をしました...",
    "例：システムのバグを特定し修正完了。ただ検証が一部未完了です...",
    "例：明日は10時から定例会議、午後はB社への見積書送付です...",
    "例：顧客から要望のあった新機能について検討が必要です...",
    "例：事務作業が溜まっているので、午前中に一気に片付けます..."
]

# --- 2. サイドバー設定 ---
with st.sidebar:
    st.title("⚙️ 日報項目設定")
    st.info("会社や助成金に合わせて項目を追加してください。")
    
    new_cols = []
    for i, col in enumerate(st.session_state.columns):
        # カラムの中に薄字で例文を表示
        p_text = examples[i] if i < len(examples) else "例：内容を入力してください..."
        val = st.text_input(f"項目 {i+1}", value=col, placeholder=p_text, key=f"col_input_{i}")
        current_val = val
        new_cols.append(current_val)
    st.session_state.columns = new_cols

    if st.button("➕ 項目を追加"):
        st.session_state.columns.append("")
        st.rerun()
    
    if len(st.session_state.columns) > 1 and st.button("➖ 最後の項目を削除"):
        st.session_state.columns.pop()
        st.rerun()

# --- 3. メイン画面：音声入力パネル ---
st.title("🎙️ AI日報 & 会議資料ハブ")

st.header("Step 1: 音声入力（API不要）")
st.markdown("#### **今日あったことを音声で入力してください。整理されてなくても大丈夫です。**")
st.write("「録音開始」を押して自由に話し、終わったら「停止」を押してください。")

# JavaScript: ブラウザで音声認識し、結果をボタンに表示 & 自動コピー
st_speech_html = """
<div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #ced4da; text-align: center;">
    <button id="start-btn" style="background-color: #ff4b4b; color: white; padding: 12px 24px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">🎤 録音開始</button>
    <button id="stop-btn" style="background-color: #4b4bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; margin-left: 10px;">⏹️ 停止・コピー</button>
    <p id="status" style="margin-top: 15px; font-weight: bold; color: #1f1f1f;">待機中...</p>
    <textarea id="temp-result" style="width: 100%; height: 80px; margin-top: 10px; border-radius: 5px; border: 1px solid #ddd; padding: 10px; font-size: 14px;" placeholder="ここに話した内容がリアルタイムで表示されます..."></textarea>
    <p style="font-size: 0.8em; color: #666; margin-top: 5px;">※停止ボタンを押すと、自動的にクリップボードへコピーされます。</p>
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
        status.innerText = "🎤 認識中... 独り言のようにお話しください";
        textArea.value = "";
    };

    stopBtn.onclick = () => {
        recognition.stop();
        status.innerText = "✅ コピー完了！下の枠に貼り付けて内容を確認してください。";
        textArea.select();
        document.execCommand('copy'); 
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
components.html(st_speech_html, height=250)

# --- 4. 編集可能なテキストエリア ---
st.subheader("📝 文字起こし内容の確認・編集")
st.info("上の「停止・コピー」を押した後、下の枠をクリックして「貼り付け（Ctrl+V / ⌘+V）」をしてください。")

edited_text = st.text_area(
    "話した内容の「生データ」です。誤字があってもAIが修正するので、そのままでもOK！",
    value=st.session_state.transcript_text,
    height=200,
    key="main_editor",
    placeholder="ここに音声を貼り付けてください..."
)
st.session_state.transcript_text = edited_text

if st.button("内容をクリアして最初からやり直す"):
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

【生の声（文字起こしデータ）】
{st.session_state.transcript_text}

【出力ルール】
1. 各項目を「項目名：内容」の形式で整理してください。
2. 音声の内容が不足している項目は、前後の文脈から自然な内容を推論して補完するか、一般的な事務作業として埋めてください。
3. 文体は丁寧なビジネス文書（です・ます調）に整えてください。
---
    """
    st.code(master_prompt, language="markdown")
    st.success("指示書が完成しました！これをコピーしてChatGPTやGeminiに貼り付けてください。")

    st.divider()
    st.header("Step 3: 会議資料の構成案を作る")
    ai_report = st.text_area("AIから返ってきた日報テキストをここに貼り付けてください", key="ai_report_paster", height=150)
    
    if ai_report:
        st.subheader("🚀 資料作成用プロンプト")
        slide_prompt = f"以下の日報を元に、会議用スライドの構成案をMarkdown形式で作成してください。\\n\\n{ai_report}"
        st.code(slide_prompt, language="markdown")

st.markdown("---")
st.caption("No-API & User-Friendly Design | 快適な日報ライフを。")
