import base64
import urllib.request
import ssl
import os

# These are the absolute most current stable links from the v86 project home
V86_JS = "https://copy.sh/v86/build/libv86.js"
# Switching to the 'linux3.iso' which is often used for the basic v86 demos
ALPINE_ISO = "https://copy.sh/v86/images/linux3.iso" 

def get_base64(url):
    print(f"[*] Downloading: {url}")
    # Bypass SSL issues
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Servers often block Python's default User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as response:
            data = response.read()
            print(f"[+] Downloaded {len(data)} bytes. Encoding...")
            return base64.b64encode(data).decode('utf-8')
    except Exception as e:
        print(f"[!] Error: {e}")
        return None

def generate_offline_vm():
    v86_code = get_base64(V86_JS)
    iso_data = get_base64(ALPINE_ISO)

    if not v86_code or not iso_data:
        # Emergency fallback to a known tiny floppy image if the ISO fails
        print("[!] Trying emergency floppy mirror...")
        iso_data = get_base64("https://copy.sh/v86/images/linux.iso")

    if not v86_code or not iso_data:
        print("[!] Fatal: Could not reach any mirrors. Are you sure the Codespace has internet access?")
        return

    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Offline Linux VM</title>
    <style>
        body {{ background: #000; color: #0f0; font-family: monospace; margin: 0; padding: 20px; }}
        #screen {{ white-space: pre; font-family: 'Courier New', monospace; line-height: 1.0; font-size: 14px; letter-spacing: 0px; }}
        .status {{ color: #555; border-bottom: 1px solid #222; margin-bottom: 10px; padding-bottom: 5px; font-size: 11px; }}
        #save-status {{ color: #0ff; display: none; }}
    </style>
</head>
<body>
    <div class="status">V86_OFFLINE_READY | PERSISTENCE: IndexedDB <span id="save-status"> - SAVING...</span></div>
    <div id="screen"></div>
    <script>
        const v86_bin = atob("{v86_code}");
        const iso_bin = atob("{iso_data}");
        function str2ab(str) {{
            const buf = new ArrayBuffer(str.length);
            const bufView = new Uint8Array(buf);
            for (let i = 0; i < str.length; i++) bufView[i] = str.charCodeAt(i);
            return buf;
        }}
        const script = document.createElement('script');
        script.text = v86_bin;
        document.head.appendChild(script);
        const DB_NAME = "v86_db";
        async function getStore() {{
            return new Promise(res => {{
                const req = indexedDB.open(DB_NAME, 1);
                req.onupgradeneeded = e => e.target.result.createObjectStore("state");
                req.onsuccess = e => res(e.target.result.transaction("state", "readwrite").objectStore("state"));
            }});
        }}
        window.onload = async function() {{
            let initialState = null;
            try {{
                const store = await getStore();
                const req = store.get("last_snapshot");
                initialState = await new Promise(r => req.onsuccess = () => r(req.result));
            }} catch(e) {{}}
            const emulator = new V86Starter({{
                screen_container: document.getElementById("screen"),
                cdrom: {{ buffer: str2ab(iso_bin) }},
                autostart: true,
                initial_state: initialState ? {{ buffer: initialState }} : null
            }});
            setInterval(async () => {{
                document.getElementById("save-status").style.display = "inline";
                emulator.take_snapshot(async (err, result) => {{
                    if (!err) {{
                        const store = await getStore();
                        store.put(result, "last_snapshot");
                    }}
                    setTimeout(() => document.getElementById("save-status").style.display = "none", 1000);
                }});
            }}, 30000);
        }};
    </script>
</body>
</html>
"""
    with open("linux_offline.html", "w") as f:
        f.write(html_template)
    print("\n[+] SUCCESS: 'linux_offline.html' generated.")

if __name__ == "__main__":
    generate_offline_vm()