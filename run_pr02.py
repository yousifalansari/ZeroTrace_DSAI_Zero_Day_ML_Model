"""Reproducible PR02 experiments for the UNSW-NB15 category-holdout study.

Writes new artifacts under results/pr02 and figures/pr02; existing artifacts are
left untouched. Run with: python run_pr02.py --data-dir data
"""
from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
import json
import os
import platform
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix,
    f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.stats import norm
import sklearn

SEED = 42
CATEG = ["proto", "service", "state"]
TARGET, CATEGORY, ID = "label", "attack_cat", "id"
EXPECTED = {
    "Normal": (56000, 37000), "Generic": (40000, 18871), "Exploits": (33393, 11132),
    "Fuzzers": (18184, 6062), "DoS": (12264, 4089), "Reconnaissance": (10491, 3496),
    "Analysis": (2000, 677), "Backdoor": (1746, 583), "Shellcode": (1133, 378), "Worms": (130, 44),
}

class FlowFeatures(BaseEstimator, TransformerMixin):
    """Feature creation plus fold-local feature selection/transform choices."""
    def __init__(self, categorical=CATEG, corr_threshold=0.95, min_frequency=100):
        self.categorical = categorical
        self.corr_threshold = corr_threshold
        self.min_frequency = min_frequency

    def _engineer(self, X):
        x = X.drop(columns=[c for c in [ID, CATEGORY, TARGET] if c in X.columns]).copy()
        x["byte_ratio"] = np.log1p(x.sbytes) - np.log1p(x.dbytes)
        x["pkt_ratio"] = np.log1p(x.spkts) - np.log1p(x.dpkts)
        x["bytes_per_pkt"] = (x.sbytes + x.dbytes) / (x.spkts + x.dpkts).clip(lower=1)
        x["no_response"] = (x.dpkts == 0).astype("int8")
        return x

    def fit(self, X, y=None):
        x = self._engineer(X)
        numeric = [c for c in x.columns if c not in self.categorical]
        numeric = [c for c in numeric if c != "is_ftp_login"]
        # Greedy correlation pruning is learned only from the current training fold.
        corr = x[numeric].corr().abs().fillna(0)
        keep = []
        for col in numeric:
            if all(corr.loc[col, prior] <= self.corr_threshold for prior in keep):
                keep.append(col)
        self.numeric_ = keep
        self.log_ = [c for c in keep if x[c].min() >= 0 and x[c].skew() > 1]
        self.linear_ = [c for c in keep if c not in self.log_]
        self.cat_ = list(self.categorical)
        self.num_pipe_ = ColumnTransformer([
            ("log", Pipeline([("log1p", Log1p()), ("scale", StandardScaler())]), self.log_),
            ("linear", StandardScaler(), self.linear_),
            ("cat", OneHotEncoder(min_frequency=self.min_frequency,
                handle_unknown="infrequent_if_exist", sparse_output=False), self.cat_),
        ], verbose_feature_names_out=True)
        self.num_pipe_.fit(x, y)
        return self

    def transform(self, X):
        return self.num_pipe_.transform(self._engineer(X))

    def get_feature_names_out(self, input_features=None):
        return self.num_pipe_.get_feature_names_out()

class Log1p(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X): return np.log1p(np.clip(np.asarray(X, dtype=float), 0, None))

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1<<20),b""): h.update(block)
    return h.hexdigest()

def load_data(data_dir):
    train_p, test_p = data_dir/"train.csv", data_dir/"test.csv"
    if not train_p.exists() or not test_p.exists():
        raise FileNotFoundError(f"Expected {train_p} and {test_p}. See README.md.")
    train=pd.read_csv(train_p); test=pd.read_csv(test_p)
    assert train.shape==(175341,45) and test.shape==(82332,45), (train.shape,test.shape)
    for c in (TARGET,CATEGORY): assert c in train and c in test
    for d in (train,test):
        assert ((d[CATEGORY]=="Normal")== (d[TARGET]==0)).all(), "Label/category mismatch"
    for c,(ntr,nte) in EXPECTED.items():
        assert (train[CATEGORY]==c).sum()==ntr and (test[CATEGORY]==c).sum()==nte, c
    return train,test,{"train_sha256":digest(train_p),"test_sha256":digest(test_p),
                      "train_shape":list(train.shape),"test_shape":list(test.shape)}

