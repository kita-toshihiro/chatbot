import requests
import streamlit as st

# タイトルと説明の表示
st.title("💬 チャットボット（Ollama: gemma4-200k）")
st.write("`http://jula2.ield.kumamoto-u.ac.jp:11434` の Ollama サーバー上のモデルを利用して応答を生成します。")

# 必要に応じて Streamlit Secrets（.streamlit/secrets.toml）からベースURLを上書き可能
ollama_base_url = st.secrets.get(
    "OLLAMA_BASE_URL",
    "http://jula2.ield.kumamoto-u.ac.jp:11434",
).rstrip("/")

model_name = st.secrets.get("OLLAMA_MODEL", "gemma4-200k:latest")
st.write(f"接続先: `{ollama_base_url}` / モデル: **{model_name}**")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 既存のチャットメッセージを表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザーがメッセージを入力するためのチャット入力フィールド
if prompt := st.chat_input("ここにメッセージを入力"):
    # ユーザーのプロンプトを保存・表示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Ollama /api/chat 向けに messages 形式を準備
    chat_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    api_url = f"{ollama_base_url}/api/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": chat_messages,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.8,
        },
    }

    try:
        with st.chat_message("assistant"):
            # 200kコンテキストや初回ロード時は時間がかかる場合があるためタイムアウトを長めに設定
            with st.spinner(f"{model_name} が応答を生成中..."):
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=120,
                )
                response.raise_for_status()

                result = response.json()
                message_obj = result.get("message") or {}
                reply = message_obj.get("content")

                if not reply:
                    reply = f"エラー: 応答テキストが見つかりませんでした。詳細: {result}"

                st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

    except requests.exceptions.RequestException as e:
        error_message = f"APIリクエストエラーが発生しました: {e}"
        st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})
    except Exception as e:
        error_message = f"予期せぬエラーが発生しました: {e}"
        st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})
