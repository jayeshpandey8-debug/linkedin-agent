"""
get_linkedin_token.py
Run this ONCE to get your LinkedIn access token.
Steps:
  1. Run: python get_linkedin_token.py
  2. Browser opens → log into LinkedIn
  3. Token printed in terminal → paste into .env
"""

import http.server
import urllib.parse
import webbrowser
import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("LINKEDIN_CLIENT_ID") or input("LinkedIn Client ID: ").strip()
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET") or input("LinkedIn Client Secret: ").strip()
REDIRECT_URI  = "http://localhost:8080/callback"
SCOPE         = "openid profile w_member_social"

AUTH_URL = (
    f"https://www.linkedin.com/oauth/v2/authorization"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&scope={urllib.parse.quote(SCOPE)}"
)

print(f"\n[OAuth] Opening browser for LinkedIn login...")
webbrowser.open(AUTH_URL)

auth_code = None

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        params    = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h2>Done! You can close this tab.</h2>")
        print("[OAuth] Code received.")

    def log_message(self, *args):
        pass

print("Waiting for LinkedIn callback on http://localhost:8080/callback ...")
http.server.HTTPServer(("localhost", 8080), CallbackHandler).handle_request()

if not auth_code:
    print("ERROR: No auth code received.")
    sys.exit(1)

print("Exchanging code for token...")
resp = requests.post(
    "https://www.linkedin.com/oauth/v2/accessToken",
    data={
        "grant_type":    "authorization_code",
        "code":          auth_code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
    timeout=15,
)

if resp.status_code == 200:
    data    = resp.json()
    token   = data.get("access_token", "")
    expires = data.get("expires_in", 0)

    print("\n" + "═"*60)
    print(f"✅ TOKEN (valid {expires//86400} days):\n\n{token}\n")
    print("═"*60)
    print("\nAdd to your .env file:")
    print(f"LINKEDIN_ACCESS_TOKEN={token}")

    # Fetch URN
    me = requests.get(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if me.status_code == 200:
        uid = me.json().get("id", "")
        print(f"LINKEDIN_PERSON_URN=urn:li:person:{uid}")
else:
    print(f"ERROR: {resp.status_code} {resp.text}")
