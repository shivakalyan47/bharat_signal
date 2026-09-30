import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
import re
from typing import List, Dict, Any, Optional

from apps.intelligence.schemas.signal import (
    Signal, SignalType, SignalSource, SignalLocation,
    SourceCategory, VerificationStatus, ProvenanceLabel
)

NEWSAPI_KEY = "7aedd4f11e8f4825b0da092e46110155"
WORLDNEWSAPI_KEY = "31cab2cd7b9544f0a9360f9d1e6db993"

INDIA_LOCATIONS = {
    # State Capitals and Major Cities
    "New Delhi": (28.6139, 77.2090, "North India"),
    "Delhi": (28.7041, 77.1025, "North India"),
    "Mumbai": (19.0760, 72.8777, "West India"),
    "Bangalore": (12.9716, 77.5946, "South India"),
    "Bengaluru": (12.9716, 77.5946, "South India"),
    "Hyderabad": (17.3850, 78.4867, "South India"),
    "Chennai": (13.0827, 80.2707, "South India"),
    "Kolkata": (22.5726, 88.3639, "East India"),
    "Ahmedabad": (23.0225, 72.5714, "West India"),
    "Pune": (18.5204, 73.8567, "West India"),
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
    "Ludhiana": (30.9010, 75.8573, "North India"),
    "Agra": (27.1767, 78.0081, "North India"),
    "Nashik": (20.0110, 73.7903, "West India"),
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
    "Howrah": (22.5958, 88.3236, "East India"),
    "Ranchi": (23.3441, 85.3096, "East India"),
    "Gwalior": (26.2124, 78.1772, "Central India"),
    "Jabalpur": (23.1815, 79.9864, "Central India"),
    "Coimbatore": (11.0168, 76.9558, "South India"),
    "Vijayawada": (16.5062, 80.6480, "South India"),
    "Jodhpur": (26.2389, 73.0243, "North India"),
    "Madurai": (9.9252, 78.1198, "South India"),
    "Raipur": (21.2514, 81.6296, "Central India"),
    "Kota": (25.2138, 75.8648, "North India"),
    "Chandigarh": (30.7333, 76.7794, "North India"),
    "Guwahati": (26.1445, 91.7362, "Northeast India"),
    "Solapur": (17.6599, 75.9064, "West India"),
    "Hubli-Dharwad": (15.3647, 75.1240, "South India"),
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
    "Mira-Bhayandar": (19.2952, 72.8544, "West India"),
    "Warangal": (17.9689, 79.5941, "South India"),
    "Thiruvananthapuram": (8.5241, 76.9366, "South India"),
    "Bhiwandi": (19.2813, 73.0483, "West India"),
    "Saharanpur": (29.9640, 77.5460, "North India"),
    "Gorakhpur": (26.7606, 83.3732, "North India"),
    "Guntur": (16.3067, 80.4365, "South India"),
    "Bikaner": (28.0229, 73.3119, "North India"),
    "Amravati": (20.9320, 77.7523, "West India"),
    "Noida": (28.5355, 77.3910, "North India"),
    "Jamshedpur": (22.8046, 86.2029, "East India"),
    "Bhilai": (21.1938, 81.3509, "Central India"),
    "Cuttack": (20.4625, 85.8828, "East India"),
    "Firozabad": (27.1599, 78.3957, "North India"),
    "Kochi": (9.9312, 76.2673, "South India"),
    "Bhavnagar": (21.7645, 72.1519, "West India"),
    "Dehradun": (30.3165, 78.0322, "North India"),
    "Durgapur": (23.5204, 87.3119, "East India"),
    "Asansol": (23.6739, 86.9524, "East India"),
    "Rourkela": (22.2604, 84.8536, "East India"),
    "Nanded": (19.1383, 77.3210, "West India"),
    "Kolhapur": (16.7050, 74.2433, "West India"),
    "Ajmer": (26.4499, 74.6399, "North India"),
    "Akola": (20.7059, 77.0015, "West India"),
    "Gulbarga": (17.3297, 76.8343, "South India"),
    "Jamnagar": (22.4707, 70.0577, "West India"),
    "Ujjain": (23.1765, 75.7885, "Central India"),
    "Loni": (28.7500, 77.2800, "North India"),
    "Siliguri": (26.7271, 88.3953, "East India"),
    "Jhansi": (25.4484, 78.5685, "North India"),
    "Ulhasnagar": (19.2184, 73.1631, "West India"),
    "Nellore": (14.4426, 79.9865, "South India"),
    "Jammu": (32.7266, 74.8570, "North India"),
    "Sangli-Miraj & Kupwad": (16.8524, 74.5815, "West India"),
    "Belgaum": (15.8497, 74.4977, "South India"),
    "Mangalore": (12.8722, 74.8425, "South India"),
    "Ambattur": (13.1143, 80.1548, "South India"),
    "Tirunelveli": (8.7139, 77.7567, "South India"),
    "Malegaon": (20.5537, 74.5359, "West India"),
    "Gaya": (24.7955, 85.0002, "East India"),
    "Jalgaon": (21.0077, 75.5626, "West India"),
    "Udaipur": (24.5854, 73.7125, "North India"),
    "Maheshtala": (22.5126, 88.2471, "East India"),
    "Davanagere": (14.4644, 75.9218, "South India"),
    "Kozhikode": (11.2588, 75.7804, "South India"),
    "Kurnool": (15.8281, 78.0373, "South India"),
    "Rajpur Sonarpur": (22.4385, 88.4323, "East India"),
    "Rajahmundry": (17.0005, 81.8040, "South India"),
    "Bokaro": (23.6693, 86.1511, "East India"),
    "South Dumdum": (22.6131, 88.4011, "East India"),
    "Bellary": (15.1394, 76.9214, "South India"),
    "Patiala": (30.3398, 76.3869, "North India"),
    "Gopalpur": (22.6247, 88.5175, "East India"),
    "Agartala": (23.8315, 91.2868, "Northeast India"),
    "Bhagalpur": (25.2425, 87.0177, "East India"),
    "Muzaffarnagar": (29.4727, 77.7085, "North India"),
    "Bhatpara": (22.8687, 88.4116, "East India"),
    "Panihati": (22.6934, 88.3758, "East India"),
    "Latur": (18.4088, 76.5604, "West India"),
    "Dhule": (20.9042, 74.7749, "West India"),
    "Tirupati": (13.6288, 79.4192, "South India"),
    "Rohtak": (28.8955, 76.5816, "North India"),
    "Korba": (22.3595, 82.7501, "Central India"),
    "Bhilwara": (25.3463, 74.6364, "North India"),
    "Berhampur": (19.3150, 84.7941, "East India"),
    "Muzaffarpur": (26.1209, 85.3647, "East India"),
    "Ahmednagar": (19.0952, 74.7496, "West India"),
    "Mathura": (27.4924, 77.6737, "North India"),
    "Kollam": (8.8932, 76.6141, "South India"),
    "Avadi": (13.1187, 80.0963, "South India"),
    "Kadapa": (14.4674, 78.8241, "South India"),
    "Kamarhati": (22.6713, 88.3761, "East India"),
    "Sambalpur": (21.4669, 83.9812, "East India"),
    "Bilaspur": (22.0797, 82.1409, "Central India"),
    "Shahjahanpur": (27.8806, 79.9126, "North India"),
    "Satara": (17.6805, 73.9926, "West India"),
    "Bijapur": (16.8302, 75.7100, "South India"),
    "Rampur": (28.8154, 79.0270, "North India"),
    "Shimoga": (13.9299, 75.5681, "South India"),
    "Chandrapur": (19.9615, 79.2961, "West India"),
    "Junagadh": (21.5222, 70.4579, "West India"),
    "Thrissur": (10.5276, 76.2144, "South India"),
    "Alwar": (27.5530, 76.6346, "North India"),
    "Bardhaman": (23.2324, 87.8615, "East India"),
    "Kulti": (23.7344, 86.8524, "East India"),
    "Nizamabad": (18.6705, 78.0966, "South India"),
    "Parbhani": (19.2644, 76.7656, "West India"),
    "Tumkur": (13.3392, 77.1016, "South India"),
    "Khammam": (17.2473, 80.1514, "South India"),
    "Uzhavarkarai": (11.9547, 79.7915, "South India"),
    "Bihar Sharif": (25.1982, 85.5146, "East India"),
    "Panipat": (29.3909, 76.9635, "North India"),
    "Darbhanga": (26.1542, 85.8918, "East India"),
    "Bally": (22.6288, 88.3444, "East India"),
    "Aizawl": (23.7271, 92.7176, "Northeast India"),
    "Dewas": (22.9676, 76.0534, "Central India"),
    "Ichalkaranji": (16.7027, 74.4566, "West India"),
    "Karnal": (29.6857, 76.9905, "North India"),
    "Bathinda": (30.2110, 74.9455, "North India"),
    "Jalna": (19.8297, 75.8800, "West India"),
    "Eluru": (16.7107, 81.1031, "South India"),
    "Barasat": (22.7214, 88.4804, "East India"),
    "Kirari Suleman Nagar": (28.6946, 77.0673, "North India"),
    "Purnia": (25.7771, 87.4753, "East India"),
    "Satna": (24.5828, 80.8292, "Central India"),
    "Mau": (25.9385, 83.5658, "North India"),
    "Sonipat": (28.9880, 77.0210, "North India"),
    "Farrukhabad": (27.3820, 79.5855, "North India"),
    "Sagar": (23.8388, 78.7378, "Central India"),
    "Durg": (21.1904, 81.2849, "Central India"),
    "Imphal": (24.8170, 93.9368, "Northeast India"),
    "Ratlam": (23.3315, 75.0367, "Central India"),
    "Hapur": (28.7306, 77.7759, "North India"),
    "Anantapur": (14.6819, 77.6006, "South India"),
    "Arrah": (25.5604, 84.6603, "East India"),
    "Karimnagar": (18.4386, 79.1288, "South India"),
    "Etawah": (26.7725, 79.0287, "North India"),
    "Ambernath": (19.2081, 73.1873, "West India"),
    "North Dumdum": (22.6457, 88.4173, "East India"),
    "Bharatpur": (27.2152, 77.4932, "North India"),
    "Begusarai": (25.4184, 86.1273, "East India"),
    "Gandhinagar": (23.2156, 72.6369, "West India"),
    "Baranagar": (22.6415, 88.3704, "East India"),
    "Tiruvottiyur": (13.1610, 80.3015, "South India"),
    "Puducherry": (11.9416, 79.8083, "South India"),
    "Sikar": (27.6094, 75.1398, "North India"),
    "Thoothukudi": (8.7642, 78.1348, "South India"),
    "Rewa": (24.5367, 81.3039, "Central India"),
    "Mirzapur": (25.1481, 82.5694, "North India"),
    "Raichur": (16.2076, 77.3614, "South India"),
    "Pali": (25.7711, 73.3234, "North India"),
    "Ramagundam": (18.7610, 79.4795, "South India"),
    "Silchar": (24.8333, 92.7789, "Northeast India"),
    "Haridwar": (29.9457, 78.1642, "North India"),
    "Vijayanagaram": (18.1132, 83.3977, "South India"),
    "Tenali": (16.2396, 80.6433, "South India"),
    "Nagercoil": (8.1833, 77.4119, "South India"),
    "Sri Ganganagar": (29.9038, 73.8772, "North India"),
    "Karawal Nagar": (28.7303, 77.2721, "North India"),
    "Mango": (22.8252, 86.2081, "East India"),
    "Thanjavur": (10.7870, 79.1378, "South India"),
    "Bulandshahr": (28.4069, 77.8498, "North India"),
    "Uluberia": (22.4735, 88.1065, "East India"),
    "Katni": (23.8320, 80.3980, "Central India"),
    "Sambhal": (28.5833, 78.5667, "North India"),
    "Singrauli": (24.1979, 82.6631, "Central India"),
    "Nadiad": (22.6916, 72.8633, "West India"),
    "Secunderabad": (17.4399, 78.4983, "South India"),
    "Naihati": (22.8953, 88.4239, "East India"),
    "Yamunanagar": (30.1290, 77.2674, "North India"),
    "Bidhannagar": (22.5804, 88.4098, "East India"),
    "Pallavaram": (12.9675, 80.1491, "South India"),
    "Bidar": (17.9104, 77.5199, "South India"),
    "Munger": (25.3712, 86.4738, "East India"),
    "Panchkula": (30.6942, 76.8606, "North India"),
    "Burhanpur": (21.3105, 76.2335, "Central India"),
    "Kharagpur": (22.3302, 87.3237, "East India"),
    "Dindigul": (10.3673, 77.9803, "South India"),
    "Gandhidham": (23.0763, 70.1336, "West India"),
    "Hospet": (15.2689, 76.3909, "South India"),
    "Nangloi Jat": (28.6833, 77.0667, "North India"),
    "Malda": (25.0108, 88.1411, "East India"),
    "Ongole": (15.5057, 80.0499, "South India"),
    "Deoghar": (24.4842, 86.6970, "East India"),
    "Chapra": (25.7796, 84.7499, "East India"),
    "Haldia": (22.0257, 88.0583, "East India"),
    "Khandwa": (21.8315, 76.3533, "Central India"),
    "Nandyal": (15.4788, 78.4815, "South India"),
    "Morena": (26.4950, 78.0011, "Central India"),
    "Amroha": (28.9044, 78.4674, "North India"),
    "Anand": (22.5645, 72.9289, "West India"),
    "Bhind": (26.5645, 78.7885, "Central India"),
    "Bhalswa Jahangir Pur": (28.7354, 77.1638, "North India"),
    "Madhyamgram": (22.6983, 88.4557, "East India"),
    "Bhiwani": (28.7989, 76.1302, "North India"),
    "Berhampore": (24.0988, 88.2679, "East India"),
    "Ambala": (30.3782, 76.7767, "North India"),
    "Morbi": (22.8120, 70.8320, "West India"),
    "Fatehpur": (25.9288, 80.8122, "North India"),
    "Raebareli": (26.2239, 81.2403, "North India"),
    "Khora": (28.6258, 77.3323, "North India"),
    "Chittoor": (13.2172, 79.1003, "South India"),
    "Bhusawal": (21.0455, 75.8011, "West India"),
    "Orai": (25.9898, 79.4673, "North India"),
    "Bahraich": (27.5750, 81.5956, "North India"),
    "Vellore": (12.9165, 79.1325, "South India"),
    "Mahesana": (23.5880, 72.3693, "West India"),
    "Raiganj": (25.6171, 88.1189, "East India"),
    "Sirsa": (29.5332, 75.0177, "North India"),
    "Danapur": (25.6322, 85.0487, "East India"),
    "Serampore": (22.7500, 88.3400, "East India"),
    "Sultan Pur Majra": (28.6981, 77.0689, "North India"),
    "Guna": (24.6469, 77.3168, "Central India"),
    "Jaunpur": (25.7464, 82.6837, "North India"),
    "Panvel": (18.9894, 73.1175, "West India"),
    "Shivpuri": (25.4326, 77.6534, "Central India"),
    "Surendranagar Dudhrej": (22.7284, 71.6371, "West India"),
    "Unnao": (26.5414, 80.4900, "North India"),
    "Chinsurah": (22.8850, 88.3970, "East India"),
    "Alappuzha": (9.4981, 76.3388, "South India"),
    "Kottayam": (10.5947, 76.5160, "South India"),
    "Machilipatnam": (16.1783, 81.1325, "South India"),
    "Shimla": (31.1048, 77.1734, "North India"),
    "Adoni": (15.6322, 77.2728, "South India"),
    "Udupi": (13.3409, 74.7421, "South India"),
    "Katihar": (25.5414, 87.5670, "East India"),
    "Proddatur": (14.7309, 78.5565, "South India"),
    "Mahbubnagar": (16.7456, 78.0034, "South India"),
    "Saharsa": (25.8776, 86.5925, "East India"),
    "Dibrugarh": (27.4728, 94.9120, "Northeast India"),
    "Jorhat": (26.7509, 94.2037, "Northeast India"),
    "Hazaribagh": (23.9925, 85.3637, "East India"),
    "Hindupur": (13.8282, 77.4921, "South India"),
    "Nagaon": (26.3486, 92.6841, "Northeast India"),
    "Sasaram": (24.9490, 84.0314, "East India"),
    "Hajipur": (25.6858, 85.2078, "East India"),
    "Giridih": (24.1905, 86.3060, "East India"),
    "Bhimavaram": (16.5449, 81.5212, "South India"),
    "Kumbakonam": (10.9601, 79.3845, "South India"),
    "Bongaigaon": (26.4795, 90.5562, "Northeast India"),
    "Dehri": (24.9176, 84.1853, "East India"),
    "Madanapalle": (13.5510, 78.5028, "South India"),
    "Siwan": (26.2201, 84.3567, "East India"),
    "Bettiah": (26.8049, 84.5020, "East India"),
    "Ramgarh": (23.6338, 85.5186, "East India"),
    "Tinsukia": (27.4912, 95.3468, "Northeast India"),
    "Guntakal": (15.1666, 77.3789, "South India"),
    "Srikakulam": (18.2949, 83.8938, "South India"),
    "Motihari": (26.6436, 84.9080, "East India"),
    "Dharmavaram": (14.4131, 77.7126, "South India"),
    "Medininagar": (24.0326, 84.0734, "East India"),
    "Gudivada": (16.4326, 80.9934, "South India"),
    "Phagwara": (31.2240, 75.7708, "North India"),
    "Pudukkottai": (10.3797, 78.8205, "South India"),
    "Hosur": (12.7409, 77.8253, "South India"),
    "Narasaraopet": (16.2360, 80.0504, "South India"),
    "Suryapet": (17.1439, 79.6239, "South India"),
    "Miryalaguda": (16.8744, 79.5704, "South India"),
    "Tadipatri": (14.9142, 78.0069, "South India"),
    "Karaikudi": (10.0735, 78.7732, "South India"),
    "Amalapuram": (16.5770, 82.0039, "South India"),
    "Jagdalpur": (19.0740, 82.0298, "Central India"),
    "Neyveli": (11.5985, 79.4862, "South India"),
    "Chilakaluripet": (16.0890, 80.1670, "South India"),
    "Port Blair": (11.6234, 92.7265, "South India"),
}

