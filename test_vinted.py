import requests

WEBHOOK_URL = "COLLE ICI TON WEBHOOK DISCORD"  # Remplace par ton webhook

data = {
    "content": "Salut, test d'envoi via webhook Discord !"
}

response = requests.post(WEBHOOK_URL, json=data)

print("Status code:", response.status_code)
print("Response text:", response.text)




