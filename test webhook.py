import requests

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1424838729272655938/xcXUXdPipAQO41z8m92st7th0krihjIlcsRNJTbhEv2x0vg2EVjR1GWvqdEgRCxhThQO"  # Remplace par ton webhook

data = {
    "content": "Salut, test d'envoi via webhook Discord !"
}

response = requests.post(WEBHOOK_URL, json=data)

print("Status code:", response.status_code)
print("Response text:", response.text)
