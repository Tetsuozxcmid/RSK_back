# Project Architecture Map

This file is the baseline architecture and navigation map for the colocated backend repository.

Primary goal:
- make backend work fast without rediscovering which service owns which contract;
- explain how this repo relates to the sibling frontend repo in the current workspace;
- record the service boundaries that are easiest to confuse during auth/profile work.

How to use this file:
- read `What Is Easy To Confuse First` before changing auth, OAuth, profile, or service contracts;
- read `Service Ownership Map` to find the right microservice first;
- read `Frontend Integration Map` before changing endpoints that are consumed by `rsk_fr`;
- use `Task Index` when you need the shortest path to the right files.

Related local workspace repos:
- sibling frontend/BFF repo: `../../rsk_fr`
- frontend architecture map: `../../rsk_fr/CLAUDE.md`
- main backend project README: `README.md`

## What Is Easy To Confuse First

This repository is not one backend app. It is a multi-service backend behind `https://api.rosdk.ru`.

Important current ambiguities and boundaries:

1. Auth and profile are different services.
- `auth_service` owns users as auth identities, sessions, OAuth providers, cookies, password flows, and JWT issuance.
- `user_profile` owns profile fields such as `NameIRL`, `Surname`, `Patronymic`, organization, and role projection.
- changing login or OAuth success does not automatically mean the profile schema is complete for MAYAK.

2. Frontend-visible URLs are shaped by Traefik prefixes.
- the external route namespace is defined in `docker-compose.yml`;
- some services keep the external prefix in the path, others strip it first;
- do not assume internal FastAPI route prefixes match the public URL 1:1 without checking Traefik labels.

3. Social login data is currently split across layers.
- provider user info is fetched in `auth_service`;
- initial profile creation happens later through RabbitMQ consumption in `user_profile`;
- the first profile row may still be incomplete for MAYAK FIO requirements.

4. The sibling frontend repo is part of the real working system.
- `../../rsk_fr` contains many Next.js API proxy routes that forward directly to this backend;
- fixing only the frontend can hide a contract problem that belongs here;
- fixing only this repo can break the frontend proxy/BFF assumptions if request or response shapes change.

5. Cookies and redirects are production-domain-oriented.
- auth cookies are set for `.rosdk.ru`;
- OAuth callbacks redirect to frontend URLs from env;
- local development often requires env overrides, not only code changes.

6. Some user lifecycle is event-driven, not only request-driven.
- `auth_service` publishes `user.created`;
- `user_profile` consumes that event to create profile rows;
- `user_profile` also publishes/consumes role updates through RabbitMQ.

7. MAYAK uses portal auth but has stricter profile requirements.
- MAYAK frontend in `../../rsk_fr` requires `Surname + NameIRL`;
- backend social-login success alone is not enough if profile projection stores only partial name data.

## Top-Level Structure

- `docker-compose.yml` main service topology and public route ownership
- `docker-compose.override.yml` local/dev-oriented compose overrides
- `auth_service/` authentication, registration, JWT, cookies, OAuth
- `user_profile/` profile storage and profile APIs
- `teams_service/` team membership and team metadata
- `orgs_service/` organization lookup and metadata
- `projects_service/` project/task flows
- `learning_service/` learning/course flows
- `admin_service/` Telegram admin bot
- `admin-panel_service/` admin-panel-related service
- `monitoring/` Prometheus and monitoring config

## Public Route Ownership Map

Traefik routing in `docker-compose.yml` maps public `api.rosdk.ru` paths to services:

- `/auth/*` -> `auth_service`
- `/users/*` -> `user_profile`
- `/teams/*` -> `teams_service`
- `/orgs/*` -> `orgs_service`
- `/projects/*` -> `projects_service`
- `/learning/*` -> `learning_service`
- `/admin_bot/*` -> `admin_service`

Important prefix nuance:
- `auth_service` strips `/auth` before FastAPI routing, so external `/auth/users_interaction/login/` maps to internal `/users_interaction/login/`.
- `learning_service` strips `/learning`, so external `/learning/api/courses/` maps to internal `/api/courses/`.
- `user_profile`, `teams_service`, `orgs_service`, and `projects_service` are exposed with their service prefix intact, so the public URL usually includes both the Traefik prefix and the FastAPI router prefix.

