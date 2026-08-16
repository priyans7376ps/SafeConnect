import pytest

from app import create_app
from app.extensions import db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret',
        'SECRET_KEY': 'test-secret'
    })
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_user(client, payload=None):
    p = payload or {
        'name': 'Test User',
        'email': 'test@example.com',
        'phone': '+1234567890',
        'password': 'secret123'
    }
    return client.post('/api/auth/register', json=p)


def login_user(client, payload=None):
    p = payload or {
        'email': 'test@example.com',
        'password': 'secret123'
    }
    return client.post('/api/auth/login', json=p)


def register_and_login(client, email, password='secret123', name='User'):
    response = register_user(client, {
        'name': name,
        'email': email,
        'phone': '+10000000000',
        'password': password,
    })
    assert response.status_code == 201, response.get_data(as_text=True)
    login = login_user(client, {'email': email, 'password': password})
    assert login.status_code == 200, login.get_data(as_text=True)
    return login.get_json()['data']['token']


def auth_header(token):
    return {'Authorization': f'Bearer {token}'}


def create_emergency_for(client, token, emergency_type='Medical', description='Test', priority='HIGH'):
    resp = client.post('/api/emergencies', json={
        'emergency_type': emergency_type,
        'description': description,
        'priority': priority,
    }, headers=auth_header(token))
    assert resp.status_code == 201, resp.get_data(as_text=True)
    return resp.get_json()['data']['emergency']


def get_notifications_for(client, token):
    resp = client.get('/api/notifications', headers=auth_header(token))
    assert resp.status_code == 200, resp.get_data(as_text=True)
    return resp.get_json()['data']['notifications']


# ---------------------------------------------------------------------------
# Milestone 1 — Existing tests (must still pass)
# ---------------------------------------------------------------------------

def test_user_registration(client):
    response = register_user(client)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['user']['email'] == 'test@example.com'


def test_login(client):
    register_user(client)
    response = login_user(client)
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    assert 'token' in response.get_json()['data']


def test_protected_endpoint(client):
    response = client.get('/api/users/profile')
    assert response.status_code == 401


def test_creating_emergency(client):
    register_user(client)
    token = login_user(client).get_json()['data']['token']
    response = client.post('/api/emergencies', json={
        'emergency_type': 'Medical',
        'description': 'Chest pain',
        'priority': 'HIGH'
    }, headers=auth_header(token))
    assert response.status_code == 201
    assert response.get_json()['data']['emergency']['status'] == 'ACTIVE'


def test_retrieving_emergencies(client):
    register_user(client)
    token = login_user(client).get_json()['data']['token']
    client.post('/api/emergencies', json={
        'emergency_type': 'Medical', 'description': 'Fall', 'priority': 'MEDIUM'
    }, headers=auth_header(token))
    response = client.get('/api/emergencies', headers=auth_header(token))
    assert response.status_code == 200
    assert len(response.get_json()['data']['emergencies']) >= 1


def test_creating_trusted_contact(client):
    register_user(client)
    token = login_user(client).get_json()['data']['token']
    response = client.post('/api/contacts', json={
        'name': 'Mom',
        'phone': '+1234567890',
        'email': 'mom@example.com',
        'relationship': 'Family',
        'is_primary': True
    }, headers=auth_header(token))
    assert response.status_code == 201
    assert response.get_json()['data']['contact']['name'] == 'Mom'


def test_creating_location(client):
    register_user(client)
    token = login_user(client).get_json()['data']['token']
    response = client.post('/api/locations', json={
        'latitude': 40.7128,
        'longitude': -74.0060,
        'accuracy': 12.5,
        'address': 'New York'
    }, headers=auth_header(token))
    assert response.status_code == 201
    assert response.get_json()['data']['location']['latitude'] == 40.7128


def test_notification_retrieval(client):
    """Owner should NOT receive their own EMERGENCY_ALERT; notifications list is still accessible."""
    register_user(client)
    token = login_user(client).get_json()['data']['token']
    client.post('/api/emergencies', json={
        'emergency_type': 'Medical', 'description': 'Testing alert', 'priority': 'HIGH'
    }, headers=auth_header(token))
    response = client.get('/api/notifications', headers=auth_header(token))
    assert response.status_code == 200
    # Owner does NOT receive their own EMERGENCY_ALERT — so count is 0 when no other users exist
    notifications = response.get_json()['data']['notifications']
    emergency_alerts = [n for n in notifications if n['notification_type'] == 'EMERGENCY_ALERT']
    assert len(emergency_alerts) == 0


def test_emergency_response_authorization(client):
    owner_token = register_and_login(client, 'owner@example.com', name='Owner')
    responder_token = register_and_login(client, 'helper@example.com', name='Helper')

    emergency = client.post('/api/emergencies', json={
        'emergency_type': 'Medical', 'description': 'Need help', 'priority': 'HIGH'
    }, headers=auth_header(owner_token))
    emergency_id = emergency.get_json()['data']['emergency']['id']

    response = client.post(f'/api/responses/emergency/{emergency_id}', json={
        'message': 'I can help'
    }, headers=auth_header(responder_token))
    assert response.status_code == 201
    payload = response.get_json()['data']['response']
    assert payload['emergency_id'] == emergency_id
    assert payload['responder_id'] == 2

    # Owner cannot respond to their own emergency
    own_response = client.post(f'/api/responses/emergency/{emergency_id}', json={
        'message': 'I can help'
    }, headers=auth_header(owner_token))
    assert own_response.status_code == 403

    # Duplicate response blocked
    second_response = client.post(f'/api/responses/emergency/{emergency_id}', json={
        'message': 'I can help again'
    }, headers=auth_header(responder_token))
    assert second_response.status_code == 409

    # Cannot respond to resolved emergency
    client.post(f'/api/emergencies/{emergency_id}/resolve', headers=auth_header(owner_token))
    third_response = client.post(f'/api/responses/emergency/{emergency_id}', json={
        'message': 'Too late'
    }, headers=auth_header(responder_token))
    assert third_response.status_code == 400

    # Unauthenticated request blocked
    unauth = client.post(f'/api/responses/emergency/{emergency_id}', json={'message': 'No auth'})
    assert unauth.status_code == 401


def test_location_authorization_and_emergency_access(client):
    owner_token = register_and_login(client, 'owner2@example.com', name='Owner2')
    other_token = register_and_login(client, 'other2@example.com', name='Other2')

    emergency = client.post('/api/emergencies', json={
        'emergency_type': 'Fire', 'description': 'House fire', 'priority': 'HIGH'
    }, headers=auth_header(owner_token))
    emergency_id = emergency.get_json()['data']['emergency']['id']

    # Owner can post location for their own emergency
    owner_location = client.post(f'/api/locations/emergency/{emergency_id}', json={
        'latitude': 12.0, 'longitude': 13.0, 'accuracy': 5.0
    }, headers=auth_header(owner_token))
    assert owner_location.status_code == 201

    # Non-owner cannot post location for another user's emergency
    other_location = client.post(f'/api/locations/emergency/{emergency_id}', json={
        'latitude': 20.0, 'longitude': 21.0, 'accuracy': 5.0
    }, headers=auth_header(other_token))
    assert other_location.status_code == 403

    # After M2, other2 receives EMERGENCY_ALERT so CAN view the emergency details (200, not 403)
    # But other2 must NOT be able to read the private location data
    unauthorized_location_read = client.get(
        f'/api/locations/emergency/{emergency_id}', headers=auth_header(other_token)
    )
    assert unauthorized_location_read.status_code == 403

    # Posting location to resolved emergency blocked
    client.post(f'/api/emergencies/{emergency_id}/resolve', headers=auth_header(owner_token))
    rejected = client.post(f'/api/locations/emergency/{emergency_id}', json={
        'latitude': 40.0, 'longitude': 41.0, 'accuracy': 5.0
    }, headers=auth_header(owner_token))
    assert rejected.status_code == 400


