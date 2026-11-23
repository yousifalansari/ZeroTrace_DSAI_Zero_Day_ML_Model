"""Build the editable Progress Report 02 from verified results/pr02 tables."""
from pathlib import Path
import json
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parent
R=ROOT/"results/pr02"
F=ROOT/"figures/pr02"
OUT=ROOT/"Progress_Report_02.docx"
e1=pd.read_csv(R/"E1_overall.csv")
e2=pd.read_csv(R/"E2_loaco.csv")
cats=pd.read_csv(R/"E1_by_category.csv")
q=pd.read_csv(R/"data_quality.csv")
overlap=pd.read_csv(R/"feature_overlap_by_category.csv",index_col=0)
manifest=json.loads((R/"run_manifest.json").read_text())
numeric_summary=pd.read_csv(R/"numeric_summary.csv",index_col=0)
outlier_summary=pd.read_csv(R/"outlier_summary.csv",index_col=0)
seed=pd.read_csv(R/"seed_sensitivity.csv")
misses=pd.read_csv(R/"E2_missed_attack_records.csv")
models=e1.model.tolist()
EXPECTED={"Normal":(56000,37000),"Generic":(40000,18871),"Exploits":(33393,11132),"Fuzzers":(18184,6062),
"DoS":(12264,4089),"Reconnaissance":(10491,3496),"Analysis":(2000,677),"Backdoor":(1746,583),"Shellcode":(1133,378),"Worms":(130,44)}

doc=Document()
sec=doc.sections[0]
sec.page_width=Inches(8.27); sec.page_height=Inches(11.69)
sec.top_margin=Inches(.72); sec.bottom_margin=Inches(.68); sec.left_margin=Inches(.78); sec.right_margin=Inches(.78)
styles=doc.styles
styles['Normal'].font.name='Times New Roman'; styles['Normal'].font.size=Pt(10); styles['Normal'].font.color.rgb=RGBColor(0,0,0)
styles['Normal'].paragraph_format.space_after=Pt(5)
for name,size in [('Title',24),('Heading 1',16),('Heading 2',12),('Heading 3',10)]:
    st=styles[name]; st.font.name='Times New Roman'; st.font.size=Pt(size); st.font.bold=True; st.font.color.rgb=RGBColor(0,0,0)
    st.paragraph_format.space_before=Pt(10 if name!='Title' else 0); st.paragraph_format.space_after=Pt(5)
    if name.startswith('Heading'): st.paragraph_format.keep_with_next=True

def shade(cell,fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),fill); tcPr.append(shd)
def set_repeat_table_header(row):
    trPr=row._tr.get_or_add_trPr(); rep=OxmlElement('w:tblHeader'); rep.set(qn('w:val'),'true'); trPr.append(rep)
def keep_table_row_together(row):
    trPr=row._tr.get_or_add_trPr(); el=OxmlElement('w:cantSplit'); trPr.append(el)
