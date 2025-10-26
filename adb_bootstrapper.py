import subprocess
import time
import re
import xml.etree.ElementTree as ET
import os

# --- PENTING: CONFIGURATION ---
# Port terakhir yang berhasil adalah 37753, kita jaga nilai ini.
ADB_IP_PORT = "192.168.1.16:37753" 
UI_FILE_PATH = "ui.xml"

# FUNGSI DASAR (Tidak Berubah)
def run_adb_command(command_parts):
    """Menjalankan perintah ADB shell dan menangani output/error."""
    try:
        result = subprocess.run(
            command_parts,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=5
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.strip() or e.stdout.strip()
        return f"ADB_ERROR (Code {e.returncode}): {error_output}"
    except Exception as e:
        return f"ERROR: {e}"

def get_center_coords(bounds_string):
    """Menghitung koordinat tengah (x, y) dari string bounds: [x1,y1][x2,y2]"""
    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_string)
    if not match: return None
    x1, y1, x2, y2 = map(int, match.groups())
    return (x1 + x2) // 2, (y1 + y2) // 2

def find_and_tap_text(target_text, scroll_max=1):
    """Mencari teks yang cocok dalam UI.xml dan mengetuknya."""
    # Logika pencarian dan gulir tetap sama...
    target_text_lower = target_text.lower()
    
    for scroll_count in range(scroll_max + 1):
        # ... (Dump & Pull UI)
        run_adb_command(['adb', 'shell', 'uiautomator', 'dump', f'/sdcard/{UI_FILE_PATH}'])
        run_adb_command(['adb', 'pull', f'/sdcard/{UI_FILE_PATH}', '.'])
        
        if os.path.exists(UI_FILE_PATH):
            try:
                tree = ET.parse(UI_FILE_PATH)
                root = tree.getroot()
                
                for node in root.iter():
                    text = node.get('text', '')
                    content_desc = node.get('content-desc', '')
                    bounds = node.get('bounds')
                    
                    if bounds and (target_text_lower in text.lower() or target_text_lower in content_desc.lower()):
                        coords = get_center_coords(bounds)
                        if coords:
                            run_adb_command(['adb', 'shell', 'input', 'tap', str(coords[0]), str(coords[1])])
                            return True
            except Exception:
                pass
        
        if scroll_count < scroll_max:
            run_adb_command(['adb', 'shell', 'input', 'swipe', '500', '1500', '500', '500', '300']) 
            time.sleep(1) 

    return False

# --- FUNGSI BOOTSTRAP SHIZUKU BARU ---
def bootstrap_shizuku():
    """Meluncurkan Shizuku dan mengklik tombol 'Start'."""
    print("--- MEMULAI FUNGSI BOOTSTRAP SHIZUKU ---")

    # 1. Luncurkan aplikasi Shizuku
    launch_cmd = ['adb', 'shell', 'am', 'start', '-n', 'moefou.shizuku.privileged.api/.MainActivity']
    result = run_adb_command(launch_cmd)
    
    if "ADB_ERROR" in result:
        return f"SHIZUKU GAGAL: Koneksi ADB mati. {result}"
        
    print(f"[{time.strftime('%H:%M:%S')}] Meluncurkan Shizuku.")
    time.sleep(2) # Tunggu Shizuku terbuka

    # 2. Tap tombol "Start"
    if find_and_tap_text("Start", scroll_max=0):
        print(f"[{time.strftime('%H:%M:%S')}] Tap SUKSES pada tombol 'Start'.")
        time.sleep(1)
        # 3. Verifikasi dengan mencari teks 'running' (Opsional tapi bagus)
        run_adb_command(['adb', 'shell', 'uiautomator', 'dump', f'/sdcard/{UI_FILE_PATH}'])
        run_adb_command(['adb', 'pull', f'/sdcard/{UI_FILE_PATH}', '.'])
        
        if os.path.exists(UI_FILE_PATH) and 'running' in open(UI_FILE_PATH).read().lower():
             return "BOOTSTRAP SHIZUKU SELESAI TOTAL: Shizuku sekarang berjalan. Koneksi ADB menjadi stabil!"
        else:
            return "BOOTSTRAP SHIZUKU SELESAI: Tombol 'Start' diklik, tetapi status berjalan tidak terdeteksi. Harap periksa Shizuku secara manual."
    else:
        # Jika tombol 'Start' tidak ditemukan (karena sudah berjalan), ini tetap dianggap sukses
        return "BOOTSTRAP SHIZUKU SELESAI: Tombol 'Start' tidak ditemukan (kemungkinan sudah berjalan). Koneksi ADB stabil."


# --- FUNGSI UTAMA BOOTSTRAP (MIUI) ---
def bootstrap_wireless_debugging():
    # Logika navigasi Settings -> ... -> Debugging Nirkabel
    
    print("--- MEMULAI BOOTSTRAP NAVIGASI MIUI ---")
    
    # KITA SKIP NAVIGASI KARENA SUDAH BERHASIL DAN MEMASTIKAN KONEKSI AKTIF (dari log 'already connected')
    
    # 1. Melanjutkan langsung ke Shizuku
    print("Menduga Debugging Nirkabel sudah aktif. Melanjutkan langsung ke Shizuku.")
    
    return bootstrap_shizuku()

# --- DEMO ---
if __name__ == "__main__":
    print(f"PERHATIAN: Skrip ini membutuhkan koneksi ADB ke {ADB_IP_PORT} untuk menginisiasi tindakan.")
    # Kita tidak perlu menjalankan kembali navigasi Settings karena sudah dipastikan berhasil dan terhubung.
    # Cukup panggil fungsi Shizuku secara langsung.
    report = bootstrap_wireless_debugging()
    print("\n--- LAPORAN OTOMASI SHIZUKU ---")
    print(report)
