import os

os.makedirs("test_cvs", exist_ok=True)

cvs = {
    "ahmed_backend.txt": """Ahmed Mohamed
Full Stack / Backend Developer
Location: Cairo, Egypt
Email: ahmed@example.com

Summary
Passionate backend developer with 4 years of experience building scalable microservices and APIs using Python, FastAPI, and PostgreSQL.

Experience
Senior Backend Engineer | Tech Solutions
- Designed and developed high-performance REST APIs using FastAPI and Django.
- Managed PostgreSQL database optimizations and migrations.
- Implemented background tasks using Celery and Redis.
- Dockerized applications and set up CI/CD pipelines.

Skills
Python, FastAPI, Django, PostgreSQL, Docker, Redis, REST APIs, Git, Linux
""",
    
    "sarah_frontend.txt": """Sarah Ahmed
Frontend Web Developer
Email: sarah@example.com

Summary
Frontend developer with 2 years of experience in designing and developing modern, responsive web applications using React and Vite.

Experience
Frontend Developer | Web Soft
- Developed user interfaces using React.js and TailwindCSS.
- Consumed APIs and integrated them with the interactive UI.
- Optimized application performance for speed across all devices.
- Wrote tests using Jest and RTL.

Skills
React, JavaScript, HTML, CSS, TailwindCSS, Vite, Redux, Git
""",

    "omar_data_scientist.txt": """Omar Ali
Data Scientist & Machine Learning Engineer
Email: omar@example.com

Profile
Data Scientist with a master's degree in Computer Science. Proficient in developing predictive models and analyzing large datasets.

Experience
Data Scientist | Data Minds Inc
- Built machine learning models for customer churn prediction using Scikit-Learn and XGBoost.
- Performed NLP tasks including sentiment analysis with HuggingFace Transformers and PyTorch.
- Analyzed data using Pandas, NumPy, and SQL.
- Visualized results with Matplotlib and Tableau.

Skills
Python, Machine Learning, PyTorch, Scikit-Learn, NLP, Transformers, Pandas, SQL, Data Visualization
""",

    "mahmoud_devops.txt": """Mahmoud Hassan
DevOps & Cloud Engineer
Email: mahmoud@example.com

Summary
Experienced DevOps engineer focused on cloud infrastructure, CI/CD, and automation.

Experience
Cloud Engineer | CloudTech
- Provisioned infrastructure on AWS using Terraform.
- Managed Kubernetes clusters and deployed microservices.
- Automated testing and deployment workflows via GitHub Actions.
- Monitored systems with Prometheus and Grafana.

Skills
AWS, Kubernetes, Docker, Terraform, CI/CD, GitHub Actions, Linux, Bash, Prometheus
""",

    "nour_mobile.txt": """Nour Mostafa
Mobile App Developer (Flutter)
Email: nour@example.com

Objective
Mobile application developer specialized in Flutter, striving to develop engaging applications for both Android and iOS platforms.

Experience
Mobile Developer | Appify
- Developed cross-platform applications using the Flutter framework and Dart.
- Integrated applications with Firebase databases.
- Managed application state using Provider and Riverpod.
- Deployed applications to Google Play and the App Store.

Skills
Flutter, Dart, Firebase, RESTful APIs, UI/UX, Git
"""
}

for filename, content in cvs.items():
    with open(os.path.join("test_cvs", filename), "w", encoding="utf-8") as f:
        f.write(content)

print("Created 5 test CVs successfully.")
