"""Load benchmark: seed N students into a scratch DB and time the hot endpoints.
    DATABASE_URL=sqlite:///./bench.db python bench.py 100000
"""
import sys
import time

from fastapi.testclient import TestClient

import seed
from database import Base, SessionLocal, engine
from main import app

n = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
Base.metadata.create_all(bind=engine)
db = SessionLocal()
t = time.perf_counter()
seed.seed_demo(db)
seed.seed_bulk(db, n)
print(f"seed {n:,} students: {time.perf_counter() - t:.1f}s")
db.close()

c = TestClient(app)
tok = c.post("/api/auth/login", json={"email": "admin@quest-portal.local", "password": seed.DEMO_PASSWORD}).json()["access_token"]
h = {"Authorization": f"Bearer {tok}"}


def timed(label, path, runs=5):
    ts = []
    for _ in range(runs):
        t0 = time.perf_counter()
        r = c.get(path, headers=h)
        assert r.status_code == 200, (path, r.text)
        ts.append((time.perf_counter() - t0) * 1000)
    ts.sort()
    print(f"{label:<34} median {ts[len(ts)//2]:7.1f} ms   max {ts[-1]:7.1f} ms")


timed("students page 1 (25)", "/api/students?page=1&page_size=25")
timed("students page 2000", "/api/students?page=2000&page_size=25")
timed("students filter batch+risk", "/api/students?batch=21&risk_level=High")
timed("students search roll prefix", "/api/students?q=21IT-9")
timed("students sort by cgpa desc", "/api/students?sort=cgpa&desc=true")
timed("dashboard summary", "/api/dashboard/summary")
timed("fees list (status=Pending)", "/api/fees?status=Pending")
t = time.perf_counter()
r = c.post("/api/risk/recompute", headers=h)
print(f"risk recompute {r.json()['updated']:,} students: {time.perf_counter() - t:.1f}s")
t = time.perf_counter()
print(c.post("/api/chat", json={"message": "high risk students in batch 21"}, headers=h).json()["answer"][:80], f"({(time.perf_counter()-t)*1000:.0f} ms)")
