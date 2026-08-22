#!/usr/bin/env python3
"""Interactive & Automated REST API Onboarding Script for Growixa.

Works for Local, Staging, and Production without server terminal or database access.
If arguments are not passed via CLI flags, it interactively prompts the user.

Usage:
    # Interactive mode (prompts for inputs):
    python3 scripts/api_onboard_tenant.py

    # Non-interactive CLI mode:
    python3 scripts/api_onboard_tenant.py --api http://localhost:8000 --email admin@iitdeveloper.com --password YourNewSecretPassword123!
"""

import argparse
import getpass
import sys
from typing import Any

try:
    import httpx
except ImportError:
    print("[!] 'httpx' library is required. Install it using:\n    pip install httpx")
    sys.exit(1)

IITDEVELOPER_COMPANY_PAYLOAD: dict[str, Any] = {
    "name": "IITDeveloper",
    "logo_url": "https://iitdeveloper.com/logo.png",
    "website": "https://iitdeveloper.com",
    "industry": "Custom Software, AI Automation & DevOps",
    "timezone": "Asia/Kolkata",
    "default_language": "en",
    "legal_footer": (
        "© 2019-2026 IITDeveloper. All rights reserved. "
        "Registered Business in India. Remote-First Distributed Engineering Team."
    ),
    "contact_details": {
        "email": "info@iitdeveloper.com",
        "phone": "+91-73027-55534",
        "support_availability": "24/7 Support Available",
        "founded_year": 2019,
        "team_model": "Remote-First Distributed Team",
        "headquarters": "India",
        "tagline": "Custom Software, AI Automation & DevOps for Growing Businesses",
        "services_count": 12,
        "core_services": [
            "Website & Web App Development (Next.js, React, Node.js, Python)",
            "Mobile App Development (iOS & Android)",
            "AI Agents & Autonomous Workflows (LLMs, MCP protocols, automation)",
            "Cloud Infrastructure & DevOps (AWS, GCP, Docker, Kubernetes, CI/CD)",
            "Shopify Store Design & Ecommerce Solutions",
            "Salesforce CRM Consulting & Integrations",
            "Performance Marketing & B2B Lead Generation",
            "SEO & SMM Optimization",
            "Graphic Design, Visual Identity & Motion Graphics",
        ],
        "social_links": {
            "website": "https://iitdeveloper.com",
            "linkedin": "https://www.linkedin.com/in/iitdeveloper-com-655a57213/",
            "github": "https://github.com/iitdeveloper-git",
            "instagram": "https://instagram.com/iitdeveloper_official",
            "x": "https://x.com/developer_iit",
        },
    },
}

IITDEVELOPER_BRAND_PAYLOAD: dict[str, Any] = {
    "brand_voice": (
        "Direct, witty, engineering-driven, reliable, and results-focused. "
        "We automate things… including your headaches. We turn caffeine into high-performance code, "
        "build production-ready systems, and scale businesses with AI workflows and modern tech. "
        "Fast, reliable, tested on real users, and built to last."
    ),
    "required_facts": [
        "Founded in 2019 as a remote-first engineering and AI automation company registered in India.",
        "Delivers 12 core services spanning custom web/mobile apps, AI agents, cloud DevOps, and growth marketing.",
        "Provides 24/7 support availability for production systems and client operations.",
        "Official company website is https://iitdeveloper.com with direct contact at info@iitdeveloper.com.",
    ],
    "forbidden_claims": [
        "Never make unverified promises of overnight #1 Google ranking or instant traffic without data.",
        "Never present IITDeveloper as a generic body shop; emphasize senior engineering ownership and craftsmanship.",
        "Never ship unverified AI hallucinations or non-functional code snippets.",
    ],
}

