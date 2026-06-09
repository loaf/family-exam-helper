import base64
import json
import zipfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_ZIP = STATIC_DIR / "import-template-example.zip"


# 1x1 PNGs for sample assets
PNG_RED = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGP4zwAAAgEBAMW6d9kAAAAASUVORK5CYII="
)
PNG_BLUE = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def build_template_payload():
    return {
        "format": "family-exam-helper-template",
        "version": 1,
        "subjects": ["数学", "物理"],
        "questions": [
            {
                "subject": "数学",
                "tag": "几何,组合题",
                "type": "composite",
                "difficulty": 2,
                "content": '<p>阅读下列材料，完成小题：</p><p><img src="assets/figure-1.png" alt="示意图"></p>',
                "explanation": "<p>整组解析内容。</p>",
                "children": [
                    {
                        "type": "single_choice",
                        "difficulty": 2,
                        "score": 3,
                        "content": '<p>根据图形判断，下列说法正确的是：</p>',
                        "options": [
                            {"label": "A", "content": "<p>选项 A</p>"},
                            {"label": "B", "content": "<p>选项 B</p>"},
                            {"label": "C", "content": "<p>选项 C</p>"},
                            {"label": "D", "content": "<p>选项 D</p>"},
                        ],
                        "answer": "A",
                        "explanation": '<p>小题解析中也可以带图：</p><p><img src="./assets/detail-1.png" alt="解析图"></p>',
                    },
                    {
                        "type": "fill_blank",
                        "difficulty": 2,
                        "score": 2,
                        "content": "<p>请填写图中角度名称：</p>",
                        "options": [],
                        "answer": "锐角|acute angle",
                        "explanation": "<p>支持多个可接受答案。</p>",
                    },
                ],
            },
            {
                "subject": "物理",
                "tag": "力学",
                "type": "single_choice",
                "difficulty": 1,
                "score": 2,
                "content": "<p>力的国际单位是？</p>",
                "options": [
                    {"label": "A", "content": "<p>牛顿</p>"},
                    {"label": "B", "content": "<p>焦耳</p>"},
                    {"label": "C", "content": "<p>瓦特</p>"},
                    {"label": "D", "content": "<p>帕斯卡</p>"},
                ],
                "answer": "A",
                "explanation": "<p>力的国际单位是牛顿。</p>",
            },
        ],
    }


def main():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_template_payload()
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("template.json", json.dumps(payload, ensure_ascii=False, indent=2))
        zf.writestr("assets/figure-1.png", PNG_RED)
        zf.writestr("assets/detail-1.png", PNG_BLUE)
    print(f"wrote {OUTPUT_ZIP}")


if __name__ == "__main__":
    main()
