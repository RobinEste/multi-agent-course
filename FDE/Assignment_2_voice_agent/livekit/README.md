# Optional LiveKit Room Demo

This folder adds a lightweight LiveKit step to the assignment. It is optional. The core hotel voice agent runs without LiveKit.

The goal is to show how a real-time media platform represents a call-like session:

```text
room = session
participant = caller or agent
track = audio stream
```

This is not a full SIP setup. SIP requires additional telephony configuration such as a LiveKit SIP trunk and dispatch rule.

## Install

```bash
cd FDE/Assignment_2_voice_agent/livekit
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

Set these environment variables:

```env
LIVEKIT_URL=https://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_ROOM=aurora-demo-room
```

## Create A Room

```bash
python create_room.py
```

## Create Join Tokens

Caller token:

```bash
python create_token.py --identity caller-demo --name "Caller Demo"
```

Agent token:

```bash
python create_token.py --identity aurora-agent --name "Aurora Agent"
```

The caller token represents a user or phone caller. The agent token represents the voice agent joining the same room.

## How This Maps To SIP

| SIP Demo | LiveKit Room Demo |
|----------|-------------------|
| SIP INVITE creates a call | Room is created or joined |
| Caller sends RTP audio | Caller participant publishes an audio track |
| Agent replies with RTP audio | Agent participant publishes an audio track |
| REFER transfers the call | App or SIP layer routes participant to another destination |
| BYE ends the call | Participant leaves or room closes |

## Production Extension

To turn this into a real SIP demo, add:

- LiveKit SIP trunk
- Dispatch rule that sends inbound calls to a room
- Agent worker that joins the room
- Audio bridge between LiveKit tracks and the hotel agent pipeline
- Transfer handling for front-desk escalation
