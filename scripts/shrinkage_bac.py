# Pasul 6 — shrinkage empirical-Bayes + bootstrap, replicând metodologia EN VIII
# (shrinkage_mediana.py), dar în interiorul fiecărei celule ORAȘ × FILIERĂ × AN.
#
# DE CE ÎN INTERIORUL CELULEI: prezumția de bază a proiectului e că, în același oraș, cele
# trei filiere sunt trei lumi sociale diferite. Populația de referință a unui liceu — media
# spre care e tras și varianța față de care e judecat — trebuie deci să fie lumea lui, nu
# toate liceele la un loc. Un liceu tehnologic tras spre media tuturor liceelor ar fi
# penalizat pentru că e tehnologic, ceea ce nu e o informație despre el.
# Nici pooling temporal: Friedman l-a exclus (p < 1e-6 în toate orașele), deci și media, și
# varianța priorului se estimează separat pe fiecare an.
#
# Mecanica (ca la EN):
#   mediana liceului + SE prin bootstrap (B replici, resampling de candidați);
#   mu_hat = media medianelor din celulă; tau2 = var(mediane) − media(SE²), tăiat la 0
#      (metoda momentelor: varianța observată între licee minus cea explicabilă prin zgomot);
#   w = tau2 / (tau2 + SE²)  — cât de mult se crede liceului pe cuvânt;
#   theta = w·mediană + (1−w)·mu_hat;
#   var posterioară = 1/(1/tau2 + 1/SE²);  interval = theta ± 1,96·SE_post.
# Un liceu cu puțini candidați are SE mare, deci w mic: e tras spre media lumii lui și
# primește interval larg. Asta e tot rostul — un clasament naiv i-ar da un loc pe care
# datele nu-l susțin.
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
from collections import defaultdict, Counter
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from statistici import cu_neprezentati, mediana_cenzurata, SUB

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..', 'date', 'bac')
MIN_N = 10           # candidați minimi într-o celulă liceu×filieră×an.
                     # EN folosea 15; aici ar tăia o treime din tehnologice (12,9 → 9,3
                     # licee/an), iar shrinkage-ul penalizează oricum celulele mici.
MIN_LICEE = 4        # sub atâtea licee, tau2 nu e estimabil onest — celula se raportează
                     # descriptiv, fără clasament
B = 2000
YEARS = list(range(2017, 2026))
CITIES = ['CLUJ-NAPOCA', 'IAȘI', 'TIMIȘOARA']
FILIERE = ['teoretica', 'tehnologica', 'vocationala']
rng = np.random.default_rng(20260717)

with open(os.path.join(BASE, 'candidati_bac.json'), encoding='utf-8') as f:
    data = json.load(f)
orase, den = data['orase'], data['denumiri']

# Celula = TOȚI candidații promoției curente. Cei cu notă intră cu ea; cei fără rezultat
# (absenți, eliminați) intră fără notă, așezați sub toți — vezi statistici.mediana_cenzurata.
cell = defaultdict(list)
fara = Counter()
for (an, siiir, forma, filiera, profil, promo, status,
     medie_pub, medie_calc) in data['candidati']:
    if promo != 1 or filiera not in FILIERE:
        continue
    k = (orase[siiir], filiera, an, siiir)
    if medie_calc is not None:
        cell[k].append(medie_calc)
    else:
        fara[k] += 1

# Un liceu poate avea clase din două filiere (Carmen Sylva are și teoretic, și vocațional).
# Sunt celule diferite, cu mediane diferite, și apar pe taburi diferite — deci le marcăm
# cu filiera, ca să nu pară eroare de dublare.
SUFIX = {'teoretica': 'teoretic', 'tehnologica': 'tehnologic', 'vocationala': 'vocațional'}
CHEI = set(cell) | set(fara)
def n_tot(k):
    return len(cell[k]) + fara[k]
fil_per_scoala = defaultdict(set)
for k in CHEI:
    c, f, a, siiir = k
    if n_tot(k) >= MIN_N:
        fil_per_scoala[(siiir, a)].add(f)

def eticheta(siiir, an, fil):
    nume = den[siiir].strip()
    return f'{nume} — {SUFIX[fil]}' if len(fil_per_scoala[(siiir, an)]) > 1 else nume

def boot_se_median(note, c):
    """SE al medianei prin bootstrap, reeșantionând TOȚI candidații — și pe cei fără
    rezultat, reprezentați prin santinela SUB. Valoarea santinelei nu contează: fiind sub
    orice notă, ocupă aceleași poziții ca orice altă valoare de dedesubt."""
    a = np.asarray(cu_neprezentati(note, c), dtype=float)
    idx = rng.integers(0, len(a), size=(B, len(a)))
    return float(np.median(a[idx], axis=1).std(ddof=1))

