import streamlit as st
import google.generativeai as genai
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import re

# --- ページ設定 ---
st.set_page_config(page_title="Silver Sentinel AI", page_icon="⚖️")
st.title("⚖️ Silver Sentinel v4.0")
st.caption("powered by Jenny (Gemini 2.0 Flash)")

# --- APIキーの設定（GitHubのSecretsから読み込む） ---
#
YOUTUBE_KEY = st.secrets["YOUTUBE_KEY"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]
USD_JPY = 150.0

# Gemini 2.0 Flash の設定
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# セッション状態（会話の記憶）の初期化
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# --- 関数群 ---
def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_cost(usage):
    """"""
    in_cost = (usage.prompt_token_count / 1000000) * 0.10 * USD_JPY
    out_cost = (usage.candidates_token_count / 1000000) * 0.40 * USD_JPY
    return in_cost + out_cost

# --- メイン画面 ---
st.markdown("### 🔍 YouTube要約 & チャート解析")
input_url = st.text_input("YouTube動画 または チャート画像のURLを貼り付けてください")

if st.button("分析を実行", type="primary"):
    if input_url:
        with st.spinner("ジェニーが解析中..."):
            try:
                v_id = extract_video_id(input_url)
                if v_id:
                    # YouTube要約
                    res = requests.get(f"https://www.googleapis.com/youtube/v3/videos?key={YOUTUBE_KEY}&id={v_id}&part=snippet").json()
                    title = res['items'][0]['snippet']['title']
                    try:
                        transcript = YouTubeTranscriptApi.get_transcript(v_id, languages=['ja'])
                        text = " ".join([t['text'] for t in transcript])
                    except:
                        text = res['items'][0]['snippet']['description']
                    prompt = f"銀CFD投資家の視点で、この動画を要約してください。\n\nタイトル: {title}\n内容: {text[:6000]}"
                    response = st.session_state.chat_session.send_message(prompt)
                else:
                    # チャート解析
                    img_data = requests.get(input_url).content
                    prompt = "銀CFDのプロトレーダーとして、このチャートを分析してください。"
                    response = st.session_state.chat_session.send_message([prompt, {'mime_type': 'image/jpeg', 'data': img_data}])

                st.success("分析完了！")
                st.info(f"💰 推定コスト: {get_cost(response.usage_metadata):.4f} 円")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# --- 追加質問エリア ---
if st.session_state.chat_session.history:
    st.divider()
    st.markdown("### 💬 ジェニーに詳しく聞く")
    user_query = st.text_input("質問を入力してください（例：月曜日の損切りラインは？）")
    if st.button("質問する"):
        with st.spinner("回答中..."):
            response = st.session_state.chat_session.send_message(user_query)
            st.write(f"🤖 **ジェニー:** {response.text}")
            st.caption(f"コスト: {get_cost(response.usage_metadata):.4f} 円")