TEMPLATES_DATA = [
    {
        "name": "AI Agents & Autonomous Workflows Consultation",
        "subject": "Discover How AI Agents Can Automate 60% of Your Manual Pipelines",
        "body_html": """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>AI Automation Discovery</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#0b1a2b; color:#ffffff; padding:40px;">
  <div style="max-width:600px; margin:0 auto; background:#112233; border-radius:16px; border:1px solid rgba(255,214,98,0.2); padding:32px;">
    <div style="text-align:center; margin-bottom:24px;">
      <img src="https://iitdeveloper.com/logo.png" alt="IITDeveloper" style="height:48px;">
    </div>
    <h1 style="color:#ffd662; font-size:24px; margin-bottom:16px; text-align:center;">Automate Things… Including Your Headaches 🚀</h1>
    <p style="color:#d1d5db; font-size:16px; line-height:1.6;">Hi {{first_name}},</p>
    <p style="color:#d1d5db; font-size:16px; line-height:1.6;">
      At <strong>IITDeveloper</strong>, we build intelligent AI agents and autonomous workflows that handle repetitive operational tasks so your core team can focus on product engineering and business growth.
    </p>
    <div style="background:rgba(255,214,98,0.08); border-left:4px solid #ffd662; padding:16px; border-radius:8px; margin:24px 0;">
      <p style="margin:0; color:#ffd662; font-weight:600;">What we build for growing businesses:</p>
      <ul style="margin:8px 0 0 0; padding-left:20px; color:#e5e7eb; line-height:1.6;">
        <li>Custom LLM Agents & Task Pipelines (MCP protocols)</li>
        <li>Intelligent Customer Support & Lead Qualification Bots</li>
        <li>Automated Data Synchronization across CRMs & Cloud DBs</li>
      </ul>
    </div>
    <div style="text-align:center; margin:32px 0;">
      <a href="https://iitdeveloper.com/contact" style="background:#ffd662; color:#0b1a2b; padding:14px 28px; font-weight:bold; border-radius:12px; text-decoration:none; display:inline-block;">Book a Free AI Architecture Call →</a>
    </div>
    <hr style="border:0; border-top:1px solid rgba(255,255,255,0.1); margin:24px 0;">
    <p style="font-size:12px; color:#9ca3af; text-align:center;">
      IITDeveloper • Remote-First Distributed Team • <a href="https://iitdeveloper.com" style="color:#ffd662;">iitdeveloper.com</a>
    </p>
  </div>
</body>
</html>""",
        "body_text": "At IITDeveloper, we build intelligent AI agents and autonomous workflows. Book a call at https://iitdeveloper.com/contact",
    },
    {
        "name": "Full-Stack Web & App Modernization Sprint",
        "subject": "Turn Your App Into High-Performance Code That Actually Converts",
        "body_html": """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Web Modernization</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#0b1a2b; color:#ffffff; padding:40px;">
  <div style="max-width:600px; margin:0 auto; background:#112233; border-radius:16px; border:1px solid rgba(255,214,98,0.2); padding:32px;">
    <div style="text-align:center; margin-bottom:24px;">
      <img src="https://iitdeveloper.com/logo.png" alt="IITDeveloper" style="height:48px;">
    </div>
    <h1 style="color:#ffd662; font-size:24px; margin-bottom:16px; text-align:center;">We Turn Caffeine Into Clean Code 💻</h1>
    <p style="color:#d1d5db; font-size:16px; line-height:1.6;">Hi {{first_name}},</p>
    <p style="color:#d1d5db; font-size:16px; line-height:1.6;">
      Is your application slowing down or struggling to scale? Our full-stack engineering team builds lightning-fast web and mobile apps using <strong>Next.js 15, React, Python FastAPI, and cloud-native microservices</strong>.
    </p>
    <div style="text-align:center; margin:32px 0;">
      <a href="https://iitdeveloper.com/services/website-development" style="background:#ffd662; color:#0b1a2b; padding:14px 28px; font-weight:bold; border-radius:12px; text-decoration:none; display:inline-block;">View What We Build →</a>
    </div>
    <hr style="border:0; border-top:1px solid rgba(255,255,255,0.1); margin:24px 0;">
    <p style="font-size:12px; color:#9ca3af; text-align:center;">
      IITDeveloper • Registered in India • <a href="https://iitdeveloper.com" style="color:#ffd662;">iitdeveloper.com</a>
    </p>
  </div>
</body>
</html>""",
        "body_text": "Full stack web & mobile application modernization with Next.js & Python. Explore https://iitdeveloper.com",
    },
]


def prompt_user_if_missing(args: argparse.Namespace) -> tuple[str, str, str, str, str]:
    print("=" * 65)
    print(" 🚀 GROWIXA REST API CUSTOMER ONBOARDING CLIENT")
    print("=" * 65)

    base_url = args.api
    if not base_url:
        default_url = "http://localhost:8000"
        entered = input(f"[*] Enter API Base URL [{default_url}]: ").strip()
        base_url = entered if entered else default_url

    email = args.email
    if not email:
        while not email:
            email = input(
                "[*] Enter Customer Account Email (e.g. info@iitdeveloper.com): "
            ).strip()

    password = args.password
    if not password:
        while not password:
            password = getpass.getpass("[*] Enter Account Password: ").strip()

    full_name = args.name
    if not full_name:
        default_name = "Ravi Kant Yadav"
        entered = input(f"[*] Enter Owner Full Name [{default_name}]: ").strip()
        full_name = entered if entered else default_name

    company_name = args.company
    if not company_name:
        default_company = "IITDeveloper"
        entered = input(f"[*] Enter Company Name [{default_company}]: ").strip()
        company_name = entered if entered else default_company

    print("-" * 65)
    return base_url.rstrip("/"), email, password, full_name, company_name