out = {}
stat_nedef = []
print(f'Prior estimat în interiorul celulei oraș×filieră×an. '
      f'Prag: ≥{MIN_N} candidați/liceu, ≥{MIN_LICEE} licee/celulă. B={B}\n')
print(f'{"oraș":<12} {"filieră":<12} {"an":>5} {"k":>3} {"mu_hat":>7} {"tau2":>7} '
      f'{"w median":>9} {"Δrang max":>9} {"dif. de medie":>13}')
for city in CITIES:
    for fil in FILIERE:
        for an in YEARS:
            scoli = []
            for k in CHEI:
                c, f, a, siiir = k
                if not (c == city and f == fil and a == an and n_tot(k) >= MIN_N):
                    continue
                m = mediana_cenzurata(cell[k], fara[k])
                if m is None:          # peste jumătate neprezentați — mediana nu e definită
                    stat_nedef.append((siiir, fil, an, n_tot(k), fara[k]))
                    continue
                scoli.append({'cod': siiir, 'denumire': eticheta(siiir, an, fil),
                              'n': n_tot(k), 'n_fara_rezultat': fara[k], 'mediana': m,
                              'se': boot_se_median(cell[k], fara[k])})
            k = len(scoli)
            if k < MIN_LICEE:
                continue
            ms = np.array([s['mediana'] for s in scoli])
            se2 = np.array([s['se'] ** 2 for s in scoli])
            mu_hat = float(ms.mean())
            tau2 = max(0.0, float(ms.var(ddof=1) - se2.mean()))
            for s in scoli:
                v2 = s['se'] ** 2
                w = 0.0 if tau2 <= 1e-9 else tau2 / (tau2 + v2)
                theta = w * s['mediana'] + (1 - w) * mu_hat
                pv = v2 if tau2 <= 1e-9 else 1.0 / (1.0 / tau2 + 1.0 / v2)
                sd = pv ** 0.5
                s.update(w_shrink=round(w, 3), mediana_shrink=round(theta, 3),
                         se_shrink=round(sd, 3), ci_low=round(theta - 1.96 * sd, 3),
                         ci_high=round(theta + 1.96 * sd, 3),
                         mediana=round(s['mediana'], 3), se=round(s['se'], 3))
            for i, s in enumerate(sorted(scoli, key=lambda s: -s['mediana'])):
                s['rang_naiv'] = i + 1
            for i, s in enumerate(sorted(scoli, key=lambda s: -s['mediana_shrink'])):
                s['rang_shrink'] = i + 1
            # câte licee se disting de media lumii lor (intervalul nu conține mu_hat)
            distincte = sum(1 for s in scoli if s['ci_high'] < mu_hat or s['ci_low'] > mu_hat)
            dmax = max(abs(s['rang_naiv'] - s['rang_shrink']) for s in scoli)
            wmed = float(np.median([s['w_shrink'] for s in scoli]))
            out[f'{city}|{fil}|{an}'] = {
                'k': k, 'mu_hat': round(mu_hat, 3), 'tau2': round(tau2, 4),
                'w_median': round(wmed, 3), 'delta_rang_max': dmax,
                'licee_distincte_de_medie': distincte,
                'scoli': sorted(scoli, key=lambda s: s['rang_shrink'])}
            print(f'{city:<12} {fil:<12} {an:>5} {k:>3} {mu_hat:>7.3f} {tau2:>7.4f} '
                  f'{wmed:>9.3f} {dmax:>9} {distincte:>6}/{k:<6}')

op = os.path.join(BASE, 'shrinkage_bac.json')
with open(op, 'w', encoding='utf-8') as f:
    json.dump({'min_candidati': MIN_N, 'min_licee': MIN_LICEE, 'B': B,
               'prior': 'estimat în interiorul celulei oraș×filieră×an', 'celule': out},
              f, ensure_ascii=False, indent=1)
print(f'\nsalvat: {op}')

print('\n=== TIMIȘOARA 2025, pe filiere (clasament după shrinkage) ===')
for fil in FILIERE:
    key = f'TIMIȘOARA|{fil}|2025'
    if key not in out:
        continue
    c = out[key]
    print(f'\n── {fil.upper()}  (k={c["k"]}, mu={c["mu_hat"]:.2f}, tau2={c["tau2"]:.4f}, '
          f'se disting de medie: {c["licee_distincte_de_medie"]}/{c["k"]})')
    for s in c['scoli']:
        print(f'  {s["rang_shrink"]:2d}. {s["denumire"][:46]:<46} n={s["n"]:4d} '
              f'brut={s["mediana"]:5.2f}(#{s["rang_naiv"]:2d}) → {s["mediana_shrink"]:5.2f} '
              f'[{s["ci_low"]:5.2f}, {s["ci_high"]:5.2f}]  w={s["w_shrink"]:.2f}')
