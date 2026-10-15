import requests

URL = "https://srsmatha.org/srsmatha_tatkal/main_web/tatkal.php"
res = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})

# Check if the page contains dynamic placeholders or actual numbers
print("Is 'Fetching Tatkal availability' in response?:", "Fetching Tatkal availability" in res.text)
print("Is 'Tatkal options available' in response?:", "Tatkal options available" in res.text)

# Save the raw HTML to inspect what python actually got
with open("dump.html", "w", encoding="utf-8") as f:
    f.write(res.text)
print("Saved raw HTML to dump.html")
