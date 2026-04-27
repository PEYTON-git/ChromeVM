import base64, urllib.request, ssl, os

V86_JS = "https://copy.sh/v86/build/libv86.js"
LINUX_IMG = "https://copy.sh/v86/images/linux3.iso"

def get_b64(url):
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx) as r:
        return base64.b64encode(r.read()).decode('utf-8')

print("[*] Building High-Readability Version...")
v86_data = get_b64(V86_JS)
krn_data = get_b64(LINUX_IMG)

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ChromeVM 2.0 | Terminal</title>
    <style>
        :root {{
            --bg-color: #1e1e1e;
            --text-color: #d4d4d4;
            --accent-color: #4ec9b0;
            --cursor-color: #aeafad;
        }}
        body {{ 
            background: var(--bg-color); 
            color: var(--text-color); 
            font-family: 'Cascadia Code', 'Source Code Pro', 'Courier New', monospace; 
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }}
        #header {{
            background: #252526;
            padding: 8px 15px;
            font-size: 12px;
            color: #858585;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
        }}
        #terminal-container {{
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            cursor: text;
        }}
        #terminal {{ 
            white-space: pre-wrap; 
            word-break: break-all; 
            font-size: 15px; 
            line-height: 1.4;
            letter-spacing: 0.5px;
        }}
        .cursor {{
            display: inline-block;
            width: 8px;
            height: 18px;
            background: var(--cursor-color);
            vertical-align: middle;
            animation: blink 1s step-end infinite;
        }}
        @keyframes blink {{
            50% {{ opacity: 0; }}
        }}
        /* Custom Scrollbar */
        ::-webkit-scrollbar {{ width: 10px; }}
        ::-webkit-scrollbar-track {{ background: #1e1e1e; }}
        ::-webkit-scrollbar-thumb {{ background: #333; border-radius: 5px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #444; }}
    </style>
</head>
<body>
    <div id="header">
        <span>root@chromevm:~</span>
        <span>V86_EMULATOR_ACTIVE</span>
    </div>
    <div id="terminal-container" onclick="document.body.focus()">
        <div id="terminal">Booting Linux kernel...</div><span class="cursor"></span>
    </div>

    <script>
        const v86_bin = atob("{v86_data}");
        const krn_bin = atob("{krn_data}");

        function toBuf(b64) {{
            const str = atob(b64);
            const buf = new Uint8Array(str.length);
            for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
            return buf.buffer;
        }}

        const s = document.createElement('script');
        s.text = v86_bin;
        document.head.appendChild(s);

        window.onload = () => {{
            const term = document.getElementById("terminal");
            const container = document.getElementById("terminal-container");
            
            const emulator = new V86Starter({{
                bzimage: {{ buffer: toBuf("{krn_data}") }},
                autostart: true,
                memory_size: 32 * 1024 * 1024,
                vga_enabled: false,
            }});

            emulator.add_listener("serial0-output-char", (char) => {{
                if (term.innerText.includes("Booting Linux kernel...")) term.innerText = "";
                term.innerText += char;
                container.scrollTop = container.scrollHeight;
            }});

            window.addEventListener("keypress", (e) => {{
                emulator.serial0_send(String.fromCharCode(e.which));
            }});
            
            // Special keys (Backspace, Enter)
            window.addEventListener("keydown", (e) => {{
                if(e.keyCode === 8) emulator.serial0_send(String.fromCharCode(127)); // Backspace
                if(e.keyCode === 13) emulator.serial0_send(String.fromCharCode(13)); // Enter
            }});
        }};
    </script>
</body>
</html>"""

with open("linux_pro.html", "w") as f: f.write(html)
print("[SUCCESS] Created 'linux_pro.html' - High Readability Version")