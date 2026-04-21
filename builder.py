import base64

# The ISO file you downloaded
iso_file = "alpine-virt-3.18.4-x86.iso"

html_part1 = """<!DOCTYPE html>
<html>
<head>
    <title>Alpine Linux Offline</title>
    <style>
        body { margin: 0; background: #000; color: #0f0; font-family: monospace; overflow: hidden; }
        #screen { width: 100vw; height: 100vh; }
    </style>
</head>
<body>
    <div id="screen">Loading Alpine Linux...</div>
    <script src="https://copy.sh/v86/build/libv86.js"></script>
    <script>
        const ISO_DATA = \""""

html_part2 = """\";
        const emulator = new V86Starter({
            wasm_path: "https://copy.sh/v86/build/v86.wasm",
            memory_size: 256 * 1024 * 1024,
            vga_canvas: document.createElement("canvas"),
            term_container: document.getElementById("screen"),
            bios: { url: "https://copy.sh/v86/bios/seabios.bin" },
            cdrom: { url: "data:application/octet-stream;base64," + ISO_DATA },
            autostart: true,
        });
    </script>
</body>
</html>"""

print("Reading ISO and converting to Base64 (this takes about 5 seconds)...")
with open(iso_file, "rb") as f:
    # This reads the binary and safely formats it as a single line of text
    b64_string = base64.b64encode(f.read()).decode('utf-8')

print("Stitching the HTML file together...")
with open("AlpineOS-Offline.html", "w") as f:
    f.write(html_part1)
    f.write(b64_string)
    f.write(html_part2)

print("Success! Your single-file OS is ready to download.")