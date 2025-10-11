import requests

url = "https://www.vinted.fr"
response = requests.get(url)

print("Code HTTP :", response.status_code)
print("Début du contenu :", response.text[:100])