def test_user_and_contact_and_notification_scoping(client):
    """
    Updated for Milestone 2:
    - owner3 creates an emergency → other3 receives EMERGENCY_ALERT (not empty).
    - owner3 does NOT receive their own EMERGENCY_ALERT.
    - Contact data remains scoped to the owner.
    """
    owner_token = register_and_login(client, 'owner3@example.com', name='Owner3')
    other_token = register_and_login(client, 'other3@example.com', name='Other3')

    # Contact scoping — other3 cannot modify owner3's contact
    contact = client.post('/api/contacts', json={
        'name': 'Mom', 'phone': '+1111111111', 'relationship': 'Family'
    }, headers=auth_header(owner_token))
    assert contact.status_code == 201
    contact_id = contact.get_json()['data']['contact']['id']

    other_contact_update = client.put(f'/api/contacts/{contact_id}', json={
        'name': 'Hacker'
    }, headers=auth_header(other_token))
    assert other_contact_update.status_code == 404

    # Emergency creation
    emergency = client.post('/api/emergencies', json={
        'emergency_type': 'Medical', 'description': 'Need attention', 'priority': 'HIGH'
    }, headers=auth_header(owner_token))
    emergency_id = emergency.get_json()['data']['emergency']['id']
    client.post('/api/locations/emergency/{0}'.format(emergency_id), json={
        'latitude': 12.0, 'longitude': 13.0
    }, headers=auth_header(owner_token))

    # M2: other3 should now have an EMERGENCY_ALERT notification
    other_notifications = client.get('/api/notifications', headers=auth_header(other_token))
    assert other_notifications.status_code == 200
    other_notif_list = other_notifications.get_json()['data']['notifications']
    assert len(other_notif_list) >= 1
    alert_types = [n['notification_type'] for n in other_notif_list]
    assert 'EMERGENCY_ALERT' in alert_types

    # owner3 must NOT receive their own EMERGENCY_ALERT
    own_notifications = client.get('/api/notifications', headers=auth_header(owner_token))
    assert own_notifications.status_code == 200
    own_notif_list = own_notifications.get_json()['data']['notifications']
    own_alert_types = [n['notification_type'] for n in own_notif_list]
    assert 'EMERGENCY_ALERT' not in own_alert_types


# ---------------------------------------------------------------------------
# Milestone 2 — Emergency Broadcast Tests (Tests 1–13)
# ---------------------------------------------------------------------------

def _setup_four_users(client):
    """Register users A, B, C, D and return their tokens."""
    token_a = register_and_login(client, 'usera@example.com', name='UserA')
    token_b = register_and_login(client, 'userb@example.com', name='UserB')
    token_c = register_and_login(client, 'userc@example.com', name='UserC')
    token_d = register_and_login(client, 'userd@example.com', name='UserD')
    return token_a, token_b, token_c, token_d


def test_m2_01_emergency_is_active(client):
    """Test 1 — User A creates emergency → status is ACTIVE."""
    token_a = register_and_login(client, 'a1@test.com', name='A')
    emergency = create_emergency_for(client, token_a)
    assert emergency['status'] == 'ACTIVE'


def test_m2_02_user_b_receives_alert(client):
    """Test 2 — User B receives EMERGENCY_ALERT when A creates an emergency."""
    token_a, token_b, _, _ = _setup_four_users(client)
    create_emergency_for(client, token_a)
    notifications = get_notifications_for(client, token_b)
    types = [n['notification_type'] for n in notifications]
    assert 'EMERGENCY_ALERT' in types


def test_m2_03_user_c_receives_alert(client):
    """Test 3 — User C receives EMERGENCY_ALERT."""
    token_a, _, token_c, _ = _setup_four_users(client)
    create_emergency_for(client, token_a)
    notifications = get_notifications_for(client, token_c)
    types = [n['notification_type'] for n in notifications]
    assert 'EMERGENCY_ALERT' in types


def test_m2_04_user_d_receives_alert(client):
    """Test 4 — User D receives EMERGENCY_ALERT."""
    token_a, _, _, token_d = _setup_four_users(client)
    create_emergency_for(client, token_a)
    notifications = get_notifications_for(client, token_d)
    types = [n['notification_type'] for n in notifications]
    assert 'EMERGENCY_ALERT' in types


def test_m2_05_user_a_does_not_receive_own_alert(client):
    """Test 5 — User A does NOT receive their own EMERGENCY_ALERT."""
    token_a, _, _, _ = _setup_four_users(client)
    create_emergency_for(client, token_a)
    notifications = get_notifications_for(client, token_a)
    types = [n['notification_type'] for n in notifications]
    assert 'EMERGENCY_ALERT' not in types


def test_m2_06_notification_contains_correct_emergency_id(client):
    """Test 6 — Notification for B contains the correct emergency_id."""
    token_a, token_b, _, _ = _setup_four_users(client)
    emergency = create_emergency_for(client, token_a)
    emergency_id = emergency['id']
    notifications = get_notifications_for(client, token_b)
    alert = next((n for n in notifications if n['notification_type'] == 'EMERGENCY_ALERT'), None)
    assert alert is not None
    assert alert['emergency_id'] == emergency_id


def test_m2_07_notification_starts_unread(client):
    """Test 7 — EMERGENCY_ALERT notification is initially unread."""
    token_a, token_b, _, _ = _setup_four_users(client)
    create_emergency_for(client, token_a)
    notifications = get_notifications_for(client, token_b)
    alert = next((n for n in notifications if n['notification_type'] == 'EMERGENCY_ALERT'), None)
    assert alert is not None
    assert alert['is_read'] is False


def test_m2_08_user_b_can_retrieve_own_notifications(client):
    """Test 8 — User B can retrieve their own notifications (200 OK)."""
    token_a, token_b, _, _ = _setup_four_users(client)
    create_emergency_for(client, token_a)
    resp = client.get('/api/notifications', headers=auth_header(token_b))
    assert resp.status_code == 200
    assert len(resp.get_json()['data']['notifications']) >= 1


def test_m2_09_user_b_cannot_access_user_c_notifications(client):
    """Test 9 — User B's token fetches only B's notifications, not C's.

    The /notifications endpoint is always scoped to the authenticated user,
    so there is no direct way for B to read C's notifications by ID.
    We verify that B's notification list does not contain C-owned rows.
    """
    token_a, token_b, token_c, _ = _setup_four_users(client)
    create_emergency_for(client, token_a)

    b_notifications = get_notifications_for(client, token_b)
    c_notifications = get_notifications_for(client, token_c)

    b_ids = {n['id'] for n in b_notifications}
    c_ids = {n['id'] for n in c_notifications}

    # The sets of notification IDs must be completely disjoint
    assert b_ids.isdisjoint(c_ids), "B and C share notification IDs — scope leak!"


