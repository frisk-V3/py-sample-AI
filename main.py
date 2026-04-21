import json
import os
import random

AI_FILE = "AI.json"

# Markovデータを読み込む
def load_model():
    if os.path.exists(AI_FILE):
        with open(AI_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Markovデータを保存
def save_model(model):
    with open(AI_FILE, "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)

# Markov遷移を追加（学習）
def learn(model, text):
    tokens = list(text)
    for i in range(len(tokens) - 1):
        a = tokens[i]
        b = tokens[i + 1]
        model.setdefault(a, [])
        if b not in model[a]:
            model[a].append(b)
    # 最後は終端
    last = tokens[-1]
    model.setdefault(last, [])
    if None not in model[last]:
        model[last].append(None)

# Markovで文章生成
def generate(model, start=None, max_len=50):
    if not model:
        return "（まだ学習データがありません）"

    if start is None or start not in model:
        start = random.choice(list(model.keys()))

    result = [start]
    current = start

    for _ in range(max_len):
        next_tokens = model.get(current, [])
        if not next_tokens:
            break
        nxt = random.choice(next_tokens)
        if nxt is None:
            break
        result.append(nxt)
        current = nxt

    return "".join(result)

# メインループ
def chat():
    model = load_model()
    print("Markov AI チャット開始（exit で終了）")

    while True:
        user = input("あなた: ").strip()
        if user.lower() == "exit":
            break

        # 学習
        learn(model, user)

        # 返答生成
        reply = generate(model, start=user[0] if user else None)
        print("AI:", reply)

        # 保存
        save_model(model)

if __name__ == "__main__":
    chat()
