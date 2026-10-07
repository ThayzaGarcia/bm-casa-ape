import base64, json, re, pathlib
S = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path('/home/user/bm-casa-ape/relatorios/maximize/eqtl-servicos-setembro-2026.html')
RED, DK, BLK = '#EA2548', '#9A0000', '#000000'
M = ['JAN|26','FEV|26','MAR|26','ABR|26','MAIO|26','JUN|26','JUL|26','AGO|26','SET|26']
N = None
def bar(data, color=RED, **kw):
    d = {'data': data, 'color': color}; d.update(kw); return d
ret = [8,11,9,6,10,7,6,9,4.8]
charts = {
  'eqAlc': {'bars': [bar([582767,877867,969197,1011755,640791,604910,643892,357702,351469])], 'fv': 8.5, 'fx': 8.5, 'bw': 30},
  'eqSeg': {'bars': [bar([26377,28549,30665,31875,33356,34682,36440,38311,39448])], 'fv': 8.5, 'fx': 8.5, 'bw': 28},
  'eqNovos': {'bars': [bar([1519,2172,2116,1210,1481,1326,1758,1871,1137])], 'fv': 9, 'fx': 8.5, 'bw': 30},
  'eqInt': {'bars': [bar([5935,7686,9439,3493,2585,1982,2873,4345,1169])], 'fv': 9.5, 'fx': 8.5, 'bw': 30},
  'eqRet': {'line': {'data': ret, 'color': BLK, 'suf': '%', 'fs': 12}, 'fx': 8.5, 'top': 14},
  'eqVis': {'bars': [bar([19597,20546,23356,19032,14491,18724,30657,20933,23650], RED, lc=RED)],
            'line2': {'data': [1519,2172,2116,1210,1481,1326,1758,1871,1137], 'color': DK},
            'line': {'data': ret, 'color': BLK, 'suf': '%', 'diamond': True, 'below': False, 'scale': .35, 'fs': 12, 'bold': True},
            'fv': 11, 'fx': 10, 'bw': 44, 'top': 22},
  'eqFmt': {'bars': [bar([2,8,7,2,3,1,6,6,2], RED), bar([3,2,4,3,4,7,2,3,5], BLK), bar([4,4,2,6,3,2,0,3,3], DK)], 'fv': 10, 'fx': 8, 'bw': 16, 'top': 18},
  'eqEdit': {'labels': ['venda direta','engajamento (collab)','informativo','social'], 'bars': [bar([6,1,2,1])], 'fv': 13, 'fx': 10, 'bw': 50, 'top': 20},
  'eqInv': {'bars': [bar([32578.45,35912.74,47848.18,47880.62,29573.69,40340.28,42483.80,45562.40,N])], 'money': True, 'fv': 8.5, 'fx': 9, 'bw': 40, 'top': 22},
  'eqIdade': {'labels': ['18-24','25-34','35-44','45-54','55-64','65+'], 'suf': '%', 'bars': [bar([10,34.5,31,15,5.5,3])], 'fv': 11, 'fx': 10, 'bw': 36, 'top': 18},
  'eqGeo': {'labels': ['Teresina','São Luís','Belém','Maceió','Timon','Imperatriz'], 'suf': '%', 'bars': [bar([9.6,9.5,4.4,3.7,2.5,2.3])], 'fv': 11, 'fx': 9.5, 'bw': 34, 'top': 18},
  'eqGen': {'labels': ['feminino','masculino'], 'suf': '%', 'bars': [bar([65.6,34.4])], 'fv': 13, 'fx': 11, 'bw': 50, 'top': 18},
}
data = {'meses': M, 'charts': charts}
t = (S/'head.html').read_text(encoding='utf8') + (S/'slides.html').read_text(encoding='utf8') + (S/'tail.html').read_text(encoding='utf8')
def img(m):
    b = (S/'emb'/(m.group(1)+'.jpg')).read_bytes()
    return 'data:image/jpeg;base64,' + base64.b64encode(b).decode()
t = re.sub(r'%%IMG:(\w+)%%', img, t)
t = t.replace('%%DATA%%', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
assert '%%' not in t
OUT.write_text(t, encoding='utf8'); print(OUT, len(t))