def clean_train(d):
    # IDs are record identifiers, not flow features; ignore them for duplicates.
    feature_cols=[c for c in d.columns if c not in [ID,CATEGORY,TARGET]]
    de=d.drop_duplicates(feature_cols+[CATEGORY,TARGET]).copy()
    conflict=de.groupby(feature_cols,dropna=False)[TARGET].transform("nunique")>1
    conflict_rows=int(conflict.sum())
    de=de.loc[~conflict].reset_index(drop=True)
    return de, {"input_rows":len(d),"after_exact_duplicate_removal":len(d.drop_duplicates(feature_cols+[CATEGORY,TARGET])),
                "conflicting_label_rows_removed":conflict_rows,"final_rows":len(de)}

def build_model(name, seed):
    if name=="Logistic Regression":
        clf=LogisticRegression(class_weight="balanced",max_iter=3000,random_state=seed)
        grid={"clf__C":[0.1,1,10]}
    elif name=="Random Forest":
        clf=RandomForestClassifier(n_estimators=100,class_weight="balanced_subsample",n_jobs=-1,random_state=seed)
        grid={"clf__max_depth":[None,18]}
    else:
        try: from xgboost import XGBClassifier
        except ImportError as e: raise RuntimeError("XGBoost is required by requirements.txt") from e
        clf=XGBClassifier(n_estimators=150,max_depth=6,learning_rate=.08,subsample=.9,
            colsample_bytree=.9,reg_lambda=1,objective="binary:logistic",eval_metric="logloss",
            n_jobs=-1,random_state=seed,tree_method="hist")
        grid={"clf__max_depth":[4,6]}
    pipe=Pipeline([("prep",FlowFeatures()),("clf",clf)])
    return pipe,grid

def get_metrics(y,prob):
    pred=(np.asarray(prob)>=.5).astype(int)
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return {"n":int(len(y)),"accuracy":accuracy_score(y,pred),"precision":precision_score(y,pred,zero_division=0),
      "recall":recall_score(y,pred,zero_division=0),"f1":f1_score(y,pred,zero_division=0),"fpr":fp/(fp+tn),
      "roc_auc":roc_auc_score(y,prob),"average_precision":average_precision_score(y,prob),
      "tn":int(tn),"fp":int(fp),"fn":int(fn),"tp":int(tp)}

def wilson(k,n):
    if n==0:return (np.nan,np.nan)
    z=norm.ppf(.975); p=k/n; den=1+z*z/n
    center=(p+z*z/(2*n))/den; half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return center-half,center+half