## Service Ownership Map

### auth_service

Owns:
- user registration and email confirmation
- login/logout and JWT cookie issuance
- OAuth via VK and Yandex
- provider identity storage (`auth_provider`, `provider_id`)
- publishing `user.created` / `user_verified` events

Start here for:
- login failures
- cookie issues
- OAuth callback bugs
- redirect URL bugs
- provider email/name extraction

Key files:
- `auth_service/app/routes/users_router/router.py`
- `auth_service/app/cruds/users_crud/crud.py`
- `auth_service/app/services/vk_oauth.py`
- `auth_service/app/services/yandex_oauth.py`
- `auth_service/app/config.py`

Important current behavior:
- OAuth users are created in auth DB via `create_oauth_user`.
- VK callback reads `first_name`, `last_name`, and `email` from VK user info.
- Yandex callback reads `default_email` plus `real_name` or `display_name`.
- auth cookie is `users_access_token`, set as HttpOnly for `.rosdk.ru`.

### user_profile

Owns:
- profile fields (`NameIRL`, `Surname`, `Patronymic`, `Region`, `Organization`, `Type`)
- get/update-my-profile APIs
- role update projection
- profile creation from RabbitMQ events

Start here for:
- missing or malformed profile fields
- MAYAK FIO readiness problems
- profile update bugs
- role sync bugs

Key files:
- `user_profile/app/routes/profile_routers/router.py`
- `user_profile/app/cruds/profile_crud.py`
- `user_profile/app/services/grabber.py`
- `user_profile/app/services/rabbitmq.py`
- `user_profile/app/main.py`

Important current behavior:
- authenticated profile endpoints read `users_access_token` from cookies.
- `consume_user_created_events` creates a profile row when auth publishes `user.created`.
- current profile bootstrap stores incoming `name` into `NameIRL` and leaves `Surname` empty.
- this is one of the main reasons a socially logged-in user can still fail MAYAK FIO completeness checks.

### teams_service

Owns:
- team creation, join/leave, membership queries
- profile/org side effects when users join teams or orgs

Key files:
- `teams_service/app/routes/teams_router/router.py`
- `teams_service/app/services/user_profile_client.py`

### orgs_service

Owns:
- organization catalogue and lookup
- organization detail/count endpoints

### projects_service

Owns:
- project and task runtime for the projects domain
- moderator review routes in the projects namespace

### learning_service

Owns:
- courses, submissions, moderator review flows in the learning namespace

## Frontend Integration Map

The sibling frontend repo `../../rsk_fr` is a Next.js app with many thin proxy/BFF endpoints. Common mappings:

- `../../rsk_fr/src/pages/api/auth/login.js` -> `auth_service` login
- `../../rsk_fr/src/pages/api/auth/reg.js` -> `auth_service` register
- `../../rsk_fr/src/pages/api/auth/oauth/callback.js` and `.../vk/callback.js` -> auth/OAuth flows
- `../../rsk_fr/src/pages/api/profile/info.js` -> `user_profile` get-my-profile
- `../../rsk_fr/src/pages/api/profile/update.js` -> `user_profile` update-my-profile and my-role
- `../../rsk_fr/src/pages/api/org/*` -> `orgs_service`
- `../../rsk_fr/src/pages/api/teams/*` -> `teams_service`
- `../../rsk_fr/src/pages/api/projects/*` -> `projects_service`
- `../../rsk_fr/src/pages/api/cours/*` -> `learning_service`

Working rule:
- when changing a backend contract used by the frontend, inspect the matching proxy route in `../../rsk_fr/src/pages/api/*` and any page/component code that depends on its current payload shape.
- frontend OAuth wiring is currently mixed: there is a generic callback path in the frontend repo, but the backend repo's concrete provider callbacks live in `auth_service/app/services/yandex_oauth.py` and `auth_service/app/services/vk_oauth.py`.

## Auth And Profile Flow Map

### Email/password registration

High-level flow:
1. Frontend proxy in `../../rsk_fr/src/pages/api/auth/reg.js` calls `auth_service`.
2. `auth_service` creates a provisional user and publishes `user.created`.
3. `user_profile` consumes that event and creates the initial profile row.
4. Email confirmation later finalizes auth data in `auth_service`.

