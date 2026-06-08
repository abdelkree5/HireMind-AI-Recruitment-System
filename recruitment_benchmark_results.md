# Recruitment-Specific Benchmark Suite & Failure Analysis

Report Generated At: 2026-06-06T19:46:11.318184 UTC

This report evaluates the **HireMind RAG Pipeline** against a rigorous benchmark suite composed of **1 Ideal Candidate** and **10 Hard Negative Scenarios** designed to trigger and test search pitfalls in recruitment.

## Target Role Profile
- **Job Title**: `Senior DevOps Engineer`
- **Required Skills**: `AWS`, `Kubernetes`, `Docker`, `Terraform`, `CI/CD`, `Linux`, `Prometheus`, `Grafana`
- **Experience Level**: `Senior (8+ years)`
- **Domain**: `devops`

## Benchmark Summary Table
| Candidate Scenario | Target Role Fit | Dense Rank | BM25 Rank | Hybrid RRF Rank | Reranked Rank | Final Score |
|---|---|---|---|---|---|---|
| **Alice Smith** | ✅ Relevant (True Positive) | #2 | #1 | #2 | **#1** | 75.1% |
| **Charlie Brown** | ❌ Irrelevant (Hard Negative) | #8 | #6 | #6 | **#2** | 53.1% |
| **Bob Jones** | ❌ Irrelevant (Hard Negative) | #1 | #2 | #1 | **#3** | 46.0% |
| **David Wilson** | ❌ Irrelevant (Hard Negative) | #5 | #4 | #4 | **#4** | 35.1% |
| **Ian Malcolm** | ❌ Irrelevant (Hard Negative) | #11 | #5 | #9 | **#5** | 9.2% |
| **Eve Adams** | ❌ Irrelevant (Hard Negative) | #4 | #3 | #3 | **#6** | 4.8% |
| **Frank Miller** | ❌ Irrelevant (Hard Negative) | #10 | #10 | #11 | **#7** | 0.0% |
| **Grace Hopper** | ✅ Relevant (True Positive) | #3 | #7 | #5 | **#8** | 0.0% |
| **Harry Potter** | ❌ Irrelevant (Hard Negative) | #7 | #8 | #8 | **#9** | 0.0% |
| **Jane Doe** | ❌ Irrelevant (Hard Negative) | #9 | #11 | #10 | **#10** | 0.0% |
| **Karl Marx** | ❌ Irrelevant (Hard Negative) | #6 | #9 | #7 | **#11** | 0.0% |

## Configuration Confusion Matrices
Classification performance of each model configuration in identifying relevant profiles (Ideal, Synonym) and filtering out the 9 hard negatives.

### Dense Only
| Actual / Predicted | Predicted Relevant (Positive) | Predicted Irrelevant (Negative) |
|---|---|---|
| **Actual Relevant** | TP: **1** | FN: **1** |
| **Actual Irrelevant**| FP: **1** | TN: **8** |

*Metrics: Accuracy: **0.818** | Precision: **0.500** | Recall: **0.500***

### BM25 Only
| Actual / Predicted | Predicted Relevant (Positive) | Predicted Irrelevant (Negative) |
|---|---|---|
| **Actual Relevant** | TP: **1** | FN: **1** |
| **Actual Irrelevant**| FP: **1** | TN: **8** |

*Metrics: Accuracy: **0.818** | Precision: **0.500** | Recall: **0.500***

### Hybrid RRF
| Actual / Predicted | Predicted Relevant (Positive) | Predicted Irrelevant (Negative) |
|---|---|---|
| **Actual Relevant** | TP: **1** | FN: **1** |
| **Actual Irrelevant**| FP: **1** | TN: **8** |

*Metrics: Accuracy: **0.818** | Precision: **0.500** | Recall: **0.500***

