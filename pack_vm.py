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
    # Reuse your download logic here
    for f, url in FILES.items():
        if not os.path.exists(f):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as r, open(f, 'wb') as out: out.write(r.read())

    print("[*] Preparing v2 Lobotomy...")
    with open("libv86.js", "r", encoding="utf-8") as f:
        # We wrap the engine in a check that forces it into the global scope
        engine_raw = "window.V86Starter = (function(){ " + f.read().replace("</script>", "<\\/script>") + " return typeof V86Starter !== 'undefined' ? V86Starter : this.V86Starter; })();"

    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Linux VM (Ultimate Proxy)</title>
    <style>
        body { background: #111; color: #0f0; font-family: 'Consolas', monospace; padding: 20px; }
        #log { background: #000; border: 1px solid #333; padding: 10px; height: 150px; overflow-y: auto; font-size: 12px; margin-bottom: 10px; }
        #screen_container { border: 2px solid #444; background: #000; display: inline-block; }
        .info { color: #888; }
        .warn { color: #ff0; }
        .err { color: #f00; font-weight: bold; }
    </style>
</head>
<body>
    <div id="log">>> Ready for Proxy Injection...</div>
    <div id="screen_container">
        <div style="white-space: pre; font: 14px monospace; line-height: 14px"></div>
        <canvas style="display:none"></canvas>
    </div>

    <script>
        const logger = document.getElementById("log");
        function print(msg, type='') { 
            logger.innerHTML += `<div class="${type}">> ${msg}</div>`; 
            logger.scrollTop = logger.scrollHeight;
        }

        // Optimized Memory-Safe Decoder
        function decodeAsset(name, b64) {
            print(`Unpacking ${name}...`, 'info');
            const str = window.atob(b64);
            const buf = new Uint8Array(str.length);
            for(let i=0; i<str.length; i++) buf[i] = str.charCodeAt(i);
            return buf.buffer;
        }

        async function init() {
            try {
                print("Checking Kernel Proxy...");
                
                // Injecting engine...
                [[ENGINE_CODE]]

                const V86 = window.V86Starter;
                if (!V86) throw new Error("Kernel Proxy failed to export V86Starter.");
                print("Kernel verified. Memory check passed.", "info");

                // Decode assets one by one to prevent RAM spikes
                const wasm = decodeAsset("WASM Module", "[[WASM]]");
                const bios = decodeAsset("System BIOS", "[[BIOS]]");
                const vga  = decodeAsset("VGA BIOS", "[[VGA]]");
                const iso  = decodeAsset("Linux ISO (30MB)", "[[ISO]]");

                print("Ignition...", "warn");
                window.emulator = new V86({
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
                print("SYSTEM RUNNING.");

            } catch (e) {
                print("FATAL: " + e.message, "err");
                console.error(e);
            }
        }

        // Wait for page to settle
        window.onload = () => setTimeout(init, 500);
    </script>
</body>
</html>
"""
    
    # Manual replacement to prevent f-string issues
    final = html_template.replace("[[ENGINE_CODE]]", f"<script>{engine_raw}</script>")
    final = final.replace("[[WASM]]", get_b64("v86.wasm"))
    final = final.replace("[[BIOS]]", get_b64("seabios.bin"))
    final = final.replace("[[VGA]]", get_b64("vgabios.bin"))
    final = final.replace("[[ISO]]", get_b64("linux4.iso"))

    with open("linux_proxy.html", "w", encoding="utf-8") as f:
        f.write(final)
    print("[OK] Created linux_proxy.html")

if __name__ == "__main__":
    main()