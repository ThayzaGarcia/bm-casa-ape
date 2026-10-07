import base64, json, re, pathlib
S = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path('/home/user/bm-casa-ape/relatorios/maximize/guarana-tuchaua-setembro-2026.html')
RED, DK, BLK = '#EA2548', '#9A0000', '#000000'
M = ['JAN|26','FEV|26','MAR|26','ABR|26','MAIO|26','JUN|26','JUL|26','AGO|26','SET|26']
N = None
def bar(data, color=RED, **kw):
    d = {'data': data, 'color': color}; d.update(kw); return d
igRet = [9,6,19,13,16,1,5,4,3.3]
fbRet = [-4,-10,-3,9,9,1,13,3,3.3]
charts = {
  'gtIgAlc': {'bars': [bar([181750,154437,29170,136817,416610,1382413,316051,168782,47560])], 'fv': 9, 'fx': 8.5, 'bw': 30},
  'gtIgSeg': {'bars': [bar([15873,16100,16207,16660,18558,19293,19567,19791,19852])], 'fv': 9, 'fx': 8.5, 'bw': 28},
  'gtIgInt': {'bars': [bar([6208,4012,6050,5746,33769,41424,15582,8369,1093])], 'fv': 9.5, 'fx': 8.5, 'bw': 30},
  'gtIgRet': {'line': {'data': igRet, 'color': BLK, 'suf': '%', 'fs': 12}, 'fx': 8.5, 'top': 14},
  'gtIgOrgPag': {'bars': [bar([3072,3532,N,5706,47295,114900,18306,17910,N], RED, lc=RED, pend=False),
                          bar([179392,153091,27266,132375,385613,1291337,296800,341826,50130], DK, lc=DK)], 'fv': 8.5, 'fx': 8.5, 'bw': 22, 'top': 22},
  'gtIgVis': {'bars': [bar([2503,3856,751,3366,12128,65553,5676,5271,1862], RED, lc=RED)],
              'line2': {'data': [N,227,107,453,1898,735,274,224,61], 'color': DK},
              'line': {'data': igRet, 'color': BLK, 'suf': '%', 'diamond': True, 'below': False, 'scale': .25, 'fs': 11, 'bold': True},
              'fv': 9.5, 'fx': 8.5, 'bw': 34, 'top': 18},
  'gtIgFmt': {'bars': [bar([5,2,3,2,2,5,2,0,5], RED), bar([2,1,1,0,0,3,1,2,1], BLK), bar([2,2,3,3,4,0,4,4,2], DK)], 'fv': 10, 'fx': 8, 'bw': 16, 'top': 18},
  'gtIgEdit': {'labels': ['cultural/regional','sazonal (verão)','collab creator','gastronomia','consumo','inspiracional'], 'bars': [bar([2,2,1,1,1,1])], 'fv': 13, 'fx': 9.5, 'bw': 44, 'top': 20},
  'gtInv': {'labels': ['MAIO|26','JUN|26','JUL|26','AGO|26','SET|26'], 'bars': [bar([4699.56,12943.64,2098.51,1375.74,699.73])], 'money': True, 'fv': 10, 'fx': 9, 'bw': 44, 'top': 20},
  'gtFoco': {'labels': ['MAIO|26','JUN|26','JUL|26','AGO|26','SET|26'], 'suf': '%', 'bars': [bar([41,20,14,13,0], RED, lc=RED), bar([59,80,86,87,100], DK, lc=DK)], 'fv': 10, 'fx': 9, 'bw': 22, 'top': 18},
  'gtFbVis': {'bars': [bar([4645,2559,258,11832,19543,132645,46014,20382,20406])], 'fv': 9, 'fx': 8.5, 'bw': 30},
  'gtFbSeg': {'bars': [bar([1189,1181,1180,1222,1285,1309,1348,1358,1365])], 'fv': 9, 'fx': 8.5, 'bw': 30},
  'gtFbInt': {'bars': [bar([25,10,2,238,467,778,1914,372,65])], 'fv': 10, 'fx': 8.5, 'bw': 30},
  'gtFbRet': {'line': {'data': fbRet, 'color': BLK, 'suf': '%', 'fs': 12, 'below': False}, 'fx': 8.5, 'top': 22},
  'gtFbCombo': {'bars': [bar([97,52,33,493,689,3855,4146,293,214], RED, lc=RED)],
                'line2': {'data': [-4,-5,-1,42,63,24,39,10,7], 'color': DK},
                'line': {'data': fbRet, 'color': BLK, 'suf': '%', 'diamond': True, 'below': False, 'scale': .3, 'fs': 13, 'bold': True},
                'fv': 13, 'fx': 12, 'bw': 56, 'top': 30},
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
