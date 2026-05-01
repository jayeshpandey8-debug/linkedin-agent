"""
linkedin_api.py
LinkedIn UGC Posts API integration.
Handles posting, token verification, OAuth flow.
"""

import requests
import config

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

def _headers():
    return {
        "Authorization":  f"Bearer {config.LINKEDIN_ACCESS_TOKEN}",
        "Content-Type":   "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def verify_token() -> dict:
    resp = requests.get(f"{LINKEDIN_API_BASE}/userinfo", headers=_headers(), timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print(f"[LinkedIn] Token valid — {data.get('name', '?')}")
        return data
    print(f"[LinkedIn] Token invalid: {resp.status_code}")
    return {}


def get_person_urn() -> str:
    if config.LINKEDIN_PERSON_URN:
        return config.LINKEDIN_PERSON_URN
    resp = requests.get(f"{LINKEDIN_API_BASE}/me", headers=_headers(), timeout=10)
    if resp.status_code == 200:
        uid = resp.json().get("id", "")
        return f"urn:li:person:{uid}"
    raise RuntimeError(f"Cannot fetch URN: {resp.status_code} {resp.text}")


def post_to_linkedin(post_text: str) -> dict:
    """
    Post text to LinkedIn. Returns success/failure dict.
    For poll format, post as text post with the poll options included
    (LinkedIn Poll API requires special permissions not in basic tier).
    """
    if not config.LINKEDIN_ACCESS_TOKEN:
        return {"success": False, "post_id": None, "error": "No access token."}

    try:
        person_urn = get_person_urn()
    except Exception as e:
        return {"success": False, "post_id": None, "error": str(e)}

    payload = {
        "author":         person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary":    {"text": post_text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    resp = requests.post(
        f"{LINKEDIN_API_BASE}/ugcPosts",
        headers=_headers(),
        json=payload,
        timeout=15,
    )

    if resp.status_code in (200, 201):
        post_id = resp.headers.get("X-RestLi-Id", "")
        print(f"[LinkedIn] ✅ Posted — ID: {post_id}")
        return {"success": True, "post_id": post_id, "error": None}
    else:
        print(f"[LinkedIn] ❌ Failed: {resp.status_code} {resp.text}")
        return {"success": False, "post_id": None, "error": resp.text}


def get_oauth_url(redirect_uri: str) -> str:
    scope = "openid profile w_member_social"
    return (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={config.LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope.replace(' ', '%20')}"
    )


def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  redirect_uri,
            "client_id":     config.LINKEDIN_CLIENT_ID,
            "client_secret": config.LINKEDIN_CLIENT_SECRET,
        },
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json()
    print(f"[LinkedIn] Token exchange failed: {resp.status_code} {resp.text}")
    return {}
