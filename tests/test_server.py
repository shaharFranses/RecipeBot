import hashlib, hmac, json, os, sys
os.environ.update(WHATSAPP_APP_SECRET="s3cret", WHATSAPP_VERIFY_TOKEN="vt", ALLOWED_NUMBERS="972500000000", SITE_URL="https://x.github.io/RecipeBot")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bot"))
from fastapi.testclient import TestClient
import server, storage, whatsapp
from extract import Recipe, Ingredient
from reel import Reel

sent = []
whatsapp.send_text = lambda to, t: sent.append((to, t))
server.whatsapp.send_text = whatsapp.send_text
server.storage.find_by_url = lambda u: None
saved = []
server.storage.save_recipe = lambda r, reel, added_by="": (saved.append((r, reel)) or {"id": "abc"})
server.fetch_reel = lambda u: Reel(url=u, caption="cap", author="a", thumbnail=None, video_path=None)
server.extract_recipe = lambda reel: Recipe(is_recipe=True, title="עוגת שוקולד", description="", servings="8", total_time="45 דקות",
    ingredients=[Ingredient(item="קמח", amount="2 כוסות")], steps=["לערבב", "לאפות"], tags=["קינוח"])

c = TestClient(server.app)
assert c.get("/webhook", params={"hub.mode":"subscribe","hub.verify_token":"vt","hub.challenge":"42"}).text == "42"
assert c.get("/webhook", params={"hub.mode":"subscribe","hub.verify_token":"bad","hub.challenge":"42"}).status_code == 403

def post(sender, text, mid):
    body = json.dumps({"entry":[{"changes":[{"value":{"messages":[{"id":mid,"from":sender,"type":"text","text":{"body":text}}]}}]}]}).encode()
    sig = "sha256=" + hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
    return c.post("/webhook", content=body, headers={"X-Hub-Signature-256": sig, "Content-Type":"application/json"})

assert c.post("/webhook", content=b"{}", headers={"X-Hub-Signature-256":"sha256=00"}).status_code == 401
assert post("972500000000", "תראי https://www.instagram.com/reels/DT0MRTbiHyV/?igsh=x", "m1").status_code == 200
post("972500000000", "dup https://www.instagram.com/reels/DT0MRTbiHyV/", "m1")   # duplicate id ignored
post("111", "https://www.instagram.com/reel/zzz/", "m2")                         # unknown number ignored
post("972500000000", "שלום", "m3")
print("saved url:", saved[0][1].url)
for to, t in sent: print("---", to); print(t)
assert len(saved) == 1 and saved[0][1].url == "https://www.instagram.com/reel/DT0MRTbiHyV"
print("OK")
