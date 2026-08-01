import json

data = {
    "VIP": {
        "source": "VIP",
        "translation": "VIP",
        "category": "abbreviation",
        "total_count": 0,
        "books": {},
        "book_count": 0,
        "locked": True,
        "status": "manual_locked",
        "aliases": [],
        "notes": ["manual override"],
        "confidence": 1.0,
        "created_by": "manual"
    },
    "CIA": {
        "source": "CIA",
        "translation": "中央情報局",
        "category": "organization",
        "total_count": 0,
        "books": {},
        "book_count": 0,
        "locked": True,
        "status": "manual_locked",
        "aliases": [],
        "notes": ["manual override"],
        "confidence": 1.0,
        "created_by": "manual"
    },
    "UNHRDO": {
        "source": "UNHRDO",
        "translation": "聯合國人權發展組織",
        "category": "organization",
        "total_count": 0,
        "books": {},
        "book_count": 0,
        "locked": True,
        "status": "manual_locked",
        "aliases": [],
        "notes": ["manual override with translation"],
        "confidence": 1.0,
        "created_by": "manual"
    }
}

with open("d:/Python/NTPE/glossary_override.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Written successfully")