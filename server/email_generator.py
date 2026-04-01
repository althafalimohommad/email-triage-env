"""
Synthetic Email Data Generator for Email Triage Environment.

Generates realistic email datasets with ground-truth labels for all 3 tasks.
Each email comes with known correct classification, priority, and expected action.
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path


# ── Email Templates ──────────────────────────────────────────────────────────

SENDERS = {
    "urgent": [
        ("ceo@acmecorp.com", "acmecorp.com"),
        ("sre-alerts@acmecorp.com", "acmecorp.com"),
        ("security@acmecorp.com", "acmecorp.com"),
        ("manager@acmecorp.com", "acmecorp.com"),
        ("vp-engineering@acmecorp.com", "acmecorp.com"),
    ],
    "follow_up": [
        ("colleague@acmecorp.com", "acmecorp.com"),
        ("lead@acmecorp.com", "acmecorp.com"),
        ("vendor@partnerco.com", "partnerco.com"),
        ("client@bigclient.com", "bigclient.com"),
    ],
    "fyi": [
        ("hr@acmecorp.com", "acmecorp.com"),
        ("newsletter@techdigest.io", "techdigest.io"),
        ("comms@acmecorp.com", "acmecorp.com"),
        ("updates@industry-news.com", "industry-news.com"),
    ],
    "spam": [
        ("deals@random-shop.xyz", "random-shop.xyz"),
        ("winner@lottery-intl.co", "lottery-intl.co"),
        ("noreply@verify-now.click", "verify-now.click"),
        ("offers@cheap-meds.biz", "cheap-meds.biz"),
        ("admin@prize-claim.net", "prize-claim.net"),
    ],
    "meeting": [
        ("calendar@acmecorp.com", "acmecorp.com"),
        ("pm@acmecorp.com", "acmecorp.com"),
        ("teammate@acmecorp.com", "acmecorp.com"),
        ("recruiter@hiringco.com", "hiringco.com"),
    ],
    "approval": [
        ("finance@acmecorp.com", "acmecorp.com"),
        ("hr@acmecorp.com", "acmecorp.com"),
        ("procurement@acmecorp.com", "acmecorp.com"),
        ("legal@acmecorp.com", "acmecorp.com"),
    ],
}

SUBJECTS = {
    "urgent": [
        "🚨 URGENT: Production server down — all hands needed",
        "CRITICAL: Customer data breach detected — immediate action required",
        "P0 Incident: Payment processing failing across all regions",
        "URGENT: Key client threatening to cancel contract TODAY",
        "EMERGENCY: Security vulnerability in production — patch ASAP",
        "ACTION REQUIRED: Board meeting moved to today — need your report NOW",
        "CRITICAL BUG: Users losing data on save — fix needed immediately",
        "URGENT: Regulatory deadline is TODAY — compliance docs missing",
    ],
    "follow_up": [
        "RE: Q3 roadmap — waiting on your input",
        "Following up: design review feedback",
        "Reminder: project proposal due this Friday",
        "RE: Could you review the attached document?",
        "Circling back on the API integration timeline",
        "Gentle reminder: action items from last standup",
        "RE: Budget allocation — need your sign-off",
        "Following up on our conversation about the migration plan",
    ],
    "fyi": [
        "FYI: New office holiday schedule for 2026",
        "Company All-Hands recording now available",
        "Weekly Engineering Newsletter — Issue #147",
        "FYI: Updated parking policy starting next month",
        "New blog post: How we scaled to 10M users",
        "Team offsite photos uploaded to shared drive",
        "Industry report: State of AI in Enterprise 2026",
        "FYI: Kitchen renovation — use 3rd floor break room",
    ],
    "spam": [
        "YOU WON $1,000,000!!! Claim your prize NOW!!!",
        "🔥 EXCLUSIVE DEAL: 95% OFF designer watches — TODAY ONLY",
        "Congratulations! You've been selected for a special offer",
        "URGENT: Your account will be suspended — verify immediately",
        "Make $5,000/day from home with this ONE trick",
        "Re: Your order #99281 — action required",
        "You have (1) new message from a beautiful woman near you",
        "Limited time: FREE iPhone 20 — just pay shipping!",
    ],
    "meeting": [
        "Meeting Invite: Sprint Planning (Tomorrow 10 AM)",
        "Can we sync for 30 min Thursday afternoon?",
        "1:1 rescheduled to 3 PM Wednesday",
        "Team retrospective — please add agenda items",
        "Interview panel: Frontend candidate at 2 PM",
        "Lunch & Learn: Introduction to WebAssembly",
        "Standup reminder — daily at 9:15 AM",
        "Meeting: Quarterly Business Review prep",
    ],
    "approval": [
        "Expense Report #4521 — $2,340 — Needs Your Approval",
        "PTO Request: Dec 23-27 — Awaiting Manager Approval",
        "Purchase Order: New dev laptops ($15,000) — Approval Required",
        "Contract Amendment: Partner Co. — Legal review needed",
        "Access Request: Production database — Security approval required",
        "Hiring Requisition: Senior Backend Engineer — VP approval needed",
        "Travel Request: SF conference — Budget approval required",
        "Software License: Renewal $8,500/yr — Finance approval needed",
    ],
}

BODIES = {
    "urgent": [
        "The production server went down at 2:47 AM. Our monitoring shows all API endpoints returning 500 errors. Customer-facing services are completely unavailable. We need everyone online ASAP to diagnose and fix this. Current impact: ~50,000 users affected. Please join the incident channel immediately.",
        "Our security team has detected unauthorized access to the customer database. Preliminary analysis shows potential exposure of email addresses and hashed passwords for approximately 12,000 accounts. We need to: 1) Contain the breach 2) Notify affected users 3) Report to regulatory bodies within 72 hours. Drop everything and join the war room.",
        "Payment processing has been failing intermittently since 6 AM. We've confirmed the issue affects Stripe and PayPal integrations across US, EU, and APAC regions. Revenue impact estimated at $45,000/hour. Engineering and finance teams need to coordinate on this immediately.",
        "Our biggest client (30% of revenue) just emailed saying they're evaluating competitors and want a meeting TODAY to discuss unresolved issues. We need sales, engineering, and product leads in a room by 2 PM to prepare our response and retention strategy.",
        "A critical RCE vulnerability (CVE-2026-1234) has been published affecting our web framework version. Our production systems are vulnerable. A patch is available but requires testing. We need to deploy to staging within 2 hours and production by end of day.",
    ],
    "follow_up": [
        "Hey, just following up on the Q3 roadmap discussion from last week. We need your team's priorities and resource estimates to finalize the plan. Could you send those over by Thursday? The leadership team is expecting the final version by next Monday.",
        "Hi, I wanted to circle back on the design review from Tuesday. You had some great suggestions about the navigation flow, but I want to make sure I captured your concerns about the mobile layout correctly. Can you confirm the feedback in the shared doc?",
        "Quick reminder that the project proposal for the new microservices architecture is due this Friday. I know you wanted to include the cost analysis — do you have the numbers from the cloud team yet? Happy to help if you need anything.",
        "Following up on our conversation about the database migration plan. The DBA team has approved the schema changes, but we still need your sign-off on the rollback strategy before we can schedule the maintenance window.",
    ],
    "fyi": [
        "Hi team, just a heads up that the office will be closed on the following dates for the 2026 holiday season: Dec 24-25, Dec 31-Jan 1. Please plan your projects accordingly. Remote work is available for all other days during the holiday period.",
        "The recording from yesterday's company all-hands is now available on the intranet. Key topics covered: Q3 financial results (revenue up 15%), new product roadmap, and the upcoming office expansion. Q&A section starts at the 45-minute mark.",
        "This week in engineering: We shipped the new caching layer (latency down 40%), the mobile team hit 99.9% crash-free rate, and we're kicking off the accessibility audit next sprint. Full details in the wiki.",
        "Just FYI — the parking garage on the east side will be closed for renovations starting next month. Temporary parking will be available in Lot C. Shuttle service will run every 15 minutes from 7 AM to 7 PM.",
    ],
    "spam": [
        "CONGRATULATIONS!!! You have been randomly selected as our GRAND PRIZE WINNER of $1,000,000 USD! To claim your prize, simply click the link below and enter your bank account details for instant transfer. This offer expires in 24 hours! Don't miss out on this once-in-a-lifetime opportunity! Click here: http://totally-legit-prize.xyz/claim",
        "Dear valued customer, we noticed unusual activity on your account. Your account will be PERMANENTLY SUSPENDED unless you verify your identity within 12 hours. Click here to verify: http://secure-verify-account.click/login. Note: Failure to verify will result in permanent data loss.",
        "Hi! I am Prince Abubakar from Nigeria. I have $50,000,000 USD that I need help transferring to a foreign account. For your assistance, you will receive 30% ($15,000,000). Please reply with your full name, address, and bank details to proceed. This is 100% legal and risk-free.",
        "🔥 FLASH SALE 🔥 Get designer watches, handbags, and electronics at 95% OFF retail price! We're the #1 rated online store with millions of satisfied customers. Order now and get FREE shipping worldwide! Visit: http://super-cheap-deals.biz/shop",
    ],
    "meeting": [
        "Hi team, let's get together for our bi-weekly sprint planning session tomorrow at 10 AM in Conference Room B (or join via Zoom link below). Please come prepared with: 1) Status update on current sprint items, 2) Blockers and risks, 3) Capacity for next sprint. Expected duration: 1 hour.",
        "Hey! Are you free Thursday afternoon for a quick sync? I want to go over the API contract changes before we start implementation next week. 30 minutes should be enough. Let me know what time works for you between 1-5 PM.",
        "Our 1:1 has been rescheduled from Monday to Wednesday at 3 PM due to the client demo conflict. Same Zoom link. I'd like to discuss your career development goals and the tech lead opportunity that opened up.",
        "Reminder: Team retrospective is this Friday at 2 PM. Please add your thoughts to the retro board before the meeting: What went well? What could be improved? Action items from last retro. Link to board: retro.acmecorp.com/sprint-47",
    ],
    "approval": [
        "Hi, please review and approve the attached expense report #4521 for $2,340.00. Breakdown: Client dinner ($450), Uber rides during business trip ($190), Hotel in NYC 2 nights ($1,200), Conference registration ($500). All receipts are attached. This needs approval by end of week for the current billing cycle.",
        "I'd like to request PTO from December 23-27 (3 working days + 2 holidays). My projects are on track and I've arranged coverage with Sarah for any urgent issues. Please approve at your earliest convenience so I can book flights.",
        "We need to order 10 new MacBook Pro laptops for the incoming engineering hires starting January 15. Total cost: $15,000. Vendor: Apple Business. Delivery: 5-7 business days. Budget code: ENG-2026-Q1. Please approve so we can place the order this week.",
        "The annual license renewal for our monitoring platform is due January 1. Cost: $8,500/year (same as last year). We evaluated alternatives but this remains the best option for our needs. Finance approval required to process payment. Detailed comparison report attached.",
    ],
}

RESPONSE_KEYWORDS = {
    "urgent": ["acknowledge", "investigating", "priority", "immediately", "team", "fix", "update"],
    "approval": ["approved", "review", "confirmed", "processed", "authorize"],
}


# ── Generator Functions ──────────────────────────────────────────────────────


def _generate_email(category: str, index: int) -> dict:
    """Generate a single email with ground-truth labels."""
    sender_info = random.choice(SENDERS[category])
    subject = random.choice(SUBJECTS[category])
    body = random.choice(BODIES[category])

    # Vary timestamps — emails arrive over the last 48 hours
    hours_ago = random.randint(0, 48)
    timestamp = (datetime.now() - timedelta(hours=hours_ago)).isoformat()

    priority_map = {
        "urgent": 5,
        "approval": 4,
        "follow_up": 3,
        "meeting": 3,
        "fyi": 2,
        "spam": 1,
    }
    action_map = {
        "urgent": "reply",
        "approval": "reply",
        "follow_up": "flag",
        "meeting": "classify",
        "fyi": "classify",
        "spam": "archive",
    }

    return {
        "email_id": f"email-{index:03d}-{uuid.uuid4().hex[:6]}",
        "sender": sender_info[0],
        "sender_domain": sender_info[1],
        "subject": subject,
        "body": body,
        "timestamp": timestamp,
        "has_attachments": random.random() > 0.7,
        "reply_to": None,
        "labels": {
            "category": category,
            "priority": priority_map[category],
            "expected_action": action_map[category],
            "needs_reply": category in ("urgent", "approval"),
            "response_keywords": RESPONSE_KEYWORDS.get(category, []),
        },
    }


def _get_distribution(task_id: str) -> dict:
    """Get category distribution for each task difficulty."""
    distributions = {
        "easy": {
            "spam": 10,
            "urgent": 2,
            "fyi": 4,
            "follow_up": 2,
            "meeting": 2,
        },
        "medium": {
            "spam": 5,
            "urgent": 5,
            "follow_up": 5,
            "fyi": 5,
            "meeting": 5,
            "approval": 5,
        },
        "hard": {
            "spam": 6,
            "urgent": 8,
            "follow_up": 6,
            "fyi": 4,
            "meeting": 6,
            "approval": 10,
        },
    }
    return distributions[task_id]


TASK_CONFIGS = {
    "easy": {
        "task_id": "easy",
        "description": (
            "You are an email triage assistant. For each email, determine if it is SPAM or NOT SPAM. "
            "Use the CLASSIFY action. If it's spam, set category='spam'. "
            "For legitimate emails, set the most appropriate category "
            "(urgent, follow_up, fyi, meeting, approval). "
            "Set priority to 1 for spam, or your best estimate (1-5) for others."
        ),
        "available_actions": ["classify"],
        "time_limit": 120,
        "difficulty": "easy",
    },
    "medium": {
        "task_id": "medium",
        "description": (
            "You are an email triage assistant. For each email:\n"
            "1. CLASSIFY it into one of: urgent, follow_up, fyi, spam, meeting, approval\n"
            "2. Set PRIORITY (1=lowest, 5=critical)\n"
            "3. Optionally FLAG important emails or ARCHIVE spam\n"
            "Maximize both classification accuracy and priority accuracy."
        ),
        "available_actions": ["classify", "flag", "archive"],
        "time_limit": 180,
        "difficulty": "medium",
    },
    "hard": {
        "task_id": "hard",
        "description": (
            "You are a professional email triage assistant handling a busy executive inbox. "
            "For each email:\n"
            "1. CLASSIFY into: urgent, follow_up, fyi, spam, meeting, approval\n"
            "2. Set PRIORITY (1=lowest, 5=critical)\n"
            "3. For urgent/approval emails: REPLY with an appropriate professional response\n"
            "4. For spam: ARCHIVE immediately\n"
            "5. For complex issues beyond your scope: ESCALATE with a reason\n"
            "6. For important non-urgent items: FLAG for follow-up\n"
            "CRITICAL: Never miss an urgent email — heavy penalty for missed urgents.\n"
            "Response quality matters — include relevant acknowledgments and next steps."
        ),
        "available_actions": ["classify", "reply", "flag", "archive", "escalate"],
        "time_limit": 300,
        "difficulty": "hard",
    },
}


def generate_dataset(task_id: str) -> dict:
    """
    Generate a complete email dataset for a given task.

    Args:
        task_id: One of 'easy', 'medium', 'hard'

    Returns:
        Dictionary with 'task_config' and 'emails' keys
    """
    random.seed(42 + hash(task_id))  # Deterministic for reproducibility

    distribution = _get_distribution(task_id)
    emails = []
    index = 0

    for category, count in distribution.items():
        for _ in range(count):
            email = _generate_email(category, index)
            emails.append(email)
            index += 1

    # Shuffle but with fixed seed for reproducibility
    random.shuffle(emails)

    return {
        "task_config": TASK_CONFIGS[task_id],
        "emails": emails,
    }


def generate_all_datasets(output_dir: str = "data"):
    """Generate and save datasets for all 3 tasks."""
    os.makedirs(output_dir, exist_ok=True)

    for task_id in ["easy", "medium", "hard"]:
        data = generate_dataset(task_id)
        filepath = os.path.join(output_dir, f"emails_{task_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✓ Generated {filepath} — {len(data['emails'])} emails")


if __name__ == "__main__":
    generate_all_datasets()
