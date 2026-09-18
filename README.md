# BMEN-600-Project

## Team 3
Matthew Christoffersen  
Dylan Lam  
Yohan Min  
Perpetual Ogedegbe  

## Candidate #1:

### Biomedical problem
Deep sleep (N3/slow-wave) and REM sleep are thought to decline with age, and this loss is linked to worse memory consolidation, mood regulation, and metabolic health in older adults. If true, automatic sleep-stage classifiers (usually trained/validated mostly on younger subjects) may perform worse in older adults — whose EEG shows lower-amplitude slow waves and less-distinct REM signatures — meaning current tools could systematically misclassify or underdetect deep/REM sleep in exactly the population where tracking it matters most (e.g., for dementia or cardiovascular risk screening).

### Research Question
Does the time spent in deep sleep and REM sleep decline with age, and does automatic sleep-stage scoring work as well in older adults? 

### Dataset
Sleep-EDF Expanded (PhysioNet): overnight sleep recordings from healthy adults aged 25–101, scored by experts.   
Link: https://physionet.org/content/sleep-edfx/1.0.0/

### Biggest Uncertainty
There are fewer participants at the oldest ages.

## Candidate #2 

### Biomedical problem
Stroke can damage the neural pathways that coordinate reciprocal muscle activation, so survivors may show abnormal co-contraction (agonist/antagonist muscles firing together) and mistimed activation of thigh and shank muscles on the affected side during gait — contributing to stiff, inefficient, unsafe walking. The open question is whether this reflects stroke's direct effect on motor control, or is just a byproduct of walking slower (since speed alone affects co-contraction even in healthy adults).

### Question
Compared with age-matched healthy adults, do stroke survivors show more co-contraction and altered activation timing of the thigh and shin muscles on their affected side during walking? 

### Dataset
50 stroke survivors (ages 19–85) and 138 healthy adults (ages 21–86). Van Criekinge et al., 2023, Scientific Data: "A full-body motion capture gait dataset of 138 able-bodied adults across the life span and 50 stroke survivors."  
Link: https://springernature.figshare.com/collections/A_full-body_motion_capture_gait_dataset_of_138_able-bodied_adults_across_the_life_span_and_50_stroke_survivors/6503791/1

### Biggest uncertainty
Whether any difference you find comes from the stroke itself or just from walking slower. 

We are currently leaning towards Candidate #2
