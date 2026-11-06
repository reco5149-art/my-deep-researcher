"""테스트용 합성 자료(사실 아님)를 만든다. 실제 자료는 build_corpus.py 로 모은다."""
import json
from pathlib import Path

DOCS = {
    "crossfit": ("CrossFit", ["greg_glassman", "crossfit_games", "reebok", "rhabdomyolysis", "paleolithic_diet", "michael_p_murphy", "hyrox"]),
    "greg_glassman": ("Greg Glassman", ["crossfit", "crossfit_games"]),
    "crossfit_games": ("CrossFit Games", ["crossfit", "2007_crossfit_games", "2011_crossfit_games", "rich_froning_jr", "tia_clair_toomey", "reebok"]),
    "2007_crossfit_games": ("2007 CrossFit Games", ["crossfit_games", "2011_crossfit_games"]),
    "2011_crossfit_games": ("2011 CrossFit Games", ["crossfit_games", "rich_froning_jr", "reebok"]),
    "rich_froning_jr": ("Rich Froning Jr.", ["crossfit_games", "2011_crossfit_games"]),
    "tia_clair_toomey": ("Tia-Clair Toomey", ["crossfit_games", "hyrox"]),
    "hyrox": ("Hyrox", ["crossfit", "tia_clair_toomey"]),
    "reebok": ("Reebok", ["crossfit", "crossfit_games"]),
    "rhabdomyolysis": ("Rhabdomyolysis", ["crossfit"]),
    "paleolithic_diet": ("Paleolithic diet", ["crossfit"]),
    "michael_p_murphy": ("Michael P. Murphy", ["crossfit"]),
}


def build(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, (doc_id, (title, links)) in enumerate(DOCS.items()):
        year = 2000 + i
        para = (f"{title} is a synthetic test document created in {year}. It is not a real source. "
                f"This paragraph mentions {title} and the year {year} so that tests can find clues. ")
        filler = " ".join(f"Section {k}: {title} notes for testing, year {year + k % 3}." for k in range(1, 40))
        text = f"{para}\n\n== Details ==\n{filler}\n\n" + (filler * (3 if doc_id == "crossfit" else 1))
        lines.append(json.dumps({"id": doc_id, "title": title, "url": f"https://example.org/{doc_id}",
                                 "source": "synthetic", "chars": len(text), "links": links, "text": text},
                                ensure_ascii=False))
    out = path / "docs.jsonl"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build(Path(__file__).parent / "fixture_corpus"))
