import urllib.request
import json

cities = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777)
}

for city, (lat, lon) in cities.items():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation&hourly=temperature_2m&timezone=Asia%2FKolkata"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            print(f"{city}: Current Temp = {data['current']['temperature_2m']} C, Precip = {data['current']['precipitation']} mm")
    except Exception as e:
        print(f"Failed for {city}: {e}")
