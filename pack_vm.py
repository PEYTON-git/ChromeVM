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
            print(f"[*] Downloading {f}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as r, open(f, 'wb') as out: out.write(r.read())

    print("[*] Reading Engine...")
    with open("libv86.js", "r", encoding="utf-8") as f:
        # We ONLY escape the closing script tag. No other modifications.
        engine_raw = f.read().replace("</script>", "<\\/script>")

    wasm_b64 = get_b64("v86.wasm")
    bios_b64 = get_b64("seabios.bin")
    vga_b64 = get_b64("vgabios.bin")
    iso_b64 = get_b64("linux4.iso")

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Linux VM (Linear)</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; }
        #screen_container { border: 1px solid #333; display: inline-block; background: #000; }
        .status { color: #555; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div id="status" class="status">System: Initializing Linear Boot...</div>
    <div id="screen_container">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display:none"></canvas>
    </div>

    <script>
        [[ENGINE_RAW]]
    </script>

    <script>
        const status = document.getElementById("status");
        
        function decode(b64) {
            const str = window.atob(b64);
            const buf = new Uint8Array(str.length);
            for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
            return buf.buffer;
        }

        async function boot() {
            try {
                status.innerText = "Status: Verifying V86Starter...";
                if (typeof V86Starter === 'undefined') {
                    throw new Error("Engine failed to register. The browser likely blocked the internal script.");
                }

                status.innerText = "Status: Decoding WASM...";
                const wasm = decode("[[WASM]]");
                
                status.innerText = "Status: Decoding BIOS/ISO (35MB)...";
                const bios = decode("[[BIOS]]");
                const vga = decode("[[VGA]]");
                const iso = decode("[[ISO]]");

                status.innerText = "Status: Ignition...";
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
                    autostart: true
                });
                
                status.style.display = "none";
            } catch (e) {
                status.style.color = "red";
                status.innerText = "FATAL ERROR: " + e.message;
                console.error(e);
            }
        }

        // Run immediately
        boot();
    </script>
</body>
</html>
"""
    
    # Using replace instead of f-string to be safe
    final = html_template.replace("[[ENGINE_RAW]]", engine_raw)
    final = final.replace("[[WASM]]", wasm_b64)
    final = final.replace("[[BIOS]]", bios_b64)
    final = final.replace("[[VGA]]", vga_b64)
    final = final.replace("[[ISO]]", iso_b64)

    with open("linux_linear.html", "w", encoding="utf-8") as f:
        f.write(final)
    print("[OK] Created linux_linear.html")

if __name__ == "__main__":
    main()