from flask import Flask, render_template_string, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Veritabanı kurulumu
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///t2_studyo_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10))  # 'PT' veya 'Pilates'
    hour = db.Column(db.String(5))   # '07:00'
    date = db.Column(db.String(20))  # '2026-03-28'
    names = db.Column(db.Text, default="") # Kayıtlı isimler

with app.app_context():
    db.create_all()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>T2 Studio | Profesyonel Takvim</title>
    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', sans-serif;
            background: url('/static/T2.jpeg') no-repeat center center fixed;
            background-size: cover;
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .overlay {
            background: rgba(0, 0, 0, 0.65);
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
        }
        .header { margin: 30px 0; text-align: center; z-index: 1; }
        .date-input {
            padding: 12px 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.1); color: white; font-size: 1.1rem; backdrop-filter: blur(10px);
            outline: none; cursor: pointer;
        }
        .container {
            display: flex; flex-wrap: wrap; justify-content: center;
            gap: 30px; padding: 20px; width: 95%; max-width: 1600px; margin-bottom: 50px;
        }
        .panel {
            flex: 1; min-width: 500px;
            background: rgba(255, 255, 255, 0.07);
            backdrop-filter: blur(30px);
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 30px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.7);
        }
        h2 { text-align: center; letter-spacing: 4px; margin-bottom: 30px; color: #fff; font-size: 1.8rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; }
        
        .row {
            display: flex; align-items: flex-start;
            background: rgba(255, 255, 255, 0.04);
            margin-bottom: 15px; padding: 15px; border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.05);
            transition: all 0.3s ease;
        }
        .row:hover { background: rgba(255, 255, 255, 0.08); border-color: rgba(255,255,255,0.2); }
        
        .hour { font-size: 1.2rem; font-weight: bold; width: 65px; color: #00d2ff; padding-top: 10px; }
        
        /* Yeni Çok Satırlı Giriş Alanı */
        .input-box {
            flex-grow: 1; margin: 0 20px;
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px; padding: 12px;
            color: white; font-size: 1rem; outline: none;
            resize: none; /* Manuel büyütmeyi engeller */
            min-height: 50px; /* En az 2 satır yüksekliği */
            font-family: inherit;
            line-height: 1.4;
        }
        .input-box:focus { border-color: #00d2ff; background: rgba(0,0,0,0.4); box-shadow: 0 0 10px rgba(0,210,255,0.3); }
        
        .status-container { display: flex; flex-direction: column; align-items: center; gap: 10px; min-width: 80px; }
        .status { font-size: 0.9rem; color: #00d2ff; font-weight: bold; }
        
        .save-btn {
            background: linear-gradient(135deg, #27ae60, #2ecc71);
            color: white; border: none; padding: 10px 18px;
            border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 0.85rem;
            transition: 0.2s; box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
        }
        .save-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(39, 174, 96, 0.5); }
        .full { color: #ff4757; }
    </style>
</head>
<body>
    <div class="overlay"></div>
    <div class="header">
        <h1 style="text-transform: uppercase; margin-bottom: 20px; letter-spacing: 5px;">T2 STUDIO</h1>
        <input type="date" id="datePicker" class="date-input" value="2026-03-28">
    </div>

    <div class="container">
        <div class="panel">
            <h2>PT TAKVİMİ</h2>
            <div id="pt-list"></div>
        </div>
        <div class="panel">
            <h2>PİLATES TAKVİMİ</h2>
            <div id="pilates-list"></div>
        </div>
    </div>

    <script>
        const hours = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00", "00:00"];

        async function load() {
            const date = document.getElementById('datePicker').value;
            const res = await fetch(`/api/get?date=${date}`);
            const data = await res.json();
            render('pt-list', 'PT', data.PT);
            render('pilates-list', 'Pilates', data.Pilates);
        }

        function render(id, type, savedData) {
            const div = document.getElementById(id);
            div.innerHTML = '';
            hours.forEach(h => {
                const names = savedData[h] || "";
                const count = names.trim() === "" ? 0 : names.split(',').filter(n => n.trim() !== "").length;
                const isFull = count >= 20;

                div.innerHTML += `
                    <div class="row">
                        <div class="hour">${h}</div>
                        <textarea id="${type}-${h}" class="input-box" 
                                  placeholder="İsimleri virgülle ayırarak girin..."
                                  oninput="updateCount('${type}', '${h}')">${names}</textarea>
                        <div class="status-container">
                            <span id="count-${type}-${h}" class="status ${isFull ? 'full' : ''}">${count}/20</span>
                            <button class="save-btn" onclick="save('${type}', '${h}')">KAYDET</button>
                        </div>
                    </div>
                `;
            });
        }

        function updateCount(type, hour) {
            const val = document.getElementById(`${type}-${hour}`).value;
            const count = val.trim() === "" ? 0 : val.split(',').filter(n => n.trim() !== "").length;
            const counter = document.getElementById(`count-${type}-${hour}`);
            counter.innerText = `${count}/20`;
            if (count >= 20) counter.classList.add('full');
            else counter.classList.remove('full');
        }

        async function save(type, hour) {
            const date = document.getElementById('datePicker').value;
            const names = document.getElementById(`${type}-${hour}`).value;
            const count = names.trim() === "" ? 0 : names.split(',').filter(n => n.trim() !== "").length;
            
            if (count > 20) {
                alert("Uyarı: Bu saatte 20 kişilik kapasite aşılmış görünüyor!");
            }

            const res = await fetch('/api/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({type, hour, date, names})
            });
            
            if(res.ok) {
                const btn = event.target;
                btn.innerText = "KAYDEDİLDİ";
                btn.style.background = "#3498db";
                setTimeout(() => { btn.innerText = "KAYDET"; btn.style.background = ""; }, 2000);
            }
        }

        document.getElementById('datePicker').onchange = load;
        load();
    </script>
</body>
</html>
"""

@app.route('/api/get')
def get_data():
    date = request.args.get('date')
    items = Reservation.query.filter_by(date=date).all()
    out = {"PT": {}, "Pilates": {}}
    for i in items:
        out[i.type][i.hour] = i.names
    return jsonify(out)

@app.route('/api/save', methods=['POST'])
def save_data():
    data = request.json
    item = Reservation.query.filter_by(type=data['type'], hour=data['hour'], date=data['date']).first()
    if item:
        item.names = data['names']
    else:
        item = Reservation(type=data['type'], hour=data['hour'], date=data['date'], names=data['names'])
        db.session.add(item)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True)