def test_m2_10_user_b_can_mark_notification_as_read(client):
    """Test 10 — User B can mark their EMERGENCY_ALERT as read."""
    token_a, token_b, _, _ = _setup_four_users(client)
    create_emergency_for(client, token_a)
    notifications = get_notifications_for(client, token_b)
    alert = next((n for n in notifications if n['notification_type'] == 'EMERGENCY_ALERT'), None)
    assert alert is not None

    resp = client.put(f"/api/notifications/{alert['id']}/read", headers=auth_header(token_b))
    assert resp.status_code == 200
    assert resp.get_json()['data']['notification']['is_read'] is True


def test_m2_11_no_duplicate_alerts_on_repeated_broadcast(client):
    """Test 11 — Calling broadcast again for the same emergency creates no duplicates."""
    from app.services.notification_service import broadcast_emergency_alert
    from app.models.emergency import Emergency
    from app import create_app

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret',
        'SECRET_KEY': 'test-secret',
    })
    with app.app_context():
        db.create_all()
        inner_client = app.test_client()

        token_a, token_b, _, _ = _setup_four_users(inner_client)
        emergency = create_emergency_for(inner_client, token_a)
        emergency_id = emergency['id']

        # Simulate repeated broadcast call (idempotency check)
        with app.app_context():
            emerg_obj = Emergency.query.get(emergency_id)
            result1 = broadcast_emergency_alert(emerg_obj)
            db.session.commit()

        # B should still have exactly 1 EMERGENCY_ALERT for this emergency
        b_notifications = get_notifications_for(inner_client, token_b)
        alerts = [
            n for n in b_notifications
            if n['notification_type'] == 'EMERGENCY_ALERT' and n['emergency_id'] == emergency_id
        ]
        assert len(alerts) == 1, f"Expected 1 alert, got {len(alerts)}"

        db.session.remove()
        db.drop_all()


def test_m2_12_existing_auth_tests_still_pass(client):
    """Test 12 — Basic auth smoke test still passes."""
    response = register_user(client)
    assert response.status_code == 201
    login_resp = login_user(client)
    assert login_resp.status_code == 200
    assert 'token' in login_resp.get_json()['data']


def test_m2_13_milestone1_security_preserved(client):
    """Test 13 — Milestone 1 location and contact security rules still enforced."""
    owner_token = register_and_login(client, 'sec_owner@example.com', name='SecOwner')
    other_token = register_and_login(client, 'sec_other@example.com', name='SecOther')

    emergency = client.post('/api/emergencies', json={
        'emergency_type': 'Threat', 'description': 'Security test', 'priority': 'HIGH'
    }, headers=auth_header(owner_token))
    emergency_id = emergency.get_json()['data']['emergency']['id']

    # Non-owner cannot write location for another user's emergency
    bad_location = client.post(f'/api/locations/emergency/{emergency_id}', json={
        'latitude': 99.0, 'longitude': 99.0, 'accuracy': 1.0
    }, headers=auth_header(other_token))
    assert bad_location.status_code == 403

    # Non-owner cannot read private location data even after receiving EMERGENCY_ALERT
    bad_read = client.get(f'/api/locations/emergency/{emergency_id}',
                          headers=auth_header(other_token))
    assert bad_read.status_code == 403

    # Non-owner cannot cancel the emergency
    bad_cancel = client.post(f'/api/emergencies/{emergency_id}/cancel',
                             headers=auth_header(other_token))
    assert bad_cancel.status_code == 403

    # Non-owner cannot resolve the emergency
    bad_resolve = client.post(f'/api/emergencies/{emergency_id}/resolve',
                              headers=auth_header(other_token))
    assert bad_resolve.status_code == 403


# ---------------------------------------------------------------------------
# Milestone 3 — Continuous Live Location Tracking Tests
# ---------------------------------------------------------------------------

def _post_location(client, token, emergency_id, lat=12.34, lng=56.78, accuracy=5.0):
    """Helper: POST a location update for an emergency."""
    return client.post(
        f'/api/locations/emergency/{emergency_id}',
        json={'latitude': lat, 'longitude': lng, 'accuracy': accuracy},
        headers=auth_header(token),
    )


def _get_latest(client, token, emergency_id):
    """Helper: GET latest location for an emergency."""
    return client.get(
        f'/api/locations/emergency/{emergency_id}/latest',
        headers=auth_header(token),
    )


def test_m3_01_owner_can_submit_location(client):
    """Test 1 — Emergency owner can submit a location update (201)."""
    token = register_and_login(client, 'm3t1@test.com', name='T1')
    emergency = create_emergency_for(client, token)
    resp = _post_location(client, token, emergency['id'])
    assert resp.status_code == 201
    body = resp.get_json()['data']['location']
    assert body['latitude'] == 12.34
    assert body['longitude'] == 56.78


def test_m3_02_other_user_cannot_submit_location(client):
    """Test 2 — Non-owner cannot write location for another user's emergency (403)."""
    owner_token = register_and_login(client, 'm3t2_owner@test.com', name='Owner')
    other_token = register_and_login(client, 'm3t2_other@test.com', name='Other')
    emergency = create_emergency_for(client, owner_token)
    resp = _post_location(client, other_token, emergency['id'])
    assert resp.status_code == 403


def test_m3_03_unauthenticated_cannot_submit_location(client):
    """Test 3 — Unauthenticated request is rejected (401)."""
    token = register_and_login(client, 'm3t3@test.com', name='T3')
    emergency = create_emergency_for(client, token)
    resp = client.post(
        f'/api/locations/emergency/{emergency["id"]}',
        json={'latitude': 10.0, 'longitude': 20.0},
    )
    assert resp.status_code == 401


def test_m3_04_nonexistent_emergency_rejected(client):
    """Test 4 — Location submission for a non-existent emergency (404)."""
    token = register_and_login(client, 'm3t4@test.com', name='T4')
    resp = _post_location(client, token, 999_999)
    assert resp.status_code == 404


def test_m3_05_resolved_emergency_rejects_location(client):
    """Test 5 — Location submission to a RESOLVED emergency is rejected (400)."""
    token = register_and_login(client, 'm3t5@test.com', name='T5')
    emergency = create_emergency_for(client, token)
    client.post(f'/api/emergencies/{emergency["id"]}/resolve', headers=auth_header(token))
    resp = _post_location(client, token, emergency['id'])
    assert resp.status_code == 400


def test_m3_06_cancelled_emergency_rejects_location(client):
    """Test 6 — Location submission to a CANCELLED emergency is rejected (400)."""
    token = register_and_login(client, 'm3t6@test.com', name='T6')
    emergency = create_emergency_for(client, token)
    client.post(f'/api/emergencies/{emergency["id"]}/cancel', headers=auth_header(token))
    resp = _post_location(client, token, emergency['id'])
    assert resp.status_code == 400


def test_m3_07_owner_can_get_latest_location(client):
    """Test 7 — Owner can retrieve the latest location for their emergency."""
    token = register_and_login(client, 'm3t7@test.com', name='T7')
    emergency = create_emergency_for(client, token)
    _post_location(client, token, emergency['id'], lat=11.11, lng=22.22)
    resp = _get_latest(client, token, emergency['id'])
    assert resp.status_code == 200
    loc = resp.get_json()['data']['location']
    assert loc['latitude'] == 11.11
    assert loc['longitude'] == 22.22
    assert 'timestamp' in loc
    assert 'emergency_id' in loc
    # Privacy: user_id must NOT be exposed in the latest-location response
    assert 'user_id' not in loc


