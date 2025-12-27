"""
Test suite for Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check structure of an activity
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_have_required_fields(self):
        """Test that all activities have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Activity {activity_name} missing {field}"


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=student@test.com"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "student@test.com" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        # Get initial participants
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()["Chess Club"]["participants"].copy()
        
        # Sign up
        test_email = "newstudent@test.com"
        signup_response = client.post(
            f"/activities/Chess%20Club/signup?email={test_email}"
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()["Chess Club"]["participants"]
        assert test_email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1

    def test_signup_duplicate_student(self):
        """Test that a student cannot sign up twice for the same activity"""
        email = "duplicate@test.com"
        
        # First signup
        response1 = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Try to sign up again
        response2 = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@test.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_invalid_email(self):
        """Test signup with various email formats"""
        # This tests that the endpoint accepts the parameter
        response = client.post(
            "/activities/Chess%20Club/signup?email=noemail"
        )
        # FastAPI doesn't validate email format by default without a validator
        assert response.status_code == 200

    def test_signup_different_activities(self):
        """Test that a student can sign up for multiple different activities"""
        email = "multi@test.com"
        
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            f"/activities/Drama%20Club/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify in both activities
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Drama Club"]["participants"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unregister@test.com"
        
        # First sign up
        client.post(
            f"/activities/Tennis%20Club/signup?email={email}"
        )
        
        # Then unregister
        response = client.delete(
            f"/activities/Tennis%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "remove@test.com"
        
        # Sign up
        client.post(
            f"/activities/Gym%20Class/signup?email={email}"
        )
        
        # Get count before unregister
        before = client.get("/activities").json()["Gym Class"]["participants"]
        assert email in before
        initial_count = len(before)
        
        # Unregister
        response = client.delete(
            f"/activities/Gym%20Class/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        after = client.get("/activities").json()["Gym Class"]["participants"]
        assert email not in after
        assert len(after) == initial_count - 1

    def test_unregister_nonexistent_activity(self):
        """Test unregister from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=student@test.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up(self):
        """Test unregister when student is not signed up"""
        response = client.delete(
            "/activities/Basketball%20Team/unregister?email=notsigndup@test.com"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_twice(self):
        """Test that a student cannot unregister twice"""
        email = "twiceunreg@test.com"
        
        # Sign up
        client.post(
            f"/activities/Robotics%20Club/signup?email={email}"
        )
        
        # First unregister
        response1 = client.delete(
            f"/activities/Robotics%20Club/unregister?email={email}"
        )
        assert response1.status_code == 200
        
        # Try to unregister again
        response2 = client.delete(
            f"/activities/Robotics%20Club/unregister?email={email}"
        )
        assert response2.status_code == 400


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Redirect status
        assert response.headers["location"] == "/static/index.html"


class TestParticipantManagement:
    """Integration tests for participant management"""

    def test_signup_and_unregister_workflow(self):
        """Test complete workflow of signing up and unregistering"""
        email = "workflow@test.com"
        activity = "Art%20Studio"
        
        # Initial check
        activities = client.get("/activities").json()
        initial_count = len(activities["Art Studio"]["participants"])
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        activities = client.get("/activities").json()
        assert email in activities["Art Studio"]["participants"]
        assert len(activities["Art Studio"]["participants"]) == initial_count + 1
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregister
        activities = client.get("/activities").json()
        assert email not in activities["Art Studio"]["participants"]
        assert len(activities["Art Studio"]["participants"]) == initial_count

    def test_multiple_participants_management(self):
        """Test managing multiple participants in an activity"""
        activity = "Debate%20Team"
        emails = [f"debate{i}@test.com" for i in range(3)]
        
        # Sign up multiple students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all are signed up
        activities = client.get("/activities").json()
        for email in emails:
            assert email in activities["Debate Team"]["participants"]
        
        # Remove one
        response = client.delete(f"/activities/{activity}/unregister?email={emails[0]}")
        assert response.status_code == 200
        
        # Verify only that one was removed
        activities = client.get("/activities").json()
        assert emails[0] not in activities["Debate Team"]["participants"]
        assert emails[1] in activities["Debate Team"]["participants"]
        assert emails[2] in activities["Debate Team"]["participants"]
