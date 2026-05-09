"""
linkedin_api.py - Updated with image posting support
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
        print(f"[LinkedIn] Token valid — {data.get('name','?')}")
        return data
    print(f"[LinkedIn] Token invalid: {resp.status_code}")
    return {}


def get_person_urn() -> str:
    if config.LINKEDIN_PERSON_URN:
        return config.LINKEDIN_PERSON_URN
    resp = requests.get(f"{LINKEDIN_API_BASE}/me", headers=_headers(), timeout=10)
    if resp.status_code == 200:
        uid = resp.json().get("id","")
        return f"urn:li:person:{uid}"
    raise RuntimeError(f"Cannot fetch URN: {resp.status_code} {resp.text}")


def register_image_upload(person_urn: str) -> dict | None:
    """Step 1: Register image upload with LinkedIn."""
    url = f"{LINKEDIN_API_BASE}/assets?action=registerUpload"
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": person_urn,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    try:
        resp = requests.post(url, headers=_headers(), json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            asset = data["value"]["asset"]
            upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            print(f"[LinkedIn] Image registered. Asset: {asset}")
            return {"asset": asset, "upload_url": upload_url}
    except Exception as e:
        print(f"[LinkedIn] Register image error: {e}")
    return None


def upload_image_bytes(upload_url: str, image_bytes: bytes) -> bool:
    """Step 2: Upload image bytes to LinkedIn."""
    try:
        resp = requests.put(
            upload_url,
            data=image_bytes,
            headers={"Authorization": f"Bearer {config.LINKEDIN_ACCESS_TOKEN}"},
            timeout=30,
        )
        if resp.status_code in (200, 201):
            print("[LinkedIn] Image uploaded successfully.")
            return True
        print(f"[LinkedIn] Image upload failed: {resp.status_code}")
    except Exception as e:
        print(f"[LinkedIn] Upload error: {e}")
    return False


def post_to_linkedin(post_text: str, image_bytes: bytes = None) -> dict:
    """
    Post to LinkedIn with optional image.
    If image_bytes provided, uploads image first then attaches to post.
    """
    if not config.LINKEDIN_ACCESS_TOKEN:
        return {"success": False, "post_id": None, "error": "No access token."}

    try:
        person_urn = get_person_urn()
    except Exception as e:
        return {"success": False, "post_id": None, "error": str(e)}

    # Try to upload image if provided
    image_asset = None
    if image_bytes:
        print("[LinkedIn] Uploading image...")
        reg = register_image_upload(person_urn)
        if reg:
            uploaded = upload_image_bytes(reg["upload_url"], image_bytes)
            if uploaded:
                image_asset = reg["asset"]

    # Build post payload
    if image_asset:
        # Post with image
        payload = {
            "author":          person_urn,
            "lifecycleState":  "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary":    {"text": post_text},
                    "shareMediaCategory": "IMAGE",
                    "media": [{
                        "status":      "READY",
                        "media":       image_asset,
                        "title":       {"text": ""},
                    }]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
        print("[LinkedIn] Posting with image...")
    else:
        # Text only post
        payload = {
            "author":          person_urn,
            "lifecycleState":  "PUBLISHED",
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
        print("[LinkedIn] Posting text only...")

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
        f"&scope={scope.replace(' ','%20')}"
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
    return {}
