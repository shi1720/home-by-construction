import unittest,itertools,sys
from pathlib import Path
from collections import Counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core import anchor,addition_cost,knapsack,country_bounds,abstention_cost

class TestCore(unittest.TestCase):
 def test_ties_and_threshold(self):
  self.assertIsNone(anchor({'A':2,'B':2}))
  self.assertIsNone(anchor({'A':2}))
  self.assertEqual(anchor({'A':2,'B':1,'C':1}),'A')
  self.assertIsNone(anchor({'A':2,'B':1,'C':1},strict=True))
 def test_cost_against_all_completions(self):
  checks=0
  for values in itertools.product(range(4),repeat=3):
   counts=dict(zip('ABC',values))
   for strict in [False,True]:
    for target in 'ABC':
     expected=addition_cost(counts,target,strict=strict)
     # Enumerate every allocation at each lower budget and the first feasible budget.
     found=None
     for budget in range(expected+1):
      for x in range(budget+1):
       for y in range(budget-x+1):
        add=(x,y,budget-x-y)
        v={c:counts[c]+t for c,t in zip('ABC',add)}
        if anchor(v,strict=strict)==target:found=budget;break
       if found is not None:break
      if found is not None:break
     self.assertEqual(found,expected,(counts,target,strict))
     checks+=1
  self.assertEqual(checks,384)
 def test_abstention_exhaustive(self):
  for values in itertools.product(range(4),repeat=3):
   counts=dict(zip('ABC',values))
   for strict in [False,True]:
    if anchor(counts,strict=strict) is None:continue
    expected=abstention_cost(counts,strict=strict);found=None
    for budget in range(expected+1):
     for x in range(budget+1):
      for y in range(budget-x+1):
       v={c:counts[c]+t for c,t in zip('ABC',(x,y,budget-x-y))}
       if anchor(v,strict=strict) is None:found=budget;break
      if found is not None:break
     if found is not None:break
    self.assertEqual(found,expected,(counts,strict))
 def test_contract_semantics(self):
  from audit_contract import report
  z=report({'BE':2,'DE':1,'ES':1},budget=1)
  self.assertEqual(z['documented_anchor'],'BE')
  self.assertEqual(z['minimum_additions_for_abstention'],1)
  self.assertFalse(z['retains_same_resolved_anchor_at_budget'])
  self.assertIsNone(z['biographical_origin_evidence'])
  with self.assertRaises(ValueError):report({'BE':-1})
  with self.assertRaises(ValueError):report({'BE':3},{'value':'BE'})
 def test_knapsack_exhaustive(self):
  rng=np.random.default_rng(55)
  for _ in range(200):
   items=list(zip(rng.integers(1,10,size=8).tolist(),rng.integers(1,20,size=8).tolist()))
   dp=knapsack(items,25)
   brute=np.zeros(26,dtype=int)
   for bits in itertools.product([0,1],repeat=8):
    cost=sum(z*x[0] for z,x in zip(bits,items));val=sum(z*x[1] for z,x in zip(bits,items))
    if cost<=25:brute[cost:]=np.maximum(brute[cost:],val)
   np.testing.assert_array_equal(dp,brute)
 def test_country_bounds_joint_bruteforce(self):
  counts={'a':Counter(BE=4,DE=1),'b':Counter(BE=1,DE=3),'c':Counter(BE=2,NL=1)}
  labs={a:anchor(v) for a,v in counts.items()}
  M,F,lo,hi=country_bounds(counts,labs,'BE',12)
  feasible=[]
  for targets in itertools.product(['BE','DE','NL','OUT'],repeat=3):
   cost=sum(addition_cost(counts[a],t) for a,t in zip(counts,targets))
   foreign=sum(counts[a]['BE']*(t!='BE') for a,t in zip(counts,targets))
   feasible.append((cost,foreign))
  for b in range(13):
   vs=[v for cost,v in feasible if cost<=b]
   self.assertEqual(lo[b],min(vs));self.assertEqual(hi[b],max(vs))
 def test_addition_not_deletion(self):
  c={'BE':3};self.assertEqual(addition_cost(c,'OUT'),4)
  self.assertEqual(addition_cost({'BE':3,'DE':2},'DE'),2)

if __name__=='__main__':unittest.main()
