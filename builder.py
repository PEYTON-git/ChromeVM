import base64
import urllib.request
import os

print("1. Downloading emulator files...")
urllib.request.urlretrieve("https://copy.sh/v86/build/libv86.js", "libv86.js")
urllib.request.urlretrieve("https://copy.sh/v86/build/v86.wasm", "v86.wasm")
urllib.request.urlretrieve("https://copy.sh/v86/bios/seabios.bin", "seabios.bin")

# We assume you still have the Alpine ISO in the Codespace from earlier
iso_file = "alpine-virt-3.18.4-x86.iso"

print("2. Converting binary files to Base64 (this takes a few seconds)...")
def get_b64(filename):
    with open(filename, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

wasm_b64 = get_b64("v86.wasm")
bios_b64 = get_b64("seabios.bin")
iso_b64 = get_b64(iso_file)

print("3. Reading JavaScript driver...")
with open("libv86.js", "r", encoding="utf-8") as f:
    js_code = f.read()

print("4. Stitching the Ultimate HTML file...")
# Notice how ALL external URLs have been replaced with Base64 data variables
html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Ultimate Offline VM</title>
    <style>
        body {{ margin: 0; background: #000; color: #0f0; font-family: monospace; overflow: hidden; }}
        #screen {{ width: 100vw; height: 100vh; }}
    </style>
</head>
<body>
    <div id="screen">Booting True Offline VM...</div>
    
    <script>{js_code}</script>
    
    <script>
        const emulator = new V86Starter({{
            wasm_path: "data:application/wasm;base64,{wasm_b64}",
            memory_size: 256 * 1024 * 1024,
            vga_canvas: document.createElement("canvas"),
            term_container: document.getElementById("screen"),
            bios: {{ url: "data:application/octet-stream;base64,{bios_b64}" }},
            cdrom: {{ url: "data:application/octet-stream;base64,{iso_b64}" }},
            autostart: true,
        }});
    </script>
</body>
</html>"""

with open("True-Offline-OS.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Success! Your completely offline OS is ready.")