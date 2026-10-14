from pathlib import Path
import pandas as pd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'axes.titleweight':'bold','savefig.bbox':'tight'})
blue='#235789';gold='#E3A126';red='#B64C46';gray='#76818C';light='#EEF3F7'
def save(fig,name):
 fig.savefig(OUT/f'{name}.pdf');fig.savefig(OUT/f'{name}.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(9,3.2));ax.set_xlim(0,10);ax.set_ylim(0,3);ax.axis('off')
boxes=[(.1,1.65,1.8,.85,'Artist practice\nand biography'),(2.55,1.65,1.8,.85,'Collector and\ncountry support'),(5,1.65,1.8,.85,'Documented\ncountry counts'),(7.55,1.65,2.1,.85,'Inferred anchor\n(unique ≥ 50%)'),(5,.15,1.8,.85,'Same documented\nworks evaluated'),(7.55,.15,2.1,.85,'Out-of-anchor\nshare and ranking')]
for x,y,w,h,t in boxes:
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.06',facecolor=light,edgecolor=blue));ax.text(x+w/2,y+h/2,t,ha='center',va='center')
for s,e in [((1.95,2.075),(2.45,2.075)),((4.4,2.075),(4.9,2.075)),((6.85,2.075),(7.45,2.075)),((5.9,1.55),(5.9,1.1)),((6.85,.575),(7.45,.575)),((8.6,1.55),(8.6,1.1))]:
 ax.add_patch(FancyArrowPatch(s,e,arrowstyle='-|>',mutation_scale=12,color=blue))
ax.text(2.2,.5,'A changed label can recode\nunchanged works.',ha='center',color=red,fontweight='bold')
save(fig,'measurement_pipeline')
# Geographic support full-cohort composition across all subsets.
s=pd.read_csv(ROOT/'results/support.csv');fig,ax=plt.subplots(figsize=(8.3,3.6))
for col,color,label in [('same',blue,'Same anchor'),('changed',red,'Reassigned anchor'),('abstained_present',gold,'Present, abstained'),('absent',gray,'Absent')]:
 vals=[s.loc[s['size']==k,col].mean()/3051*100 for k in range(1,7)]
 if col=='same':bottom=np.zeros(6)
 ax.bar(range(1,7),vals,bottom=bottom,color=color,label=label,width=.65);bottom+=np.array(vals)
ax.set(xlabel='Number of countries retained (all subsets)',ylabel='Mean share of 3,051 baseline artists (%)',ylim=(0,100));ax.legend(ncol=2,frameon=False,loc='upper left',bbox_to_anchor=(0,1.28));ax.grid(axis='y',alpha=.15);save(fig,'country_support')
# Completion sensitivity on immutable country cohorts.
b=pd.read_csv(ROOT/'results/completion_curve.csv');denoms=pd.read_csv(ROOT/'results/countries.csv').set_index('country').cohort.to_dict();fig,axes=plt.subplots(2,3,figsize=(9,5.2),sharex=True,sharey=True)
for ax,c in zip(axes.flat,['BE','DE','ES','NL','PT','US']):
 z=b[(b.country==c)&(b.fraction<=.1)]
 ax.fill_between(100*z.fraction,100*z.lower_share,100*z.upper_share,alpha=.16,color=blue)
 ax.plot(100*z.fraction,100*z.upper_share,color=blue,lw=1.2);ax.plot(100*z.fraction,100*z.lower_share,color=blue,lw=1.2)
 ax.axhline(100*z.baseline_share.iloc[0],color=red,linestyle='--',lw=1.2)
 ax.set_title(f'{c}  (n = {int(denoms[c]):,})',fontsize=10);ax.set_ylim(0,102);ax.grid(alpha=.12)
 for v in [1,5,10]:ax.set_xticks([0,1,5,10])
fig.supxlabel('Total additional documentation / 30,696 fixed-cohort works (%)',fontsize=10)
fig.supylabel('Out-of-anchor share in original country cohort (%)',fontsize=10)
fig.text(.5,1.01,'Blue: exact completion envelope    Red: observed panel estimate',ha='center',fontsize=10);fig.tight_layout();save(fig,'completion_envelopes')
# Shared completions, exact minimum for each pair.
r=pd.read_csv(ROOT/'results/rank_reversal.csv');order=['NL','PT','BE','DE','US','ES'];matrix=np.full((6,6),np.nan)
for row in r.itertuples():matrix[order.index(row.higher_baseline),order.index(row.lower_baseline)]=row.minimum_joint_additions_for_strict_reversal
fig,ax=plt.subplots(figsize=(6.5,4.3));im=ax.imshow(np.ma.masked_invalid(matrix),cmap='Blues',vmin=0,vmax=400)
for i in range(6):
 for j in range(6):
  if np.isfinite(matrix[i,j]):ax.text(j,i,str(int(matrix[i,j])),ha='center',va='center',color='white' if matrix[i,j]>240 else '#16283A',fontsize=11)
ax.set_xticks(range(6),order);ax.set_yticks(range(6),order);ax.set_xlabel('Lower baseline destination');ax.set_ylabel('Higher baseline destination');ax.spines[['left','bottom']].set_visible(False)
fig.colorbar(im,ax=ax,label='Minimum jointly allocated additions',fraction=.045,pad=.04);save(fig,'rank_reversal')
# Collector flip comparison: uncertainty is Monte Carlo, not population confidence.
x=pd.read_csv(ROOT/'results/collector_artists_anonymous.csv');rand=pd.read_csv(ROOT/'results/random_deletion.csv')
fig,axes=plt.subplots(1,2,figsize=(8,3.6))
vals=[int((x.largest_state==1).sum()),rand.changed.mean()];q=rand.changed.quantile([.025,.975]).to_numpy()
axes[0].bar([0,1],vals,color=[blue,gold],width=.55);axes[0].errorbar(1,vals[1],yerr=[[vals[1]-q[0]],[q[1]-vals[1]]],color='#222',capsize=4,fmt='none')
axes[0].set_xticks([0,1],['Largest collector\ndeleted','Equal-size random\nmarker deletion']);axes[0].set_ylabel('Artists reassigned to another anchor');axes[0].set_ylim(0,44)
for i,v in enumerate(vals):axes[0].text(i,v+1,f'{v:.1f}' if i else str(v),ha='center')
counts=[int(x.stable_all.sum()),int(x.any_flip.sum()),int(x.any_abstain.sum())]
axes[1].barh([0,1,2],counts,color=[blue,red,gold]);axes[1].set_yticks([0,1,2],['Stable for every\ncollector deletion','At least one\nreassignment','At least one\nabstention']);axes[1].set_xlabel('Artists (categories can overlap)');axes[1].set_xlim(0,2300)
for i,v in enumerate(counts):axes[1].text(v+30,i,str(v),va='center')
fig.tight_layout(w_pad=3);save(fig,'collector_influence')
