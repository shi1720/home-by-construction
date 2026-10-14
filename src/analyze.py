from pathlib import Path
from collections import Counter,defaultdict
import itertools,json,hashlib,sys
import numpy as np
import pandas as pd
from core import anchor,addition_cost,country_bounds,COUNTRIES

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parent/'data'
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)

def load(month,countries):
    frames=[]
    for c in countries:
        x=pd.read_csv(DATA/f'{c}_{month}.csv',keep_default_na=False)
        assert (x.country==c).all()
        x['export_country']=c
        frames.append(x)
    d=pd.concat(frames,ignore_index=True)
    assert not d.id.duplicated().any()
    return d

def single(d):
    return d[(d.artists_count==1)&(d.artist1_url!='')].copy()

def count_map(d,artist='artist1_url'):
    z=defaultdict(Counter)
    for a,c in zip(d[artist],d.country):z[a][c]+=1
    return dict(z)

def labels(counts,minimum=3,strict=False):
    return {a:h for a,v in counts.items() if (h:=anchor(v,minimum,strict)) is not None}

def basic(d,minimum=3,strict=False):
    counts=count_map(d);lab=labels(counts,minimum,strict)
    cohort=d[d.artist1_url.isin(lab)]
    return {'records':len(d),'artists':len(counts),'assigned_artists':len(lab),'cohort_records':len(cohort),'domestic_records':sum(cohort.country==cohort.artist1_url.map(lab)),'multi_country_assigned':sum(len(counts[a])>1 for a in lab)}

raw=load('2026-10',COUNTRIES);d=single(raw);counts=count_map(d);lab=labels(counts)
summary={'raw_records':len(raw),'primary':basic(d),'data_checks':{'duplicate_ids':int(raw.id.duplicated().sum()),'missing_hunter_primary':int((d.hunter_url=='').sum())}}
country=[]
for c in COUNTRIES:
    x=raw[raw.country==c];s=d[d.country==c];co=s[s.artist1_url.isin(lab)]
    hunter=s.hunter_url.value_counts()
    country.append({'country':c,'raw':len(x),'single':len(s),'cohort':len(co),'assigned_artists':co.artist1_url.nunique(),'foreign':int(sum(co.country!=co.artist1_url.map(lab))),'hunter_count':int(s.hunter_url.nunique()),'top_hunter_share':float(hunter.iloc[0]/len(s)),'top5_hunter_share':float(hunter.head(5).sum()/len(s)),'nonempty_nationality':int(sum(s.attribute_artist_nationality!=''))})
pd.DataFrame(country).to_csv(OUT/'countries.csv',index=False)
# Geographic support: include all full-panel artists in every denominator.
support=[]
for r in range(1,7):
    for cc in itertools.combinations(COUNTRIES,r):
        sub={a:Counter({c:v for c,v in counts[a].items() if c in cc}) for a in lab}
        other=labels(sub)
        support.append({'countries':'+'.join(cc),'size':r,'same':sum(other.get(a)==lab[a] for a in lab),'changed':sum(a in other and other[a]!=lab[a] for a in lab),'abstained_present':sum(a not in other and bool(sub[a]) for a in lab),'absent':sum(not sub[a] for a in lab)})
pd.DataFrame(support).to_csv(OUT/'support.csv',index=False)
# Per-artist hunter counterfactuals on original cohort; URLs never exported.
rng=np.random.default_rng(1720406)
collector=[];random_totals=np.zeros((200,3),dtype=int)
for a,x in d[d.artist1_url.isin(lab)].groupby('artist1_url',sort=True):
    by={h:Counter(z.country) for h,z in x.groupby('hunter_url',sort=True) if h!=''}
    outcomes=[]
    for h,rem in by.items():
        left=counts[a]-rem;new=anchor(left)
        outcomes.append(0 if new==lab[a] else 1 if new is not None else 2)
    largest=max(by,key=lambda h:(sum(by[h].values()),h)) if by else None
    k=sum(by[largest].values()) if largest else 0
    remaining=counts[a]-by[largest] if largest else counts[a]
    largest_h=anchor(remaining)
    largest_state=0 if largest_h==lab[a] else 1 if largest_h is not None else 2
    vec=x.country.to_numpy()
    for i in range(200):
        keep=rng.choice(len(vec),len(vec)-k,replace=False)
        new=anchor(Counter(vec[keep]));state=0 if new==lab[a] else 1 if new is not None else 2
        random_totals[i,state]+=1
    collector.append({'n':len(x),'countries':len(counts[a]),'hunters':len(by),'largest_share':k/len(x),'any_flip':int(1 in outcomes),'any_abstain':int(2 in outcomes),'stable_all':int(all(o==0 for o in outcomes)),'largest_state':largest_state,'flip_additions':min(addition_cost(counts[a],c) for c in (*COUNTRIES,'OUT') if c!=lab[a])})
