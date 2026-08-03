# Are pragul o bază empirică? Pragurile (8 la teste, 15 la grafice) au intrat în cod pe
# 14-15 iulie 2026 fără justificare scrisă. Aici se calculează ce ar putea s-o dea.
#
# Pentru fiecare celulă școală×an, cu orice număr de candidați, se estimează prin bootstrap
# intervalul de 95% al medianei, și se raportează două mărimi:
#
#   1. LĂȚIMEA intervalului, în puncte de notă — cât de precisă e estimarea.
#   2. ACOPERIREA: ce fracțiune din câmpul orașului din acel an acoperă intervalul, unde
#      câmpul e distanța dintre cea mai mică și cea mai mare mediană de școală. Asta e
#      mărimea care contează pentru un clasament: o școală al cărei interval acoperă
#      jumătate din câmp nu are rang, are o zonă.
import io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from statistici import cu_neprezentati, mediana_cu_neprezentati

DATE = os.path.join(HERE, '..', 'date')
YEARS = [str(y) for y in range(2020, 2026)]
B = 2000
N_MIN = 3
OUT = os.path.join(DATE, 'prag_incertitudine.json')

# Criteriile, declarate. Pragurile NU se citesc dintr-un cot al curbei — curba n-are cot,
# scade neted. Ele traduc în număr de candidați o alegere despre cât nedeterminare acceptăm:
#   * un test compară populații și suportă unități zgomotoase, care se mediază → jumătate
#   * un grafic numește o școală anume, iar acolo nedeterminarea e o afirmație → o treime
CRITERII = {'prag_teste': 0.50, 'prag_grafice': 1 / 3}
FEREASTRA = 3          # fereastra glisantă ±3 candidați, ca să nu decidă zgomotul unui n
# Baza pe care se măsoară „câmpul" orașului. E declarată fix, ca pragul să nu depindă de
# prag; stabilitatea se verifică la final, recalculând cu pragul obținut.
BAZA_CAMP = 15

rng = np.random.default_rng(20260803)
NOTE = json.load(io.open(os.path.join(DATE, 'note_en.json'), encoding='utf-8'))
reg = NOTE['orase']

celule = []
for an in YEARS:
    scoli = NOTE['ani'][an]['scoli']
    # câmpul orașului: distanța dintre cea mai mică și cea mai mare mediană de școală,
    # calculat pe școlile care oricum ar intra în clasament
    camp = {}
    for oras in set(reg.values()):
        ms = [mediana_cu_neprezentati(r['note'], r['neprezentati'])
              for c, r in scoli.items()
              if reg.get(c) == oras and len(r['note']) >= BAZA_CAMP]
        ms = [m for m in ms if m is not None]
        camp[oras] = max(ms) - min(ms) if len(ms) > 1 else None

    for cod, r in scoli.items():
        oras = reg.get(cod)
        if oras is None or len(r['note']) < N_MIN:
            continue
        toate = np.asarray(cu_neprezentati(r['note'], r['neprezentati']), dtype=float)
        n = len(toate)
        esantioane = rng.integers(0, n, size=(B, n))
        meds = np.median(toate[esantioane], axis=1)
        lo, hi = np.percentile(meds, [2.5, 97.5])
        celule.append({'an': int(an), 'oras': oras, 'cod': cod,
                       'n_note': len(r['note']), 'n_total': n,
                       'latime': round(float(hi - lo), 3),
                       'acoperire': round(float(hi - lo) / camp[oras], 4) if camp[oras] else None})
    print(f'{an}: {sum(1 for c in celule if c["an"] == int(an))} celule')


def rezumat(sel):
    lat = sorted(c['latime'] for c in sel)
    acop = sorted(c['acoperire'] for c in sel if c['acoperire'] is not None)
    med = lambda v: v[len(v) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) / 2
    return {'n_celule': len(sel),
            'latime_mediana': round(med(lat), 3) if lat else None,
            'latime_q90': round(lat[int(0.9 * (len(lat) - 1))], 3) if lat else None,
            'acoperire_mediana': round(med(acop), 4) if acop else None}


# curba pe fiecare valoare a lui n, cât timp sunt destule celule; apoi pe intervale
pe_n = {}
for n in range(N_MIN, 41):
    sel = [c for c in celule if c['n_note'] == n]
    if len(sel) >= 3:
        pe_n[n] = rezumat(sel)
BENZI = [(3, 7), (8, 11), (12, 14), (15, 19), (20, 29), (30, 49), (50, 99), (100, 10 ** 6)]
pe_banda = {f'{a}-{b if b < 1000 else "+"}': rezumat([c for c in celule
                                                     if a <= c['n_note'] <= b])
            for a, b in BENZI}

# --- pragurile, derivate din criterii ---
def acoperire_la(n):
    sel = sorted(c['acoperire'] for c in celule
                 if c['acoperire'] is not None and abs(c['n_note'] - n) <= FEREASTRA)
    if len(sel) < 12:
        return None
    return sel[len(sel) // 2] if len(sel) % 2 else (sel[len(sel) // 2 - 1] + sel[len(sel) // 2]) / 2


curba = {n: acoperire_la(n) for n in range(N_MIN, 60)}
praguri = {}
for nume, tinta in CRITERII.items():
    ales = None
    for n in sorted(curba):
        a = curba[n]
        # primul n de la care acoperirea scade sub țintă ȘI rămâne sub ea
        if a is not None and a < tinta and all(
                (curba[m] is None or curba[m] < tinta) for m in sorted(curba) if m > n):
            ales = n
            break
    assert ales is not None, f'criteriul {nume} ({tinta}) nu e atins nicăieri pe curbă'
    praguri[nume] = {'valoare': ales, 'criteriu': round(tinta, 4),
                     'acoperire_la_prag': round(curba[ales], 4)}
    print(f'{nume}: {ales} candidați (acoperire {100 * curba[ales]:.1f}%, '
          f'criteriu sub {100 * tinta:.0f}%)')

json.dump({'B': B, 'n_minim_analizat': N_MIN, 'fereastra': FEREASTRA,
           'baza_camp': BAZA_CAMP, 'criterii': CRITERII, 'praguri': praguri,
           'curba_acoperire': {str(n): (round(a, 4) if a is not None else None)
                               for n, a in curba.items()},
           'celule': celule, 'pe_numar_de_candidati': pe_n, 'pe_banda': pe_banda},
          io.open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False)

print()
print(f"{'candidați':>12} {'celule':>7} {'lățime mediană':>15} {'lățime P90':>11} {'acoperire':>10}")
for k, v in pe_banda.items():
    if v['n_celule']:
        print(f"{k:>12} {v['n_celule']:>7} {v['latime_mediana']:>15.3f} "
              f"{v['latime_q90']:>11.3f} {100 * v['acoperire_mediana']:>9.1f}%")
print()
print('salvat:', os.path.normpath(OUT))
