import csv
from datetime import datetime
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.family"] = "MS Gothic"

file_path = r"C:\Python\bigfive\shistumon.txt"
kaisetsu_path = r"C:\Python\bigfive\kaisetsu.txt"

factor_pair = {
    "外向性": (1, 6),
    "協調性": (2, 7),
    "勤勉性": (3, 8),
    "神経質傾向": (4, 9),
    "開放性": (5, 10),
}

# 逆転項目
REVERSE_ITEM = [2, 6, 8, 9, 10]


def load_shitsumon(file_path):
    if not os.path.exists(file_path):
        print(f"エラー:ファイルが見つかりません: {file_path}")
        return None

    shitsumon = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if text:
                shitsumon.append(text)

    return shitsumon


def load_kaisetsu(file_path):
    """kaisetsu.txt を読み込んでセクションごとの辞書を作成する"""
    kaisetsu_dict = {}
    if not os.path.exists(file_path):
        print(f"警告: 解説ファイルが見つかりません: {file_path}")
        return kaisetsu_dict

    current_section = None
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue

            # [外向性] や [心理学コラム] などの見出しタグをチェック
            if text.startswith("[") and text.endswith("]"):
                current_section = text[1:-1]
                kaisetsu_dict[current_section] = ""
            elif current_section:
                kaisetsu_dict[current_section] += text + "\n"

    return kaisetsu_dict


def show_instructions():
    """開始時に入力方法や選択肢の意味を表示する関数"""
    print("=" * 50)
    print("    【 Big5 簡易性格診断（10項目） 】")
    print("=" * 50)
    print("以下の質問について、今のあなたにどれくらい当てはまるかを")
    print("【 1 〜 7 】の数字で答えてください。\n")
    print("  1: 全く当てはまらない")
    print("  2: 当てはまらない")
    print("  3: どちらかといえば当てはまらない")
    print("  4: どちらでもない")
    print("  5: どちらかといえば当てはまる")
    print("  6: 当てはまる")
    print("  7: 非常によく当てはまる")
    print("=" * 50)
    print()


def answer(q_num, q_text):
    print("-" * 30)
    print(f"[質問{q_num}]")
    print(q_text)

    while True:
        try:
            val = int(input("回答(1-7)>>>"))
            if 1 <= val <= 7:
                return val
            else:
                print("エラー:1〜7で入力してください")
        except ValueError:
            print("エラー:半角数字で入力してください")


def calculate_score(answers):
    score = {}
    for factor, (q1, q2) in factor_pair.items():
        val1 = (8 - answers[q1]) if q1 in REVERSE_ITEM else answers[q1]
        val2 = (8 - answers[q2]) if q2 in REVERSE_ITEM else answers[q2]
        score[factor] = (val1 + val2) / 2
    return score


def display_result(scores, kaisetsu_data):
    """診断結果と解説・コラムを表示する関数"""
    print("\n" + "=" * 50)
    print("      【 Big5 診断結果 】")
    print("=" * 50)

    for factor, score in scores.items():
        bar = "★" * int(round(score))
        print(f"{factor:6s} : {score:.1f} 点  {bar}")

    print("=" * 50)
    print("※ スコアは 1.0（低い）〜 7.0（高い）の範囲です。\n")

    # --- 各因子の解説表示 ---
    if kaisetsu_data:
        print("\n【 📖 各因子の詳細解説 】")
        for factor, score in scores.items():
            print(f"\n🔹 {factor} (あなたのスコア: {score:.1f}点)")
            if factor in kaisetsu_data:
                print(kaisetsu_data[factor].strip())
            else:
                print("  ※ この因子の解説はありません。")

        # --- 心理学コラムの表示 ---
        if "心理学コラム" in kaisetsu_data:
            print("\n" + "-" * 50)
            print("🔬 心理学コラム")
            print("-" * 50)
            print(kaisetsu_data["心理学コラム"].strip())

        # --- 参考文献の表示 ---
        if "参考文献" in kaisetsu_data:
            print("\n" + "-" * 50)
            print("📚 参考文献・学術的根拠")
            print("-" * 50)
            print(kaisetsu_data["参考文献"].strip())
            print("-" * 50)


def plot_radar_chart(scores):
    """ペンタゴン（レーダーチャート）を表示する関数"""
    df = pd.Series(scores)
    labels = list(df.index)
    values = list(df.values)

    # グラフを閉じるために先頭要素を末尾に追加
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    # 描画の準備
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    ax.set_theta_offset(np.pi / 2)  # 外向性を真上にする
    ax.set_theta_direction(-1)  # 時計回り
    ax.set_rlim(1, 7)  # 範囲は 1〜7

    plt.xticks(angles[:-1], labels, size=12)

    # データ描画
    ax.plot(angles, values, color="skyblue", linewidth=2, linestyle="solid")
    ax.fill(angles, values, color="skyblue", alpha=0.4)

    plt.title("【 Big5 性格診断レーダーチャート 】", size=15, color="navy", y=1.1)
    plt.show()


def save_to_csv(answers, scores, output_file=r"C:\Python\bigfive\results.csv"):
    """回答と計算結果をCSVファイルに追記保存する関数"""
    file_exists = os.path.exists(output_file)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ヘッダー列（日時, Q1〜Q10, 外向性〜開放性）
    headers = ["datetime"] + [f"Q{i}" for i in range(1, 11)] + list(scores.keys())

    # 書き込むデータ行
    row = [now] + [answers[i] for i in range(1, 11)] + list(scores.values())

    # UTF-8 (BOM付き) で保存してExcelの文字化けを防ぐ
    with open(output_file, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)  # 初回のみヘッダー書き込み
        writer.writerow(row)

    print(f"\n結果が保存されました: {output_file}\n")


def main():
    """プログラム全体を順番に動かすメイン処理"""
    # 1. 質問ファイル・解説ファイルの読み込み
    shitsumon = load_shitsumon(file_path)
    if not shitsumon or len(shitsumon) < 10:
        print("エラー: 質問が10項目揃っていません。ファイルを確認してください。")
        return

    kaisetsu_data = load_kaisetsu(kaisetsu_path)

    # 2. 案内の表示
    show_instructions()

    # 3. 10個の質問に順番に回答
    answers = {}
    for i in range(1, 11):
        answers[i] = answer(i, shitsumon[i - 1])

    # 4. スコア計算（逆転項目も自動処理）
    scores = calculate_score(answers)

    # 5. ターミナルに結果・解説表示
    display_result(scores, kaisetsu_data)

    # 6. CSVファイルへ自動保存
    save_to_csv(answers, scores)

    # 7. ペンタゴングラフ（レーダーチャート）表示
    plot_radar_chart(scores)


if __name__ == "__main__":
    main()