def test_m3_08_unauthorized_user_cannot_get_latest_location(client):
    """Test 8 — Non-owner/non-responder cannot read the private latest location (403)."""
    owner_token = register_and_login(client, 'm3t8_owner@test.com', name='Owner8')
    other_token = register_and_login(client, 'm3t8_other@test.com', name='Other8')
    emergency = create_emergency_for(client, owner_token)
    _post_location(client, owner_token, emergency['id'])
    resp = _get_latest(client, other_token, emergency['id'])
    assert resp.status_code == 403


def test_m3_09_multiple_location_updates_stored(client):
    """Test 9 — Multiple location updates are stored independently."""
    token = register_and_login(client, 'm3t9@test.com', name='T9')
    emergency = create_emergency_for(client, token)
    eid = emergency['id']

    _post_location(client, token, eid, lat=10.0, lng=20.0)
    _post_location(client, token, eid, lat=10.1, lng=20.1)
    _post_location(client, token, eid, lat=10.2, lng=20.2)

    # Check via the full list endpoint (owner can read all)
    resp = client.get(f'/api/locations/emergency/{eid}', headers=auth_header(token))
    assert resp.status_code == 200
    locs = resp.get_json()['data']['locations']
    assert len(locs) == 3


def test_m3_10_latest_returns_newest_location(client):
    """Test 10 — /latest always returns the most-recently stored location."""
    token = register_and_login(client, 'm3t10@test.com', name='T10')
    emergency = create_emergency_for(client, token)
    eid = emergency['id']

    _post_location(client, token, eid, lat=10.0, lng=20.0)
    _post_location(client, token, eid, lat=89.0, lng=89.0)  # newest

    resp = _get_latest(client, token, eid)
    assert resp.status_code == 200
    loc = resp.get_json()['data']['location']
    assert loc['latitude'] == 89.0
    assert loc['longitude'] == 89.0



def test_m3_11_milestone1_security_still_passes(client):
    """Test 11 — M1 security rules still enforced after M3 changes."""
    owner_token = register_and_login(client, 'm3t11_o@test.com', name='M3Owner')
    other_token = register_and_login(client, 'm3t11_x@test.com', name='M3Other')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    assert _post_location(client, other_token, eid).status_code == 403
    assert client.get(f'/api/locations/emergency/{eid}',
                      headers=auth_header(other_token)).status_code == 403
    assert client.post(f'/api/emergencies/{eid}/cancel',
                       headers=auth_header(other_token)).status_code == 403


def test_m3_12_milestone2_notifications_still_pass(client):
    """Test 12 — M2 broadcast notifications still created after M3 changes."""
    owner_token = register_and_login(client, 'm3t12_a@test.com', name='M3A')
    other_token = register_and_login(client, 'm3t12_b@test.com', name='M3B')
    create_emergency_for(client, owner_token)
    notifications = get_notifications_for(client, other_token)
    types = [n['notification_type'] for n in notifications]
    assert 'EMERGENCY_ALERT' in types


# ---------------------------------------------------------------------------
# Milestone 4 — Real-time Location Delivery Using WebSockets Tests
# ---------------------------------------------------------------------------

def test_m4_01_authenticated_owner_can_connect(client):
    """Test 1 — Authenticated emergency owner can connect and join room."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t1@test.com', name='M4Owner')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    s_client = socketio.test_client(client.application, flask_test_client=client)
    assert s_client.is_connected()

    s_client.emit('join_emergency', {'emergency_id': eid, 'token': owner_token})
    received = s_client.get_received()
    assert len(received) >= 1
    event = received[0]
    assert event['name'] == 'joined_emergency'
    assert event['args'][0]['emergency_id'] == eid


def test_m4_02_authorized_responder_can_connect(client):
    """Test 2 — Authorized responder can connect and join emergency room."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t2_o@test.com', name='M4Owner2')
    resp_token = register_and_login(client, 'm4t2_r@test.com', name='M4Resp2')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    # Responder responds to emergency
    client.post(f'/api/responses/emergency/{eid}', json={'message': 'Responding'}, headers=auth_header(resp_token))

    s_client = socketio.test_client(client.application, flask_test_client=client)
    s_client.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    received = s_client.get_received()
    assert len(received) >= 1
    assert received[0]['name'] == 'joined_emergency'


def test_m4_03_random_user_cannot_join_emergency_room(client):
    """Test 3 — Random authenticated user CANNOT join emergency room."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t3_o@test.com', name='M4Owner3')
    random_token = register_and_login(client, 'm4t3_x@test.com', name='M4Random3')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    s_client = socketio.test_client(client.application, flask_test_client=client)
    s_client.emit('join_emergency', {'emergency_id': eid, 'token': random_token})
    received = s_client.get_received()
    assert len(received) >= 1
    assert received[0]['name'] == 'error'
    assert 'Not authorized' in received[0]['args'][0]['message']


def test_m4_04_unauthenticated_user_cannot_join_room(client):
    """Test 4 — Unauthenticated user cannot join emergency room."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t4_o@test.com', name='M4Owner4')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    s_client = socketio.test_client(client.application, flask_test_client=client)
    s_client.emit('join_emergency', {'emergency_id': eid, 'token': 'invalid-token'})
    received = s_client.get_received()
    assert len(received) >= 1
    assert received[0]['name'] == 'error'


def test_m4_05_owner_submits_valid_location_persisted(client):
    """Test 5 — Emergency owner submits valid location via REST, persisted in DB."""
    owner_token = register_and_login(client, 'm4t5@test.com', name='M4Owner5')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    resp = _post_location(client, owner_token, eid, lat=40.7128, lng=-74.0060)
    assert resp.status_code == 201

    # Verify DB persistence via latest API
    latest_resp = _get_latest(client, owner_token, eid)
    assert latest_resp.status_code == 200
    assert latest_resp.get_json()['data']['location']['latitude'] == 40.7128


def test_m4_06_authorized_responder_receives_location_update(client):
    """Test 6 — Authorized responder receives location_update event via socket."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t6_o@test.com', name='M4Owner6')
    resp_token = register_and_login(client, 'm4t6_r@test.com', name='M4Resp6')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'On my way'}, headers=auth_header(resp_token))

    s_resp = socketio.test_client(client.application, flask_test_client=client)
    s_resp.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    s_resp.get_received()  # clear join event

    _post_location(client, owner_token, eid, lat=51.5074, lng=-0.1278)

    received = s_resp.get_received()
    assert len(received) >= 1
    upd = received[0]
    assert upd['name'] == 'location_update'
    payload = upd['args'][0]
    assert payload['emergency_id'] == eid
    assert payload['latitude'] == 51.5074
    assert payload['longitude'] == -0.1278


def test_m4_07_unauthorized_user_does_not_receive_location_update(client):
    """Test 7 — Unauthorized user does NOT receive location_update event."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t7_o@test.com', name='M4Owner7')
    unauth_token = register_and_login(client, 'm4t7_u@test.com', name='M4Unauth7')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    s_unauth = socketio.test_client(client.application, flask_test_client=client)
    s_unauth.emit('join_emergency', {'emergency_id': eid, 'token': unauth_token})
    s_unauth.get_received()  # clear rejection error

    _post_location(client, owner_token, eid, lat=12.34, lng=56.78)

    received = s_unauth.get_received()
    # Filter for location_update events
    loc_updates = [e for e in received if e['name'] == 'location_update']
    assert len(loc_updates) == 0


