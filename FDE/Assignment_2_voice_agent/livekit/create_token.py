"""Create a LiveKit room join token for a caller or agent participant.

Required environment variables:
    LIVEKIT_API_KEY
    LIVEKIT_API_SECRET

Optional:
    LIVEKIT_ROOM

Example:
    python create_token.py --identity caller-demo --name "Caller Demo"
    python create_token.py --identity aurora-agent --name "Aurora Agent"
"""

from __future__ import annotations

import argparse
import os

from livekit import api


def _require_env(names: list[str]) -> None:
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing required environment variable(s): {joined}")


def main() -> None:
    _require_env(["LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"])
    parser = argparse.ArgumentParser(description="Create a LiveKit room join token")
    parser.add_argument("--identity", required=True, help="Unique participant identity")
    parser.add_argument("--name", default=None, help="Human-readable participant name")
    parser.add_argument("--room", default=os.getenv("LIVEKIT_ROOM", "aurora-demo-room"))
    args = parser.parse_args()

    token = (
        api.AccessToken(os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])
        .with_identity(args.identity)
        .with_name(args.name or args.identity)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=args.room,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )

    print(token)


if __name__ == "__main__":
    main()
