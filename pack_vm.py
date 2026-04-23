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

def get_b64(f):
    with open(f, "rb") as file: return base64.b64encode(file.read()).decode("utf-8")

def main():
    for f, url in FILES.items():
        if not os.path.exists(f):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as r, open(f, 'wb') as out: out.write(r.read())

    # Encode the engine so it's invisible to the initial page scan
    engine_b64 = get_b64("libv86.js")
    
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Linux VM (Worker Escape)</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; }
        #log { color: #444; font-size: 12px; margin-bottom: 10px; }
        #screen_container { border: 1px solid #222; display: inline-block; }
    </style>
</head>
<body>
    <div id="log">>> Initializing Stealth Boot...</div>
    <div id="screen_container">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display:none"></canvas>
    </div>

    <script>
        const logger = document.getElementById("log");
        const print = (m) => logger.innerText = "Status: " + m;

        function decode(b64) {
            const str = window.atob(b64);
            const buf = new Uint8Array(str.length);
            for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
            return buf.buffer;
        }

        async function launch() {
            try {
                print("Deploying Worker Shadow...");
                
                // We turn the engine into a Blob and then a URL
                const engineBlob = new Blob([window.atob("[[ENGINE_B64]]")], {type: 'text/javascript'});
                const engineUrl = URL.createObjectURL(engineBlob);

                // We inject a script tag that points to the BLOB URL
                // This often bypasses inline-script blocks because the source is an "external" blob
                const script = document.createElement('script');
                script.src = engineUrl;
                
                script.onload = async () => {
                    print("Kernel Bridge Established. Decoding Assets...");
                    
                    const wasm = decode("[[WASM]]");
                    const bios = decode("[[BIOS]]");
                    const vga = decode("[[VGA]]");
                    const iso = decode("[[ISO]]");

                    print("Igniting...");
                    new V86Starter({
                        wasm_fn: async (i) => {
                            const { instance } = await WebAssembly.instantiate(wasm, i);
                            return instance.exports;
                        },
                        memory_size: 128 * 1024 * 1024,
                        screen_container: document.getElementById("screen_container"),
                        bios: { buffer: bios },
                        vga_bios: { buffer: vga },
                        cdrom: { buffer: iso },
                        autostart: true
                    });
                    print("Running.");
                };

                script.onerror = () => { print("Shadow Injection Blocked."); };
                document.body.appendChild(script);

            } catch (e) {
                print("FATAL: " + e.message);
            }
        }

        launch();
    </script>
</body>
</html>
"""
    
    final = html_template.replace("[[ENGINE_B64]]", engine_b64)
    final = final.replace("[[WASM]]", get_b64("v86.wasm"))
    final = final.replace("[[BIOS]]", get_b64("seabios.bin"))
    final = final.replace("[[VGA]]", get_b64("vgabios.bin"))
    final = final.replace("[[ISO]]", get_b64("linux4.iso"))

    with open("linux_stealth.html", "w", encoding="utf-8") as f:
        f.write(final)
    print("[OK] Created linux_stealth.html")

main()