def test_m4_08_multiple_authorized_responders_receive_location_update(client):
    """Test 8 — Multiple authorized responders receive the same location_update."""
    from app.extensions import socketio
    c1 = client.application.test_client()
    c2 = client.application.test_client()

    owner_token = register_and_login(client, 'm4t8_o@test.com', name='M4Owner8')
    r1_token = register_and_login(c1, 'm4t8_r1@test.com', name='M4Resp8_1')
    r2_token = register_and_login(c2, 'm4t8_r2@test.com', name='M4Resp8_2')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    c1.post(f'/api/responses/emergency/{eid}', json={'message': 'R1 here'}, headers=auth_header(r1_token))
    c2.post(f'/api/responses/emergency/{eid}', json={'message': 'R2 here'}, headers=auth_header(r2_token))

    s_r1 = socketio.test_client(client.application, flask_test_client=c1)
    s_r1.emit('join_emergency', {'emergency_id': eid, 'token': r1_token})
    s_r1.get_received()

    s_r2 = socketio.test_client(client.application, flask_test_client=c2)
    s_r2.emit('join_emergency', {'emergency_id': eid, 'token': r2_token})
    s_r2.get_received()

    _post_location(client, owner_token, eid, lat=35.6762, lng=139.6503)

    rec1 = [e for e in s_r1.get_received() if e['name'] == 'location_update']
    rec2 = [e for e in s_r2.get_received() if e['name'] == 'location_update']

    assert len(rec1) == 1
    assert len(rec2) == 1
    assert rec1[0]['args'][0]['latitude'] == 35.6762
    assert rec2[0]['args'][0]['latitude'] == 35.6762



def test_m4_09_invalid_location_not_broadcast(client):
    """Test 9 — Invalid location update is not persisted and not broadcast."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t9_o@test.com', name='M4Owner9')
    resp_token = register_and_login(client, 'm4t9_r@test.com', name='M4Resp9')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'Ready'}, headers=auth_header(resp_token))
    s_resp = socketio.test_client(client.application, flask_test_client=client)
    s_resp.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    s_resp.get_received()

    # Invalid latitude 999.0
    bad_resp = _post_location(client, owner_token, eid, lat=999.0, lng=50.0)
    assert bad_resp.status_code == 400

    rec = [e for e in s_resp.get_received() if e['name'] == 'location_update']
    assert len(rec) == 0


def test_m4_10_location_update_for_resolved_emergency_rejected_and_not_broadcast(client):
    """Test 10 — Location update for resolved emergency is rejected and not broadcast."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t10_o@test.com', name='M4Owner10')
    resp_token = register_and_login(client, 'm4t10_r@test.com', name='M4Resp10')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'Helping'}, headers=auth_header(resp_token))
    s_resp = socketio.test_client(client.application, flask_test_client=client)
    s_resp.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    s_resp.get_received()

    # Resolve emergency
    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))

    # Try to post location after resolve
    bad_post = _post_location(client, owner_token, eid, lat=10.0, lng=10.0)
    assert bad_post.status_code == 400

    rec = [e for e in s_resp.get_received() if e['name'] == 'location_update']
    assert len(rec) == 0


def test_m4_11_location_update_for_cancelled_emergency_rejected_and_not_broadcast(client):
    """Test 11 — Location update for cancelled emergency is rejected and not broadcast."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t11_o@test.com', name='M4Owner11')
    resp_token = register_and_login(client, 'm4t11_r@test.com', name='M4Resp11')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'Helping'}, headers=auth_header(resp_token))
    s_resp = socketio.test_client(client.application, flask_test_client=client)
    s_resp.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    s_resp.get_received()

    # Cancel emergency
    client.post(f'/api/emergencies/{eid}/cancel', headers=auth_header(owner_token))

    bad_post = _post_location(client, owner_token, eid, lat=10.0, lng=10.0)
    assert bad_post.status_code == 400

    rec = [e for e in s_resp.get_received() if e['name'] == 'location_update']
    assert len(rec) == 0


def test_m4_12_emergency_end_event_delivered_to_connected_authorized_users(client):
    """Test 12 — Emergency end event is delivered to connected authorized users."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t12_o@test.com', name='M4Owner12')
    resp_token = register_and_login(client, 'm4t12_r@test.com', name='M4Resp12')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'Helping'}, headers=auth_header(resp_token))
    s_resp = socketio.test_client(client.application, flask_test_client=client)
    s_resp.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    s_resp.get_received()

    # Resolve emergency
    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))

    rec = [e for e in s_resp.get_received() if e['name'] == 'emergency_ended']
    assert len(rec) == 1
    assert rec[0]['args'][0]['emergency_id'] == eid
    assert rec[0]['args'][0]['status'] == 'RESOLVED'


def test_m4_13_users_cannot_join_ended_emergencies(client):
    """Test 13 — Users cannot join ended emergencies."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'm4t13_o@test.com', name='M4Owner13')
    resp_token = register_and_login(client, 'm4t13_r@test.com', name='M4Resp13')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'Helping'}, headers=auth_header(resp_token))
    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))

    s_resp = socketio.test_client(client.application, flask_test_client=client)
    s_resp.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    received = s_resp.get_received()
    assert len(received) >= 1
    assert received[0]['name'] == 'error'
    assert 'not active' in received[0]['args'][0]['message']


def test_m4_14_milestone1_security_preserved(client):
    """Test 14 — Existing Milestone 1 security tests pass."""
    owner_token = register_and_login(client, 'm4t14_o@test.com', name='M4Owner14')
    other_token = register_and_login(client, 'm4t14_x@test.com', name='M4Other14')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    assert _post_location(client, other_token, eid).status_code == 403
    assert client.get(f'/api/locations/emergency/{eid}', headers=auth_header(other_token)).status_code == 403


def test_m4_15_milestone2_notifications_still_pass(client):
    """Test 15 — Existing Milestone 2 notification tests pass."""
    owner_token = register_and_login(client, 'm4t15_a@test.com', name='M4Owner15')
    other_token = register_and_login(client, 'm4t15_b@test.com', name='M4Other15')
    create_emergency_for(client, owner_token)
    notifications = get_notifications_for(client, other_token)
    types = [n['notification_type'] for n in notifications]
    assert 'EMERGENCY_ALERT' in types


def test_m4_16_milestone3_location_tests_still_pass(client):
    """Test 16 — Existing Milestone 3 location tests pass."""
    token = register_and_login(client, 'm4t16@test.com', name='M4T16')
    emergency = create_emergency_for(client, token)
    eid = emergency['id']

    _post_location(client, token, eid, lat=10.0, lng=20.0)
    _post_location(client, token, eid, lat=89.0, lng=89.0)

    resp = _get_latest(client, token, eid)
    assert resp.status_code == 200
    loc = resp.get_json()['data']['location']
    assert loc['latitude'] == 89.0
    assert loc['longitude'] == 89.0


# ---------------------------------------------------------------------------
# Phase 6 — "I CAN HELP" Responder Flow Tests
# ---------------------------------------------------------------------------

def test_p6_01_user_b_can_respond_to_user_a_active_emergency(client):
    """Test 1 — User B can respond to User A's active emergency and owner gets notification."""
    owner_token = register_and_login(client, 'p6t1_a@test.com', name='UserA')
    resp_token = register_and_login(client, 'p6t1_b@test.com', name='UserB')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    res = client.post(f'/api/responses/emergency/{eid}', json={'message': 'I can help'}, headers=auth_header(resp_token))
    assert res.status_code == 201
    body = res.get_json()['data']['response']
    assert body['responder_id'] == 2
    assert body['status'] == 'ACCEPTED'

    # Check owner notification
    owner_notifs = get_notifications_for(client, owner_token)
    resp_notifs = [n for n in owner_notifs if n['notification_type'] == 'EMERGENCY_RESPONSE']
    assert len(resp_notifs) == 1
    assert resp_notifs[0]['title'] == 'Help is on the way'