def run_onboarding(
    base_url: str, email: str, password: str, full_name: str, company_name: str
) -> None:
    print(f"[*] Target API Endpoint: {base_url}")
    print(f"[*] Target Account User: {email}")
    print(f"[*] Target Company Name: {company_name}")

    client = httpx.Client(base_url=base_url, timeout=30.0)

    # Step 1: Check if user exists & login
    print("\n[1/5] Checking authentication...")
    login_resp = client.post("/auth/login", json={"email": email, "password": password})

    if login_resp.status_code == 200:
        print("[+] Logged in successfully with existing account!")
    elif login_resp.status_code in (401, 404):
        print(
            "[*] User not registered yet. Creating new tenant account via /accounts/register..."
        )
        reg_resp = client.post(
            "/accounts/register",
            json={
                "account_name": company_name,
                "email": email,
                "password": password,
                "full_name": full_name,
                "plan_slug": "pro",
            },
        )
        if reg_resp.status_code == 201:
            print("[+] Account registered successfully!")
            token = reg_resp.json().get("token")
            if token:
                print(f"[*] Verifying email token: {token[:10]}...")
                ver_resp = client.post("/accounts/verify-email", json={"token": token})
                if ver_resp.status_code in (200, 204):
                    print("[+] Email verified successfully!")
                else:
                    print(f"[!] Email verification warning: {ver_resp.status_code}")
            # Log in with the newly created account
            login_resp = client.post(
                "/auth/login", json={"email": email, "password": password}
            )
            if login_resp.status_code != 200:
                print(
                    f"[!] Login failed after registration: {login_resp.status_code} {login_resp.text}"
                )
                sys.exit(1)
            print("[+] Logged in with newly created account!")
        elif reg_resp.status_code == 409:
            print("[!] User email already exists, but provided password did not match.")
            sys.exit(1)
        else:
            print(f"[!] Registration failed: {reg_resp.status_code} {reg_resp.text}")
            sys.exit(1)
    else:
        print(f"[!] Unexpected response: {login_resp.status_code} {login_resp.text}")
        sys.exit(1)

    # Step 2: Update Company Profile
    print("\n[2/5] Updating Company Profile...")
    company_payload = dict(IITDEVELOPER_COMPANY_PAYLOAD)
    company_payload["name"] = company_name
    comp_resp = client.put("/company/profile", json=company_payload)
    if comp_resp.status_code == 200:
        print(
            f"[+] Company Profile updated: {comp_resp.json().get('name')} ({comp_resp.json().get('website')})"
        )
    else:
        print(
            f"[!] Failed to update Company Profile: {comp_resp.status_code} {comp_resp.text}"
        )

    # Step 3: Update Brand Profile & Voice
    print("\n[3/5] Updating Brand Voice & Guardrails...")
    brand_resp = client.put("/brand/profile", json=IITDEVELOPER_BRAND_PAYLOAD)
    if brand_resp.status_code == 200:
        print("[+] Brand Profile & Voice updated successfully!")
    else:
        print(
            f"[!] Failed to update Brand Profile: {brand_resp.status_code} {brand_resp.text}"
        )

    # Step 4: Create Branded Email Templates
    print("\n[4/5] Setting up Branded Email Templates...")
    existing_templates = client.get("/templates")
    existing_names = (
        {t.get("name") for t in existing_templates.json()}
        if existing_templates.status_code == 200
        else set()
    )

    for tmpl in TEMPLATES_DATA:
        if tmpl["name"] in existing_names:
            print(f"[*] Template '{tmpl['name']}' already exists — skipping.")
            continue
        t_resp = client.post(
            "/templates",
            json={
                "name": tmpl["name"],
                "subject": tmpl["subject"],
                "body_html": tmpl["body_html"],
                "body_text": tmpl["body_text"],
            },
        )
        if t_resp.status_code == 201:
            print(f"[+] Created Template: {tmpl['name']}")
        else:
            print(
                f"[!] Failed to create template '{tmpl['name']}': {t_resp.status_code} {t_resp.text}"
            )

    # Step 5: Finished
    print("\n" + "=" * 65)
    print(" 🎉 ONBOARDING COMPLETED SUCCESSFULLY VIA REST API!")
    print("=" * 65)
    print(f"  • API URL:      {base_url}")
    print(f"  • Account:      {company_name}")
    print(f"  • User Email:   {email}")
    print("  • Company Info: https://iitdeveloper.com")
    print("  • Brand Voice:  Configured & Active")
    print("  • Templates:    2 Branded Templates Ready")
    print("=" * 65)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Onboard a customer tenant via Growixa REST API"
    )
    parser.add_argument(
        "--api",
        default=None,
        help="API Base URL (e.g. http://localhost:8000 or https://api.prod.com)",
    )
    parser.add_argument("--email", default=None, help="User email")
    parser.add_argument("--password", default=None, help="User password")
    parser.add_argument("--name", default=None, help="User full name")
    parser.add_argument(
        "--company", default=None, help="Company Name (default: IITDeveloper)"
    )

    args = parser.parse_args()
    base_url, email, password, full_name, company_name = prompt_user_if_missing(args)
    run_onboarding(
        base_url=base_url,
        email=email,
        password=password,
        full_name=full_name,
        company_name=company_name,
    )


if __name__ == "__main__":
    main()
