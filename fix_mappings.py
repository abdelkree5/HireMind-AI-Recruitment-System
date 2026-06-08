import os
import re

files = [
    'backend/app/services/auth_service.py',
    'backend/app/services/interview_service.py',
    'backend/app/services/recruitment_service.py'
]

pattern = re.compile(r'(?<!\w)(row|candidate_row|job_row|count_row|score_row)\[([\"\'a-zA-Z_]+)\]')
keys_pattern = re.compile(r'(?<!\w)(row|candidate_row|job_row|count_row|score_row)\.keys\(\)')

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = pattern.sub(r'\1._mapping[\2]', content)
    content = keys_pattern.sub(r'\1._mapping.keys()', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print('Done!')