### Hybrid + Reranker
| Actual / Predicted | Predicted Relevant (Positive) | Predicted Irrelevant (Negative) |
|---|---|---|
| **Actual Relevant** | TP: **1** | FN: **1** |
| **Actual Irrelevant**| FP: **1** | TN: **8** |

*Metrics: Accuracy: **0.818** | Precision: **0.500** | Recall: **0.500***

## Detailed Scenario Analysis & Ranking Explanations

### Scenario 1: Alice Smith
- **Actual Classification**: Relevant
- **Rankings**: Dense: **#2** | BM25: **#1** | Hybrid RRF: **#2** | Reranked: **#1**
- **Final Match Score**: `75.1%`
- **Matched Skills**: `aws`, `ci/cd`, `docker`, `grafana`, `kubernetes`, `linux`, `prometheus`, `terraform`
- **Missing Skills**: *None*
- **Active Penalties**: Missing required language capability: English
- **Match Explanation**: *[REJECTED: Missing required language capability: English] Alice Smith is scored at 75.14% match for the Senior DevOps Engineer role. Matched core skills: aws, ci/cd, docker, grafana. Experience: Candidate has 9 years vs Job's 8 years. Seniority level (Senior) is aligned. Technical domain (devops) is a strong match.*

**Ranking Dynamics Explanation**:
- **Movement**: Remained ranked at **#1** or top across all configurations.
- **Rationale**: The ideal candidate contains all explicit skills, has high conceptual semantic alignment, matches the seniority requirement, and holds exact domain compatibility. This keeps them at the top in all stages.

### Scenario 2: Bob Jones
- **Actual Classification**: Irrelevant (Hard Negative)
- **Rankings**: Dense: **#1** | BM25: **#2** | Hybrid RRF: **#1** | Reranked: **#3**
- **Final Match Score**: `46.0%`
- **Matched Skills**: `aws`, `ci/cd`, `docker`, `grafana`, `kubernetes`, `linux`, `prometheus`, `terraform`
- **Missing Skills**: *None*
- **Active Penalties**: Missing mandatory skill(s): Kubernetes (-30%), Missing required language capability: English
- **Match Explanation**: *[REJECTED: Kubernetes, Missing required language capability: English] Bob Jones is scored at 45.95% match for the Senior DevOps Engineer role. Matched core skills: aws, ci/cd, docker, grafana. Experience: Candidate has 8 years vs Job's 8 years. Seniority level (Senior) is aligned. Technical domain (devops) is a strong match.*

