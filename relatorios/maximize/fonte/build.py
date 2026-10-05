import base64, json, re, pathlib
S = pathlib.Path(__file__).resolve().parent  # template.html aqui; imagens em pdfs/emb/
OUT = pathlib.Path('/home/user/bm-casa-ape/relatorios/maximize/echo-enova-setembro-2026.html')

RED, DK, BLK, GRY, PINK, LGRY = '#EA2548', '#9A0000', '#000000', '#A6A6A6', '#D96B6B', '#6B6B6B'
M = ['JAN|26', 'FEV|26', 'MAR|26', 'ABR|26', 'MAIO|26', 'JUN|26', 'JUL|26', 'AGO|26', 'SET|26']
N = None

def bar(data, color=RED, **kw):
    d = {'data': data, 'color': color}; d.update(kw); return d

charts = {
  # ---------- Echo Instagram ----------
  'echoIgAlcance': {'bars': [bar([612663,254014,226831,315849,323722,158841,198089,58077,52155])], 'fv': 10.5, 'fx': 8.5, 'bw': 30},
  'echoIgSeg':     {'bars': [bar([100,76,256,635,430,618,244,79,91])], 'fv': 11, 'fx': 8.5, 'bw': 28},
  'echoIgInter':   {'bars': [bar([3560,2088,4013,4027,4676,2053,2729,2541,1976])], 'fv': 11, 'fx': 8.5, 'bw': 30},
  'echoIgRet':     {'line': {'data': [4,7,14,20,18,30,14,7,7], 'color': BLK, 'suf': '%', 'fs': 12}, 'fx': 8.5, 'top': 14},
  'echoIgOrgPag':  {'bars': [bar([3714,3907,7559,4399,4227,4597,8150,8737,7928], RED, lc=RED),
                             bar([608479,251663,220071,313205,321514,156018,191017,50285,43750], DK, lc=DK)], 'fv': 8.5, 'fx': 8.5, 'bw': 22, 'top': 22},
  'echoIgVisitas': {'bars': [bar([2577,1098,1790,3186,2423,2074,1741,1207,1308], RED, lc=RED)],
                    'line2': {'data': [100,76,256,635,430,618,244,79,91], 'color': DK},
                    'line': {'data': [4,7,14,20,18,30,14,7,7], 'color': BLK, 'suf': '%', 'diamond': True, 'below': False, 'scale': .9, 'fs': 11, 'bold': True},
                    'fv': 9.5, 'fx': 8.5, 'bw': 34, 'top': 18},
  'echoIgEdit':    {'bars': [bar([0,1,1,1,5,1,3,2,1], RED, name='produto/informativo', hideZero=True),
                             bar([0,4,2,3,3,7,4,6,6], BLK, name='institucional (parceria ou autoridade)', hideZero=True),
                             bar([6,5,6,3,6,4,6,7,6], GRY, name='educativo', hideZero=True),
                             bar([7,4,4,3,3,4,2,5,4], DK, name='timing/sazonalidade', hideZero=True),
                             bar([3,0,0,0,0,0,0,0,5], PINK, name='mercado livre de energia', hideZero=True),
                             bar([0,1,2,1,1,1,2,1,1], LGRY, name='ESG', hideZero=True)], 'fv': 9, 'fx': 9, 'bw': 13, 'top': 14},
  'echoIgFmt':     {'bars': [bar([2,6,9,9,10,10,11,13,13], RED), bar([5,3,1,2,1,2,0,2,1], BLK), bar([9,6,8,6,10,6,8,6,9], DK)], 'fv': 10.5, 'fx': 9, 'bw': 20, 'top': 18},
  # ---------- Enova Instagram ----------
  'enovaIgAlcance': {'bars': [bar([1716,2096,1138,1121,901,1621,1064,1096,668])], 'fv': 10.5, 'fx': 8.5, 'bw': 30},
  'enovaIgSeg':     {'bars': [bar([-47,-61,-15,-17,-141,5,-33,-27,-33])], 'fv': 11, 'fx': 8.5, 'bw': 28},
  'enovaIgInter':   {'bars': [bar([226,368,279,152,139,660,269,221,201])], 'fv': 11, 'fx': 8.5, 'bw': 30},
  'enovaIgRet':     {'line': {'data': [-7,-8,-2,-3,-27,1,-6,-4,-6.1], 'color': BLK, 'suf': '%', 'fs': 12, 'below': False}, 'fx': 8.5, 'top': 18},
  'enovaIgOrgPag':  {'bars': [bar([1700,2085,1136,1121,898,1617,1054,1095,N], RED, lc=RED),
                              bar([17,10,2,1,3,3,10,1,N], DK, lc=DK, pend=False)], 'fv': 9, 'fx': 8.5, 'bw': 22, 'top': 22},
  'enovaIgVisitas': {'bars': [bar([680,735,628,546,521,570,593,620,543], RED, lc=RED)],
                     'line2': {'data': [-47,-61,-15,-17,-141,5,-33,-27,-33], 'color': DK},
                     'line': {'data': [-7,-8,-2,-3,-27,1,-6,-4,-6.1], 'color': BLK, 'suf': '%', 'diamond': True, 'below': False, 'scale': .14, 'fs': 10, 'bold': True},
                     'fv': 9.5, 'fx': 8.5, 'bw': 34, 'top': 18},
  'enovaIgEdit':    {'bars': [bar([1,4,4,2,1,2,1,3,3], RED, name='produto', hideZero=True),
                              bar([3,0,2,1,2,1,0,1,0], DK, name='timing/sazonalidade', hideZero=True, pend=False),
                              bar([2,2,2,1,2,4,2,1,0], GRY, name='educativo', hideZero=True, pend=False),
                              bar([0,0,0,1,0,1,0,2,0], PINK, name='institucional', hideZero=True, pend=False),
                              bar([0,2,0,0,0,0,0,0,1], LGRY, name='ESG', hideZero=True, pend=False)], 'fv': 9, 'fx': 9, 'bw': 14, 'top': 14},
  'enovaIgFmt':     {'bars': [bar([1,1,3,3,2,5,2,2,1], RED), bar([1,4,3,0,0,0,0,0,0], BLK), bar([5,2,2,2,3,3,2,4,3], DK)], 'fv': 10.5, 'fx': 9, 'bw': 20, 'top': 18},
  # ---------- Echo LinkedIn ----------
  'echoLiVis':   {'bars': [bar([2650,1883,2142,2475,2436,2456,2325,2447,2202])], 'fv': 10.5, 'fx': 8.5, 'bw': 30},
  'echoLiSeg':   {'bars': [bar([1090,1366,911,833,664,613,537,528,567])], 'fv': 10.5, 'fx': 8.5, 'bw': 28},
  'echoLiInter': {'bars': [bar([652,729,472,749,741,620,826,912,494])], 'fv': 11, 'fx': 8.5, 'bw': 30},
  'echoLiRet':   {'line': {'data': [41,75,43,34,27,25,23,22,25.7], 'color': BLK, 'suf': '%', 'fs': 12}, 'fx': 8.5, 'top': 14},
  'echoLiFmt':   {'bars': [bar([3,2,4,6,6,4,3,7,2], RED), bar([6,0,0,2,3,2,3,1,9], BLK), bar([1,4,5,5,10,4,6,3,0], DK), bar([2,3,2,2,2,2,2,2,1], LGRY)], 'fv': 10, 'fx': 9, 'bw': 16, 'top': 18},
  'echoLiCombo': {'bars': [bar([2650,1883,2142,2475,2436,2456,2325,2447,2202], RED, lc=RED)],
                  'line2': {'data': [1090,1366,911,833,664,613,537,528,567], 'color': DK},
                  'line': {'data': [41,75,43,34,27,25,23,22,25.7], 'color': BLK, 'suf': '%', 'diamond': True, 'below': False, 'scale': .25, 'fs': 12, 'bold': True},
                  'fv': 12, 'fx': 11, 'bw': 56, 'top': 24},
  # ---------- Enova LinkedIn ----------
  'enovaLiVis':   {'bars': [bar([98,77,135,91,70,106,92,64,101])], 'fv': 11, 'fx': 8.5, 'bw': 30},
  'enovaLiSeg':   {'bars': [bar([5,5,7,17,35,35,18,5,20])], 'fv': 11, 'fx': 8.5, 'bw': 28},
  'enovaLiInter': {'bars': [bar([0,0,0,0,0,0,0,0,1])], 'fv': 11, 'fx': 8.5, 'bw': 30},
  'enovaLiRet':   {'line': {'data': [5,6,5,19,50,33,20,8,19.8], 'color': BLK, 'suf': '%', 'fs': 12, 'below': False}, 'fx': 8.5, 'top': 22},
  'enovaLiCombo': {'bars': [bar([98,77,135,91,70,106,92,64,101], RED, lc=RED)],
                   'line2': {'data': [5,5,7,17,35,35,18,5,20], 'color': DK},
                   'line': {'data': [5,6,5,19,50,33,20,8,19.8], 'color': BLK, 'suf': '%', 'diamond': True, 'below': False, 'scale': .45, 'fs': 12, 'bold': True},
                   'fv': 12, 'fx': 11, 'bw': 56, 'top': 24},
  'echoLiEdit': {'labels': ['institucional','educativo','ESG','timing/sazonal','mercado livre','newsletter'], 'bars': [bar([5,2,2,1,1,1])], 'fv': 12, 'fx': 10, 'bw': 40, 'top': 18},
  'nlComp': {'labels': ['visualizações','impressões','engajamento'], 'bars': [bar([8987,4788,100], GRY, name='ago'), bar([813,1555,22], RED, name='set')], 'fv': 11, 'fx': 11, 'bw': 40, 'top': 20},
}
data = {'meses': M, 'charts': charts}

t = (S / 'template.html').read_text(encoding='utf8')
def img(m):
    b = (S / 'pdfs/emb' / (m.group(1) + '.jpg')).read_bytes()
    return 'data:image/jpeg;base64,' + base64.b64encode(b).decode()
t = re.sub(r'%%IMG:(\w+)%%', img, t)
t = t.replace('%%DATA%%', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
assert '%%' not in t
OUT.write_text(t, encoding='utf8')
print(OUT, len(t))
