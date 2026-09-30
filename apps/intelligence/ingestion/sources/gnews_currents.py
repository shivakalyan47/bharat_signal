import json
import logging
import re
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from apps.intelligence.schemas.signal import (
    Signal, SignalSource, SignalLocation,
    SignalType, SourceCategory, VerificationStatus, ProvenanceLabel
)

logger = logging.getLogger(__name__)

GNEWS_API_KEY = "adecbcd5e33d7aa2b3ca92d255edcbc7"
CURRENTS_API_KEY = "WzSfvkJlNnQSsD_Xb-nATIb-s9mWoWZlm5--vIqgdbAsWQEl"

INDIA_LOCATIONS = {
    "Delhi": (28.6139, 77.2090, "North India"),
    "New Delhi": (28.6139, 77.2090, "North India"),
    "Mumbai": (19.0760, 72.8777, "West India"),
    "Bengaluru": (12.9716, 77.5946, "South India"),
    "Bangalore": (12.9716, 77.5946, "South India"),
    "Chennai": (13.0827, 80.2707, "South India"),
    "Kolkata": (22.5726, 88.3639, "East India"),
    "Hyderabad": (17.3850, 78.4867, "South India"),
    "Pune": (18.5204, 73.8567, "West India"),
    "Ahmedabad": (23.0225, 72.5714, "West India"),
    "Surat": (21.1702, 72.8311, "West India"),
    "Jaipur": (26.9124, 75.7873, "North India"),
    "Lucknow": (26.8467, 80.9462, "North India"),
    "Kanpur": (26.4499, 80.3319, "North India"),
    "Nagpur": (21.1458, 79.0882, "Central India"),
    "Indore": (22.7196, 75.8577, "Central India"),
    "Thane": (19.2183, 72.9781, "West India"),
    "Bhopal": (23.2599, 77.4126, "Central India"),
    "Visakhapatnam": (17.6868, 83.2185, "South India"),
    "Pimpri-Chinchwad": (18.6298, 73.7997, "West India"),
    "Patna": (25.5941, 85.1376, "East India"),
    "Vadodara": (22.3072, 73.1812, "West India"),
    "Ghaziabad": (28.6692, 77.4538, "North India"),
    "Ludhiana": (30.9010, 75.8523, "North India"),
    "Agra": (27.1767, 78.0081, "North India"),
    "Nashik": (20.0110, 73.7903, "West India"),
    "Ranchi": (23.3441, 85.3096, "East India"),
    "Faridabad": (28.4089, 77.3178, "North India"),
    "Meerut": (28.9845, 77.7064, "North India"),
    "Rajkot": (22.3039, 70.8022, "West India"),
    "Kalyan-Dombivli": (19.2403, 73.1305, "West India"),
    "Vasai-Virar": (19.3919, 72.8397, "West India"),
    "Varanasi": (25.3176, 82.9739, "North India"),
    "Srinagar": (34.0837, 74.7973, "North India"),
    "Aurangabad": (19.8762, 75.3433, "West India"),
    "Dhanbad": (23.7957, 86.4304, "East India"),
    "Amritsar": (31.6340, 74.8723, "North India"),
    "Navi Mumbai": (19.0330, 73.0297, "West India"),
    "Allahabad": (25.4358, 81.8463, "North India"),
    "Prayagraj": (25.4358, 81.8463, "North India"),
    "Howrah": (22.5958, 88.3110, "East India"),
    "Jabalpur": (23.1686, 79.9339, "Central India"),
    "Gwalior": (26.2124, 78.1772, "Central India"),
    "Vijayawada": (16.5062, 80.6480, "South India"),
    "Jodhpur": (26.2389, 73.0243, "North India"),
    "Madurai": (9.9252, 78.1198, "South India"),
    "Raipur": (21.2514, 81.6296, "Central India"),
    "Kota": (25.1499, 75.8333, "North India"),
    "Guwahati": (26.1445, 91.7362, "Northeast India"),
    "Chandigarh": (30.7333, 76.7794, "North India"),
    "Solapur": (17.6599, 75.9064, "West India"),
    "Hubli": (15.3647, 75.1240, "South India"),
    "Bareilly": (28.3670, 79.4304, "North India"),
    "Moradabad": (28.8386, 78.7733, "North India"),
    "Mysore": (12.2958, 76.6394, "South India"),
    "Gurgaon": (28.4595, 77.0266, "North India"),
    "Gurugram": (28.4595, 77.0266, "North India"),
    "Aligarh": (27.8974, 78.0880, "North India"),
    "Jalandhar": (31.3260, 75.5762, "North India"),
    "Tiruchirappalli": (10.7905, 78.7047, "South India"),
    "Bhubaneswar": (20.2961, 85.8245, "East India"),
    "Salem": (11.6643, 78.1460, "South India"),
    "Warangal": (18.0000, 79.5833, "South India"),
    "Mira-Bhayandar": (19.2952, 72.8544, "West India"),
    "Thiruvananthapuram": (8.5241, 76.9366, "South India"),
    "Bhiwandi": (19.2950, 73.0632, "West India"),
    "Saharanpur": (29.9640, 77.5460, "North India"),
    "Gorakhpur": (26.7606, 83.3732, "North India"),
    "Guntur": (16.3067, 80.4365, "South India"),
    "Bikaner": (28.0229, 73.3119, "North India"),
    "Amravati": (20.9320, 77.7523, "West India"),
    "Noida": (28.5355, 77.3910, "North India"),
    "Jamshedpur": (22.8046, 86.2029, "East India"),
    "Bhilai": (21.1938, 81.3509, "Central India"),
    "Cuttack": (20.4625, 85.8830, "East India"),
    "Firozabad": (27.1599, 78.3956, "North India"),
    "Kochi": (9.9312, 76.2673, "South India"),
}

