import unittest
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_session
from app.dependencies import Memberships, ProgressReports
from app.models import Assignment, Notification, User
from app.repositories.auth import AuthRepository
from app.repositories.user import UserRepository
from app.security import AuthSettings, create_access_token, decode_access_token, hash_password, verify_password
from app.services.auth import AuthService
from app.schemas.user import UserView
from app.services.base import WorkflowError
from bootstrap_hr import bootstrap_hr
from main import create_app


class TrainingAPITest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.addCleanup(self.engine.dispose)

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, connection_record):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.engine)

        def override_session():
            with Session(self.engine, expire_on_commit=False) as session:
                yield session

        @asynccontextmanager
        async def test_lifespan(application):
            yield

        self.settings = AuthSettings(secret_key="test-only-key-not-for-production-0123456789")
        self.app = create_app(lifespan_handler=test_lifespan, auth_settings=self.settings)
        self.app.dependency_overrides[get_session] = override_session
        self.client = self.enterContext(TestClient(self.app))
        self.password = "secure-test-password"
        self.tokens = {}
        with Session(self.engine, expire_on_commit=False) as session:
            user = User(name="HR", email="hr@example.com", role="hr")
            session.add(user)
            session.commit()
            self.hr = UserView.model_validate(user).model_dump(mode="json")
            AuthService(AuthRepository(session), UserRepository(session)).set_password(user.id, self.password)
        self.tokens[self.hr["id"]] = self.login(self.hr["email"])
        self.client.headers.update(self.headers(self.hr["id"]))
        self.manager = self.post("/api/staff", {"name": "Manager", "email": "manager@example.com", "role": "manager"})
        self.provision(self.manager)
        self.trainees = [self.post("/api/trainees", {
            "name": f"Trainee {index}", "email": f"trainee{index}@example.com", "onboarded_by_id": self.hr["id"],
        }) for index in range(3)]
        for trainee in self.trainees:
            self.provision(trainee)
        self.plan = self.post("/api/plans", {
            "title": "Python foundations", "description": "Complete the exercises", "manager_id": self.manager["id"],
        })

    def login(self, email, password=None):
        response = self.client.post("/api/auth/token", data={
            "grant_type": "password", "username": email,
            "password": password or self.password,
        })
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["access_token"]

    def headers(self, user_id):
        return {"Authorization": f"Bearer {self.tokens[user_id]}"}

    def provision(self, user):
        response = self.client.put(f"/api/auth/accounts/{user['id']}/password", json={"password": self.password})
        self.assertEqual(response.status_code, 204, response.text)
        self.tokens[user["id"]] = self.login(user["email"])

    def post(self, path, data, actor_id=None):
        if actor_id is None:
            if path in ("/api/staff", "/api/trainees"):
                actor_id = self.hr["id"]
            elif path.endswith("/reports"):
                actor_id = data["trainee_id"]
            else:
                actor_id = self.manager["id"]
        response = self.client.post(path, json=data, headers=self.headers(actor_id))
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_app_factory_creates_isolated_instances(self):
        other_app = create_app()
        self.assertIsNot(self.app, other_app)
        self.assertEqual(other_app.dependency_overrides, {})
        self.assertEqual(self.app.openapi(), other_app.openapi())

    def test_oauth_login_and_revocation(self):
        password = "secure-test-password"
        with Session(self.engine, expire_on_commit=False) as session:
            AuthService(AuthRepository(session), UserRepository(session)).set_password(self.hr["id"], password)
        response = self.client.post("/api/auth/token", data={
            "grant_type": "password", "username": self.hr["email"], "password": password,
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        profile = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(profile.json()["id"], self.hr["id"])
        self.assertNotIn("password_hash", profile.json())
        for email in (self.hr["email"], "missing@example.com"):
            failed = self.client.post("/api/auth/token", data={"username": email, "password": "wrong-password"})
            self.assertEqual(failed.status_code, 401)
            self.assertEqual(failed.headers["WWW-Authenticate"], "Bearer")
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        response = self.client.post("/api/auth/password", headers=headers, json={
            "current_password": password, "new_password": "updated-secure-password",
        })
        self.assertEqual(response.status_code, 204, response.text)
        self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 401)
        response = self.client.post("/api/auth/token", data={"username": self.hr["email"], "password": "updated-secure-password"})
        new_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        self.assertEqual(self.client.post("/api/auth/logout", headers=new_headers).status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me", headers=new_headers).status_code, 401)

    def test_every_workflow_route_requires_authentication(self):
        schema = self.app.openapi()
        public = {"/", "/api/health", "/api/auth/token"}
        for path, operations in schema["paths"].items():
            if path in public:
                continue
            resolved = path
            for parameter in ("user_id", "trainee_id", "cohort_id", "plan_id", "assignment_id", "report_id", "notification_id"):
                resolved = resolved.replace("{" + parameter + "}", "1")
            for method, operation in operations.items():
                with self.subTest(path=path, method=method):
                    self.assertEqual(operation["security"], [{"OAuth2PasswordBearer": []}])
                    response = self.client.request(method, resolved, headers={"Authorization": ""}, json={})
                    self.assertEqual(response.status_code, 401, response.text)
                    self.assertEqual(response.headers["WWW-Authenticate"], "Bearer")
        self.assertEqual(self.client.get("/api/health", headers={"Authorization": ""}).status_code, 200)

    def test_invalid_tokens_and_database_roles(self):
        token = self.tokens[self.trainees[0]["id"]]
        claims = jwt.decode(token, self.settings.secret_key, algorithms=["HS256"], audience=self.settings.audience)
        expired = jwt.encode({**claims, "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, self.settings.secret_key, algorithm="HS256")
        for invalid in ("not-a-token", token + "tampered", expired):
            response = self.client.get("/api/auth/me", headers={"Authorization": "Bearer " + invalid})
            self.assertEqual(response.status_code, 401)
        role_claim = jwt.encode({**claims, "role": "hr"}, self.settings.secret_key, algorithm="HS256")
        response = self.client.post("/api/staff", headers={"Authorization": "Bearer " + role_claim}, json={
            "name": "Escalation", "email": "escalation@example.com", "role": "hr",
        })
        self.assertEqual(response.status_code, 403)
        with Session(self.engine) as session:
            session.get(User, self.manager["id"]).role = "trainee"
            session.commit()
        response = self.client.post("/api/plans", headers=self.headers(self.manager["id"]), json={
            "title": "Escalation", "description": "Invalid", "manager_id": self.manager["id"],
        })
        self.assertEqual(response.status_code, 403)

    def test_actor_spoofing_and_role_permissions(self):
        manager_headers = self.headers(self.manager["id"])
        trainee_headers = self.headers(self.trainees[0]["id"])
        for path in ("/api/plans", "/api/cohorts"):
            body = {"manager_id": self.hr["id"], "name": "Spoof"} if path.endswith("cohorts") else {
                "manager_id": self.hr["id"], "title": "Spoof", "description": "Invalid",
            }
            self.assertEqual(self.client.post(path, headers=manager_headers, json=body).status_code, 403)
        self.assertEqual(self.client.get("/api/trainees", headers=trainee_headers).status_code, 403)
        self.assertEqual(self.client.get(f"/api/trainees/{self.trainees[1]['id']}", headers=trainee_headers).status_code, 403)
        for headers in (manager_headers, trainee_headers):
            self.assertEqual(self.client.post("/api/staff", headers=headers, json={
                "name": "Unauthorized", "email": "unauthorized@example.com", "role": "hr",
            }).status_code, 403)
            self.assertEqual(self.client.put(f"/api/auth/accounts/{self.hr['id']}/password", headers=headers, json={
                "password": "unauthorized-password",
            }).status_code, 403)
        assignment = self.post(f"/api/plans/{self.plan['id']}/assignments", {"trainee_id": self.trainees[0]["id"]})[0]
        response = self.client.post(f"/api/assignments/{assignment['id']}/reports", headers=trainee_headers, json={
            "trainee_id": self.trainees[1]["id"], "progress": 99, "summary": "Spoofed",
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get(f"/api/assignments/{assignment['id']}/reports").json(), [])

    def test_scoped_lists_and_cross_record_access(self):
        other = self.post("/api/staff", {"name": "Other Manager", "email": "other@example.com", "role": "manager"})
        self.provision(other)
        other_headers = self.headers(other["id"])
        trainee_id = self.trainees[0]["id"]
        trainee_headers = self.headers(trainee_id)
        other_plan = self.post("/api/plans", {
            "title": "Other Plan", "description": "Another track", "manager_id": other["id"],
        }, actor_id=other["id"])
        cohort = self.post("/api/cohorts", {"name": "Owned Cohort", "manager_id": self.manager["id"]})
        self.post(f"/api/cohorts/{cohort['id']}/members", {"trainee_id": trainee_id})
        self.assertEqual(self.client.get("/api/cohorts", headers=other_headers).json(), [])
        self.assertEqual(len(self.client.get("/api/cohorts", headers=trainee_headers).json()), 1)
        self.assertEqual(self.client.get(f"/api/cohorts/{cohort['id']}/members", headers=other_headers).status_code, 403)
        self.assertEqual(self.client.get("/api/plans", headers=trainee_headers).json(), [])
        self.assertEqual(self.client.get(f"/api/plans/{self.plan['id']}", headers=trainee_headers).status_code, 403)
        self.assertEqual(self.client.get("/api/plans?limit=1", headers=other_headers).json()[0]["id"], other_plan["id"])
        self.assertEqual(self.client.patch(f"/api/plans/{self.plan['id']}", headers=other_headers, json={"title": "Intrusion"}).status_code, 403)
        own_assignment = self.post(f"/api/plans/{self.plan['id']}/assignments", {"trainee_id": trainee_id})[0]
        self.post(f"/api/plans/{other_plan['id']}/assignments", {"trainee_id": trainee_id}, actor_id=other["id"])
        self.post(f"/api/plans/{self.plan['id']}/assignments", {"trainee_id": self.trainees[1]["id"]})
        self.assertEqual(len(self.client.get("/api/plans", headers=trainee_headers).json()), 2)
        scoped = self.client.get(f"/api/trainees/{trainee_id}/assignments", headers=other_headers).json()
        self.assertEqual([item["plan_id"] for item in scoped], [other_plan["id"]])
        self.assertEqual(self.client.get(f"/api/assignments/{own_assignment['id']}/reports", headers=other_headers).status_code, 403)
        self.assertEqual(self.client.get(f"/api/assignments/{own_assignment['id']}/reports", headers=self.headers(self.trainees[1]["id"])).status_code, 403)
        self.assertEqual(self.client.get(f"/api/trainees/{trainee_id}/assignments", headers=self.headers(self.trainees[1]["id"])).status_code, 403)
        self.assertEqual(self.client.get(f"/api/trainees/{trainee_id}/notifications", headers=self.headers(self.trainees[1]["id"])).status_code, 403)

    def test_hr_password_reset_revokes_tokens(self):
        trainee = self.trainees[0]
        headers = self.headers(trainee["id"])
        response = self.client.put(f"/api/auth/accounts/{trainee['id']}/password", json={"password": "short"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 200)
        response = self.client.put(f"/api/auth/accounts/{trainee['id']}/password", json={"password": "newly-provisioned-password"})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 401)
        new_token = self.login(trainee["email"], "newly-provisioned-password")
        self.assertEqual(self.client.get("/api/auth/me", headers={"Authorization": "Bearer " + new_token}).status_code, 200)

    def test_domain_dependencies_share_session(self):
        probe = FastAPI()
        probe.dependency_overrides[get_session] = self.app.dependency_overrides[get_session]

        @probe.get("/dependencies")
        def inspect_dependencies(reports: ProgressReports, memberships: Memberships):
            repositories = [
                reports.repository, reports.assignments.repository,
                reports.assignments.memberships, reports.plans.repository,
                reports.plans.assignments, reports.users.repository,
                reports.notifications.repository, memberships.repository,
                memberships.cohorts.repository,
            ]
            session = reports.repository.session
            return {
                "shared_session": all(repository.session is session for repository in repositories),
                "overridden_database": session.bind is self.engine,
                "cached_services": (
                    reports.assignments.plans is reports.plans
                    and memberships.users is reports.users
                    and reports.plans.assignments is reports.assignments.repository
                    and reports.assignments.notifications is reports.notifications
                ),
            }

        with TestClient(probe) as client:
            response = client.get("/dependencies")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {
            "shared_session": True, "overridden_database": True, "cached_services": True,
        })

    def test_cohort_and_solo_workflow(self):
        self.assertEqual(self.client.get("/api/health").json(), {"status": "healthy"})
        cohort = self.post("/api/cohorts", {"name": "October cohort", "manager_id": self.manager["id"]})
        for trainee in self.trainees[:2]:
            self.post(f"/api/cohorts/{cohort['id']}/members", {"trainee_id": trainee["id"]})
        assignments = self.post(f"/api/plans/{self.plan['id']}/assignments", {"cohort_id": cohort["id"]})
        self.assertEqual(len(assignments), 2)
        solo = self.post(f"/api/plans/{self.plan['id']}/assignments", {"trainee_id": self.trainees[2]["id"]})
        self.assertIsNone(solo[0]["cohort_id"])
        response = self.client.patch(f"/api/plans/{self.plan['id']}", json={"description": "Updated exercises"}, headers=self.headers(self.manager["id"]))
        self.assertEqual(response.status_code, 200, response.text)
        assignment = assignments[0]
        trainee_id = assignment["trainee_id"]
        report = self.post(f"/api/assignments/{assignment['id']}/reports", {
            "trainee_id": trainee_id, "progress": 60, "summary": "Completed first module",
        })
        response = self.client.patch(f"/api/reports/{report['id']}/feedback", json={
            "manager_id": self.manager["id"], "feedback": "Proceed to the next module",
        }, headers=self.headers(self.manager["id"]))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["reviewed_by_id"], self.manager["id"])
        reports = self.client.get(f"/api/assignments/{assignment['id']}/reports").json()
        self.assertEqual(reports[0]["feedback"], "Proceed to the next module")
        stored = self.client.get(f"/api/trainees/{trainee_id}/assignments").json()
        self.assertEqual(stored[0]["progress"], 60)
        notifications = self.client.get(f"/api/trainees/{trainee_id}/notifications", headers=self.headers(trainee_id)).json()
        self.assertEqual(len(notifications), 3)
        response = self.client.patch(f"/api/trainees/{trainee_id}/notifications/{notifications[0]['id']}/read", headers=self.headers(trainee_id))
        self.assertTrue(response.json()["is_read"])
        self.assertEqual(len(self.client.get("/api/trainees?offset=1&limit=1").json()), 1)

    def test_validation_roles_and_missing_records(self):
        response = self.client.post("/api/trainees", json={
            "name": "Invalid", "email": "new@example.com", "onboarded_by_id": self.manager["id"],
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get("/api/plans/999").status_code, 404)
        for target in ({}, {"cohort_id": 1, "trainee_id": 1}):
            self.assertEqual(self.client.post(f"/api/plans/{self.plan['id']}/assignments", json=target, headers=self.headers(self.manager["id"])).status_code, 422)
        for update in ({}, {"title": None}, {"title": " "}):
            self.assertEqual(self.client.patch(f"/api/plans/{self.plan['id']}", json=update, headers=self.headers(self.manager["id"])).status_code, 422)
        cohort = self.post("/api/cohorts", {"name": "Empty", "manager_id": self.manager["id"]})
        self.assertEqual(self.client.post(f"/api/plans/{self.plan['id']}/assignments", json={"cohort_id": cohort["id"]}, headers=self.headers(self.manager["id"])).status_code, 400)
        self.assertEqual(self.client.post("/api/staff", json={"name": "Duplicate", "email": "HR@EXAMPLE.COM", "role": "hr"}).status_code, 409)
        self.assertEqual(self.client.get("/api/trainees?limit=0").status_code, 422)

    def test_duplicate_assignment_is_atomic(self):
        cohort = self.post("/api/cohorts", {"name": "Cohort", "manager_id": self.manager["id"]})
        for trainee in self.trainees[:2]:
            self.post(f"/api/cohorts/{cohort['id']}/members", {"trainee_id": trainee["id"]})
        self.post(f"/api/plans/{self.plan['id']}/assignments", {"trainee_id": self.trainees[0]["id"]})
        response = self.client.post(f"/api/plans/{self.plan['id']}/assignments", json={"cohort_id": cohort["id"]}, headers=self.headers(self.manager["id"]))
        self.assertEqual(response.status_code, 409)
        with Session(self.engine) as session:
            self.assertEqual(len(list(session.scalars(select(Assignment)))), 1)
            self.assertEqual(len(list(session.scalars(select(Notification)))), 1)

    def test_report_and_notification_ownership(self):
        assignment = self.post(f"/api/plans/{self.plan['id']}/assignments", {"trainee_id": self.trainees[0]["id"]})[0]
        path = f"/api/assignments/{assignment['id']}/reports"
        self.assertEqual(self.client.post(path, json={"trainee_id": self.trainees[1]["id"], "progress": 50, "summary": "Wrong owner"}).status_code, 403)
        self.assertEqual(self.client.post(path, json={"trainee_id": self.trainees[0]["id"], "progress": 101, "summary": "Invalid progress"}, headers=self.headers(self.trainees[0]["id"])).status_code, 422)
        report = self.post(path, {"trainee_id": self.trainees[0]["id"], "progress": 50, "summary": "Done"})
        manager = self.post("/api/staff", {"name": "Other", "email": "other@example.com", "role": "manager"})
        self.provision(manager)
        self.assertEqual(self.client.patch(f"/api/reports/{report['id']}/feedback", json={"manager_id": manager["id"], "feedback": "Wrong manager"}, headers=self.headers(manager["id"])).status_code, 403)
        notifications = self.client.get(f"/api/trainees/{self.trainees[0]['id']}/notifications", headers=self.headers(self.trainees[0]["id"])).json()
        self.assertEqual(self.client.patch(f"/api/trainees/{self.trainees[1]['id']}/notifications/{notifications[0]['id']}/read", headers=self.headers(self.trainees[1]["id"])).status_code, 404)


class SecurityTest(unittest.TestCase):
    def setUp(self):
        self.settings = AuthSettings(secret_key="test-only-key-not-for-production-0123456789")

    def test_password_hashing(self):
        password_hash = hash_password("secure-test-password")
        self.assertNotEqual(password_hash, "secure-test-password")
        self.assertTrue(verify_password("secure-test-password", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))
        self.assertFalse(verify_password("password", "not-a-hash"))

    def test_token_validation(self):
        token = create_access_token(7, 2, self.settings)
        self.assertEqual(decode_access_token(token, self.settings), (7, 2))
        with self.assertRaises(jwt.InvalidTokenError):
            decode_access_token(token, AuthSettings(secret_key="different-test-key-not-for-production-12345"))
        claims = jwt.decode(token, self.settings.secret_key, algorithms=["HS256"], audience=self.settings.audience)
        for field, value in (
            ("exp", datetime.now(timezone.utc) - timedelta(seconds=1)),
            ("aud", "another-client"),
            ("iss", "another-issuer"),
            ("sub", "not-a-user"),
            ("ver", True),
        ):
            with self.subTest(field=field):
                invalid = jwt.encode({**claims, field: value}, self.settings.secret_key, algorithm="HS256")
                with self.assertRaises(jwt.InvalidTokenError):
                    decode_access_token(invalid, self.settings)

    def test_requires_secure_configuration(self):
        with self.assertRaises(ValueError):
            AuthSettings(secret_key="short")
        with self.assertRaises(ValueError):
            AuthSettings(secret_key=self.settings.secret_key, token_minutes=0)

    def test_bootstrap_preserves_existing_user_records(self):
        engine = create_engine("sqlite://")
        self.addCleanup(engine.dispose)
        User.__table__.create(engine)
        with Session(engine, expire_on_commit=False) as session:
            user = User(name="Existing HR", email="existing@example.com", role="hr")
            session.add(user)
            session.commit()
            original_id = user.id
            Base.metadata.create_all(engine)
            provisioned = bootstrap_hr("Existing HR", user.email, "secure-existing-password", session)
            self.assertEqual(provisioned.id, original_id)
            service = AuthService(AuthRepository(session), UserRepository(session))
            authenticated, credential = service.authenticate(user.email, "secure-existing-password")
            self.assertEqual(authenticated.id, original_id)
            with self.assertRaises(WorkflowError):
                bootstrap_hr("Existing HR", user.email, "replacement-password", session)
            self.assertTrue(verify_password("secure-existing-password", credential.password_hash))


if __name__ == "__main__":
    unittest.main()