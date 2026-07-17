# Pasul „verificarea distribuțiilor" (cerut de user, 2026-07-16): pe fiecare
# celulă LICEU × FILIERĂ × AN (promoția curentă, cu medie calculată) măsoară forma
# distribuției mediilor, ca să decidem empiric mediană vs medie. Mulțimea de
# referință e celula liceu×filieră, nu liceul: sub prezumția că filierele sunt lumi
# sociale distincte, o distribuție a unui liceu amestecată între filiere n-are
# referință (o versiune anterioară exact asta făcea).
#   - asimetrie g1 + testul D'Agostino de asimetrie (z, p) — implementare manuală,
#     scipy nu e instalat;
#   - boltire (exces g2);
#   - gap medie-mediană (în puncte și ca percentilă) și corelația lui cu nivelul
#     școlii (la EN: r=-0,64 → media penaliza sistematic școlile bune);
#   - efect de plafon (pondere medii ≥9,50) și de prag (pondere în [5,90, 6,10]).
# Scrie date/bac/distributii_bac.json + rezumat la stdout.
import sys, os, json, math
sys.stdout.reconfigure(encoding='utf-8')
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..', 'date', 'bac')
N_MIN = 15   # sub atâtea medii pe școală-an, forma distribuției nu e estimabilă

with open(os.path.join(BASE, 'candidati_bac.json'), encoding='utf-8') as f:
    data = json.load(f)
orase = data['orase']
den = data['denumiri']

# Lucrăm pe medie_calc (media oficială recalculată, definită pentru toți cei prezenți
# la toate probele), NU pe medie_pub — aceea există doar pentru cine a luat ≥5 la
# fiecare probă, deci ar da distribuția supraviețuitorilor. Vezi STARE.md.
FILIERE = ('teoretica', 'tehnologica', 'vocationala')
grupe = defaultdict(list)   # (siiir, filiera, an) -> [medii], doar promoția curentă
for (an, siiir, forma, filiera, profil, promo, status,
     medie_pub, medie_calc) in data['candidati']:
    if promo == 1 and medie_calc is not None and filiera in FILIERE:
        grupe[(siiir, filiera, an)].append(medie_calc)

def momente(x):
    n = len(x)
    m = sum(x) / n
    m2 = sum((v - m) ** 2 for v in x) / n
    m3 = sum((v - m) ** 3 for v in x) / n
    m4 = sum((v - m) ** 4 for v in x) / n
    if m2 == 0:
        return m, 0.0, 0.0
    g1 = m3 / m2 ** 1.5
    g2 = m4 / m2 ** 2 - 3.0
    return m, g1, g2

def mediana(x):
    s = sorted(x)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2

def norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))

def dagostino_skew_z(g1, n):
    """Testul D'Agostino pentru asimetrie (Y -> z), valabil pt n>=8."""
    if n < 8:
        return None
    Y = g1 * math.sqrt((n + 1) * (n + 3) / (6.0 * (n - 2)))
    beta2 = 3.0 * (n * n + 27 * n - 70) * (n + 1) * (n + 3) / ((n - 2) * (n + 5) * (n + 7) * (n + 9))
    W2 = -1 + math.sqrt(2 * (beta2 - 1))
    delta = 1 / math.sqrt(0.5 * math.log(W2))
    alpha = math.sqrt(2.0 / (W2 - 1))
    if Y == 0:
        return 0.0
    z = delta * math.log(Y / alpha + math.sqrt((Y / alpha) ** 2 + 1))
    return z

rez = []
for (siiir, filiera, an), medii in sorted(grupe.items()):
    n = len(medii)
    if n < N_MIN:
        continue
    m, g1, g2 = momente(medii)
    med = mediana(medii)
    z = dagostino_skew_z(g1, n)
    p = 2 * (1 - norm_cdf(abs(z))) if z is not None else None
    rez.append({
        'siiir': siiir, 'filiera': filiera, 'an': an, 'oras': orase[siiir], 'denumire': den[siiir],
        'n': n, 'medie': round(m, 3), 'mediana': round(med, 3),
        'gap': round(m - med, 3), 'skew_g1': round(g1, 3), 'kurt_g2': round(g2, 3),
        'z_skew': round(z, 3) if z is not None else None,
        'p_skew': round(p, 5) if p is not None else None,
        'pond_plafon_950': round(sum(1 for v in medii if v >= 9.5) / n, 3),
        'pond_prag_6': round(sum(1 for v in medii if 5.9 <= v <= 6.1) / n, 3),
    })

def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)

def cuartile(v):
    s = sorted(v)
    n = len(s)
    def q(f):
        i = f * (n - 1)
        lo, hi = int(i), min(int(i) + 1, n - 1)
        return s[lo] + (i - lo) * (s[hi] - s[lo])
    return q(0.25), q(0.5), q(0.75)

print(f'celule liceu×filieră-an cu n>={N_MIN}: {len(rez)} '
      f'(din {len(grupe)} cu ≥1 medie, promoția curentă)')
skews = [r['skew_g1'] for r in rez]
q1, q2, q3 = cuartile(skews)
print(f'asimetrie g1: Q1={q1:.2f}  mediană={q2:.2f}  Q3={q3:.2f}')
neg = sum(1 for s in skews if s < 0)
print(f'  negativă (coadă stânga): {neg}/{len(skews)} = {neg/len(skews):.0%}')
sig = sum(1 for r in rez if r['p_skew'] is not None and r['p_skew'] < 0.05)
print(f'  semnificativ asimetrice (D\'Agostino, p<0,05): {sig}/{len(rez)} = {sig/len(rez):.0%}')
gaps = [r['gap'] for r in rez]
g_q1, g_q2, g_q3 = cuartile(gaps)
print(f'gap medie−mediană: Q1={g_q1:.3f}  mediană={g_q2:.3f}  Q3={g_q3:.3f}')
r_gap = pearson([r['mediana'] for r in rez], gaps)
print(f'corelație gap × mediană școlii (EN VIII: r=−0,64): r={r_gap:.2f}')
r_skew = pearson([r['mediana'] for r in rez], skews)
print(f'corelație skew × mediană școlii: r={r_skew:.2f}')
plafon = sum(1 for r in rez if r['pond_plafon_950'] >= 0.10)
print(f'școală-an cu ≥10% medii ≥9,50 (plafon): {plafon}/{len(rez)}')

out_path = os.path.join(BASE, 'distributii_bac.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({'n_min': N_MIN, 'r_gap_mediana': round(r_gap, 3),
               'r_skew_mediana': round(r_skew, 3), 'scoala_an': rez},
              f, ensure_ascii=False, indent=1)
print(f'salvat: {out_path}')
