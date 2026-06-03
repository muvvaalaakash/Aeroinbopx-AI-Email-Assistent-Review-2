import os
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="AeroInbox Rule Engine Service",
    description="Internal microservice to manage rules and evaluate rule-based email prioritization scores.",
    version="1.0.0"
)

RULES_FILE = os.path.join(os.path.dirname(__file__), "rules.json")

class PreferenceBoosts(BaseModel):
    inbox_boost: int = 0
    spam_boost: int = 0

class RulesConfig(BaseModel):
    vip_senders: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    custom_senders: List[str] = Field(default_factory=list)
    custom_keywords: List[str] = Field(default_factory=list)
    custom_categories: Dict[str, Any] = Field(default_factory=dict)
    preference_boosts: PreferenceBoosts = Field(default_factory=PreferenceBoosts)

class EmailModel(BaseModel):
    id: str
    sender: str
    subject: str
    snippet: str
    body: str
    folder: str

class EmailEvaluationResult(BaseModel):
    rule_score: int
    matched_rules: List[str]

def load_rules() -> Dict[str, Any]:
    """
    Loads configuration rules from rules.json. Fallbacks to defaults if file missing or corrupted.
    """
    if not os.path.exists(RULES_FILE):
        return {
            "vip_senders": ["ceo", "founder", "manager", "board", "director", "vice president"],
            "domains": ["client.com", "partner.com", "customer.com"],
            "keywords": ["urgent", "action required", "escalation", "payment", "invoice", "compliance", "immediately", "asap", "deadline"],
            "custom_senders": [],
            "custom_keywords": [],
            "custom_categories": {},
            "preference_boosts": {"inbox_boost": 0, "spam_boost": 0}
        }
    try:
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        # Graceful fallback
        return {}

def save_rules(rules: Dict[str, Any]):
    """
    Saves configuration rules to rules.json.
    """
    try:
        with open(RULES_FILE, "w") as f:
            json.dump(rules, f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save rules to disk: {str(e)}")

@app.get("/rules", response_model=RulesConfig)
def get_rules():
    """
    Returns the currently configured rules database.
    """
    return load_rules()

@app.post("/rules", response_model=RulesConfig)
def update_rules(config: RulesConfig):
    """
    Overwrites the rules database with a new configuration.
    """
    save_rules(config.model_dump())
    return config

@app.post("/evaluate/bulk", response_model=Dict[str, EmailEvaluationResult])
def evaluate_emails_bulk(emails: List[EmailModel]):
    """
    Runs rule matching logic over a list of emails and returns rule scores and match reasons.
    """
    rules = load_rules()
    vip_senders = [v.lower() for v in rules.get("vip_senders", [])]
    domains = [d.lower().strip("@") for d in rules.get("domains", [])]
    keywords = [k.lower() for k in rules.get("keywords", [])]
    custom_senders = [cs.lower() for cs in rules.get("custom_senders", [])]
    custom_keywords = [ck.lower() for ck in rules.get("custom_keywords", [])]
    boosts = rules.get("preference_boosts", {})
    inbox_boost = boosts.get("inbox_boost", 0)
    spam_boost = boosts.get("spam_boost", 0)

    results = {}

    for email in emails:
        rule_score = 0
        matched_rules = []
        sender_lower = email.sender.lower()
        subject_lower = email.subject.lower()
        snippet_lower = email.snippet.lower()
        body_lower = email.body.lower()

        # 1. VIP Senders
        vip_matched = False
        for vip in vip_senders:
            if vip in sender_lower:
                rule_score += 30
                matched_rules.append(f"VIP Sender Title: {vip}")
                vip_matched = True
                break

        # 2. Custom User Senders
        if not vip_matched:
            for cs in custom_senders:
                if cs in sender_lower:
                    rule_score += 35
                    matched_rules.append(f"Custom VIP Sender: {cs}")
                    break

        # 3. Domain Rules
        # Extract email domain if possible
        domain_matched = False
        # Simple domain extract from sender
        import re
        email_match = re.search(r'[\w\.-]+@([\w\.-]+)', sender_lower)
        if email_match:
            sender_domain = email_match.group(1)
            # Check domains
            for d in domains:
                if d in sender_domain:
                    rule_score += 20
                    matched_rules.append(f"Important Domain: @{d}")
                    domain_matched = True
                    break
            
            # Check custom domains
            if not domain_matched:
                # Custom domains can be defined under custom_categories or as simple rules if needed
                pass

        # 4. Standard Keywords (Subject & Snippet & Body)
        kw_matched_count = 0
        for kw in keywords:
            if kw in subject_lower or kw in snippet_lower:
                rule_score += 10
                matched_rules.append(f"Urgent Keyword: {kw}")
                kw_matched_count += 1
                if kw_matched_count >= 3: # Cap standard keyword scores at 30 points
                    break

        # 5. Custom User Keywords
        custom_kw_matched_count = 0
        for ck in custom_keywords:
            if ck in subject_lower or ck in body_lower:
                rule_score += 15
                matched_rules.append(f"Custom Keyword Match: {ck}")
                custom_kw_matched_count += 1
                if custom_kw_matched_count >= 2: # Cap custom keyword scores at 30 points
                    break

        # 6. Folder boosts
        if email.folder.upper() == "INBOX" and inbox_boost != 0:
            rule_score += inbox_boost
            matched_rules.append(f"Folder Preference Boost: Inbox ({inbox_boost})")
        elif email.folder.upper() == "SPAM" and spam_boost != 0:
            rule_score += spam_boost
            matched_rules.append(f"Folder Preference Boost: Spam ({spam_boost})")

        results[email.id] = EmailEvaluationResult(
            rule_score=rule_score,
            matched_rules=matched_rules
        )

    return results

@app.get("/health")
def health():
    return {"status": "healthy", "service": "rule-engine-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
