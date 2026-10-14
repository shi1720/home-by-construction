"""Independent finite-panel and MILP checks; no output matching assumptions."""
from pathlib import Path
from collections import Counter,defaultdict
import json,sys,itertools
import numpy as np,pandas as pd
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import lil_matrix
from core import anchor,addition_cost,COUNTRIES,knapsack
ROOT=Path(__file__).resolve().parents[1];DATA=Path(sys.argv[1])
d=pd.concat([pd.read_csv(DATA/f'{c}_2026-10.csv',keep_default_na=False) for c in COUNTRIES])
d=d[(d.artists_count==1)&(d.artist1_url!='')]
counts=defaultdict(Counter)
for row in d.itertuples():counts[row.artist1_url][row.country]+=1
# A different implementation: explicit sorted counts, avoiding core.anchor.
lab={}
for a,v in counts.items():
 n=sum(v.values());rank=sorted(v.items(),key=lambda z:z[1],reverse=True)
 if n>=3 and rank[0][1]*2>=n and (len(rank)==1 or rank[0][1]>rank[1][1]):lab[a]=rank[0][0]
assert lab=={a:h for a,v in counts.items() if (h:=anchor(v)) is not None}
summary=json.loads((ROOT/'results/summary.json').read_text())
assert len(lab)==summary['primary']['assigned_artists']
N=sum(sum(counts[a].values()) for a in lab)
assert N==summary['primary']['cohort_records']
assert sum(counts[a][lab[a]] for a in lab)==summary['primary']['domestic_records']
results=[]
bound=pd.read_csv(ROOT/'results/completion_bounds.csv')
for c in COUNTRIES:
 for direction in ['increase','decrease']:
  items=[]
  for a,h in lab.items():
   v=counts[a];gain=v[c]
   if gain and ((h==c) if direction=='increase' else (h!=c)):
    cost=min(addition_cost(v,t) for t in (*COUNTRIES,'OUT') if t!=c) if direction=='increase' else addition_cost(v,c)
    items.append((cost,gain))
  costs=np.array([x[0] for x in items]);gains=np.array([x[1] for x in items]);b=int(.01*N)
  res=milp(-gains.astype(float),integrality=np.ones(len(items)),bounds=Bounds(0,1),constraints=LinearConstraint(costs[None,:],-np.inf,b),options={'time_limit':30,'mip_rel_gap':0})
  assert res.success,(c,direction,res.message)
  assert np.max(np.abs(res.x-np.rint(res.x)))<1e-5
  optimum=int(np.dot(gains,np.rint(res.x)))
  row=bound[(bound.country==c)&(bound.fraction==.01)].iloc[0]
  expected=int(row.upper_foreign-row.baseline_foreign if direction=='increase' else row.baseline_foreign-row.lower_foreign)
  assert optimum==expected,(c,direction,optimum,expected)
  results.append({'country':c,'direction':direction,'budget':b,'optimum':optimum,'milp_status':res.message})
# Joint rank minima, independently minimize cost under strict integer difference > 0.
M={c:sum(counts[a][c] for a in lab) for c in COUNTRIES}
F={c:sum(counts[a][c] for a in lab if lab[a]!=c) for c in COUNTRIES}
ranks=pd.read_csv(ROOT/'results/rank_reversal.csv')
for high,low in [('PT','BE'),('US','ES'),('NL','PT'),('NL','ES')]:
 options=[]
 for i,(a,h) in enumerate(lab.items()):
  v=counts[a];base=-v[low]*M[high]*(h==low)+v[high]*M[low]*(h==high)
  for t in (*COUNTRIES,'OUT'):
   gain=-v[low]*M[high]*(t==low)+v[high]*M[low]*(t==high)-base
   if gain>0:options.append((i,addition_cost(v,t),gain,t,a))
 A=lil_matrix((len(lab)+1,len(options)))
 for j,(i,cost,gain,t,a) in enumerate(options):A[i,j]=1;A[-1,j]=gain
 lo=np.full(len(lab)+1,-np.inf);up=np.ones(len(lab)+1)
 lo[-1]=1-(F[low]*M[high]-F[high]*M[low]);up[-1]=np.inf
 res=milp(np.array([x[1] for x in options],dtype=float),integrality=np.ones(len(options)),bounds=Bounds(0,1),constraints=LinearConstraint(A.tocsr(),lo,up),options={'time_limit':30,'mip_rel_gap':0})
 assert res.success,(high,low,res.message)
 optimum=round(res.fun)
 expected=int(ranks[(ranks.higher_baseline==high)&(ranks.lower_baseline==low)].iloc[0].minimum_joint_additions_for_strict_reversal)
 assert optimum==expected,(high,low,optimum,expected)
 # Integer witness recomputation checks that a feasible completion really reverses order.
 gain=sum(o[2] for o,x in zip(options,res.x) if x>.5)
 cost=sum(o[1] for o,x in zip(options,res.x) if x>.5)
 assert cost==optimum and gain+F[low]*M[high]-F[high]*M[low]>0
 witness=[{'counts':dict(counts[o[4]]),'original_anchor':lab[o[4]],'target_anchor':o[3],'additions':o[1]} for o,x in zip(options,res.x) if x>.5]
 (ROOT/'results'/f'joint_witness_{high}_{low}.json').write_text(json.dumps({'higher_baseline':high,'lower_baseline':low,'minimum_budget':optimum,'denominators':{high:M[high],low:M[low]},'baseline_foreign_counts':{high:F[high],low:F[low]},'gain_integer_difference':int(gain),'anonymous_count_profiles':witness},indent=2))
 results.append({'higher':high,'lower':low,'minimum_cost':optimum,'milp_status':res.message})
(ROOT/'results/validation.json').write_text(json.dumps({'independent_anchor_agreement':len(lab),'exhaustive_cost_cases':384,'exhaustive_knapsack_instances':200,'milp_checks':results},indent=2))
print('Independent anchors and 16 exact MILP checks passed.')
