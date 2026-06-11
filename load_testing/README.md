# HireMind Load Testing Framework

This directory contains reusable load-testing resources for Phase 3 performance validation.

## Included tools

- Locust: Python-based user behavior simulation for candidate upload, matching, recruiter workflows, and multi-agent workflows.
- k6: JavaScript-based load testing for scenario-driven throughput and latency measurement.

## Supported scenarios

1. Candidate Resume Upload
2. Candidate Matching
3. Recruiter Workflow
4. Multi-Agent Workflow

## Setup

1. Install requirements for Locust:

```powershell
cd load_testing
py -3 -m pip install -r requirements.txt
```

2. Install k6 separately:

- Windows: https://k6.io/docs/getting-started/installation/#windows
- macOS / Linux: use the package manager or install script

## Environment variables

- `BASE_URL`: base URL for the backend service (default: `http://localhost:8000`)
- `PERF_TEST_EMAIL`: login email for performance test user
- `PERF_TEST_PASSWORD`: login password for performance test user
- `PERF_TEST_FULL_NAME`: name for the performance test user
- `PERF_TEST_COMPANY_NAME`: company name for the performance test user
- `PERF_SCENARIO`: k6 scenario name for the `scenarios.js` script

## Locust usage

```powershell
cd load_testing
py -3 -m locust -f locustfile.py --headless -u 100 -r 10 --run-time 5m --csv=results/locust_100
```

For larger throughput tests, change the user count:

```powershell
py -3 -m locust -f locustfile.py --headless -u 500 -r 20 --run-time 5m --csv=results/locust_500
py -3 -m locust -f locustfile.py --headless -u 1000 -r 50 --run-time 5m --csv=results/locust_1000
py -3 -m locust -f locustfile.py --headless -u 5000 -r 100 --run-time 5m --csv=results/locust_5000
```

To run a specific scenario, use the `--user-class` argument with one of the user classes from `locustfile.py`:

- `CandidateUploadUser`
- `CandidateMatchingUser`
- `RecruiterWorkflowUser`
- `MultiAgentWorkflowUser`

Example:

```powershell
py -3 -m locust -f locustfile.py --headless --user-class CandidateUploadUser -u 500 -r 50 --run-time 5m --csv=results/locust_candidate_upload_500
```

## k6 usage

```powershell
cd load_testing\k6
k6 run -e BASE_URL=http://localhost:8000 -e PERF_TEST_EMAIL=perf+recruiter@hiremind.test -e PERF_TEST_PASSWORD=PerfTest123! -e PERF_SCENARIO=multi_agent_workflow scenarios.js
```

## Result templates

Use the report templates in `docs/` after running the tests to populate measured benchmark values and bottleneck analysis.


---

## 👨‍💻 Developer
**Developed by abdelkreem abdelhaleem frahat**

* **LinkedIn:** [abdelkreem abdelhaleem frahat](https://www.linkedin.com/in/abdelkreem-frahat-160g/)
* **Phone:** 01025453847
