import sys
sys.stdout.reconfigure(encoding='utf-8')
import json

P = r"C:\Users\Viorel Proteasa\Documents\evaluare-nationala\date\shrinkage_mediana.json"
d = json.load(open(P, encoding='utf-8'))
YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

by_code = {}
names = {}
mu_tau = {}
for y in YEARS:
    yd = d[str(y)]
    mu_tau[y] = (yd['mu_hat'], yd['tau2'])
    for s in yd['scoli']:
        code = s['cod']
        names[code] = s['denumire']
        by_code.setdefault(code, {})[y] = s

balanced = {c: ys for c, ys in by_code.items() if all(y in ys for y in YEARS)}
print(f'scoli prezente in toti cei 6 ani (n>=15 candidati/an): {len(balanced)} din {len(by_code)} totale')

rows = []
for code, ys in balanced.items():
    ranks = [ys[y]['rang_shrink'] for y in YEARS]
    zs = [(ys[y]['mediana_shrink'] - mu_tau[y][0]) / (mu_tau[y][1] ** 0.5) for y in YEARS]
    delta_rank = ranks[0] - ranks[-1]  # pozitiv = urcare (rang mai mic la final)
    delta_z = zs[-1] - zs[0]
    # slope simplu (regresie liniara pe rang, x=0..5)
    n = len(YEARS)
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(ranks) / n
    cov = sum((x - mx) * (r - my) for x, r in zip(xs, ranks)) / n
    varx = sum((x - mx) ** 2 for x in xs) / n
    slope_rank = -cov / varx  # negam ca sa fie pozitiv = urcare (rang scade cu timpul)
    rows.append({
        'cod': code, 'denumire': names[code],
        'ranguri': ranks, 'z_scores': [round(z, 2) for z in zs],
        'delta_rank': delta_rank, 'delta_z': round(delta_z, 2),
        'slope_rank_pe_an': round(slope_rank, 2),
        'n_ultimul_an': ys[2025]['n'],
    })

rows.sort(key=lambda r: -r['delta_rank'])
print('\n=== TOP 5 URCĂ (rang 2020 -> rang 2025) ===')
for r in rows[:5]:
    print(f"  {r['denumire']:<45s} ranguri {r['ranguri']}  delta_rank={r['delta_rank']:+d}  delta_z={r['delta_z']:+.2f}  slope={r['slope_rank_pe_an']:+.2f}/an")

print('\n=== TOP 5 COBOARĂ (rang 2020 -> rang 2025) ===')
for r in rows[-5:][::-1]:
    print(f"  {r['denumire']:<45s} ranguri {r['ranguri']}  delta_rank={r['delta_rank']:+d}  delta_z={r['delta_z']:+.2f}  slope={r['slope_rank_pe_an']:+.2f}/an")

rows.sort(key=lambda r: -abs(r['slope_rank_pe_an']))
print('\n=== TOP 5 cea mai CONSISTENTĂ tendință (slope mare, indiferent de semn) ===')
for r in rows[:5]:
    print(f"  {r['denumire']:<45s} ranguri {r['ranguri']}  slope={r['slope_rank_pe_an']:+.2f}/an  delta_rank={r['delta_rank']:+d}")

op = r"C:\Users\Viorel Proteasa\Documents\evaluare-nationala\date\dinamica_ranguri.json"
with open(op, 'w', encoding='utf-8') as f:
    json.dump(sorted(rows, key=lambda r: -r['delta_rank']), f, ensure_ascii=False, indent=1)
print('\nsaved', op)
