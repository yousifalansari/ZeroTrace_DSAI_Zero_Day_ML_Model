"""Create print-friendly black-and-white figures from verified PR02 data/results."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"figures/pr02"
OUT.mkdir(parents=True,exist_ok=True)
train=pd.read_csv(ROOT/"data/train.csv")
test=pd.read_csv(ROOT/"data/test.csv")

plt.rcParams.update({"font.family":"serif","font.size":9,"axes.edgecolor":"black",
    "axes.labelcolor":"black","text.color":"black","xtick.color":"black",
    "ytick.color":"black","axes.titlecolor":"black","figure.facecolor":"white",
    "axes.facecolor":"white","savefig.facecolor":"white"})

# Dataset distribution, with train/test differentiated by fill and hatch.
cats=["Normal","Generic","Exploits","Fuzzers","DoS","Reconnaissance","Analysis","Backdoor","Shellcode","Worms"]
fig,axs=plt.subplots(1,2,figsize=(11,4.2))
for ax,cols,title in [(axs[0],["Normal","Attack"],"Binary label"),(axs[1],cats,"Attack category")]:
    x=np.arange(len(cols)); w=.38
    for j,(d,label,fc,hatch) in enumerate([(train,"Train","#555555","//"),(test,"Test","#D9D9D9","\\\\")]):
        vals=[(d.attack_cat.eq(c).mean()*100 if c!="Attack" else d.label.eq(1).mean()*100) for c in cols]
        ax.bar(x+(j-.5)*w,vals,w,label=label,color=fc,edgecolor="black",hatch=hatch,linewidth=.7)
    ax.set_xticks(x,["Attack" if c=="Attack" else c for c in cols],rotation=30 if len(cols)>2 else 0,ha="right" if len(cols)>2 else "center")
    ax.set_ylabel("Percent of partition"); ax.set_title(title); ax.grid(axis="y",color="#D0D0D0",linewidth=.5); ax.set_axisbelow(True)
    ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(OUT/"class_distribution_bw.png",dpi=220,bbox_inches="tight"); plt.close(fig)

# Feature distributions on a log1p visualization scale; no observations are removed.
selected=["dur","sbytes","dbytes","rate","sttl","dttl","sload","smean","ct_srv_src","ct_state_ttl"]
fig,axs=plt.subplots(2,5,figsize=(12,5.2))
for ax,col in zip(axs.flat,selected):
    for d,label,fc in [(train,"Train","#666666"),(test,"Test","#BDBDBD")]:
        for is_attack,ls in [(False,"Normal"),(True,"Attack")]:
            arr=np.log1p(np.clip(d.loc[d.label.eq(int(is_attack)),col].to_numpy(dtype=float),0,None))
            class_color="#BDBDBD" if not is_attack else "#555555"
            ax.hist(arr,bins=35,alpha=.45 if label=="Train" else 1,density=True,
                    color=class_color,edgecolor="black",linewidth=.4,
                    histtype="stepfilled" if label=="Train" else "step",
                    linestyle="solid" if label=="Train" else "dashed")
    ax.set_title(f"log1p({col})",fontsize=8); ax.tick_params(labelsize=7); ax.grid(axis="y",color="#E0E0E0",linewidth=.4)
fig.legend(handles=[Patch(facecolor="#BDBDBD",edgecolor="black",alpha=.65,label="Train normal"),
    Patch(facecolor="#555555",edgecolor="black",alpha=.65,label="Train attack"),
    Line2D([0],[0],color="#777777",linestyle="--",label="Test normal"),
    Line2D([0],[0],color="black",linestyle="--",label="Test attack")],
    loc="upper center",ncol=4,frameon=False,fontsize=8)
fig.tight_layout(rect=(0,0,1,.93))
fig.savefig(OUT/"selected_feature_distributions_bw.png",dpi=220,bbox_inches="tight"); plt.close(fig)

# Primary E1 FPR.
e1=pd.read_csv(ROOT/"results/pr02/E1_overall.csv")
fig,ax=plt.subplots(figsize=(7,4.4)); x=np.arange(len(e1))
bars=ax.bar(x,e1.fpr,color=["#404040","#888888","#C8C8C8"],edgecolor="black",linewidth=.8)
for b,v in zip(bars,e1.fpr): ax.text(b.get_x()+b.get_width()/2,v+.012,f"{v:.3f}",ha="center",fontsize=8)
ax.set_xticks(x,e1.model,rotation=10); ax.set_ylim(0,max(.4,float(e1.fpr.max()+.08))); ax.set_ylabel("False positive rate on normal test traffic")
ax.set_title("E1 reference false positive rate at threshold 0.5"); ax.grid(axis="y",color="#D0D0D0",linewidth=.5); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(OUT/"e1_false_positive_rate.png",dpi=220,bbox_inches="tight"); plt.close(fig)

# E2 category recall with grayscale/hatches and Wilson intervals.
e2=pd.read_csv(ROOT/"results/pr02/E2_loaco.csv")
models=e1.model.tolist(); cats=e2.held_out_category.drop_duplicates().tolist(); x=np.arange(len(cats)); width=.25
fills=["#424242","#8A8A8A","#D0D0D0"]; hatches=["//","xx",".."]
fig,ax=plt.subplots(figsize=(11,4.8))
for j,(model,fc,hatch) in enumerate(zip(models,fills,hatches)):
    d=e2[e2.model.eq(model)].set_index("held_out_category").loc[cats]
    ax.bar(x+(j-1)*width,d.attack_recall,width,label=model,color=fc,edgecolor="black",hatch=hatch,linewidth=.6,
        yerr=[d.attack_recall-d.recall_ci_low,d.recall_ci_high-d.attack_recall],capsize=2,error_kw={"elinewidth":.7,"ecolor":"black"})
ax.set_xticks(x,cats,rotation=25,ha="right"); ax.set_ylim(0,1.08); ax.set_ylabel("Recall on held-out attack category")
ax.set_title("LOACO attack recall at threshold 0.5 with 95% Wilson intervals"); ax.legend(frameon=False,ncol=3,loc="upper center",bbox_to_anchor=(.5,1.16))
ax.grid(axis="y",color="#D0D0D0",linewidth=.5); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(OUT/"loaco_recall_models.png",dpi=220,bbox_inches="tight"); plt.close(fig)

print(f"Saved monochrome PR02 figures in {OUT}")
