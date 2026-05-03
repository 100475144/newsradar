from app.tests.fixtures.auth import user_data, registered_user, auth_token, verify_user
from app.modules.auth.models import User
from app.core.security import verify_password, verify_token

"""
Verificar base de datos en casos necesarios, ejemplo: 
register es necesario porque forma parte de su responsabilidad modificar DB
login no es necesario porque no altera DB
token tampoco altera DB 
me tampoco altera DB
PROBLEMA: No se hace rollback tras cada test, los datos de test se quedan en DB.
"""

"""
TODO: Requisitos y matriz de trazabilidad de requisitos, por lo menos 
de los endpoints del API
TODO: Cerrar la base de datos (PostgreSQL) cuando los tests acaben
"""

############ TESTS /api/v1/auth/register ############

def test_register_success(client, db, user_data):
    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 201
    data = response.json()
    
    assert data["user"]["email"] == user_data["email"]
    assert data["user"]["first_name"] == user_data["first_name"]
    assert data["user"]["last_name"] == user_data["last_name"]
    assert data["user"]["organization"] == user_data["organization"]
    assert type(data["user"]["id"]) is int  

    # Valores por defecto en el registro
    assert data["user"]["role"] == "gestor"
    assert data["user"]["is_active"] is True
    assert data["user"]["is_verified"] is False

    assert data["user"]["created_at"] is not None
    assert data["user"]["updated_at"] is not None
   
   # Comprobar datos que se han almacenado en la BD
    user = db.query(User).filter_by(email=user_data["email"]).first()
    assert user is not None
    assert user.email == user_data["email"]
    assert user.first_name == user_data["first_name"]
    assert user.last_name == user_data["last_name"]
    assert user.organization == user_data["organization"]
    assert type(user.id) is int  
    # Verificamos el hash del password
    assert verify_password(user_data["password"], user.hashed_password) is True
    assert user.role == "gestor"
    assert user.is_active is True
    assert user.is_verified is False

    assert user.created_at is not None
    assert user.updated_at is not None


def test_register_duplicate_email(client, user_data, registered_user):
    #client.post("/api/v1/auth/register", json=user_data)

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 400
    assert "A user with this email already exists." in response.json()["detail"]

def test_register_invalid_email(client, user_data):
    user_data["email"] = "invalid-email"

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 422
    assert "value is not a valid email address" in response.json()["detail"][0]["msg"]
    #assert "value is not a valid email address: An email address must have an @-sign."

############ TESTS /api/v1/auth/verify-email ############

############ TESTS /api/v1/auth/resend-verification ############

############ TESTS /api/v1/auth/login ############
def test_login_success(client, verify_user):
    response = client.post("/api/v1/auth/login", json={
        "email": verify_user["email"],
        "password": verify_user["password"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verificar que el token es válido
    token = data["access_token"]
    payload = verify_token(token)
    assert payload["sub"] is not None

def test_login_wrong_password(client, registered_user):
    response = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    assert "Invalid email or password." in response.json()["detail"]

def test_login_user_not_found(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "noone@test.com",
        "password": "password123"
    })

    assert response.status_code == 401
    assert "Invalid email or password." in response.json()["detail"]

def test_login_inactive_user(client, db, registered_user):
    # desactivar usuario directamente en DB
    user = db.query(User).filter_by(email=registered_user["email"]).first()
    user.is_active = False
    db.commit()
    # verificar usuario en la BD

    response = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"]
    })

    assert response.status_code == 401
    assert "This user account is inactive." in response.json()["detail"]

############ TESTS /api/v1/auth/token ############

def test_token_success(client, verify_user):
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": verify_user["email"],
            "password": verify_user["password"]
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()

def test_token_invalid_credentials(client):
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "wrong@test.com",
            "password": "wrong"
        }
    )

    assert response.status_code == 401
    assert "Invalid email or password." in response.json()["detail"]

############ TESTS /api/v1/auth/me ############
def test_me(client, auth_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    assert "email" in response.json()

def test_me_no_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_me_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )

    assert response.status_code == 401

def test_me_user_deleted(client, db, auth_token, user_data):
    user = db.query(User).filter_by(email=user_data["email"]).first()
    db.delete(user)
    db.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 401
    assert "Could not validate credentials." in response.json()["detail"]

############ TESTS /api/v1/auth/users ############

############ TESTS /api/v1/auth/users/{user_id}/role ############

