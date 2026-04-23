import base64
import os

def get_b64(f):
    with open(f, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")

# Check if files exist first
required = ["libv86.js", "v86.wasm", "seabios.bin", "vgabios.bin", "linux4.iso"]
missing = [f for f in required if not os.path.exists(f)]

if missing:
    print(f"[!] Error: Missing files: {missing}")
    print("[!] Run your pack_vm.py first to download them.")
else:
    print("[*] All files found. Building Diagnostic index.html...")

    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ChromeVM - Diagnostic Boot</title>
    <style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 20px; }
        #terminal { border: 1px solid #333; background: #000; display: inline-block; min-width: 640px; min-height: 400px; }
        #status_log { border-left: 2px solid #0a0; padding-left: 10px; margin-bottom: 20px; color: #0a0; font-size: 13px; height: 150px; overflow-y: auto; }
        .err { color: #f55; }
        .success { color: #5f5; font-weight: bold; }
    </style>
</head>
<body>
    <div id="status_log">Ready to inject...</div>
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
                report("STEP 1: Creating Engine Blob...");
                const engineBlob = new Blob([window.atob("[[ENGINE_B64]]")], {type: 'text/javascript'});
                const engineUrl = URL.createObjectURL(engineBlob);
                
                report("STEP 2: Injecting Script Tag...");
                const script = document.createElement('script');
                script.src = engineUrl;
                
                script.onload = async () => {
                    report("STEP 3: Engine script verified in RAM.", "success");
                    
                    try {
                        report("STEP 4: Decoding 12MB ISO + BIOS...");
                        const wasm = decode("[[WASM]]");
                        const bios = decode("[[BIOS]]");
                        const vga = decode("[[VGA]]");
                        const iso = decode("[[ISO]]");

                        report("STEP 5: Initializing V86Starter Instance...");
                        window.emulator = new V86Starter({
                            wasm_fn: async (i) => {
                                report("STEP 6: WASM Request Received.");
                                try {
                                    const { instance } = await WebAssembly.instantiate(wasm, i);
                                    report("STEP 7: WASM Instantiated Successfully!", "success");
                                    return instance.exports;
                                } catch (e) {
                                    report("WASM CRASH: " + e.message, "err");
                                }
                            },
                            memory_size: 64 * 1024 * 1024,
                            screen_container: document.getElementById("terminal"),
                            bios: { buffer: bios },
                            vga_bios: { buffer: vga },
                            cdrom: { buffer: iso },
                            autostart: true
                        });

                        report("STEP 8: Handing control to Emulator...", "success");
                        
                        setTimeout(() => {
                            if (logBox.innerText.includes("Step 8")) {
                                report("STEP 9: Manual screen wake-up triggered.");
                                if(window.emulator.screen_adapter) {
                                    window.emulator.screen_adapter.render_text_screen();
                                }
                            }
                        }, 5000);

                    } catch (inner) {
                        report("INIT ERROR: " + inner.message, "err");
                    }
                };

                script.onerror = () => report("ERR: Browser blocked script execution.", "err");
                document.body.appendChild(script);

            } catch (e) {
                report("FATAL: " + e.message, "err");
            }
        }

        window.onload = startVM;
    </script>
</body>
</html>"""

    # These must be aligned exactly with the 'if' block
    final_output = html_template.replace("[[ENGINE_B64]]", get_b64("libv86.js"))
    final_output = final_output.replace("[[WASM]]", get_b64("v86.wasm"))
    final_output = final_output.replace("[[BIOS]]", get_b64("seabios.bin"))
    final_output = final_output.replace("[[VGA]]", get_b64("vgabios.bin"))
    final_output = final_output.replace("[[ISO]]", get_b64("linux4.iso"))

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_output)
    
    print("[SUCCESS] index.html updated with Debugger. Push to GitHub and check Step numbers!")