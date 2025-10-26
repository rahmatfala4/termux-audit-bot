import subprocess
import time
import sys

# --- KONFIGURASI PERANGKAT ---
# Ukuran layar POCO X3 NFC (1080x2400)
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 2400

# Nama Package dan Service Automate
AUTOMATE_PACKAGE = "com.llamalab.automate"
AUTOMATE_ACCESSIBILITY_SERVICE = "com.llamalab.automate/.services.AccessibilityService"

def run_adb_command(command):
    """Fungsi untuk menjalankan perintah ADB shell."""
    full_command = f"adb shell {command}"
    print(f"Menjalankan: {full_command}")
    
    try:
        # Jalankan perintah langsung di shell Termux
        result = subprocess.run(
            full_command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"ERROR ADB: Perintah gagal dengan kode {e.returncode}")
        print(f"Stderr: {e.stderr.strip()}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR ADB: Timeout (Perangkat mungkin sibuk).")
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR ADB: ADB tidak ditemukan. Pastikan sudah terinstal.")
        sys.exit(1)

def check_accessibility_status():
    """Memeriksa apakah layanan aksesibilitas Automate sudah aktif."""
    print("Memeriksa status Aksesibilitas saat ini...")
    try:
        settings_secure = run_adb_command(f"settings get secure enabled_accessibility_services")
        if settings_secure and AUTOMATE_ACCESSIBILITY_SERVICE in settings_secure:
            return True
        return False
    except Exception:
        return False

def enable_automate_accessibility():
    """Melakukan navigasi MIUI untuk mengaktifkan layanan Aksesibilitas Automate."""

    print("\n--- MEMULAI AUTOMATE ACCESSIBILITY ENABLER ---")
    
    if check_accessibility_status():
        print("STATUS: LAYANAN AKSESIBILITAS AUTOMATE SUDAH AKTIF.")
        print("Skrip selesai.")
        return

    print("STATUS: Layanan Aksesibilitas Automate TIDAK AKTIF. Memulai navigasi...")

    # 1. Buka halaman pengaturan Aplikasi yang Didownload
    # (Aksesibilitas -> Aplikasi yang Didownload)
    print("[1] Meluncurkan halaman Aksesibilitas Terunduh...")
    run_adb_command(f"am start -n com.android.settings/.Settings\\$AccessibilitySettingsActivity --ez accessibility_check_status_only false")
    time.sleep(2) # Tunggu Settings terbuka

    # 2. Ketuk pada 'Automate'
    # Berdasarkan gambar Anda, 'Automate' adalah entri pertama di daftar.
    automate_tap_y = int(SCREEN_HEIGHT * 0.25) 
    print(f"[2] Mengetuk 'Automate' di koordinat y={automate_tap_y}...")
    run_adb_command(f"input tap {SCREEN_WIDTH//2} {automate_tap_y}")
    time.sleep(2) # Tunggu halaman detail layanan terbuka

    # 3. Ketuk tombol 'Aktifkan' (Sakelar)
    # Koordinat perkiraan untuk sakelar/tombol toggle
    toggle_tap_y = int(SCREEN_HEIGHT * 0.2) 
    print(f"[3] Mengetuk sakelar Aktif/Nonaktif di y={toggle_tap_y}...")
    run_adb_command(f"input tap {SCREEN_WIDTH//2} {toggle_tap_y}")
    time.sleep(2) # Tunggu dialog peringatan muncul

    # 4. Menyetujui dialog peringatan (klik 'OK'/'Accept' setelah 10 detik menunggu peringatan keamanan)
    print("[4] Menunggu dialog peringatan keamanan (10 detik)... TOLONG JANGAN SENTUH LAYAR...")
    time.sleep(10) 
    
    # Koordinat perkiraan tombol 'OK' atau 'Izinkan' di dialog pop-up MIUI
    confirm_button_x = int(SCREEN_WIDTH * 0.75) 
    confirm_button_y = int(SCREEN_HEIGHT * 0.88)
    print(f"[5] Mengetuk tombol 'Izinkan' / 'OK' di ({confirm_button_x}, {confirm_button_y})...")
    run_adb_command(f"input tap {confirm_button_x} {confirm_button_y}")
    time.sleep(1)

    # 5. Tekan tombol Kembali (untuk menutup Settings jika tidak otomatis)
    print("[6] Menekan tombol Kembali.")
    run_adb_command("input keyevent 4")
    
    time.sleep(2)
    
    # 6. Verifikasi Akhir
    if check_accessibility_status():
        print("\n--- SUKSES AKHIR ---")
        print("Layanan Aksesibilitas Automate berhasil diaktifkan.")
    else:
        print("\n--- PERLU TINDAKAN MANUAL ---")
        print("Aksesibilitas mungkin belum aktif. Periksa dan aktifkan secara manual.")

if __name__ == "__main__":
    enable_automate_accessibility()
