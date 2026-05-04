import os
import glob
from backend.app.services.cv_parser import extract_candidate_profile_text

cv_files = glob.glob("test_cvs/*.txt")
for file_path in cv_files:
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    filename = os.path.basename(file_path)
    print(f"\n======================================")
    print(f"Testing CV: {filename}")
    try:
        profile_text, skills, raw_text = extract_candidate_profile_text(file_bytes, filename)
        print(f"Skills Extracted: {skills}")
        print(f"Profile Text Length: {len(profile_text)} chars")
        print(f"Status: Success!")
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
    print(f"======================================\n")
