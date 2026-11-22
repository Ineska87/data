import json
import zipfile
from pathlib import Path
from datetime import datetime

out = Path(r"data/raw/reports/PKN")
files_info = []
for p in sorted(out.iterdir()):
    if p.name == "manifest.json":
        continue
    info = {
        "file": p.name,
        "bytes": p.stat().st_size,
        "mb": round(p.stat().st_size / 1e6, 2),
    }
    if p.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(p) as z:
                names = z.namelist()
                info["zip_entries"] = len(names)
                info["zip_sample"] = names[:5]
        except Exception as e:
            info["zip_error"] = str(e)
    files_info.append(info)
    extra = f"  entries={info.get('zip_entries')}" if "zip_entries" in info else ""
    print(f"{p.name:45} {info['mb']:7.2f} MB{extra}")

manifest = {
    "ticker": "PKN",
    "company": "ORLEN S.A.",
    "source_index": "https://www.orlen.pl/pl/relacje-inwestorskie/raporty-i-publikacje/sprawozdania",
    "downloaded_at": datetime.now().isoformat(timespec="seconds"),
    "scope": "AR skonsolidowane 2020-2025 (ZIP z PDF) + dane liczbowe + raport zintegrowany 2021",
    "skipped": [
        "raport zintegrowany 2020 (~202MB)",
        "raport zintegrowany 2022 (~328MB)",
        "kwartały/prezentacje - nastepna runda",
    ],
    "files": files_info,
    "status": "complete_core_AR",
}
(out / "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("TOTAL files:", len(files_info))
print("TOTAL MB:", round(sum(f["bytes"] for f in files_info) / 1e6, 1))
