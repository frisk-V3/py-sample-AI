import json
import os
import random
import re

AI_FILE = "AI.json"
LANG_FILES = {
    "python": "Code_py.json",
    "js": "Code_js.json",
    "csharp": "Code_cs.json",
    "haxe": "Code_hx.json"
}

# --- I/O helpers ---
def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_lang_files():
    for p in LANG_FILES.values():
        if not os.path.exists(p):
            save_json(p, {})

# --- Markov learn / generate (character-level) ---
def learn(model, text):
    if not text:
        return
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

def generate(model, start=None, max_len=120):
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

# --- language detection ---
def detect_language(text, filename_hint=None):
    # filename hint by "/file name.ext"
    if filename_hint:
        if filename_hint.endswith(".py"): return "python"
        if filename_hint.endswith(".js"): return "js"
        if filename_hint.endswith(".cs"): return "csharp"
        if filename_hint.endswith(".hx"): return "haxe"
    # prefix force: "/lang js ..." or "js:..."
    m = re.match(r"^/lang\s+(\w+)\s+", text)
    if m:
        return m.group(1).lower()
    m2 = re.match(r"^(\w+):", text)
    if m2 and m2.group(1).lower() in LANG_FILES:
        return m2.group(1).lower()
    # keyword heuristics
    if re.search(r"\bdef\b|\bprint\(|self\b|:\s*$|import\s+|from\s+|async\s+|await\b", text):
        return "python"
    if "console.log" in text or re.search(r"\bvar\b|\blet\b|\bconst\b|=>|require\(|module\.exports", text):
        return "js"
    if re.search(r"\busing\b|\bnamespace\b|\bConsole\.WriteLine\b|\bpublic\b|\bprivate\b|\bclass\b", text):
        return "csharp"
    if re.search(r"\btrace\(|haxe\b|\buntyped\b|\bpackage\b", text):
        return "haxe"
    return "unknown"

# --- merge models (shallow merge of dicts; lists concatenated then deduped) ---
def merge_models(*models):
    merged = {}
    for m in models:
        for k, v in m.items():
            merged.setdefault(k, [])
            # preserve order, avoid duplicates
            for item in v:
                if item not in merged[k]:
                    merged[k].append(item)
    return merged

# --- main chat loop ---
def chat():
    ensure_lang_files()
    ai = load_json(AI_FILE)
    lang_models = {lang: load_json(path) for lang, path in LANG_FILES.items()}

    print("Hybrid Language-aware Markov Chat（exitで終了）")
    print("強制言語: '/lang js <code>' または 'js:<code>'、ファイル名ヒント: '/file example.py'")

    while True:
        raw = input("あなた: ").rstrip()
        if not raw:
            continue
        if raw.lower() == "exit":
            break

        # check for /file hint (user can type: /file example.py <content>)
        filename_hint = None
        mfile = re.match(r"^/file\s+(\S+)\s*(.*)$", raw)
        if mfile:
            filename_hint = mfile.group(1)
            # replace raw with remainder (actual content)
            raw = mfile.group(2).strip()
            if not raw:
                print("ファイルヒントを受け取りましたが、内容が空です。続けて入力してください。")
                continue

        # detect language (may be 'unknown' or one of keys)
        lang = detect_language(raw, filename_hint=filename_hint)
        if lang not in LANG_FILES and lang != "unknown":
            # normalize common aliases
            if lang in ("js", "javascript"):
                lang = "js"
            elif lang in ("py", "python"):
                lang = "python"
            elif lang in ("cs", "csharp", "c#"):
                lang = "csharp"
            elif lang in ("hx", "haxe"):
                lang = "haxe"

        # decide learning targets
        learned_to = []
        if lang in LANG_FILES:
            # code-like: learn into that language model
            learn(lang_models[lang], raw)
            learned_to.append(lang)
            # also learn into AI.json if input contains natural language (mixed)
            if re.search(r"[ぁ-んァ-ン一-龥]|\\b(please|お願いします|ありがとう)\\b", raw, flags=re.I):
                learn(ai, raw)
                learned_to.append("ai")
        else:
            # unknown -> treat as conversation: learn into AI
            learn(ai, raw)
            learned_to.append("ai")
            # but if it contains code-like chars, also learn into all code models (soft)
            if re.search(r"[{}();=>

\[\]

<>]|console\.log|def\s+", raw):
                for l in lang_models:
                    learn(lang_models[l], raw)
                    learned_to.append(l)

        # prepare model for generation
        if lang in LANG_FILES:
            # merge AI + that language model
            model = merge_models(ai, lang_models[lang])
        else:
            # unknown: merge AI + all language models
            model = merge_models(ai, *lang_models.values())

        # choose start token: prefer first char of user if present in model
        start = raw[0] if raw and raw[0] in model else None
        reply = generate(model, start=start, max_len=160)

        print("AI:", reply)
        # save updated models
        save_json(AI_FILE, ai)
        for l, path in LANG_FILES.items():
            save_json(path, lang_models[l])

        # feedback
        print(f"(学習: {', '.join(learned_to)})")

if __name__ == "__main__":
    chat()
