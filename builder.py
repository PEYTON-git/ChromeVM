import base64
import os

print("1. Reading and converting files to Base64...")
def get_b64(filename):
    print(f"   -> Processing {filename}...")
    with open(filename, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

wasm_b64 = get_b64("v86.wasm")
bios_b64 = get_b64("seabios.bin")
iso_b64 = get_b64("alpine-virt-3.18.4-x86.iso")

print("2. Reading the JS engine...")
with open("libv86.js", "r", encoding="utf-8") as f:
    js_code = f.read()

# THE MAGIC FIX: Escaping the rogue HTML tags inside the JavaScript file
js_code = js_code.replace("</script>", "<\\/script>")

print("3. Assembling the Ultimate Frankenstein HTML...")
html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Alpine: The Final Stand</title>
    <style>
        body {{ margin: 0; background: #111; color: #0f0; font-family: monospace; overflow: hidden; }}
        #terminal {{ width: 100vw; height: 100vh; }}
        #status {{ position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.8); padding: 5px; z-index: 999; }}
    </style>
</head>
<body>
    <div id="status">Step 1: Extracting payload from HTML...</div>
    <div id="terminal"></div>
    
    <script type="text/plain" id="data-wasm">{wasm_b64}</script>
    <script type="text/plain" id="data-bios">{bios_b64}</script>
    <script type="text/plain" id="data-iso">{iso_b64}</script>
    
    <script>{js_code}</script>
    
    <script>
        setTimeout(() => {{
            try {{
                if (typeof V86Starter === 'undefined') {{
                    throw new Error("V86Starter still blocked. Chrome is restricting local execution.");
                }}

                document.getElementById("status").innerText = "Step 2: Loading data into memory...";
                
                const wasm_str = document.getElementById("data-wasm").textContent;
                const bios_str = document.getElementById("data-bios").textContent;
                const iso_str = document.getElementById("data-iso").textContent;
                
                document.getElementById("status").innerText = "Step 3: Igniting Virtual Machine...";
                
                const emulator = new V86Starter({{
                    wasm_path: "data:application/wasm;base64," + wasm_str,
                    memory_size: 256 * 1024 * 1024,
                    vga_canvas: document.createElement("canvas"),
                    term_container: document.getElementById("terminal"),
                    bios: {{ url: "data:application/octet-stream;base64," + bios_str }},
                    cdrom: {{ url: "data:application/octet-stream;base64," + iso_str }},
                    autostart: true,
                }});

                emulator.add_listener("emulator-ready", () => {{
                    document.getElementById("status").style.display = "none";
                }});

            }} catch (error) {{
                document.getElementById("status").innerText = "CRASH: " + error.message;
            }}
        }}, 1500);
    </script>
</body>
</html>"""

with open("Alpine-Final-Stand.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Success! Download Alpine-Final-Stand.html and test it.")