def nlp_extract_intelligence(title: str, description: str) -> dict:
    text = f"{title} {description}".lower()
    
    # Defaults
    result = {
        "signal_type": SignalType.MEDIA,
        "severity": 0.1,
        "entities": [],
        "concepts": set(),
        "domain": "general",
        "region": "Unknown",
        "lat": 0.0,
        "lon": 0.0
    }
    
    # 1. Severity extraction — news is inherently noteworthy, minimum 0.3
    catastrophic_words = ['catastrophic', 'devastating', 'deadly', 'fatal', 'death', 'killed', 'disaster', 'massacre', 'casualties', 'victims']
    major_words = ['major', 'severe', 'critical', 'emergency', 'massive', 'destruction', 'destroyed', 'collapsed', 'derailed']
    significant_words = ['significant', 'serious', 'warning', 'heavy', 'danger', 'injured', 'trapped', 'rescue', 'alert', 'damage']
    moderate_words = ['moderate', 'impact', 'disruption', 'affected', 'hit', 'struck']
    minor_words = ['minor', 'slight', 'small']
    
    if any(w in text for w in catastrophic_words):
        result["severity"] = 0.95
    elif any(w in text for w in major_words):
        result["severity"] = 0.80
    elif any(w in text for w in significant_words):
        result["severity"] = 0.60
    elif any(w in text for w in moderate_words):
        result["severity"] = 0.45
    elif any(w in text for w in minor_words):
        result["severity"] = 0.35
    else:
        result["severity"] = 0.30  # baseline for any news article
        
    # 2. Extract Entities, Region, Lat, Lon
    found_locations = []
    for loc, (lat, lon, region) in INDIA_LOCATIONS.items():
        if loc.lower() in text:
            found_locations.append((loc, lat, lon, region))
            result["entities"].append(loc)
            
    if found_locations:
        # Just use the first matched location for coordinates and region
        loc_name, lat, lon, region = found_locations[0]
        result["lat"] = lat
        result["lon"] = lon
        result["region"] = region
    else:
        # Default to center of India if no location found
        result["lat"] = 22.5
        result["lon"] = 82.5
        result["region"] = "Central India"
        
    # 3. Concepts, Domain, Signal Type
    disaster_keywords = ['earthquake', 'flood', 'cyclone', 'landslide', 'storm', 'tsunami', 'tremor', 'quake']
    weather_keywords = ['rain', 'rainfall', 'heatwave', 'cold wave', 'thunderstorm', 'cloudburst', 'monsoon']
    health_keywords = ['disease', 'outbreak', 'virus', 'pandemic', 'hospital', 'fever', 'dengue', 'malaria', 'covid']
    infra_keywords = ['bridge collapse', 'power outage', 'derailment', 'building collapse', 'road', 'highway', 'dam', 'blackout']
    security_keywords = ['terror', 'bomb', 'explosion', 'protest', 'riots', 'attack', 'encounter', 'naxal', 'militant']
    environment_keywords = ['pollution', 'smog', 'drought', 'aqi', 'toxic', 'oil spill', 'forest fire', 'wildfire']
    transport_keywords = ['train accident', 'bus accident', 'road accident', 'traffic', 'crash', 'collision', 'pile up']
    industrial_keywords = ['fire', 'factory fire', 'industrial', 'gas leak', 'chemical', 'blaze', 'inferno']
    
    if any(w in text for w in disaster_keywords):
        result["domain"] = "disaster"
        result["signal_type"] = SignalType.SEISMIC if any(w in text for w in ['earthquake', 'tremor', 'quake', 'seismic']) else SignalType.WEATHER
        result["concepts"].update([w for w in disaster_keywords if w in text])
    elif any(w in text for w in weather_keywords):
        result["domain"] = "weather"
        result["signal_type"] = SignalType.WEATHER
        result["concepts"].update([w for w in weather_keywords if w in text])
    elif any(w in text for w in health_keywords):
        result["domain"] = "health"
        result["signal_type"] = SignalType.HEALTH
        result["concepts"].update([w for w in health_keywords if w in text])
    elif any(w in text for w in transport_keywords):
        result["domain"] = "transport"
        result["signal_type"] = SignalType.TRANSPORT
        result["concepts"].update([w for w in transport_keywords if w in text])
    elif any(w in text for w in industrial_keywords):
        result["domain"] = "industrial"
        result["signal_type"] = SignalType.INDUSTRIAL
        result["concepts"].update([w for w in industrial_keywords if w in text])
    elif any(w in text for w in infra_keywords):
        result["domain"] = "infrastructure"
        result["signal_type"] = SignalType.INFRASTRUCTURE
        result["concepts"].update([w for w in infra_keywords if w in text])
    elif any(w in text for w in security_keywords):
        result["domain"] = "security"
        result["signal_type"] = SignalType.PUBLIC_REPORT
        result["concepts"].update([w for w in security_keywords if w in text])
    elif any(w in text for w in environment_keywords):
        result["domain"] = "environment"
        result["signal_type"] = SignalType.ENVIRONMENTAL
        result["concepts"].update([w for w in environment_keywords if w in text])
        
    result["concepts"] = list(result["concepts"])
    return result