def fit_eval(name,train,test,seed):
    pipe,grid=build_model(name,seed)
    if name=="XGBoost":
        positives=int((train[TARGET]==1).sum()); negatives=int((train[TARGET]==0).sum())
        pipe.set_params(clf__scale_pos_weight=negatives/max(positives,1))
    # Fold-local pipeline includes feature engineering, feature selection, encoding, and scaling.
    cv=StratifiedKFold(3,shuffle=True,random_state=seed)
    search=GridSearchCV(pipe,grid,scoring="f1",cv=cv,n_jobs=1,refit=True,error_score="raise")
    t=time.perf_counter(); search.fit(train,train[TARGET]); tune_fit_s=time.perf_counter()-t
    best=search.best_estimator_
    t=time.perf_counter(); prob=best.predict_proba(test)[:,1]; predict_s=time.perf_counter()-t
    m=get_metrics(test[TARGET],prob)
    m.update({"model":name,"best_params":json.dumps(search.best_params_,sort_keys=True),
              "cv_best_f1":search.best_score_,"fit_and_cv_seconds":tune_fit_s,"prediction_seconds":predict_s,
              "threshold":0.5})
    return best,prob,m

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",type=Path,default=Path("data")); ap.add_argument("--seed",type=int,default=SEED)
    ap.add_argument("--include-xgboost",action="store_true",help="Run XGBoost when its native OpenMP runtime is available")
    ap.add_argument("--repeat-seeds",action="store_true",help="Repeat E1/E2 runs with seeds 7 and 21")
    args=ap.parse_args(); warnings.filterwarnings("default")
    out=Path("results/pr02"); figs=Path("figures/pr02"); out.mkdir(parents=True,exist_ok=True); figs.mkdir(parents=True,exist_ok=True)
    tr_raw,te,manifest=load_data(args.data_dir)
    tr,cleaning=clean_train(tr_raw); manifest.update(cleaning)
    models=["Logistic Regression","Random Forest"]
    if args.include_xgboost:
        try:
            from xgboost import XGBClassifier  # noqa: F401
            models.append("XGBoost")
        except Exception as exc:
            print(f"Skipping XGBoost: {exc}",flush=True)
    manifest.update({"seed":args.seed,"repeat_seeds":[7,21] if args.repeat_seeds else [],"cv_folds":3,"models":models,
      "threshold":0.5,"python":platform.python_version(),"pandas":pd.__version__,"numpy":np.__version__,"scikit_learn":sklearn.__version__,
      "xgboost":version("xgboost") if "XGBoost" in models else None})
    (out/"run_manifest.json").write_text(json.dumps(manifest,indent=2))
    feature_cols=[c for c in tr.columns if c not in [ID,CATEGORY,TARGET]]
    # EDA and integrity outputs.
    quality=[]
    for nm,d in [("train",tr_raw),("test",te)]:
        quality.append({"partition":nm,"rows":len(d),"missing_cells":int(d.isna().sum().sum()),
          "exact_duplicate_rows_ignoring_id":int(d.duplicated(feature_cols+[CATEGORY,TARGET]).sum()),
          "label_category_disagreements":int(((d[CATEGORY]=="Normal")!=(d[TARGET]==0)).sum())})
    pd.DataFrame(quality).to_csv(out/"data_quality.csv",index=False)
    numeric_cols=[c for c in feature_cols if c not in CATEG]
    numeric_summary=tr_raw[numeric_cols].describe().T
    numeric_summary["skew"]=tr_raw[numeric_cols].skew()
    numeric_summary.to_csv(out/"numeric_summary.csv")
    q1,q3=tr_raw[numeric_cols].quantile(.25),tr_raw[numeric_cols].quantile(.75)
    iqr=q3-q1
    outliers=((tr_raw[numeric_cols] < q1-1.5*iqr) | (tr_raw[numeric_cols] > q3+1.5*iqr)).mean()*100
    pd.DataFrame({"iqr_outlier_percent":outliers,"skew":tr_raw[numeric_cols].skew(),
      "max_over_p99":tr_raw[numeric_cols].max()/tr_raw[numeric_cols].quantile(.99).replace(0,np.nan)}).to_csv(out/"outlier_summary.csv")
    train_features=pd.util.hash_pandas_object(tr_raw[feature_cols].astype(str),index=False).to_numpy()
    test_features=pd.util.hash_pandas_object(te[feature_cols].astype(str),index=False).to_numpy()
    train_feature_set=set(train_features.tolist())
    overlap=np.isin(test_features,list(train_feature_set))
    overlap_by=te.assign(feature_seen_in_train=overlap).groupby(CATEGORY).feature_seen_in_train.agg(["sum","count","mean"])
    overlap_by.to_csv(out/"feature_overlap_by_category.csv")
    # E1 reference and E2 LOACO. All preprocessing and selection are re-fit per run.
    e1=[]; e2=[]; category_rows=[]; missed_records=[]
    cats=[c for c in EXPECTED if c!="Normal"]
    for model in models:
        print(f"Fitting {model} E1",flush=True)
        fitted,prob,met=fit_eval(model,tr,te,args.seed); met["experiment"]="E1 reference"; e1.append(met)
        pd.DataFrame(e1).to_csv(out/"E1_overall_checkpoint.csv",index=False)
        for cat in cats:
            print(f"Fitting {model} LOACO {cat}",flush=True)
            trc=tr.loc[tr[CATEGORY]!=cat]
            subset=te.loc[te[CATEGORY].isin(["Normal",cat])].copy()
            f,p,m=fit_eval(model,trc,subset,args.seed)
            cmask=(subset[CATEGORY]==cat).to_numpy(); n=int(cmask.sum()); k=int((p[cmask]>=.5).sum())
            lo,hi=wilson(k,n)
            trc_features=set(pd.util.hash_pandas_object(trc[feature_cols].astype(str),index=False).to_numpy().tolist())
            heldout_features=pd.util.hash_pandas_object(subset.loc[cmask,feature_cols].astype(str),index=False).to_numpy()
            overlap_cat=np.isin(heldout_features,list(trc_features))
            feature_unseen=~overlap_cat
            unseen_n=int(feature_unseen.sum())
            unseen_k=int(((p[cmask]>=.5)&feature_unseen).sum())
            unseen_lo,unseen_hi=wilson(unseen_k,unseen_n)
            e2.append({"model":model,"held_out_category":cat,"test_n":n,"attack_recall":k/n,
              "false_negatives":n-k,"recall_ci_low":lo,"recall_ci_high":hi,"normal_fpr":m["fpr"],"normal_n":int((~cmask).sum()),
              "feature_unseen_n":unseen_n,"feature_unseen_recall":(unseen_k/unseen_n if unseen_n else np.nan),
              "feature_unseen_ci_low":unseen_lo,"feature_unseen_ci_high":unseen_hi,
              "e1_seen_recall":float((prob[te[CATEGORY].eq(cat).to_numpy()]>=.5).mean()),
              "recall_gap":float((prob[te[CATEGORY].eq(cat).to_numpy()]>=.5).mean()-k/n),
              "heldout_feature_vectors_seen_in_remaining_train":float(overlap_cat.mean()),
              "cv_best_f1":m["cv_best_f1"],"best_params":m["best_params"],
              "fit_and_cv_seconds":m["fit_and_cv_seconds"],"prediction_seconds":m["prediction_seconds"]})
            for ridx in subset.index[cmask & (p < .5)]:
                miss=subset.loc[ridx].to_dict()
                miss.update({"model":model,"held_out_category":cat,"predicted_attack_probability":float(p[subset.index.get_loc(ridx)]),
                  "feature_vector_seen_in_remaining_train":bool(overlap_cat[np.flatnonzero(subset.index[cmask]==ridx)[0]])})
                missed_records.append(miss)
            pd.DataFrame(e2).to_csv(out/"E2_loaco_checkpoint.csv",index=False)
        pd.DataFrame(category_rows).to_csv(out/"E1_by_category_checkpoint.csv",index=False)
        # Per-category E1 metrics for attack recall / normal false alarms.
        for cat in EXPECTED:
            mask=te[CATEGORY].eq(cat).to_numpy(); n=int(mask.sum()); k=int((prob[mask]>=.5).sum()); lo,hi=wilson(k,n)
            category_rows.append({"model":model,"category":cat,"n":n,"metric":"FPR" if cat=="Normal" else "attack_recall",
                "value":k/n,"ci_low":lo,"ci_high":hi})
    pd.DataFrame(e1).to_csv(out/"E1_overall.csv",index=False)
    pd.DataFrame(e2).to_csv(out/"E2_loaco.csv",index=False)
    pd.DataFrame(missed_records).to_csv(out/"E2_missed_attack_records.csv",index=False)
    pd.DataFrame(category_rows).to_csv(out/"E1_by_category.csv",index=False)
    if args.repeat_seeds:
        seed_rows=[]
        for repeat_seed in [7,21]:
            for model in models:
                print(f"Repeat seed {repeat_seed}: {model} E1",flush=True)
                _,repeat_prob,repeat_met=fit_eval(model,tr,te,repeat_seed)
                seed_rows.append({"seed":repeat_seed,"model":model,"experiment":"E1","category":"All",
                    "recall":repeat_met["recall"],"fpr":repeat_met["fpr"],"f1":repeat_met["f1"],
                    "roc_auc":repeat_met["roc_auc"],"n":repeat_met["n"]})
                for cat in cats:
                    print(f"Repeat seed {repeat_seed}: {model} LOACO {cat}",flush=True)
                    trc=tr.loc[tr[CATEGORY]!=cat]
                    sub=te.loc[te[CATEGORY].isin(["Normal",cat])]
                    _,rp,rm=fit_eval(model,trc,sub,repeat_seed)
                    cmask=(sub[CATEGORY]==cat).to_numpy(); n=int(cmask.sum()); k=int((rp[cmask]>=.5).sum())
                    seed_rows.append({"seed":repeat_seed,"model":model,"experiment":"E2","category":cat,
                        "recall":k/n,"fpr":rm["fpr"],"f1":rm["f1"],"roc_auc":rm["roc_auc"],"n":n})
                    pd.DataFrame(seed_rows).to_csv(out/"seed_sensitivity_checkpoint.csv",index=False)
        base_e1=pd.DataFrame(e1)
        for _,r in base_e1.iterrows():
            seed_rows.append({"seed":args.seed,"model":r.model,"experiment":"E1","category":"All",
                "recall":r.recall,"fpr":r.fpr,"f1":r.f1,"roc_auc":r.roc_auc,"n":r.n})
        for _,r in pd.DataFrame(e2).iterrows():
            seed_rows.append({"seed":args.seed,"model":r.model,"experiment":"E2","category":r.held_out_category,
                "recall":r.attack_recall,"fpr":r.normal_fpr,"f1":np.nan,"roc_auc":np.nan,"n":r.test_n})
        pd.DataFrame(seed_rows).sort_values(["experiment","model","category","seed"]).to_csv(out/"seed_sensitivity.csv",index=False)
    # Clear visual evidence from the actual three-model runs.
    e2df=pd.DataFrame(e2)
    fig,ax=plt.subplots(figsize=(12,5)); cats_order=cats; x=np.arange(len(cats)); width=.25
    for j,model in enumerate(models):
        d=e2df[e2df.model==model].set_index("held_out_category").loc[cats_order]
        ax.bar(x+(j-1)*width,d.attack_recall,width,label=model,yerr=[d.attack_recall-d.recall_ci_low,d.recall_ci_high-d.attack_recall],capsize=2)
    ax.set_xticks(x,cats_order,rotation=25,ha="right"); ax.set_ylim(0,1.05); ax.set_ylabel("Recall on held-out attack category")
    ax.set_title("LOACO attack recall at threshold 0.5 with 95% Wilson intervals"); ax.legend(); fig.tight_layout(); fig.savefig(figs/"loaco_recall_models.png",dpi=200); plt.close(fig)
    e1df=pd.DataFrame(e1)
    fig,ax=plt.subplots(figsize=(8,5)); ax.bar(e1df.model,e1df.fpr,color="#c87536"); ax.set_ylim(0,1); ax.set_ylabel("False positive rate on normal test traffic")
    ax.set_title("E1 reference false positive rate at threshold 0.5"); ax.tick_params(axis="x",rotation=15); fig.tight_layout(); fig.savefig(figs/"e1_false_positive_rate.png",dpi=200); plt.close(fig)
    print("Outputs:",out,"and",figs)
    print(pd.DataFrame(e1)[["model","accuracy","precision","recall","f1","fpr","roc_auc","average_precision","fit_and_cv_seconds","prediction_seconds"]].to_string(index=False))

if __name__=="__main__": main()
