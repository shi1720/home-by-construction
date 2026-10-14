"""A data-agnostic CLI keeping biography separate from documented geography.

Input: JSON {counts: {country: count}, biography: {value: ..., source: ...}}
Biography is optional; the program never infers it. No source dataset needed.
"""
import argparse,json
from core import anchor,addition_cost,abstention_cost,COUNTRIES

def report(counts,biography=None,budget=0):
    if any(not isinstance(v,int) or isinstance(v,bool) or v<0 for v in counts.values()):
        raise ValueError('Counts must be nonnegative integers')
    if not isinstance(budget,int) or budget<0:raise ValueError('Budget must be a nonnegative integer')
    if biography is not None and (not biography.get('value') or not biography.get('source')):
        raise ValueError('Biographical evidence requires a value and source')
    h=anchor(counts)
    targets=set(COUNTRIES)|set(counts)|{'OUT'}
    switch=min(addition_cost(counts,t) for t in targets if t!=h) if h else None
    unresolved=abstention_cost(counts) if h else 0
    return {'biographical_origin_evidence':biography,'documented_anchor':h,
      'label_semantics':'dominant documented country; not biographical origin',
      'support_countries':sorted(c for c,v in counts.items() if v),
      'documented_records':sum(counts.values()),
      'rule':{'minimum_records':3,'majority':'at_least_half','ties':'abstain'},
      'completion_model':'additional records in any country, at least three possible countries',
      'minimum_additions_for_resolved_switch':switch,
      'minimum_additions_for_abstention':unresolved,
      'retains_same_resolved_anchor_at_budget': bool(h is not None and budget<min(switch,unresolved)),
      'addition_budget':budget}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--budget',type=int,default=0);args=p.parse_args()
    with open(args.input) as f:d=json.load(f)
    print(json.dumps(report(d['counts'],d.get('biography'),args.budget),indent=2))
