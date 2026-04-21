import base64
import json
import os

# 1. Verify the engine actually downloaded correctly
js_size = os.path.getsize("libv86.js")
print(f"libv86.js file size: {js_size} bytes")
if js_size < 100000:
    print("CRITICAL ERROR: libv86.js is too small! The download failed.")
    print("Stop here and re-download the files.")
    exit()

def get_b64(filename):
    print(f"Encoding {filename}...")
    with open(filename, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

wasm_b64 = get_b64("v86.wasm")
bios_b64 = get_b64("seabios.bin")
iso_b64 = get_b64("alpine-virt-3.18.4-x86.iso")

print("Reading and neutralizing the JS engine...")
with open("libv86.js", "r", encoding="utf-8") as f:
    raw_js = f.read()

# THE NUKE: This wraps the entire file in safe quotes and escapes every dangerous character.
# Chrome's HTML parser won't trip over a single line of this.
safe_js_string = json.dumps(raw_js)

print("Building the un-crashable HTML...")
html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Alpine: Unstoppable Edition</title>
    <style>
        body {{ margin: 0; background: #000; color: #0f0; font-family: monospace; overflow: hidden; }}
        #screen {{ width: 100vw; height: 100vh; }}
        #status {{ position: fixed; top: 10px; left: 10px; background: #111; padding: 10px; z-index: 100; border: 1px solid #0f0; }}
    </style>
</head>
<body>
    <div id="status">Step 1: Injecting Engine via Memory...</div>
    <div id="screen"></div>
    
    <script type="text/plain" id="wasm-data">{wasm_b64}</script>
    <script type="text/plain" id="bios-data">{bios_b64}</script>
    <script type="text/plain" id="iso-data">{iso_b64}</script>

    <script>
        try {{
            // Load the perfectly safe JSON string
            const engineCode = {safe_js_string};
            
            // Create a brand new script tag in the browser's brain
            const scriptTag = document.createElement("script");
            scriptTag.textContent = engineCode;
            
            // Force the browser to run it
            document.head.appendChild(scriptTag);
            
            document.getElementById("status").innerText = "Step 2: Engine Injected. Waiting for boot...";
        }} catch(e) {{
            document.getElementById("status").innerText = "INJECTION CRASH: " + e.message;
        }}
    </script>

    <script>
        window.onload = () => {{
            setTimeout(() => {{
                try {{
                    if (typeof V86Starter === 'undefined') {{
                        throw new Error("V86Starter is STILL not defined. ChromeOS might be blocking WebAssembly completely.");
                    }}

                    document.getElementById("status").innerText = "Step 3: Booting Alpine Linux...";
                    
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
                        document.getElementById("status").style.display = "none";
                    }});
                }} catch (e) {{
                    document.getElementById("status").innerText = "CRASH: " + e.message;
                }}
            }}, 1000); // 1 second delay
        }};
    </script>
</body>
</html>"""

with open("Alpine-Unstoppable.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Done! Download Alpine-Unstoppable.html")