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
    
    # We encode the engine itself as Base64 to keep it safe from the HTML parser
    engine_b64 = get_b64("libv86.js")
    wasm_b64 = get_b64("v86.wasm")
    bios_b64 = get_b64("seabios.bin")
    vga_b64 = get_b64("vgabios.bin")
    iso_b64 = get_b64("linux4.iso")

    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Linux VM (Blob-Injection)</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: 'Courier New', monospace; padding: 20px; }
        #screen_container { border: 2px solid #333; display: inline-block; background: #000; margin-top: 10px; }
        #log { color: #008f11; font-size: 13px; margin-bottom: 10px; border-left: 2px solid #008f11; padding-left: 10px; height: 120px; overflow-y: auto; }
        .err { color: #ff3e3e; }
    </style>
</head>
<body>
    <div id="log">>> Terminal Initialized...</div>
    <div id="screen_container">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display:none"></canvas>
    </div>

    <script>
        const logger = document.getElementById("log");
        function print(msg, isError = false) {
            logger.innerHTML += `<br><span class="${isError ? 'err' : ''}">[${new Date().toLocaleTimeString()}] ${msg}</span>`;
            logger.scrollTop = logger.scrollHeight;
        }

        // Convert Base64 to a Blob and create a virtual URL for it
        function createBlobUrl(b64, type) {
            const str = window.atob(b64);
            const buf = new Uint8Array(str.length);
            for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
            const blob = new Blob([buf], { type: type });
            return URL.createObjectURL(blob);
        }

        async function start() {
            try {
                print("Step 1: Injecting Virtual Engine...");
                const engineUrl = createBlobUrl("[[ENGINE_B64]]", "text/javascript");
                
                // We create a real script tag pointing to our virtual file
                const script = document.createElement("script");
                script.src = engineUrl;
                
                script.onload = async () => {
                    print("Step 2: Engine script verified.");
                    
                    if (typeof V86Starter === "undefined") {
                        print("CRITICAL: V86Starter still not found in global scope. Attempting manual fix...", true);
                        // Sometimes browsers hide it; we can try to find it in the window
                        if (window.V86Starter) { print("Manual fix: Found in window."); }
                        else { throw new Error("Engine loaded but failed to export V86Starter."); }
                    }

                    print("Step 3: Decoding Virtual Disks...");
                    const wasmBuf = await (await fetch(createBlobUrl("[[WASM]]", "application/wasm"))).arrayBuffer();
                    const biosBuf = await (await fetch(createBlobUrl("[[BIOS]]", "application/octet-stream"))).arrayBuffer();
                    const vgaBuf = await (await fetch(createBlobUrl("[[VGA]]", "application/octet-stream"))).arrayBuffer();
                    const isoBuf = await (await fetch(createBlobUrl("[[ISO]]", "application/octet-stream"))).arrayBuffer();

                    print("Step 4: Launching Kernel...");
                    window.emulator = new V86Starter({
                        wasm_fn: async (i) => {
                            const res = await WebAssembly.instantiate(wasmBuf, i);
                            return res.instance.exports;
                        },
                        memory_size: 128 * 1024 * 1024,
                        screen_container: document.getElementById("screen_container"),
                        bios: { buffer: biosBuf },
                        vga_bios: { buffer: vgaBuf },
                        cdrom: { buffer: isoBuf },
                        autostart: true
                    });
                    print("SUCCESS: VM is running.");
                };

                script.onerror = () => { throw new Error("Virtual script injection failed."); };
                document.body.appendChild(script);

            } catch (e) {
                print("FATAL ERROR: " + e.message, true);
            }
        }

        start();
    </script>
</body>
</html>
"""
    
    # Manual stitching
    final_html = html_template.replace("[[ENGINE_B64]]", engine_b64)
    final_html = final_html.replace("[[WASM]]", wasm_b64)
    final_html = final_html.replace("[[BIOS]]", bios_b64)
    final_html = final_html.replace("[[VGA]]", vga_b64)
    final_html = final_html.replace("[[ISO]]", iso_b64)

    with open("linux_blob.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("\n[OK] Created linux_blob.html")

if __name__ == "__main__":
    main()