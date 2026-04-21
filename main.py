import json
import os
import random

AI_FILE = "AI.json"
CODE_FILE = "Code.json"

# JSON読み込み
def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# JSON保存
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Markov学習
def learn(model, text):
    tokens = list(text)
    for i in range(len(tokens) - 1):
        a = tokens[i]
        b = tokens[i + 1]
        model.setdefault(a, [])
        if b not in model[a]:
            model[a].append(b)
    last = tokens[-1]
    model.setdefault(last, [])
    if None not in model[last]:
        model[last].append(None)

# Markov生成
def generate(model, start=None, max_len=80):
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

def chat():
    # 2つのJSONを読み込む
    ai = load_json(AI_FILE)
    code = load_json(CODE_FILE)

    # マージ（単純に辞書を合体）
    model = {**ai, **code}

    print("Hybrid Markov AI チャット開始（exit で終了）")

    while True:
        user = input("あなた: ").strip()
        if user.lower() == "exit":
            break

        # 学習（AI と Code 両方に学習させる）
        learn(ai, user)
        learn(code, user)

        # 返答生成
        reply = generate(model, start=user[0] if user else None)
        print("AI:", reply)

        # 保存
        save_json(AI_FILE, ai)
        save_json(CODE_FILE, code)

        # マージし直す（モデル更新）
        model = {**ai, **code}

if __name__ == "__main__":
    chat()