Important consequence:
- profile creation is decoupled from final email verification.

### Social login (VK/Yandex)

High-level flow:
1. Frontend starts OAuth, but provider callback handling lives in `auth_service`.
2. `auth_service` exchanges the provider code for an access token.
3. `auth_service` fetches provider user info and creates/fetches the auth user.
4. `auth_service` publishes `user.created`.
5. `user_profile` consumes the event and creates the profile projection.
6. Frontend later reads profile data from `user_profile`.

Important current consequence:
- provider name/email extraction already happens in `auth_service`;
- profile completeness still depends on how `user_profile` projects the event payload into `NameIRL` and `Surname`.

### Why MAYAK can still require manual FIO

Current cross-repo interpretation:
- MAYAK frontend in `../../rsk_fr` requires `NameIRL + Surname`.
- `auth_service` may know a full provider name.
- `user_profile` bootstrap currently writes the incoming `name` to `NameIRL` and leaves `Surname` empty.
- therefore a user can be authorized successfully and still be blocked by MAYAK's FIO completeness gate.

If the task is "auto-fill FIO after OAuth", the likely change surface is:
- `auth_service/app/services/vk_oauth.py`
- `auth_service/app/services/yandex_oauth.py`
- `user_profile/app/services/rabbitmq.py`
- potentially `user_profile` schemas/CRUD if profile bootstrap needs a richer name shape
- plus frontend validation or UX only if the user-visible flow changes

## Local Environment Notes

- public-domain assumptions live in env/config, especially in `auth_service/app/config.py`
- OAuth callbacks rely on `VK_REDIRECT_URI`, `YANDEX_REDIRECT_URI`, `YANDEX_FRONTEND_URL`, and `FRONTEND_URL`
- auth/profile local testing often fails because cookies are scoped to `.rosdk.ru`, not because the route logic is wrong
- when debugging local auth, verify env, redirect URIs, cookie domain, and frontend proxy target together

## Working Rules

- Do not treat `auth_service` user fields as the canonical profile model.
- Do not fix backend data-shape problems only in the frontend unless the task explicitly asks for a frontend-only workaround.
- If the issue involves auth success but wrong/missing profile data, inspect both `auth_service` and `user_profile`.
- If the issue involves role drift, inspect RabbitMQ publication/consumption, not only the PATCH endpoint.
- If changing OAuth behavior, verify cookie/redirect behavior and the sibling frontend callback pages together.
- If changing public endpoints, preserve existing path prefixes unless the task explicitly changes infrastructure routing.

## Task Index

When a task says:

`change login or password flow`
- start with `auth_service/app/routes/users_router/router.py`
- then `auth_service/app/cruds/users_crud/crud.py`

`change VK or Yandex OAuth`
- start with `auth_service/app/services/vk_oauth.py`
- `auth_service/app/services/yandex_oauth.py`
- then inspect frontend usage in `../../rsk_fr/src/pages/callback_auth.js`, `../../rsk_fr/src/pages/vk-callback.js`, and `../../rsk_fr/src/pages/api/auth/*`

`change profile fields or FIO behavior`
- start with `user_profile/app/routes/profile_routers/router.py`
- `user_profile/app/cruds/profile_crud.py`
- `user_profile/app/services/rabbitmq.py`
- then inspect frontend profile/MAYAK consumers in `../../rsk_fr/src/pages/api/profile/*` and `../../rsk_fr/src/components/features/tools-2/settings.js`

`change role behavior`
- start with `user_profile/app/routes/profile_routers/router.py`
- `user_profile/app/services/rabbitmq.py`
- then inspect auth-role or frontend admin consumers

`change teams/orgs/projects/learning contract`
- start with the owning service here
- then inspect the matching proxy under `../../rsk_fr/src/pages/api/`

## Update Rule

Update this file whenever a task meaningfully changes:
- service ownership boundaries;
- public route prefixes or routing assumptions;
- auth/profile/OAuth flow contracts;
- RabbitMQ event contracts that affect profile or role projection;
- the sibling frontend integration assumptions above.
