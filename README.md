# BMEN-600-Project

## Team 3
Matthew Christoffersen  
Dylan Lam  
Yohan Min  
Perpetual Ogedegbe  

## Project decision
**GO**: we are proceeding with this research question and dataset. First check: confirm that tibialis anterior EMG is available in the file format we use.

## Team plan
| Task | Lead | Collaborators and reviewers | What does the whole team need to understand? |
|---|---|---|---|
| Literature review and background research | Matthew | Perpetual (independent search for missing evidence and perspectives); Yohan (reviewer) | Why co-contraction after stroke matters clinically; what earlier studies found; why walking speed is a confounder |
| Dataset interpretation | Matthew | Yohan (collaborator, since he will preprocess the data); Dylan (reviewer) | Who is in each group; which muscles were recorded; how EMG was processed and normalized; missing EMG; how the paretic side is labelled |
| Dataset cleaning / preprocessing | Yohan | Matthew (participant selection rules); Perpetual (reviewer) | Inclusion/exclusion choices; how age-matching was done; how strides are averaged per participant |
| Analysis (co-contraction, timing, statistics) | Dylan | Yohan (collaborator); Perpetual (reviewer) | How the co-contraction index and on/off timing are calculated; the three ways we handle walking speed; which tests we use and why |
| Validation and evaluation | Perpetual | Matthew (compares values with the literature); Dylan (reviewer) | How results were checked: recalculating CCI by hand for a few participants, plotting individual participants, testing different on/off thresholds, rerunning without the 3 assisted participants |
| Interpretation | Matthew | Perpetual and Dylan (collaborators); Yohan (reviewer) | Whether differences remain after controlling for speed; what that means for rehabilitation; limitations |
| Documentation and reproducibility | Dylan | Everyone documents their own part; Yohan (reviewer: reruns the code from the README on a fresh computer) | How to rerun the full analysis from the raw files |

### Decision-making
- **Whole team:** research question, muscle pairs, how we handle walking speed, final interpretation and conclusions.
- **Lead + reviewer:** technical choices within a task, e.g., the on/off threshold, the age-matching method and the choice of statistical test.
- **Individual lead:** day-to-day organization of their task and code/file structure within it.

### How we check each other's work
- Every task has a reviewer who is not the lead.
- Code changes go to GitHub with a short description, and the reviewer looks over them before we rely on the results.

## Project: Muscle activity during walking after stroke

### Problem statement
After a stroke, damage to descending motor pathways can disrupt the normal "one muscle on, its opposite off" pattern of walking. Muscles on the affected (paretic) side may fire together (co-contraction) or at the wrong time in the gait cycle, which stiffens the joints, raises the energy cost of walking and may increase fall risk. Rehabilitation often aims to reduce this abnormal activity. However, stroke survivors also walk more slowly, and slower walking by itself changes muscle activation, even in healthy people. If we can't separate the two, we can't tell whether an abnormal pattern is a direct result of the stroke (and worth targeting in therapy) or simply a side effect of walking slowly.

This project uses a public gait dataset (47 stroke survivors and 111 able-bodied adults with EMG) to measure co-contraction and activation timing of knee and ankle muscle pairs during walking. We will then test whether the differences between groups remain after accounting for walking speed.

### Hypotheses
1. **Co-contraction:** The paretic leg shows more co-contraction at the knee and ankle than age-matched able-bodied adults and than the non-paretic leg.
2. **Timing:** Paretic-side muscles are active for a larger share of the gait cycle, with onsets and offsets that differ from able-bodied adults.
3. **Speed:** These differences are still present after controlling for walking speed.

