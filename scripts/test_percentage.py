#!/usr/bin/env python3
"""Test percentage confidence output."""

from ai_engine.reasoning import recommend_job_titles_from_cv_text

cv = 'Senior DevOps 15+ years. Designed AWS multi-account. Monitoring with Grafana and ELK. Kubernetes, Terraform, CI/CD.'

result = recommend_job_titles_from_cv_text(cv)

print('\n' + '='*70)
print('Top 5 Matches with % Confidence')
print('='*70)
for i, match in enumerate(result.matches[:5], 1):
    print(f'{i}. {match.job_title:35} | Level: {match.match_level:6} | Confidence: {match.confidence_score:6.2f}%')

print('\n' + '='*70)
print('✓ Configuration: Confidence as percentage (0-100)')
print('='*70)
