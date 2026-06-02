import streamlit as st
import json

# --- 画面の基本設定 ---
st.set_page_config(page_title="AIインテリアコーディネーター", layout="wide")
st.title("🛋️ AIインテリアコーディネーター (仮)")

# --- ダミーデータ（API通信の代わり） ---
# 以前設計したAIの出力プロンプトと同じ形のJSONデータです
dummy_response = """
{
  "advice": "お部屋の縦長な間取りを活かし、奥にベッド、手前にリビングスペースを配置することで、空間を広く見せることができます。白を基調としつつ、木目の家具を取り入れることで、ご希望の温かみのある北欧風の空間に仕上がります。",
  "total_estimated_price": 85000,
  "furniture_list": [
    {
      "item_name": "2人掛けファブリックソファ",
      "reason": "部屋の主役として、温かみのあるグレーを選択。壁際に配置します。",
      "estimated_price": 45000,
      "search_keyword": "2人掛け ソファ ファブリック 北欧"
    },
    {
      "item_name": "木製ローテーブル",
      "reason": "ソファの色味に合わせたオーク材のテーブルです。",
      "estimated_price": 15000,
      "search_keyword": "ローテーブル 木製 オーク 北欧"
    },
    {
      "item_name": "間接照明（フロアライト）",
      "reason": "部屋の角に配置し、夜はリラックスできる空間を演出します。",
      "estimated_price": 25000,
      "search_keyword": "フロアライト 間接照明 北欧 スタンド"
    }
  ],
  "image_prompt": "A photorealistic interior design of a room..."
}
"""

# --- ① 条件入力（サイドバー） ---
with st.sidebar:
    st.header("📋 お部屋の条件")
    floor_plan = st.text_input("部屋の間取り", placeholder="例: 8畳のワンルーム、縦長")
    atmosphere = st.text_input("希望の雰囲気", placeholder="例: 北欧風、白と木目が基調")
    budget = st.number_input("ご予算 (円)", min_value=0, value=100000, step=10000)
    
    submit_button = st.button("🌟 理想の部屋を提案してもらう")

# --- ② 提案表示（メインエリア） ---
if submit_button:
    # ここで本当はAPIを呼び出しますが、今回はダミーのJSONをPythonの辞書型に変換します
    data = json.loads(dummy_response)
    
    tab1, tab2 = st.tabs(["🛋️ レイアウト提案", "🛒 おすすめ家具"])
    
    # タブ1: レイアウト提案
    with tab1:
        st.subheader("💡 AIからの総合アドバイス")
        st.write(data["advice"])
        
        st.subheader("🖼️ 理想の部屋のイメージ")
        st.info("※API連携後、ここにDALL-E 3で生成した画像が表示されます")
        # st.image(image_url) # API連携後にコメントアウトを外す
        
    # タブ2: おすすめ家具と予算シミュレーション
    with tab2:
        st.subheader("💰 ご予算のシミュレーション")
        
        # 予算に対する使用割合を計算してプログレスバーを表示
        progress_ratio = min(data["total_estimated_price"] / budget, 1.0) if budget > 0 else 0.0
        st.progress(progress_ratio)
        st.write(f"概算合計: **{data['total_estimated_price']:,}円** / 予算: {budget:,}円")
        
        st.divider() # 区切り線
        
        st.subheader("🛍️ 提案された家具一覧")
        for idx, item in enumerate(data["furniture_list"], 1):
            st.markdown(f"**{idx}. {item['item_name']} (概算: ¥{item['estimated_price']:,})**")
            st.write(f"💡 理由: {item['reason']}")
            
            # 検索キーワードをURLエンコード（空白を+に変換）してYahooショッピングのリンクを作成
            search_url = f"https://shopping.yahoo.co.jp/search?p={item['search_keyword'].replace(' ', '+')}"
            st.link_button("👉 Yahoo!ショッピングで探す", search_url)
            st.write("---")
else:
    # ボタンが押される前の初期表示
    st.info("👈 左のサイドバーに条件を入力して、「理想の部屋を提案してもらう」ボタンを押してください。")

# --- サイドバーの一番下にプレゼン資料へのリンクボタンを追加 ---
st.sidebar.markdown("---")  # 区切り線
st.sidebar.write("### 📄 開発資料")

# 先ほどコピーしたGitHubのRaw URLをここに貼り付けます
raw_html_url = "https://emuzu-morishita.github.io/ai-interior-app/presentation.html"

# ボタンのように見えるリンク（HTML）を作成
st.sidebar.markdown(
    f'<a href="{raw_html_url}" target="_blank" style="text-decoration: none;">'
    '<button style="width: 100%; padding: 10px; background-color: #1e293b; color: #a3e635; '
    'border: 1px solid #334155; border-radius: 8px; cursor: pointer; font-weight: bold;">'
    '📊 プレゼン資料を見る'
    '</button></a>',
    unsafe_allow_html=True
)