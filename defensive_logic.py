import xml.etree.ElementTree as ET
import subprocess
import re
import os
import time

# --- PENTING: CONFIGURATION ---
# Meskipun nilai ini TIDAK DIGUNAKAN untuk analisis, ia tetap ada untuk kasus 
# di mana Anda ingin mencoba koneksi penuh dari Python. Jaga agar tetap akurat 
# jika Anda pernah ingin mencoba full scan lagi.
ADB_IP_PORT = "192.168.1.16:41367" 
UI_FILE_PATH = "ui.xml"
DEFENSIVE_KEYWORDS = ["ok", "lanjutkan", "izinkan", "selesai", "tutup", "perbarui", "notifikasi", "lanjut"]

# --- FUNGSI ADB DASAR ---
def run_adb_command(command_parts):
    """
    Menjalankan perintah ADB shell dan menangani output/error.
    """
    # Menggunakan timeout kecil karena kita tahu koneksi ADB nirkabel rentan
    try:
        result = subprocess.run(
            command_parts,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=5 # Mengurangi timeout untuk kecepatan
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.strip() or e.stdout.strip()
        return f"ADB_ERROR (Code {e.returncode}): {error_output}"
    except Exception as e:
        return f"ERROR: {e}"

def tap_element(x, y):
    """Mensimulasikan tap pada koordinat layar menggunakan adb shell."""
    # Pastikan koneksi ADB AKTIF saat fungsi ini dipanggil.
    # Tap harus selalu dijalankan segera setelah ADB shell berhasil.
    tap_cmd = ['adb', 'shell', 'input', 'tap', str(x), str(y)]
    print(f"[{time.strftime('%H:%M:%S')}] EKSEKUSI TAP: {tap_cmd}")
    return run_adb_command(tap_cmd)


def get_center_coords(bounds_string):
    """Menghitung koordinat tengah (x, y) dari string bounds: [x1,y1][x2,y2]"""
    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_string)
    if not match:
        return None
    x1, y1, x2, y2 = map(int, match.groups())
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    return center_x, center_y

# --- FUNGSI UTAMA CEK DEFENSIF (ANALISIS) ---
def defensive_check_analysis():
    """
    Membaca ui.xml yang ada dan mencari kata kunci defensif.
    """
    if not os.path.exists(UI_FILE_PATH):
        return f"ERROR: File {UI_FILE_PATH} tidak ditemukan. Harap jalankan langkah 'adb pull' terlebih dahulu."
        
    tree = ET.parse(UI_FILE_PATH)
    root = tree.getroot()
    keywords_to_find = [k.lower() for k in DEFENSIVE_KEYWORDS]
    
    print(f"[{time.strftime('%H:%M:%S')}] Menganalisis XML untuk kata kunci: {keywords_to_find}")

    for node in root.iter():
        text = node.get('text', '').lower()
        content_desc = node.get('content-desc', '').lower()
        bounds = node.get('bounds')
        
        # Logika Pencarian: Mencari kecocokan sebagian di teks atau deskripsi
        if bounds and (any(k in text for k in keywords_to_find) or any(k in content_desc for k in keywords_to_find)):
            
            coords = get_center_coords(bounds)
            if coords:
                element_name = text or content_desc
                print(f"DEFENSE TRIGGERED: Ditemukan elemen: '{element_name}'")
                
                # Kita harus mencoba tap, tetapi tap akan gagal jika koneksi ADB mati.
                # Kita tetap menjalankannya karena pada momen ini, koneksi adalah yang terbaru.
                tap_result = tap_element(coords[0], coords[1])
                
                # Jika tap gagal karena device offline, ini adalah risiko yang harus kita ambil
                if "ADB_ERROR" in tap_result:
                    return f"CEK SUKSES (Tindakan Terlambat): Elemen '{element_name}' ditemukan, tetapi tap gagal (Koneksi ADB mati). Harap ulangi langkah 1 dan 2 dengan cepat. Detail: {tap_result}"
                else:
                    return f"CEK SUKSES (Tindakan Diambil): Elemen '{element_name}' ({coords[0]}, {coords[1]}) diklik. Hasil ADB: {tap_result}"
                
    return "CEK BERHASIL (Aman): Tidak ada kata kunci defensif yang ditemukan."

# Fungsi ini TIDAK AKAN DIGUNAKAN LAGI karena tidak stabil.
def full_defensive_scan(ip_port=ADB_IP_PORT):
    # Ditinggalkan.
    pass


# --- DEMO BARU: HANYA ANALISIS FILE YANG SUDAH ADA ---
if __name__ == "__main__":
    # Panggil langsung fungsi analisis pada file ui.xml yang ada. 
    # File ini dijamin valid karena ditarik oleh perintah shell sebelumnya.
    scan_report = defensive_check_analysis()
    print("\n--- LAPORAN ANALISIS DEFENSIF ---")
    print(scan_report)
