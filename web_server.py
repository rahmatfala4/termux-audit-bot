# Import modul yang diperlukan
import os
import json
import subprocess
import logging
import requests # Mengganti google-genai dengan requests
from flask import Flask, request, jsonify, render_template_string

# --- Konfigurasi Awal ---

# Inisialisasi Flask
app = Flask(__name__)
app.config['DEBUG'] = True
logging.basicConfig(level=logging.INFO)

# Dapatkan kunci API dari environment
# Catatan: Di Termux, ini perlu diatur di environment, misal: export GEMINI_API_KEY='YOUR_KEY'
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Konstanta API
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# Inisialisasi daftar chat history global (menyimpan role dan content)
chat_history = []
APP_ID = os.environ.get("APP_ID", "termux_dev_bot")
AUDIT_FILE = "audit_report.md"

# --- Fungsi Utilitas (Termux, Git) ---

def run_termux_command(command):
    """Menjalankan perintah shell Termux dan mengembalikan outputnya."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            executable='/bin/bash'
        )
        return {
            "success": True,
            "output": result.stdout.strip() if result.stdout else "Perintah berhasil dieksekusi.",
            "error": result.stderr.strip()
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "output": None,
            "error": f"Error Code: {e.returncode}\n{e.stderr.strip()}"
        }
    except Exception as e:
        return {
            "success": False,
            "output": None,
            "error": f"Error umum saat menjalankan perintah: {e}"
        }

def run_git_audit(commit_message):
    """Menjalankan alur Git Audit: add, commit -S, push."""
    try:
        # 1. Pastikan file audit ada (untuk simulasi)
        if not os.path.exists(AUDIT_FILE):
             with open(AUDIT_FILE, "w") as f:
                f.write(f"# Audit Report for {APP_ID}\n\nInitial setup.")

        # 2. Add semua file
        add_result = run_termux_command("git add .")
        if not add_result['success']:
            return f"Error Git Add: {add_result['error']}"

        # 3. Commit dengan GPG Signing (-S)
        commit_command = f'git commit -S -m "{commit_message.replace("\"", "")}"'
        commit_result = run_termux_command(commit_command)
        if not commit_result['success'] and "nothing to commit" not in commit_result['error']:
            return f"Error Git Commit -S: {commit_result['error']}"

        # 4. Push ke remote
        push_result = run_termux_command("git push")
        if not push_result['success']:
            return f"Error Git Push: {push_result['error']}"
        
        return "Sinkronisasi Git selesai: `git add .`, `git commit -S`, `git push` berhasil.\nCommit Message: " + commit_message
    
    except Exception as e:
        return f"Error Fatal Git Audit: {e}"

# --- Fungsi Inti Gemini (Menggunakan Requests) ---

def generate_gemini_content(prompt):
    """Memanggil model Gemini menggunakan pustaka requests."""
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY tidak diatur di environment Termux Anda."

    # Batasi history untuk menjaga ukuran payload
    current_history = chat_history[-10:] + [{"role": "user", "parts": [{"text": prompt}]}]
    
    payload = {
        "contents": current_history,
        "tools": [{"google_search": {}}], # Gunakan Google Search Grounding
        "systemInstruction": {
            "parts": [{
                "text": "Anda adalah Asisten Gemini yang bekerja di server pengembangan Termux. Tugas Anda adalah membantu pengguna dengan riset bisnis, debugging kode, eksekusi perintah Termux, dan mengelola sinkronisasi Git/Audit. Jawab dengan singkat, jelas, dan profesional. Jika ada konteks Git atau Audit, jangan mengulang tawaran riset umum."
            }]
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    params = {'key': GEMINI_API_KEY}

    try:
        # Panggil API menggunakan requests
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        result = response.json()
        candidate = result.get('candidates', [{}])[0]
        
        # Ekstrak teks
        text_response = candidate.get('content', {}).get('parts', [{}])[0].get('text', "Tidak ada respons teks dari model.")

        # Perbarui chat history global (hanya jika berhasil)
        chat_history.append({"role": "user", "parts": [{"text": prompt}]})
        chat_history.append({"role": "model", "parts": [{"text": text_response}]})

        # Ekstrak grounding sources
        sources = []
        grounding_metadata = candidate.get('groundingMetadata')
        if grounding_metadata and grounding_metadata.get('groundingAttributions'):
            for attr in grounding_metadata['groundingAttributions']:
                web = attr.get('web')
                if web and web.get('uri') and web.get('title'):
                    sources.append(f"[{web['title']}]({web['uri']})")
        
        if sources:
            text_response += "\n\n**Sumber Riset:**\n" + "\n".join(sources)
        
        return text_response

    except requests.exceptions.HTTPError as e:
        return f"Error HTTP API Gemini: {e.response.status_code}. Detail: {e.response.text}"
    except Exception as e:
        return f"Error saat memanggil Gemini (Requests): {e}"

def run_automated_audit():
    """Menjalankan simulasi Audit: riset, simpan ke file, Git commit & push."""
    
    # 1. Riset Harga Bitcoin
    research_prompt = "Apa harga Bitcoin saat ini dan ringkas status pasar dalam satu kalimat."
    gemini_response = generate_gemini_content(research_prompt)
    
    # Hapus penanda sumber dan ambil teks intinya
    audit_content = gemini_response.split("**Sumber Riset**")[0].strip()

    # 2. Simpan hasil riset ke file audit
    try:
        with open(AUDIT_FILE, "a") as f:
            f.write(f"\n\n## Audit Data - {os.popen('date').read().strip()}\n")
            f.write(audit_content)
            
        # 3. Commit dan Push
        commit_message = f"Audit Otomatis: Update harga Bitcoin terbaru. {os.popen('date -I').read().strip()}"
        git_status = run_git_audit(commit_message)
        
        return f"**Audit Otomatis Selesai.**\n\n- Hasil Riset Disimpan ke `{AUDIT_FILE}`.\n- **Laporan Riset:** {audit_content}\n- **Status Sinkronisasi:** {git_status}"
    
    except Exception as e:
        return f"Error saat menjalankan Audit Otomatis: {e}"


# --- Endpoint Flask ---

@app.route('/process_input', methods=['POST'])
def process_input():
    """Endpoint tunggal untuk memproses Chat, Termux, Git, dan Audit."""
    data = request.json
    user_input = data.get('input', '').strip()
    
    response_text = ""

    if user_input.startswith('!'):
        # Mode Termux Shell
        command = user_input[1:].strip()
        termux_result = run_termux_command(command)
        if termux_result['success']:
            response_text = f"**Termux Output (Shell):**\n```bash\n{termux_result['output']}\n```"
            if termux_result['error']:
                 response_text += f"\n\n**Warning (Stderr):**\n```\n{termux_result['error']}\n```"
        else:
            response_text = f"**Termux Error:**\n```\n{termux_result['error']}\n```"
            
    elif user_input.lower().startswith('/git'):
        # Mode Git Commit
        commit_message = user_input[5:].strip()
        if not commit_message:
            commit_message = f"Pembaruan berkala dari {APP_ID}"
        
        response_text = f"**Proses Git Sinkronisasi:** Mulai commit '{commit_message}'..."
        response_text += "\n\n" + run_git_audit(commit_message)

    elif user_input.lower() == '/audit':
        # Mode Audit Otomatis
        response_text = "**Proses Audit Otomatis:** Memulai riset, simpan file, commit -S, dan push..."
        response_text += "\n\n" + run_automated_audit()
        
    else:
        # Mode Chat/Riset Gemini
        response_text = generate_gemini_content(user_input)

    return jsonify({"response": response_text})

@app.route('/')
def index():
    """Menampilkan antarmuka web (hanya HTML/CSS/JS)."""
    
    user_id = "UserTermux"
    current_path = os.getcwd()
    
    # Menggunakan json.dumps untuk chat_history agar aman dimasukkan ke JavaScript
    history_json = json.dumps(chat_history).replace("'", "\\'").replace('\n', '\\n')

    html_content = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <title>Termux Dev Bot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            transition: background-color 0.3s, color 0.3s;
        }}
        .chat-container {{
            max-height: calc(100vh - 10rem); /* Sesuaikan tinggi agar tidak tertutup input fixed */
            overflow-y: auto;
            scroll-behavior: smooth;
            padding-bottom: 5rem; /* Tambahkan padding bawah agar pesan tidak tertutup footer */
        }}
        .message-bubble {{
            max-width: 85%;
            word-wrap: break-word;
        }}
        .user-bubble {{
            background-color: #3b82f6; /* Biru */
            color: white;
            border-bottom-right-radius: 0;
        }}
        .gemini-bubble {{
            background-color: #4b5563; /* Abu-abu Gelap */
            color: white;
            border-bottom-left-radius: 0;
        }}
        body {{
            background-color: #1f2937; /* Gray 800 */
            color: #f3f4f6; /* Gray 100 */
        }}
        .card-panel {{
            background-color: #374151; /* Gray 700 */
            color: #f3f4f6;
        }}
        .input-area {{
            background-color: #374151;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 20;
        }}
        .input-field {{
            background-color: #4b5563; /* Gray 600 */
            color: white;
        }}
        .input-field::placeholder {{
            color: #9ca3af; /* Gray 400 */
        }}
        /* Media Query for Mobile (Single Column) */
        @media (max-width: 768px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
            .panel-gemini {{
                display: none; /* Sembunyikan panel Gemini di mobile */
            }}
            .chat-container {{
                max-height: calc(100vh - 12rem); /* Penyesuaian akhir untuk mobile */
            }}
        }}
    </style>
</head>
<body class="bg-gray-800 text-gray-100 min-h-screen flex flex-col">

    <!-- Header -->
    <header class="bg-gray-900 shadow p-4 sticky top-0 z-10">
        <h1 class="text-xl font-bold text-blue-400">Termux Dev/Riset Business</h1>
        <p class="text-sm text-gray-400">Online | ID: {request.host_url} | User: {user_id}</p>
        <p class="text-xs text-gray-500">Dir: {current_path}</p>
    </header>

    <!-- Main Content Area -->
    <main class="flex-grow p-4 grid grid-cols-1 md:grid-cols-3 gap-4 main-content">

        <!-- Kiri: Chat Interface (2/3 lebar di desktop) -->
        <div class="md:col-span-2 flex flex-col h-full">
            
            <!-- Chat Container -->
            <div id="chat-container" class="flex-grow chat-container p-2 space-y-4 rounded-lg card-panel shadow-inner">
                <div class="flex justify-start">
                    <div class="message-bubble gemini-bubble p-3 rounded-xl">
                        <p class="font-semibold text-blue-300">Gemini:</p>
                        <p class="mt-1">Selamat datang! Saya Asisten Gemini. Ketik pesan, atau gunakan <code class="bg-gray-700 p-0.5 rounded">'!'</code> untuk perintah Termux.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Kanan: Utility/Gemini Assistant (1/3 lebar di desktop, disembunyikan di mobile) -->
        <div class="panel-gemini md:col-span-1 flex flex-col space-y-4">
            
            <!-- Info Panel -->
            <div class="card-panel p-4 rounded-lg shadow-lg">
                <h2 class="text-lg font-semibold text-blue-400 mb-2">Utilitas & Status</h2>
                <p class="text-sm">Gunakan kolom chat untuk perintah:</p>
                <ul class="text-xs list-disc list-inside mt-2 space-y-1 text-gray-300">
                    <li><code class="font-mono">!</code>: Perintah Termux (contoh: <code class="font-mono">!ls -l</code>)</li>
                    <li><code class="font-mono">/git</code>: Commit Git otomatis (contoh: <code class="font-mono">/git Laporan hari ini</code>)</li>
                    <li><code class="font-mono">/audit</code>: Audit otomatis (riset BTC, simpan file, commit).</li>
                    <li>Pertanyaan lain: Riset bisnis dengan Gemini.</li>
                </ul>
            </div>
            
            <!-- Simulasi Log/Status -->
            <div id="log-status" class="card-panel p-4 rounded-lg shadow-lg flex-grow">
                <h2 class="text-lg font-semibold text-blue-400 mb-2">Log Aksi</h2>
                <div id="status-messages" class="text-sm space-y-1 text-gray-300">
                    <p>Log akan muncul di sini.</p>
                </div>
            </div>
        </div>

    </main>
    
    <!-- Input Area (Fixed di bagian bawah) -->
    <div class="input-area p-4 rounded-t-xl shadow-2xl flex items-center">
        <input type="text" id="user-input" class="flex-grow input-field p-3 rounded-l-lg border-2 border-gray-700 focus:outline-none focus:border-blue-500" placeholder="Ketik pesan, atau gunakan !perintah Termux, /audit, /git..." onkeypress="if(event.key === 'Enter') sendMessage()">
        <button onclick="sendMessage()" id="send-button" class="bg-blue-600 hover:bg-blue-700 text-white font-bold p-3 rounded-r-lg transition duration-150 ease-in-out flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A5.996 5.996 0 0115.772 3h.538a6 6 0 011 11.218z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8.25 21h7.5A2.25 2.25 0 0018 18.75V8.25A2.25 2.25 0 0015.75 6H8.25A2.25 2.25 0 006 8.25v7.5A2.25 2.25 0 008.25 18z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A5.996 5.996 0 0115.772 3h.538a6 6 0 011 11.218z" />
            </svg>
        </button>
    </div>
    
    <!-- Footer -->
    <footer class="bg-gray-900 p-3 text-center text-xs text-gray-500 mt-4 hidden md:block">
        &copy; 2025 Termux Dev Bot. Powered by Gemini.
    </footer>

    <!-- JavaScript -->
    <script>
        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        const statusMessages = document.getElementById('status-messages');
        let chatHistoryData = JSON.parse('{history_json}');
        
        // Fungsi untuk menambahkan pesan ke UI
        function addMessage(role, text) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = 'flex ' + (role === 'user' ? 'justify-end' : 'justify-start');
            
            const bubble = document.createElement('div');
            const bubbleClass = 'message-bubble p-3 rounded-xl shadow-md transition duration-300 ease-in-out ' + (role === 'user' ? 'user-bubble' : 'gemini-bubble');
            bubble.className = bubbleClass;
            
            if (role === 'model') {{
                const header = document.createElement('p');
                header.className = 'font-semibold text-blue-300';
                header.textContent = 'Gemini:';
                bubble.appendChild(header);
                
                const content = document.createElement('div');
                // Mengganti Markdown bold dan inline code
                const formattedText = text
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                    .replace(/`([^`]+)`/g, '<code class="bg-gray-700 p-0.5 rounded text-yellow-300">$1</code>')
                    .replace(/\\n/g, '<br>');
                content.innerHTML = '<p class="mt-1">' + formattedText + '</p>';
                bubble.appendChild(content);

            }} else {{
                bubble.textContent = text;
            }}
            
            messageDiv.appendChild(bubble);
            chatContainer.appendChild(messageDiv);
            
            // Scroll ke bawah
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }}
        
        // Fungsi untuk menampilkan pesan status/log
        function addStatus(message) {{
            const p = document.createElement('p');
            p.className = 'text-xs text-gray-400 border-t border-gray-600 pt-1';
            p.textContent = '[' + new Date().toLocaleTimeString() + '] ' + message;
            statusMessages.prepend(p);
        }}

        // Memuat history awal
        chatHistoryData.forEach(item => {{
            if (item.role === 'user') {{
                addMessage('user', item.parts[0].text);
            }} else if (item.role === 'model') {{
                addMessage('model', item.parts[0].text);
            }}
        }});

        // Fungsi utama pengiriman pesan
        async function sendMessage() {{
            const input = userInput.value.trim();
            if (!input) return;

            addMessage('user', input);
            userInput.value = '';
            sendButton.disabled = true;
            sendButton.innerHTML = '<svg class="animate-spin h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';
            addStatus('Mengirim perintah: "' + input + '"...');

            try {{
                const response = await fetch('/process_input', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ input: input }})
                }});

                if (!response.ok) {{
                    throw new Error('HTTP error! status: ' + response.status);
                }}

                const data = await response.json();
                
                addMessage('model', data.response);
                addStatus('Respons diterima.');

            }} catch (error) {{
                console.error('Fetch error:', error);
                addMessage('model', 'Error Komunikasi: Gagal mendapatkan respons dari server Termux. Cek konsol server Anda. (' + error.message + ')');
                addStatus('Error Komunikasi: ' + error.message);
            }} finally {{
                sendButton.disabled = false;
                sendButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A5.996 5.996 0 0115.772 3h.538a6 6 0 011 11.218z" /><path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8.25 21h7.5A2.25 2.25 0 0018 18.75V8.25A2.25 2.25 0 0015.75 6H8.25A2.25 2.25 0 006 8.25v7.5A2.25 2.25 0 008.25 18z" /><path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A5.996 5.996 0 0115.772 3h.538a6 6 0 011 11.218z" /></svg>';
            }}
        }}

        // Inisialisasi: Scroll ke bawah
        window.onload = () => {{
            chatContainer.scrollTop = chatContainer.scrollHeight;
            addStatus("Antarmuka dimuat. Siap untuk interaksi.");
        }};
    </script>
</body>
</html>
    """
    
    return render_template_string(html_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
