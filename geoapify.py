import os
import requests
from typing import List, Dict, Optional

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

def search_places(
    categories: str = "catering.restaurant",
    filter_circle: Optional[str] = None,
    filter_rect: Optional[str] = None,
    bias: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    lang: str = "en"
) -> List[Dict]:
    """
    Search for places using Geoapify Places API.
    
    Args:
        categories: Comma-separated list of categories.
        filter_circle: "lat,lon,radius_meters"
        filter_rect: "lon1,lat1,lon2,lat2"
        bias: "proximity:lon,lat" or "countrycode:iso_code"
        limit: Max results (default 20).
        offset: Pagination offset.
        lang: Language code.
        
    Returns:
        List of place features.
    """
    if not GEOAPIFY_API_KEY:
        raise ValueError("GEOAPIFY_API_KEY not found in environment variables.")

    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": categories,
        "apiKey": GEOAPIFY_API_KEY,
        "limit": limit,
        "offset": offset,
        "lang": lang
    }
    
    # Prioritize circle filter if both are present
    if filter_circle:
        # App/Agent sends "lat,lon,radius" OR "lon,lat,radius"
        # Geoapify expects "lon,lat,radius"
        clean_filter = filter_circle.replace("circle:", "").strip()
        parts = clean_filter.split(',')
        if len(parts) == 3:
            p1, p2, radius = parts
            try:
                v1 = float(p1.strip())
                v2 = float(p2.strip())
                
                # Heuristic for Bangalore/India: Lon (approx 77) > Lat (approx 12)
                # We want output to be Lon, Lat (Big, Small)
                if v1 < v2: 
                    # Input is Lat, Lon (Small, Big) -> SWAP
                    params["filter"] = f"circle:{v2},{v1},{radius.strip()}"
                    print(f"🔄 Smart Swap: {v1},{v2} -> {v2},{v1} (Lat,Lon -> Lon,Lat)")
                else:
                    # Input is Lon, Lat (Big, Small) -> KEEP
                    params["filter"] = f"circle:{v1},{v2},{radius.strip()}"
                    print(f"✅ Kept coordinates: {v1},{v2} (Already Lon,Lat)")
            except ValueError:
                # Fallback if parsing fails
                params["filter"] = f"circle:{filter_circle}"
        else:
            params["filter"] = f"circle:{filter_circle}"
    elif filter_rect:
        params["filter"] = f"rect:{filter_rect}"
        
    if bias:
        # Handle bias parameter robustness
        # Geoapify expects proximity:lon,lat
        clean_bias = bias.replace("proximity:", "").strip()
        clean_bias = clean_bias.replace("countrycode:IN", "").strip() # Remove countrycode if mixed in
        
        parts = clean_bias.split(',')
        if len(parts) == 2:
            try:
                v1 = float(parts[0].strip())
                v2 = float(parts[1].strip())
                
                # Same heuristic: We want Lon, Lat (Big, Small)
                if v1 < v2:
                     params["bias"] = f"proximity:{v2},{v1}"
                     print(f"🔄 Smart Bias Swap: {v1},{v2} -> {v2},{v1}")
                else:
                     params["bias"] = f"proximity:{v1},{v2}"
                     print(f"✅ Kept Bias: {v1},{v2}")
            except ValueError:
                 params["bias"] = bias
        else:
            params["bias"] = bias

    print(f"🌍 Calling Geoapify API: {url}")
    print(f"   Params: {params}")

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        features = data.get("features", [])
        print(f"✅ Geoapify Response: Found {len(features)} places.")
        return features
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Geoapify Places API: {e}")
        return []
