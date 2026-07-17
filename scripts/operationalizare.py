# Sursa unică a operaționalizării: arborele profil → filieră.
#
# Modelul e tabul „Operaționalizare" din raportul F2202/PatrimVen: arborele coboară de la
# concept (rădăcina) la clasele terminale (frunzele), iar figura NU se scrie de mână — se
# generează din aceeași sursă care aplică regula, ca să nu poată diverge de ea.
#
# Aici regula e o partiție: fiecare profil aparține exact unei filiere. Nu o postulăm, o
# verificăm pe date la fiecare rulare (assert-ul de mai jos): dacă vreun profil ar apărea
# în două filiere, arborele nu se generează. Verificat pe 84.868 de candidați, 9 ani,
# 3 orașe: 9 profiluri, fiecare cu o singură filieră, zero excepții.
import os, json
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..', 'date', 'bac')
FILIERE = ('teoretica', 'tehnologica', 'vocationala')
NUME_FIL = {'teoretica': 'Teoretică', 'tehnologica': 'Tehnologică', 'vocationala': 'Vocațională'}

def construieste(candidati, doar_oras=None, orase=None):
    """Arborele filieră → profil, cu efective, derivat din date. Ridică AssertionError
    dacă partiția nu ține."""
    pe_profil = defaultdict(Counter)
    n_profil = Counter()
    for (an, siiir, forma, filiera, profil, promo, status, mp, mc) in candidati:
        if promo != 1 or mc is None or filiera not in FILIERE:
            continue
        if doar_oras and orase[siiir] != doar_oras:
            continue
        pe_profil[profil][filiera] += 1
        n_profil[profil] += 1
    ambigue = {p: dict(c) for p, c in pe_profil.items() if len(c) > 1}
    assert not ambigue, f'profil cu mai multe filiere — partiția nu ține: {ambigue}'
    fil_of = {p: next(iter(c)) for p, c in pe_profil.items()}
    copii = defaultdict(list)
    for p, f in fil_of.items():
        copii[f].append(p)
    arbore = {'name': 'Candidați, promoția curentă', 'n': sum(n_profil.values()), 'children': []}
    for f in FILIERE:
        ps = sorted(copii[f], key=lambda p: -n_profil[p])
        if not ps:
            continue
        arbore['children'].append({
            'name': NUME_FIL[f], 'n': sum(n_profil[p] for p in ps),
            'children': [{'name': p, 'n': n_profil[p]} for p in ps]})
    return arbore

def layout(arbore, dx=34, dy=250):
    """Tidy tree orizontal, calculat aici (CSP-ul artifactului blochează d3 de pe CDN).
    Frunzele se așază la pas fix; părintele se centrează pe copii."""
    noduri, muchii = [], []
    y = [0.0]
    def plaseaza(nod, adanc):
        if nod.get('children'):
            xs = [plaseaza(c, adanc + 1) for c in nod['children']]
            x = (xs[0] + xs[-1]) / 2
        else:
            x = y[0]
            y[0] += dx
        nod['_x'], nod['_y'] = x, adanc * dy
        noduri.append(nod)
        for c in nod.get('children', []):
            muchii.append((nod, c))
        return x
    plaseaza(arbore, 0)
    return noduri, muchii

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    d = json.load(open(os.path.join(BASE, 'candidati_bac.json'), encoding='utf-8'))
    a = construieste(d['candidati'])
    print('partiția profil → filieră ține pe toate datele.\n')
    print(f'{a["name"]}  (n={a["n"]:,})')
    for f in a['children']:
        print(f'  ├─ {f["name"]:<14} n={f["n"]:>6,}')
        for p in f['children']:
            print(f'  │    └─ {p["name"]:<44} n={p["n"]:>6,}')