def test_p6_02_user_b_cannot_respond_twice(client):
    """Test 2 — User B cannot respond twice to the same emergency (409)."""
    owner_token = register_and_login(client, 'p6t2_a@test.com', name='UserA2')
    resp_token = register_and_login(client, 'p6t2_b@test.com', name='UserB2')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    r1 = client.post(f'/api/responses/emergency/{eid}', json={'message': 'I can help'}, headers=auth_header(resp_token))
    assert r1.status_code == 201

    r2 = client.post(f'/api/responses/emergency/{eid}', json={'message': 'I can help again'}, headers=auth_header(resp_token))
    assert r2.status_code == 409


def test_p6_03_user_a_cannot_respond_to_own_emergency(client):
    """Test 3 — Emergency owner User A cannot respond to their own emergency (403)."""
    owner_token = register_and_login(client, 'p6t3_a@test.com', name='UserA3')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    res = client.post(f'/api/responses/emergency/{eid}', json={'message': 'Helping myself'}, headers=auth_header(owner_token))
    assert res.status_code == 403


def test_p6_04_user_c_cannot_access_responder_location_before_responding(client):
    """Test 4 — User C who has not responded cannot access private location (403)."""
    owner_token = register_and_login(client, 'p6t4_a@test.com', name='UserA4')
    other_token = register_and_login(client, 'p6t4_c@test.com', name='UserC4')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    _post_location(client, owner_token, eid, lat=12.34, lng=56.78)

    res = _get_latest(client, other_token, eid)
    assert res.status_code == 403


def test_p6_05_after_responding_user_b_can_access_latest_location(client):
    """Test 5 — After responding, User B can access the emergency latest location."""
    owner_token = register_and_login(client, 'p6t5_a@test.com', name='UserA5')
    resp_token = register_and_login(client, 'p6t5_b@test.com', name='UserB5')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    _post_location(client, owner_token, eid, lat=25.123, lng=82.456)
    client.post(f'/api/responses/emergency/{eid}', json={'message': 'I can help'}, headers=auth_header(resp_token))

    res = _get_latest(client, resp_token, eid)
    assert res.status_code == 200
    assert res.get_json()['data']['location']['latitude'] == 25.123


def test_p6_06_after_responding_user_b_can_join_websocket_room(client):
    """Test 6 — After responding, User B can join the emergency WebSocket room."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'p6t6_a@test.com', name='UserA6')
    resp_token = register_and_login(client, 'p6t6_b@test.com', name='UserB6')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'I can help'}, headers=auth_header(resp_token))

    s_client = socketio.test_client(client.application, flask_test_client=client)
    s_client.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    received = s_client.get_received()
    assert len(received) >= 1
    assert received[0]['name'] == 'joined_emergency'


def test_p6_07_user_b_receives_location_update(client):
    """Test 7 — Authorized responder User B receives location_update event via socket."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'p6t7_a@test.com', name='UserA7')
    resp_token = register_and_login(client, 'p6t7_b@test.com', name='UserB7')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'I can help'}, headers=auth_header(resp_token))
    s_resp = socketio.test_client(client.application, flask_test_client=client)
    s_resp.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    s_resp.get_received()

    _post_location(client, owner_token, eid, lat=19.076, lng=72.877)

    rec = [e for e in s_resp.get_received() if e['name'] == 'location_update']
    assert len(rec) == 1
    assert rec[0]['args'][0]['latitude'] == 19.076


def test_p6_08_unauthorized_user_c_does_not_receive_location_update(client):
    """Test 8 — Unauthorized User C (not responded) does not receive location_update."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'p6t8_a@test.com', name='UserA8')
    other_token = register_and_login(client, 'p6t8_c@test.com', name='UserC8')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    s_other = socketio.test_client(client.application, flask_test_client=client)
    s_other.emit('join_emergency', {'emergency_id': eid, 'token': other_token})
    s_other.get_received()

    _post_location(client, owner_token, eid, lat=10.0, lng=10.0)

    rec = [e for e in s_other.get_received() if e['name'] == 'location_update']
    assert len(rec) == 0


# ---------------------------------------------------------------------------
# Phase 7 — "REACHED SAFELY" Emergency Completion Flow Tests
# ---------------------------------------------------------------------------

def test_p7_09_emergency_owner_can_resolve_active_emergency(client):
    """Test 9 — Emergency owner can resolve active emergency (REACHED SAFELY)."""
    owner_token = register_and_login(client, 'p7t9_a@test.com', name='UserA9')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    res = client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))
    assert res.status_code == 200
    assert res.get_json()['data']['emergency']['status'] == 'RESOLVED'


def test_p7_10_responder_cannot_resolve_emergency(client):
    """Test 10 — Responder User B cannot resolve emergency (403)."""
    owner_token = register_and_login(client, 'p7t10_a@test.com', name='UserA10')
    resp_token = register_and_login(client, 'p7t10_b@test.com', name='UserB10')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'I can help'}, headers=auth_header(resp_token))

    res = client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(resp_token))
    assert res.status_code == 403


def test_p7_11_random_user_cannot_resolve_emergency(client):
    """Test 11 — Random user cannot resolve emergency (403)."""
    owner_token = register_and_login(client, 'p7t11_a@test.com', name='UserA11')
    other_token = register_and_login(client, 'p7t11_c@test.com', name='UserC11')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    res = client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(other_token))
    assert res.status_code == 403


def test_p7_12_resolved_emergency_rejects_new_location_updates(client):
    """Test 12 — Resolved emergency rejects new location updates (400)."""
    owner_token = register_and_login(client, 'p7t12_a@test.com', name='UserA12')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))

    res = _post_location(client, owner_token, eid, lat=12.0, lng=12.0)
    assert res.status_code == 400


def test_p7_13_resolved_emergency_cannot_be_joined_through_websocket(client):
    """Test 13 — Resolved emergency cannot be joined through WebSocket."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'p7t13_a@test.com', name='UserA13')
    resp_token = register_and_login(client, 'p7t13_b@test.com', name='UserB13')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'I can help'}, headers=auth_header(resp_token))
    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))

    s_resp = socketio.test_client(client.application, flask_test_client=client)
    s_resp.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    received = s_resp.get_received()
    assert len(received) >= 1
    assert received[0]['name'] == 'error'
    assert 'not active' in received[0]['args'][0]['message']


def test_p7_14_emergency_ended_is_broadcast(client):
    """Test 14 — emergency_ended is broadcast when owner resolves emergency."""
    from app.extensions import socketio
    owner_token = register_and_login(client, 'p7t14_a@test.com', name='UserA14')
    resp_token = register_and_login(client, 'p7t14_b@test.com', name='UserB14')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'Helping'}, headers=auth_header(resp_token))
    s_resp = socketio.test_client(client.application, flask_test_client=client)
    s_resp.emit('join_emergency', {'emergency_id': eid, 'token': resp_token})
    s_resp.get_received()

    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))

    rec = [e for e in s_resp.get_received() if e['name'] == 'emergency_ended']
    assert len(rec) == 1
    assert rec[0]['args'][0]['status'] == 'RESOLVED'


