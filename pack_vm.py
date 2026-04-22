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

ISO_MIRRORS = [
    "https://i.copy.sh/linux4.iso",
    "https://copy.sh/v86/images/linux4.iso"
]

def download_file(url, filename):
    if os.path.exists(filename):
        return
    print(f"[*] Downloading {filename}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
            out_file.write(response.read())
    except urllib.error.URLError as e:
        print(f"[!] Failed to download {filename}: {e}")
        sys.exit(1)

def download_with_fallback(mirrors, filename):
    if os.path.exists(filename):
        return
    print(f"[*] Downloading {filename}...")
    for url in mirrors:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
                out_file.write(response.read())
            return
        except urllib.error.URLError:
            continue
    print(f"[!] Critical Error: All mirrors failed for {filename}.")
    sys.exit(1)

def encode_file_to_raw_base64(filepath):
    """Returns JUST the Base64 string, no data URI wrapper."""
    print(f"[*] Encoding {filepath} to Base64...")
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def main():
    print("--- Checking and Pulling Dependencies ---")
    for filename, url in V86_FILES.items():
        download_file(url, filename)
    download_with_fallback(ISO_MIRRORS, "linux4.iso")
    print("-----------------------------------------\n")

    with open("libv86.js", "r", encoding="utf-8") as f:
        v86_js_content = f.read()

    # Get raw base64 instead of Data URIs
    wasm_b64 = encode_file_to_raw_base64("v86.wasm")
    bios_b64 = encode_file_to_raw_base64("seabios.bin")
    vgabios_b64 = encode_file_to_raw_base64("vgabios.bin")
    iso_b64 = encode_file_to_raw_base64("linux4.iso")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline Linux VM</title>
    <style>
        body {{ background-color: #111; color: #eee; margin: 0; padding: 20px; font-family: sans-serif; display: flex; justify-content: center; }}
        #screen_container {{ background-color: #000; border: 2px solid #444; padding: 5px; min-width: 640px; min-height: 400px; }}
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
        // Memory-safe Base64 to Blob URL converter
        function b64ToBlobUrl(b64, mimeType) {{
            const binary = window.atob(b64);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {{
                bytes[i] = binary.charCodeAt(i);
            }}
            const blob = new Blob([bytes.buffer], {{ type: mimeType }});
            return URL.createObjectURL(blob);
        }}

        window.onload = function() {{
            // Convert Base64 strings to fake files in RAM
            const wasmUrl = b64ToBlobUrl("{wasm_b64}", "application/wasm");
            const biosUrl = b64ToBlobUrl("{bios_b64}", "application/octet-stream");
            const vgaUrl = b64ToBlobUrl("{vgabios_b64}", "application/octet-stream");
            const isoUrl = b64ToBlobUrl("{iso_b64}", "application/octet-stream");

            var emulator = new V86Starter({{
                wasm_path: wasmUrl,
                memory_size: 128 * 1024 * 1024,
                vga_memory_size: 8 * 1024 * 1024,
                screen_container: document.getElementById("screen_container"),
                bios: {{ url: biosUrl }},
                vga_bios: {{ url: vgaUrl }},
                cdrom: {{ url: isoUrl, async: true }},
                autostart: true
            }});
        }};
    </script>
</body>
</html>
"""

    output_filename = "linux_offline_fixed.html"
    print(f"\n[*] Writing everything to {output_filename}...")
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_template)
        
    print(f"[OK] Done! Open {output_filename} from your standard Downloads folder.")

if __name__ == "__main__":
    main()