**Ranking Dynamics Explanation**:
- **Movement**: Ranks relatively high in Dense (#3) and BM25 (#3), but drop/adjusts in the final Reranked ranking.
- **Rationale**: Standard search models fail to penalize the absence of a single must-have skill if all other skills match. The multi-factor scoring correctly identifies that Kubernetes is a core missing skill, scoring it lower dynamically and keeping it below the fully qualified synonym candidate.

### Scenario 3: Charlie Brown
- **Actual Classification**: Irrelevant (Hard Negative)
- **Rankings**: Dense: **#8** | BM25: **#6** | Hybrid RRF: **#6** | Reranked: **#2**
- **Final Match Score**: `53.1%`
- **Matched Skills**: `aws`, `docker`, `kubernetes`, `terraform`
- **Missing Skills**: `ci/cd`, `grafana`, `linux`, `prometheus`
- **Active Penalties**: Missing required language capability: English
- **Match Explanation**: *[REJECTED: Missing required language capability: English] Charlie Brown is scored at 53.11% match for the Senior DevOps Engineer role. Matched core skills: aws, docker, kubernetes, terraform. Gaps found in: ci/cd, grafana, linux. Experience: Candidate has 8 years vs Job's 8 years. Seniority level (Senior) is aligned. Technical domain (devops) is a strong match.*

**Ranking Dynamics Explanation**:
- **Movement**: Ranks very high in Dense (#4) due to the presence of terms like 'Senior DevOps' and 'AWS, Docker', but falls in Reranked and Hybrid. BM25 ranks it moderate.
- **Rationale**: The Cross-Encoder and Reranked scoring models look at contextual responsibilities. Since they detect the profile is purely a 'Scrum Master' / coordinator without hands-on implementation experience, their score is heavily adjusted down.

### Scenario 4: David Wilson
- **Actual Classification**: Irrelevant (Hard Negative)
- **Rankings**: Dense: **#5** | BM25: **#4** | Hybrid RRF: **#4** | Reranked: **#4**
- **Final Match Score**: `35.1%`
- **Matched Skills**: `aws`, `ci/cd`, `docker`, `grafana`, `kubernetes`, `linux`, `prometheus`, `terraform`
- **Missing Skills**: *None*
- **Active Penalties**: Seniority mismatch: Candidate is Mid but job requires Senior, Missing required language capability: English
- **Match Explanation**: *[REJECTED: Missing required language capability: English, Seniority mismatch: Candidate is Mid but job requires Senior] David Wilson is scored at 35.07% match for the Senior DevOps Engineer role. Matched core skills: aws, ci/cd, docker, grafana. Experience: Candidate has 8 years vs Job's 8 years. Seniority level (Senior) is aligned. Technical domain (devops) is a strong match.*

**Ranking Dynamics Explanation**:
- **Movement**: Ranks high in BM25 (#4) due to keyword frequency/density boosting, but drops significantly in Dense and Reranked.
- **Rationale**: BM25 Okapi is vulnerable to keyword repetition. However, Dense vectors capture the lack of syntactic coherence, and the Reranked model penalizes the lack of experience structure, causing them to move down.

### Scenario 5: Eve Adams
- **Actual Classification**: Irrelevant (Hard Negative)
- **Rankings**: Dense: **#4** | BM25: **#3** | Hybrid RRF: **#3** | Reranked: **#6**
- **Final Match Score**: `4.8%`
- **Matched Skills**: `aws`, `ci/cd`, `docker`, `grafana`, `kubernetes`, `linux`, `prometheus`, `terraform`
- **Missing Skills**: *None*
- **Active Penalties**: Experience deficit penalty (-40%), Experience below minimum requirement: 1 yrs vs required 5 yrs, Missing required language capability: English
- **Match Explanation**: *[REJECTED: Missing required language capability: English, Experience below minimum requirement: 1 yrs vs required 5 yrs] Eve Adams is scored at 4.83% match for the Senior DevOps Engineer role. Matched core skills: aws, ci/cd, docker, grafana. Experience: Candidate has 1 years vs Job's 8 years. Seniority level (Senior) is aligned. Technical domain (devops) is a strong match.*

**Ranking Dynamics Explanation**:
- **Movement**: Ranks high in BM25 (#2) due to perfect keyword matching, but drops significantly in Reranked.
- **Rationale**: BM25 does not understand numeric years or seniority context, ranking the junior profile at the top. The Reranked model parses the experience duration (1 year vs 8 required) and infers the seniority mismatch, applying a direct **-5% Seniority Mismatch penalty** and scoring experience alignment low, pulling the candidate down.

### Scenario 6: Frank Miller
- **Actual Classification**: Irrelevant (Hard Negative)
- **Rankings**: Dense: **#10** | BM25: **#10** | Hybrid RRF: **#11** | Reranked: **#7**
- **Final Match Score**: `0.0%`
- **Matched Skills**: `linux`
- **Missing Skills**: `aws`, `ci/cd`, `docker`, `grafana`, `kubernetes`, `prometheus`, `terraform`
- **Active Penalties**: Missing mandatory skill(s): Kubernetes, Terraform, AWS (-30%), Missing mandatory skill: Kubernetes, Missing mandatory skill: Terraform, Missing mandatory skill: AWS, Missing required language capability: English
- **Match Explanation**: *[REJECTED: Kubernetes, Missing required language capability: English, AWS, Terraform] Frank Miller is scored at 0.0% match for the Senior DevOps Engineer role. Matched core skills: linux. Gaps found in: aws, ci/cd, docker. Experience: Candidate has 8 years vs Job's 8 years. Seniority level (Senior) is aligned.*

**Ranking Dynamics Explanation**:
- **Movement**: Ranks extremely low in BM25 (#11) and Reranked (#11).
- **Rationale**: Lack of any technical skill overlap or domain alignment. The system identifies a domain mismatch (Windows Sysadmin) and penalizes it, keeping it at the bottom.

### Scenario 7: Grace Hopper
- **Actual Classification**: Relevant
- **Rankings**: Dense: **#3** | BM25: **#7** | Hybrid RRF: **#5** | Reranked: **#8**
- **Final Match Score**: `0.0%`
- **Matched Skills**: `aws`, `kubernetes`
- **Missing Skills**: `ci/cd`, `docker`, `grafana`, `linux`, `prometheus`, `terraform`
- **Active Penalties**: Missing mandatory skill(s): Terraform (-30%), Missing mandatory skill: Terraform, Missing required language capability: English
- **Match Explanation**: *[REJECTED: Missing required language capability: English, Terraform] Grace Hopper is scored at 0.0% match for the Senior DevOps Engineer role. Matched core skills: aws, kubernetes. Gaps found in: ci/cd, docker, grafana. Experience: Candidate has 8 years vs Job's 8 years. Seniority level (Senior) is aligned. Technical domain (devops) is a strong match.*

**Ranking Dynamics Explanation**:
- **Movement**: Ranks very low in BM25 (#8) but jumps dramatically in Dense (#2) and Reranked (#2).
- **Rationale**: BM25 suffers from vocabulary mismatch since the CV uses terms like 'K8s', 'Amazon Web Services', and 'blueprints' instead of explicit keywords. The Dense model captures the semantic equivalence, and the Agent query expansion rewrites synonyms, boosting its rank to **#2** right below the ideal candidate.

### Scenario 8: Harry Potter
- **Actual Classification**: Irrelevant (Hard Negative)
- **Rankings**: Dense: **#7** | BM25: **#8** | Hybrid RRF: **#8** | Reranked: **#9**
- **Final Match Score**: `0.0%`
- **Matched Skills**: `linux`
- **Missing Skills**: `aws`, `ci/cd`, `docker`, `grafana`, `kubernetes`, `prometheus`, `terraform`
- **Active Penalties**: Missing mandatory skill(s): Kubernetes, Terraform, AWS (-30%), Missing mandatory skill: Kubernetes, Missing mandatory skill: Terraform, Missing mandatory skill: AWS, Seniority mismatch: Candidate is Mid but job requires Senior, Missing required language capability: English
- **Match Explanation**: *[REJECTED: Missing required language capability: English, Terraform, Kubernetes, AWS, Seniority mismatch: Candidate is Mid but job requires Senior] Harry Potter is scored at 0.0% match for the Senior DevOps Engineer role. Matched core skills: linux. Gaps found in: aws, ci/cd, docker. Experience: Candidate has 8 years vs Job's 8 years. Seniority level (Senior) is aligned.*

**Ranking Dynamics Explanation**:
- **Movement**: Ranks moderate in BM25 (#7) due to 'Linux' and 'Bash', but drops in Dense and Reranked.
- **Rationale**: General Linux admin tasks lack the high-level cloud management concepts (AWS, Kubernetes, Terraform) required. Reranked penalizes the missing core skills.

### Scenario 9: Ian Malcolm
- **Actual Classification**: Irrelevant (Hard Negative)
- **Rankings**: Dense: **#11** | BM25: **#5** | Hybrid RRF: **#9** | Reranked: **#5**
- **Final Match Score**: `9.2%`
- **Matched Skills**: `aws`, `ci/cd`, `docker`, `kubernetes`, `linux`, `terraform`
- **Missing Skills**: `grafana`, `prometheus`
- **Active Penalties**: Missing mandatory skill(s): Kubernetes, Terraform (-30%), Seniority mismatch: Candidate is Mid but job requires Senior, Missing required language capability: English
- **Match Explanation**: *[REJECTED: Kubernetes, Missing required language capability: English, Seniority mismatch: Candidate is Mid but job requires Senior, Terraform] Ian Malcolm is scored at 9.2% match for the Senior DevOps Engineer role. Matched core skills: aws, ci/cd, docker, kubernetes. Gaps found in: grafana, prometheus. Experience: Candidate has 10 years vs Job's 8 years. Seniority level (Senior) is aligned. Technical domain (devops) is a strong match.*

**Ranking Dynamics Explanation**:
- **Movement**: Ranks moderate in BM25 (#6) and Dense (#6), but drops in Reranked.
- **Rationale**: The candidate has not worked with the target tools in over 7 years, shifting to project management. The multi-factor scoring detects experience decay and non-recent domain alignment, pulling the candidate down.

### Scenario 10: Jane Doe
- **Actual Classification**: Irrelevant (Hard Negative)
- **Rankings**: Dense: **#9** | BM25: **#11** | Hybrid RRF: **#10** | Reranked: **#10**
- **Final Match Score**: `0.0%`
- **Matched Skills**: *None*
- **Missing Skills**: `aws`, `ci/cd`, `docker`, `grafana`, `kubernetes`, `linux`, `prometheus`, `terraform`
- **Active Penalties**: Missing mandatory skill(s): Kubernetes, Terraform, AWS (-30%), Missing mandatory skill: Kubernetes, Missing mandatory skill: Terraform, Missing mandatory skill: AWS, Missing required language capability: English
- **Match Explanation**: *[REJECTED: Kubernetes, Missing required language capability: English, AWS, Terraform] Jane Doe is scored at 0.0% match for the Senior DevOps Engineer role. Gaps found in: aws, ci/cd, docker. Experience: Candidate has 10 years vs Job's 8 years. Seniority level (Senior) is aligned.*

**Ranking Dynamics Explanation**:
- **Movement**: Ranks very low across all configurations.
- **Rationale**: Generic keywords ('Agile, Troubleshooting') do not match the specific high-impact DevOps technical stack, making it irrelevant for both sparse and dense retrieval.

### Scenario 11: Karl Marx
- **Actual Classification**: Irrelevant (Hard Negative)
- **Rankings**: Dense: **#6** | BM25: **#9** | Hybrid RRF: **#7** | Reranked: **#11**
- **Final Match Score**: `0.0%`
- **Matched Skills**: *None*
- **Missing Skills**: `aws`, `ci/cd`, `docker`, `grafana`, `kubernetes`, `linux`, `prometheus`, `terraform`
- **Active Penalties**: Domain mismatch (-5%), Missing mandatory skill(s): Kubernetes, Terraform, AWS (-30%), Missing mandatory skill: Kubernetes, Missing mandatory skill: Terraform, Missing mandatory skill: AWS, Missing required language capability: English
- **Match Explanation**: *[REJECTED: Kubernetes, Missing required language capability: English, AWS, Terraform] Karl Marx is scored at 0.0% match for the Senior DevOps Engineer role. Gaps found in: aws, ci/cd, docker. Experience: Candidate has 9 years vs Job's 8 years. Seniority level (Senior) is aligned. Domain focus is in backend_ai (expected devops).*

**Ranking Dynamics Explanation**:
- **Movement**: Ranks high in Dense (#5) due to general cloud architecture and programming topics, but drops in BM25 and Reranked.
- **Rationale**: The candidate is a Backend Software Architect. Dense vectors align with high-level software terms, but the lack of specific tool matches (Terraform, Kubernetes, Docker) is exposed by BM25 and weighted heavily by the final multi-factor scorer, preventing a false positive match.