# Descarcă rezultatele BAC per-candidat, sesiunea de vară (I/iunie), 2017-2025,
# de pe data.gov.ro în date/bac/. URL-uri din API-ul CKAN (package_show pe fiecare set).
#
# ALEGE ÎNTOTDEAUNA FORMATUL CU VALORI TIPATE (XLSX sau ODS), NICIODATĂ CSV.
# CSV-urile ministerului au separatorul zecimal virgulă ne-quotat: „6,31" devine două
# câmpuri, rândurile ajung la 52-61 de câmpuri la un antet de 52, iar nota nu se poate
# reconstrui din format — „5,6 · 9" și „5 · 6,9" sunt amândouă valide și dau medii
# diferite. Prima versiune a acestui script prefera CSV-ul „ca să nu depindem de ODS" și
# pierdea astfel 1,8% din rânduri în 2017 și 2019, complet degeaba: aceleași seturi conțin
# un XLSX (2019) și un ODS (2017), cu valorile ca numere. Verifică toate resursele unui
# set înainte de a alege (package_show), nu doar prima.
#
# 2016 nu se descarcă: e scos din analiză (singurul an cu regula veche de contestație).
import sys, os, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.join(os.path.dirname(__file__), '..', 'date', 'bac')

FILES = {
    'bac_2017_s1.ods':  'https://data.gov.ro/dataset/cb54fa0b-4d8c-4cef-b0d9-fe80e0c99743/resource/fd31ca32-cbfb-4fb2-ba9f-49e80a966e65/download/2017-09-25-date-deschise-2017-i.ods',
    'bac_2018_s1.xlsx': 'https://data.gov.ro/dataset/1007a44d-0b53-477a-bc49-8c59e00db39e/resource/bda23092-c00e-4feb-92bf-9df53e19f366/download/date-deschise-bac-2018-sesiunea-1.xlsx',
    'bac_2019_s1.xlsx': 'https://data.gov.ro/dataset/83ab8216-a862-407c-ad74-7dba39d22061/resource/450e7341-ec1e-43f8-b9f8-75145afc894c/download/2019-08-06-date-deschise-bac-2019-i.xlsx',
    'bac_2020_s1.xlsx': 'https://data.gov.ro/dataset/e996dc5c-48d1-4cbc-9aaf-2f4c3a2362a5/resource/b0de486e-fa2f-4380-9c6c-71e36d6e35c1/download/date-deschise-bac-2020-sesiunea-1.xlsx',
    'bac_2021_s1.xlsx': 'https://data.gov.ro/dataset/6827d28b-76de-41e1-a75a-a9251b04714a/resource/2db91f1c-77a6-44bd-a5d7-e1c384c49275/download/2021.08.10_bac_date-deschise_2021.xlsx',
    'bac_2022_s1.xlsx': 'https://data.gov.ro/dataset/0778231d-be65-41c8-9530-6f8dbceaaa08/resource/9e0419b2-342c-4849-ad69-78f6dab8efc4/download/2022.07.06_bac_export-sesiunea-1-2022.xlsx',
    'bac_2023_s1.xlsx': 'https://data.gov.ro/dataset/90cd5404-01b7-4002-ac63-6e44917afbf9/resource/9635d473-edcb-4df6-af26-968f8030df54/download/2023.07.19_bac_date-deschise_2023-ses1.xlsx',
    'bac_2024_s1.xlsx': 'https://data.gov.ro/dataset/c23424d9-2367-44ee-a19f-2405277ed9ec/resource/46737b48-5873-4775-8621-f9b28fef6ed7/download/2024.09.30_bac_date-deschise_2024-ses1.xlsx',
    'bac_2025_s1.xlsx': 'https://data.gov.ro/dataset/b3af0e55-19ff-4e6c-8b1c-6a715c10cb04/resource/c101dded-606c-4807-8059-e7f3cb4fd3aa/download/2025.10.01_bac_2025-ses1_date-deschise.xlsx',
}

os.makedirs(BASE, exist_ok=True)
for fname, url in FILES.items():
    dest = os.path.join(BASE, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print(f'{fname}: există deja ({os.path.getsize(dest):,} B), sar')
        continue
    print(f'{fname}: descarc...', flush=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, 'wb') as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    print(f'{fname}: OK, {os.path.getsize(dest):,} B')
