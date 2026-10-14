"""Auditable geography anchors and sharp fixed-cohort completion sensitivity."""
from collections import Counter
import numpy as np

COUNTRIES = ('BE','DE','ES','NL','PT','US')

def anchor(counts, minimum=3, strict=False):
    counts = {k:int(v) for k,v in counts.items() if v > 0}
    n = sum(counts.values())
    if n < minimum or not counts:
        return None
    top = max(counts.values())
    winners = [k for k,v in counts.items() if v == top]
    if len(winners) != 1 or (2*top <= n if strict else 2*top < n):
        return None
    return winners[0]

def addition_cost(counts, target, minimum=3, strict=False):
    """Minimum additions to make target the unique qualifying anchor.

    Adding all new markers to target is optimal. Counts can include zeroes.
    """
    n = sum(counts.values())
    t = counts.get(target,0)
    rival = max((v for c,v in counts.items() if c != target), default=0)
    return max(0, minimum-n, n-2*t+(1 if strict else 0), rival-t+1)

def knapsack(items, budget):
    """Exact 0-1 maximum value at each at-most integer budget.

    Each item is (nonnegative integer cost, nonnegative integer value).
    No repeated item use; slice operands are materialized before assignment.
    """
    dp = np.zeros(budget+1,dtype=np.int64)
    for cost,value in items:
        if cost <= 0:
            raise ValueError('positive costs required for change items')
        if cost <= budget and value > 0:
            dp[cost:] = np.maximum(dp[cost:], dp[:-cost] + value)
    return dp

def country_bounds(artist_counts, anchors, country, budget):
    cohort = list(anchors)
    denominator = sum(artist_counts[a].get(country,0) for a in cohort)
    home = sum(artist_counts[a].get(country,0) for a in cohort if anchors[a] == country)
    increase_foreign, decrease_foreign = [], []
    for a in cohort:
        counts = artist_counts[a];value = counts.get(country,0)
        if not value:
            continue
        if anchors[a] == country:
            cost = min(addition_cost(counts,t) for t in (*COUNTRIES,'OUT') if t != country)
            increase_foreign.append((cost,value))
        else:
            decrease_foreign.append((addition_cost(counts,country),value))
    initial = denominator-home
    up = knapsack(increase_foreign,budget)
    down = knapsack(decrease_foreign,budget)
    return denominator, initial, initial-down, initial+up

def abstention_cost(counts, minimum=3, strict=False):
    """Minimum additions that remove a currently resolved anchor.

    Completion space must contain at least three countries. Returns 0 if
    already unresolved. An eligible baseline cannot lose minimum support
    by additions. A tie or loss of majority are the remaining mechanisms.
    """
    h=anchor(counts,minimum,strict)
    if h is None:
        return 0
    n=sum(counts.values());m=counts[h]
    r=max((v for c,v in counts.items() if c!=h),default=0)
    return min(m-r,2*m-n+(0 if strict else 1))
