from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- MODEL ----------------
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(20), nullable=False)  # pt / pilates
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

# ---------------- KAPASİTE ----------------
CAPACITY = {
    "pt": 10,
    "pilates": 10
}

# ---------------- ANA SAYFA ----------------
@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>Spor Salonu Takvim</title>

  <link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/locales/tr.global.min.js"></script>

  <style>
    body { font-family: Arial; margin: 40px; }
    #calendar { max-width: 1000px; margin: auto; }
  </style>
</head>
<body>

<h2>PT & Pilates Rezervasyon Takvimi</h2>
<p>Aynı saat için PT (10) + Pilates (10) ayrı ayrı alınabilir</p>

<div id="calendar"></div>

<script>
document.addEventListener("DOMContentLoaded", function () {
  const calendar = new FullCalendar.Calendar(
    document.getElementById("calendar"),
    {
      locale: "tr",

      /* 👇 GÜNLÜK GÖRÜNÜM */
      initialView: "timeGridDay",

      /* 👇 ÜST BUTONLAR */
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "timeGridDay,timeGridWeek"
      },

      selectable: true,
      slotDuration: "01:00:00",

      /* 👇 SAAT KUTULARI DAHA BÜYÜK */
      slotMinHeight: 90,

      allDaySlot: false,

      slotLabelFormat: {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      },
      eventTimeFormat: {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      },

      events: "/reservations",

      select: function (info) {
        const section = prompt(
          "Bölüm seç:\\npt = Personal Training\\npilates = Pilates"
        );

        if (section !== "pt" && section !== "pilates") {
          alert("Geçersiz seçim");
          return;
        }

        fetch("/reserve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            start: info.startStr,
            section: section
          })
        })
        .then(res => res.json())
        .then(data => {
          alert(data.message || data.error);
          calendar.refetchEvents();
        });
      },

      eventClick: function(info) {
        if (confirm("Rezervasyon iptal edilsin mi?")) {
          fetch("/cancel", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: info.event.id })
          })
          .then(res => res.json())
          .then(data => {
            alert(data.message || data.error);
            info.event.remove();
          });
        }
      }
    }
  );

  calendar.render();
});
</script>

</body>
</html>
"""

# ---------------- TAKVİM VERİLERİ ----------------
@app.route("/reservations")
def reservations():
    res = Reservation.query.all()
    return jsonify([
        {
            "id": r.id,
            "title": r.section.upper(),
            "start": r.start_time.isoformat(),
            "end": r.end_time.isoformat(),
            "color": "#2196f3" if r.section == "pt" else "#e91e63"
        } for r in res
    ])

# ---------------- REZERVASYON ----------------
@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.json
    section = data["section"]
    start = datetime.fromisoformat(data["start"])
    end = start + timedelta(hours=1)

    count = Reservation.query.filter(
        Reservation.section == section,
        Reservation.start_time < end,
        Reservation.end_time > start
    ).count()

    if count >= CAPACITY[section]:
        return jsonify({
            "error": f"{section.upper()} için bu saat dolu (max {CAPACITY[section]})"
        }), 400

    r = Reservation(section=section, start_time=start, end_time=end)
    db.session.add(r)
    db.session.commit()

    return jsonify({"message": f"{section.upper()} rezervasyonu alındı"})

# ---------------- İPTAL ----------------
@app.route("/cancel", methods=["POST"])
def cancel():
    data = request.json
    r = Reservation.query.get(data["id"])

    if not r:
        return jsonify({"error": "Rezervasyon bulunamadı"}), 404

    db.session.delete(r)
    db.session.commit()
    return jsonify({"message": "Rezervasyon iptal edildi"})

# ---------------- ÇALIŞTIR ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run



