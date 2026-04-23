import base64
import os
import urllib.request

# Configuration
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
            print(f"[!] {name} exists. Skipping download.")
            continue
        print(f"[*] Downloading {name}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                with open(name, 'wb') as f: f.write(resp.read())
            print(f"[OK] Saved {name}")
        except Exception as e:
            print(f"[ERR] Failed to download {name}: {e}")

def get_b64_and_anchor(f):
    """Reads file and adds a global anchor to the JS engine if necessary."""
    with open(f, "rb") as file:
        data = file.read()
    
    # If it's the engine, we append a line to FORCE it into the window object
    if f == "libv86.js":
        print("[*] Applying Global Anchor Patch to libv86.js...")
        anchor = b"\nwindow.V86Starter = typeof V86Starter !== 'undefined' ? V86Starter : this.V86Starter;"
        data = data + anchor
        
    return base64.b64encode(data).decode("utf-8")

def main():
    fetch_files()
    
    # Verify we have everything
    if not all(os.path.exists(f) for f in FILES):
        print("\n[FAIL] Missing files! Ensure your internet is working.")
        return

    print("\n[*] Assembling Diagnostic index.html...")

    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ChromeVM - Diagnostic</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; overflow-x: hidden; }
        #terminal { border: 1px solid #333; background: #000; display: inline-block; min-width: 640px; min-height: 400px; }
        #status_log { border-left: 2px solid #0a0; padding-left: 10px; margin-bottom: 20px; color: #0a0; font-size: 13px; height: 160px; overflow-y: auto; background: #050505; }
        .err { color: #f55; font-weight: bold; }
        .success { color: #5f5; font-weight: bold; }
        .step { color: #888; }
    </style>
</head>
<body>
    <div id="status_log">Ready for Injection Sequence...</div>
    <div id="terminal">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display:none"></canvas>
    </div>

    <script>
        const logBox = document.getElementById("status_log");
        function report(msg, type='') {
            const time = new Date().toLocaleTimeString().split(' ')[0];
            logBox.innerHTML += `<br>[${time}] <span class="${type}">${msg}</span>`;
            logBox.scrollTop = logBox.scrollHeight;
            console.log(msg);
        }

        function decode(b64) {
            const str = window.atob(b64);
            const buf = new Uint8Array(str.length);
            for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
            return buf.buffer;
        }

        async function startVM() {
            try {
                report("STEP 1: Encoding Engine to Blob...", "step");
                const engineCode = window.atob("[[ENGINE_B64]]");
                const engineBlob = new Blob([engineCode], {type: 'text/javascript'});
                const engineUrl = URL.createObjectURL(engineBlob);
                
                report("STEP 2: Injecting Ghost Script Tag...", "step");
                const script = document.createElement('script');
                script.src = engineUrl;
                
                script.onload = async () => {
                    report("STEP 3: Engine script active in browser.", "success");
                    
                    // Attempt to locate the engine across all possible scopes
                    const V86 = window.V86Starter || V86Starter || self.V86Starter;

                    if (!V86) {
                        report("FATAL ERROR: V86Starter is still hidden. The anchor patch failed to leak the variable.", "err");
                        return;
                    }

                    try {
                        report("STEP 4: Decoding 12MB Linux Assets...", "step");
                        const wasm = decode("[[WASM]]");
                        const bios = decode("[[BIOS]]");
                        const vga = decode("[[VGA]]");
                        const iso = decode("[[ISO]]");

                        report("STEP 5: Initializing Emulator Instance...", "step");
                        window.emulator = new V86({
                            wasm_fn: async (i) => {
                                report("STEP 6: WebAssembly Handshake Started...", "step");
                                try {
                                    const { instance } = await WebAssembly.instantiate(wasm, i);
                                    report("STEP 7: WASM KERNEL LIVE!", "success");
                                    return instance.exports;
                                } catch (e) {
                                    report("WASM COMPILE ERROR: " + e.message, "err");
                                }
                            },
                            memory_size: 64 * 1024 * 1024,
                            screen_container: document.getElementById("terminal"),
                            bios: { buffer: bios },
                            vga_bios: { buffer: vga },
                            cdrom: { buffer: iso },
                            autostart: true
                        });

                        report("STEP 8: Control handed to BIOS.", "success");
                        report("--- BOOTING LINUX ---", "success");

                    } catch (inner) {
                        report("INITIALIZATION FAILED: " + inner.message, "err");
                    }
                };

                script.onerror = () => report("SECURITY BLOCK: Browser killed the script injection.", "err");
                document.body.appendChild(script);

            } catch (e) {
                report("BOOTSTRAP ERROR: " + e.message, "err");
            }
        }

        window.onload = startVM;
    </script>
</body>
</html>"""

    # Final Stitching
    print("[*] Stitching Base64 strings (this may take a moment)...")
    final_output = html_template.replace("[[ENGINE_B64]]", get_b64_and_anchor("libv86.js"))
    final_output = final_output.replace("[[WASM]]", get_b64_and_anchor("v86.wasm"))
    final_output = final_output.replace("[[BIOS]]", get_b64_and_anchor("seabios.bin"))
    final_output = final_output.replace("[[VGA]]", get_b64_and_anchor("vgabios.bin"))
    final_output = final_output.replace("[[ISO]]", get_b64_and_anchor("linux4.iso"))

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_output)
    
    print("\n[SUCCESS] index.html is ready. Push to GitHub and check Step 3!")

if __name__ == "__main__":
    main()