import csv
from datetime import datetime
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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

# 逆転項目
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
    """質問文をテキストから読み込みます"""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            if len(lines) >= 10:
                return lines[:10]
    return DEFAULT_SHITSUMON


def load_kaisetsu(file_path):
    """kaisetsu.txt を読み込んでセクションごとの辞書を作成します"""
    kaisetsu_dict = {}
    if not os.path.exists(file_path):
        return kaisetsu_dict

    current_section = None
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue

            # [見出し] タグをチェック
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


def plot_radar_chart(scores):
    """Plotlyを使ってレーダーチャートを描画します"""
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
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[1, 7],
                dtick=1,
            )
        ),
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
    st.title("🧩 Big5 簡易性格診断（10項目）")
    st.write(
        "以下の10個の質問について、今のあなたにどれくらい当てはまるかをスライダーでお答えください。"
    )

    # データの読み込み
    shitsumon_list = load_shitsumon(file_path)
    kaisetsu_data = load_kaisetsu(kaisetsu_path)

    # --- 【テスト前に表示】 Big5についての説明 ---
    if "Big5とは" in kaisetsu_data:
        with st.expander("💡 そもそも「Big5」とは？（解説を開く）"):
            st.write(kaisetsu_data["Big5とは"])

    # 選択肢の目安
    with st.expander("💡 選択肢の目安（1〜7）を見る"):
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
    st.subheader("📝 質問コーナー")

    # スライダー入力
    for i in range(1, 11):
        answers[i] = st.slider(
            label=f"Q{i}. {shitsumon_list[i-1]}",
            min_value=1,
            max_value=7,
            value=4,
            key=f"q_{i}",
        )

    st.write("---")

    # 診断ボタンを押した後の処理
    if st.button("📊 診断結果を表示する", type="primary", use_container_width=True):
        scores = calculate_score(answers)

        st.success("診断が完了しました。")
        st.subheader("【 5因子スコア 】")

        # スコア表示
        cols = st.columns(5)
        for idx, (factor, score) in enumerate(scores.items()):
            cols[idx].metric(label=factor, value=f"{score:.1f}点")

        # グラフ描画 (Plotly)
        st.write("---")
        fig = plot_radar_chart(scores)
        st.plotly_chart(fig, use_container_width=True)

        # --- 【テスト後に表示】 各因子の詳細解説 ---
        st.write("---")
        st.subheader("📖 各因子の解説")

        for factor, score in scores.items():
            with st.expander(f"🔹 {factor} (あなたのスコア: {score:.1f}点) の解説"):
                if factor in kaisetsu_data:
                    st.write(kaisetsu_data[factor])
                else:
                    st.write("※ この因子の解説テキストが見つかりません。")

        # --- 【テスト後に表示】 心理学コラム ＆ 参考文献 ---
        st.write("---")

        if "心理学コラム" in kaisetsu_data:
            with st.expander(
                "🔬 心理学コラム：なぜ Big5 は「本物の性格診断」と呼ばれるのか？"
            ):
                st.write(kaisetsu_data["心理学コラム"])

        if "参考文献" in kaisetsu_data:
            with st.expander("📚 参考文献・学術的根拠"):
                st.write(kaisetsu_data["参考文献"])


if __name__ == "__main__":
    main()
