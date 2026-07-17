# Pasul 5 — testul structural temporal: sunt anii interschimbabili?
#
# FRIEDMAN pe fiecare entitate ORAȘ × FILIERĂ: blocuri = celulele liceu×filieră prezente
# în toți cei 9 ani, tratament = anul. Dacă anii ies diferiți, NU se face pooling
# temporal — regula proiectului: fără pooling fără test.
#
# MULȚIMEA DE REFERINȚĂ E ÎNTOTDEAUNA CELULA ORAȘ×FILIERĂ — orașul singur nu apare
# nicăieri. Sub prezumția că filierele sunt lumi sociale distincte, orice statistică a
# unui oraș agregată între filiere n-are referință. Aici au existat două încălcări,
# ambele eliminate:
#   - un Kruskal-Wallis pe an care grupa TOATE celulele unui oraș, amestecând filierele
#     (varianta corectă, în interiorul filierei, e în filiera_bac.py — testul de aici
#     era redundant și greșit);
#   - un Friedman care bloca pe liceu, cu mediana calculată între filiere.
#
# Statistica per celulă-an = mediana cenzurată (toți candidații promoției curente; cei
# fără rezultat intră fără notă, așezați jos — vezi statistici.py).
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
from collections import defaultdict, Counter
from statistici import rank_all, chi2_sf, mediana_cenzurata

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..', 'date', 'bac')
MIN_N = 8            # sub 8 candidați, mediana celulei-an nu e folosită (ca la EN)
YEARS = list(range(2017, 2026))
CITIES = ['CLUJ-NAPOCA', 'IAȘI', 'TIMIȘOARA']
FILIERE = ('teoretica', 'tehnologica', 'vocationala')

with open(os.path.join(BASE, 'candidati_bac.json'), encoding='utf-8') as f:
    data = json.load(f)
orase = data['orase']

acc = defaultdict(list)
fara = Counter()
for (an, siiir, forma, filiera, profil, promo, status,
     medie_pub, medie_calc) in data['candidati']:
    if promo != 1 or filiera not in FILIERE:
        continue
    if medie_calc is not None:
        acc[(siiir, filiera, an)].append(medie_calc)
    else:
        fara[(siiir, filiera, an)] += 1

matrix = defaultdict(dict)          # (siiir, filiera) -> {an: mediana cenzurată}
for k in set(acc) | set(fara):
    siiir, filiera, an = k
    if len(acc[k]) + fara[k] >= MIN_N:
        m = mediana_cenzurata(acc[k], fara[k])
        if m is not None:
            matrix[(siiir, filiera)][an] = m

out = {'min_candidati_per_celula_an': MIN_N,
       'statistica': 'mediana cenzurată a medie_calc, promoția curentă',
       'friedman_pe_orase': {}}
k = len(YEARS)
print(f'FRIEDMAN pe fiecare entitate oraș×filieră — blocuri = celulele liceu×filieră '
      f'prezente în toți cei {k} ani, tratament = anul')
for city in CITIES:
  for fil in FILIERE:
    blocks = [[ys[y] for y in YEARS] for (siiir, filiera), ys in matrix.items()
              if orase[siiir] == city and filiera == fil and all(y in ys for y in YEARS)]
    n = len(blocks)
    if n < 3:
        print(f'  {city} · {fil}: doar {n} celule balansate — test nefăcut')
        continue
    rank_sums = [0.0] * k
    tie_num = 0.0
    for b in blocks:
        rr = rank_all(b)
        for i, r in enumerate(rr):
            rank_sums[i] += r
        cnt = Counter(b)
        tie_num += sum(t ** 3 - t for t in cnt.values())
    Q = 12.0 / (n * k * (k + 1)) * sum(rs * rs for rs in rank_sums) - 3 * n * (k + 1)
    denom = 1 - tie_num / (n * k * (k * k - 1))
    if denom > 0:
        Q /= denom
    p = chi2_sf(Q, k - 1)
    W = Q / (n * (k - 1))
    mean_ranks = [round(rs / n, 2) for rs in rank_sums]
    out['friedman_pe_orase'][f'{city}|{fil}'] = {
        'n_celule_balansate': n, 'Q': round(Q, 3), 'df': k - 1,
        'p': float(f'{p:.4g}'), 'kendall_W': round(W, 4),
        'rang_mediu_pe_an': dict(zip(map(str, YEARS), mean_ranks))}
    semn = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    print(f'  {city:<12} {fil:<12} n={n:>3} Q={Q:6.2f} p={p:9.4g} {semn:<3} W={W:.3f}  '
          + '  '.join(f'{y}:{r:.1f}' for y, r in zip(YEARS, mean_ranks)))

op = os.path.join(BASE, 'teste_bac.json')
with open(op, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f'\nsalvat: {op}')
