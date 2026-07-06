import os
import re
import urllib.request

def main():
    # Make sure target directories exist
    os.makedirs("static/fonts", exist_ok=True)
    os.makedirs("static/css", exist_ok=True)

    urls = [
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap",
        "https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Exo+2:wght@300;400;600&display=swap"
    ]

    # Firefox or Chrome User-Agent to get modern woff2 format from Google Fonts API
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    combined_css = ""

    for url in urls:
        print(f"Fetching CSS metadata from: {url}")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                css_content = response.read().decode('utf-8')
                combined_css += "\n" + css_content
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")

    # Find all source URLs (matching https://... or http://...)
    # The URL could have quotes: url('https://...') or url("https://...") or url(https://...)
    font_urls = re.findall(r'url\([\'"]?(https://[^\'")]+)[\'"]?\)', combined_css)
    font_urls = list(set(font_urls))  # deduplicate

    print(f"Found {len(font_urls)} unique font files to download.")

    url_mapping = {}

    for f_url in font_urls:
        # Extract a unique local filename
        filename = f_url.split('/')[-1]
        local_path = os.path.join("static/fonts", filename)
        
        print(f"Downloading {filename}...")
        try:
            req_font = urllib.request.Request(f_url, headers=headers)
            with urllib.request.urlopen(req_font) as font_resp:
                with open(local_path, "wb") as f:
                    f.write(font_resp.read())
            # Map remote URL to local relative path
            url_mapping[f_url] = f"/static/fonts/{filename}"
        except Exception as e:
            print(f"Error downloading {f_url}: {e}")

    # Replace all remote URLs in the CSS with local relative paths
    local_css = combined_css
    for remote_url, local_path in url_mapping.items():
        local_css = local_css.replace(remote_url, local_path)

    # Write local CSS file
    with open("static/css/fonts.css", "w", encoding="utf-8") as f:
        f.write(local_css)

    print("Success: Saved local fonts CSS to static/css/fonts.css")

if __name__ == "__main__":
    main()
