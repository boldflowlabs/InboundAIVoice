import asyncio
import os
import json
import httpx
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(".env")

# Market mapping configs
MARKET_CONFIGS = {
    "US": {"anchorsite": "Ashburn, VA", "env_suffix": "US"},
    "UK": {"anchorsite": "London, UK", "env_suffix": "UK"},
    "CA": {"anchorsite": "Toronto, Canada", "env_suffix": "CA"},
    "AU": {"anchorsite": "Sydney, Australia", "env_suffix": "AU"},
    "AE": {"anchorsite": "Dubai, UAE", "env_suffix": "AE"},
}

def clean_e164(phone: str) -> str:
    """Format the phone number to strict E.164 format."""
    if not phone:
        return ""
    # Strip non-digit characters except +
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned

async def setup_telnyx_connection(api_key: str, anchorsite: str, sip_domain: str, phone_number: str) -> str:
    """Provision FQDN Connection and associate FQDN & Phone Number using Telnyx API v2."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Check if FQDN connection already exists
        conn_id = None
        print("Checking Telnyx FQDN connections...")
        resp = await client.get("https://api.telnyx.com/v2/fqdn_connections", headers=headers)
        if resp.status_code == 200:
            conns = resp.json().get("data", [])
            for c in conns:
                if c.get("connection_name") == "BoldFlow Labs SIP Connection":
                    conn_id = c.get("id")
                    print(f"Found existing Telnyx FQDN connection: {conn_id}")
                    break
        
        # 2. Create FQDN connection if it doesn't exist
        if not conn_id:
            print("Creating new Telnyx FQDN connection...")
            payload = {
                "active": True,
                "connection_name": "BoldFlow Labs SIP Connection",
                "anchorsite_override": anchorsite,
                "inbound": {
                    "ani_number_format": "+E.164",
                    "dnis_number_format": "+e164"
                }
            }
            resp = await client.post("https://api.telnyx.com/v2/fqdn_connections", headers=headers, json=payload)
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"Failed to create Telnyx connection: {resp.text}")
            conn_id = resp.json().get("data", {}).get("id")
            print(f"Created Telnyx FQDN connection: {conn_id}")

        # 3. Add or verify FQDN record for LiveKit SIP Domain
        print(f"Verifying FQDN record for {sip_domain}...")
        fqdn_resp = await client.get("https://api.telnyx.com/v2/fqdns", headers=headers)
        fqdn_exists = False
        if fqdn_resp.status_code == 200:
            fqdns = fqdn_resp.json().get("data", [])
            for f in fqdns:
                if f.get("fqdn") == sip_domain and f.get("connection_id") == conn_id:
                    fqdn_exists = True
                    print(f"FQDN record for {sip_domain} already exists.")
                    break
        
        if not fqdn_exists:
            print(f"Creating FQDN record pointing to {sip_domain}...")
            fqdn_payload = {
                "connection_id": conn_id,
                "fqdn": sip_domain,
                "port": 5060,
                "dns_record_type": "a"
            }
            resp = await client.post("https://api.telnyx.com/v2/fqdns", headers=headers, json=fqdn_payload)
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"Failed to create Telnyx FQDN record: {resp.text}")
            print("FQDN record created successfully.")

        # 4. Find phone number ID
        print(f"Looking up Telnyx ID for number {phone_number}...")
        num_resp = await client.get(f"https://api.telnyx.com/v2/phone_numbers?filter[phone_number][eq]={phone_number}", headers=headers)
        if num_resp.status_code != 200:
            raise RuntimeError(f"Failed to search for Telnyx number: {num_resp.text}")
        nums_data = num_resp.json().get("data", [])
        if not nums_data:
            print(f"Warning: Phone number {phone_number} not found in your Telnyx account. Please purchase it or configure it manually.")
            return conn_id
        
        num_id = nums_data[0].get("id")
        
        # 5. Associate phone number with connection
        print(f"Associating number {phone_number} with connection {conn_id}...")
        voice_payload = {
            "connection_id": conn_id
        }
        resp = await client.patch(f"https://api.telnyx.com/v2/phone_numbers/{num_id}/voice", headers=headers, json=voice_payload)
        if resp.status_code not in (200, 204):
            raise RuntimeError(f"Failed to associate phone number with connection: {resp.text}")
        print("Associated phone number successfully.")
        return conn_id

async def setup_telnyx_credential_connection(api_key: str) -> tuple[str, str]:
    """Retrieve or create Telnyx Credential Connection and return (username, password)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Allow environment overrides
    env_user = os.getenv("TELNYX_SIP_USERNAME")
    env_pass = os.getenv("TELNYX_SIP_PASSWORD")
    if env_user and env_pass:
        print("Using Telnyx SIP credentials from environment variables.")
        return env_user, env_pass

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Check if Credential Connection already exists
        print("Checking Telnyx Credential connections...")
        resp = await client.get("https://api.telnyx.com/v2/credential_connections", headers=headers)
        if resp.status_code == 200:
            conns = resp.json().get("data", [])
            for c in conns:
                if c.get("connection_name") == "BoldFlow Labs Credential Connection":
                    conn_id = c.get("id")
                    user_name = c.get("user_name")
                    password = c.get("password")
                    
                    if not password:
                        # Fetch individual connection details to get password
                        print(f"Retrieving details for connection: {conn_id}")
                        detail_resp = await client.get(f"https://api.telnyx.com/v2/credential_connections/{conn_id}", headers=headers)
                        if detail_resp.status_code == 200:
                            detail_data = detail_resp.json().get("data", {})
                            user_name = detail_data.get("user_name")
                            password = detail_data.get("password")
                    
                    if user_name and password:
                        print(f"Found existing Telnyx Credential connection: {conn_id} (user: {user_name})")
                        return user_name, password

        # Create Credential Connection if it doesn't exist
        print("Creating new Telnyx Credential connection...")
        import secrets
        import string
        def generate_random_string(length=16):
            chars = string.ascii_letters + string.digits
            return "".join(secrets.choice(chars) for _ in range(length))

        username = f"boldflow_{generate_random_string(8)}"
        password = generate_random_string(20)

        payload = {
            "active": True,
            "connection_name": "BoldFlow Labs Credential Connection",
            "user_name": username,
            "password": password
        }
        resp = await client.post("https://api.telnyx.com/v2/credential_connections", headers=headers, json=payload)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Failed to create Telnyx Credential connection: {resp.text}")

        data = resp.json().get("data", {})
        ret_user = data.get("user_name") or username
        ret_pass = data.get("password") or password
        print(f"Created Telnyx Credential connection (user: {ret_user})")
        return ret_user, ret_pass

