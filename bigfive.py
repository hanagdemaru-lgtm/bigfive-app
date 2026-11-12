import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from supabase import create_client, Client

# --- Supabase 接続設定 ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception:
    supabase = None

# ファイルパス（相対パス）
file_path = "bigfive_shitumon.txt"
kaisetsu_path = "kaisetsu.txt"

# --- Big5 因子マッピング (29問用) ---
BIG5_FACTORS = {
    "外向性": [1, 2, 3, 4, 5],
    "勤勉性": [6, 7, 8, 9, 10, 11, 12],
    "神経質傾向": [13, 14, 15, 16, 17],
    "開放性": [18, 19, 20, 21, 22, 23],
    "調和性": [24, 25, 26, 27, 28, 29],
}

# --- 逆転項目の指定 (1から始まる設問番号) ---
REVERSE_ITEM = [1, 6, 7, 8, 9, 11, 20, 24, 25, 28]

# フォールバック用のデフォルト29問
DEFAULT_SHITSUMON = [
    "無口な", "社交的", "話し好き", "外交的", "陽気な",
    "いい加減な", "ルーズな", "成り行き任せな", "怠惰な", "計画性のある",
    "軽率な", "几帳面な", "不安になりやすい", "心配性", "弱気になる",
    "緊張しやすい", "憂鬱な", "多才の", "進歩的", "独裁的な",
    "頭の回転がはやい", "興味のひろい", "好奇心が強い", "短期", "怒りっぽい",
    "温和な", "寛大な", "自己中心的", "親切な"
]


def load_shitsumon(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            if len(lines) >= 29:
                return lines[:29]
    return DEFAULT_SHITSUMON


def load_kaisetsu(file_path):
    kaisetsu_dict = {}
    if not os.path.exists(file_path):
        return kaisetsu_dict

    current_section = None
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            if text.startswith("[") and text.endswith("]"):
                current_section = text[1:-1]
                kaisetsu_dict[current_section] = ""
            elif current_section:
                kaisetsu_dict[current_section] += text + "\n"
    return kaisetsu_dict


def calculate_score(answers):
    processed = {}
    # 逆転項目の処理 (7件法: 8 - 値)
    for i in range(1, 30):
        val = answers[i]
        processed[i] = (8 - val) if i in REVERSE_ITEM else val

    factor_scores = {}
    for factor, q_list in BIG5_FACTORS.items():
        vals = [processed[q] for q in q_list]
        factor_scores[factor] = sum(vals) / len(vals)
        
    return factor_scores


def save_to_supabase(answers, scores):
    """29問の回答と各因子スコアをSupabaseに保存します"""
    if supabase is None:
        return False

    data = {}
    # q1 〜 q29 を動的に格納
    for i in range(1, 30):
        data[f"q{i}"] = answers[i]

    # 各因子スコアを格納
    data.update({
        "factor_e": scores["外向性"],
        "factor_c": scores["勤勉性"],
        "factor_n": scores["神経質傾向"],
        "factor_o": scores["開放性"],
        "factor_a": scores["調和性"],
    })

    try:
        supabase.table("results").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"DB保存エラー: {e}")
        return False


def plot_radar_chart(scores):
    categories = list(scores.keys())
    values = list(scores.values())

    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            name="診断スコア",
            line_color="#3366CC",
            fillcolor="rgba(51, 102, 204, 0.3)",
        )
    )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[1, 7], dtick=1)),
        showlegend=False,
        title=dict(
            text="<b>【 Big5 性格診断結果 】</b>",
            x=0.5,
            xanchor="center",
            font=dict(size=18, color="white"),
        ),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def main():
    st.title("Big5 本格性格診断（29項目）")
    st.write("以下の29個の項目について、あなた自身にどれくらい当てはまるかをそれぞれスライダーでお答えください。")

    shitsumon_list = load_shitsumon(file_path)
    kaisetsu_data = load_kaisetsu(kaisetsu_path)

    if "Big5とは" in kaisetsu_data:
        with st.expander("そもそも「Big5」とは？（解説を開く）"):
            st.write(kaisetsu_data["Big5とは"])

    with st.expander("選択肢の目安（1〜7）を見る"):
        st.write("""
        * **1**: 全く当てはまらない
        * **2**: 当てはまらない
        * **3**: どちらかといえば当てはまらない
        * **4**: どちらでもない
        * **5**: どちらかといえば当てはまる
        * **6**: 当てはまる
        * **7**: 非常によく当てはまる
        """)

    answers = {}

    st.write("---")
    st.subheader("質問項目")

    for i in range(1, 30):
        answers[i] = st.slider(
            label=f"Q{i}. {shitsumon_list[i-1]}",
            min_value=1,
            max_value=7,
            value=4,
            key=f"q_{i}",
        )

    st.write("---")

    if st.button("診断結果を表示する", type="primary", use_container_width=True):
        scores = calculate_score(answers)

        # データベースに保存
        saved = save_to_supabase(answers, scores)
        if saved:
            st.success("診断が完了し、回答データがSupabaseに保存されました。")
        else:
            st.warning("診断が完了しました（DB保存はスキップまたは失敗しました）。")

        st.subheader("【 5因子スコア 】")

        cols = st.columns(5)
        for idx, (factor, score) in enumerate(scores.items()):
            cols[idx].metric(label=factor, value=f"{score:.2f}点")

        st.write("---")
        fig = plot_radar_chart(scores)
        st.plotly_chart(fig, use_container_width=True)

        st.write("---")
        st.subheader("各因子の解説")

        for factor, score in scores.items():
            with st.expander(f"🔹 {factor} の解説"):
                if factor in kaisetsu_data:
                    st.write(kaisetsu_data[factor])
                else:
                    st.write("※ この因子の解説テキストが見つかりません。")

        st.write("---")

        if "心理学コラム" in kaisetsu_data:
            with st.expander("心理学コラム：なぜ Big5 はクオリティの高い性格診断と呼ばれるのか？"):
                st.write(kaisetsu_data["心理学コラム"])

        if "参考文献" in kaisetsu_data:
            with st.expander("参考文献・学術的根拠"):
                st.write(kaisetsu_data["参考文献"])


if __name__ == "__main__":
    main()
