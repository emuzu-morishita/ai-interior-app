import streamlit as st
from google import genai
from google.genai import types
import json

# タイトル
st.title("AI Interior Coordinator (Gemini版)")

# サイドバーにAPIキーの入力欄を設置（テスト用）
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# サイドバーに入力欄を作っておくか、直接コードに貼る用
# (今回は仮でサイドバーに入力欄を作る想定にします)
stability_key = st.sidebar.text_input("Stability AI API Key", type="password")

# --- ユーザー入力 ---
room_size = st.selectbox("間取り（広さ）", ["6畳", "8畳", "10畳", "12畳以上"])
budget = st.number_input("予算 (円)", min_value=5000, max_value=1000000, value=50000, step=5000)
taste = st.text_input("好みのテイスト（例：北欧モダン、インダストリアル）", "北欧モダン")

if st.button("コーディネートを生成する"):
    if not gemini_key:
        st.error("サイドバーにGeminiのAPIキーを入力してください。")
    else:
        # クライアントの初期化
        client = genai.Client(api_key=gemini_key)
        
        # AIへの指示（プロンプト）
        prompt = f"""
        あなたはプロのインテリアコーディネーターです。
        以下の条件に合わせた家具の提案を、必ず指定されたJSONフォーマットのみで出力してください。
        
        【条件】
        - 広さ: {room_size}
        - 予算: {budget}円
        - テイスト: {taste}
        
        【厳守事項】
        予算が5,000円など極端に低い場合は、大型家具ではなく、間接照明やクッションなどの小物で部屋の質感を上げる代替案を提案してください。
        """

        # GeminiにJSONの形（スキーマ）を教えて、強制的にその形で出力させる設定
        # (前回OpenAIで設定したものと同じ構造をGemini用に翻訳しています)
        response = client.models.generate_content(
            model='gemini-2.5-flash', # 高速・無料枠ありの優秀なモデル
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "item_name": types.Schema(type=types.Type.STRING, description="家具・小物の名前"),
                        "price": types.Schema(type=types.Type.INTEGER, description="概算金額"),
                        "reason": types.Schema(type=types.Type.STRING, description="選定した理由"),
                        "image_prompt": types.Schema(type=types.Type.STRING, description="DALL-E 3やStable Diffusion用の高精細な英語画像生成プロンプト")
                    },
                    required=["item_name", "price", "reason", "image_prompt"]
                )
            ),
        )

        # 結果を表示
        result_json = json.loads(response.text)
        st.success("AIからの提案（JSONデータ）の抽出に成功しました！")
        st.write(result_json)
        
        # 次のステップ用（ここに画像生成の処理を追加します）
        st.info(f"💡 このプロンプトを使って、次にStability AIで画像を生成します:\n`{result_json['image_prompt']}`")

        # --- ここから下に画像生成のコードを追加 ---
        st.subheader("🖼️ 理想の部屋のイメージ（AI生成）")
        
        if not stability_key:
            st.warning("サイドバーにStability AIのAPIキーを入力すると、画像が自動生成されます。")
        else:
            with st.spinner("理想の部屋のイメージ画像を生成中..."):
                import requests
                from PIL import Image
                import io

                # Stability AI SD3 APIの呼び出し
                url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
                headers = {
                    "authorization": f"Bearer {stability_key}",
                    "accept": "image/*"
                }
                data = {
                    "prompt": result_json['image_prompt'], # Geminiが作ったプロンプトをそのまま投入！
                    "output_format": "jpeg",
                    "aspect_ratio": "1:1" # 正方形
                }

                response = requests.post(url, headers=headers, files={"none": ''}, data=data)

                if response.status_code == 200:
                    # バイナリデータを画像に変換して表示
                    image = Image.open(io.BytesIO(response.content))
                    st.image(image, caption="AIが提案する理想のレイアウト", use_container_width=True)
                else:
                    st.error(f"画像生成に失敗しました: {response.json().get('errors', 'Unknown Error')}")