import base64

def get_b64(filename):
    with open(filename, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

print("Encoding files...")
wasm_b64 = get_b64("v86.wasm")
bios_b64 = get_b64("seabios.bin")
iso_b64 = get_b64("alpine-virt-3.18.4-x86.iso")

with open("libv86.js", "r", encoding="utf-8") as f:
    js_code = f.read().replace("</script>", "<\\/script>")

html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Alpine Linux Solo</title>
    <style>
        body {{ margin: 0; background: #000; color: #0f0; font-family: monospace; }}
        #screen {{ width: 100vw; height: 100vh; }}
        #status {{ position: fixed; top: 0; left: 0; background: #222; padding: 10px; z-index: 10; }}
    </style>
</head>
<body>
    <div id="status">Initializing...</div>
    <div id="screen"></div>
    
    <script type="text/plain" id="wasm-data">{wasm_b64}</script>
    <script type="text/plain" id="bios-data">{bios_b64}</script>
    <script type="text/plain" id="iso-data">{iso_b64}</script>

    <script>{js_code}</script>

    <script>
        window.onload = () => {{
            const status = document.getElementById("status");
            try {{
                status.innerText = "Engine Loaded. Preparing Disk...";
                
                const emulator = new V86Starter({{
                    wasm_path: "data:application/wasm;base64," + document.getElementById("wasm-data").textContent,
                    memory_size: 256 * 1024 * 1024,
                    vga_canvas: document.createElement("canvas"),
                    term_container: document.getElementById("screen"),
                    bios: {{ url: "data:application/octet-stream;base64," + document.getElementById("bios-data").textContent }},
                    cdrom: {{ url: "data:application/octet-stream;base64," + document.getElementById("iso-data").textContent }},
                    autostart: true,
                }});

                emulator.add_listener("emulator-ready", () => {{
                    status.style.display = "none";
                }});
            }} catch(e) {{
                status.innerText = "Error: " + e.message;
            }}
        }};
    </script>
</body>
</html>"""

with open("Alpine-Portable.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Done! Download Alpine-Portable.html")