"""End-to-end smoke test against the real app, no server needed."""
import secrets

from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)
c.__enter__()          # fire lifespan: create_all + seed
ok = lambda r: (r.status_code, r.json())

print("health:", c.get("/health").status_code)

# 0. an account: project endpoints are members-only, so the smoke test signs
# up like any other user. Throwaway address, throwaway password.
email = f"smoke-{secrets.token_hex(4)}@example.com"
reg = c.post("/auth/register", json={"email": email, "password": secrets.token_urlsafe(20)})
c.headers["authorization"] = "Bearer " + reg.json()["token"]
print("account:", reg.status_code, email)

# 1. recommendation
r = c.get("/plans/recommend", params={"plot_size_sqft": 2000, "budget_max": 6500000,
                                      "family_members": 4, "elderly_residents": 1,
                                      "theme": "warm contemporary"})
recs = r.json()["results"]
print("recommend:", r.status_code, [(x["name"], x["match_score"], x["why"][:1]) for x in recs])

# 2. create project from the top plan
r = c.post("/projects", json={
    "name": "Chennai demo", "plan_id": recs[0]["plan_id"],
    "brief": {"plot": {"w": 40, "h": 50}, "budget_max": 4500000, "family_members": 4,
              "elderly_residents": 1, "children": 2, "theme": "warm contemporary",
              "region": "Chennai", "required_spaces": ["living","kitchen","dining"]}})
print("create:", r.status_code)
pid = r.json()["id"]

# 3. full propagation
a = c.get(f"/projects/{pid}/analysis").json()
print("built_up:", a["takeoff"]["built_up_sqft"], "fsi:", a["takeoff"]["fsi"],
      "cover:", a["takeoff"]["ground_coverage"])
print("cost total:", a["cost"]["total"], "source:", a["cost"]["rate_source"])
print("blocking:", a["compliance"]["blocking_count"],
      "| readiness:", a["readiness"]["composite"], a["readiness"]["verdict"])
for f in a["compliance"]["findings"]:
    if f["outcome"] == "LIKELY_FAIL":
        print("   FAIL:", f["rule_title"], "-", f["explanation"][:90])

# 4. what-if: add a fourth bedroom
r = c.post(f"/projects/{pid}/what-if", json={
    "type": "add_room",
    "room": {"id": "bed_4", "name": "Bedroom 4", "type": "bedroom",
             "floor": 1, "x": 18, "y": 23, "w": 12, "h": 11}})
imp = r.json()["impact"]
print("what-if add bedroom:", r.status_code)
for k in ("built_up_sqft", "total_cost", "readiness", "doors"):
    print(f"   {k}: {imp[k]['before']} -> {imp[k]['after']} ({imp[k]['delta']:+})")
print("   committed:", imp["committed"])

# 5. interiors propagate into cost
r = c.patch(f"/projects/{pid}", json={
    "interiors": {"living": ["l-sofa", "l-f-marble", "l-lt-cove"], "kitchen": ["k-cab"]},
    "summary": "Selected living and kitchen interiors."})
a2 = c.get(f"/projects/{pid}/analysis").json()
print("after interiors: total", a["cost"]["total"], "->", a2["cost"]["total"],
      "| interiors line:", a2["cost"]["interiors"])

# 6. overlap detection — drag a room on top of another
rooms = c.get(f"/projects/{pid}").json()["rooms"]
rooms[1] = {**rooms[1], "x": rooms[4]["x"], "y": rooms[4]["y"], "floor": rooms[4]["floor"]}
c.patch(f"/projects/{pid}", json={"rooms": rooms})
a3 = c.get(f"/projects/{pid}/analysis").json()
print("overlaps detected:", a3["takeoff"]["overlaps"], "blocking:", a3["compliance"]["blocking_count"],
      "readiness:", a3["readiness"]["composite"])

# 7. decisions + snapshot
c.post(f"/projects/{pid}/versions", params={"label": "before client review"})
d = c.get(f"/projects/{pid}/decisions").json()
print("decisions logged:", len(d), "->", [x["summary"][:44] for x in d[:3]])

# 8. cortex without a key must 503, not invent
r = c.post(f"/projects/{pid}/cortex/structural")
print("cortex without key:", r.status_code)
