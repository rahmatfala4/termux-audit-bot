import subprocess
import time

# Path yang berhasil Anda identifikasi dan setel sebelumnya.
SHIZUKU_APK_PATH = "/data/app/~~D1Al29dL0e18e1WI5vQ4gg==/moe.shizuku.privileged.api-30o9EvehBV51q7hx0BdDQg==/base.apk"
SHIZUKU_LIBRARY_PATH = "/data/app/~~D1Al29dL0e18e1WI5vQ4gg==/moe.shizuku.privileged.api-30o9EvehBV51q7hx0BdDQg==/lib/arm64/libshizuku.so"

def check_shizuku_status():
    """Mengeksekusi perintah shizuku status secara langsung menggunakan jalur yang sudah ditentukan."""
    
    print("--- MEMERIKSA STATUS KONEKSI SHIZUKU (Final Fix) ---")
    
    # Perintah Shizuku: JANGAN gunakan "sh". Panggil library secara langsung.
    command_parts = [
        SHIZUKU_LIBRARY_PATH, # <--- LANGSUNG PANGGIL BINER
        SHIZUKU_APK_PATH, 
        "status" # Argumen "status" untuk mendapatkan laporan
    ]
    
    try:
        # Jalankan perintah langsung di shell Termux
        result = subprocess.run(
            command_parts,
            check=False,
            capture_output=True,
            text=True,
            encoding='utf-8', 
            errors='ignore',
            timeout=10
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        # Logika Verifikasi Status
        if "Shizuku is running" in stdout:
            print("STATUS: BERHASIL TERHUBUNG!")
            print("Shizuku berjalan dan siap digunakan oleh Termux.")
            print("\n--- OUTPUT SHIZUKU MENTAH ---")
            print(stdout)
        elif "service is not running" in stdout:
            print("STATUS: TIDAK BERJALAN")
            print("Server Shizuku tidak aktif. Jalankan skrip ADB Bootstrap untuk mengaktifkannya.")
        elif stdout and not stderr:
            print("STATUS: OUTPUT TERDEKODEKAN (Perlu Analisis Lanjutan)")
            print("\n--- OUTPUT SHIZUKU LENGKAP ---")
            print(stdout)
        else:
            print("STATUS: GAGAL TOTAL ATAU OUTPUT KOSONG")
            print(f"Error Code: {result.returncode}")
            print(f"Stderr: {stderr or 'Kosong'}")

    except Exception as e:
        print(f"ERROR EKSEKUSI PYTHON: {e}")

if __name__ == "__main__":
    check_shizuku_status()
