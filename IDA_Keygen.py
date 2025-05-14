import ctypes
import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timedelta
from tkinter import PhotoImage, filedialog

import customtkinter as ctk

now = datetime.now()
now_str = now.strftime("%Y-%m-%d %H:%M:%S")
end_str = (now + timedelta(days=365 * 10)).strftime("%Y-%m-%d %H:%M:%S")

try:
    import win32api
except ImportError:
    win32api = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class CustomDialog:
    def __init__(self, parent, title, message):
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        try:
            if platform.system() == "Windows":
                icon_path = "icon.ico"
                if os.path.exists(icon_path):
                    self.dialog.iconbitmap(icon_path)
            else:
                icon_path = "icon.png"
                if os.path.exists(icon_path):
                    icon = PhotoImage(file=icon_path)
                    self.dialog.iconphoto(True, icon)
        except Exception as e:
            print(f"Failed to set icon: {e}")

        label = ctk.CTkLabel(self.dialog, text=message, wraplength=350)
        label.pack(pady=20)

        btn = ctk.CTkButton(self.dialog, text="OK", command=self.dialog.destroy)
        btn.pack(pady=10)

        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

def json_stringify_alphabetical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

def buf_to_bigint(buf):
    return int.from_bytes(buf, byteorder="little")

def bigint_to_buf(i):
    return i.to_bytes((i.bit_length() + 7) // 8, byteorder="little")

pub_modulus_patched = buf_to_bigint(
    bytes.fromhex(
        "edfd42cbf978546e8911225884436c57140525650bcf6ebfe80edbc5fb1de68f4c66c29cb22eb668788afcb0abbb718044584b810f8970cddf227385f75d5dddd91d4f18937a08aa83b28c49d12dc92e7505bb38809e91bd0fbd2f2e6ab1d2e33c0c55d5bddd478ee8bf845fcef3c82b9d2929ecb71f4d1b3db96e3a8e7aaf93"
    )
)
private_key = buf_to_bigint(
    bytes.fromhex(
        "77c86abbb7f3bb134436797b68ff47beb1a5457816608dbfb72641814dd464dd640d711d5732d3017a1c4e63d835822f00a4eab619a2c4791cf33f9f57f9c2ae4d9eed9981e79ac9b8f8a411f68f25b9f0c05d04d11e22a3a0d8d4672b56a61f1532282ff4e4e74759e832b70e98b9d102d07e9fb9ba8d15810b144970029874"
    )
)
exponent = 0x13

def encrypt(message):
    encrypted = pow(buf_to_bigint(message[::-1]), private_key, pub_modulus_patched)
    return bigint_to_buf(encrypted)

def sign_hexlic(payload: dict) -> str:
    data = {"payload": payload}
    data_str = json_stringify_alphabetical(data)
    buffer = bytearray(128)
    for i in range(33):
        buffer[i] = 0x42
    sha256 = hashlib.sha256()
    sha256.update(data_str.encode())
    digest = sha256.digest()
    for i in range(32):
        buffer[33 + i] = digest[i]
    encrypted = encrypt(buffer)
    return encrypted.hex().upper()

def add_every_addon(license):
    addons = [
        "HEXX86", "HEXX64", "HEXARM", "HEXARM64", "HEXMIPS", "HEXMIPS64",
        "HEXPPC", "HEXPPC64", "HEXRV64", "HEXARC", "HEXARC64",
        
        # Probably cloud?
        "HEXCX86",
        "HEXCX64",
        "HEXCARM",
        "HEXCARM64",
        "HEXCMIPS",
        "HEXCMIPS64",
        "HEXCPPC",
        "HEXCPPC64",
        "HEXCRV",
        "HEXCRV64",
        "HEXCARC",
        "HEXCARC64",
        "LUMINA",
        "TEAMS"
    ]

    for i, addon in enumerate(addons, 1):
        license["payload"]["licenses"][0]["add_ons"].append(
            {
                "id": f"48-2137-ACAB-{i:02}",
                "code": addon,
                "owner": license["payload"]["licenses"][0]["id"],
                "start_date": now_str,
                "end_date": end_str,
            }
        )

def generate_patched_dll(filename, status_text):
    if not os.path.exists(filename):
        status_text.insert("end", f"Didn't find {filename}, skipping patch generation\n")
        return
    with open(filename, "rb") as f:
        data = f.read()
        if data.find(bytes.fromhex("EDFD42CBF978")) != -1:
            status_text.insert("end", f"{filename} looks to be already patched :)\n")
            return
        if data.find(bytes.fromhex("EDFD425CF978")) == -1:
            status_text.insert("end", f"{filename} doesn't contain the original modulus.\n")
            return
        data = data.replace(
            bytes.fromhex("EDFD425CF978"), bytes.fromhex("EDFD42CBF978")
        )
        backup_filename = f"{filename}.bak"
        os.rename(filename, backup_filename)
        with open(filename, "wb") as f:
            f.write(data)
        status_text.insert("end", f"Patched {filename} successfully! Original file backed up as {backup_filename}\n")

class KeygenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IDA Pro License Generator")
        self.root.geometry("600x550")
        self.root.resizable(False, False)
        
        try:
            if platform.system() == "Windows":
                icon_path = "icon.ico"
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
            else:
                icon_path = "icon.png"
                if os.path.exists(icon_path):
                    icon = PhotoImage(file=icon_path)
                    self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"Failed to set icon: {e}")

        self.required_files = [
            "ida32.dll", "ida64.dll", "ida.dll",
            "libida32.so", "libida64.so", "libida.so",
            "libida32.dylib", "libida.dylib", "libida64.dylib"
        ]

        self.label_folder = ctk.CTkLabel(root, text="IDA Pro Installation Folder:")
        self.label_folder.pack(pady=5)
        self.entry_folder = ctk.CTkEntry(root, width=400)
        self.entry_folder.insert(0, os.getcwd())
        self.entry_folder.pack(pady=5)
        self.btn_browse = ctk.CTkButton(root, text="Browse", command=self.browse_folder)
        self.btn_browse.pack(pady=5)

        self.label_name = ctk.CTkLabel(root, text="Name:")
        self.label_name.pack(pady=5)
        self.entry_name = ctk.CTkEntry(root, width=300)
        self.entry_name.insert(0, "decryptable")
        self.entry_name.pack()

        self.label_email = ctk.CTkLabel(root, text="Email:")
        self.label_email.pack(pady=5)
        self.entry_email = ctk.CTkEntry(root, width=300)
        self.entry_email.insert(0, "hack@decryptable.dev")
        self.entry_email.pack()

        self.btn_generate = ctk.CTkButton(root, text="Generate License", command=self.generate_license)
        self.btn_generate.pack(pady=10)

        self.btn_patch = ctk.CTkButton(root, text="Patch IDA Pro", command=self.patch_files)
        self.btn_patch.pack(pady=5)

        self.btn_about = ctk.CTkButton(root, text="About", command=self.show_about)
        self.btn_about.pack(pady=5)

        self.status_text = ctk.CTkTextbox(root, width=500, height=200)
        self.status_text.pack(pady=10)

        self.check_admin_and_directory()

    def show_about(self):
        about_message = (
            "IDA Pro License Generator\n"
            "-------------------------\n"
            "Author: decryptable\n"
            "Contact: https://t.me/hexac\n\n"
            "Keygen for IDA Pro version 9 and above. Works on 9.0 properly. "
            "But it hasn't been tested in version 9.1 and above."
        )
        CustomDialog(self.root, "About", about_message)

    def check_admin_and_directory(self):
        if platform.system() == "Windows":
            try:
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    CustomDialog(
                        self.root,
                        "Administrator Required",
                        "This program requires administrator privileges to run on Windows. Please run as administrator."
                    )
                    self.disable_inputs()
                    return
            except:
                CustomDialog(
                    self.root,
                    "Permission Error",
                    "Unable to verify administrator privileges. Please run as administrator."
                )
                self.disable_inputs()
                return

        self.check_directory()

    def get_file_version(self, filepath):
        if platform.system() == "Windows" and win32api:
            try:
                info = win32api.GetFileVersionInfo(filepath, "\\")
                version = f"{info['FileVersionMS'] >> 16}.{info['FileVersionMS'] & 0xFFFF}"
                return version
            except:
                return None
        elif platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["otool", "-l", filepath], capture_output=True, text=True
                )
                if "version" in result.stdout:
                    for line in result.stdout.splitlines():
                        if "version" in line:
                            parts = line.strip().split()
                            if len(parts) > 1 and parts[1].startswith("9.0"):
                                return parts[1]
                return None
            except:
                return None
        else:
            try:
                result = subprocess.run(
                    ["file", filepath], capture_output=True, text=True
                )
                if "version" in result.stdout.lower():
                    for line in result.stdout.splitlines():
                        if "9.0" in line:
                            return "9.0"
                return None
            except:
                return None

    def check_directory(self):
        folder = self.entry_folder.get()
        ida_exe = "ida.exe" if platform.system() == "Windows" else "ida"
        ida64_exe = "ida64.exe" if platform.system() == "Windows" else "ida64"
        ida_path = os.path.join(folder, ida_exe)
        ida64_path = os.path.join(folder, ida64_exe)

        if not os.path.exists(ida_path) and not os.path.exists(ida64_path):
            CustomDialog(
                self.root,
                "Invalid Directory",
                f"No '{ida_exe}' or '{ida64_exe}' found in the specified folder. Please select a valid IDA Pro 9.0 installation folder."
            )
            self.disable_inputs()
            return

        version_ida = self.get_file_version(ida_path) if os.path.exists(ida_path) else None
        version_ida64 = self.get_file_version(ida64_path) if os.path.exists(ida64_path) else None

        if (version_ida and "9.0" not in version_ida) and (version_ida64 and "9.0" not in version_ida64):
            CustomDialog(
                self.root,
                "Invalid Version",
                f"Neither '{ida_exe}' nor '{ida64_exe}' has a valid version (9.0 required). "
                f"Found versions: {version_ida or 'Unknown'} (ida), {version_ida64 or 'Unknown'} (ida64)."
            )
            self.disable_inputs()
            return

        if not any(os.path.exists(os.path.join(folder, f)) for f in self.required_files):
            CustomDialog(
                self.root,
                "Invalid Directory",
                "No IDA Pro library files (.dll, .so, .dylib) found. Please select a valid IDA Pro 9.0 installation folder."
            )
            self.disable_inputs()
            return

        self.enable_inputs()

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select IDA Pro Installation Folder")
        if folder:
            self.entry_folder.delete(0, "end")
            self.entry_folder.insert(0, folder)
            self.check_directory()

    def disable_inputs(self):
        self.entry_name.configure(state="disabled")
        self.entry_email.configure(state="disabled")
        self.btn_generate.configure(state="disabled")
        self.btn_patch.configure(state="disabled")
        self.entry_folder.configure(state="normal")
        self.btn_browse.configure(state="normal")

    def enable_inputs(self):
        self.entry_name.configure(state="normal")
        self.entry_email.configure(state="normal")
        self.btn_generate.configure(state="normal")
        self.btn_patch.configure(state="normal")
        self.entry_folder.configure(state="normal")
        self.btn_browse.configure(state="normal")

    def generate_license(self):
        try:
            license = {
                "header": {"version": 1},
                "payload": {
                    "name": self.entry_name.get(),
                    "email": self.entry_email.get(),
                    "licenses": [
                        {
                            "description": "license",
                            "edition_id": "ida-pro",
                            "id": "48-2137-ACAB-99",
                            "license_type": "named",
                            "product": "IDA",
                            "seats": 100,
                            "start_date": now_str,
                            "end_date": end_str,
                            "issued_on": now_str,
                            "owner": self.entry_email.get(),
                            "product_id": "IDA",
                            "add_ons": [],
                            "features": [],
                        }
                    ],
                },
            }

            add_every_addon(license)
            license["signature"] = sign_hexlic(license["payload"])
            serialized = json_stringify_alphabetical(license)

            filename = os.path.join(self.entry_folder.get(), "idapro.hexlic")
            with open(filename, "w") as f:
                f.write(serialized)

            license_info = license["payload"]["licenses"][0]
            addons = ", ".join(addon["code"] for addon in license_info["add_ons"])
            readable_output = (
                f"License Generated Successfully!\n"
                f"-----------------------------\n"
                f"Saved to: {filename}\n\n"
                f"Licensee Information:\n"
                f"  Name: {license['payload']['name']}\n"
                f"  Email: {license['payload']['email']}\n"
                f"  License ID: {license_info['id']}\n\n"
                f"License Details:\n"
                f"  Product: {license_info['product']} ({license_info['product_id']})\n"
                f"  Edition: {license_info['edition_id']}\n"
                f"  Type: {license_info['license_type'].capitalize()}\n"
                f"  Seats: {license_info['seats']}\n"
                f"  Issued On: {license_info['issued_on']}\n"
                f"  Start Date: {license_info['start_date']}\n"
                f"  End Date: {license_info['end_date']}\n"
                f"  Add-ons: {addons or 'None'}\n\n"
                f"Signature: {license['signature'][:50]}... (truncated)\n"
            )

            self.status_text.delete("1.0", "end")
            self.status_text.insert("end", readable_output)
        except Exception as e:
            CustomDialog(self.root, "Error", f"Failed to generate license: {str(e)}")

    def patch_files(self):
        try:
            folder = self.entry_folder.get()
            files = [
                os.path.join(folder, f) for f in self.required_files
                if os.path.isfile(os.path.join(folder, f))
            ]

            if not files:
                self.status_text.delete("1.0", "end")
                self.status_text.insert("end", "No required IDA Pro library files found in the folder.\n")
                return

            self.status_text.delete("1.0", "end")
            for file in files:
                generate_patched_dll(file, self.status_text)
        except Exception as e:
            CustomDialog(self.root, "Error", f"Failed to patch files: {str(e)}")

if __name__ == "__main__":
    root = ctk.CTk()
    app = KeygenApp(root)
    root.mainloop()