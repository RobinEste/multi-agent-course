"""Create a LiveKit room for the optional room/session demo.

Required environment variables:
    LIVEKIT_URL
    LIVEKIT_API_KEY
    LIVEKIT_API_SECRET

Optional:
    LIVEKIT_ROOM
"""

from __future__ import annotations

import asyncio
import os
import sys

from livekit import api


def _require_env(names: list[str]) -> None:
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing required environment variable(s): {joined}")


def _room_name() -> str:
    return os.getenv("LIVEKIT_ROOM", "aurora-demo-room")


async def main() -> None:
    _require_env(["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"])
    room_name = _room_name()
    try:
        async with api.LiveKitAPI() as lkapi:
            room = await lkapi.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=10 * 60,
                    max_participants=10,
                )
            )
    except Exception as exc:
        print(f"failed to create room {room_name!r}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"created room: {room.name}")


if __name__ == "__main__":
    asyncio.run(main())
