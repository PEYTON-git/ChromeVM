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
    
    # We read the engine and PREPEND the environment shield
    with open("libv86.js", "r", encoding="utf-8") as f:
        # This wrapper forces the engine to ignore any school-filter 'module' or 'define' variables
        shield_prefix = "var module=undefined;var exports=undefined;var define=undefined;"
        engine_raw = shield_prefix + f.read().replace("</script>", "<\\/script>")

    wasm_b64 = get_b64("v86.wasm")
    bios_b64 = get_b64("seabios.bin")
    vga_b64 = get_b64("vgabios.bin")
    iso_b64 = get_b64("linux4.iso")

    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Linux VM (Environment Shield)</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; }
        #screen_container { border: 1px solid #333; background: #000; display: inline-block; }
        #log { font-size: 12px; color: #0a0; border-bottom: 1px solid #222; padding-bottom: 10px; margin-bottom: 10px; height: 150px; overflow-y: auto; }
        .err { color: #f55; font-weight: bold; }
    </style>
</head>
<body>
    <div id="log">>> Shielding Environment...</div>
    <div id="screen_container">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display:none"></canvas>
    </div>

    <script>
        try {
            // Self-Executing clean room
            (function() {
                var module = undefined;
                var exports = undefined;
                var define = undefined;
                [[ENGINE_CODE]]
                // Force a manual global assignment just in case
                if (typeof V86Starter !== 'undefined') {
                    window.V86Starter = V86Starter;
                }
            })();
            window.engineLoaded = true;
        } catch (e) {
            window.engineError = e.message;
        }
    </script>

    <script>
        const logger = document.getElementById("log");
        function print(msg, isErr=false) {
            logger.innerHTML += `<br><span class="${isErr?'err':''}">> ${msg}</span>`;
            logger.scrollTop = logger.scrollHeight;
        }

        function decode(b64) {
            const str = window.atob(b64);
            const buf = new Uint8Array(str.length);
            for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
            return buf.buffer;
        }

        async function boot() {
            print("Step 1: Verifying Shielded Engine...");
            if (!window.V86Starter) {
                print("FAILED: V86Starter is still hiding. Error: " + (window.engineError || "Scoping Lockout"), true);
                return;
            }

            try {
                print("Step 2: Unpacking VM Assets...");
                const wasm = decode("[[WASM]]");
                const bios = decode("[[BIOS]]");
                const vga = decode("[[VGA]]");
                const iso = decode("[[ISO]]");

                print("Step 3: Initializing Emulator...");
                new V86Starter({
                    wasm_fn: async (i) => {
                        const res = await WebAssembly.instantiate(wasm, i);
                        return res.instance.exports;
                    },
                    memory_size: 128 * 1024 * 1024,
                    screen_container: document.getElementById("screen_container"),
                    bios: { buffer: bios },
                    vga_bios: { buffer: vga },
                    cdrom: { buffer: iso },
                    autostart: true
                });
                print("Step 4: Boot Sequence Initiated.");
            } catch (err) {
                print("RUNTIME ERROR: " + err.message, true);
            }
        }

        setTimeout(boot, 200);
    </script>
</body>
</html>
"""
    
    final_html = html_template.replace("[[ENGINE_CODE]]", engine_raw)
    final_html = final_html.replace("[[WASM]]", wasm_b64)
    final_html = final_html.replace("[[BIOS]]", bios_b64)
    final_html = final_html.replace("[[VGA]]", vga_b64)
    final_html = final_html.replace("[[ISO]]", iso_b64)

    with open("linux_shield.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("\n[OK] Created linux_shield.html")

if __name__ == "__main__":
    main()