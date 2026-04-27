import base64
import urllib.request
import ssl
import os
import sys

# ==========================================
# CONFIGURATION & STABLE MIRRORS
# ==========================================
V86_JS_URL = "https://copy.sh/v86/build/libv86.js"
LINUX_KERNEL_URL = "https://copy.sh/v86/images/linux3.iso"

def get_base64(url):
    """Downloads a file and converts it to a Base64 string."""
    print(f"[*] Fetching: {url}")
    
    # Bypass SSL restrictions often found in Codespaces/School Networks
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Mimic a real browser to prevent 403 Forbidden errors
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            encoded = base64.b64encode(data).decode('utf-8')
            print(f"[+] Successfully encoded {len(data)} bytes.")
            return encoded
    except Exception as e:
        print(f"[!] ERROR downloading {url}: {e}")
        return None

def assemble():
    print("--- STARTING VM ASSEMBLY ---")
    
    # 1. Acquire Components
    v86_base64 = get_base64(V86_JS_URL)
    kernel_base64 = get_base64(LINUX_KERNEL_URL)
    
    if not v86_base64 or not kernel_base64:
        print("\n[FATAL ERROR] Could not download components. Check your internet connection.")
        sys.exit(1)

    # 2. Build the Unified HTML
    # We use a direct ArrayBuffer conversion inside the HTML for maximum speed.
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline Linux Terminal</title>
    <style>
        body {{ background: #000; color: #0f0; font-family: 'Courier New', monospace; margin: 0; padding: 15px; overflow: hidden; }}
        #screen {{ white-space: pre; font-size: 14px; line-height: 1.2; outline: none; }}
        .info {{ color: #444; font-size: 10px; border-bottom: 1px solid #222; margin-bottom: 10px; }}
        #save-notify {{ color: cyan; display: none; }}
    </style>
</head>
<body>
    <div class="info">V86_READY | STORAGE: IndexedDB <span id="save-notify">(SAVING...)</span></div>
    <div id="screen" tabindex="0"></div>

    <script>
        // Data injected by Python Assembler
        const V86_CODE = "{v86_base64}";
        const KERNEL_DATA = "{kernel_base64}";

        // Convert Base64 to ArrayBuffer
        function b64ToBuffer(b64) {{
            const bin = atob(b64);
            const buf = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
            return buf.buffer;
        }}

        // Inject the v86 Engine
        const v86Script = document.createElement('script');
        v86Script.text = atob(V86_CODE);
        document.head.appendChild(v86Script);

        // IndexedDB Persistence Logic
        const DB_NAME = "v86_persistence";
        const STORE_NAME = "state";

        async function getDBStore() {{
            return new Promise((resolve) => {{
                const req = indexedDB.open(DB_NAME, 1);
                req.onupgradeneeded = e => e.target.result.createObjectStore(STORE_NAME);
                req.onsuccess = e => resolve(e.target.result.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME));
            }});
        }}

        window.onload = async function() {{
            const screen = document.getElementById("screen");
            let initialState = null;

            // Try to load saved state
            try {{
                const store = await getDBStore();
                const req = store.get("last_state");
                initialState = await new Promise(r => req.onsuccess = () => r(req.result));
            }} catch(e) {{ console.log("New session started."); }}

            const settings = {{
                screen_container: screen,
                bzimage: {{ buffer: b64ToBuffer(KERNEL_DATA) }},
                autostart: true,
                memory_size: 64 * 1024 * 1024,
                vga_enabled: false // Serial mode for JSLinux-style speed
            }};

            if (initialState) settings.initial_state = {{ buffer: initialState }};

            const emulator = new V86Starter(settings);
            console.log("VM Started.");
            screen.focus();

            // Auto-save every 30 seconds
            setInterval(async () => {{
                document.getElementById("save-notify").style.display = "inline";
                emulator.take_snapshot(async (err, result) => {{
                    if (!err) {{
                        const store = await getDBStore();
                        store.put(result, "last_state");
                    }}
                    setTimeout(() => document.getElementById("save-notify").style.display = "none", 1000);
                }});
            }}, 30000);
        }};
    </script>
</body>
</html>"""

    # 3. Save the File
    output_path = "portable_linux.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"\n[SUCCESS] Unified VM created: {output_path}")
    print("[*] DOWNLOAD this file and open it on your Chromebook.")

# Execute the script
if __name__ == "__main__":
    assemble()