#### How each hypothesis is tested
| Hypothesis | Outcome measure | Muscles / pairs | Comparison | Statistical test | Supported if… |
|---|---|---|---|---|---|
| **H1a** Co-contraction vs. able-bodied | CCI (Falconer & Winter): whole gait cycle, stance, swing | Knee: VL–BF, VL–ST · Ankle: TA–GAS | Paretic leg vs. age-matched able-bodied (mean of L/R legs) | Mann–Whitney U, Holm-corrected | Paretic CCI is higher |
| **H1b** Co-contraction vs. other leg | Same as H1a | Same as H1a | Paretic vs. non-paretic leg, same stroke survivor | Wilcoxon signed-rank, Holm-corrected | Paretic CCI is higher |
| **H2** Activation timing | Onset, offset and % of gait cycle active (envelope > threshold, e.g. 25% of max) | VL, BF, ST, TA, GAS (each muscle) | Paretic vs. able-bodied; paretic vs. non-paretic | Mann–Whitney U / Wilcoxon signed-rank, Holm-corrected | Paretic muscles are active longer, with shifted onsets/offsets |
| **H3** Speed | CCI and % active (from H1–H2) | Same as above | (a) Paretic vs. non-paretic leg (same speed by design)<br>(b) All participants, adjusting for speed<br>(c) Speed-matched subset | (a) Wilcoxon signed-rank<br>(b) Regression: outcome ~ group + speed + age<br>(c) Mann–Whitney U | Group difference remains after speed is accounted for (e.g. group term still significant in (b)) |

All tests use one value per participant (strides averaged first). Speed comes from Supplementary Table 5 of the paper.

### Biomedical problem
Stroke can damage the neural pathways that coordinate reciprocal muscle activation, so survivors may show abnormal co-contraction (agonist/antagonist muscles firing together) and mistimed activation of thigh and shank muscles on the affected side during gait — contributing to stiff, inefficient, unsafe walking. The open question is whether this reflects stroke's direct effect on motor control, or is just a byproduct of walking slower (since speed alone affects co-contraction even in healthy adults).

### Research question
Compared with age-matched healthy adults, do stroke survivors show more co-contraction and altered activation timing of the thigh and shin muscles on their affected side during walking?

### Biggest uncertainty
Whether any difference we find comes from the stroke itself or just from walking slower.

### Dataset
Van Criekinge et al., 2023, *Scientific Data*: "A full-body motion capture gait dataset of 138 able-bodied adults across the life span and 50 stroke survivors."  
Paper: https://doi.org/10.1038/s41597-023-02767-y  
Data (Figshare, CC0 licence): https://springernature.figshare.com/collections/A_full-body_motion_capture_gait_dataset_of_138_able-bodied_adults_across_the_life_span_and_50_stroke_survivors/6503791/1

#### Participants
| Group | N | Ages | With EMG |
|---|---|---|---|
| Stroke survivors | 50 | 19–85 | 47 (missing: TVC11, TVC55, TVC57) |
| Able-bodied adults | 138 | 21–86 | 111 (missing: SUBJ23, 48, 54, 72, 85, SUBJ118–138) |

- Stroke participants were all within 5 months of stroke onset, with no previous stroke.
- Everyone walked over a 12 m walkway at a self-selected speed, without walking aids or orthoses.
- Three stroke participants (TVC48, TVC51, TVC54) held a physiotherapist's hand for minimal support.

#### Muscles recorded (surface EMG, both legs)
| Region | Muscles |
|---|---|
| Thigh | rectus femoris (RF), vastus lateralis (VL), biceps femoris (BF), semitendinosus (ST) |
| Shank | tibialis anterior (TA), gastrocnemius (GAS) |
| Trunk | erector spinae (ERS) |

Possible agonist/antagonist pairs: VL or RF vs. BF or ST (knee) and TA vs. GAS (ankle).

#### Files
| File type | Stroke | Able-bodied | Contents |
|---|---|---|---|
| Excel (.xlsx) | 15 MB | 38 MB | Stride-normalized sagittal joint angles and EMG envelopes. The Figshare description lists GAS, RF, VL, BF, ST and ERS (no TA). |
| MATLAB (.mat) | 2.9 GB | 6.2 GB | Stride-normalized data for all 7 muscles (raw and normalized envelopes), gait events and anthropometrics |
| C3D (.zip) | 316 MB | 463 MB | Original recordings: unfiltered EMG, marker data, kinematics and kinetics |

#### EMG processing already applied (Excel and MAT files)
- 10–300 Hz band-pass filter, rectification and a 50 ms moving average (linear envelope)
- Each stride time-normalized to 1000 points
- Amplitude normalized to each participant's maximum per muscle across their strides (no MVC trials)

