import base64
import os
import urllib.request

# --- Configuration ---
FILES = {
    "libv86.js": "https://unpkg.com/v86/build/libv86.js",
    "v86.wasm": "https://unpkg.com/v86/build/v86.wasm",
    "seabios.bin": "https://raw.githubusercontent.com/copy/v86/master/bios/seabios.bin",
    "vgabios.bin": "https://raw.githubusercontent.com/copy/v86/master/bios/vgabios.bin",
    "linux4.iso": "https://copy.sh/v86/images/linux4.iso"
}

def fetch_dependencies():
    for filename, url in FILES.items():
        if not os.path.exists(filename):
            print(f"[*] Downloading {filename}...")
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception as e:
                print(f"[!] Failed to download {filename}: {e}")

def get_b64(filepath):
    print(f"[*] Encoding {filepath} to Base64...")
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def main():
    print("--- Verifying Dependencies ---")
    fetch_dependencies()
    print("------------------------------\n")

    print("[*] Packaging components...")
    
    # Inject JS as raw text to bypass Data URI length limitations.
    # Escaping script tags prevents the HTML from breaking prematurely.
    with open("libv86.js", "r", encoding="utf-8") as f:
        v86_js = f.read().replace("</script>", "<\\/script>")

    wasm_b64 = get_b64("v86.wasm")
    bios_b64 = get_b64("seabios.bin")
    vga_b64 = get_b64("vgabios.bin")
    iso_b64 = get_b64("linux4.iso")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Linux VM (Refined)</title>
    <style>
        body {{ background: #0f172a; color: #e2e8f0; font-family: ui-sans-serif, system-ui, sans-serif; display: flex; flex-direction: column; align-items: center; padding: 2rem; margin: 0; }}
        .container {{ background: #1e293b; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); max-width: 800px; width: 100%; }}
        #screen_container {{ background: #000; border: 2px solid #334155; border-radius: 0.25rem; min-width: 640px; min-height: 400px; display: flex; justify-content: center; align-items: center; overflow: hidden; margin-top: 1rem; position: relative; }}
        #log {{ font-family: monospace; color: #38bdf8; margin-bottom: 1rem; padding: 0.75rem; background: #020617; border-radius: 0.25rem; white-space: pre-wrap; }}
        .error {{ color: #ef4444 !important; font-weight: bold; }}
        .success {{ color: #22c55e !important; }}
    </style>
</head>
<body>
    <div class="container">
        <h2 style="margin-top:0;">Offline Linux Environment</h2>
        <div id="log">Initializing diagnostics...</div>
        <div id="screen_container">
            <div style="white-space: pre; font: 14px monospace; line-height: 14px; position: absolute; top: 5px; left: 5px;"></div>
            <canvas style="display:none"></canvas>
        </div>
    </div>

    <script>
        {v86_js}
    </script>

    <script>
        const logEl = document.getElementById('log');
        const log = (msg, type = '') => {{
            logEl.innerHTML += `<br><span class="${{type}}">> ${{msg}}</span>`;
            logEl.scrollTop = logEl.scrollHeight;
        }};

        // Efficient, sequential Base64 to ArrayBuffer decoder (Memory Safe)
        function decodeBase64(b64) {{
            const binString = window.atob(b64);
            const len = binString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {{
                bytes[i] = binString.charCodeAt(i);
            }}
            return bytes.buffer;
        }}

        async function initVM() {{
            try {{
                log("Checking environment compatibility...");
                if (typeof V86Starter === 'undefined') {{
                    throw new Error("v86 engine failed to load. The browser dropped the script.");
                }}
                if (typeof WebAssembly === 'undefined') {{
                    throw new Error("WebAssembly is completely disabled on this device.");
                }}

                log("Decoding WebAssembly engine...");
                const wasmBuf = decodeBase64("{wasm_b64}");
                
                log("Decoding BIOS and OS Disks (this may take a few seconds)...");
                const biosBuf = decodeBase64("{bios_b64}");
                const vgaBuf = decodeBase64("{vga_b64}");
                const isoBuf = decodeBase64("{iso_b64}");

                log("Booting Virtual Machine...", "success");
                
                const emulator = new V86Starter({{
                    wasm_fn: async (imports) => {{
                        try {{
                            const {{ instance }} = await WebAssembly.instantiate(wasmBuf, imports);
                            return instance.exports;
                        }} catch (e) {{
                            log("WASM Compilation blocked! Your Chromebook's security policy likely blocks 'unsafe-wasm-eval' for local files.", "error");
                            throw e;
                        }}
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
                log("FATAL ERROR: " + err.message, "error");
            }}
        }}

        // Start after a tiny delay to allow the HTML/CSS to render first
        setTimeout(initVM, 150);
    </script>
</body>
</html>
"""
    
    output = "linux_refined.html"
    print(f"\n[*] Writing everything to {output}...")
    with open(output, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"[OK] Done! Move {output} to your local Downloads folder and run it.")

if __name__ == "__main__":
    main()