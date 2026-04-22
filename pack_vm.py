import base64
import os
import sys
import urllib.request
import urllib.error

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
    if os.path.exists(filename): return
    print(f"[*] Downloading {filename}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
            out_file.write(response.read())
    except Exception as e:
        print(f"[!] Failed: {e}")
        sys.exit(1)

def download_with_fallback(mirrors, filename):
    if os.path.exists(filename): return
    print(f"[*] Downloading {filename}...")
    for url in mirrors:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
                out_file.write(response.read())
            return
        except: continue
    print(f"[!] All mirrors failed for {filename}.")
    sys.exit(1)

def encode_raw_base64(filepath):
    print(f"[*] Encoding {filepath} into RAM buffer...")
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def main():
    print("--- Pulling Dependencies ---")
    for filename, url in V86_FILES.items(): download_file(url, filename)
    download_with_fallback(ISO_MIRRORS, "linux4.iso")
    print("----------------------------\n")

    with open("libv86.js", "r", encoding="utf-8") as f:
        v86_js = f.read()

    wasm_b64 = encode_raw_base64("v86.wasm")
    bios_b64 = encode_raw_base64("seabios.bin")
    vgabios_b64 = encode_raw_base64("vgabios.bin")
    iso_b64 = encode_raw_base64("linux4.iso")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Offline Linux VM</title>
    <style>
        body {{ background-color: #111; color: #eee; margin: 0; padding: 20px; display: flex; justify-content: center; }}
        #screen_container {{ background-color: #000; border: 2px solid #444; padding: 5px; min-width: 640px; min-height: 400px; }}
    </style>
    <script>
        {v86_js}
    </script>
</head>
<body>
    <div id="screen_container">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display: none"></canvas>
    </div>

    <script>
        // Decodes Base64 directly into raw RAM (ArrayBuffer)
        function b64ToBuffer(b64) {{
            const binary = window.atob(b64);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {{
                bytes[i] = binary.charCodeAt(i);
            }}
            return bytes.buffer;
        }}

        // WebAssembly still needs a Blob URL in v86, but full files work fine
        function b64ToBlobUrl(b64, mime) {{
            return URL.createObjectURL(new Blob([b64ToBuffer(b64)], {{type: mime}}));
        }}

        window.onload = function() {{
            // Hydrate everything directly into memory to bypass local file restrictions
            const biosBuf = b64ToBuffer("{bios_b64}");
            const vgaBuf = b64ToBuffer("{vgabios_b64}");
            const isoBuf = b64ToBuffer("{iso_b64}");
            const wasmUrl = b64ToBlobUrl("{wasm_b64}", "application/wasm");

            var emulator = new V86Starter({{
                wasm_path: wasmUrl,
                memory_size: 128 * 1024 * 1024,
                vga_memory_size: 8 * 1024 * 1024,
                screen_container: document.getElementById("screen_container"),
                bios: {{ buffer: biosBuf }},     // Using raw RAM instead of URLs
                vga_bios: {{ buffer: vgaBuf }},  // Using raw RAM instead of URLs
                cdrom: {{ buffer: isoBuf }},     // Using raw RAM instead of URLs
                autostart: true
            }});
        }};
    </script>
</body>
</html>
"""
    output = "linux_offline_RAM.html"
    print(f"\n[*] Writing to {output}...")
    with open(output, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"[OK] Done! Open {output} locally.")

if __name__ == "__main__":
    main()