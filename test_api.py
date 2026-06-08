import requests

url = "https://easy-budget-analisis-pe.onrender.com/api"

# 1. Register
res = requests.post(f"{url}/auth/register", json={
    "name": "Test User",
    "email": "test@test.com",
    "password": "password123"
})
print("Register:", res.json())

# 2. Login
res = requests.post(f"{url}/auth/login", json={
    "email": "test@test.com",
    "password": "password123"
})
user = res.json().get("user")
print("Login:", res.json())

# 3. Add product
if user:
    res = requests.post(f"{url}/products", json={
        "user_id": user["id"],
        "name": "Test Product",
        "fixedCost": 100,
        "variableCost": 10,
        "salePrice": 20,
        "forecastUnits": 50,
        "stock": 5
    })
    print("Add Product:", res.json())
