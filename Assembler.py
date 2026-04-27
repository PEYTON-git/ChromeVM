import base64, urllib.request, ssl, os

# V86 Engine and a tiny Linux 3 ISO
V86_JS = "https://copy.sh/v86/build/libv86.js"
LINUX_IMG = "https://copy.sh/v86/images/linux3.iso"

def get_b64(url):
    print(f"[*] Fetching: {url}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            data = r.read()
            print(f"[+] Encoded {len(data)} bytes.")
            return base64.b64encode(data).decode('utf-8')
    except Exception as e:
        print(f"[!] FAILED: {e}")
        return None

def build():
    print("[*] Assembling ChromeVM...")
    v86_data = get_b64(V86_JS)
    krn_data = get_b64(LINUX_IMG)

    if not v86_data or not krn_data:
        print("[!] Aborting due to download failure.")
        return

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ChromeVM | Terminal</title>
    <style>
        :root {{ --bg: #1e1e1e; --fg: #d4d4d4; }}
        body {{ 
            background: var(--bg); color: var(--fg); 
            font-family: 'Courier New', monospace; 
            margin: 0; display: flex; flex-direction: column; height: 100vh; 
        }}
        #header {{ 
            background: #252526; padding: 10px; font-size: 12px; 
            color: #858585; border-bottom: 1px solid #333; 
        }}
        #terminal-container {{ 
            flex: 1; padding: 10px; overflow: auto; background: #000; 
        }}
        /* v86's screen engine will inject its pre tag here */
        #screen_container {{ font-size: 14px; line-height: 1.2; outline: none; }}
    </style>
</head>
<body>
    <div id="header">root@chromevm:~ | V86_EMULATOR_ACTIVE</div>
    <div id="terminal-container" onclick="document.getElementById('screen_container').focus()">
        <div id="screen_container" tabindex="0"></div>
    </div>

    <script>
        // 1. Inject the v86 Emulator Engine cleanly
        const s = document.createElement('script');
        s.text = atob("{v86_data}");
        document.head.appendChild(s);

        // 2. Decode Base64 to ArrayBuffer safely (Fixed bug here)
        function b64ToBuffer(b64) {{
            const bin = atob(b64);
            const buf = new Uint8Array(bin.length);
            for(let i=0; i<bin.length; i++) buf[i] = bin.charCodeAt(i);
            return buf.buffer;
        }}

        // 3. Boot VM
        window.onload = () => {{
            const emulator = new V86Starter({{
                screen_container: document.getElementById("screen_container"),
                // Fixed bug: Using 'cdrom' instead of 'bzimage' for an ISO file
                cdrom: {{ buffer: b64ToBuffer("{krn_data}") }},
                autostart: true,
                memory_size: 32 * 1024 * 1024,
                // Fixed bug: Restored VGA so the ISO can draw its bootloader text
                vga_enabled: true 
            }});
        }};
    </script>
</body>
</html>"""

    with open("linux_final.html", "w") as f:
        f.write(html)
    print("\n[SUCCESS] Created 'linux_final.html'!")

if __name__ == "__main__":
    build()