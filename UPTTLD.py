from flask import Flask, request, redirect, session, url_for, render_template_string, send_from_directory
import os, yt_dlp, glob, time, random, subprocess, sys, webbrowser
from colorama import init, Fore, Style
import pyfiglet

init(autoreset=True)

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

VIDEO_FOLDER = 'videos'
os.makedirs(VIDEO_FOLDER, exist_ok=True)

COLORS = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]

USERNAME = "TTDWLD"
PASSWORD = "SHAHO143"

def print_colored(text):
    print(random.choice(COLORS) + text + Style.RESET_ALL)

def download_media(url, quality):
    output_path = os.path.join(VIDEO_FOLDER, '%(id)s.%(ext)s')
    format_map = {
        "720p": "best[height<=720][ext=mp4]",
        "1080p": "best[height<=1080][ext=mp4]",
        "4k": "best[height<=2160][ext=mp4]",
        "8k": "best[height<=4320][ext=mp4]",
    }
    ydl_opts = {
        'format': format_map.get(quality, 'best[ext=mp4]'),
        'outtmpl': output_path,
        'quiet': True,
        'nocheckcertificate': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info['id'] + '.mp4'

def cleanup_old_videos(folder=VIDEO_FOLDER, max_age_seconds=3600):
    now = time.time()
    for filepath in glob.glob(os.path.join(folder, '*')):
        if os.path.isfile(filepath) and now - os.path.getmtime(filepath) > max_age_seconds:
            try:
                os.remove(filepath)
                print_colored(f"Deleted old file: {filepath}")
            except Exception as e:
                print_colored(f"Error deleting {filepath}: {e}")

@app.route('/')
def home():
    if session.get('user'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['user'] = username
            return redirect(url_for('dashboard'))
        return "Invalid login."
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    cleanup_old_videos()
    video_file = None
    error = None

    if request.method == 'POST':
        video_url = request.form['video_url']
        quality = request.form['quality']
        try:
            video_file = download_media(video_url, quality)
        except Exception as e:
            error = f"Error downloading: {e}"

    return render_template_string(DASHBOARD_HTML, video_file=video_file, error=error)

@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

STYLE_BLOCK = '''
<style>
body {
    background-color: #111;
    color: pink;
    font-family: sans-serif;
}
input, select, button {
    background-color: #222;
    color: pink;
    border: 1px solid #444;
    padding: 6px;
    margin-top: 6px;
}
a { color: #f99; }
</style>
'''

ASCII_LOGO = STYLE_BLOCK + '''
<div id="ascii-logo" style="white-space: pre; font-family: monospace; font-size: 14px; text-align:center;"></div>
<div style="display: flex; justify-content: center;">
    <div id="owner-name" style="font-size: 18px; font-weight: bold;"></div>
</div>
<script>
const colors = ["pink", "magenta", "fuchsia"];
const asciiArt = `888888 888888     8888b.   dP"Yb  Yb        dP 88b 88 88      dP"Yb     db    8888b.  
  88     88        8I  Yb dP   Yb  Yb  db  dP  88Yb88 88     dP   Yb   dPYb    8I  Yb 
  88     88        8I  dY Yb   dP   YbdPYbdP   88 Y88 88  .o Yb   dP  dP__Yb   8I  dY 
  88     88       8888Y"   YbodP     YP  YP    88  Y8 88ood8  YbodP  dP""""Yb 8888Y"`;

function renderAscii(color) {
    document.getElementById('ascii-logo').innerHTML = `<span style="color:${color}">${asciiArt}</span>`;
    document.getElementById('owner-name').innerHTML = `<span style="color:${color}">OWNER: SHAHARIA</span>`;
}

let i = 0;
setInterval(() => {
    renderAscii(colors[i % colors.length]);
    i++;
}, 250);
</script>
<audio autoplay loop id="bg-music" style="display:none;">
    <source src="https://cdn.pixabay.com/audio/2022/12/17/audio_7b6b2a53e6.mp3" type="audio/mp3">
</audio>
'''

LOGIN_HTML = ASCII_LOGO + '''
<h2>Login</h2>
<form method="POST">
    Username: <input name="username" required><br><br>
    Password: <input name="password" type="password" required><br><br>
    <button type="submit">Login</button>
</form>
'''

DASHBOARD_HTML = ASCII_LOGO + '''
<h2>Welcome, {{ session['user'] }}</h2>
<form id="download-form" method="POST" onsubmit="startDownload(event)">
    <label>Paste TikTok Video URL:</label><br>
    <input name="video_url" style="width: 400px;" required><br><br>
    <label>Select Video Quality:</label>
    <select name="quality" required>
        <option value="720p">720p</option>
        <option value="1080p">1080p</option>
        <option value="4k">4K</option>
        <option value="8k">8K Ultra</option>
    </select><br><br>
    <button type="submit">Download</button>
</form>

<div id="loader" style="display:none; text-align:center;">
    <p id="progress-text">Starting download...</p>
    <img src="https://i.gifer.com/YCZH.gif" style="width: 720px;">
</div>

<script>
function getRandomColor() {
    const colors = ["hotpink", "magenta", "fuchsia"];
    return colors[Math.floor(Math.random() * colors.length)];
}

function startDownload(e) {
    e.preventDefault();
    const form = document.getElementById("download-form");
    const loader = document.getElementById("loader");
    const progressText = document.getElementById("progress-text");

    loader.style.display = "block";
    progressText.style.color = getRandomColor();

    const colorInterval = setInterval(() => {
        progressText.style.color = getRandomColor();
    }, 300);

    const formData = new FormData(form);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/dashboard");

    xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
            let percent = Math.round((e.loaded / e.total) * 100);
            progressText.innerText = "Uploading: " + percent + "%";
        }
    };

    xhr.onload = function () {
        clearInterval(colorInterval);
        if (xhr.status === 200) {
            document.open();
            document.write(xhr.responseText);
            document.close();
        } else {
            progressText.innerText = "Download failed.";
            progressText.style.color = "red";
        }
    };

    xhr.send(formData);
}
</script>

{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}

{% if video_file %}
    <h3>Downloaded Video</h3>
    <video width="720" controls autoplay>
        <source src="/videos/{{ video_file }}" type="video/mp4">
        Your browser does not support the video tag.
    </video>
{% endif %}

<br>
<a href="/logout">Logout</a> | 
<a href="https://www.facebook.com/md.shaharia.1675275" target="_blank">Contact</a>
'''

def main():
    banner = pyfiglet.figlet_format("TIKTOK DWLD")
    print_colored(banner)

    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port_input = input("Enter port to run on (default 5001): ").strip()
        port = int(port_input) if port_input.isdigit() else 5001

    url = f"http://localhost:{port}/"
    print_colored(f"Starting on {url}")
    try:
        webbrowser.open(url)
    except:
        print_colored("Could not open browser automatically.")

    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()