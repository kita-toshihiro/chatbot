import requests
import streamlit as st

# タイトルと説明の表示
st.title("💬 チャットボット（Cloudflare Workers AI）")
st.write("Cloudflare Workers AI の OpenAI互換 Chat Completions API を利用して応答を生成します。")

# Streamlit Community CloudのSecretsから認証情報を取得
# .streamlit/secrets.toml に以下を設定してください:
# CF_ACCOUNT_ID = "YOUR_ACCOUNT_ID"
# CF_API_TOKEN = "YOUR_API_TOKEN"
cf_account_id = st.secrets.get("CF_ACCOUNT_ID")
cf_api_token = st.secrets.get("CF_API_TOKEN")

if not cf_account_id or not cf_api_token:
    st.info(
        "Streamlit の Secrets に `CF_ACCOUNT_ID` と `CF_API_TOKEN` を設定してください。",
        icon="🗝️",
    )
else:
    # ユーザーがモデルを選択できるようにする（利用可能なモデルIDに変更してください）
    model_name = st.selectbox(
        "使用する Cloudflare Workers AI モデルを選択",
        (
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            "@cf/qwen/qwen2.5-coder-32b-instruct",
        ),
    )
    st.write(f"現在のモデル: **{model_name}**")

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

        # OpenAI互換の messages 形式に変換
        chat_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        # Cloudflare Workers AI の OpenAI互換エンドポイント
        api_url = (
            f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}"
            "/ai/v1/chat/completions"
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cf_api_token}",
        }

        payload = {
            "model": model_name,
            "messages": chat_messages,
            "temperature": 0.7,
            "top_p": 0.8,
        }

        try:
            # アシスタントの応答をチャットメッセージコンテナ内に表示
            with st.chat_message("assistant"):
                with st.spinner(f"{model_name} が応答を生成中..."):
                    response = requests.post(
                        api_url,
                        headers=headers,
                        json=payload,
                        timeout=30,
                    )
                    response.raise_for_status()

                    result = response.json()
                    choices = result.get("choices") or []

                    if choices:
                        choice = choices[0]
                        finish_reason = choice.get("finish_reason")
                        message_obj = choice.get("message") or {}
                        content = message_obj.get("content")

                        if finish_reason == "length":
                            reply = "応答が途中で終了しました（トークン上限超過）。"
                        elif content:
                            reply = content
                        else:
                            reply = f"エラー: 応答テキストが見つかりませんでした。詳細: {result}"
                    else:
                        reply = f"エラー: 応答に choices が見つかりませんでした。詳細: {result}"

                    st.markdown(reply)

            # アシスタントの応答をセッションステートに保存
            st.session_state.messages.append({"role": "assistant", "content": reply})

        except requests.exceptions.RequestException as e:
            error_message = f"APIリクエストエラーが発生しました: {e}"
            st.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})
        except Exception as e:
            error_message = f"予期せぬエラーが発生しました: {e}"
            st.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})
