# Devine clasamentul determinat dacă îl restrângem la școli tot mai mari?
#
# Întrebarea userului, 3 august 2026: dacă scoatem școlile mici, ies mișcările de la un an
# la altul din intervalele de incertitudine? Răspunsul e nu, și motivul contează: lățimea
# intervalului scade în locuri, dar numai fiindcă sunt mai puține locuri. Raportată la câmp
# rămâne aceeași, iar mișcările susținute rămân câteva procente, fără tendință.
#
# Nedeterminarea nu vine de la școlile mici. Vine din faptul că medianele stau aproape una
# de alta față de cât variază o mediană calculată pe câteva zeci de candidați.
import io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(P, 'scripts'))
from statistici import cu_neprezentati

DATE = os.path.join(P, 'date')
YEARS = [str(y) for y in range(2020, 2026)]
B = 2000
PRAGURI = [18, 25, 30, 40, 50, 70]

rng = np.random.default_rng(20260803)
NOTE = json.load(io.open(os.path.join(DATE, 'note_en.json'), encoding='utf-8'))
reg = NOTE['orase']


def ranguri(mat):
    ordine = np.argsort(-mat, axis=1, kind='stable')
    b, k = mat.shape
    r = np.empty((b, k), dtype=float)
    np.put_along_axis(r, ordine, np.tile(np.arange(1, k + 1, dtype=float), (b, 1)), axis=1)
    return r


OUT = os.path.join(DATE, 'restrictie_clasament.json')
rezultat = {}
print(f"{'prag':>5}{'școli/an':>10}{'lățime tipică':>15}{'ca % din câmp':>15}"
      f"{'mișcări':>9}{'ies din interval':>18}")
for prag in PRAGURI:
    per_an, lat_toate, k_toate = {}, [], []
    for an in YEARS:
        coduri = [c for c, r in NOTE['ani'][an]['scoli'].items()
                  if reg.get(c) == 'TIMIȘOARA' and len(r['note']) >= prag]
        if len(coduri) < 5:
            continue
        meds = np.empty((B, len(coduri)))
        for i, c in enumerate(coduri):
            r = NOTE['ani'][an]['scoli'][c]
            t = np.asarray(cu_neprezentati(r['note'], r['neprezentati']), dtype=float)
            meds[:, i] = np.median(t[rng.integers(0, len(t), size=(B, len(t)))], axis=1)
        R = ranguri(meds)
        lo = np.percentile(R, 2.5, axis=0)
        hi = np.percentile(R, 97.5, axis=0)
        pub = (-meds.mean(axis=0)).argsort().argsort() + 1
        per_an[an] = {c: {'lo': lo[i], 'hi': hi[i], 'pub': int(pub[i])}
                      for i, c in enumerate(coduri)}
        lat_toate += list(hi - lo + 1)
        k_toate.append(len(coduri))

    total = ies = 0
    for a, b_ in zip(YEARS, YEARS[1:]):
        if a not in per_an or b_ not in per_an:
            continue
        for c in set(per_an[a]) & set(per_an[b_]):
            x, y = per_an[a][c], per_an[b_][c]
            if x['pub'] == y['pub']:
                continue
            total += 1
            if x['lo'] > y['hi'] or y['lo'] > x['hi']:
                ies += 1
    lat = sorted(lat_toate)
    lt = lat[len(lat) // 2]
    kmed = sum(k_toate) / len(k_toate)
    rezultat[str(prag)] = {
        'scoli_pe_an': round(kmed, 1),
        'latime_tipica': round(lt, 1),
        'latime_pct_din_camp': round(100 * lt / kmed, 1),
        'miscari': total,
        'miscari_sustinute': ies,
        'miscari_sustinute_pct': round(100 * ies / total, 1) if total else None}
    print(f'{prag:>5}{kmed:>10.0f}{lt:>13.0f} locuri{100 * lt / kmed:>14.0f}%'
          f'{total:>9}{ies:>13} ({100 * ies / total if total else 0:.0f}%)')

json.dump({'praguri_testate': PRAGURI, 'B': B, 'oras': 'TIMIȘOARA', 'pe_prag': rezultat},
          io.open(OUT, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, indent=1)
print()
print('salvat:', os.path.normpath(OUT))