def _parse_date(date_str: str) -> datetime:
    try:
        date_str = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(date_str)
    except Exception:
        return datetime.now(timezone.utc)

def fetch_newsapi_signals() -> list[Signal]:
    signals = []
    try:
        query = 'India disaster OR earthquake OR flood OR cyclone OR fire OR landslide OR storm OR accident OR emergency OR crisis OR infrastructure OR power outage OR bridge collapse OR drought OR heatwave OR pollution OR terror OR bomb OR explosion OR protest OR riots'
        url_everything = f"https://newsapi.org/v2/everything?q={urllib.parse.quote(query)}&language=en&sortBy=publishedAt&pageSize=50&apiKey={NEWSAPI_KEY}"
        
        req = urllib.request.Request(url_everything, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            articles = data.get('articles', [])
            
        url_headlines = f"https://newsapi.org/v2/top-headlines?country=in&category=general&pageSize=50&apiKey={NEWSAPI_KEY}"
        req_h = urllib.request.Request(url_headlines, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_h, timeout=10) as response_h:
            data_h = json.loads(response_h.read().decode())
            articles.extend(data_h.get('articles', []))
            
        index = 1
        for article in articles:
            title = article.get('title') or ""
            desc = article.get('description') or ""
            if not title and not desc:
                continue
                
            nlp = nlp_extract_intelligence(title, desc)
            
            sig = Signal(
                id=f"SIG-NEWS-NAPI-{index:04d}",
                source=SignalSource(
                    id="newsapi-org",
                    name="NewsAPI",
                    category=SourceCategory.MEDIA,
                    verification=VerificationStatus.REPUTABLE
                ),
                type=nlp["signal_type"],
                title=title[:120],
                description=desc[:500],
                location=SignalLocation(
                    latitude=nlp["lat"],
                    longitude=nlp["lon"],
                    region=nlp["region"]
                ),
                timestamp=_parse_date(article.get('publishedAt', '')),
                entities=nlp["entities"],
                severity=nlp["severity"],
                provenance=ProvenanceLabel.OBSERVED,
                confidence=0.8,
                language='en',
                domain=nlp["domain"],
                tags=list(nlp["concepts"]) if isinstance(nlp["concepts"], set) else nlp["concepts"]
            )
            signals.append(sig)
            index += 1
            
    except Exception as e:
        print(f"Error fetching from NewsAPI: {e}")
        
    return signals

def fetch_worldnews_signals() -> list[Signal]:
    signals = []
    try:
        url = f"https://api.worldnewsapi.com/search-news?text=India&source-countries=in&language=en&number=50&sort=publish-time&sort-direction=DESC&api-key={WORLDNEWSAPI_KEY}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            articles = data.get('news', [])
            
        index = 1
        for article in articles:
            title = article.get('title') or ""
            desc = article.get('text') or ""
            if not title and not desc:
                continue
                
            nlp = nlp_extract_intelligence(title, desc)
            
            sig = Signal(
                id=f"SIG-NEWS-WNAPI-{index:04d}",
                source=SignalSource(
                    id="worldnewsapi",
                    name="WorldNewsAPI",
                    category=SourceCategory.MEDIA,
                    verification=VerificationStatus.REPUTABLE
                ),
                type=nlp["signal_type"],
                title=title[:120],
                description=desc[:500],
                location=SignalLocation(
                    latitude=nlp["lat"],
                    longitude=nlp["lon"],
                    region=nlp["region"]
                ),
                timestamp=_parse_date(article.get('publish_date', '')),
                entities=nlp["entities"],
                severity=nlp["severity"],
                provenance=ProvenanceLabel.OBSERVED,
                confidence=0.8,
                language='en',
                domain=nlp["domain"],
                tags=list(nlp["concepts"]) if isinstance(nlp["concepts"], set) else nlp["concepts"]
            )
            signals.append(sig)
            index += 1
            
    except Exception as e:
        print(f"Error fetching from WorldNewsAPI: {e}")
        
    return signals

def fetch_all_news_signals() -> list[Signal]:
    all_signals = fetch_newsapi_signals() + fetch_worldnews_signals()
    
    seen_titles = set()
    deduped = []
    for sig in all_signals:
        title_lower = sig.title.lower().strip()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            deduped.append(sig)
            
    return deduped
