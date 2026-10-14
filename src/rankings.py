"""Joint completion witnesses for destination order reversals."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json
import pandas as pd,numpy as np
from core import anchor,addition_cost,COUNTRIES
ROOT=Path(__file__).resolve().parents[1];DATA=Path(sys.argv[1])
d=pd.concat([pd.read_csv(DATA/f'{c}_2026-10.csv',keep_default_na=False) for c in COUNTRIES])
d=d[(d.artists_count==1)&(d.artist1_url!='')]
counts=defaultdict(Counter)
for a,c in zip(d.artist1_url,d.country):counts[a][c]+=1
lab={a:h for a,v in counts.items() if (h:=anchor(v)) is not None}
M={c:sum(counts[a][c] for a in lab) for c in COUNTRIES}
F={c:sum(counts[a][c] for a in lab if lab[a]!=c) for c in COUNTRIES}
N=sum(M.values());B=int(.05*N)
rows=[]
for high,low in __import__('itertools').combinations(sorted(COUNTRIES,key=lambda c:F[c]/M[c],reverse=True),2):
    initial=F[low]*M[high]-F[high]*M[low]
    dp=np.zeros(B+1,dtype=np.int64)
    for a,h in lab.items():
        v=counts[a];base=-v[low]*M[high]*(h==low)+v[high]*M[low]*(h==high)
        options={}
        for target in (*COUNTRIES,'OUT'):
            gain=-v[low]*M[high]*(target==low)+v[high]*M[low]*(target==high)-base
            cost=addition_cost(v,target)
            if gain>0 and cost<=B:
                options[cost]=max(options.get(cost,0),gain)
        old=dp.copy()
        for cost,gain in options.items():
            dp[cost:]=np.maximum(dp[cost:],old[:-cost]+gain)
    possible=np.flatnonzero(dp+initial>0)
    minimum=int(possible[0]) if len(possible) else None
    rows.append({'higher_baseline':high,'lower_baseline':low,'baseline_gap_pp':100*(F[high]/M[high]-F[low]/M[low]),'minimum_joint_additions_for_strict_reversal':minimum,'searched_budget':B})
pd.DataFrame(rows).to_csv(ROOT/'results/rank_reversal.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