def _fetch_url(url: str) -> Optional[Dict]:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            return json.loads(data.decode('utf-8'))
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return None

def nlp_extract_intelligence(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    
    severity = 0.3
    if re.search(r'\b(catastrophic|devastating|deadly|killed|death)\b', text_lower):
        severity = 0.95
    elif re.search(r'\b(major|severe|critical|emergency|massive|destruction)\b', text_lower):
        severity = 0.8
    elif re.search(r'\b(significant|serious|warning|heavy|danger|injured)\b', text_lower):
        severity = 0.6
    elif re.search(r'\b(moderate|impact)\b', text_lower):
        severity = 0.45

    entities = []
    lat, lon, region = None, None, None
    for loc, (l_lat, l_lon, l_reg) in INDIA_LOCATIONS.items():
        if re.search(rf'\b{loc.lower()}\b', text_lower):
            entities.append(loc)
            if not lat:
                lat, lon, region = l_lat, l_lon, l_reg

    if not lat:
        lat, lon, region = 22.5, 82.5, "Central India"
        
    sig_type = SignalType.MEDIA
    if re.search(r'\b(earthquake|tremor|seismic)\b', text_lower):
        sig_type = SignalType.SEISMIC
    elif re.search(r'\b(flood|rain|cyclone|storm|weather)\b', text_lower):
        sig_type = SignalType.WEATHER
    elif re.search(r'\b(fire|explosion|industrial)\b', text_lower):
        sig_type = SignalType.INDUSTRIAL
    elif re.search(r'\b(health|disease|hospital)\b', text_lower):
        sig_type = SignalType.HEALTH
    elif re.search(r'\b(road|bridge|power|building)\b', text_lower):
        sig_type = SignalType.INFRASTRUCTURE
    elif re.search(r'\b(protest|terror|security)\b', text_lower):
        sig_type = SignalType.PUBLIC_REPORT
    elif re.search(r'\b(pollution|environment)\b', text_lower):
        sig_type = SignalType.ENVIRONMENTAL

    domain = "general"
    if sig_type in (SignalType.SEISMIC, SignalType.WEATHER, SignalType.INDUSTRIAL):
        domain = "disaster"
    elif sig_type == SignalType.HEALTH:
        domain = "health"
    elif sig_type == SignalType.INFRASTRUCTURE:
        domain = "infrastructure"
    elif sig_type == SignalType.PUBLIC_REPORT:
        domain = "security"
    elif sig_type == SignalType.ENVIRONMENTAL:
        domain = "environment"

    concepts = []
    if "flood" in text_lower or "rain" in text_lower:
        concepts.append("water_logging")
    if "fire" in text_lower:
        concepts.append("fire_hazard")
    if "accident" in text_lower:
        concepts.append("road_accident")
    if not concepts:
        concepts.append("general_news")

    return {
        "severity": severity,
        "entities": entities,
        "lat": lat,
        "lon": lon,
        "region": region,
        "signal_type": sig_type,
        "domain": domain,
        "concepts": concepts
    }

def fetch_gnews_signals() -> List[Signal]:
    signals = []
    
    urls = [
        f"https://gnews.io/api/v4/search?q=India+disaster+OR+earthquake+OR+flood+OR+cyclone+OR+fire+OR+accident+OR+emergency&lang=en&country=in&max=50&apikey={GNEWS_API_KEY}",
        f"https://gnews.io/api/v4/top-headlines?category=general&lang=en&country=in&max=50&apikey={GNEWS_API_KEY}"
    ]
    
    seen_urls = set()
    index = 1
    for url in urls:
        data = _fetch_url(url)
        if not data or 'articles' not in data:
            continue
            
        for article in data['articles']:
            a_url = article.get('url')
            if not a_url or a_url in seen_urls:
                continue
            seen_urls.add(a_url)
            
            title = article.get('title', '')
            desc = article.get('description', '')
            content = article.get('content', '')
            full_text = f"{title} {desc} {content}"
            
            pub_date = article.get('publishedAt')
            try:
                dt = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except Exception:
                dt = datetime.now(timezone.utc)
                
            nlp = nlp_extract_intelligence(full_text)
            
            signal = Signal(
                id=f"SIG-NEWS-GNEWS-{index:04d}",
                source=SignalSource(
                    id="gnews-api",
                    name="GNews",
                    category=SourceCategory.MEDIA,
                    verification=VerificationStatus.REPUTABLE
                ),
                type=nlp["signal_type"],
                title=title,
                description=desc[:500] if desc else title,
                location=SignalLocation(
                    latitude=nlp["lat"],
                    longitude=nlp["lon"],
                    region=nlp["region"]
                ),
                timestamp=dt,
                entities=nlp["entities"],
                severity=nlp["severity"],
                provenance=ProvenanceLabel.OBSERVED,
                confidence=0.75,
                language="en",
                domain=nlp["domain"],
                tags=nlp["concepts"]
            )
            signals.append(signal)
            index += 1
            
    return signals

def fetch_currents_signals() -> List[Signal]:
    signals = []
    
    urls = [
        f"https://api.currentsapi.services/v1/search?keywords=India+disaster+earthquake+flood+cyclone+fire+accident&language=en&country=IN&apiKey={CURRENTS_API_KEY}",
        f"https://api.currentsapi.services/v1/latest-news?language=en&country=IN&apiKey={CURRENTS_API_KEY}"
    ]
    
    seen_urls = set()
    index = 1
    for url in urls:
        data = _fetch_url(url)
        if not data or 'news' not in data:
            continue
            
        for article in data['news']:
            a_url = article.get('url')
            if not a_url or a_url in seen_urls:
                continue
            seen_urls.add(a_url)
            
            title = article.get('title', '')
            desc = article.get('description', '')
            full_text = f"{title} {desc}"
            
            pub_date = article.get('published')
            try:
                dt = datetime.strptime(pub_date[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except Exception:
                dt = datetime.now(timezone.utc)
                
            nlp = nlp_extract_intelligence(full_text)
            
            signal = Signal(
                id=f"SIG-NEWS-CURR-{index:04d}",
                source=SignalSource(
                    id="currents-api",
                    name="CurrentsAPI",
                    category=SourceCategory.MEDIA,
                    verification=VerificationStatus.REPUTABLE
                ),
                type=nlp["signal_type"],
                title=title,
                description=desc[:500] if desc else title,
                location=SignalLocation(
                    latitude=nlp["lat"],
                    longitude=nlp["lon"],
                    region=nlp["region"]
                ),
                timestamp=dt,
                entities=nlp["entities"],
                severity=nlp["severity"],
                provenance=ProvenanceLabel.OBSERVED,
                confidence=0.75,
                language="en",
                domain=nlp["domain"],
                tags=nlp["concepts"]
            )
            signals.append(signal)
            index += 1
            
    return signals

def fetch_extra_news_signals() -> List[Signal]:
    gnews = fetch_gnews_signals()
    currents = fetch_currents_signals()
    
    all_signals = gnews + currents
    unique_signals = []
    seen_titles = set()
    
    for sig in all_signals:
        title_lower = sig.title.lower().strip()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_signals.append(sig)
            
    return unique_signals
