import os
import requests
import time
import uuid
from typing import Dict, Optional, List

OLA_MAPS_API_KEY = os.getenv("OLA_MAPS_API_KEY")

def get_access_token():
    return None

def get_place_details(lat: float, lon: float) -> Dict:
    """
    Get place details using Ola Maps Reverse Geocoding or Places API.
    """
    if not OLA_MAPS_API_KEY:
        raise ValueError("OLA_MAPS_API_KEY not found in environment variables.")
        
    url = "https://api.olamaps.io/places/v1/reverse-geocode"
    params = {
        "latlng": f"{lat},{lon}",
        "api_key": OLA_MAPS_API_KEY
    }
    
    print(f"🗺️ Calling Ola Maps Reverse Geocode: {lat}, {lon}")

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            print("✅ Ola Maps Response: Details found.")
            return data["results"][0]
        print("⚠️ Ola Maps Response: No details found.")
        return {}
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Ola Maps Reverse Geocode: {e}")
        return {}

def search_places(query: str, lat: float, lon: float) -> List[Dict]:
    """
    Searches for places using Ola Maps API (Autocomplete) and fetches details.
    """
    if not OLA_MAPS_API_KEY:
        raise ValueError("OLA_MAPS_API_KEY not found in environment variables.")

    query_lower = query.lower()
    
    # --- Hardcoded Directory Logic ---
    DIRECTORY_PLACES = {
        "museum": [
            {"name": "Visvesvaraya Industrial and Technological Museum", "lat": 12.9753, "lon": 77.5963, "address": "Kasturba Rd, Ambedkar Veedhi, Bengaluru, Karnataka 560001"},
            {"name": "Government Museum", "lat": 12.9767, "lon": 77.5958, "address": "Kasturba Rd, Ambedkar Veedhi, Bengaluru, Karnataka 560001"},
            {"name": "HAL Heritage Centre and Aerospace Museum", "lat": 12.9532, "lon": 77.6816, "address": "HAL Old Airport Rd, Marathahalli, Bengaluru, Karnataka 560037"},
            {"name": "Jawaharlal Nehru Planetarium", "lat": 12.9849, "lon": 77.5896, "address": "Sri T, Sankey Rd, High Grounds, Bengaluru, Karnataka 560001"},
            {"name": "Indian Music Experience Museum", "lat": 12.8914, "lon": 77.5861, "address": "JP Nagar 7th Phase, Bengaluru, Karnataka 560078"},
            {"name": "Brain Museum", "lat": 12.9344, "lon": 77.5933, "address": "NIMHANS, Hosur Road, Bengaluru, Karnataka 560029"}
        ],
        "zoo": [
            {"name": "Bannerghatta Biological Park", "lat": 12.8009, "lon": 77.5777, "address": "Bannerghatta Rd, Bengaluru, Karnataka 560083"}
        ]
    }
    
    # Check if query matches a directory category
    directory_category = None
    if "museum" in query_lower:
        directory_category = "museum"
    elif "zoo" in query_lower:
        directory_category = "zoo"
        
    if directory_category:
        print(f"📂 Using Hardcoded Directory for: '{directory_category}'")
        results = []
        from math import radians, sin, cos, sqrt, atan2
        R = 6371  # Earth radius in km
        
        for place in DIRECTORY_PLACES[directory_category]:
            # Calculate distance
            place_lat = place["lat"]
            place_lon = place["lon"]
            dlat = radians(place_lat - lat)
            dlon = radians(place_lon - lon)
            a = sin(dlat / 2)**2 + cos(radians(lat)) * cos(radians(place_lat)) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            distance = R * c
            
            results.append({
                "name": place["name"],
                "address": place["address"],
                "lat": place_lat,
                "lon": place_lon,
                "place_id": f"dir_{place['name'].replace(' ', '_')}",
                "rating": "4.5", # Placeholder rating
                "distance": f"{distance:.1f} km",
                "status": "ACTIVE"
            })
            
        # Sort by distance
        results.sort(key=lambda x: float(x["distance"].split()[0]))
        return results

    # --- Standard Ola Maps Search ---
    refined_query = query
    
    refinements = {
        "parks": "Park",
        "park": "Park",
        "brewery": "Microbrewery",
        "gym": "Gymnasium Fitness Center",
        "library": "Public Library",
        "arcade": "Shopping Mall",
        "shopping": "Shopping Mall",
        "theaters": "Cinema",
        "movies": "Cinema"
    }
    
    for key, value in refinements.items():
        if key in query_lower and value.lower() not in query_lower:
            import re
            refined_query = re.sub(r'\b' + re.escape(key) + r'\b', value, refined_query, flags=re.IGNORECASE)
            print(f"🔄 Refined Query: '{query}' -> '{refined_query}'")
            break

    url = "https://api.olamaps.io/places/v1/autocomplete"
    
    params = {
        "input": refined_query,
        "location": f"{lat},{lon}",
        "api_key": OLA_MAPS_API_KEY
    }

    print(f"🗺️ Calling Ola Maps Search (Autocomplete): {refined_query} near {lat},{lon}")

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        predictions = data.get("predictions", [])
        print(f"✅ Ola Maps Response: Found {len(predictions)} places.")
        
        detailed_results = []
        details_url = "https://api.olamaps.io/places/v1/details"
        
        sparse_categories = ["museum", "zoo", "amusement park", "stadium", "airport", "theme park"]
        is_sparse = any(cat in query_lower for cat in sparse_categories)
        max_distance = 30.0 if is_sparse else 7.0
        
        print(f"📏 Max Distance set to: {max_distance} km (Sparse: {is_sparse})")
        
        directory_names = []
        for cat_list in DIRECTORY_PLACES.values():
            for item in cat_list:
                directory_names.append(item["name"].lower())

        # Check up to 50 predictions to find 3 good ones
        for p in predictions[:50]:
            if len(detailed_results) >= 3:
                break
                
            place_id = p.get("place_id")
            if not place_id:
                continue
                
            try:
                # Fetch details
                d_params = {"place_id": place_id, "api_key": OLA_MAPS_API_KEY}
                d_resp = requests.get(details_url, params=d_params)
                if d_resp.status_code == 200:
                    d_data = d_resp.json().get("result", {})
                    
                    place_name = (d_data.get("name") or p.get("description") or "").lower()
                    
                    # --- Directory Exclusion Check ---
                    is_in_directory = False
                    for dir_name in directory_names:
                        if dir_name in place_name or place_name in dir_name:
                             is_in_directory = True
                             break
                        
                    if is_in_directory:
                        print(f"⚠️ Skipping {d_data.get('name')} (Exists in Directory)")
                        continue

                    # --- Irrelevant Keywords Filtering ---
                    irrelevant_keywords = [
                        "parking", "metro", "ward", "road", "junction", "bus stop", 
                        "railway", "station", "atm", "toll", "post office"
                    ]
                    
                    is_activity_search = any(k in query_lower for k in ["park", "activity", "activities", "tourist", "sightseeing", "attraction", "place", "shopping", "mall", "market"])
                    is_theater_search = any(k in query_lower for k in ["theater", "theatre", "movie", "cinema"])
                    
                    if is_activity_search or is_theater_search:
                        irrelevant_keywords.extend([
                            "hotel", "inn", "residency", "packers", "movers", "travels", "lodge", 
                            "school", "college", "university", "academy", "class", "openhouse",
                            "developers", "enclave", "apartment", "building", "tower", "mall", 
                            "shopping", "store", "outlet", "estate", 
                            "tech park", "industrial", "campus", "office", "corporate", "sez", 
                            "zone", "business park", "export",
                            "infra", "infrastructure", "construction", "pvt ltd", "private limited", "limited",
                            "shipping", "courier", "online", "logistics", "cargo", "freight", "import", "inc", "builders", "contractors",
                            "event", "flingg", "decor", "planter", "cabinet", "furniture", "nursery"
                        ])
                        
                        if "shopping" in query_lower or "mall" in query_lower or "market" in query_lower:
                             irrelevant_keywords.extend(["cafe", "coffee", "tea", "restaurant", "food", "dining"])
                             for allowed in ["mall", "shopping", "store", "outlet"]:
                                 if allowed in irrelevant_keywords:
                                     irrelevant_keywords.remove(allowed)
                        
                    if is_theater_search:
                        irrelevant_keywords.extend(["maac", "animation", "education", "coaching"])
                        
                    if "brewery" in query_lower:
                        irrelevant_keywords.extend(["coffee", "cafe", "tea"])
                    if "gym" in query_lower:
                        irrelevant_keywords.extend(["school", "academy", "class"])
                        
                    # Restaurant specific exclusions
                    if "restaurant" in query_lower or "cafe" in query_lower:
                        irrelevant_keywords.extend(["tyre", "wheel", "residency", "apartment", "lodge", "pg", "paying guest"])

                    # --- Address Marker Filtering ---
                    import re
                    if re.match(r'^\d+', place_name) or "near " in place_name or "opp " in place_name or "opposite " in place_name:
                         print(f"⚠️ Skipping {d_data.get('name')} (Address marker detected)")
                         continue
                         
                    skipped = False
                    for keyword in irrelevant_keywords:
                        if keyword in place_name:
                            print(f"⚠️ Skipping {d_data.get('name')} (Match: '{keyword}')")
                            skipped = True
                            break
                    
                    # Debug print for Continental Residency
                    if "continental residency" in place_name:
                        print(f"🐞 DEBUG: Checking 'continental residency'. Keywords: {irrelevant_keywords}")
                        print(f"🐞 DEBUG: Skipped? {skipped}")

                    if skipped:
                        continue
                    
                    loc = d_data.get("geometry", {}).get("location", {})
                    
                    # --- Distance Check ---
                    try:
                        place_lat = loc.get("lat")
                        place_lon = loc.get("lng")
                        if place_lat and place_lon:
                            from math import radians, sin, cos, sqrt, atan2
                            R = 6371  # Earth radius in km
                            dlat = radians(place_lat - lat)
                            dlon = radians(place_lon - lon)
                            a = sin(dlat / 2)**2 + cos(radians(lat)) * cos(radians(place_lat)) * sin(dlon / 2)**2
                            c = 2 * atan2(sqrt(a), sqrt(1 - a))
                            distance = R * c
                            
                            if distance > max_distance:
                                print(f"⚠️ Skipping {d_data.get('name')} (Too far: {distance:.2f} km > {max_distance} km)")
                                continue
                            
                            place_distance = distance
                    except Exception as e:
                        print(f"⚠️ Error calculating distance: {e}")
                        place_distance = None

                    detailed_results.append({
                        "name": d_data.get("name") or p.get("description"),
                        "address": d_data.get("formatted_address"),
                        "lat": loc.get("lat"),
                        "lon": loc.get("lng"),
                        "place_id": place_id,
                        "rating": d_data.get("rating", "N/A"),
                        "distance": f"{place_distance:.1f} km" if place_distance else "N/A",
                        "status": "ACTIVE"
                    })
            except Exception as e:
                print(f"⚠️ Error fetching details for {place_id}: {e}")
                continue
        
        # --- Fallback for Parks ---
        if len(detailed_results) < 3 and ("park" in query_lower or "parks" in query_lower) and "garden" not in query_lower:
            print(f"⚠️ Found only {len(detailed_results)} parks. Trying fallback search for 'Garden'...")
            fallback_query = query_lower.replace("parks", "garden").replace("park", "garden")
            
            print(f"🗺️ Calling Ola Maps Search (Fallback): {fallback_query} near {lat},{lon}")
            try:
                f_params = {
                    "input": fallback_query,
                    "location": f"{lat},{lon}",
                    "api_key": OLA_MAPS_API_KEY
                }
                f_resp = requests.get(url, params=f_params)
                if f_resp.status_code == 200:
                    f_data = f_resp.json()
                    f_predictions = f_data.get("predictions", [])
                    print(f"✅ Ola Maps Fallback Response: Found {len(f_predictions)} places.")
                    
                    for p in f_predictions[:25]:
                        if len(detailed_results) >= 5:
                            break
                        
                        place_id = p.get("place_id")
                        if not place_id: continue
                        
                        # Check if already in results
                        if any(r["place_id"] == place_id for r in detailed_results):
                            continue
                            
                        try:
                            d_params = {"place_id": place_id, "api_key": OLA_MAPS_API_KEY}
                            d_resp = requests.get(details_url, params=d_params)
                            if d_resp.status_code == 200:
                                d_data = d_resp.json().get("result", {})
                                place_name = (d_data.get("name") or p.get("description") or "").lower()
                                
                                # Apply same filters
                                import re
                                if re.match(r'^\d+', place_name) or "near " in place_name or "opp " in place_name: continue
                                
                                skipped = False
                                for keyword in irrelevant_keywords:
                                    if keyword in place_name:
                                        skipped = True
                                        break
                                if skipped: continue
                                
                                loc = d_data.get("geometry", {}).get("location", {})
                                place_lat = loc.get("lat")
                                place_lon = loc.get("lng")
                                
                                place_distance = None
                                if place_lat and place_lon:
                                    from math import radians, sin, cos, sqrt, atan2
                                    R = 6371
                                    dlat = radians(place_lat - lat)
                                    dlon = radians(place_lon - lon)
                                    a = sin(dlat / 2)**2 + cos(radians(lat)) * cos(radians(place_lat)) * sin(dlon / 2)**2
                                    c = 2 * atan2(sqrt(a), sqrt(1 - a))
                                    distance = R * c
                                    if distance > max_distance: continue
                                    place_distance = distance

                                detailed_results.append({
                                    "name": d_data.get("name") or p.get("description"),
                                    "address": d_data.get("formatted_address"),
                                    "lat": loc.get("lat"),
                                    "lon": loc.get("lng"),
                                    "place_id": place_id,
                                    "rating": d_data.get("rating", "N/A"),
                                    "distance": f"{place_distance:.1f} km" if place_distance else "N/A",
                                    "status": "ACTIVE"
                                })
                        except: continue
            except: pass

        # --- Fallback for Shopping ---
        # If we found fewer than 3 results for "Shopping Mall", try searching for generic "Shopping"
        if len(detailed_results) < 3 and "shopping" in query_lower and "mall" not in query_lower:
            print(f"⚠️ Found only {len(detailed_results)} malls. Trying fallback search for 'Shopping'...")
            # We want to search for 'Shopping' specifically, so we use the original query 
            # (which likely contains 'Shopping') but we must ensure we don't refine it to 'Mall' again.
            # Since we are calling the API directly here, refinements won't apply.
            fallback_query = query
            
            print(f"🗺️ Calling Ola Maps Search (Fallback): {fallback_query} near {lat},{lon}")
            try:
                f_params = {
                    "input": fallback_query,
                    "location": f"{lat},{lon}",
                    "api_key": OLA_MAPS_API_KEY
                }
                f_resp = requests.get(url, params=f_params)
                if f_resp.status_code == 200:
                    f_data = f_resp.json()
                    f_predictions = f_data.get("predictions", [])
                    print(f"✅ Ola Maps Fallback Response: Found {len(f_predictions)} places.")
                    
                    for p in f_predictions[:25]:
                        if len(detailed_results) >= 5:
                            break
                        
                        place_id = p.get("place_id")
                        if not place_id: continue
                        
                        # Check if already in results
                        if any(r["place_id"] == place_id for r in detailed_results):
                            continue
                            
                        try:
                            d_params = {"place_id": place_id, "api_key": OLA_MAPS_API_KEY}
                            d_resp = requests.get(details_url, params=d_params)
                            if d_resp.status_code == 200:
                                d_data = d_resp.json().get("result", {})
                                place_name = (d_data.get("name") or p.get("description") or "").lower()
                                
                                # Apply same filters
                                import re
                                if re.match(r'^\d+', place_name) or "near " in place_name or "opp " in place_name: continue
                                
                                skipped = False
                                for keyword in irrelevant_keywords:
                                    if keyword in place_name:
                                        skipped = True
                                        break
                                if skipped: continue
                                
                                loc = d_data.get("geometry", {}).get("location", {})
                                place_lat = loc.get("lat")
                                place_lon = loc.get("lng")
                                
                                place_distance = None
                                if place_lat and place_lon:
                                    from math import radians, sin, cos, sqrt, atan2
                                    R = 6371
                                    dlat = radians(place_lat - lat)
                                    dlon = radians(place_lon - lon)
                                    a = sin(dlat / 2)**2 + cos(radians(lat)) * cos(radians(place_lat)) * sin(dlon / 2)**2
                                    c = 2 * atan2(sqrt(a), sqrt(1 - a))
                                    distance = R * c
                                    if distance > max_distance: continue
                                    place_distance = distance

                                detailed_results.append({
                                    "name": d_data.get("name") or p.get("description"),
                                    "address": d_data.get("formatted_address"),
                                    "lat": loc.get("lat"),
                                    "lon": loc.get("lng"),
                                    "place_id": place_id,
                                    "rating": d_data.get("rating", "N/A"),
                                    "distance": f"{place_distance:.1f} km" if place_distance else "N/A",
                                    "status": "ACTIVE"
                                })
                        except: continue
            except: pass

        return deduplicate_places(detailed_results)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Ola Maps Search: {e}")
        return []

def deduplicate_places(places: List[Dict]) -> List[Dict]:
    """
    Deduplicate places based on name similarity and substring matching.
    """
    import difflib
    
    unique_results = []
    
    for place in places:
        is_duplicate = False
        name = place["name"].lower()
        
        for existing in unique_results:
            existing_name = existing["name"].lower()
            
            if name in existing_name or existing_name in name:
                print(f"🧹 Deduplicating: '{place['name']}' merged with '{existing['name']}' (Substring)")
                is_duplicate = True
                break
            
            similarity = difflib.SequenceMatcher(None, name, existing_name).ratio()
            if similarity > 0.8:
                print(f"🧹 Deduplicating: '{place['name']}' merged with '{existing['name']}' (Similarity: {similarity:.2f})")
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_results.append(place)
            
    return unique_results
