# BMEN-600-Project

## Team 3
Matthew Christoffersen  
Dylan Lam  
Yohan Min  
Perpetual Ogedegbe  

## Project: Muscle activity during walking after stroke

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
