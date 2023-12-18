"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc


from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.user1 = User.signup(username='testuser1', email='test1@test.com', password='password1', image_url = None)
        uid1 = 1111
        self.user1.id = uid1
        self.user2 = User.signup(username='testuser2', email='test2@test.com', password='password2', image_url =None)
        uid2 = 2222
        self.user2.id = uid2
        
        db.session.add(self.user1)
        db.session.add(self.user2)

        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transactions."""
        db.session.remove()
        db.drop_all()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(repr(u), f'<User #{u.id}: {u.username}, {u.email}>')

    ####
    #
    # Following tests
    #
    ####

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user1.following), 1)
        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(self.user1.following[0].id, self.user2.id)


        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))
        

    def test_is_followed_by(self):
        self.user1.followers.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user2.following), 1)
        self.assertEqual(len(self.user2.followers), 0)
        self.assertEqual(self.user1.followers[0].id, self.user2.id)


        self.assertTrue(self.user1.is_followed_by(self.user2))
        self.assertFalse(self.user2.is_followed_by(self.user1))

    
     ####
    #
    # Signup tests
    #
    ####

    def test_valid_signup(self):
        new_user = User.signup(username="newuser", email="new@example.com", password="password1", image_url=None)
        uid = 99999
        new_user.id = uid
        db.session.commit()

        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.id, 99999)
        self.assertEqual(new_user.username, "newuser")
        self.assertEqual(new_user.email, "new@example.com")
        self.assertNotEqual(new_user.password, "password1")
        # Bcrypt strings should start with $2b$
        self.assertTrue(new_user.password.startswith("$2b$"))

    def test_invalid_signup(self):
        invalid = User.signup(None, "test@test.com", "password", None)
        uid = 123456789
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_signup_duplicate_username(self):
        invalid = User.signup("testuser", "test2@test.com", "password", None)
        uid = 1234
        invalid.id = uid
        self.assertEqual(invalid.username, "testuser")

        invalid_duplicate = User.signup("testuser", "test22@test.com", "password", None)
        uid2 = 12345
        invalid_duplicate.id = uid2
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_signup_duplicate_email(self):
        invalid = User.signup("testuser1", "test2@test.com", "password", None)
        uid = 1234
        invalid.id = uid
        self.assertEqual(invalid.username, "testuser1")

        invalid_duplicate = User.signup("testuser2", "test2@test.com", "password", None)
        uid2 = 12345
        invalid_duplicate.id = uid2
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "email@email.com", None, None)

   ####
    #
    # Authentication tests
    #
    ####
    def test_valid_authentication(self):
        u = User.authenticate(self.user1.username, "password1")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.user1.id)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "password1"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.user1.username, "badpassword"))

