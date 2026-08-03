"""Fiecare cifra din proza index.html, verificata contra JSON-urilor din date/."""
import io, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
D = os.path.join(P, 'date')
J = lambda n: json.load(io.open(os.path.join(D, n), encoding='utf-8'))

html = io.open(os.path.join(P, 'index.html'), encoding='utf-8').read()
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
W = {c: fr[c]['kendall_W'] for c in ('IAȘI', 'TIMIȘOARA', 'CLUJ-NAPOCA')}
check('Kendall W Iasi 0,37', round(W['IAȘI'], 2) == 0.37, W['IAȘI'])
check('Kendall W TM 0,36', round(W['TIMIȘOARA'], 2) == 0.36, W['TIMIȘOARA'])
check('Kendall W CJ 0,12', round(W['CLUJ-NAPOCA'], 2) == 0.12, W['CLUJ-NAPOCA'])

rm = {c: fr[c]['rang_mediu'] for c in W}
jos = [rm[c][a] for c in rm for a in ('2021', '2024')]
check('interval 1,9-2,9 pt 2021+2024', (r1(min(jos)), r1(max(jos))) == (1.9, 2.9),
      (min(jos), max(jos)))
check('2021 si 2024 sunt cei mai mici doi ani, in fiecare oras',
      all(sorted(rm[c], key=lambda a: rm[c][a])[:2] == sorted(['2021', '2024'],
          key=lambda a: rm[c][a]) for c in rm))
check('CJ 2020 = 4,4', r1(rm['CLUJ-NAPOCA']['2020']) == 4.4, rm['CLUJ-NAPOCA']['2020'])
check('TM 2020 = 4,9', r1(rm['TIMIȘOARA']['2020']) == 4.9, rm['TIMIȘOARA']['2020'])
check('IS 2025 = 4,7', r1(rm['IAȘI']['2025']) == 4.7, rm['IAȘI']['2025'])
check('TM 2025 = 4,1', r1(rm['TIMIȘOARA']['2025']) == 4.1, rm['TIMIȘOARA']['2025'])
check('CJ 2025 = 3,8', r1(rm['CLUJ-NAPOCA']['2025']) == 3.8, rm['CLUJ-NAPOCA']['2025'])
check('max la CJ e 2020', max(rm['CLUJ-NAPOCA'], key=rm['CLUJ-NAPOCA'].get) == '2020')
check('max la TM e 2020', max(rm['TIMIȘOARA'], key=rm['TIMIȘOARA'].get) == '2020')
check('max la IS e 2025', max(rm['IAȘI'], key=rm['IAȘI'].get) == '2025')
check('CJ 2025 langa 2022 si 2023', abs(rm['CLUJ-NAPOCA']['2025'] - rm['CLUJ-NAPOCA']['2022']) < 0.2
      and abs(rm['CLUJ-NAPOCA']['2025'] - rm['CLUJ-NAPOCA']['2023']) < 0.2)

ex = fr['_exemplu']
med = ex['mediane']
check('Take Ionescu: medianele din text', [med[a] for a in map(str, range(2020, 2026))]
      == [8.95, 8.82, 8.835, 9.07, 8.7, 8.735], med)
check('Take Ionescu: pozitiile 5,3,4,6,1,2',
      [ex['ranguri'][a] for a in map(str, range(2020, 2026))] == [5, 3, 4, 6, 1, 2])
check('diferenta 2022-2021 = 0,015', abs((med['2022'] - med['2021']) - 0.015) < 1e-9,
      med['2022'] - med['2021'])

print('--- Kruskal-Wallis (kw_pe_ani.json) ---')
kw = J('kw_pe_ani.json')['ani']
eps = [v['epsilon2'] for v in kw.values()]
check('eps2 intre 0,00 si 0,05', 0 <= min(eps) and max(eps) <= 0.051, (min(eps), max(eps)))
check('cel mai mic eps2 e in 2023, = 0,002',
      min(kw, key=lambda a: kw[a]['epsilon2']) == '2023' and round(kw['2023']['epsilon2'], 3) == 0.002)
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
check('CJ-TM semnificativ in 2020, 2021, 2022, 2024',
      [a for a, ps in sig.items() if ps] == ['2020', '2021', '2022', '2024'], sig)
check('2023 si 2025: omnibus nu respinge', kw['2023']['p'] > 0.05 and kw['2025']['p'] > 0.05,
      (kw['2023']['p'], kw['2025']['p']))
check('2024: omnibus p=0,054', round(kw['2024']['p'], 3) == 0.054, kw['2024']['p'])
check('2024: Dunn CJ-TM p=0,047',
      round([d['p_holm'] for d in kw['2024']['dunn_holm']
             if d['pereche'] == 'CLUJ-NAPOCA vs TIMIȘOARA'][0], 3) == 0.047)

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
