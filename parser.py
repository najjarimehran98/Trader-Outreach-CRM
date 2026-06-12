import re
from datetime import datetime


def parse_trader_profile(text: str) -> dict:
    """Extract trader information from any pasted text.

    Supports various formats like:
    - Trader: Name
    - Platform: eToro
    - Followers: 15000
    - Monthly Return: +12.5%
    etc.
    """
    result = {
        "trader_name": "",
        "platform": "Manual",
        "location": "",
        "language": "",
        "strategy_type": "",
        "twitter": "",
        "telegram": "",
        "discord": "",
        "youtube": "",
        "website": "",
        "monthly_return": 0.0,
        "yearly_return": 0.0,
        "followers": 0,
        "copiers": 0,
        "assets_under_management": 0.0,
        "maximum_drawdown": 0.0,
        "risk_score": 0,
        "contact_method": "",
        "contact_info": "",
        "research_notes": "",
        "tags": "",
        "status": "Trader Found",
        "pipeline_stage": "Research",
        "date_added": datetime.utcnow().isoformat() + "Z",
        "date_updated": datetime.utcnow().isoformat() + "Z",
        "first_contact_date": None,
        "last_contact_date": None,
        "outreach_attempts": 0,
        "audience_strength": 0,
        "trading_consistency": 0,
        "communication_quality": 0,
        "crypto_knowledge": 0,
        "likelihood_to_join": 0,
        "brand_value": 0,
        "fit_score": 0,
        "creator_score": 0,
    }

    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or ':' not in line:
            continue

        # Split on first colon only
        parts = line.split(':', 1)
        key = parts[0].strip().lower()
        value = parts[1].strip()

        # Map key to result fields
        if 'trader' in key or 'name' in key:
            result['trader_name'] = value
        elif 'platform' in key:
            result['platform'] = value
        elif 'location' in key:
            result['location'] = value
        elif 'language' in key:
            result['language'] = value
        elif 'strategy' in key:
            result['strategy_type'] = value
        elif 'twitter' in key or 'x.com' in key:
            result['twitter'] = value.replace('@', '').strip()
        elif 'telegram' in key:
            result['telegram'] = value
        elif 'discord' in key:
            result['discord'] = value
        elif 'youtube' in key:
            result['youtube'] = value
        elif 'website' in key or 'url' in key or 'site' in key:
            result['website'] = value
        elif 'monthly' in key and 'return' in key:
            match = re.search(r'[-+]?[\d,.]+%?', value)
            if match:
                result['monthly_return'] = float(match.group().replace('%', '').replace(',', ''))
        elif 'yearly' in key and 'return' in key:
            match = re.search(r'[-+]?[\d,.]+%?', value)
            if match:
                result['yearly_return'] = float(match.group().replace('%', '').replace(',', ''))
        elif 'followers' in key:
            match = re.search(r'[\d,]+', value.replace(',', ''))
            if match:
                result['followers'] = int(match.group())
        elif 'copiers' in key:
            match = re.search(r'[\d,]+', value.replace(',', ''))
            if match:
                result['copiers'] = int(match.group())
        elif 'aum' in key or 'assets' in key or 'under management' in key:
            match = re.search(r'[\d,.]+', value.replace(',', ''))
            if match:
                result['assets_under_management'] = float(match.group())
        elif 'drawdown' in key:
            match = re.search(r'[\d,.]+%?', value)
            if match:
                result['maximum_drawdown'] = float(match.group().replace('%', ''))
        elif 'risk' in key and 'score' in key:
            match = re.search(r'\d+', value)
            if match:
                result['risk_score'] = int(match.group())
        elif 'contact' in key and 'method' in key:
            result['contact_method'] = value
        elif 'contact' in key and 'info' in key:
            result['contact_info'] = value
        elif 'notes' in key or 'research' in key:
            result['research_notes'] = value
        elif 'tags' in key or 'tags:' in key:
            result['tags'] = value

    return result