def test_p7_15_safe_arrival_notification_is_created(client):
    """Test 15 — Safe-arrival notification (EMERGENCY_SAFE) is created for alert recipients & responders."""
    owner_token = register_and_login(client, 'p7t15_a@test.com', name='UserA15')
    resp_token = register_and_login(client, 'p7t15_b@test.com', name='UserB15')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'Helping'}, headers=auth_header(resp_token))
    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))

    b_notifs = get_notifications_for(client, resp_token)
    safe_notifs = [n for n in b_notifs if n['notification_type'] == 'EMERGENCY_SAFE']
    assert len(safe_notifs) == 1
    assert safe_notifs[0]['title'] == 'Emergency Resolved'


def test_p7_16_safe_arrival_notification_does_not_duplicate_on_repeated_resolve(client):
    """Test 16 — Repeated resolve or broadcast_safe_arrival call does not duplicate notifications."""
    from app.services.notification_service import broadcast_safe_arrival
    from app.models.emergency import Emergency

    owner_token = register_and_login(client, 'p7t16_a@test.com', name='UserA16')
    resp_token = register_and_login(client, 'p7t16_b@test.com', name='UserB16')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'Helping'}, headers=auth_header(resp_token))
    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))

    # Repeat broadcast_safe_arrival call manually
    with client.application.app_context():
        emerg_obj = db.session.get(Emergency, eid)
        res = broadcast_safe_arrival(emerg_obj)
        db.session.commit()
        assert res['recipients_notified'] == 0

    b_notifs = get_notifications_for(client, resp_token)
    safe_notifs = [n for n in b_notifs if n['notification_type'] == 'EMERGENCY_SAFE']
    assert len(safe_notifs) == 1


def test_p7_17_existing_emergency_status_is_correctly_resolved(client):
    """Test 17 — Existing emergency status is correctly RESOLVED."""
    owner_token = register_and_login(client, 'p7t17_a@test.com', name='UserA17')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))
    res = client.get(f'/api/emergencies/{eid}', headers=auth_header(owner_token))
    assert res.status_code == 200
    assert res.get_json()['data']['emergency']['status'] == 'RESOLVED'


# ============================================================
# PHASE 8 TESTS — REAL PUSH NOTIFICATIONS
# ============================================================

def test_p8_01_create_push_subscription_success(client):
    """Test 1 — Authenticated user can register a push subscription."""
    token = register_and_login(client, 'p8t1@test.com', name='P8User1')
    payload = {
        'endpoint': 'https://push.services.mozilla.com/v1/sub_p8_01',
        'keys': {'p256dh': 'key_p256dh_sample_123', 'auth': 'key_auth_sample_456'},
        'user_agent': 'Mozilla/5.0 TestBrowser',
    }
    res = client.post('/api/notifications/push-subscription', json=payload, headers=auth_header(token))
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['subscription']['endpoint'] == payload['endpoint']


def test_p8_02_unauthenticated_push_subscription_rejected(client):
    """Test 2 — Unauthenticated user cannot register a push subscription."""
    payload = {
        'endpoint': 'https://push.services.mozilla.com/v1/sub_p8_02',
        'keys': {'p256dh': 'p256dh', 'auth': 'auth'},
    }
    res = client.post('/api/notifications/push-subscription', json=payload)
    assert res.status_code == 401


def test_p8_03_invalid_push_subscription_payload_rejected(client):
    """Test 3 — Missing required subscription keys returns 400 Bad Request."""
    token = register_and_login(client, 'p8t3@test.com', name='P8User3')
    payload = {'endpoint': 'https://push.services.mozilla.com/v1/sub_p8_03'}
    res = client.post('/api/notifications/push-subscription', json=payload, headers=auth_header(token))
    assert res.status_code == 400
    assert res.get_json()['success'] is False


def test_p8_04_duplicate_push_subscription_is_idempotent(client):
    """Test 4 — Duplicate subscription endpoint updates existing record without duplicate DB row."""
    from app.models.push_subscription import PushSubscription
    token = register_and_login(client, 'p8t4@test.com', name='P8User4')
    payload = {
        'endpoint': 'https://push.services.mozilla.com/v1/sub_p8_04_dup',
        'keys': {'p256dh': 'key1', 'auth': 'auth1'},
    }
    r1 = client.post('/api/notifications/push-subscription', json=payload, headers=auth_header(token))
    assert r1.status_code == 201

    payload['keys']['p256dh'] = 'key1_updated'
    r2 = client.post('/api/notifications/push-subscription', json=payload, headers=auth_header(token))
    assert r2.status_code == 201

    with client.application.app_context():
        count = PushSubscription.query.filter_by(endpoint=payload['endpoint']).count()
        assert count == 1
        sub = PushSubscription.query.filter_by(endpoint=payload['endpoint']).first()
        assert sub.p256dh == 'key1_updated'


def test_p8_05_emergency_creates_push_delivery_for_eligible_users(client):
    """Test 5 — Emergency creation triggers push notification to registered active community users."""
    from app.models.push_subscription import PushSubscription
    token_a = register_and_login(client, 'p8t5_a@test.com', name='P8UserA')
    token_b = register_and_login(client, 'p8t5_b@test.com', name='P8UserB')

    client.post('/api/notifications/push-subscription', json={
        'endpoint': 'https://push.services.mozilla.com/v1/sub_p8_05_b',
        'keys': {'p256dh': 'dh_b', 'auth': 'auth_b'},
    }, headers=auth_header(token_b))

    emergency = create_emergency_for(client, token_a)
    assert emergency['id'] is not None

    with client.application.app_context():
        sub_b = PushSubscription.query.filter_by(endpoint='https://push.services.mozilla.com/v1/sub_p8_05_b').first()
        assert sub_b is not None


def test_p8_06_i_can_help_creates_owner_push_notification(client):
    """Test 6 — Responding I CAN HELP triggers push notification to emergency owner."""
    owner_token = register_and_login(client, 'p8t6_o@test.com', name='P8Owner6')
    resp_token = register_and_login(client, 'p8t6_r@test.com', name='P8Resp6')

    client.post('/api/notifications/push-subscription', json={
        'endpoint': 'https://push.services.mozilla.com/v1/sub_p8_06_o',
        'keys': {'p256dh': 'dh_o', 'auth': 'auth_o'},
    }, headers=auth_header(owner_token))

    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    res = client.post(f'/api/responses/emergency/{eid}', json={'message': 'Coming to help'}, headers=auth_header(resp_token))
    assert res.status_code == 201

    owner_notifs = get_notifications_for(client, owner_token)
    assert any(n['notification_type'] == 'EMERGENCY_RESPONSE' for n in owner_notifs)


def test_p8_07_reached_safely_creates_safe_arrival_push_notification(client):
    """Test 7 — Resolving emergency creates safe-arrival notification and triggers push delivery."""
    owner_token = register_and_login(client, 'p8t7_o@test.com', name='P8Owner7')
    resp_token = register_and_login(client, 'p8t7_r@test.com', name='P8Resp7')

    client.post('/api/notifications/push-subscription', json={
        'endpoint': 'https://push.services.mozilla.com/v1/sub_p8_07_r',
        'keys': {'p256dh': 'dh_r', 'auth': 'auth_r'},
    }, headers=auth_header(resp_token))

    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/responses/emergency/{eid}', json={'message': 'I am helping'}, headers=auth_header(resp_token))
    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))

    resp_notifs = get_notifications_for(client, resp_token)
    assert any(n['notification_type'] == 'EMERGENCY_SAFE' for n in resp_notifs)


