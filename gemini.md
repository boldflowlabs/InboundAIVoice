# 🎙️ BoldFlow AI Voice Agent (Inbound) — Gemini Live Implementation Guide
### Stack: Google Gemini Live API · LiveKit · Telnyx Telephony

---

## Overview

| Layer | Service | Purpose |
|---|---|---|
| STT / LLM / TTS | Google Gemini Live | Unified real-time multimodal audio session (`beta.realtime.RealtimeModel`) |
| Transport | LiveKit | WebRTC real-time audio |
| Telephony | Telnyx FQDN Connection | Inbound + Outbound SIP routing |

---

## Part 1: Prerequisites & API Keys

Before deploying, ensure you have the following credentials.

### 1.1 Google Gemini API
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API Key → `AIzaSyxxxxxxxxxxxx`
3. Make sure the key has access to Gemini 2.0 / 2.5 Flash models.

### 1.2 Telnyx
1. Create an account at [Telnyx](https://telnyx.com/)
2. Copy your API V2 Key.
3. Purchase a DID number.

### 1.3 LiveKit Cloud
1. Go to [LiveKit Cloud](https://cloud.livekit.io/)
2. Create a project and obtain `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET`.
3. Obtain your SIP URI/Domain from the SIP settings.

---

## Part 2: Project Setup & Execution

### 2.1 Configuration
Update your `.env` or `config.json` with the following variables:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LIVEKIT_SIP_DOMAIN=your-project.sip.livekit.cloud
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxx
TELNYX_API_KEY=KEYxxxxxxxxxxxx
TELNYX_OUTBOUND_NUMBER=+1XXXXXXXXXX
DEPLOYMENT_MARKET=US
```

### 2.2 Provisioning Telephony
Run the provisioning script to configure the Telnyx FQDN Connection and LiveKit SIP Trunk:
```bash
python setup_trunk.py
```
This automatically registers the FQDN connection pointing to LiveKit, associates your phone number, and configures the LiveKit inbound and outbound SIP trunks.

### 2.3 Run the Voice Agent
Start the agent worker:
```bash
python agent.py dev
```

### 2.4 Run the Dashboard
Start the local dashboard UI:
```bash
python ui_server.py
```
Open `http://localhost:8000` to view call logs, calendar bookings, CRM contacts, and config options.