col=pd.DataFrame(collector);col.to_csv(OUT/'collector_artists_anonymous.csv',index=False)
pd.DataFrame(random_totals,columns=['same','changed','abstained']).to_csv(OUT/'random_deletion.csv',index=False)
summary['collector']={'artists':len(col),'any_flip':int(col.any_flip.sum()),'any_abstain':int(col.any_abstain.sum()),'stable_all':int(col.stable_all.sum()),'largest_state':col.largest_state.value_counts().to_dict(),'random_mean':random_totals.mean(axis=0).tolist(),'random_q025':np.quantile(random_totals,.025,axis=0).tolist(),'random_q975':np.quantile(random_totals,.975,axis=0).tolist()}
for name,mask in [('n10',col.n>=10),('multi_hunter_n10',(col.n>=10)&(col.hunters>=2)),('multi_country',col.countries>1)]:
    s=col[mask];summary['collector'][name]={'artists':len(s),'any_flip':int(s.any_flip.sum()),'any_abstain':int(s.any_abstain.sum()),'stable_all':int(s.stable_all.sum()),'largest_state':s.largest_state.value_counts().to_dict()}
# Completion budgets on fixed assigned cohort. Exact globally shared budget per extremum.
N=sum(sum(counts[a].values()) for a in lab);B=int(.5*N)
bounds=[];curves=[]
for c in COUNTRIES:
    denominator,initial,lower,upper=country_bounds(counts,lab,c,B)
    for b in range(int(.1*N)+1):
        curves.append({'country':c,'budget':b,'fraction':b/N,'baseline_share':initial/denominator,'lower_share':float(lower[b]/denominator),'upper_share':float(upper[b]/denominator)})
    for f in [0,.01,.05,.10,.20,.50]:
        b=int(f*N)
        bounds.append({'country':c,'fraction':f,'budget':b,'denominator':denominator,'baseline_foreign':initial,'lower_foreign':int(lower[b]),'upper_foreign':int(upper[b]),'baseline_share':initial/denominator,'lower_share':float(lower[b]/denominator),'upper_share':float(upper[b]/denominator)})
pd.DataFrame(bounds).to_csv(OUT/'completion_bounds.csv',index=False)
pd.DataFrame(curves).to_csv(OUT/'completion_curve.csv',index=False)
# Comparator tags, deliberately conservative explicit aliases.
alias={}
for code,names in {'BE':['Belgium','Belgian'],'DE':['Germany'],'ES':['Spain','Spanish'],'NL':['Dutch','Netherlands','The Netherlands'],'PT':['Portugal','Portuguese'],'US':['USA'],'GB':['United Kingdom (UK)','British'],'BR':['Brasil','Brazil'],'IT':['Italy','Italia'],'CZ':['Czech'],'DK':['Denmark','Danish'],'PL':['Poland','Polish'],'TR':['Turkey','Turkish'],'SR':['Surinam']}.items():
    for n in names:alias[n.casefold()]=code
for n in ['Algeria','Angola','Argentina','Australia','Austria','Canada','Chile','Colombia','Croatia','Denmark','Egypt','Estonia','France','Gambia','Greece','Hong Kong','Ireland','Israel','Japan','Lithuania','Luxembourg','Mexico','Morocco','Nepal','Palestine','Peru','Puerto Rico','Russia','Serbia','Slovakia','South Africa','Switzerland','Syria','Thailand','Tunisia','Ukraine','Uruguay','Venezuela','Bosnia-Herzegovina','Bulgaria','China','Cuba','Dominican Republic','El Salvador','Finland','Georgia','Hungary','India','Indonesia','Iran','Jordan','Malawi','Malaysia','Nicaragua','Romania','Sweden']:
    alias.setdefault(n.casefold(),n)
(ROOT/'nationality_aliases.json').write_text(json.dumps(alias,indent=2,sort_keys=True))
def parse_tag(t):
    if not t:return None
    if t.startswith('['):
        try:v=json.loads(t)
        except ValueError:return None
    else:v=[t]
    if len(v)!=1:return None
    return alias.get(str(v[0]).strip().casefold())

