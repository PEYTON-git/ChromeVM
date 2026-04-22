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
                pass

def get_b64(filepath):
    print(f"[*] Encoding {filepath} to Base64...")
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def main():
    print("--- Verifying Dependencies ---")
    fetch_dependencies()
    print("------------------------------\n")

    print("[*] Packaging components...")
    
    # Encode EVERYTHING, including the JS engine, to avoid HTML parser conflicts
    engine_b64 = get_b64("libv86.js")
    wasm_b64 = get_b64("v86.wasm")
    bios_b64 = get_b64("seabios.bin")
    vga_b64 = get_b64("vgabios.bin")
    iso_b64 = get_b64("linux4.iso")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Linux VM (Ghost Injection)</title>
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
        const logEl = document.getElementById('log');
        const log = (msg, type = '') => {{
            logEl.innerHTML += `<br><span class="${{type}}">> ${{msg}}</span>`;
            logEl.scrollTop = logEl.scrollHeight;
        }};

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
                log("Unpacking JavaScript Engine...");
                
                // Decode the engine Base64 into raw text to bypass the HTML parser
                const engineBytes = new Uint8Array(decodeBase64("{engine_b64}"));
                const engineCode = new TextDecoder('utf-8').decode(engineBytes);
                
                // Inject directly into the DOM
                const script = document.createElement('script');
                script.text = engineCode;
                document.body.appendChild(script);

                if (typeof V86Starter === 'undefined') {{
                    throw new Error("Engine unpacked, but the browser security policy blocked execution.");
                }}
                log("Engine loaded successfully!", "success");

                log("Decoding WebAssembly module...");
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
                            log("WASM Compilation blocked by Chrome OS security policy.", "error");
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

        setTimeout(initVM, 150);
    </script>
</body>
</html>
"""
    
    output = "linux_ghost.html"
    print(f"\n[*] Writing everything to {output}...")
    with open(output, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"[OK] Done! Move {output} to your local Downloads folder and run it.")

if __name__ == "__main__":
    main()