async def main():
    # 1. Read configuration/environment
    market = os.getenv("DEPLOYMENT_MARKET", "US").upper()
    if market not in MARKET_CONFIGS:
        print(f"Invalid DEPLOYMENT_MARKET '{market}'. Defaulting to 'US'.")
        market = "US"
    
    config = MARKET_CONFIGS[market]
    env_suffix = config["env_suffix"]
    
    # Check for suffix-specific or fallback number
    phone_number_raw = os.getenv(f"TELNYX_NUMBER_{env_suffix}") or os.getenv("TELNYX_OUTBOUND_NUMBER")
    phone_number = clean_e164(phone_number_raw)
    
    telnyx_api_key = os.getenv("TELNYX_API_KEY")
    livekit_sip_domain = os.getenv("LIVEKIT_SIP_DOMAIN")
    
    print("═══ BoldFlow Labs SIP Trunk Setup ═══")
    print(f"Market: {market}")
    print(f"AnchorSite Region: {config['anchorsite']}")
    print(f"Phone Number: {phone_number}")
    print(f"LiveKit SIP Domain: {livekit_sip_domain}")
    print("─────────────────────────────────────")

    if not telnyx_api_key:
        print("Error: TELNYX_API_KEY not found in .env")
        return
    if not phone_number:
        print("Error: Phone number not found in .env (check TELNYX_NUMBER_US/UK/etc or TELNYX_OUTBOUND_NUMBER)")
        return
    if not livekit_sip_domain:
        print("Error: LIVEKIT_SIP_DOMAIN not found in .env")
        return

    # 2. Provision FQDN connection and number association on Telnyx
    try:
        connection_id = await setup_telnyx_connection(
            api_key=telnyx_api_key,
            anchorsite=config["anchorsite"],
            sip_domain=livekit_sip_domain,
            phone_number=phone_number
        )
    except Exception as e:
        print(f"❌ Telnyx Provisioning failed: {e}")
        return

    # Provision/retrieve Credential Connection for Outbound Calls
    try:
        username, password = await setup_telnyx_credential_connection(api_key=telnyx_api_key)
    except Exception as e:
        print(f"❌ Telnyx Credential Connection setup failed: {e}")
        return

    # 3. Setup LiveKit Inbound SIP Trunk & Dispatch Rule
    print("\nConnecting to LiveKit API...")
    lkapi = api.LiveKitAPI()
    sip = lkapi.sip

    try:
        # Check if Inbound Trunk already exists
        print("Checking LiveKit Inbound Trunks...")
        trunks = await sip.list_sip_inbound_trunk(api.ListSIPInboundTrunkRequest())
        existing_trunk_id = None
        for t in trunks.items:
            if phone_number in t.numbers:
                existing_trunk_id = t.sip_trunk_id
                print(f"Found existing LiveKit Inbound Trunk: {existing_trunk_id}")
                break
        
        if not existing_trunk_id:
            print("Creating LiveKit Inbound SIP Trunk...")
            trunk_info = api.SIPInboundTrunkInfo(
                name=f"Telnyx Inbound - {market}",
                numbers=[phone_number]
            )
            req = api.CreateSIPInboundTrunkRequest(trunk=trunk_info)
            trunk = await sip.create_inbound_trunk(req)
            existing_trunk_id = trunk.sip_trunk_id
            print(f"Created Inbound Trunk: {existing_trunk_id}")
        
        # Check if Dispatch Rule already exists
        print("Checking LiveKit Dispatch Rules...")
        rules = await sip.list_sip_dispatch_rule(api.ListSIPDispatchRuleRequest())
        existing_rule_id = None
        for r in rules.items:
            if r.name == f"Telnyx Route - {market}":
                existing_rule_id = r.sip_dispatch_rule_id
                print(f"Found existing LiveKit Dispatch Rule: {existing_rule_id}")
                break
        
        if not existing_rule_id:
            print("Creating LiveKit SIP Dispatch Rule...")
            rule = api.SIPDispatchRule(
                dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                    room_prefix="call-"
                )
            )
            room_config = api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(agent_name="inbound-caller")]
            )
            req = api.CreateSIPDispatchRuleRequest(
                name=f"Telnyx Route - {market}",
                rule=rule,
                room_config=room_config,
            )
            disp_rule = await sip.create_sip_dispatch_rule(req)
            print(f"Created Dispatch Rule: {disp_rule.sip_dispatch_rule_id}")

        # 4. Create/Update Outbound Trunk in LiveKit
        outbound_trunk_id = os.getenv("TELNYX_SIP_TRUNK_ID")
        if outbound_trunk_id:
            print(f"\nUpdating Outbound SIP Trunk in LiveKit ({outbound_trunk_id})...")
            await sip.update_outbound_trunk_fields(
                outbound_trunk_id,
                address="sip.telnyx.com",
                auth_username=username,
                auth_password=password,
                numbers=[phone_number],
            )
            print("✅ Outbound SIP Trunk updated.")
        else:
            print("\nCreating Outbound SIP Trunk in LiveKit...")
            outbound_config = api.SIPOutboundTrunkInfo(
                name=f"Telnyx Outbound - {market}",
                address="sip.telnyx.com",
                numbers=[phone_number],
                auth_username=username,
                auth_password=password,
            )
            outbound_req = api.CreateSIPOutboundTrunkRequest(trunk=outbound_config)
            out_trunk = await sip.create_sip_outbound_trunk(outbound_req)
            print(f"Created Outbound SIP Trunk ID: {out_trunk.sip_trunk_id}")
            print(f"IMPORTANT: Please add 'TELNYX_SIP_TRUNK_ID={out_trunk.sip_trunk_id}' to your .env file.")
            print(f"IMPORTANT: Please add 'TELNYX_SIP_USERNAME={username}' and 'TELNYX_SIP_PASSWORD={password}' to your .env file.")

        print("\n✅ Setup complete! Telnyx and LiveKit are configured.")

    except Exception as e:
        print(f"❌ LiveKit SIP configuration failed: {e}")
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(main())
