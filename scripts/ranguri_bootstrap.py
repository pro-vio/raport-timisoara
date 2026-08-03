# Intervalul de rang al fiecărei școli, ca să spună clasamentul aceeași poveste ca tabul
# cu mediane: nu „locul 6", ci „locul 4-12".
#
# La fiecare replică se reeșantionează TOATE școlile deodată, se recalculează medianele și
# se reface ordinea. Rangul e o mărime a întregii mulțimi, nu a școlii — de aceea nu se
# poate obține din intervalul medianei fiecăreia luat separat.
#
# Rangurile se calculează pe mediana brută, nu pe cea ajustată: verificat că ajustarea mută
# rangul cu cel mult 2 locuri, la 2-7 școli din ~30 (`shrinkage_mediana.json`, rang_naiv vs
# rang_shrink). Nested bootstrap pentru shrinkage la fiecare replică ar cere o eroare
# standard estimată în interiorul replicii, cu un câștig sub rezoluția rezultatului.
#
# Neprezentații intră în mediană, așezați jos, ca peste tot în lanț.
import io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from statistici import cu_neprezentati

DATE = os.path.join(HERE, '..', 'date')
YEARS = [str(y) for y in range(2020, 2026)]
ORAS = 'TIMIȘOARA'
B = 2000
OUT = os.path.join(DATE, 'ranguri_bootstrap.json')

rng = np.random.default_rng(20260803)
NOTE = json.load(io.open(os.path.join(DATE, 'note_en.json'), encoding='utf-8'))
shr = json.load(io.open(os.path.join(DATE, 'shrinkage_mediana.json'), encoding='utf-8'))
reg, den = NOTE['orase'], NOTE['denumiri']


def ranguri(mat):
    """Rang 1 = mediana cea mai mare. Ex-aequo primesc rangul mediu."""
    ordine = np.argsort(-mat, axis=1, kind='stable')
    b, k = mat.shape
    r = np.empty((b, k), dtype=float)
    np.put_along_axis(r, ordine, np.tile(np.arange(1, k + 1, dtype=float), (b, 1)), axis=1)
    # medierea ex-aequo-urilor, pe rânduri
    for i in range(b):
        v = mat[i]
        for val in np.unique(v):
            m = v == val
            if m.sum() > 1:
                r[i, m] = r[i, m].mean()
    return r


rez = {}
for an in YEARS:
    # aceleași școli ca în clasamentul publicat
    coduri = [s['cod'] for s in sorted(shr[an]['scoli'], key=lambda s: s['rang_shrink'])]
    scoli = NOTE['ani'][an]['scoli']
    meds = np.empty((B, len(coduri)))
    for idx, cod in enumerate(coduri):
        r = scoli[cod]
        toate = np.asarray(cu_neprezentati(r['note'], r['neprezentati']), dtype=float)
        n = len(toate)
        meds[:, idx] = np.median(toate[rng.integers(0, n, size=(B, n))], axis=1)
    R = ranguri(meds)
    lo = np.percentile(R, 2.5, axis=0)
    hi = np.percentile(R, 97.5, axis=0)
    rez[an] = {cod: {'denumire': den.get(cod, cod),
                     'rang_publicat': i + 1,
                     'rang_lo': float(round(lo[i], 1)),
                     'rang_hi': float(round(hi[i], 1)),
                     'latime': float(round(hi[i] - lo[i] + 1, 1))}
               for i, cod in enumerate(coduri)}
    lat = sorted(v['latime'] for v in rez[an].values())
    print(f'{an}: {len(coduri)} școli · lățimea intervalului de rang: '
          f'mediană {lat[len(lat) // 2]:.0f} locuri, maxim {lat[-1]:.0f}')

# săgețile din tabelul de clasament: câte schimbări de la un an la altul se susțin?
sageti = {}
for a, b_ in zip(YEARS, YEARS[1:]):
    comune = set(rez[a]) & set(rez[b_])
    total = sustinute = 0
    for cod in comune:
        x, y = rez[a][cod], rez[b_][cod]
        if x['rang_publicat'] == y['rang_publicat']:
            continue
        total += 1
        if x['rang_lo'] > y['rang_hi'] or y['rang_lo'] > x['rang_hi']:
            sustinute += 1
    sageti[f'{a}->{b_}'] = {'sageti_afisate': total, 'sustinute': sustinute}

json.dump({'oras': ORAS, 'B': B, 'ani': rez, 'sageti': sageti},
          io.open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False)

print()
print('Săgețile din tabelul de clasament')
print(f"{'trecere':>12}{'afișate':>9}{'susținute':>11}")
for k, v in sageti.items():
    print(f"{k:>12}{v['sageti_afisate']:>9}{v['sustinute']:>11}")
t = sum(v['sageti_afisate'] for v in sageti.values())
s = sum(v['sustinute'] for v in sageti.values())
print(f"{'TOTAL':>12}{t:>9}{s:>11}   ({100 * s / t:.0f}%)")
print()
print('salvat:', os.path.normpath(OUT))
