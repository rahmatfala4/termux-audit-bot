import subprocess
import requests

# --- FUNGSI UTAMA BOT ---

def jalankan_perintah_termux(perintah):
    """Menjalankan perintah shell dan menampilkan outputnya."""
    print(f"\n[EXEC] -> $ {perintah}")
    try:
        # Menjalankan perintah dan mengambil outputnya
        hasil = subprocess.run(
            perintah,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("--- Hasil Termux ---")
        print(hasil.stdout.strip())
        print("--------------------")
    except subprocess.CalledProcessError as e:
        print(f"!!! Error saat menjalankan perintah: {e.stderr.strip()}")
    except FileNotFoundError:
        print("!!! Perintah tidak ditemukan. Pastikan sudah diinstal.")

def cek_akses_web(url="https://api.github.com/"):
    """Melakukan ping ke URL untuk memeriksa koneksi web (Simulasi Peneliti)."""
    print(f"\n[WEB CHECK] Menguji akses ke {url}...")
    try:
        # Menggunakan requests untuk mendapatkan respons dari API publik GitHub
        response = requests.get(url, timeout=5)
        response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)
        
        print(f"-> Koneksi SUKSES (Status: {response.status_code}).")
        # Contoh data yang diambil (simulasi penelitian data)
        print("-> Data pertama yang diambil: ", response.json().get('current_user_url', 'URL Pengguna tidak tersedia'))
        return True
    except requests.exceptions.RequestException as e:
        print(f"-> Koneksi GAGAL: Tidak dapat menjangkau URL.")
        print(f"   Detail Error: {e}")
        return False

def bot_utama():
    """Fungsi utama bot yang berisi logika Y/n dan eksekusi."""
    
    # 1. UCAPAN AWAL
    print("\n==============================================")
    print(" BISMILLAHIRRAHMANIRRAHIM - BOT TERMUX AKTIF ")
    print("==============================================\n")
    
    # 2. LOGIKA KEPUTUSAN Y/n
    konfirmasi = input("Apakah Anda ingin menjalankan utilitas developer? (Y/n): ")
    
    if konfirmasi.lower() == 'y':
        print("\n[INFO] Otorisasi otomatisasi disetujui.")
        
        # 3. AUTOMATISASI: Cek Akses Web (Logika &&)
        if cek_akses_web():
            # Jika cek_akses_web berhasil (TRUE), maka jalankan perintah Termux
            print("\n[INFO] Akses Web OK. Melanjutkan ke eksekusi perintah Termux.")
            
            # 4. UTILITAS DEVELOPER: Jalankan perintah 'ls -l' (menampilkan file)
            jalankan_perintah_termux("ls -l")
            
            # 5. UTILITAS DEVELOPER: Jalankan perintah 'git status'
            jalankan_perintah_termux("git status")
        else:
            # Jika cek_akses_web gagal (FALSE), perintah Termux dibatalkan
            print("\n[INFO] Akses Web GAGAL. Eksekusi perintah Termux dibatalkan.")
        
    elif konfirmasi.lower() == 'n':
        print("\n[INFO] Perintah dibatalkan oleh pengguna. Bot dimatikan.")
        
    else:
        print("\n[INFO] Input tidak dikenal. Mohon masukkan 'Y' atau 'n'.")

if __name__ == "__main__":
    bot_utama()
