import base64
import os
import sys
import urllib.request

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
    except Exception as e: pass

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

def encode_raw_base64(filepath):
    print(f"[*] Encoding {filepath}...")
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def main():
    print("--- Pulling Dependencies ---")
    for filename, url in V86_FILES.items(): download_file(url, filename)
    download_with_fallback(ISO_MIRRORS, "linux4.iso")
    print("----------------------------\n")

    with open("libv86.js", "r", encoding="utf-8") as f:
        # CRITICAL FIX: Prevent premature script closure inside the HTML template
        v86_js = f.read().replace("</script>", "<\\/script>")

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
        // --- v86 Engine ---
        {v86_js}
    </script>
</head>
<body>
    <div id="screen_container">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px; padding: 5px;">Booting VM... Please wait up to 10 seconds.</div>
        <canvas style="display: none"></canvas>
    </div>

    <script>
        // Use browser's native C++ engine to decode Base64 instantly without locking the thread
        async function loadDataUriToBuffer(b64, mime) {{
            const dataUri = `data:${{mime}};base64,${{b64}}`;
            const res = await fetch(dataUri);
            return await res.arrayBuffer();
        }}

        window.onload = async function() {{
            try {{
                // Decode all files concurrently into raw memory
                const [wasmBuf, biosBuf, vgaBuf, isoBuf] = await Promise.all([
                    loadDataUriToBuffer("{wasm_b64}", "application/wasm"),
                    loadDataUriToBuffer("{bios_b64}", "application/octet-stream"),
                    loadDataUriToBuffer("{vgabios_b64}", "application/octet-stream"),
                    loadDataUriToBuffer("{iso_b64}", "application/octet-stream")
                ]);

                document.querySelector("#screen_container div").innerText = ""; // Clear loading text

                var emulator = new V86Starter({{
                    // Bypass internal fetch blocks by compiling the WebAssembly manually
                    wasm_fn: async function(param) {{
                        const compiled = await WebAssembly.instantiate(wasmBuf, param);
                        return compiled.instance.exports;
                    }},
                    memory_size: 128 * 1024 * 1024,
                    vga_memory_size: 8 * 1024 * 1024,
                    screen_container: document.getElementById("screen_container"),
                    bios: {{ buffer: biosBuf }},
                    vga_bios: {{ buffer: vgaBuf }},
                    cdrom: {{ buffer: isoBuf }},
                    autostart: true
                }});
            }} catch (err) {{
                // If Chrome OS blocks something, print it visibly to the screen
                document.querySelector("#screen_container div").innerHTML = 
                    `<span style="color:red; font-size:16px;">CRASH ERROR: ${{err.message}}</span>`;
            }}
        }};
    </script>
</body>
</html>
"""
    output = "linux_offline_final.html"
    print(f"\n[*] Writing to {output}...")
    with open(output, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"[OK] Done! Open {output} from your Downloads folder.")

if __name__ == "__main__":
    main()