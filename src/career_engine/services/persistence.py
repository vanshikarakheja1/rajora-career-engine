import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from career_engine.api.schemas import CareerRecommendation, StudentProfileRequest


logger = logging.getLogger(__name__)


def supabase_rest_request(
    supabase_url: str,
    anon_key: str,
    access_token: str,
    path: str,
    payload: dict[str, object],
    prefer: str = "return=minimal",
) -> None:
    if not supabase_url.startswith("https://"):
        raise ValueError("Supabase REST URL must use HTTPS.")

    request = Request(
        f"{supabase_url}/rest/v1/{path}",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "apikey": anon_key,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": prefer,
        },
    )
    with urlopen(request, timeout=8) as response:  # nosec B310
        response.read()


def save_profile_and_recommendations(
    supabase_url: str,
    anon_key: str,
    user: dict[str, object],
    profile: StudentProfileRequest,
    recommendations: list[CareerRecommendation],
) -> bool:
    access_token = str(user.get("_access_token") or "")
    user_id = str(user.get("id") or "")
    if not supabase_url or not anon_key or not access_token or not user_id:
        logger.warning("Supabase persistence skipped because configuration or user context is incomplete.")
        return False

    profile_payload = profile.model_dump(mode="json")
    recommendations_payload = [item.model_dump(mode="json") for item in recommendations]
    email = str(user.get("email") or "")

    try:
        supabase_rest_request(
            supabase_url=supabase_url,
            anon_key=anon_key,
            access_token=access_token,
            path="user_profiles?on_conflict=user_id",
            payload={
                "user_id": user_id,
                "email": email,
                "profile": profile_payload,
            },
            prefer="resolution=merge-duplicates,return=minimal",
        )
        supabase_rest_request(
            supabase_url=supabase_url,
            anon_key=anon_key,
            access_token=access_token,
            path="recommendation_history",
            payload={
                "user_id": user_id,
                "profile": profile_payload,
                "recommendations": recommendations_payload,
            },
        )
        return True
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        logger.warning("Supabase persistence failed: %s", exc)
        return False
