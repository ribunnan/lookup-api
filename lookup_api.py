from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup
import json
import os
import re

app = Flask(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

def extract_kana_from_text(text):
    match = re.search(r"読み方：([ぁ-んー゛゜]{1,10})", text)
    if match:
        return match.group(1)
    return ""

def clean_meaning(raw):
    if "［" in raw:
        parts = raw.split("［", 1)
        if len(parts) == 2:
            raw = "［" + parts[1]
    return raw.strip()[:300]

def get_weblio_meaning_and_kana(word):
    url = f"https://www.weblio.jp/content/{word}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # 提取假名
        kana_text = ""
        for tag in soup.find_all(["div", "p", "li", "dt", "dd", "span", "th"]):
            text = tag.get_text(strip=True)
            kana = extract_kana_from_text(text)
            if kana:
                kana_text = kana
                break

        # 提取释义
        kiji_elem = soup.select_one(".kijiWrp .kiji")
        meaning = kiji_elem.get_text(strip=True) if kiji_elem else "未找到释义"
        meaning = clean_meaning(meaning)

        return {
            "word": word,
            "kana": kana_text,
            "meaning": meaning,
            "source": "Weblio日文词典"
        }

    except Exception:
        return {
            "word": word,
            "kana": "",
            "meaning": "获取失败",
            "source": "Weblio日文词典"
        }

@app.route("/api/lookup")
def lookup_word():
    word = request.args.get("word", "").strip()
    if not word:
        return Response(json.dumps({"error": "请输入要查询的单词"}, ensure_ascii=False), mimetype="application/json")

    result = get_weblio_meaning_and_kana(word)
    return Response(json.dumps(result, ensure_ascii=False), mimetype="application/json")

if __name__ == "__main__":
    print("✅ 查词 API 启动中...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
