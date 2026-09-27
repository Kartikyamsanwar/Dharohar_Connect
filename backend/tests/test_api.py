from datetime import date, timedelta


def D(n):
    return (date.today() + timedelta(days=n)).isoformat()


def test_register_login_duplicate_and_bad_password(client):
    body = {"name": "Asha", "email": "asha@example.com", "password": "password123"}
    assert client.post("/api/auth/register", json=body).status_code == 200
    assert client.post("/api/auth/register", json=body).status_code == 409
    assert client.post("/api/auth/login", json={"email": "asha@example.com", "password": "wrong"}).status_code == 401
    r = client.post("/api/auth/login", json={"email": "ASHA@example.com", "password": "password123"})
    assert r.status_code == 200 and r.json()["user"]["name"] == "Asha"
    assert client.post("/api/auth/register", json={**body, "email": "x@y.com", "password": "short"}).status_code == 422


def test_bookings_require_login(client):
    assert client.get("/api/bookings").status_code == 401
    assert client.post("/api/bookings/hotel", json={"hotel_id": "hampi-budget", "check_in": D(5), "check_out": D(6)}).status_code == 401


def test_hotel_search_by_site_city_and_availability(client):
    r = client.get("/api/hotels", params={"destination": "Taj Mahal", "check_in": D(10), "check_out": D(12), "guests": 2, "rooms": 1})
    hotels = r.json()["hotels"]
    assert {h["city"] for h in hotels} == {"Agra"} and len(hotels) == 3
    assert all(h["nights"] == 2 and h["total_price"] == h["price_per_night"] * 2 for h in hotels)


def test_hotel_overlap_sold_out_and_cancel_restores(client, auth):
    base = {"hotel_id": "sanchi-premium", "guests": 3}  # 8 rooms
    first = client.post("/api/bookings/hotel", headers=auth, json={**base, "check_in": D(20), "check_out": D(23), "rooms": 5})
    assert first.status_code == 200 and first.json()["total"] == 5800 * 3 * 5
    ok = client.post("/api/bookings/hotel", headers=auth, json={**base, "check_in": D(22), "check_out": D(24), "rooms": 3})
    assert ok.status_code == 200
    full = client.post("/api/bookings/hotel", headers=auth, json={**base, "check_in": D(22), "check_out": D(23), "rooms": 1})
    assert full.status_code == 409
    later = client.post("/api/bookings/hotel", headers=auth, json={**base, "check_in": D(23), "check_out": D(24), "rooms": 5})
    assert later.status_code == 200
    assert client.post(f"/api/bookings/{first.json()['ref']}/cancel", headers=auth).json()["status"] == "cancelled"
    again = client.post("/api/bookings/hotel", headers=auth, json={**base, "check_in": D(22), "check_out": D(23), "rooms": 1})
    assert again.status_code == 200


def test_booking_validation(client, auth):
    bad = [
        {"hotel_id": "hampi-budget", "check_in": D(-2), "check_out": D(1), "rooms": 1, "guests": 1},
        {"hotel_id": "hampi-budget", "check_in": D(5), "check_out": D(5), "rooms": 1, "guests": 1},
        {"hotel_id": "hampi-budget", "check_in": D(5), "check_out": D(7), "rooms": 1, "guests": 4},
        {"hotel_id": "nope", "check_in": D(5), "check_out": D(7), "rooms": 1, "guests": 1},
    ]
    assert [client.post("/api/bookings/hotel", headers=auth, json=b).status_code for b in bad] == [422, 422, 422, 404]


def test_tickets_capacity_and_ownership(client, auth):
    listing = client.get("/api/tickets", params={"destination": "Hampi", "visit_date": D(15)}).json()["sites"]
    assert listing[0]["tickets"][0]["available"] == 1500
    r = client.post("/api/bookings/ticket", headers=auth, json={"ticket_id": "hampi-indian", "visit_date": D(15), "quantity": 4})
    assert r.status_code == 200 and r.json()["total"] == 160
    assert client.post("/api/bookings/ticket", headers=auth, json={"ticket_id": "hampi-indian", "visit_date": D(15), "quantity": 11}).status_code == 422
    assert client.post("/api/bookings/ticket", headers=auth, json={"ticket_id": "hampi-indian", "visit_date": D(-1), "quantity": 1}).status_code == 422
    other = client.post("/api/auth/register", json={"name": "Other", "email": "other@example.com", "password": "password123"}).json()["token"]
    assert client.post(f"/api/bookings/{r.json()['ref']}/cancel", headers={"Authorization": f"Bearer {other}"}).status_code == 404
    assert len(client.get("/api/bookings", headers=auth).json()["bookings"]) == 1


def test_free_entry_site(client, auth):
    r = client.post("/api/bookings/ticket", headers=auth, json={"ticket_id": "golden-temple-indian", "visit_date": D(3), "quantity": 2})
    assert r.json()["total"] == 0


def test_groups_join_once_and_match_score(client, auth):
    g = client.post("/api/groups", headers=auth, json={"name": "Hampi Crew", "destination": "Hampi", "dates": "3 days", "budget_min": 5000, "budget_max": 9000, "interests": "history", "capacity": 3}).json()
    assert g["members"] == 1 and g["joined"] is True
    assert client.post(f"/api/groups/{g['id']}/join", headers=auth).status_code == 409
    listing = client.get("/api/groups", params={"destination": "Hampi", "budget": "7000", "interests": "history"}).json()["groups"]
    assert any(x["id"] == g["id"] and x["match_score"] == 100 for x in listing)
    assert client.post("/api/groups", json={}).status_code in (401, 422)


def test_community_post_comment_like(client, auth):
    p = client.post("/api/community", headers=auth, json={"title": "Temple sunrise", "description": "Beautiful morning at the temple.", "category": "Travel Experience", "location": "Hampi"}).json()
    assert p["label"] == "community" and p["author"] == "Test User"
    assert client.post(f"/api/community/{p['id']}/comments", headers=auth, json={"text": "Lovely!"}).json()["comments"][0]["text"] == "Lovely!"
    assert client.post(f"/api/community/{p['id']}/like", headers=auth).json()["likes"] == 1
    assert client.post(f"/api/community/{p['id']}/like", headers=auth).status_code == 409


def test_saved_trips(client, auth):
    t = client.post("/api/trips", headers=auth, json={"title": "Hampi", "destination": "Hampi", "start_date": D(9), "days": 3, "payload": {"a": 1}})
    assert t.status_code == 200
    trips = client.get("/api/trips", headers=auth).json()["trips"]
    assert trips[0]["payload"] == {"a": 1}
    assert client.delete(f"/api/trips/{trips[0]['id']}", headers=auth).status_code == 200


def test_health_reports_database(client):
    h = client.get("/api/health").json()
    assert h["database_ok"] is True and h["status"] == "ok"
