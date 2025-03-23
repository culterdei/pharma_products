from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import pytest
from .db import Base
from .main import app
from .utils import get_password_hash, create_access_token
from app.crud.user_crud import UserCRUD
from app.crud.product_crud import ProductCRUD
from app.schemas.user import UserCreate


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function", autouse=True)
def db_session(db_engine):
    session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)()

    yield session

    session.rollback()

    for table in reversed(Base.metadata.sorted_tables):
        session.execute(text(f"DELETE FROM {table.name};"))
        session.commit()

    session.close()


class TestAuthentication:
    def test_login_form_get(self, client):
        response = client.get('/login_form')
        assert response.status_code == 200
        assert 'auth_form.html' in response.template.name

    def test_invalid_credentials(self, client):
        response = client.post("/login", data={
            "username": "test",
            "password": "wrong",
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    def test_valid_credentials(self, client, db_session):
        response = client.post("/login_form", data={
            "username": "testuser",
            "password": "testpass",
        })
        assert response.status_code == 200
        assert response.context["current_user"].username == "testuser"

    def test_logout(self, client, db_session):
        login_response = client.post("/login_form", data={
            "username": "testuser1",
            "password": "testpass",
        })
        response = client.get("/logout", cookies=login_response.cookies)
        assert response.status_code == 200
        assert "access_token" not in response.cookies

class TestProducts:
    def test_create_product_form_unauthenticated(self, client):
        response = client.get('/products/create')
        assert response.status_code == 422

    def test_create_product_authenticated(self, client, db_session):
        test_user = UserCreate(username="testuser2", hashed_password=get_password_hash("testpass"))
        user = UserCRUD.create(db_session, test_user)
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires,
        )
        client.cookies = {"access_token": f"Bearer {access_token}"}
        response = client.post("/products/create", data={
            "name": "Test Product",
            "description": "Description",
            "area": "Area",
            "regions": "Region",
            "ingredients": "Ingredient",
        })
        client.cookies = None
        assert response.status_code == 200
        product = ProductCRUD.get(db_session, 1)
        assert product.name == "Test Product"
        assert product.user_id == user.id

    def test_update_product_ownership_check(self, client, db_session):
        login_response1 = client.post("/login_from", data={
            "username": "user1",
            "password": "pass1",
        })
        client.post("/products/create", cookies=login_response1.cookies, data={
            "name": "User1 Product",
            "description": "Desc",
            "area": "Area",
            "regions": "Region",
            "ingredients": "Ingredient",
        })
        login_response2 = client.post("/login_form", data={
            "username": "user2",
            "password": "pass2",
        })
        response = client.post("/products/edit/1", cookies=login_response2.cookies, data={
            "name": "Modified Product",
            "description": "New Desc",
            "area": "New Area",
            "regions": "New Region",
            "ingredients": "New Ingredient",
        })
        assert response.status_code == 422

    def test_search_products(self, client, db_session):
        test_user = UserCreate(username="testuser3", hashed_password=get_password_hash("testpass"))
        UserCRUD.create(db_session, test_user)
        login_response = client.post("/login", data={
            "username": "testuser3",
            "password": "testpass",
        })
        client.post("/products/create", cookies=login_response.cookies, data={
            "name": "Test Product",
            "description": "Description",
            "area": "Area1",
            "regions": "Region1",
            "ingredients": "Ingredient",
        })
        client.post("/products/create", cookies=login_response.cookies, data={
            "name": "Another Product",
            "description": "Desc",
            "area": "Area2",
            "regions": "Region2",
            "ingredients": "Ingredient",
        })
        response = client.get("/products/search", cookies=login_response.cookies, params={
            "area": "Area1",
            "region": "Region1"
        })
        assert response.status_code == 200
        assert len(response.context["products"]) == 1
        assert response.context["areas"] == ["Area1"]

