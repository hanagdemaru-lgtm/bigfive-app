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
file_path = "shistumon.txt"
kaisetsu_path = "kaisetsu.txt"

factor_pair = {
    "外向性": (1, 6),
    "協調性": (2, 7),
    "勤勉性": (3, 8),
    "神経質傾向": (4, 9),
    "開放性": (5, 10),
}

REVERSE_ITEM = [2, 6, 8, 9, 10]

DEFAULT_SHITSUMON = [
    "1. 活気があり、外向的だと思う",
    "2. 他人に批判的で、同情心に欠けると思う",
    "3. しっかりしていて、自分に厳しいと思う",
    "4. 心配性で、不安になりやすいと思う",
    "5. 新しいことや複雑なことに興味があると思う",
    "6. おとなしく、静かだと思う",
    "7. 他人を思いやり、温かい心を持っていると思う",
    "8. だらしなく、不注意なところがあると思う",
    "9. 冷静で、気分が安定していると思う",
    "10. 独創的で、発想力が豊富だと思う",
]


def load_shitsumon(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            if len(lines) >= 10:
                return lines[:10]
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
    score = {}
    for factor, (q1, q2) in factor_pair.items():
        val1 = (8 - answers[q1]) if q1 in REVERSE_ITEM else answers[q1]
        val2 = (8 - answers[q2]) if q2 in REVERSE_ITEM else answers[q2]
        score[factor] = (val1 + val2) / 2
    return score


def save_to_supabase(answers, scores):
    """回答と計算スコアをSupabaseに保存します"""
    if supabase is None:
        return False

    data = {
        "q1": answers[1], "q2": answers[2], "q3": answers[3], "q4": answers[4], "q5": answers[5],
        "q6": answers[6], "q7": answers[7], "q8": answers[8], "q9": answers[9], "q10": answers[10],
        "factor_e": scores["外向性"],
        "factor_a": scores["協調性"],
        "factor_c": scores["勤勉性"],
        "factor_n": scores["神経質傾向"],
        "factor_o": scores["開放性"],
    }
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
    st.title("Big5 簡易性格診断（10項目）")
    st.write("以下の10個の質問について、今のあなたにどれくらい当てはまるかをスライダーでお答えください。")

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

    for i in range(1, 11):
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
            st.success("診断が完了し、回答データが保存されました。")
        else:
            st.success("診断が完了しました。")

        st.subheader("【 5因子スコア 】")

        cols = st.columns(5)
        for idx, (factor, score) in enumerate(scores.items()):
            cols[idx].metric(label=factor, value=f"{score:.1f}点")

        st.write("---")
        fig = plot_radar_chart(scores)
        st.plotly_chart(fig, use_container_width=True)

        st.write("---")
        st.subheader("📖 各因子の解説")

        for factor, score in scores.items():
            with st.expander(f"🔹 {factor} (あなたのスコア: {score:.1f}点) の解説"):
                if factor in kaisetsu_data:
                    st.write(kaisetsu_data[factor])
                else:
                    st.write("※ この因子の解説テキストが見つかりません。")

        st.write("---")

        if "心理学コラム" in kaisetsu_data:
            with st.expander("🔬 心理学コラム：なぜ Big5 は「本物の性格診断」と呼ばれるのか？"):
                st.write(kaisetsu_data["心理学コラム"])

        if "参考文献" in kaisetsu_data:
            with st.expander("参考文献・学術的根拠"):
                st.write(kaisetsu_data["参考文献"])

    # --- HAD用データ出力コーナー（画面最下部） ---
    st.write("---")
    with st.expander("🛠️ 管理者メニュー（HAD用データダウンロード）"):
        if supabase:
            if st.button("最新データを取得する"):
                response = supabase.table("results").select("*").execute()
                df = pd.DataFrame(response.data)

                if not df.empty:
                    csv_data = df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        label="HAD用CSVをダウンロード",
                        data=csv_data,
                        file_name="bigfive_had_data.csv",
                        mime="text/csv",
                    )
                    st.dataframe(df.head())
                else:
                    st.info("まだ保存されたデータがありません。")
        else:
            st.warning("DB接続設定が完了していません。Secretsを確認してください。")


if __name__ == "__main__":
    main()
