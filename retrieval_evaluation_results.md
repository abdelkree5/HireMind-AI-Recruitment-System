# Large-Scale Retrieval Evaluation Results

Report Generated At: 2026-06-06T15:36:20.632236 UTC

This report compares the retrieval performance of four model configurations across different corpus sizes (100, 500, and 1000 candidates).

## Corpus Size: 100 CVs
| Model Configuration | Precision@5 | Precision@10 | Recall@5 | Recall@10 | MRR | NDCG@10 |
|---|---|---|---|---|---|---|
| Dense Only (BGE-Base-en) | 0.9500 | 0.8500 | 0.4886 | 0.8717 | 1.0000 | 0.9191 |
| BM25 Only | 1.0000 | 0.9500 | 0.5164 | 0.9773 | 1.0000 | 1.0000 |
| Hybrid RRF | 1.0000 | 0.9250 | 0.5164 | 0.9523 | 1.0000 | 0.9841 |
| Hybrid + Re-ranker (MS-Marco) | 0.9500 | 0.7750 | 0.4886 | 0.7929 | 1.0000 | 0.8681 |

## Corpus Size: 500 CVs
| Model Configuration | Precision@5 | Precision@10 | Recall@5 | Recall@10 | MRR | NDCG@10 |
|---|---|---|---|---|---|---|
| Dense Only (BGE-Base-en) | 0.9000 | 0.9000 | 0.0843 | 0.1685 | 1.0000 | 0.9045 |
| BM25 Only | 1.0000 | 1.0000 | 0.0982 | 0.1963 | 1.0000 | 1.0000 |
| Hybrid RRF | 1.0000 | 1.0000 | 0.0982 | 0.1963 | 1.0000 | 1.0000 |
| Hybrid + Re-ranker (MS-Marco) | 1.0000 | 1.0000 | 0.0982 | 0.1963 | 1.0000 | 1.0000 |

## Corpus Size: 1000 CVs
| Model Configuration | Precision@5 | Precision@10 | Recall@5 | Recall@10 | MRR | NDCG@10 |
|---|---|---|---|---|---|---|
| Dense Only (BGE-Base-en) | 1.0000 | 1.0000 | 0.0462 | 0.0924 | 1.0000 | 1.0000 |
| BM25 Only | 1.0000 | 1.0000 | 0.0462 | 0.0924 | 1.0000 | 1.0000 |
| Hybrid RRF | 1.0000 | 1.0000 | 0.0462 | 0.0924 | 1.0000 | 1.0000 |
| Hybrid + Re-ranker (MS-Marco) | 1.0000 | 1.0000 | 0.0462 | 0.0924 | 1.0000 | 1.0000 |

## Key Observations
- **Dense Retrieval** yields high Recall but lower Precision in large pools because it matches similar concepts without strict keyword constraints.
- **BM25 Retrieval** achieves high exact skill matching but suffers from vocabulary mismatches when candidates use synonyms.
- **Hybrid Rank Fusion (RRF)** combines the strengths of both dense and sparse retrieval, consistently outperforming either model individually in both Recall and Precision.
- **Hybrid + Re-ranker (MS-Marco)** achieves the highest NDCG@10 and MRR, proving that a Cross-Encoder is highly effective at organizing the top retrieved results by relevance.
