import base64, json, re, pathlib
S = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path('/home/user/bm-casa-ape/relatorios/maximize/guarana-jesus-setembro-2026.html')
RED, DK, BLK = '#EA2548', '#9A0000', '#000000'
M = ['JAN|26','FEV|26','MAR|26','ABR|26','MAIO|26','JUN|26','JUL|26','AGO|26','SET|26']
N = None
def bar(data, color=RED, **kw):
    d = {'data': data, 'color': color}; d.update(kw); return d
igRet = [16,26,29,30,19,18,13,14,15.1]
fbRet = [-25,-38,13,-11,-7,1,-19,16,-17.1]
charts = {
  # ---------- Instagram ----------
  'gjIgAlc': {'bars': [bar([217695,160365,489418,446376,427986,1206396,262856,672476,212435])], 'fv': 9, 'fx': 8.5, 'bw': 30},
  'gjIgSeg': {'bars': [bar([55625,57426,61316,65889,69904,74948,76068,79470,81093])], 'fv': 9, 'fx': 8.5, 'bw': 28},
  'gjIgInt': {'bars': [bar([11567,6739,25408,12426,23985,31121,21035,36158,37336])], 'fv': 9.5, 'fx': 8.5, 'bw': 30},
  'gjIgRet': {'line': {'data': igRet, 'color': BLK, 'suf': '%', 'fs': 12}, 'fx': 8.5, 'top': 14},
  'gjIgOrgPag': {'bars': [bar([20424,12527,31571,20446,57414,39927,11085,88999,N], RED, lc=RED),
                          bar([196395,149344,469807,427294,380888,1173554,256217,589022,N], DK, lc=DK)], 'fv': 8.5, 'fx': 8.5, 'bw': 22, 'top': 22},
  'gjIgVis': {'bars': [bar([5129,6860,13454,15084,20794,28667,8917,23480,10771], RED, lc=RED)],
              'line2': {'data': [N,1801,3890,4573,4015,5044,1120,3402,1623], 'color': DK},
              'line': {'data': igRet, 'color': BLK, 'suf': '%', 'diamond': True, 'below': False, 'scale': .25, 'fs': 11, 'bold': True},
              'fv': 9.5, 'fx': 8.5, 'bw': 34, 'top': 18},
  'gjIgFmt': {'bars': [bar([3,0,5,1,4,5,2,4,7], RED), bar([1,3,1,3,0,1,3,1,1], BLK), bar([2,1,3,2,3,2,2,4,3], DK)], 'fv': 10, 'fx': 8, 'bw': 16, 'top': 18},
  'gjIgEdit': {'labels': ['collab com creator','sazonal (aniversário SL)','ação com o público','cultural/regional'], 'bars': [bar([4,5,1,1])], 'fv': 13, 'fx': 10, 'bw': 50, 'top': 20},
  # ---------- Investimento ----------
  'gjInv': {'labels': ['MAIO|26','JUN|26','JUL|26','AGO|26','SET|26'], 'pre': 'R$ ', 'bars': [bar([5591.12,14366.24,2960.21,3870.94,2977.04])], 'money': True, 'fv': 10, 'fx': 9, 'bw': 44, 'top': 20},
  'gjFoco': {'labels': ['MAIO|26','JUN|26','JUL|26','AGO|26','SET|26'], 'suf': '%', 'bars': [bar([11,27,27,6,37], RED, lc=RED), bar([89,73,73,94,63], DK, lc=DK)], 'fv': 10, 'fx': 9, 'bw': 22, 'top': 18},
  # ---------- Facebook ----------
  'gjFbVis': {'bars': [bar([52688,110995,407495,280709,285039,590171,157308,290369,152185])], 'fv': 9, 'fx': 8.5, 'bw': 30},
  'gjFbSeg': {'bars': [bar([156314,156135,156309,156161,156067,156101,155955,156236,156042])], 'fv': 8, 'fx': 8.5, 'bw': 30},
  'gjFbInt': {'bars': [bar([1341,1189,3027,1257,1212,4604,887,4715,2409])], 'fv': 10, 'fx': 8.5, 'bw': 30},
  'gjFbRet': {'line': {'data': fbRet, 'color': BLK, 'suf': '%', 'fs': 12, 'below': False}, 'fx': 8.5, 'top': 22},
  'gjFbCombo': {'bars': [bar([428,474,1389,1394,1315,2367,763,1724,1135], RED, lc=RED)],
                'line2': {'data': [-108,-179,174,-148,-94,34,-146,281,-194], 'color': DK},
                'line': {'data': fbRet, 'color': BLK, 'suf': '%', 'diamond': True, 'below': False, 'scale': .3, 'fs': 13, 'bold': True},
                'fv': 13, 'fx': 12, 'bw': 56, 'top': 30, 'min': -1500},
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
