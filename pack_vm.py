import base64
import os
import urllib.request

FILES = {
    "libv86.js": "https://unpkg.com/v86/build/libv86.js",
    "v86.wasm": "https://unpkg.com/v86/build/v86.wasm",
    "seabios.bin": "https://raw.githubusercontent.com/copy/v86/master/bios/seabios.bin",
    "vgabios.bin": "https://raw.githubusercontent.com/copy/v86/master/bios/vgabios.bin",
    "linux4.iso": "https://copy.sh/v86/images/linux4.iso"
}

def fetch_deps():
    for f, url in FILES.items():
        if not os.path.exists(f):
            print(f"[*] Downloading {f}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as r, open(f, 'wb') as out: out.write(r.read())

def get_b64(f):
    with open(f, "rb") as file: return base64.b64encode(file.read()).decode("utf-8")

def main():
    fetch_deps()
    
    # We read the engine and escape it specifically for HTML placement
    with open("libv86.js", "r", encoding="utf-8") as f:
        # Escaping backslashes and script tags is vital for static embedding
        engine_raw = f.read().replace("\\", "\\\\").replace("</script>", "<\\/script>")

    wasm_b64 = get_b64("v86.wasm")
    bios_b64 = get_b64("seabios.bin")
    vga_b64 = get_b64("vgabios.bin")
    iso_b64 = get_b64("linux4.iso")

    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Linux Offline (Monolith)</title>
    <style>
        body {{ background: #000; color: #0f0; font-family: monospace; padding: 20px; }}
        #screen_container {{ border: 1px solid #333; display: inline-block; }}
        #log {{ color: #888; font-size: 12px; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div id="log">System: Initializing...</div>
    <div id="screen_container">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display:none"></canvas>
    </div>

    <script>
        try {{
            {engine_raw}
            window.engineLoaded = true;
        }} catch (e) {{
            window.engineError = e.message;
        }}
    </script>

    <script>
        const logger = document.getElementById("log");
        function decode(b64) {{
            const str = window.atob(b64);
            const buf = new Uint8Array(str.length);
            for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
            return buf.buffer;
        }}

        async function boot() {{
            if (!window.engineLoaded) {{
                logger.innerHTML = "FATAL: Engine parse error: " + (window.engineError || "Unknown block");
                return;
            }}

            try {{
                logger.innerText = "Status: Decoding WASM...";
                const wasm = decode("{wasm_b64}");
                
                logger.innerText = "Status: Decoding Disks...";
                const bios = decode("{bios_b64}");
                const vga = decode("{vga_b64}");
                const iso = decode("{iso_b64}");

                logger.innerText = "Status: Booting...";
                new V86Starter({{
                    wasm_fn: async (i) => {{
                        const res = await WebAssembly.instantiate(wasm, i);
                        return res.instance.exports;
                    }},
                    memory_size: 128 * 1024 * 1024,
                    screen_container: document.getElementById("screen_container"),
                    bios: {{ buffer: bios }},
                    vga_bios: {{ buffer: vga }},
                    cdrom: {{ buffer: iso }},
                    autostart: true
                }});
                logger.style.display = "none";
            }} catch (err) {{
                logger.innerText = "Runtime Error: " + err.message;
            }}
        }}
        
        boot();
    </script>
</body>
</html>
"""
    with open("linux_monolith.html", "w", encoding="utf-8") as f: f.write(html_template)
    print("[OK] Created linux_monolith.html")

main()