import base64, urllib.request, ssl, os

V86_JS = "https://copy.sh/v86/build/libv86.js"
LINUX_IMG = "https://copy.sh/v86/images/linux3.iso"

def get_b64(url):
    print(f"[*] Fetching {url}...")
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx) as r:
        data = r.read()
        print(f"[+] Downloaded {len(data)} bytes.")
        return base64.b64encode(data).decode('utf-8')

def build():
    print("[*] Assembling Debug/Compat Version...")
    try:
        v86_data = get_b64(V86_JS)
        krn_data = get_b64(LINUX_IMG)
    except Exception as e:
        print(f"[!] Network error: {e}")
        return

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ChromeVM | Debug Edition</title>
    <style>
        body {{ background: #1e1e1e; color: #d4d4d4; font-family: monospace; margin: 0; }}
        #header {{ background: #252526; padding: 10px; font-size: 12px; border-bottom: 1px solid #333; }}
        #terminal-container {{ background: #000; height: calc(100vh - 40px); padding: 10px; overflow: auto; }}
        #screen_container {{ outline: none; }}
        .error-log {{ color: #ff5555; font-weight: bold; margin-bottom: 5px; white-space: pre-wrap; }}
        .sys-log {{ color: #55ff55; margin-bottom: 5px; }}
    </style>
</head>
<body>
    <div id="header">root@chromevm:~ | COMPATIBILITY & DEBUG MODE</div>
    <div id="terminal-container" onclick="document.getElementById('screen_container')?.focus()">
        <div id="debug-log"></div>
        <div id="screen_container" tabindex="0"></div>
    </div>

    <script>
        const debugLog = document.getElementById('debug-log');
        
        // Custom logging function
        function logMsg(msg, isErr=false) {{
            const div = document.createElement('div');
            div.className = isErr ? 'error-log' : 'sys-log';
            div.textContent = (isErr ? "[ERROR] " : "[SYSTEM] ") + msg;
            debugLog.appendChild(div);
        }}

        // Catch hidden browser crashes since DevTools is blocked!
        window.onerror = function(msg, url, lineNo) {{
            logMsg(msg + " (Line: " + lineNo + ")", true);
            return false;
        }};
        
        const origErr = console.error;
        console.error = function(...args) {{
            logMsg(args.join(" "), true);
            origErr.apply(console, args);
        }};

        logMsg("Initializing ChromeVM...");

        try {{
            logMsg("Decoding v86 Engine...");
            const s = document.createElement('script');
            s.text = atob("{v86_data}");
            document.head.appendChild(s);
            logMsg("v86 Engine successfully injected.");

            function getIsoBuffer() {{
                logMsg("Decoding Linux ISO in memory...");
                const str = atob("{krn_data}");
                const buf = new Uint8Array(str.length);
                for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
                logMsg("ISO Decode complete.");
                return buf.buffer;
            }}

            window.onload = () => {{
                logMsg("Starting V86 Emulator Engine...");
                try {{
                    const emulator = new V86Starter({{
                        screen_container: document.getElementById("screen_container"),
                        cdrom: {{ buffer: getIsoBuffer() }},
                        autostart: true,
                        memory_size: 32 * 1024 * 1024,
                        vga_enabled: true,
                        wasm_path: "", 
                        disable_wasm: true // Avoids the WebAssembly block!
                    }});
                    logMsg("Emulator launched. Waiting for video output...");
                }} catch(err) {{
                    logMsg("Emulator Crash: " + err.message, true);
                }}
            }};
        }} catch (err) {{
            logMsg("Setup Crash: " + err.message, true);
        }}
    </script>
</body>
</html>"""

    with open("chrome_debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\n[SUCCESS] Created 'chrome_debug.html'")

if __name__ == "__main__":
    build()