d['tag']=d.attribute_artist_nationality.map(parse_tag)
tags={};conflicts=0;ambiguous_artists=0
for a,x in d.groupby('artist1_url',sort=True):
    ss=set(x.tag.dropna())
    nonempty=x[~x.attribute_artist_nationality.isin(['','[]'])]
    ambiguous=nonempty.tag.isna().any()
    if ambiguous:ambiguous_artists+=1
    if len(ss)==1 and not ambiguous:tags[a]=next(iter(ss))
    elif len(ss)>1:conflicts+=1
comp=[a for a in lab if a in tags]
summary['nationality']={'tagged_records':int(d.tag.notna().sum()),'nonempty_records':int(sum(d.attribute_artist_nationality!='')),'consistent_artists':len(tags),'conflicting_artists':conflicts,'ambiguous_artists':ambiguous_artists,'assigned_comparable_artists':len(comp),'mismatching_artists':sum(tags[a]!=lab[a] for a in comp),'mismatches_outside_panel':sum(tags[a]!=lab[a] and tags[a] not in COUNTRIES for a in comp),'comparable_records':sum(sum(counts[a].values()) for a in comp),'foreign_anchor_records':sum(sum(v for c,v in counts[a].items() if c!=lab[a]) for a in comp),'foreign_tag_records':sum(sum(v for c,v in counts[a].items() if c!=tags[a]) for a in comp)}
# Same-tag evidence restricted to tagged records (no propagation).
tagged=d[d.tag.notna()&d.artist1_url.isin(lab)].copy()
summary['nationality']['same_record_comparison']={'records':len(tagged),'foreign_anchor':int(sum(tagged.country!=tagged.artist1_url.map(lab))),'foreign_tag':int(sum(tagged.country!=tagged.tag))}
# Longitudinal four-country snapshots; freeze old cohort and evaluate label updates.
cc=('BE','ES','NL','PT');oldraw=load('2026-09',cc);newraw=load('2026-10',cc);old=single(oldraw);new=single(newraw)
oc=count_map(old);nc=count_map(new);ol=labels(oc);nl=labels(nc)
common=old.set_index('id').index.intersection(new.set_index('id').index)
o=old.set_index('id').loc[common];ne=new.set_index('id').loc[common]
unchanged=(o.artist1_url==ne.artist1_url)&(o.country==ne.country)
frozen=o[unchanged&o.artist1_url.isin(ol)]
newlabel=frozen.artist1_url.map(nl)
changed=(newlabel.notna())&(newlabel!=frozen.artist1_url.map(ol))
flips=(frozen.country!=frozen.artist1_url.map(ol))!=(frozen.country!=newlabel)
add=new[~new.id.isin(oldraw.id)]
created=pd.to_datetime(add.attribute_date_created,errors='coerce',utc=True,format='mixed')
summary['temporal']={'old_raw':len(oldraw),'new_raw':len(newraw),'new_marker_ids':len(newraw[~newraw.id.isin(oldraw.id)]),'removed_marker_ids':len(oldraw[~oldraw.id.isin(newraw.id)]),'old_assigned_artists':len(ol),'label_changes':sum(a in nl and nl[a]!=ol[a] for a in ol),'label_abstentions':sum(a not in nl for a in ol),'unchanged_cohort_records':len(frozen),'records_changed_anchor':int(changed.sum()),'records_changed_domestic_status_resolved':int((flips&newlabel.notna()).sum()),'records_unresolved':int(newlabel.isna().sum()),'new_single_markers':len(add),'new_single_with_valid_creation_date':int(created.notna().sum()),'new_single_created_before_september':int((created<pd.Timestamp('2026-09-01',tz='UTC')).sum())}
summary['sensitivities']={'active':basic(d[d.status=='active']),'strict_majority':basic(d,strict=True),'minimum10':basic(d,minimum=10)}
# Collaboration extension: URL availability, one count per marker-artist pair.
edges=[];truncated=0
for _,row in raw.iterrows():
    if int(row.artists_count)>4:truncated+=1
    aa=set(str(row.get(f'artist{i}_url','')) for i in range(1,5))-{''}
    for a in aa:edges.append((row.id,a,row.country,row.hunter_url))
e=pd.DataFrame(edges,columns=['id','artist1_url','country','hunter_url'])
summary['sensitivities']['all_artist_links']=basic(e)
summary['sensitivities']['collaborative_markers_over_four']=truncated
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