def table(headers,rows,widths=None,font=8):
    t=doc.add_table(rows=1,cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style='Table Grid'
    set_repeat_table_header(t.rows[0])
    keep_table_row_together(t.rows[0])
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=str(h); shade(c,'000000')
        for p in c.paragraphs:
            for r in p.runs: r.font.bold=True; r.font.color.rgb=RGBColor(255,255,255); r.font.size=Pt(font)
    for ridx,row in enumerate(rows):
        cells=t.add_row().cells
        keep_table_row_together(t.rows[-1])
        for i,val in enumerate(row):
            cells[i].text=str(val); cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if ridx%2==1: shade(cells[i],'EAEAEA')
            for p in cells[i].paragraphs:
                p.paragraph_format.space_after=Pt(1)
                for r in p.runs: r.font.size=Pt(font)
    if widths:
        for row in t.rows:
            for i,w in enumerate(widths): row.cells[i].width=Inches(w)
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
    return t
def para(text,style=None): return doc.add_paragraph(text.replace('`',''),style)
def heading(text,level=1): doc.add_heading(text,level=level)
def caption(text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run(text); r.italic=True; r.font.size=Pt(8)
def figure(path,caption_text,width=6.2):
    doc.add_picture(str(path),width=Inches(width)); doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER
    caption(caption_text)
def fmt(x,d=3): return f"{x:.{d}f}"

# Title page
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(70)
r=p.add_run('Progress Report 02'); r.bold=True; r.font.name='Times New Roman'; r.font.size=Pt(25); r.font.color.rgb=RGBColor(0,0,0)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run('Machine Learning for Detecting Previously Unseen Network Attacks'); r.bold=True; r.font.name='Times New Roman'; r.font.size=Pt(16)
para('DSAI 310 Introduction to Data Science | Section 2',None).alignment=WD_ALIGN_PARAGRAPH.CENTER
para('American University of Bahrain | Fall 2026').alignment=WD_ALIGN_PARAGRAPH.CENTER
para('Ahmed Hazeem (F2400204)\nYousif Alansari (F2400202)\nSayed Ahmed (F2400231)').alignment=WD_ALIGN_PARAGRAPH.CENTER
para('Submitted to Dr. Maqbool Khan').alignment=WD_ALIGN_PARAGRAPH.CENTER
para('Progress Report 02 | 19 November 2026').alignment=WD_ALIGN_PARAGRAPH.CENTER
doc.add_page_break()

heading('1. Introduction')
heading('1.1 Problem statement and importance',2)
para('This project asks whether a classical supervised classifier trained on normal traffic and several known attack families will still identify traffic from an attack family excluded from training as malicious. It also measures how its score changes between a conventional test, where attack categories are represented in training, and a category holdout. A high score on a familiar benchmark can create false confidence if a detector misses an unfamiliar attack family. False negatives represent attacks incorrectly treated as benign, while false positives create alerts on normal activity and impose an analyst workload. Both errors therefore matter to a security team deciding how to use a model.')
para('Progress Report 01 framed the question around whether a model can learn a general signal of malicious flow behavior, rather than only memorizing patterns associated with attack names seen during training. This distinction is important because the binary target in this project is “normal” versus “attack”; the model is not asked to name the attack family. A successful prediction on a held-out family therefore means that its flow features were sufficient for the classifier to place the record on the attack side of its decision boundary, not that it recognized the new attack type.')
heading('1.2 Objectives',2)
para('The objectives established in Progress Report 01 remain: (1) evaluate binary attack detection when one attack category is absent from training; (2) compare Logistic Regression as a transparent baseline with Random Forest and XGBoost; (3) compare per-category recall in the conventional and category-held-out conditions; and (4) inspect missed held-out records and assess whether exact feature overlap qualifies their novelty. The present report completes the primary model comparison and record-level miss inventory. A causal explanation of model decisions and a full comparison of feature importance across runs remain future analyses.')
para('These objectives are evaluated using paired experiments on the same official train/test partitions so that the central comparison is the training condition. The analysis reports category-level recall and normal-traffic false-positive rates because a single pooled accuracy value can conceal a model that detects common attacks while missing a specific family. The error-inspection objective is only partly complete: the pipeline identifies and exports the missed test flows and their predicted probabilities, but interpreting why their feature patterns led to a miss requires a separate feature-distribution and model-explanation analysis.')
heading('1.3 Dataset context and scope',2)
para('The project uses the author-provided UNSW-NB15 training and testing partitions. Their `attack_cat` labels enable one category to be withheld from training while its test records remain available for evaluation. The study is limited to binary normal-versus-attack classification with LR, RF, and XGBoost. It does not evaluate live traffic, deep learning, one-class anomaly detection, or operational zero-day protection. Category holdout is a controlled benchmark proxy for novelty; it does not establish that attack behavior, time, infrastructure, or campaigns are independent across partitions.')
para('The official partitions contain nine attack labels in addition to Normal and were created as benchmark data rather than as a chronological stream. The experiment uses the attack category only to select records and group results; it is removed from the feature inputs along with the record identifier. Accordingly, the results address generalization across these dataset labels under the supplied partition design. They cannot on their own establish transfer to a future date, a different network, a different attack campaign, or traffic collected by another sensor.')
heading('1.4 Planned contribution and decision supported',2)
para('The intended output is a per-category comparison between detection on the conventional reference and detection when that category is excluded from training, together with false-positive rates on normal traffic. This evidence can help a defender identify categories for which a supervised classifier may need additional controls, such as signatures, anomaly detection, or analyst review. The project provides comparative benchmark evidence; it does not recommend deploying any model based on these results alone.')
para('For this report, that comparison is supplemented with the category-level difference between E1 recall and E2 recall, an exact-feature-overlap sensitivity measure, and a list of false-negative test records. The practical decision supported is therefore preliminary: whether a model’s apparently strong reference score is accompanied by acceptable detection across the available held-out labels, and which categories merit additional review. A low false-positive rate is also necessary for an alerting system to be usable, so recall is never interpreted in isolation.')
heading('1.5 Report structure',2)
para('This report carries forward the problem framing and literature review from Progress Report 01, then updates the dataset, methodology, experiments, results, contributions, and conclusion with work completed for Progress Report 02. The section order follows the project report structure: Introduction, Related Work, Dataset, Methodology, Experiments, Results and Analysis, Contributions, Conclusion, and References.')
para('The Dataset section now reports measured quality checks and exploratory figures. Methodology and Experiments describe the implemented pipeline and the E1/E2 runs rather than planned work. Results and Analysis distinguish measured findings from interpretation and identify unfinished analyses for the final report. The contribution record remains explicitly incomplete because verified PR02 task history was not present in the project files.')

heading('2. Related Work')
heading('2.1 Closed-set evaluation on UNSW-NB15',2)
para('Progress Report 01 reviewed studies reporting strong UNSW-NB15 performance when training and testing include the same attack classes. Ahmad et al. grouped features into flow, MQTT, and TCP sets and compared Random Forest, SVM, and neural networks; Random Forest achieved 98.67% binary and 97.37% multiclass accuracy in their setting [1]. Ajagbe et al. compared linear SVC, LR, RF, Decision Tree, and XGBoost on an imbalanced sample with a 70/15/15 split. RF and XGBoost performed best overall; XGBoost reported 93% precision and 88% attack recall, while LR had the lowest ROC-AUC (0.70) among the compared models [6]. Moualla et al. combined SMOTE, category-specific Extra Trees feature selection, one-vs-all extreme learning machines, and a final LR layer, reporting 98.43% multiclass accuracy on official partitions [9]. These results establish useful closed-set comparisons but do not directly measure recall when an attack family is absent from training.')
para('The studies are not directly rankable by their headline numbers because they differ in class definitions, sampling, preprocessing, partitions, and whether their task is binary or multiclass. Their high reported scores establish that supervised models can separate records under conditions where represented classes occur in both training and testing. They do not provide evidence that a model will identify a family absent from its training data. This project therefore uses the same model families as the proposal but changes the evaluation question, keeping the binary attack target while deliberately withholding the category label from training.')
heading('2.2 Feature selection and feature importance',2)
para('Kasongo and Sun used XGBoost feature importance to reduce UNSW-NB15 inputs to 19 features; the reduction raised Decision Tree binary accuracy from 88.13% to 90.85% [2]. Yin et al. proposed IGRF-RFE, reducing the feature set from 42 to 23 while improving multiclass accuracy from 82.25% to 84.24%; their data processing included removal of minority classes and resampling [10]. Pansari et al. selected 19 of 41 features with XGBoost and removed Worms and Shellcode from both training and testing for an ablation analysis. Their smaller feature set retained comparable accuracy and reduced runtime in many cases [11]. These studies motivate careful feature preparation, but they do not establish that feature rankings transfer to an attack category withheld from training. The current workflow creates flow-derived features and prunes highly correlated numeric fields within each training fold; it does not claim a complete feature-importance explanation.')
para('Feature selection can improve runtime and reduce redundancy, but selection performed on all records or on the test labels can overstate its benefit. For that reason the current model pipeline learns its correlation pruning, skew decisions, encoding, and scaling from each training fold. The final-report analysis should extend this discipline to feature interpretation: any ranking or importance comparison must be computed without using held-out test labels to select the model, and it should be reported as an association with model predictions rather than as evidence that a feature causes an attack.')
heading('2.3 Evaluation of attacks omitted from training',2)
para('Sarhan et al. are the closest methodological reference. They framed category holdout as zero-shot intrusion detection, trained RF and MLP with one attack category omitted, and reported zero-day detection rate (the fraction of held-out-category records classified as attacks). Most categories remained detectable, while Fuzzers had low detection (approximately 15% for RF and 20% for MLP); the mean was 80.67% for RF and 85.5% for MLP [4]. Their distribution-distance analysis linked weak categories to feature distributions unlike those in the training attacks. Uddin et al. removed one or more categories across ten datasets and found that RF performance on UNSW-NB15 declined as more categories were removed; with seven omitted, reported accuracy fell from 95.12% to 54.36%. Their normal-only usfAD approach maintained about 82% accuracy across omission settings [3]. Mbona and Eloff studied semi-supervised approaches, using Benford’s law to select features; their one-class SVM reached 85% F1 and a Matthews correlation coefficient of 74% across the evaluated datasets [5]. Tian et al. addressed a related but different few-shot setting using a triplet network that learns from a small number of attack examples [12].')
heading('2.4 Comparison of the main studies',2)
table(['Study','Approach','Unseen-category setting','Reported finding and limitation'],[
 ['Ahmad et al. [1]','RF, SVM, neural network; feature groups','No','98.67% RF binary accuracy; closed-set result'],
 ['Kasongo and Sun [2]','XGBoost feature selection and supervised models','No','19 features improved Decision Tree accuracy; no novelty test'],
 ['Uddin et al. [3]','RF and unknown-attack methods across datasets','Yes, categories removed','RF accuracy fell as categories were removed; multi-dataset average'],
 ['Sarhan et al. [4]','RF and MLP, one category omitted','Yes, one at a time','Mean zero-day detection 80.67% RF; Fuzzers especially difficult'],
 ['Mbona and Eloff [5]','Benford feature selection, semi-supervised models','Yes, semi-supervised','One-class SVM F1 85%; broader multi-dataset evaluation'],
 ['Ajagbe et al. [6]','LR, RF, XGBoost and other classifiers','No','RF/XGBoost led; closed-set imbalanced sample'],
 ['Moualla et al. [9]','SMOTE, Extra Trees, ELM, LR pipeline','No','98.43% multiclass accuracy on official partitions'],
 ['Yin et al. [10]','IGRF-RFE with MLP','No','Feature reduction improved reported multiclass accuracy'],
 ['Pansari et al. [11]','XGBoost feature selection and ablation','Partial class removal','Similar accuracy with faster reduced-feature runs'],
 ['Tian et al. [12]','Few-shot triplet network','Few examples available','Different setting from zero-shot category holdout'],
], [1.1,1.8,1.25,2.45],6.6)
heading('2.5 Gap and how it shapes this project',2)
para('The Progress Report 01 review identified three connected gaps. First, prior category-holdout studies do not provide the same per-category comparison between conventional and unseen-category recall on the official author-provided partitions. Second, LR and gradient boosting receive less attention in open-set studies than RF, despite their relevance in closed-set comparisons. Third, reported missed categories motivate an error analysis that relates detection failures to data overlap and flow characteristics. This project addresses the first two gaps through matched E1 and E2 evaluations for LR, RF, and XGBoost. It adds exact feature-vector overlap and a record-level missed-flow inventory as diagnostic evidence. It does not claim to explain model behavior causally or to prove operational zero-day detection.')
para('The literature supports the choice to show results by held-out family rather than only as a single mean. In particular, the low Fuzzers results reported by Sarhan et al. [4] provide context for examining whether this project sees a similar hard category, while the study design differs in data partition, preprocessing, and model configurations. The current report treats those prior findings as motivation for comparison, not as a target result that the present models are expected to reproduce.')

heading('3. Dataset')
heading('3.1 Source, partitions, and labels',2)
para('UNSW-NB15 was created at the Cyber Range Laboratory at UNSW Canberra using IXIA PerfectStorm and network-flow processing tools [7], [8]. The full dataset is larger than the partition files used here. Progress Report 01 noted a Kaggle Parquet mirror [13]; this report uses the author-provided training and testing partition CSVs available in the project resources, not a modified Google Sheets version or the mirror. The partitions have 175,341 training rows and 82,332 test rows; each contains 45 columns: an identifier, 42 flow attributes, the attack category, and the binary label. The model predicts `label` (0 normal, 1 attack). `attack_cat` is used only for category holdouts and grouped analysis; `id` is excluded from inputs.')
para('The dataset construction combines normal traffic and synthetic attack activity captured in a cyber range and converted to flow records [7], [8]. It is useful for this project because the attack-family label supports a clear leave-one-category-out protocol, and the supplied partitions provide a fixed reference experiment. At the same time, its experimental origin and fixed partitioning limit the conclusions that can be drawn about a live network, where traffic may arrive at different rates and contain different background activity.')
para('The partition files are checked against expected dimensions, category counts, label/category consistency, and SHA-256 hashes on each run. The files in `data/` match the corresponding author-provided project partition files by hashes recorded in `results/pr02/run_manifest.json`. The official UNSW Research page is the access and citation source [8]. The project README records the source-file identification by row count so the files cannot be silently reversed.')
para('The original proposal described a test count of 82,322 and spreadsheet delivery. The author partition used here contains 82,332 test rows, and the project data is stored as CSV rather than as the spreadsheet format originally anticipated. The runner rejects other dimensions or category totals, and records the SHA-256 hash of each input. This makes the exact data used for the reported metrics auditable and prevents a similarly named file or re-ordered partition from being substituted without notice.')
heading('3.2 Dataset exploration and data quality',2)
para('The training partition contains 119,341 attacks and 56,000 normal records (68.1% attacks); the test partition contains 45,332 attacks and 37,000 normal records (55.1% attacks). Category counts are highly uneven: Worms has 130 training and 44 test examples, while Generic has 40,000 and 18,871. The lower attack prevalence in training than in testing and the sharp differences among attack categories motivate class weighting and per-category recall rather than accuracy alone. Very small categories also require interval estimates and cautious interpretation.')
para('The binary class proportions also differ across the official partitions: normal traffic is 31.9% of training data and 44.9% of test data. This means precision, accuracy, and the number of false alarms depend partly on the partition’s prevalence, even if the decision threshold is held constant. For the benchmark comparison, class weights are used during fitting, but the threshold remains fixed at 0.5 to avoid selecting an operating point from the test labels. The prevalence difference is retained as a limitation when interpreting test precision and FPR.')
selected_stats=['sbytes','dbytes','rate','sload','response_body_len']
table(['Numeric feature','Median','Skew','IQR outliers (%)'],[
    [name,fmt(numeric_summary.loc[name,'50%'],2),fmt(numeric_summary.loc[name,'skew'],2),fmt(outlier_summary.loc[name,'iqr_outlier_percent'],1)] for name in selected_stats
], [2.2,1.1,1.1,2.0],8)
para('The selected flow-volume and load fields have long right tails. IQR outlier flags identify statistical extremes, not confirmed data errors; the workflow retains these records and applies log1p to eligible skewed features before scaling.')
para('The summary values show why a single scale is unsuitable across all numeric fields: byte and load variables have large skew, and several IQR rules flag a notable share of records as extreme. These values can reflect legitimate high-volume flows rather than malformed observations. The workflow therefore transforms eligible nonnegative skewed features rather than deleting statistical outliers, which would risk removing unusual but relevant attack behavior. The two grayscale figures show distribution and class differences descriptively; they are not used to choose test-set thresholds.')
para("The reproducible runner found no missing cells, negative numeric values, or disagreement between `attack_cat == Normal` and `label == 0`. `service = '-'` is retained as its own category to denote no recognized service. The training partition contains 67,601 exact duplicate rows when `id` is ignored; the test partition contains 26,387 such rows. Cleaning removes training duplicate rows and feature groups whose identical vectors map to conflicting binary labels; the official test partition is left intact so it remains the specified evaluation set. This choice prevents the cleaning procedure from altering test prevalence or removing hard cases, while overlap is explicitly measured and discussed.")
para('Duplicate counts are important because repeated flows can make the test set easier when exact copies occur in training, but deleting such records from the official test set would change the evaluation population. The implemented compromise cleans only the training partition, removes contradictory binary-label feature groups from training, and quantifies matching feature vectors separately for each test category and holdout run. Thus the primary results remain tied to the official test partition, while the report also shows how much of the nominal category holdout is not strictly novel in feature space.')
table(['Partition','Rows','Missing cells','Duplicate rows','Label/category disagreements'],[
    [r.partition,int(r.rows),int(r.missing_cells),int(r.exact_duplicate_rows_ignoring_id),int(r.label_category_disagreements)] for _,r in q.iterrows()
], [1.1,1.0,1.1,1.2,1.8],8)
para(f"After exact duplicate removal, {int(manifest['after_exact_duplicate_removal']):,} training rows remained. Removing {int(manifest['conflicting_label_rows_removed']):,} conflicting-label rows left {int(manifest['final_rows']):,} rows for model fitting. Test rows were retained.")
category_count_rows=[]
for cat in ['Normal','Generic','Exploits','Fuzzers','DoS','Reconnaissance','Analysis','Backdoor','Shellcode','Worms']:
    category_count_rows.append([cat,EXPECTED[cat][0],EXPECTED[cat][1]])
table(['Category','Train records','Train share','Test records','Test share'],[[cat,EXPECTED[cat][0],f"{100*EXPECTED[cat][0]/175341:.2f}%",EXPECTED[cat][1],f"{100*EXPECTED[cat][1]/82332:.2f}%"] for cat in ['Normal','Generic','Exploits','Fuzzers','DoS','Reconnaissance','Analysis','Backdoor','Shellcode','Worms']],[1.8,1.3,1.0,1.3,1.0],7.5)
para('Feature vectors also overlap across partitions: the overlap diagnostic counts exact matching input vectors while ignoring `id`, `attack_cat`, and `label`. Some held-out categories have substantial exact-vector overlap with the remaining training data, including DoS. Thus an E2 category is absent by label from training, but some of its test flows have a feature vector already represented under another category. Results should be read as category-label holdout results, not uniformly feature-novel detection.')
para('This distinction affects the interpretation of high recall. A classifier may correctly flag a test flow whose attack-family label was withheld because it has already encountered the same measured flow vector under another attack label. The exact-vector sensitivity results below provide a stricter subset check, but do not establish independence from near-duplicates or shared underlying activity. Both the complete category-held-out result and the filtered sensitivity should therefore be reported together.')
figure(F/'class_distribution_color.png','Figure 1. Label and attack-category distribution in the official partitions.',6.3)
doc.add_page_break()
figure(F/'selected_feature_distributions_color.png','Figure 2. Selected numeric feature distributions for normal and attack records; axes use log1p-transformed values for visualization.',6.3)

heading('4. Methodology')
heading('4.1 Data preparation and feature creation',2)
para('The runner removes `id`, `attack_cat`, and `label` from the model input. It removes exact duplicates from training using flow features plus category and label, then removes feature-vector groups associated with multiple binary labels. It does not delete test rows. Data-quality counts and cross-partition feature overlap are saved as CSV outputs.')
para('The duplicate-removal step treats `id` as a record identifier rather than as a predictive signal. First, exact duplicates with the same features, category, and binary label are reduced to one training row. Next, if a feature vector maps to both normal and attack labels, all such training rows are removed rather than allowing contradictory targets for an identical input. This decision produces a cleaner supervised target at the cost of reducing the training sample; the report records both removals so the effect is transparent.')
para('Four flow features are created: log-byte direction difference, log-packet direction difference, total bytes per packet, and a no-response indicator. `is_ftp_login` is excluded because it is redundant with `ct_ftp_cmd`. Numeric features are pruned for absolute pairwise correlation above 0.95 using training data only. Nonnegative numeric features with training-fold skew above 1 receive log1p and standardization; remaining numeric features are standardized. `proto`, `service`, and `state` are one-hot encoded; categories with fewer than 100 training-fold observations are grouped as infrequent, and unknown values are handled by the infrequent bucket when present. These choices retain rare categories as explicit levels where possible while limiting sparse feature expansion.')
para('Feature creation, correlation pruning, skew decisions, encoders, and scalers are fitted inside the scikit-learn pipeline within each CV fold. The official test partition is held out from tuning and preprocessing fitting. The feature overlap diagnostic uses test feature values only to describe overlap; it does not fit or tune a model.')
para('Keeping all learned transformations inside the pipeline prevents the validation folds from contributing feature statistics to their own training transformations. The same fitted pipeline is then applied to the official test records only after each model configuration has been selected using training-fold cross-validation. The overlap diagnostic is a post hoc description of data reuse; it does not influence feature selection, hyperparameter choice, or predictions.')
heading('4.2 Methods and modeling protocol',2)
para('E1 fits each model on the cleaned full training partition and evaluates on the full official test partition. E2 repeats the fit after excluding one attack category from training and evaluates on the 37,000 normal test records plus the test records for that held-out category. LR uses balanced class weights and tunes C over 0.1, 1, and 10. RF uses balanced subsampling weights, 100 trees, and compares unlimited depth with maximum depth 18. Each configuration uses three-fold stratified cross-validation on the relevant training data, scored by binary F1. The selected estimator is refit on that run’s full training data.')
para('The operating threshold is fixed at 0.5 for all reported test metrics; the threshold is not tuned on test data. We report accuracy, precision, recall, F1, FPR, ROC-AUC, and average precision for E1; E2 emphasizes held-out-category recall and FPR on normal traffic. Per-category recall intervals are 95% Wilson binomial intervals. They describe sampling uncertainty conditional on the fitted model and do not capture training-seed or dataset-shift uncertainty.')
para('The earlier notebook’s validation row is omitted because its prediction model had been refit on the full training partition, including those validation rows. The present report uses training-fold CV only for model selection and the untouched official test partition for the reported E1/E2 metrics. Duplicate and conflicting-label filtering is performed on the training partition before CV; because the conflict filter uses training labels, CV scores may be somewhat optimistic with respect to that filtering step. This does not expose the official test labels.')
para('This correction is material to reproducibility: the earlier validation output should not be read as an independent validation estimate, because the model producing it had already seen those rows during refitting. The present results rely on cross-validation for configuration selection and the official test partition for final reported metrics. One residual qualification is that the conflict-label cleanup is applied to the full training partition before folds are created; consequently, CV scores may benefit from knowledge that a contradictory group exists in another fold. That cleanup does not use test records, but the final report should retain this qualification when discussing model-selection scores.')
para('XGBoost uses a fixed 150-tree, learning-rate 0.08 histogram-boosting configuration and tunes maximum depth over 4 and 6. Its positive-class weight is set from the attack-to-normal ratio in each run’s training data. This model comparison is intentionally limited to the three models proposed in Progress Report 01; no additional model families are introduced.')
para('The runner uses Python, pandas, NumPy, scikit-learn, SciPy, Matplotlib, and XGBoost. The execution manifest records the seed, versions, hashes, row counts, and fold count. The primary run uses seed 42; E1 and E2 were additionally repeated with seeds 7 and 21. These three seeds measure sensitivity to stochastic fitting and CV splits, but do not provide a broad estimate of uncertainty.')
heading('4.3 Reproducible implementation and data access',2)
para('The complete runnable source is `run_pr02.py`; `PR02_UNSW_NB15_workflow.ipynb` retains exploratory analysis, and `requirements.txt` lists Python dependencies. The verified dataset files are `data/train.csv` (175,341 rows) and `data/test.csv` (82,332 rows); the README explains how to obtain the official UNSW-NB15 files if they are not bundled. From the project root, install the requirements and run `python run_pr02.py --data-dir data --include-xgboost --repeat-seeds`. On macOS, install the native OpenMP runtime with `brew install libomp` if needed by XGBoost. Results, data checks, the run manifest, and figures are written under `results/pr02/` and `figures/pr02/`. The manifest records exact partition hashes and software versions. The run uses seed 42 plus repeat seeds 7 and 21, three-fold CV, and a fixed 0.5 test threshold.')
para('The notebook remains useful for inspecting exploratory work, while the runner is the canonical source for the report’s final experiment tables because it checks the data and writes machine-readable outputs. The manifest records Python and library versions, partition hashes, row counts, model list, random seeds, fold count, and threshold. Reproduction also requires the dependencies in `requirements.txt` and, for XGBoost on macOS, the native OpenMP library noted in the README. The exact command and output locations allow another group member to regenerate the experiment tables and grayscale figures without relying on notebook state.')

heading('5. Experiments')
heading('5.1 Tool-based data and modeling workflow',2)
table(['Experiment','Training data','Evaluation data','Runs'],[
 ['E1 reference','All cleaned training rows; all attack categories represented','Full official test partition','3 models x 3 seeds'],
 ['E2 LOACO','Cleaned training data excluding category C','Normal plus test records from C','9 categories x 3 models x 3 seeds'],
], [1.1,2.2,2.2,1.1],8)
para('The primary E1 and E2 results use seed 42. The additional seed sensitivity run repeats the complete model-selection and category-holdout pipeline for seeds 7 and 21. For each E2 run, the analysis also reports recall restricted to held-out records whose exact input feature vector does not appear in that run’s remaining training data. The per-record false-negative file preserves each missed held-out test flow, predicted attack probability, and overlap flag.')
para('The run matrix contains three reference evaluations per model (one for each seed) and 27 category-holdout configurations per seed. For every held-out category, evaluation includes the 37,000 normal test records to estimate false-positive rate and all test examples from the omitted attack family to estimate attack recall. The filtered recall uses the same model predictions and test subset but excludes exact feature vectors represented in the remaining cleaned training data; it is reported as sensitivity analysis, not as a separately tuned experiment.')

heading('6. Results and Analysis')
heading('6.1 Initial experiments and results: E1 reference',2)
rows=[]
for _,r in e1.iterrows():
    rows.append([r.model,int(r.n),fmt(r.accuracy),fmt(r.precision),fmt(r.recall),fmt(r.f1),fmt(r.fpr),fmt(r.roc_auc),fmt(r.average_precision)])
table(['Model','N','Accuracy','Precision','Recall','F1','FPR','ROC-AUC','Avg. precision'],rows,[1.28,.45,.68,.7,.62,.55,.55,.7,.82],7.5)
best=e1.sort_values('f1',ascending=False).iloc[0]
para(f"At threshold 0.5, LR attains {fmt(e1.loc[e1.model=='Logistic Regression','recall'].iloc[0])} attack recall with {fmt(e1.loc[e1.model=='Logistic Regression','fpr'].iloc[0])} FPR. RF reaches {fmt(e1.loc[e1.model=='Random Forest','recall'].iloc[0])} recall and {fmt(e1.loc[e1.model=='Random Forest','fpr'].iloc[0])} FPR. XGBoost reaches {fmt(e1.loc[e1.model=='XGBoost','recall'].iloc[0])} recall and {fmt(e1.loc[e1.model=='XGBoost','fpr'].iloc[0])} FPR. XGBoost has the highest E1 F1 ({fmt(best.f1)}), ROC-AUC ({fmt(best.roc_auc)}), and average precision ({fmt(best.average_precision)}) on this test partition. These benchmark results do not establish an acceptable operational false-alarm rate.")
para('At this fixed threshold, LR’s 0.335 FPR corresponds to 12,412 of 37,000 normal test records being flagged as attacks. RF reduces that count to 10,033, and XGBoost to 9,199. Their E1 attack recalls are all high, but this residual alert volume remains substantial for an operational detector. XGBoost’s advantage is therefore a relative improvement on this benchmark, not evidence that its false-alarm burden is acceptable in practice.')
figure(F/'e1_false_positive_rate_color.png','Figure 3. E1 false-positive rates on normal records in the full test partition at threshold 0.5.',5.8)
para('The E1 confusion counts (TP, FN, FP, TN) are: '+ '; '.join(f"{r.model} {int(r.tp):,}, {int(r.fn):,}, {int(r.fp):,}, {int(r.tn):,}" for _,r in e1.iterrows()) + '. The E1 metrics are test metrics; the CV F1 values are model-selection scores and are not reported as independent test performance.')
para('The confusion counts make the tradeoff concrete: the models miss relatively few attack records in E1 but incorrectly flag many normal records. The ranking by F1, ROC-AUC, and average precision is consistent in this one reference test, but the distinction between models is modest in recall and larger in FPR. This is why the results section retains precision and FPR as well as attack recall, and why performance on E1 should not be used as a substitute for the held-out-category results.')
heading('6.2 Category-holdout results',2)
p=para('The category holdout produces a mixed generalization pattern. Fuzzers is the weakest category for all three models: '+ '; '.join(f"{m} {fmt(e2[(e2.model==m)&(e2.held_out_category=='Fuzzers')].attack_recall.iloc[0])}" for m in models) + '. Worms estimates are based on only 44 test rows, so even a high point estimate has substantial uncertainty and should not be treated as precise evidence of reliable detection.')
p.paragraph_format.keep_together=True
para('The category-level recall gap is the E1 seen-category recall minus the corresponding E2 held-out recall. The macro mean gap is 0.067 for LR, 0.055 for RF, and 0.057 for XGBoost across the nine categories. Those averages hide sharply different category outcomes: for Fuzzers, recall falls from the E1 seen result to the much lower category-holdout result for every model. The per-category table is therefore more informative than the macro gap, particularly because rare categories contribute few test records and have wide Wilson intervals.')
figure(F/'loaco_recall_models_color.png','Figure 4. E2 recall by held-out category for LR, RF, and XGBoost at threshold 0.5. Error bars are 95% Wilson intervals.',6.4)
table(['Model','Mean E1 category recall','Mean LOACO recall','Mean recall gap'],[[m,
    f"{e2[e2.model==m].e1_seen_recall.mean():.3f}",f"{e2[e2.model==m].attack_recall.mean():.3f}",
    f"{e2[e2.model==m].recall_gap.mean():.3f}"] for m in models],[1.45,1.8,1.7,1.55],7.5)
rows=[]
for _,r in e2.iterrows():
    rows.append([r.model,r.held_out_category,int(r.test_n),fmt(r.attack_recall),f"[{fmt(r.recall_ci_low)},{fmt(r.recall_ci_high)}]",fmt(r.normal_fpr),int(r.feature_unseen_n),fmt(r.feature_unseen_recall),f"{100*r.heldout_feature_vectors_seen_in_remaining_train:.1f}%"])
table(['Model','Held-out category','n','Recall','95% CI','Normal FPR','Unseen n','Unseen recall','Exact vector seen'],rows,[.9,1.05,.3,.5,.85,.55,.45,.65,.7],6.7)
p=para('The Fuzzers result is notable because all three models lose substantial recall relative to their E1 category recall. The remaining-category training data also yields nontrivial normal FPRs in many runs: LR ranges from 0.170 to 0.377, RF from 0.062 to 0.271, and XGBoost from 0.076 to 0.311. Thus attack recall alone does not describe the detector’s practical tradeoff. XGBoost improves E1 results but does not improve held-out Fuzzers recall.')
p.paragraph_format.keep_together=True
para('RF and XGBoost achieve stronger mean LOACO recall than LR in the current run, but category-wise performance is uneven and the preferred model depends on the threat family and acceptable alert rate. For example, RF has a lower normal FPR than LR in the Fuzzers holdout, but its Fuzzers recall is also low; XGBoost’s stronger E1 ranking does not transfer to the best Fuzzers result. This evidence argues against selecting a detector from its E1 score alone and supports reporting paired recall and false-alarm values for each held-out family.')
para('Exact-vector filtering removes held-out test flows whose feature vectors occur in the remaining cleaned training data. Across category/model runs, the mean fraction overlapping training is '+ '; '.join(f"{m}: {100*e2[e2.model==m].heldout_feature_vectors_seen_in_remaining_train.mean():.1f}%" for m in models) + '. Mean recall on strictly feature-unseen rows is '+ '; '.join(f"{m}: {e2[e2.model==m].feature_unseen_recall.mean():.3f}" for m in models) + '. This sensitivity analysis is a stricter descriptive subset, not a replacement test partition; an exact match may be a legitimate repeated flow, and nonmatching vectors can still be near-duplicates or otherwise familiar.')
para('The filtered values remain high on average, but this does not remove the category-specific weakness on Fuzzers. The result also depends on the exact-match definition: it ignores the record ID, category, and label, and tests exact equality across the measured feature vector. It will not detect two nearly identical flows whose counters differ slightly, nor does an exact match necessarily prove leakage if the dataset contains legitimate repeated traffic. The analysis is thus a diagnostic bound on strict novelty, not a complete duplicate- or campaign-control protocol.')
heading('6.3 Seed sensitivity and missed-record review',2)
seed_e1=seed[(seed.experiment=='E1')]
table(['Model','E1 recall across seeds','E1 FPR across seeds','E1 F1 across seeds'],[[m,
    f"{seed_e1[seed_e1.model==m].recall.mean():.3f} (SD {seed_e1[seed_e1.model==m].recall.std():.3f})",
    f"{seed_e1[seed_e1.model==m].fpr.mean():.3f} (SD {seed_e1[seed_e1.model==m].fpr.std():.3f})",
    f"{seed_e1[seed_e1.model==m].f1.mean():.3f} (SD {seed_e1[seed_e1.model==m].f1.std():.3f})"] for m in models], [1.25,1.7,1.7,1.7],7.5)
para('Seed sensitivity uses seeds 7, 21, and 42 with the same data partitions, threshold, and model grids. E1 variation is summarized as mean and sample standard deviation. LOACO recall and FPR variation is retained per category in `results/pr02/seed_sensitivity.csv`; three seeds are too few to characterize all sources of uncertainty.')
seed_e2=seed[seed.experiment=='E2']
seed_cat=seed_e2.groupby(['model','category']).agg(recall_sd=('recall','std'),fpr_sd=('fpr','std')).reset_index()
table(['Model','Mean within-category recall SD','Largest category recall SD','Mean within-category FPR SD'],[[m,
    f"{seed_cat[seed_cat.model==m].recall_sd.mean():.3f}",f"{seed_cat[seed_cat.model==m].recall_sd.max():.3f}",
    f"{seed_cat[seed_cat.model==m].fpr_sd.mean():.3f}"] for m in models],[1.35,1.8,1.7,1.8],7.2)
para('The additional table summarizes seed variation within each held-out category before averaging across categories. It separates variation due to random seed from the much larger differences between attack categories. With only three observations per category, these standard deviations are descriptive and unstable; they should not be interpreted as precise confidence bounds or as evidence that the models are insensitive to retraining.')
miss_summary=misses.groupby(['model','held_out_category']).size().reset_index(name='false_negatives')
tot=misses.groupby('model').size().to_dict()
para('The record-level E2 error review contains '+ '; '.join(f"{m}: {tot.get(m,0):,} false-negative flow records across all nine holdouts" for m in models) + '. Fuzzers accounts for the largest missed-record count in each model (LR 3,099; RF 3,241; XGBoost 3,533). Individual records and probabilities are retained in `results/pr02/E2_missed_attack_records.csv` for follow-up inspection; counts across separate category holdouts should not be added as unique flows.')
para('The false-negative file provides a reproducible index of missed flows, their category, prediction probability, and exact-overlap status. Its size alone does not explain why the misses occurred, and records across different LOACO runs are not necessarily unique because the same test flow can be evaluated in different model/holdout configurations. A final error analysis should compare missed and detected flows within categories and examine them alongside normal flows, using descriptive statistics and carefully scoped feature-importance methods.')
heading('6.4 Interpretation and threats to validity',2)
para('The official train and test partitions have different normal/attack prevalence (31.9% versus 44.9% normal) and differ in the distribution of selected features such as source TTL. The high full-test FPR is therefore a material limitation, not a minor detail. The fixed 0.5 threshold supports a common baseline comparison; it does not establish the threshold that a security team should deploy. Precision and alert counts are conditional on the test partition’s class prevalence, so the observed values should not be assumed to transfer to networks with different normal-to-attack ratios.')
para('The study evaluates one benchmark partition with label-based category holdouts. Because E2 does not separate traffic by capture time, network, device, or attacker campaign, a category absent from training is not necessarily independent in behavior or source. Cross-category exact feature matches further qualify the claim of novelty. The results should therefore be described as detection of categories withheld by label under the UNSW-NB15 partition, rather than as validation against future attacks or operational zero-day events.')
heading('6.5 Limitations',2)
heading('6.5.1 Seed and sampling uncertainty',3)
para('Only three random seeds (7, 21, and 42) were run. They provide a useful first sensitivity check for stochastic training and cross-validation splits, but three repetitions are not enough to characterize variation reliably across model configurations. In addition, Wilson intervals describe binomial uncertainty for one fitted model on the observed test records; they do not capture dataset shift, repeated-flow dependence, or uncertainty from retraining. In the final-report iteration, run at least ten pre-specified seeds, retain per-seed metrics for E1 and every E2 category, and report means, standard deviations, and intervals separately from the per-test-record binomial intervals.')
heading('6.5.2 Exact-match filtering and near-duplicate flows',3)
para('The overlap sensitivity filter identifies exact equality of the input feature vector after excluding ID, category, and label. It does not identify near-duplicates, flows with small measurement differences, or shared behavior expressed through different counters. This can leave some familiar traffic in the “feature-unseen” subset. For the final report, extend the audit with a documented near-duplicate method, such as distance-based matching on scaled numeric fields together with exact categorical matches, and show how results change under more than one justified tolerance. Keep the current exact-match result as a reproducible reference and avoid presenting either filter as proof of semantic novelty.')
heading('6.5.3 Partition shift and the fixed threshold',3)
para('The normal share differs between training (31.9%) and testing (44.9%), and selected feature distributions also differ. At the fixed 0.5 threshold, the E1 FPR ranges from 0.249 to 0.335, a substantial alert burden even though attack recall is high. In the final-report iteration, select candidate operating thresholds using a validation split drawn only from the training partition, state the selection criterion before evaluating the official test partition, and report recall, FPR, precision, and expected alert counts across the threshold curve. Do not tune the threshold on the official test set. If the benchmark supports it, include a calibration or prevalence-sensitivity analysis to show how precision changes under different attack rates.')
heading('6.5.4 Small held-out categories',3)
para('Some categories have few test examples; Worms has only 44. A single additional error changes its observed recall by about 2.3 percentage points, and a perfect observed recall still has a Wilson lower bound of 0.920. The final report should retain the interval and absolute TP/FN counts for every rare category, avoid ranking models on point estimates alone, and seek additional independent samples only if a compatible source can be documented. If no additional samples are available, the report should state that the benchmark cannot support a precise estimate for these categories.')
heading('6.5.5 Scope of the category-holdout protocol',3)
para('E2 removes a category label but does not hold out time periods, network locations, devices, or campaigns. It is one benchmark protocol, so strong performance on an omitted label cannot establish generalization to a genuinely new attack family. In the final-report iteration, add a temporal or environment-separated evaluation only if the dataset provides defensible metadata or a compatible independent dataset is available. Otherwise preserve the current scope statement and describe E2 as a controlled proxy for category novelty.')
heading('6.5.6 Incomplete explanation of model errors',3)
para('The record-level false-negative file supports inspection, but a manual comparison of missed, detected, and normal records has not yet been completed. The current results therefore identify where errors occur but do not explain their causes. For the final report, review representative errors by category, compare their flow-feature distributions with detected attacks and normal traffic, and compute feature-importance summaries on training-only or validation data. Clearly label these as model associations; do not claim causal explanations from feature importance or from individual records.')
heading('6.5.7 Contribution evidence',3)
para('Progress Report 01 records the team’s planned section assignments, while the current project directory contains no PR02 task log or meeting notes. The contribution entries cannot be completed accurately from code ownership or assumptions. Before final submission, ask each team member to confirm their actual PR02 and final-report tasks, then update the table using that record. Keep the PR01 roles as historical context and do not treat them as proof of current work.')
heading('6.5.8 Meaning of “zero-day” results',3)
para('The benchmark results do not validate an operational zero-day detector. E2 is a label-category holdout on one dataset, and the observed false-positive rates and feature overlap constrain its practical meaning. The final report should consistently call these category-held-out benchmark results, avoid deployment claims, and state that operational claims would require independent, temporally separated, or live-traffic validation with an acceptable alert burden and a documented response process.')
heading('6.6 Final-report work plan',2)
para('The next iteration should first extend the repeated-seed study and freeze a threshold-selection procedure using training-only validation. It should then rerun the overlap analysis with an explicitly documented near-duplicate sensitivity, complete the per-category missed-flow review and non-causal feature analysis, and add an independent or temporal validation only where the data supports it. The report should also obtain verified contribution statements from all members. These steps address reliability, feature novelty, false-alarm interpretation, model-error analysis, external validity, and contribution transparency without changing the project’s binary detection objective or adding unrelated model families.')

heading('7. Contributions')
para('Progress Report 01 recorded a planned division of report sections: Ahmed Hazeem drafted the Introduction and Methodology; Yousif Alansari drafted Dataset, Experiments, and Results and Analysis; Sayed Ahmed drafted Related Work, Contributions, Conclusion, and References. The report also recorded peer review among all members. Those are verified PR01 assignments, not evidence of who completed the current implementation or writing. The project folder contains no PR02 task log or meeting notes, so the team’s actual contributions for this reporting period must be entered from its work history before submission.')
para('Recording the earlier assignments preserves the project history and explains the planned division of the first report. It does not attribute the newly completed code, experiments, or report text to a named individual. The team should fill the PR02 column after confirming contribution evidence together; until then the report treats this as an administrative item that remains incomplete rather than implying unsupported authorship.')
table(['Team member','Student ID','PR01 recorded role','PR02 contribution record'],[
 ['Ahmed Hazeem','F2400204','Introduction; Methodology; peer review','Team to enter verified tasks'],
 ['Yousif Alansari','F2400202','Dataset; Experiments; Results and Analysis; peer review','Team to enter verified tasks'],
 ['Sayed Ahmed','F2400231','Related Work; Contributions; Conclusion; References; peer review','Team to enter verified tasks'],
], [1.25,.9,2.3,2.05],7.4)

heading('8. Conclusion')
para('The reproducible workflow verifies the official partitions, applies fold-local preprocessing, and evaluates LR, RF, and XGBoost on a conventional reference test and nine category holdouts. XGBoost has the strongest E1 scores (accuracy 0.881, F1 0.901, ROC-AUC 0.985) and the lowest E1 FPR (0.249), but its held-out Fuzzers recall is 0.417; LR and RF reach 0.489 and 0.465 for Fuzzers. This contrast shows why a single closed-set score is inadequate for this study.')
para('The three models preserve high E1 attack recall, but their reference false-positive rates remain high, and their category-held-out results expose a substantial weakness on Fuzzers. XGBoost’s stronger E1 ranking does not translate into the strongest Fuzzers recall. Exact-vector sensitivity, seed repeats, Wilson intervals, and record-level false-negative exports make the comparison more informative, while still leaving meaningful uncertainty and external-validity limits.')
para('The study therefore provides a reproducible comparison of binary attack detection under a conventional split and label-category holdout on UNSW-NB15. It does not demonstrate protection against operational zero-day attacks. The final report should complete the limitation-specific actions in Section 6.6, particularly broader repeated-seed evaluation, training-only threshold selection, near-duplicate sensitivity, and error review. PR02 contribution entries also require confirmation from the team before submission.')

heading('9. References')
refs=[
'[1] M. Ahmad, Q. Riaz, M. Zeeshan, H. Tahir, S. A. Haider, and M. S. Khan, “Intrusion detection in internet of things using supervised machine learning based on application and transport layer features using UNSW-NB15 data-set,” EURASIP Journal on Wireless Communications and Networking, vol. 2021, Art. no. 10, 2021, doi: 10.1186/s13638-021-01893-8.',
'[2] S. M. Kasongo and Y. Sun, “Performance analysis of intrusion detection systems using a feature selection method on the UNSW-NB15 dataset,” Journal of Big Data, vol. 7, Art. no. 105, 2020, doi: 10.1186/s40537-020-00379-6.',
'[3] M. A. Uddin, S. Aryal, M. R. Bouadjenek, M. Al-Hawawreh, and M. A. Talukder, “usfAD based effective unknown attack detection focused IDS framework,” Scientific Reports, vol. 14, Art. no. 29103, 2024, doi: 10.1038/s41598-024-80021-0.',
'[4] M. Sarhan, S. Layeghy, M. Gallagher, and M. Portmann, “From zero-shot machine learning to zero-day attack detection,” International Journal of Information Security, vol. 22, pp. 947–959, 2023, doi: 10.1007/s10207-023-00676-0.',
'[5] I. Mbona and J. H. P. Eloff, “Detecting zero-day intrusion attacks using semi-supervised machine learning approaches,” IEEE Access, vol. 10, pp. 69822–69838, 2022, doi: 10.1109/ACCESS.2022.3187116.',
'[6] S. A. Ajagbe, J. B. Awotunde, and H. Florez, “Intrusion detection: A comparison study of machine learning models using unbalanced dataset,” SN Computer Science, vol. 5, Art. no. 1028, 2024, doi: 10.1007/s42979-024-03369-0.',
'[7] N. Moustafa and J. Slay, “UNSW-NB15: A comprehensive data set for network intrusion detection systems (UNSW-NB15 network data set),” in Proc. Military Communications and Information Systems Conference (MilCIS), Canberra, ACT, Australia, 2015, pp. 1–6, doi: 10.1109/MilCIS.2015.7348942.',
'[8] UNSW Research, “The UNSW-NB15 Dataset,” University of New South Wales. [Online]. Available: https://research.unsw.edu.au/projects/unsw-nb15-dataset. [Accessed: Nov. 22, 2026].',
'[9] S. Moualla, K. Khorzom, and A. Jafar, “Improving the performance of machine learning-based network intrusion detection systems on the UNSW-NB15 dataset,” Computational Intelligence and Neuroscience, vol. 2021, Art. no. 5557577, 2021, doi: 10.1155/2021/5557577.',
'[10] Y. Yin, J. Jang-Jaccard, W. Xu, A. Singh, J. Zhu, F. Sabrina, and J. Kwak, “IGRF-RFE: A hybrid feature selection method for MLP-based network intrusion detection on UNSW-NB15 dataset,” Journal of Big Data, vol. 10, Art. no. 15, 2023, doi: 10.1186/s40537-023-00694-8.',
'[11] N. Pansari, S. Srivastava, R. Ramachandra, and M. Agarwal, “Attack classification using machine learning on UNSW-NB15 dataset using XGBoost feature selection & ablation analysis,” in Proc. 2024 IEEE 9th International Conference for Convergence in Technology (I2CT), 2024, doi: 10.1109/I2CT61223.2024.10543523.',
'[12] J.-Y. Tian, Z.-M. Wang, H. Fang, L.-M. Chen, J. Qin, J. Chen, and Z.-H. Wang, “Few-shot learning-based network intrusion detection through an enhanced parallelized triplet network,” Security and Communication Networks, vol. 2022, Art. no. 3317048, 2022, doi: 10.1155/2022/3317048.',
'[13] dhoogla, “UNSW-NB15,” Kaggle. [Online]. Available: https://www.kaggle.com/datasets/dhoogla/unswnb15. [Accessed: Nov. 22, 2026].'
]
for ref in refs:
    p=para(ref); p.paragraph_format.space_after=Pt(2)
    for run in p.runs: run.font.size=Pt(8.5)

# Consistent running footer. Page numbering is omitted so the PDF renderer
# cannot display a stale cached field on the final page.
footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=footer.add_run('DSAI 310 Progress Report 02'); r.font.size=Pt(8); r.font.color.rgb=RGBColor(90,100,110)
doc.core_properties.title='Progress Report 02: Machine Learning for Detecting Previously Unseen Network Attacks'
doc.core_properties.subject='DSAI 310 Fall 2026'
doc.save(OUT)
print(OUT)
