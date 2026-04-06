import re

def parse_search_result(line):
    """Parse lines from javdb search results like the sample in `my_file.txt`.

    Example line:
    [ Playable  ![](https://c0.jdbstatic.com/covers/yr/yrOMa.jpg) **MIST-001** 99cm... 刃流花 11/09/2013  DL ](https://javdb.com/v/yrOMa "...")

    Returns (match, dict) where dict contains keys: id, title, actress, release_date, image_url, page_url
    """
    # A single, more robust regex to capture all fields at once
    # Allow flexible leading tokens (e.g. "Playable", "Playable CN", flags) before the image
    pattern = re.compile(
        r'\[\s*(?:[^\]]*?)!\[\]\((https?://[^\)]+)\)\s+'  # 1. Image URL (allow flexible prefix before image)
        r'\*\*([A-Z0-9-]+)\*\*\s+'                             # 2. ID
        r'(.*?)'                                                    # 3. Title and Actress (greedy)
        r'(\d{1,2}/\d{1,2}/\d{4})\s+'                           # 4. Date
        r'.*?DL\s*\]\((https?://[^\s"]+)',                         # 5. Page URL
        re.VERBOSE
    )
    match = pattern.search(line)

    if not match:
        return (None, None)

    image_url = match.group(1).strip()
    scene_id = match.group(2).strip()
    pre_date_text = match.group(3).strip()
    release_date = match.group(4).strip()
    page_url = match.group(5).strip()

    # Try to extract an actress name as the last run of CJK characters
    actress = None
    title = pre_date_text
    cjk_match = re.search(r'([\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+)\s*$', pre_date_text)
    if cjk_match:
        actress = cjk_match.group(1).strip()
        title = pre_date_text[:cjk_match.start()].strip()

    formalized = {
        "id": scene_id,
        "title": title,
        "actress": actress,
        "release_date": release_date,
        "image_url": image_url,
        "page_url": page_url,
    }
    return (match, formalized)


def parse_line_generic(line):
    # Example with a different URL and actress text
    #text = """[ ![](https://some.other-cdn.com/images/a1/B2C3d4.jpg) **ABCD-123** 新しいタイトルはこちらです 桃乃木かな 特典映像 01/15/2026  DL Today ](https://javbus.com/v/B2C3d4 "新しいタイトルはこちらです 桃乃木かな 特典映像")"""
    text = line 

    # A more robust regex pattern
    # It finds the actress name by looking for the last block of CJK characters before the date.
    # Make the image prefix flexible (allow tokens like 'Playable CN' before the image)
    pattern = re.compile(
        r'\[\s*[^\]]*?\!\[\]\((https?://[^\)]+)\)'  # 1. Capture the image URL (with flexible prefix)
        r'\s+\*\*([A-Z0-9-]+)\*\*'                      # 2. Capture the ID
        r'\s+(.*?)'                                        # 3. Capture the Title (non-greedy)
        r'\s+([\u3000-\u9FFF\s]+)'                      # 4. Capture the Actress
        r'\s+.*?'                                          # Match filler text
        r'(\d{1,2}/\d{1,2}/\d{4})'                       # 5. Capture the Date
        r'.*?'                                              # Match remaining text until the end
        r'\]\((https?://[^\s"]+)'                       # 6. Capture the main link URL
        , re.VERBOSE)
    match = pattern.search(text)

    formalized_data = None 
    if match:
        # Extracting the captured groups
        formalized_data = {
                "id": match.group(2).strip(),
                "title": match.group(3).strip(),
                "actress": match.group(4).strip(),
                "release_date": match.group(5).strip(),
                "image_url": match.group(1).strip(),
                "page_url": match.group(6).strip()
            }        
        #print(formalized_data)

        #pprint.pprint(formalized_data)        
    #else:
    #    print("No match found.")
    return (match, formalized_data)
