"""Fiecare cifra din proza index.html, verificata contra JSON-urilor din date/."""
import io, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
D = os.path.join(P, 'date')
J = lambda n: json.load(io.open(os.path.join(D, n), encoding='utf-8'))

# Se verifică pagina dată ca argument (build-ul trimite fișierul candidat, înainte ca el
# să ia locul celui vechi); fără argument, pagina publicată.
PAGINA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(P, 'index.html')
html = io.open(PAGINA, encoding='utf-8').read()
proza = html[:html.index('<script src=')]

ok = bad = 0
def check(eticheta, conditie, detaliu=''):
    global ok, bad
    if conditie:
        ok += 1
        print(f'  OK   {eticheta}')
    else:
        bad += 1
        print(f'  ###  {eticheta}   {detaliu}')

def r1(x): return round(x, 1)

print('--- Friedman (friedman_mediane.json) ---')
fr = J('friedman_mediane.json')
# Valorile sunt interpolate din aceste fisiere, deci a le compara cu ele e tautologic.
# Se testeaza AFIRMATIILE pe care le face textul, plus prezenta valorii in pagina.
W = {c: fr[c]['kendall_W'] for c in ('IAȘI', 'TIMIȘOARA', 'CLUJ-NAPOCA')}
check('textul spune ca la Cluj scolile sunt cel mai putin sincrone',
      min(W, key=W.get) == 'CLUJ-NAPOCA', W)
for c, v in W.items():
    check(f'W {c} apare in pagina', f'{v:.2f}'.replace('.', ',') in proza, v)

rm = {c: fr[c]['rang_mediu'] for c in W}
ANI = [str(y) for y in range(2020, 2026)]
jos = sorted({a for c in rm for a in sorted(rm[c], key=lambda a: rm[c][a])[:2]})
check('cei doi ani de jos sunt aceiasi in toate trei orasele', len(jos) == 2, jos)
check('anii de jos sunt numiti in pagina', all(a in proza for a in jos), jos)
top = {c: max(rm[c], key=rm[c].get) for c in rm}
check('Cluj si Timisoara au acelasi an de varf',
      top['CLUJ-NAPOCA'] == top['TIMIȘOARA'], top)
check('Iasi are alt an de varf decat Cluj', top['IAȘI'] != top['CLUJ-NAPOCA'], top)
check('anul de varf al Iasului sta langa cei doi vecini ai lui la Cluj',
      'între anii de mijloc' in proza)

ex = fr['_exemplu']
med = ex['mediane']
check('exemplul didactic e tot Take Ionescu', 'TAKE IONESCU' in ex['denumire'].upper())
check('toate medianele exemplului apar in pagina',
      all(f'{med[a]:g}'.replace('.', ',') in proza for a in ANI), med)
check('pozitiile exemplului apar in pagina',
      ', '.join(str(int(ex['ranguri'][a])) for a in ANI) in proza)
per = min(((abs(med[a] - med[b]), a, b) for i, a in enumerate(ANI) for b in ANI[i + 1:]))
check('perechea de ani cea mai apropiata e cea numita in text',
      per[1] in proza and per[2] in proza and f'{per[0]:.3f}'.replace('.', ',') in proza, per)

print('--- Kruskal-Wallis (kw_pe_ani.json) ---')
kw = J('kw_pe_ani.json')['ani']
eps = {a: v['epsilon2'] for a, v in kw.items()}
check('efectul e mic in toti anii (eps2 sub 0,15)', max(eps.values()) < 0.15, max(eps.values()))
# eps2 poate iesi negativ; textul trebuie sa spuna asta exact cand se intampla
neg = [a for a in eps if eps[a] < 0]
check('fraza despre eps2 negativ apare exact cand exista eps2 negativ',
      bool(neg) == ('iese negativă' in proza), f'ani cu eps2<0: {neg}')
for a in neg:
    check(f'{a}: valoarea negativa e in text', f'{eps[a]:.3f}'.replace('.', ',') in proza, eps[a])
C = ['CLUJ-NAPOCA', 'IAȘI', 'TIMIȘOARA']
check('TM ultima in toti cei 6 ani',
      all(min(v['rang_mediu'], key=v['rang_mediu'].get) == 'TIMIȘOARA' for v in kw.values()))
check('CJ primul 2020-2024',
      all(max(kw[a]['rang_mediu'], key=kw[a]['rang_mediu'].get) == 'CLUJ-NAPOCA'
          for a in map(str, range(2020, 2025))))
check('IS primul in 2025',
      max(kw['2025']['rang_mediu'], key=kw['2025']['rang_mediu'].get) == 'IAȘI')
sig = {a: [d['pereche'] for d in v['dunn_holm'] if d['p_holm'] < 0.05] for a, v in kw.items()}
check('singurul contrast semnificativ e CJ-TM',
      set(p for ps in sig.values() for p in ps) == {'CLUJ-NAPOCA vs TIMIȘOARA'}, sig)
