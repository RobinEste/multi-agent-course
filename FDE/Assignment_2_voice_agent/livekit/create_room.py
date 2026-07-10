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

from livekit import api


def _room_name() -> str:
    return os.getenv("LIVEKIT_ROOM", "aurora-demo-room")


async def main() -> None:
    room_name = _room_name()
    async with api.LiveKitAPI() as lkapi:
        room = await lkapi.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=10 * 60,
                max_participants=10,
            )
        )
    print(f"created room: {room.name}")


if __name__ == "__main__":
    asyncio.run(main())
