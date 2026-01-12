import streamlit as st
import yaml

# アプリの設定
st.set_page_config(page_title="AI日報 & スライド構成ハブ", layout="wide")

# --- スライドタイプのYAML設定（ここを編集することで挙動を固められます） ---
SLIDE_TYPES_YAML = """
コンサル・ロジカル:
  style: "結論ファースト、定量的、ロジカルシンキングに基づいた構造"
  visual_density: "中（図解の余白を残しつつ、論理を詰め込む）"
  max_slides: 7
  format: "Executive Summary -> Analysis -> Proposal -> Expected ROI"

ビジュアル・プレゼン:
  style: "1スライド1メッセージ、大きな画像と短いキャッチコピー"
  visual_density: "低（文字を極限まで減らす）"
  max_slides: 10
  format: "Vision -> Problem -> Solution -> Big Impact"

社内スピード報告:
  style: "事実中心、アクションプラン重視、装飾不要"
  visual_density: "高（1枚に情報を集約して議論を早める）"
  max_slides: 4
  format: "Current Status -> Issues -> Next Actions"
"""

# YAMLの読み込み
slide_configs = yaml.safe_load(SLIDE_TYPES_YAML)

# --- セッション状態の初期化 ---
if 'columns' not in st.session_state:
    st.session_state.columns = ["業務内容", "成果と課題", "明日の予定"]

# --- サイドバー：設定エリア ---
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

# STEP 1: 録音と指示
st.header("Step 1: 音声から日報を作る")
col_audio, col_prompt = st.columns([1, 1])

with col_audio:
    st.subheader("1. 音声を録音")
    audio_value = st.audio_input("今日の出来事を話してください")

with col_prompt:
    st.subheader("2. 外部AIへの指示")
    fields_str = "、".join([f"「{c}」" for c in st.session_state.columns if c])
    initial_prompt = f"音声ファイルを聴いて、以下の項目で日報を作成してください。：{fields_str}"
    st.code(initial_prompt, language="markdown")

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
        purpose = st.selectbox("スライドの使用目的", [
            "社内提案（予算やリソースの確保）", 
            "社内協議（論点の整理と意思決定）", 
            "社外提案（新規受注・信頼獲得）",
            "定例報告（進捗共有とリスク報告）"
        ])
    with c2:
        st_type = st.selectbox("スライドタイプ（YAML設定）", list(slide_configs.keys()))

    # 選択されたYAML設定の取得
    config = slide_configs[st_type]
    
    # 最終的なスライド生成AI用プロンプトの組み立て
    final_slide_prompt = f"""
あなたはプロの資料作成エキスパートです。以下の【日報データ】を元に、スライド生成AI（Gamma等）に最適化された構成案を作成してください。

### 【制約条件（YAML設定に基づく）】
- スタイル: {config['style']}
- 視覚的密度: {config['visual_density']}
- 最大スライド数: {config['max_slides']}
- 基本構成: {config['format']}

### 【スライドの使用目的】
{purpose}

### 【元データ（日報内容）】
{ai_result}

### 【出力指示】
1. 各スライドのタイトルと、そのスライドに記載する箇条書きの要点を提示してください。
2. スライド生成AIが構造を理解しやすいよう、Markdownの階層構造（#や##）で出力してください。
3. 日報にない情報は、目的（{purpose}）に沿って、説得力を高めるための「仮説」として補足してください。
    """
    
    st.subheader("🚀 スライド作成AI（Gamma/Tome等）へ渡すプロンプト")
    st.code(final_slide_prompt, language="markdown")
    st.success("このプロンプトをスライド生成AIに貼り付ければ、資料が完成します！")
