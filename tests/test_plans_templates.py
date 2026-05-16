from app.models import db, User, Plan, Session
from werkzeug.security import generate_password_hash


def create_user(email="test@example.com"):
    user = User(
        first_name="Test",
        last_name="User",
        email=email,
        password_hash=generate_password_hash("Password123", method="pbkdf2:sha256")
    )
    db.session.add(user)
    db.session.commit()
    return user


def login(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id


def test_plan_create_edit_delete(client, app):
    user = create_user()
    login(client, user)

    # create plan
    response = client.post("/plan/new", data={
        "title": "Test Plan",
        "description": "Original description",
        "start_date": "2026-05-01",
        "end_date": "2026-05-10"
    }, follow_redirects=True)

    assert response.status_code == 200
    plan = Plan.query.filter_by(title="Test Plan").first()
    assert plan is not None
    assert plan.description == "Original description"
    assert plan.user_id == user.id

    # edit plan
    response = client.post(f"/plan/{plan.id}/edit", data={
        "title": "Updated Plan",
        "description": "Updated description",
        "start_date": "2026-05-02",
        "end_date": "2026-05-12"
    }, follow_redirects=True)

    assert response.status_code == 200
    updated_plan = db.session.get(Plan, plan.id)
    assert updated_plan.title == "Updated Plan"
    assert updated_plan.description == "Updated description"

    # delete plan
    response = client.post(f"/plan/{plan.id}/delete", follow_redirects=True)

    assert response.status_code == 200
    deleted_plan = db.session.get(Plan, plan.id)
    assert deleted_plan is None


def test_templates_list_only_templates(client, app):
    user = create_user()
    other_user = create_user("other@example.com")

    private_plan = Plan(
        title="Private Plan",
        description="Should not appear",
        is_template=False,
        user_id=other_user.id
    )

    template_plan = Plan(
        title="Public Template",
        description="Should appear",
        is_template=True,
        user_id=other_user.id
    )

    db.session.add(private_plan)
    db.session.add(template_plan)
    db.session.commit()

    login(client, user)

    response = client.get("/templates")

    assert response.status_code == 200
    assert b"Public Template" in response.data
    assert b"Private Plan" not in response.data


def test_template_copy_creates_new_plan(client, app):
    owner = create_user("owner@example.com")
    user = create_user("copyuser@example.com")

    template = Plan(
        title="Template Plan",
        description="Template description",
        is_template=True,
        user_id=owner.id
    )
    db.session.add(template)
    db.session.flush()

    session = Session(
        title="Template Session",
        session_type="revision",
        status="done",
        notes="Template notes",
        checklist='[{"text": "Read notes", "done": false}]',
        plan_id=template.id
    )
    db.session.add(session)
    db.session.commit()

    login(client, user)

    response = client.post(f"/templates/{template.id}/copy", follow_redirects=True)

    assert response.status_code == 200

    copied_plan = Plan.query.filter_by(
        user_id=user.id,
        title="Template Plan (copy)"
    ).first()

    assert copied_plan is not None
    assert copied_plan.description == "Template description"
    assert copied_plan.is_template is False

    copied_session = Session.query.filter_by(plan_id=copied_plan.id).first()
    assert copied_session is not None
    assert copied_session.title == "Template Session"
    assert copied_session.status == "notstarted"
    assert copied_session.notes == "Template notes"