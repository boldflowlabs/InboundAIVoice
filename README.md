# BoldFlow Labs — AI Voice Agent (Inbound)

This repository hosts the **BoldFlow Labs Inbound AI Voice Agent**, a production-ready white-labeled voice agent solution for handling inbound telephony using **Google Gemini Live API** (via `livekit-plugins-google`) and **Telnyx SIP FQDN trunking**.

The system features real-time conversational reasoning, automated appointment booking (Cal.com / Google Calendar), post-call notifications, CRM contacts list, and a modern dashboard UI to manage settings, view logs, and monitor analytics.

---

## 📂 Project Structure

### Core Components
| File | Description |
|------|-------------|
| [agent.py](file:///d:/projects/InboundAIVoice/agent.py) | Main AI worker. Connects to LiveKit rooms and routes real-time audio through Google Gemini Live API. |
| [ui_server.py](file:///d:/projects/InboundAIVoice/ui_server.py) | FastAPI server hosting the BoldFlow Labs dashboard. |
| [setup_trunk.py](file:///d:/projects/InboundAIVoice/setup_trunk.py) | Provisioning script to configure Telnyx FQDN connections and LiveKit SIP trunks. |
| [make_call.py](file:///d:/projects/InboundAIVoice/make_call.py) | Outbound dialing script using LiveKit agent dispatches. |

---

## 🚀 Getting Started

### 1. Installation

1. Install Python 3.9+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 2. Configuration

Copy `.env.example` to `.env` and fill in:
* `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_SIP_DOMAIN`
* `GOOGLE_API_KEY`
* `TELNYX_API_KEY`, `TELNYX_OUTBOUND_NUMBER`, `DEPLOYMENT_MARKET`

### 3. Setup Trunking

Run the provisioning script to configure Telnyx and LiveKit routing:
```bash
python setup_trunk.py
```

### 4. Running the Dashboard & Agent

Start the dashboard:
```bash
uvicorn ui_server:app --port 8000
```
Start the agent worker:
```bash
python agent.py dev
```

---

## 🧪 Manual Verification Checklist

Follow these steps to manually verify the setup:

1. **Verify Dashboard Access**: Visit `http://localhost:8000`. Ensure that the logo, page titles, footer, and branding reflect "BoldFlow Labs".
2. **Verify Telephony Setup**: Run `python setup_trunk.py`. Check your Telnyx dashboard to confirm that the FQDN connection "BoldFlow Labs SIP Connection" is active and mapped correctly to the LiveKit SIP domain.
3. **Verify Gemini Live Session**: Place a test call to your Telnyx number. Ensure the agent starts immediately, replies using the selected Gemini voice (e.g. Aoede), and responds correctly to appointment scheduling questions using the live calendar tools.
4. **Verify Call Logs & Transcripts**: After hanging up, check the "Call Logs" page in the dashboard. Verify that the call summary, duration, sentiment, and download links are working and populated in the Supabase database.