from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# ---------------- APP ----------------
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

# ---------------- DB ----------------
with app.app_context():
    db.create_all()

# ---------------- ANA SAYFA ----------------
@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Spor Salonu Takvim</title>

<link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.js"></script>

<style>
body { font-family: Arial; margin: 30px; }
#calendar { max-width: 1300px; margin: auto; }

/* 🔥 Saat kutuları daha büyük */
.fc-timegrid-slot {
    min-height: 100px;
}

/* Event görünümü */
.fc-event {
    font-size: 13px;
    padding: 4px;
}
</style>
</head>

<body>

<h2>PT & Pilates Rezervasyon Takvimi</h2>
<div id="calendar"></div>

<script>
document.addEventListener("DOMContentLoaded", function () {
  const calendar = new FullCalendar.Calendar(
    document.getElementById("calendar"),
    {
      locale: "tr",
      initialView: "timeGridDay",
      expandRows: true,
      height: "auto",

      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "timeGridDay,timeGridWeek"
      },

      slotMinTime: "08:00:00",
      slotMaxTime: "22:00:00",
      slotDuration: "01:00:00",
      slotLabelInterval: "01:00",
      allDaySlot: false,

      selectable: true,
      events: "/reservations",

      select: function (info) {
        const section = prompt("Bölüm seç: pt / pilates");

        if (section !== "pt" && section !== "pilates") {
          alert("Geçersiz bölüm");
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
      }
    }
  );

  calendar.render();
});
</script>

</body>
</html>
"""

# ---------------- EVENTLER ----------------
@app.route("/reservations")
def reservations():
    res = Reservation.query.all()
    return jsonify([
        {
            "title": f"{r.section.upper()}",
            "start": r.start_time.isoformat(),
            "end": r.end_time.isoformat(),
            "color": "#4A90E2" if r.section == "pt" else "#F48FB1"
        } for r in res
    ])

# ---------------- REZERVASYON ----------------
@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.json
    section = data["section"]
    start = datetime.fromisoformat(data["start"])
    end = start + timedelta(hours=1)

    # 🔥 AYNI SAATE AYNI BÖLÜM SAYISI
    count = Reservation.query.filter(
        Reservation.section == section,
        Reservation.start_time < end,
        Reservation.end_time > start
    ).count()

    if count >= CAPACITY[section]:
        return jsonify({"error": f"{section.upper()} kapasitesi dolu"}), 400

    r = Reservation(
        section=section,
        start_time=start,
        end_time=end
    )

    db.session.add(r)
    db.session.commit()

    return jsonify({"message": "Rezervasyon alındı"})

# ---------------- LOCAL ----------------
if __name__ == "__main__":
    app.run(debug=True)




