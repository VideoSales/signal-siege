import requests

BASE = "https://api.agentlot.io"

created = requests.post(
    BASE + "/api/v1/signal-siege/create",
    json={
        "name": "Sample Bot",
        "seats": 2,
        "fill_bots": True
    },
    timeout=20,
).json()

code = created["game"]["code"]
me = created["player_id"]

while True:
    game = requests.get(
        BASE + "/api/v1/signal-siege/state",
        params={"code": code},
        timeout=20,
    ).json()["game"]

    if game["status"] == "finished":
        print("winner:", game["winner"])
        break

    if game["current_player_id"] == me:
        requests.post(
            BASE + "/api/v1/signal-siege/move",
            json={
                "code": code,
                "player_id": me,
                "action": "expand",
            },
            timeout=20,
        )
