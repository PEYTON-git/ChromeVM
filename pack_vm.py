import base64
import os
import urllib.request

# Use jsDelivr for better stability
FILES = {
    "libv86.js": "https://cdn.jsdelivr.net/npm/v86/build/libv86.js",
    "v86.wasm": "https://cdn.jsdelivr.net/npm/v86/build/v86.wasm",
    "seabios.bin": "https://raw.githubusercontent.com/copy/v86/master/bios/seabios.bin",
    "vgabios.bin": "https://raw.githubusercontent.com/copy/v86/master/bios/vgabios.bin",
    "linux4.iso": "https://copy.sh/v86/images/linux4.iso"
}

def fetch_files():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    for name, url in FILES.items():
        if os.path.exists(name):
            print(f"[!] {name} exists. Skipping.")
            continue
        print(f"[*] Downloading {name}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                with open(name, 'wb') as f: f.write(resp.read())
            print(f"[OK] Saved {name}")
        except Exception as e:
            print(f"[ERR] Failed {name}: {e}")

def get_b64(f):
    with open(f, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")

# --- START PACKAGING LOGIC ---

fetch_files()

if all(os.path.exists(f) for f in FILES):
    print("\n[+] All assets verified. Assembling index.html...")
    
    # This is your template from the previous message
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ChromeVM - Terminal</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 20px; overflow: hidden; }
        #log { color: #444; font-size: 11px; margin-bottom: 5px; height: 20px; overflow: hidden; }
        #screen_container { border: 1px solid #1a1a1a; background: #000; display: inline-block; cursor: text; }
        #screen_container canvas { display: block; vertical-align: top; }
        .hint { color: #222; font-size: 10px; margin-top: 5px; }
    </style>
</head>
<body>
    <div id="log">>> Waiting for kernel...</div>
    <div id="screen_container" onclick="this.focus()">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display:none"></canvas>
    </div>
    <div class="hint">Click screen + press ENTER if stuck. Press CTRL+ALT+R to force reboot.</div>

    <script>
        const logger = document.getElementById("log");
        const print = (m) => logger.innerText = "SYS: " + m;

        function decode(b64) {
            const str = window.atob(b64);
            const buf = new Uint8Array(str.length);
            for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
            return buf.buffer;
        }

        async function launch() {
            try {
                print("Lifting Shield...");
                const engineBlob = new Blob([window.atob("[[ENGINE_B64]]")], {type: 'text/javascript'});
                const engineUrl = URL.createObjectURL(engineBlob);

                const script = document.createElement('script');
                script.src = engineUrl;
                
                script.onload = async () => {
                    print("Kernel Hotlinked. Unpacking Assets...");
                    
                    const wasm = decode("[[WASM]]");
                    const bios = decode("[[BIOS]]");
                    const vga = decode("[[VGA]]");
                    const iso = decode("[[ISO]]");

                    print("Igniting Engine...");
                    window.emulator = new V86Starter({
                        wasm_fn: async (i) => {
                            const { instance } = await WebAssembly.instantiate(wasm, i);
                            return instance.exports;
                        },
                        memory_size: 128 * 1024 * 1024,
                        screen_container: document.getElementById("screen_container"),
                        bios: { buffer: bios },
                        vga_bios: { buffer: vga },
                        cdrom: { buffer: iso },
                        autostart: true,
                        keyboard_policy: "capture-all" 
                    });

                    setTimeout(() => {
                        if (logger.innerText.includes("Igniting")) {
                            print("Waking up display...");
                            window.emulator.screen_adapter.render_text_screen();
                        }
                    }, 5000);

                    print("VM CORE RUNNING.");
                };
                document.body.appendChild(script);
            } catch (e) {
                print("CRITICAL: " + e.message);
            }
        }
        window.onload = launch;
    </script>
</body>
</html>"""

    # Injecting the Base64 data into the template
    final_output = html_template.replace("[[ENGINE_B64]]", get_b64("libv86.js"))
    final_output = final_output.replace("[[WASM]]", get_b64("v86.wasm"))
    final_output = final_output.replace("[[BIOS]]", get_b64("seabios.bin"))
    final_output = final_output.replace("[[VGA]]", get_b64("vgabios.bin"))
    final_output = final_output.replace("[[ISO]]", get_b64("linux4.iso"))

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_output)

    print("\n[SUCCESS] Created index.html. Push this to your GitHub repo!")
else:
    print("\n[FAIL] Missing files. Cannot package.")