#### To check once we download the data
- [ ] Does the Excel file really leave out TA? If so, ankle co-contraction (TA vs. GAS) needs the MAT or C3D files.
- [ ] How the stroke files mark the affected (paretic) side.
- [ ] Per-participant walking speed (Supplementary Table 5 of the paper), needed to account for speed.
- [ ] Stroke data were not screened for outliers in the MAT files (the authors did this for able-bodied data only).

## Analysis plan: what we will do with the data

**1. Choose participants**
- Stroke: the 47 participants with EMG. Analyze the paretic and non-paretic legs separately.
- Able-bodied: the 111 with EMG. To age-match, pair each stroke participant with the closest-in-age able-bodied adult (or restrict to the same age range). Use the average of the left and right legs.
- Sensitivity check: rerun the analysis without the 3 stroke participants who needed hand support (TVC48, TVC51, TVC54).

**2. Load and organize the EMG**
- Use the stride-normalized EMG envelopes (1000 points = one gait cycle, from heel strike to the next heel strike).
- Muscle pairs:
  - Knee: vastus lateralis vs. biceps femoris, and vastus lateralis vs. semitendinosus.
  - Ankle: tibialis anterior vs. gastrocnemius. This needs the MAT files if the Excel file has no TA data.
- Use toe-off events to split each stride into stance and swing.

**3. Calculate outcomes for every stride, then average per participant**
- **Co-contraction index (CCI)**, using the Falconer & Winter (1985) method: `CCI = 2 × Σ min(A, B) / Σ (A + B) × 100`, where A and B are the two muscles' envelopes. Calculate it for the whole gait cycle and separately for stance and swing.
- **Activation timing:** count a muscle as "on" when its envelope is above a set threshold (e.g., 25% of its maximum). Record onset, offset and the % of the gait cycle it is active.
- **Overall pattern:** plot the average envelope for each group over the gait cycle so differences can be seen.

**4. Handle walking speed (our biggest uncertainty)**
- **Within-person comparison:** compare the paretic and non-paretic legs of the same stroke survivor. Both legs walk at the same speed, so speed can't explain a difference between them.
- **Statistical control:** fit a regression model, CCI ~ group + walking speed + age. Speed comes from Supplementary Table 5 of the paper.
- **Speed-matched subset:** compare stroke survivors only with able-bodied adults who walked at similar speeds. This works only if enough slow able-bodied walkers exist, so we'll check the overlap first.

**5. Statistics**
- Each participant counts once: average their strides before testing.
- Stroke vs. able-bodied: Mann–Whitney U test (or the regression model above).
- Paretic vs. non-paretic: Wilcoxon signed-rank test.
- Several muscle pairs are tested, so adjust p-values (Holm correction).

**6. Figures**
- Average EMG envelopes over the gait cycle for each group and leg (mean ± SD shading).
- Box plots of CCI by group and leg.
- Scatter plot of CCI vs. walking speed, colored by group. This is the key figure for the speed question.

**Limitations to acknowledge**
- EMG is scaled to each person's own maximum, not to a maximal contraction. CCI therefore describes the *overlap* of two muscles' activity, not absolute muscle effort.
- All stroke participants were within 5 months of their stroke, so the results may not apply to chronic stroke.
- Able-bodied adults walked only at their own comfortable speed, so few may walk as slowly as the stroke group.

## Other candidate considered (not chosen)

<details>
<summary>Sleep stages and age (Sleep-EDF Expanded)</summary>

### Biomedical problem
Deep sleep (N3/slow-wave) and REM sleep are thought to decline with age, and this loss is linked to worse memory consolidation, mood regulation, and metabolic health in older adults. If true, automatic sleep-stage classifiers (usually trained/validated mostly on younger subjects) may perform worse in older adults — whose EEG shows lower-amplitude slow waves and less-distinct REM signatures — meaning current tools could systematically misclassify or underdetect deep/REM sleep in exactly the population where tracking it matters most (e.g., for dementia or cardiovascular risk screening).

### Research question
Does the time spent in deep sleep and REM sleep decline with age, and does automatic sleep-stage scoring work as well in older adults?

### Dataset
Sleep-EDF Expanded (PhysioNet): overnight sleep recordings from healthy adults aged 25–101, scored by experts.  
Link: https://physionet.org/content/sleep-edfx/1.0.0/

### Biggest uncertainty
There are fewer participants at the oldest ages.

</details>
