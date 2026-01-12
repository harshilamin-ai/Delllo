import requests
spec = requests.get("http://127.0.0.1:8001/openapi.json").json()
for path, data in spec["paths"].items():
    for method in data:
        print(f"{method.upper():5} {path}")
