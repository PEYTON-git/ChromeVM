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
    
    print("[*] Reading Engine (No interference)...")
    with open("libv86.js", "r", encoding="utf-8") as f:
        # We ONLY escape the closing script tag. Nothing else.
        engine_raw = f.read().replace("</script>", "<\\/script>")

    wasm_b64 = get_b64("v86.wasm")
    bios_b64 = get_b64("seabios.bin")
    vga_b64 = get_b64("vgabios.bin")
    iso_b64 = get_b64("linux4.iso")

    # We use a standard string template to avoid f-string brace corruption
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Linux VM (Zero-Interference)</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; text-align: center; }
        #screen_container { border: 2px solid #222; display: inline-block; margin-top: 20px; background: #000; }
        #log { color: #555; font-size: 14px; text-align: left; max-width: 640px; margin: 0 auto; border-left: 2px solid #333; padding-left: 10px; }
        .err { color: #f44; }
    </style>
</head>
<body>
    <h3>V86 OFFLINE BOOTSTRAP</h3>
    <div id="log">System: Ready.</div>
    
    <div id="screen_container">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display:none"></canvas>
    </div>

    <script type="text/javascript">
        try {
            [[ENGINE_CODE]]
            window.engineLoaded = true;
        } catch (e) {
            window.engineError = e.message;
            window.engineStack = e.stack;
        }
    </script>

    <script>
        const logger = document.getElementById("log");
        function print(msg, isError = false) {
            logger.innerHTML += `<br><span class="${isError ? 'err' : ''}">> ${msg}</span>`;
        }

        function decode(b64) {
            const str = window.atob(b64);
            const buf = new Uint8Array(str.length);
            for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
            return buf.buffer;
        }

        async function boot() {
            if (!window.engineLoaded) {
                print("FATAL: Engine failed to parse.", true);
                print("Error: " + (window.engineError || "Security Sandbox Active"), true);
                return;
            }

            try {
                print("Environment: WebAssembly check...");
                if (typeof WebAssembly !== "object") throw new Error("WASM disabled.");

                print("Storage: Decoding 32MB assets...");
                const wasm = decode("[[WASM]]");
                const bios = decode("[[BIOS]]");
                const vga = decode("[[VGA]]");
                const iso = decode("[[ISO]]");

                print("Kernel: Starting emulator core...");
                window.emulator = new V86Starter({
                    wasm_fn: async (i) => {
                        const res = await WebAssembly.instantiate(wasm, i);
                        return res.instance.exports;
                    },
                    memory_size: 128 * 1024 * 1024,
                    vga_memory_size: 8 * 1024 * 1024,
                    screen_container: document.getElementById("screen_container"),
                    bios: { buffer: bios },
                    vga_bios: { buffer: vga },
                    cdrom: { buffer: iso },
                    autostart: true
                });

                print("Success: VM Running.");
                logger.style.color = "#0a0";
            } catch (err) {
                print("RUNTIME ERROR: " + err.message, true);
                console.error(err);
            }
        }
        
        // Short delay to ensure DOM is fully painted
        setTimeout(boot, 100);
    </script>
</body>
</html>
"""
    
    # Manually stitch the strings together to avoid any Python string formatting bugs
    final_html = html_template.replace("[[ENGINE_CODE]]", engine_raw)
    final_html = final_html.replace("[[WASM]]", wasm_b64)
    final_html = final_html.replace("[[BIOS]]", bios_b64)
    final_html = final_html.replace("[[VGA]]", vga_b64)
    final_html = final_html.replace("[[ISO]]", iso_b64)

    with open("linux_zero.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("\n[OK] Created linux_zero.html")
    print("[*] Move this to your Downloads folder and try again.")

if __name__ == "__main__":
    main()