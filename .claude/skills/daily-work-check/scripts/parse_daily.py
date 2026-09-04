#!/usr/bin/env python3
"""
daily/*.docx (하루치 업무 메모, 월별 누적 파일)를 구조화된 JSON으로 파싱한다.
외부 라이브러리 없이 표준 라이브러리(zipfile + xml)만 사용한다.

사용법:
    python parse_daily.py <docx경로>

출력(JSON, stdout):
{
  "top_block": ["매주 ... 8월", ...],   # 첫 날짜 헤더 이전의 줄 (월간 반복업무 메모 등)
  "days": [
    {
      "date": "2026.8.1",
      "weekday": "토",
      "items": [
        {"text": "...", "done": true},
        ...
      ]
    },
    ...
  ]
}
"""
import sys
import re
import json
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DATE_RE = re.compile(r"^\s*(\d{4})\.(\d{1,2})\.(\d{1,2})\s*(?:\(([^)]+)\))?\s*$")


def load_paragraphs(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        xml_bytes = z.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    body = root.find(f"{W}body")
    paragraphs = []
    for p in body.findall(f"{W}p"):
        runs = p.findall(f"{W}r")
        texts = []
        run_done_flags = []
        for r in runs:
            t_parts = [t.text or "" for t in r.findall(f"{W}t")]
            text = "".join(t_parts)
            if text == "":
                continue
            rpr = r.find(f"{W}rPr")
            struck = False
            if rpr is not None:
                strike_el = rpr.find(f"{W}strike")
                if strike_el is not None:
                    val = strike_el.get(f"{W}val")
                    struck = val is None or val not in ("0", "false")
            texts.append(text)
            run_done_flags.append(struck)
        full_text = "".join(texts).strip()
        is_bullet = p.find(f".//{W}numPr") is not None
        done = bool(run_done_flags) and all(run_done_flags)
        paragraphs.append(
            {"text": full_text, "bullet": is_bullet, "done": done}
        )
    return paragraphs


def structure(paragraphs):
    top_block = []
    days = []
    current = None
    seen_first_date = False

    for para in paragraphs:
        text = para["text"]
        m = DATE_RE.match(text) if text else None
        if m:
            seen_first_date = True
            if current:
                days.append(current)
            current = {
                "date": f"{m.group(1)}.{int(m.group(2))}.{int(m.group(3))}",
                "weekday": m.group(4) or "",
                "items": [],
            }
            continue

        if not seen_first_date:
            if text:
                top_block.append(text)
            continue

        if text and para["bullet"] and current is not None:
            current["items"].append({"text": text, "done": para["done"]})

    if current:
        days.append(current)

    return {"top_block": top_block, "days": days}


def main():
    if len(sys.argv) != 2:
        print("usage: parse_daily.py <docx경로>", file=sys.stderr)
        sys.exit(1)
    paragraphs = load_paragraphs(sys.argv[1])
    result = structure(paragraphs)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
