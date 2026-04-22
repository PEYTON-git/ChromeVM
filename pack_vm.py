import base64
import os
import sys
import urllib.request
import urllib.error

# --- Dependencies ---
V86_FILES = {
    "libv86.js": "https://unpkg.com/v86/build/libv86.js",
    "v86.wasm": "https://unpkg.com/v86/build/v86.wasm",
    "seabios.bin": "https://raw.githubusercontent.com/copy/v86/master/bios/seabios.bin",
    "vgabios.bin": "https://raw.githubusercontent.com/copy/v86/master/bios/vgabios.bin"
}

# Multiple mirrors for the minimal Linux ISO to prevent DNS/Download errors
ISO_MIRRORS = [
    "https://i.copy.sh/linux4.iso",
    "https://copy.sh/v86/images/linux4.iso"
]

def download_file(url, filename):
    """Standard downloader for single URLs."""
    if os.path.exists(filename):
        print(f"[OK] {filename} already exists. Skipping download.")
        return

    print(f"[*] Downloading {filename}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
            out_file.write(response.read())
        print(f"[OK] Successfully downloaded {filename}.")
    except urllib.error.URLError as e:
        print(f"[!] Failed to download {filename}: {e}")
        sys.exit(1)

def download_with_fallback(mirrors, filename):
    """Downloader that tries multiple URLs if one fails."""
    if os.path.exists(filename):
        print(f"[OK] {filename} already exists. Skipping download.")
        return

    print(f"[*] Downloading {filename}...")
    for url in mirrors:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
                out_file.write(response.read())
            print(f"[OK] Successfully downloaded {filename} from {url}.")
            return # Success, exit the loop
        except urllib.error.URLError as e:
            print(f"    [-] Mirror failed ({url}): {e}")
            continue # Try the next URL in the list
    
    # If the loop finishes without returning, all mirrors failed
    print(f"[!] Critical Error: All mirrors failed for {filename}.")
    sys.exit(1)

def encode_file_to_data_uri(filepath, mime_type="application/octet-stream"):
    """Reads a binary file and returns a Base64 data URI."""
    print(f"[*] Encoding {filepath} to Base64 (This might take a moment)...")
    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

def main():
    print("--- Checking and Pulling Dependencies ---")
    
    # 1. Pull core engine and BIOS files
    for filename, url in V86_FILES.items():
        download_file(url, filename)
        
    # 2. Pull the ISO using the robust mirror setup
    download_with_fallback(ISO_MIRRORS, "linux4.iso")
    print("-----------------------------------------\n")

    # 3. Read libv86.js as plain text
    with open("libv86.js", "r", encoding="utf-8") as f:
        v86_js_content = f.read()

    # 4. Encode binaries to Base64 Data URIs
    wasm_uri = encode_file_to_data_uri("v86.wasm", "application/wasm")
    bios_uri = encode_file_to_data_uri("seabios.bin")
    vgabios_uri = encode_file_to_data_uri("vgabios.bin")
    iso_uri = encode_file_to_data_uri("linux4.iso")

    # 5. The HTML Template
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline Linux VM</title>
    <style>
        body {{ background-color: #111; color: #eee; margin: 0; padding: 20px; font-family: sans-serif; display: flex; justify-content: center; }}
        #screen_container {{ background-color: #000; border: 2px solid #444; padding: 5px; }}
    </style>
    <script>
        // --- v86 Engine ---
        {v86_js_content}
    </script>
</head>
<body>
    <div id="screen_container">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display: none"></canvas>
    </div>

    <script>
        window.onload = function() {{
            var emulator = new V86Starter({{
                wasm_path: "{wasm_uri}",
                memory_size: 128 * 1024 * 1024, // 128 MB RAM for minimal Linux
                vga_memory_size: 8 * 1024 * 1024,
                screen_container: document.getElementById("screen_container"),
                bios: {{ url: "{bios_uri}" }},
                vga_bios: {{ url: "{vgabios_uri}" }},
                cdrom: {{ url: "{iso_uri}", async: false }}, 
                autostart: true
            }});
        }};
    </script>
</body>
</html>
"""

    # 6. Write the final single-file HTML
    output_filename = "linux_offline.html"
    print(f"\n[*] Writing everything to {output_filename}...")
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_template)
        
    print(f"[OK] Done! The script finished successfully.")
    print(f"[OK] You can now open {output_filename} in your browser.")

if __name__ == "__main__":
    main()