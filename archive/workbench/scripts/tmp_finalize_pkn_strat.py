from pathlib import Path
import json
from datetime import datetime

out = Path("data/raw/reports/PKN")

alt = out / "PKN_2023_STRAT_aktualizacja-2030-prezentacja-alt.pdf"
main = out / "PKN_2023_STRAT_aktualizacja-2030-prezentacja.pdf"
if alt.exists() and main.exists() and alt.stat().st_size == main.stat().st_size:
    alt.unlink()
    print("removed duplicate alt presentation")

fail = out / "PKN_2020_STRAT_transformacja-energetyczna.pdf"
if fail.exists() and fail.stat().st_size < 1000:
    fail.unlink()
    print("removed failed partial")

h2 = """# Strategia wodorowa Grupy Kapitałowej ORLEN (ESPI 6/2022)

- Data: 2022-02-02
- Zrodlo: raport biezacy nr 6/2022 PKN ORLEN S.A.
- URL: https://www.orlen.pl/pl/relacje-inwestorskie/raporty-i-publikacje/raporty-biezace/2022/01/Raport-biezacy-nr-6-2022
- Rola: doszczegolowienie Strategii 2030 w obszarze wodoru

## Cztery obszary do 2030
1. Mobilnosc — lider w Europie Srodkowej, stacje tankowania H2, B2B (komunikacja publiczna) -> B2C, e-fuels
2. Rafineria i petrochemia — dekarbonizacja produkcji wodoru (CCUS), elektroliza OZE, waste-to-hydrogen
3. B+R i regulacje — partnerstwa, ekosystem wodorowy
4. Przemysl i energetyka — dostawca/odbiorca H2 w European Hydrogen Backbone

## Cele / CAPEX
- CAPEX do 2030: ok. 7,4 mld PLN (czesciowo w filarze Inwestowanie w przyszlosc Strategii 2030)
- >100 stacji tankowania H2 w Europie Srodkowej
- Nowe moce wytworcze zero/niskoemisyjnego H2 ok. 540 MW
- Redukcja emisji z produkcji H2: unikanie ok. 1,6 mln t CO2/rok; ok. 50% wolumenu H2 nisko/zeroemisyjne w 2030

## Kod QUAL
STRAT / H5 (transformacja) / opcjonalnie framing zielonej narracji
"""
(out / "PKN_2022_STRAT_strategia-wodorowa-ESPI-6-2022.md").write_text(h2, encoding="utf-8")
print("wrote hydrogen strategy md")

strat = sorted(p for p in out.iterdir() if "STRAT" in p.name)
print("STRAT files:")
total = 0
for p in strat:
    mb = p.stat().st_size / 1e6
    total += p.stat().st_size
    print(f"  {p.name:55} {mb:6.2f} MB")
print(f"STRAT total: {total/1e6:.1f} MB, n={len(strat)}")

mf = out / "manifest_strategy.json"
if mf.exists():
    data = json.loads(mf.read_text(encoding="utf-8"))
    data["files"] = [
        f
        for f in data.get("files", [])
        if "transformacja" not in f.get("file", "") and "alt" not in f.get("file", "")
    ]
    data["files"].append(
        {
            "file": "PKN_2022_STRAT_strategia-wodorowa-ESPI-6-2022.md",
            "status": "ok",
            "note": "tekst z ESPI 6/2022 (brak osobnej prezentacji PDF na IR)",
        }
    )
    data["ok"] = len([f for f in data["files"] if f.get("status") in ("ok", "exists")])
    data["total"] = len(data["files"])
    data["failed"] = []
    data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    mf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("manifest_strategy updated")
