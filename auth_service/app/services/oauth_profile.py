from __future__ import annotations


def clean_text(value: str | None) -> str:
    return str(value or "").strip()


def build_full_name(
    first_name: str = "",
    last_name: str = "",
    patronymic: str = "",
) -> str:
    return " ".join(
        part
        for part in [clean_text(first_name), clean_text(last_name), clean_text(patronymic)]
        if part
    ).strip()


def split_full_name(full_name: str | None) -> tuple[str, str, str]:
    parts = [part for part in clean_text(full_name).split() if part]
    if len(parts) < 2:
        return "", "", ""

    first_name = parts[0]
    last_name = parts[1]
    patronymic = " ".join(parts[2:]).strip() if len(parts) > 2 else ""
    return first_name, last_name, patronymic


def normalize_yandex_profile(user_data: dict | None) -> dict[str, str]:
    raw_user_data = user_data or {}

    first_name = clean_text(raw_user_data.get("first_name"))
    last_name = clean_text(raw_user_data.get("last_name"))
    patronymic = ""
    full_name = clean_text(raw_user_data.get("real_name"))
    display_name = clean_text(raw_user_data.get("display_name"))

    if full_name:
        parsed_first_name, parsed_last_name, parsed_patronymic = split_full_name(full_name)
        if not first_name:
            first_name = parsed_first_name
        if not last_name:
            last_name = parsed_last_name
        if not patronymic:
            patronymic = parsed_patronymic

    full_name = full_name or build_full_name(first_name, last_name, patronymic) or display_name

    emails = raw_user_data.get("emails") or []
    email = clean_text(raw_user_data.get("default_email"))
    if not email and emails:
        email = clean_text(emails[0])

    return {
        "email": email,
        "username": clean_text(raw_user_data.get("login")),
        "first_name": first_name,
        "last_name": last_name,
        "patronymic": patronymic,
        "full_name": full_name,
    }


def normalize_vk_profile(user_data: dict | None) -> dict[str, str]:
    raw_user_data = user_data or {}

    first_name = clean_text(raw_user_data.get("first_name"))
    last_name = clean_text(raw_user_data.get("last_name"))
    patronymic = clean_text(
        raw_user_data.get("middle_name") or raw_user_data.get("patronymic")
    )
    full_name = build_full_name(first_name, last_name, patronymic)

    return {
        "email": clean_text(raw_user_data.get("email")),
        "username": clean_text(raw_user_data.get("screen_name")),
        "first_name": first_name,
        "last_name": last_name,
        "patronymic": patronymic,
        "full_name": full_name,
    }


def build_user_registered_event(
    *,
    user_id: int,
    email: str = "",
    username: str = "",
    first_name: str = "",
    last_name: str = "",
    patronymic: str = "",
    full_name: str = "",
    role: str = "student",
    auth_provider: str = "",
) -> dict[str, str | int | bool]:
    normalized_full_name = clean_text(full_name) or build_full_name(
        first_name, last_name, patronymic
    )

    return {
        "user_id": user_id,
        "email": clean_text(email),
        "username": clean_text(username),
        "name": normalized_full_name,
        "full_name": normalized_full_name,
        "first_name": clean_text(first_name),
        "last_name": clean_text(last_name),
        "patronymic": clean_text(patronymic),
        "verified": True,
        "event_type": "user_registered",
        "role": clean_text(role) or "student",
        "auth_provider": clean_text(auth_provider),
    }