ani_sig = [a for a, ps in sig.items() if ps]
check('anii cu contrast semnificativ sunt cei din text',
      all(a in proza for a in ani_sig) and bool(ani_sig), ani_sig)
check('anii in care omnibusul nu respinge sunt cei fara pereche semnificativa',
      [a for a in kw if kw[a]['p'] > 0.05] == [a for a in kw if not sig[a]],
      {a: (kw[a]['p'], bool(sig[a])) for a in kw})
# cazul de granita: o pereche semnificativa sub un omnibus care nu respinge
granita = [a for a in kw if kw[a]['p'] >= 0.05 and sig[a]]
check('fraza despre cazul de granita apare exact cand exista un astfel de an',
      bool(granita) == ('sub un test de ansamblu care nu respinge' in proza),
      f'ani de granita: {granita}')

print('--- clasamentul, cu intervale de rang ---')
rg = J('ranguri_bootstrap.json')
sag_t = sum(v['sageti_afisate'] for v in rg['sageti'].values())
sag_s = sum(v['sustinute'] for v in rg['sageti'].values())
check('numarul de sageti testate apare in pagina', str(sag_t) in proza, sag_t)
check('textul spune cate se sustin, si e adevarat',
      ('niciuna nu se susține' in proza) if sag_s == 0 else
      ('una singură se susține' in proza) if sag_s == 1 else (str(sag_s) in proza), sag_s)
check('sagetile nu mai apar in tabel', '▲' not in proza and '▼' not in proza)
for an, sc in rg['ani'].items():
    v = sorted(sc.values(), key=lambda x: x['rang_publicat'])
    mij = v[len(v) // 2]
    check(f'{an}: primul loc e neambiguu',
          round(v[0]['rang_lo']) == round(v[0]['rang_hi']) == 1,
          (v[0]['rang_lo'], v[0]['rang_hi']))
    check(f'{an}: ultima scoala se desparte de cea din mijloc',
          v[-1]['rang_lo'] > mij['rang_hi'], (v[-1]['rang_lo'], mij['rang_hi']))

print('--- neprezentatii ---')
npz = J('neprezentati.json')
cor = npz['corelatie_nivel_vs_pondere']['TOATE']
check('corelatia e negativa sub toate trei masurile',
      all(v < 0 for k, v in cor.items() if k != 'n'), cor)
check('corelatia nu e un artefact al medianei: media da acelasi semn si marime',
      abs(cor['mediana_en'] - cor['media_en']) < 0.1, (cor['mediana_en'], cor['media_en']))
check('corelatia tine si pe masura din afara examenului (V-VIII)',
      cor['mediana_viii'] < -0.2, cor['mediana_viii'])
for k in ('mediana_en', 'media_en', 'mediana_viii'):
    check(f'valoarea {k} apare in pagina',
          f'{abs(cor[k]):.2f}'.replace('.', ',') in proza, cor[k])
pond = npz['pondere_neprezentati_pct']
ANI_N = sorted(next(iter(pond.values())))
top = {max(pond, key=lambda o: pond[o][a]) for a in ANI_N}
check('niciun oras nu are constant cea mai mare pondere de neprezentati', len(top) > 1, top)
misc = [abs(v) for o in npz['miscarea_medianei_orasului'].values() for v in o.values()]
check('miscarea medianei orasului e mica (sub 0,2 puncte)', max(misc) < 0.2, max(misc))
semne = {v > 0 for o in npz['miscarea_medianei_orasului'].values() for v in o.values() if v}
check('miscarea are semne diferite, deci nu e o coborare sistematica', len(semne) > 1, semne)

print('--- diferenta medie-mediana ---')
mv = J('medie_vs_mediana_percentil.json')
check('r = -0,64', round(mv['corelatie_medie_vs_gap'], 2) == -0.64, mv['corelatie_medie_vs_gap'])
check('media sub percentila 50 in toti cei 6 ani',
      all(v['gap_mediu'] < 0 for v in mv['per_an'].values()))

print('--- consistenta interna a prozei ---')
for t in ('div', 'p', 'h2', 'table', 'th', 'svg', 'b', 'li'):
    o = len(re.findall(r'<%s[ >]' % t, proza)); c = len(re.findall(r'</%s>' % t, proza))
    check(f'taguri <{t}> echilibrate', o == c, f'{o} deschise / {c} inchise')
for interzis in ('gap ', 'varianț', 'heterogen', 'NU e semnificativ', 'Consecința metodologică',
                 'pas cu pas', 'imaginea completă', 'mediana_cenzurata'):
    check(f'nu mai apare: {interzis!r}', interzis not in proza)

print()
print(f'{ok} verificari trecute, {bad} cazute')
sys.exit(1 if bad else 0)
