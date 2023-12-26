import requests
import re
from datetime import datetime

def check_bremen(input_list):
    """
    Function to check appointments in Bremen using a series of HTTP requests.

    Args:
    input_list (list): List of dictionaries containing location information.

    Returns:
    results: list of available locations and the checking time
    """
    results = []
    

    for location_dict in input_list:
        print(f"DEBUG: Checking {location_dict['location']}")
        # Step 1: Get the session cookie
    
        url_get_token = location_dict["url_get_token"]
        headers = {
            'Host': 'termin.bremen.de',
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Te': 'trailers',
            'Connection': 'close'
        }
        response = requests.get(url_get_token, headers=headers)
        fetched_cookies = response.cookies

        if len(fetched_cookies) > 0:
            tvo_session_cookie = next(iter(fetched_cookies)).value
            print(f'DEBUG: Fetched Session Cookie: {tvo_session_cookie}')
        else:
            print("DEBUG: No Cookie :( ... aborting")
            continue

        # Step 2: Make the first GET request
        url_get = location_dict["url_get"]
        headers = {
            'Host': 'termin.bremen.de',
            'Cookie': f'tvo_session={tvo_session_cookie}',
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': url_get_token,
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Te': 'trailers',
            'Connection': 'close'
        }
        response = requests.get(url_get, headers=headers)

        # Process the response of the first GET request
        if response.status_code == 200:
            print("DEBUG: First GET request successful.")
        else:
            print(f"DEBUG: First GET request failed with status code: {response.status_code} ... aborting")
            continue

        # Step 3: Make the second GET request
        url_get_post = location_dict["url_get_post"]
        
        headers = {
            'Host': 'termin.bremen.de',
            'Cookie': f'tvo_session={tvo_session_cookie}',
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': url_get,
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Te': 'trailers',
            'Connection': 'close'
        }

        response = requests.get(url_get_post, headers=headers)

        # Process the response of the second GET request
        if response.status_code == 200:
            print("DEBUG: Second GET request successful.")
        else:
            print(f"DEBUG: Second GET request failed with status code: {response.status_code}")
            continue

        # Step 4: Make the POST request
        headers = {
            'Host': 'termin.bremen.de',
            'Cookie': f'tvo_session={tvo_session_cookie}',
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': url_get_post,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://termin.bremen.de',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Te': 'trailers',
            'Connection': 'close'
        }
        
        payload = location_dict["post_payload"]
        response = requests.post(url_get_post, headers=headers, data=payload)

        # Process the response of the POST request
        if response.status_code == 200:
            print("DEBUG: POST request successful.")
        else:
            print(f"DEBUG: POST request failed with status code: {response.status_code}")
            continue

        # Step 5: Make the third GET request
        url_post = 'https://termin.bremen.de/termine/suggest'
        
        headers = {
            'Host': 'termin.bremen.de',
            'Cookie': f'tvo_session={tvo_session_cookie}',
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': url_get_post,
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Te': 'trailers',
            'Connection': 'close'
        }
        
        response = requests.get(url_post, headers=headers)

        # Process the response of the third GET request
        if response.status_code == 200:
            print("DEBUG: Third GET request successful.")
            
            days = []
            
            if "Kein freier Termin verfügbar" in response.text:
                print(f"DEBUG: No free appointments for {location_dict['location']}")
                status = "not available"
            elif "Fehler aufgetreten" in response.text:
                print(f"DEBUG: Error occured when checking {location_dict['location']}")
               
                status = "error"
            elif "Bitte wählen Sie die gewünschte Uhrzeit für Ihren Termin aus" in response.text:
                print(f"DEBUG: Appointments available for {location_dict['location']}")
                status = "available"
                days = parse_days(response.text)
                # quick debug:
                if location_dict['location'] == "BürgerServiceCenter-Mitte":
                    print(response.text)
            else:
                print(f"DEBUG: Unexpected result for {location_dict['location']}")
                status = "unexpected"
            
            
            result = {
                        "location":location_dict["location"], 
                        "status": status, 
                        "datetime":datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "days": days
                    }
            
                
            results.append(result)
        else:
            print(f"DEBUG: Third GET request failed with status code: {response.status_code}")
            continue
        
    return results

def parse_days(html_content):
    # Define the regex pattern to match any day of the week followed by the date format
    regex_pattern = r"(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag), (\d{2}\.\d{2}\.\d{4})"
    
    # Find all occurrences of the pattern in the HTML text
    matches = re.findall(regex_pattern, html_content)
    
    # Create a set to store unique matches
    unique_matches = set()
    
    # Add unique matches to the set
    for match in matches:
        unique_matches.add(f"{match[0]}, {match[1]}")
    
    # Convert the set to a list to maintain uniqueness
    output = list(unique_matches)
    
    # Sort the dates based on parsed date values
    sorted_output = sorted(output, key=extract_date)

    # Display the sorted dates
    print(sorted_output)
    
    return sorted_output
    
    
# Function to extract and parse the date
def extract_date(date_str):
    # Split the string by ', ' to separate the date part
    date_parts = date_str.split(', ')
    # Parse the date using the appropriate format
    return datetime.strptime(date_parts[1], '%d.%m.%Y')



