import uuid
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_auth_regression():
    # 1. Generate unique email
    test_email = f"regression_{uuid.uuid4().hex[:8]}@hiremind.test"
    test_password = "SecurePassword123!"
    
    payload = {
        "email": test_email,
        "password": test_password,
        "full_name": "Regression Tester",
        "role": "company",
        "company_name": "HireMind Regression"
    }
    
    # 2. Register first time - Should succeed 200/201
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code in (200, 201), f"First registration failed: {res1.text}"
    
    # 3. Register second time - Should fail with 409 Conflict (not 500)
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409, f"Expected 409 Conflict, got: {res2.status_code} {res2.text}"
    
    # 4. Login with registered user - Should succeed 200
    res3 = client.post("/api/auth/login", json={"email": test_email, "password": test_password})
    assert res3.status_code == 200, f"Login failed: {res3.text}"
    token = res3.json().get("access_token")
    assert token is not None, "Session token missing"

if __name__ == "__main__":
    print("Running auth regression test...")
    test_auth_regression()
    print("All tests passed successfully! No 500 errors detected.")
