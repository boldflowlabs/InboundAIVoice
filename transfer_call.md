# SIP Call Transfer Guide

This document outlines the steps to configure, run, and use the Cold Transfer (SIP REFER) functionality in the LiveKit Voice Agent.

## 1. Prerequisites

Ensure your `.env` file contains the following Telnyx SIP credentials and LiveKit configuration:

```env
# LiveKit Configuration
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
LIVEKIT_SIP_DOMAIN=your-project.sip.livekit.cloud

# Telnyx SIP Configuration
TELNYX_API_KEY=KEYxxxxxxxxxxxx
TELNYX_OUTBOUND_NUMBER=+1XXXXXXXXXX
TELNYX_SIP_TRUNK_ID=ST_XXXXXXXXXXXX

# Optional credential connection overrides
TELNYX_SIP_USERNAME=boldflow_xxxxxx
TELNYX_SIP_PASSWORD=xxxxxxxxxxxxxxxxxxxx
```

## 2. Configuration Setup

Before running the agent for the first time, you must ensure your LiveKit SIP Trunk is correctly configured with your Telnyx credentials. We have created a script to automate this.

Run the setup script:
```powershell
python setup_trunk.py
```
*   **Success**: `✅ Setup complete! Telnyx and LiveKit are configured.`
*   **Failure**: Check error message and verify `.env` values.

This provisions the Telnyx FQDN connection and credential connection, routes the phone number to LiveKit, and sets up/syncs the LiveKit inbound and outbound SIP trunks.

## 3. Running the Agent

Start the voice agent in development mode:

```powershell
python agent.py dev
```

The agent will connect to LiveKit and wait for a job.

## 4. Initiating a Call

In a **separate terminal**, trigger an outbound call to your phone:

```powershell
python make_call.py --to +1XXXXXXXXXX
```
*Replace `+1XXXXXXXXXX` with your actual phone number.*

## 5. Performing a Transfer

Once you answer the call and are talking to the agent:

### Default Transfer
Say: **"Transfer me."** or **"Transfer me to a live agent."**
*   **Action**: Agent transfers you to the default configured number (configured via `DEFAULT_TRANSFER_NUMBER` in `.env`).
*   **Mechanism**: The agent sends a SIP REFER to `sip:<DEFAULT_TRANSFER_NUMBER>@<TELNYX_SIP_DOMAIN>`.

### Custom Transfer
Say: **"Transfer me to +1 555 000 1234."**
*   **Action**: Agent transfers you to the requested number.
*   **Mechanism**: The agent constructs `sip:+15550001234@<TELNYX_SIP_DOMAIN>` and initiates the transfer.

## 6. Troubleshooting

| Error | Cause | Solution |
| :--- | :--- | :--- |
| **Status 500 (Max Auth Retry)** | Incorrect SIP credentials on Trunk. | Run `python setup_trunk.py` again to update credentials. |
| **Status 408 (Timeout)** | Invalid SIP URI or blocked by provider. | Ensure `LIVEKIT_SIP_DOMAIN` (or `TELNYX_SIP_DOMAIN` override) is set in `.env`. Verify "Call Transfer (SIP REFER)" is enabled in your Telnyx portal dashboard. |
| **Status 400 (Invalid argument)** | Destination is not a URI. | The code now automatically adds `sip:` and `@domain`. Update code if using an old version. |
| **Disconnects but no ring** | Successful transfer, but destination failed. | The transfer *left* the agent successfully. Check the destination phone number or Telnyx logs for routing issues. |
