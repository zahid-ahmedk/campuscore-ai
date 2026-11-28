import seed

PNG = seed._png()


def pay(client, headers, **over):
    data = {"category": "Examination Fee", "amount": "5000", "challan_no": "HBL-TEST-001", **over}
    files = {"receipt": over.pop("_file", ("slip.png", PNG, "image/png"))} if "_file" not in data else {"receipt": data.pop("_file")}
    data.pop("_file", None)
    return client.post("/api/fees/payments", data=data, files=files, headers=headers)


def test_requires_auth(client):
    assert client.get("/api/students").status_code == 401
    assert client.post("/api/auth/login", json={"email": "x@y.z", "password": "bad"}).status_code == 401


def test_roles(client, student, clerk, admin):
    assert client.get("/api/students", headers=student).status_code == 403
    assert client.get("/api/students", headers=clerk).status_code == 200
    assert client.post("/api/staff", json={}, headers=clerk).status_code in (403, 422)
    r = client.get("/api/students/21IT-98/profile", headers=student)
    assert r.status_code == 403  # students see only themselves
    assert client.get("/api/students/21IT-95/profile", headers=student).status_code == 200


def test_pagination(client, clerk):
    r = client.get("/api/students?page=1&page_size=2", headers=clerk).json()
    assert len(r["items"]) == 2 and r["total"] == 4 and r["pages"] == 2
    assert client.get("/api/students?page_size=1000", headers=clerk).status_code == 422


def test_receipt_validation(client, clerk):
    bad_ext = client.post("/api/fees/payments", headers=clerk, data={
        "roll_no": "21IT-70", "category": "Examination Fee", "amount": "100", "challan_no": "ABC-111"},
        files={"receipt": ("a.exe", b"MZ", "application/octet-stream")})
    assert bad_ext.status_code == 400
    spoof = client.post("/api/fees/payments", headers=clerk, data={
        "roll_no": "21IT-70", "category": "Examination Fee", "amount": "100", "challan_no": "ABC-112"},
        files={"receipt": ("a.png", b"not really a png", "image/png")})
    assert spoof.status_code == 400
    custom_empty = client.post("/api/fees/payments", headers=clerk, data={
        "roll_no": "21IT-70", "category": "Custom", "custom_category": "", "amount": "100", "challan_no": "ABC-113"},
        files={"receipt": ("a.png", PNG, "image/png")})
    assert custom_empty.status_code == 400
    bad_challan = client.post("/api/fees/payments", headers=clerk, data={
        "roll_no": "21IT-70", "category": "Examination Fee", "amount": "100", "challan_no": "a b!"},
        files={"receipt": ("a.png", PNG, "image/png")})
    assert bad_challan.status_code == 400


def test_submit_verify_flow(client, student, clerk):
    r = client.post("/api/fees/payments", headers=student, data={
        "category": "Custom", "custom_category": "Library fine", "amount": "750", "challan_no": "hbl-flow-1"},
        files={"receipt": ("slip.webp", b"RIFF\x00\x00\x00\x00WEBPVP8 ", "image/webp")})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    assert r.json()["challan_no"] == "HBL-FLOW-1" and r.json()["status"] == "Pending"
    dup = client.post("/api/fees/payments", headers=student, data={
        "category": "Examination Fee", "amount": "10", "challan_no": "HBL-FLOW-1"},
        files={"receipt": ("s.png", PNG, "image/png")})
    assert dup.status_code == 409
    assert client.get(f"/api/fees/payments/{pid}/receipt", headers=student).status_code == 200
    assert client.patch(f"/api/fees/payments/{pid}/verify", json={"status": "Verified"}, headers=student).status_code == 403
    assert client.patch(f"/api/fees/payments/{pid}/verify", json={"status": "Rejected"}, headers=clerk).status_code == 400
    ok = client.patch(f"/api/fees/payments/{pid}/verify", json={"status": "Verified"}, headers=clerk)
    assert ok.status_code == 200 and ok.json()["status"] == "Verified"


def test_fee_balance_updates_on_verification(client, clerk):
    # 21IT-98 has 20,000 paid of 45,000 and a pending 10,000 submission.
    pays = client.get("/api/fees/payments?status=Pending&q=21IT-98", headers=clerk).json()["items"]
    assert pays, "seeded pending payment missing"
    client.patch(f"/api/fees/payments/{pays[0]['id']}/verify", json={"status": "Verified"}, headers=clerk)
    data = client.get("/api/fees/student/21IT-98", headers=clerk).json()
    assert data["totals"]["paid"] == 30000 and data["totals"]["balance"] == 15000


def test_overpayment_blocked(client, clerk):
    r = client.post("/api/fees/payments", headers=clerk, data={
        "roll_no": "21IT-100", "category": "Semester Tuition Fee", "amount": "100", "challan_no": "HBL-OVER-1"},
        files={"receipt": ("a.png", PNG, "image/png")})
    assert r.status_code == 400  # already fully paid -> no open due to link; or exceeds balance


def test_chatbot_scoped(client, student, clerk):
    s = client.post("/api/chat", json={"message": "show high risk students"}, headers=student).json()
    assert s["source"] == "rules" and "21IT-95" in s["answer"] and "21IT-70" not in s["answer"]
    c = client.post("/api/chat", json={"message": "how many high risk students in batch 21?"}, headers=clerk).json()
    assert "high-risk" in c["answer"] or "High" in c["answer"]
    f = client.post("/api/chat", json={"message": "outstanding fees"}, headers=clerk).json()
    assert "PKR" in f["answer"]


def test_summary(client, clerk):
    s = client.get("/api/dashboard/summary", headers=clerk).json()
    assert s["students"] == 4 and s["fees"]["billed"] == 180000
