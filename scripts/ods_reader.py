# Cititor ODS în flux, pentru fișiere mari.
#
# De ce nu odfpy: încarcă tot documentul în memorie, iar `content.xml` al lui
# bac_2017_s1.ods are sute de MB desfăcut. Aici se face iterparse pe membrul din zip și
# se curăță fiecare rând după folosire.
#
# ODS ține valoarea numerică în atributul office:value (neafectat de virgula zecimală din
# reprezentarea vizuală, care e în <text:p>), deci nu există problema care sparge CSV-ul.
import zipfile
from xml.etree.ElementTree import iterparse

NS_T = '{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
NS_O = '{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'

def _text(cell):
    return ''.join(cell.itertext()).strip()

def _valoare(cell):
    t = cell.get(NS_O + 'value-type')
    if t == 'float' or t == 'percentage' or t == 'currency':
        v = cell.get(NS_O + 'value')
        if v is None:
            return None
        f = float(v)
        return int(f) if f.is_integer() and abs(f) < 1e15 else f
    if t == 'boolean':
        return cell.get(NS_O + 'boolean-value')
    if t is None:
        s = _text(cell)
        return s if s else None
    return _text(cell) or None

def randuri(path, max_goale=50):
    """Generează rândurile primei foi, ca liste de valori.

    Oprește după `max_goale` rânduri consecutive goale — ODS-urile au adesea mii de
    rânduri-fantomă la final, declarate prin number-rows-repeated.
    """
    with zipfile.ZipFile(path) as z:
        with z.open('content.xml') as f:
            goale = 0
            for ev, el in iterparse(f, events=('end',)):
                if el.tag != NS_T + 'table-row':
                    continue
                rand, ultim_plin = [], -1
                for cell in el:
                    if cell.tag != NS_T + 'table-cell':
                        continue
                    rep = int(cell.get(NS_T + 'number-columns-repeated', 1))
                    val = _valoare(cell)
                    if rep > 1024 and val is None:      # coada de celule goale a rândului
                        break
                    for _ in range(rep):
                        rand.append(val)
                        if val is not None:
                            ultim_plin = len(rand) - 1
                el.clear()
                rand = rand[:ultim_plin + 1]
                if not rand:
                    goale += 1
                    if goale > max_goale:
                        return
                    continue
                goale = 0
                rrep = int(el.get(NS_T + 'number-rows-repeated', 1))
                for _ in range(min(rrep, 1)):           # rândurile repetate real sunt goale
                    yield rand

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    it = randuri(sys.argv[1])
    h = next(it)
    print(f'coloane: {len(h)}')
    print(h)
    r1 = next(it)
    print('\nrând 1:')
    for n, v in zip(h, r1):
        print(f'   {str(n)[:24]:<24} = {v!r}')
    n = 2 + sum(1 for _ in it)
    print(f'\nrânduri: {n:,}')