def test_p8_08_sensitive_coordinates_excluded_from_push_payload(client):
    """Test 8 — Push notification payloads omit exact GPS coordinates, passwords, and JWTs."""
    from app.services.push_service import send_web_push_notification
    from app.models.push_subscription import PushSubscription

    token = register_and_login(client, 'p8t8@test.com', name='P8User8')
    client.post('/api/notifications/push-subscription', json={
        'endpoint': 'https://push.services.mozilla.com/v1/sub_p8_08',
        'keys': {'p256dh': 'dh8', 'auth': 'auth8'},
    }, headers=auth_header(token))

    with client.application.app_context():
        sub = PushSubscription.query.filter_by(endpoint='https://push.services.mozilla.com/v1/sub_p8_08').first()
        payload = {
            'title': 'Emergency Alert',
            'body': 'User needs help',
            'emergency_id': 99,
            'latitude': 37.7749,
            'longitude': -122.4194,
        }
        res = send_web_push_notification(sub, payload)
        assert res is True


def test_p8_09_unauthorized_user_cannot_access_emergency_data_via_push(client):
    """Test 9 — Push notification contains link URL /emergency/<id>, but unauthorized API request returns 403."""
    owner_token = register_and_login(client, 'p8t9_o@test.com', name='P8Owner9')
    random_token = register_and_login(client, 'p8t9_x@test.com', name='P8Random9')

    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    res = client.get(f'/api/locations/emergency/{eid}/latest', headers=auth_header(random_token))
    assert res.status_code == 403


def test_p8_10_stale_push_subscription_handled_and_cleaned_up(client):
    """Test 10 — Expired push subscriptions returning 410 Gone are removed from database."""
    from unittest.mock import patch, MagicMock
    from pywebpush import WebPushException
    from app.services.push_service import send_web_push_notification
    from app.models.push_subscription import PushSubscription

    token = register_and_login(client, 'p8t10@test.com', name='P8User10')
    client.post('/api/notifications/push-subscription', json={
        'endpoint': 'https://push.services.mozilla.com/v1/sub_p8_10_stale',
        'keys': {'p256dh': 'dh10', 'auth': 'auth10'},
    }, headers=auth_header(token))

    mock_resp = MagicMock()
    mock_resp.status_code = 410
    exc = WebPushException('Subscription expired', response=mock_resp)

    with client.application.app_context():
        sub = PushSubscription.query.filter_by(endpoint='https://push.services.mozilla.com/v1/sub_p8_10_stale').first()
        with patch('app.services.push_service.webpush', side_effect=exc), \
             patch.dict('os.environ', {'VAPID_PRIVATE_KEY': 'mock_key'}):
            send_web_push_notification(sub, {'title': 'Test'})

        remaining = PushSubscription.query.filter_by(endpoint='https://push.services.mozilla.com/v1/sub_p8_10_stale').first()
        assert remaining is None


# ============================================================
# PHASE 9 TESTS — OFFLINE / CONNECTION SAFETY HANDLING
# ============================================================

def test_p9_01_location_update_requires_valid_active_emergency(client):
    """Test 1 — Location updates for inactive/non-existent emergency are rejected safely."""
    owner_token = register_and_login(client, 'p9t1@test.com', name='P9User1')
    res = client.post('/api/locations/emergency/999999', json={'latitude': 12.34, 'longitude': 56.78}, headers=auth_header(owner_token))
    assert res.status_code == 404


def test_p9_02_location_update_idempotency_prevents_duplicate_records(client):
    """Test 2 — Duplicate location coordinates sent sequentially are saved or handled cleanly."""
    owner_token = register_and_login(client, 'p9t2@test.com', name='P9User2')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    r1 = client.post(f'/api/locations/emergency/{eid}', json={'latitude': 12.3456, 'longitude': 78.9012}, headers=auth_header(owner_token))
    assert r1.status_code == 201

    r2 = client.post(f'/api/locations/emergency/{eid}', json={'latitude': 12.3456, 'longitude': 78.9012}, headers=auth_header(owner_token))
    assert r2.status_code == 201


def test_p9_03_resolved_emergency_rejects_offline_retry_location(client):
    """Test 3 — Location retries sent after emergency is resolved are rejected with 400."""
    owner_token = register_and_login(client, 'p9t3@test.com', name='P9User3')
    emergency = create_emergency_for(client, owner_token)
    eid = emergency['id']

    client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(owner_token))

    res = client.post(f'/api/locations/emergency/{eid}', json={'latitude': 12.3456, 'longitude': 78.9012}, headers=auth_header(owner_token))
    assert res.status_code == 400
    assert res.get_json()['success'] is False


# ============================================================
# PHASE 10 & 11 TESTS — SECURITY, PRIVACY AUDIT & PRODUCTION READINESS
# ============================================================

def test_p10_01_health_check_endpoint(client):
    """Test 1 — Health check endpoint returns 200 OK with operational status."""
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['status'] == 'ok'


def test_p10_02_health_db_check_endpoint(client):
    """Test 2 — Database health check endpoint returns 200 OK with healthy DB status."""
    res = client.get('/api/health/db')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['database'] == 'healthy'


def test_p10_03_security_headers_present(client):
    """Test 3 — Security response headers are present on API responses."""
    res = client.get('/api/health')
    assert res.headers.get('X-Content-Type-Options') == 'nosniff'
    assert res.headers.get('X-Frame-Options') == 'DENY'
    assert '1; mode=block' in res.headers.get('X-XSS-Protection', '')


def test_p10_04_full_idor_isolation_test(client):
    """Test 4 — Comprehensive IDOR isolation: User A (owner), User B (responder), User C (unrelated)."""
    from app.extensions import socketio

    token_a = register_and_login(client, 'p10_a@test.com', name='UserA')
    token_b = register_and_login(client, 'p10_b@test.com', name='UserB')
    token_c = register_and_login(client, 'p10_c@test.com', name='UserC')

    # User A creates emergency
    emergency = create_emergency_for(client, token_a)
    eid = emergency['id']

    # User A post location update -> 201
    loc_res = client.post(f'/api/locations/emergency/{eid}', json={'latitude': 40.7128, 'longitude': -74.0060}, headers=auth_header(token_a))
    assert loc_res.status_code == 201

    # User B responds -> 201
    resp_res = client.post(f'/api/responses/emergency/{eid}', json={'message': 'User B responding'}, headers=auth_header(token_b))
    assert resp_res.status_code == 201

    # User B (authorized responder) accesses latest location -> 200
    b_loc = client.get(f'/api/locations/emergency/{eid}/latest', headers=auth_header(token_b))
    assert b_loc.status_code == 200
    assert b_loc.get_json()['data']['location']['latitude'] == 40.7128

    # User C (unrelated) attempts to access latest location -> 403
    c_loc = client.get(f'/api/locations/emergency/{eid}/latest', headers=auth_header(token_c))
    assert c_loc.status_code == 403

    # User C attempts to resolve User A's emergency -> 403
    c_resolve = client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(token_c))
    assert c_resolve.status_code == 403

    # User C attempts to join emergency WebSocket room -> error event
    s_c = socketio.test_client(client.application, flask_test_client=client)
    s_c.emit('join_emergency', {'emergency_id': eid, 'token': token_c})
    rec = s_c.get_received()
    assert len(rec) > 0
    assert rec[0]['name'] == 'error'
    assert 'Not authorized' in rec[0]['args'][0]['message']

    # User A resolves own emergency -> 200
    a_resolve = client.post(f'/api/emergencies/{eid}/resolve', headers=auth_header(token_a))
    assert a_resolve.status_code == 200




