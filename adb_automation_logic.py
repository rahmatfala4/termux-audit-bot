import subprocess

# Variabel Global untuk status koneksi ADB.
# Dalam aplikasi nyata, ini akan diatur ke True setelah adb connect berhasil.
IS_ADB_CONNECTED = True 

def run_adb_command(command_parts):
    """
    Menjalankan perintah ADB shell dan menangani output/error.
    
    Args:
        command_parts (list): Daftar bagian perintah, misalnya: ['adb', 'shell', 'input', 'tap', '500', '1000']
    
    Returns:
        str: Output atau pesan error dari perintah ADB.
    """
    if not IS_ADB_CONNECTED:
        return "Error: ADB tidak terhubung. Silakan jalankan 'adb connect IP:PORT' terlebih dahulu."
    
    try:
        # Menjalankan perintah ADB. Menggunakan shell=False (disarankan untuk keamanan)
        # tetapi memerlukan daftar command_parts yang terpisah.
        result = subprocess.run(
            command_parts,
            check=True,  # Akan menaikkan CalledProcessError jika kode keluar non-nol
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10 # Timeout setelah 10 detik
        )
        
        # Output sukses
        return result.stdout.strip()
    
    except subprocess.CalledProcessError as e:
        # Perintah ADB gagal (misalnya, device offline, error syntax shell)
        error_output = e.stderr.strip() or e.stdout.strip()
        return f"ADB Command Failed (Exit Code {e.returncode}): {error_output}"
    
    except subprocess.TimeoutExpired:
        return "Error: Perintah ADB timeout setelah 10 detik."
    except FileNotFoundError:
        return "Error: Perintah 'adb' tidak ditemukan. Pastikan android-tools terinstal."
    except Exception as e:
        return f"Error Tidak Terduga: {e}"

def check_device_status():
    """Mengecek apakah perangkat terhubung."""
    status = run_adb_command(['adb', 'devices'])
    if "device" in status:
        return f"Status: Sukses. {status.splitlines()[1].strip()}"
    return status

def simulate_tap(x, y):
    """Mensimulasikan tap pada koordinat layar."""
    print(f"Mengirim tap ke ({x}, {y})...")
    # Perintah adb shell input tap X Y
    command = ['adb', 'shell', 'input', 'tap', str(x), str(y)]
    return run_adb_command(command)

def get_screen_resolution():
    """Mendapatkan resolusi layar perangkat."""
    # Perintah adb shell wm size
    output = run_adb_command(['adb', 'shell', 'wm', 'size'])
    if output.startswith("Physical size:"):
        return output.replace("Physical size: ", "").strip()
    return f"Gagal mendapatkan resolusi: {output}"

# --- Contoh Penggunaan (Setel IS_ADB_CONNECTED = True untuk mengujinya) ---

# Anda akan memanggil fungsi ini dari rute Flask di web_server.py
# Contoh 1: Cek status koneksi
# print(check_device_status())

# Contoh 2: Dapatkan resolusi
# print(get_screen_resolution())

# Contoh 3: Tap di tengah layar (misalnya resolusi 1080x2400)
# print(simulate_tap(540, 1200))
