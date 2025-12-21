from typing import List, Dict, Any
import datetime
import urllib.parse
from fpdf import FPDF

def parse_time_to_ics_format(time_str: str) -> str:
    """
    Convert '10:00 AM' to 'YYYYMMDDTHHMMSS' format for ICS.
    Assumes the event is for tomorrow for simplicity, or today if not specified.
    """
    try:
        # Parse the time string (e.g., "10:00 AM")
        dt = datetime.datetime.strptime(time_str, "%I:%M %p")
        
        # Set date to tomorrow to ensure it's in the future
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        dt = dt.replace(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
        
        return dt.strftime("%Y%m%dT%H%M%S")
    except ValueError:
        return ""

import re

def parse_markdown_itinerary(markdown_text: str) -> tuple[List[Dict[str, str]], str]:
    """
    Parse the markdown itinerary to extract structured data and the summary.
    Strictly looks for '### Name' headers to identify items.
    Returns: (items, summary_text)
    """
    items = []
    current_item = {}
    summary_text = ""
    capturing_summary = False
    
    lines = markdown_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for Summary Section
        if line.startswith('### Summary') or line.startswith('📝 Summary') or line.strip() == 'Summary':
            capturing_summary = True
            # Flush the last item if it exists
            if current_item.get('name'):
                items.append(current_item)
                current_item = {}
            continue
            
        if capturing_summary:
            summary_text += line + " "
            continue
            
        # Check for Name (Strict Header or Bullet Point)
        # Matches: ### Name, * **Name**, 1. **Name**
        name_match = re.search(r'^###\s+(.*)|^\*\s+\*\*(.*?)\*\*|^\d+\.\s+\*\*(.*?)\*\*', line)
        if name_match:
            # Extract name from whichever group matched
            potential_name = next((g for g in name_match.groups() if g), "").strip()
            
            # Ignore generic headers or summary sections
            if potential_name.lower() in ['itinerary', 'mini-itinerary', 'shopping', 'restaurants', 'activities'] or 'summary' in potential_name.lower():
                continue
                
            # If we have a previous item with at least a name, save it
            if current_item.get('name'):
                items.append(current_item)
                current_item = {}
            
            current_item['name'] = potential_name
            continue
            
        # Check for Address
        # Matches: *Address*, Address: ...
        address_match = re.search(r'^\*(.*?)\*|^Address:\s*(.*)', line, re.IGNORECASE)
        if address_match:
             extracted_addr = ""
             for group in address_match.groups():
                if group:
                    extracted_addr = group.strip()
                    break
             
             # Clean up "Address:" prefix if captured inside italics
             extracted_addr = re.sub(r'^Address:\s*', '', extracted_addr, flags=re.IGNORECASE).strip()
             
             if extracted_addr and not current_item.get('address'):
                 current_item['address'] = extracted_addr
                 continue

        # Check for Time
        # Matches: 🕒 ..., Time: ..., 10:00 AM - ...
        time_match = re.search(r'(?:🕒|Time:)\s*(.*)|(\d{1,2}:\d{2}\s*[AP]M\s*-\s*\d{1,2}:\d{2}\s*[AP]M)', line, re.IGNORECASE)
        if time_match:
            time_str = ""
            for group in time_match.groups():
                if group:
                    time_str = group.strip()
                    break
            
            if time_str and not current_item.get('start_time'):
                if '-' in time_str:
                    parts = time_str.split('-')
                    current_item['start_time'] = parts[0].strip()
                    current_item['end_time'] = parts[1].strip()
                else:
                    current_item['start_time'] = time_str
                    current_item['end_time'] = ""
                continue
            
        # Description (Anything else, if we have a name)
        if current_item.get('name'):
            # Avoid appending if it looks like a header or separator
            if line.startswith('---'):
                continue
                
            current_desc = current_item.get('description', "")
            current_item['description'] = (current_desc + " " + line).strip()
            
    # Append the last item (if we didn't already flush it at summary)
    if current_item.get('name'):
        items.append(current_item)
            
    return items, summary_text.strip()

def create_ics_file(itinerary_items: List[Any]) -> str:
    """
    Create an ICS file content for the itinerary.
    Expects a list of ItineraryItem objects or dictionaries.
    """
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Local Discovery Agent//EN\n"
    
    for item in itinerary_items:
        # Handle both Pydantic models and dictionaries
        if hasattr(item, 'name'):
            name = item.name
            address = item.address
            description = item.description
            start_str = item.start_time
            end_str = item.end_time
        else:
            name = item.get("name", "Event")
            address = item.get("address", "")
            description = item.get("description", "")
            start_str = item.get("start_time", "")
            end_str = item.get("end_time", "")
            
        start_time = parse_time_to_ics_format(start_str)
        end_time = parse_time_to_ics_format(end_str)
        
        if start_time and end_time:
            ics_content += "BEGIN:VEVENT\n"
            ics_content += f"SUMMARY:{name}\n"
            ics_content += f"DTSTART:{start_time}\n"
            ics_content += f"DTEND:{end_time}\n"
            ics_content += f"DESCRIPTION:{description}\n"
            ics_content += f"LOCATION:{address}\n"
            ics_content += "END:VEVENT\n"
            
    ics_content += "END:VCALENDAR"
    return ics_content

def create_pdf_file(itinerary_items: List[Any], summary: str) -> bytes:
    """
    Create a PDF file for the itinerary.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Helper to sanitize text for FPDF (Latin-1 only)
    def sanitize(text):
        return text.encode('latin-1', 'replace').decode('latin-1')

    # Title
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, txt=sanitize("My Itinerary"), ln=True, align='C')
    pdf.ln(10)
    
    # Items
    for i, item in enumerate(itinerary_items, 1):
        if hasattr(item, 'name'):
            name = item.name
            address = item.address
            description = item.description
            time_slot = f"{item.start_time} - {item.end_time}"
        else:
            name = item.get("name", "Unknown")
            address = item.get("address", "")
            description = item.get("description", "")
            time_slot = f"{item.get('start_time', '')} - {item.get('end_time', '')}"
            
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, txt=sanitize(f"{i}. {name}"), ln=True)
        
        pdf.set_font("Arial", style="I", size=10)
        pdf.cell(0, 8, txt=sanitize(f"Time: {time_slot}"), ln=True)
        pdf.cell(0, 8, txt=sanitize(f"Address: {address}"), ln=True)
        
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 8, txt=sanitize(description))
        pdf.ln(5)

    # Summary (at the end)
    if summary:
        pdf.ln(10)
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(200, 10, txt=sanitize("Summary"), ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=sanitize(summary))
        pdf.ln(10)
        
    return pdf.output(dest='S').encode('latin-1')
