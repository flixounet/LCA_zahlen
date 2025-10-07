# -*- coding: utf-8 -*-
# Greek–Latin Numbers Trainer (Streamlit) — simple Greek keyboard (no diacritics)
# Run:
#   pip install streamlit
#   streamlit run greek_numbers_streamlit_simple.py

import unicodedata
import json
import csv
import io
import random
import streamlit as st

# -------------------- Base data --------------------
BASE_ENTRIES = [
    {"roman":"I","arabic":1,"latin":"unus","greek":"εις/μια/εν"},
    {"roman":"II","arabic":2,"latin":"duo","greek":"δυο"},
    {"roman":"III","arabic":3,"latin":"tres","greek":"τρεις/τρια"},
    {"roman":"IV","arabic":4,"latin":"quattuor","greek":"τεσσαρες/τεσσαρα"},
    {"roman":"V","arabic":5,"latin":"quinque","greek":"πεντε"},
    {"roman":"VI","arabic":6,"latin":"sex","greek":"εξ"},
    {"roman":"VII","arabic":7,"latin":"septem","greek":"επτα"},
    {"roman":"VIII","arabic":8,"latin":"octo","greek":"οκτω"},
    {"roman":"IX","arabic":9,"latin":"novem","greek":"εννεα"},
    {"roman":"X","arabic":10,"latin":"decem","greek":"δεκα"},
    {"roman":"XX","arabic":20,"latin":"viginti","greek":"εικοσι"},
    {"roman":"XXX","arabic":30,"latin":"triginta","greek":"τριακοντα"},
    {"roman":"XL","arabic":40,"latin":"quadraginta","greek":"τεσσερακοντα"},
    {"roman":"L","arabic":50,"latin":"quinquaginta","greek":"πεντηκοντα"},
    {"roman":"LX","arabic":60,"latin":"sexaginta","greek":"εξηκοντα"},
    {"roman":"LXX","arabic":70,"latin":"septuaginta","greek":"εβδομηκοντα"},
    {"roman":"LXXX","arabic":80,"latin":"octoginta","greek":"ογδοηκοντα"},
    {"roman":"XC","arabic":90,"latin":"nonaginta","greek":"ενενηκοντα"},
    {"roman":"C","arabic":100,"latin":"centum","greek":"εκατον"},
    {"roman":"D","arabic":500,"latin":"quingenti","greek":"πεντακοσιοι/πεντακοσιαι/πεντακοσια"},
    {"roman":"M","arabic":1000,"latin":"mille","greek":"χιλιοι/χιλιαι/χιλια"},
]

VOWELS = "αεηιουω"
CONSONANTS_ROW1 = "βγδεζηθικλμνξ"
CONSONANTS_ROW2 = "οπρσςτυφχψω"

TEMPLATE_CSV = "roman,arabic,latin,greek\nI,1,unus,εις/μια/εν\nIV,4,quattuor,τεσσαρες/τεσσαρα\nX,10,decem,δεκα\n"

# -------------------- Utils --------------------
def strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("ς", "σ")
    return s.lower().strip()

def is_correct(user: str, solutions: str) -> bool:
    u = strip_accents(user)
    for part in solutions.split("/"):
        if strip_accents(part) == u:
            return True
    return False

def auto_final_sigma(text: str) -> str:
    out = []
    for i, ch in enumerate(text):
        if ch == "σ":
            nx = text[i+1] if i+1 < len(text) else ""
            if nx == "" or nx.isspace() or nx in ",.;:!?)»”'’":
                out.append("ς")
            else:
                out.append("σ")
        else:
            out.append(ch)
    return "".join(out)

def load_csv_bytes(b: bytes):
    content = b.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    required = {"roman","arabic","latin","greek"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError("CSV braucht Spalten: roman, arabic, latin, greek")
    rows = []
    for row in reader:
        try:
            rows.append({
                "roman": row["roman"].strip(),
                "arabic": int(row["arabic"]),
                "latin": row["latin"].strip(),
                "greek": row["greek"].strip(),
            })
        except Exception:
            pass
    return rows

def load_json_bytes(b: bytes):
    data = json.loads(b.decode("utf-8"))
    rows = []
    for item in data:
        rows.append({
            "roman": str(item["roman"]).strip(),
            "arabic": int(item["arabic"]),
            "latin": str(item["latin"]).strip(),
            "greek": str(item["greek"]).strip(),
        })
    return rows

def merge_entries(base, extra):
    seen = {(e["roman"], e["arabic"]) for e in base}
    out = list(base)
    added = 0
    for e in extra:
        key = (e["roman"], e["arabic"])
        if key not in seen:
            out.append(e); seen.add(key); added += 1
    return out, added

# -------------------- Session State --------------------
def init_state():
    st.session_state.setdefault("pool", list(BASE_ENTRIES))
    st.session_state.setdefault("started", False)
    st.session_state.setdefault("mode", "WRITE")
    st.session_state.setdefault("rounds", 10)
    st.session_state.setdefault("round_i", 0)
    st.session_state.setdefault("score", 0)
    st.session_state.setdefault("current", None)
    st.session_state.setdefault("options", [])
    st.session_state.setdefault("answer", "")
    st.session_state.setdefault("feedback", "")
    st.session_state.setdefault("await_next", False)
    st.session_state.setdefault("auto_final_sigma", True)

init_state()

# -------------------- Sidebar --------------------
st.sidebar.title("Einstellungen")

mode_label = st.sidebar.radio("Modus", ["Multiple Choice", "Schreibmodus"], index=1)
st.session_state.mode = "MC" if mode_label == "Multiple Choice" else "WRITE"

st.session_state.rounds = st.sidebar.slider("Anzahl Fragen", 5, 100, st.session_state.rounds)
st.session_state.auto_final_sigma = st.sidebar.checkbox("σ → ς am Wortende", value=st.session_state.auto_final_sigma)

# File upload
st.sidebar.markdown("### Datensätze laden (CSV oder JSON)")
uploads = st.sidebar.file_uploader("Dateien wählen (mehrere möglich)", type=["csv","json"], accept_multiple_files=True)
if uploads:
    all_new = []
    errors = []
    for up in uploads:
        try:
            if up.name.lower().endswith(".csv"):
                rows = load_csv_bytes(up.read())
            else:
                rows = load_json_bytes(up.read())
            all_new.extend(rows)
        except Exception as e:
            errors.append(f"{up.name}: {e}")
    if errors:
        st.sidebar.warning("Einige Dateien konnten nicht geladen werden:\n" + "\n".join(errors))
    if all_new:
        st.session_state.pool, added = merge_entries(st.session_state.pool, all_new)
        st.sidebar.success(f"{len(all_new)} Zeilen gelesen, {added} neu. Gesamt: {len(st.session_state.pool)}")

st.sidebar.download_button(
    "CSV-Vorlage herunterladen",
    data=TEMPLATE_CSV.encode("utf-8"),
    file_name="greek_numbers_template.csv",
    mime="text/csv"
)

colA, colB = st.sidebar.columns(2)
if colA.button("Start", use_container_width=True):
    st.session_state.started = True
    st.session_state.round_i = 0
    st.session_state.score = 0
    st.session_state.feedback = ""
    st.session_state.await_next = False
    st.session_state.answer = ""
    st.session_state.current = None
    st.session_state.options = []
if colB.button("Reset", use_container_width=True):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# -------------------- Main --------------------
st.title("Greek–Latin Numbers Trainer (Streamlit) — einfache griechische Tastatur")

def pick_new_question():
    st.session_state.current = random.choice(st.session_state.pool)
    st.session_state.answer = ""
    st.session_state.feedback = ""
    st.session_state.await_next = False
    if st.session_state.mode == "MC":
        correct = st.session_state.current["greek"]
        opts = {correct}
        while len(opts) < min(4, len(st.session_state.pool)):
            opts.add(random.choice(st.session_state.pool)["greek"])
        st.session_state.options = random.sample(list(opts), k=len(opts))

def next_round():
    st.session_state.round_i += 1
    if st.session_state.round_i > st.session_state.rounds:
        st.success(f"Fertig! Ergebnis: {st.session_state.score}/{st.session_state.rounds}")
        st.session_state.started = False
        return
    pick_new_question()

if not st.session_state.started:
    st.info("Wähle links den Modus, stelle die Anzahl der Fragen ein und klicke **Start**. "
            "Über **Datensätze laden** kannst du zusätzliche CSV/JSON-Dateien mit Zahlen hinzufügen.")
else:
    if st.session_state.current is None:
        next_round()
    e = st.session_state.current

    st.subheader(f"Runde {st.session_state.round_i}/{st.session_state.rounds}   •   Punkte: {st.session_state.score}")
    st.markdown(f"**Frage:** `{e['roman']}` (= {e['arabic']})  &nbsp;&nbsp;|&nbsp;&nbsp; **Latein:** *{e['latin']}*")

    if st.session_state.mode == "MC":
        cols = st.columns(2)
        labels = ["A","B","C","D"]
        for i, opt in enumerate(st.session_state.options):
            label = labels[i] if i < len(labels) else str(i+1)
            if cols[i % 2].button(f"{label}: {opt}", key=f"mc_{i}", use_container_width=True, disabled=st.session_state.await_next):
                if strip_accents(opt) == strip_accents(e["greek"]):
                    st.session_state.score += 1
                    st.session_state.feedback = "✅ Richtig!"
                else:
                    st.session_state.feedback = f"❌ Falsch. Richtig: {e['greek']}"
                st.session_state.await_next = True

        st.info(st.session_state.feedback or "Wähle die richtige griechische Zahl.")
        st.button("Weiter", on_click=next_round, disabled=not st.session_state.await_next)

    else:
        # Write Mode
        st.text_input("Antwort (Altgriechisch – ohne Diakritika nötig):", key="answer", value=st.session_state.answer)
        st.markdown("**Einfache griechische Bildschirmtastatur**")

        # Keyboard rows
        # Vowels
        cv = st.columns(len(VOWELS))
        for i, v in enumerate(VOWELS):
            if cv[i].button(v, key=f"v_{v}"):
                st.session_state.answer += v
                if st.session_state.auto_final_sigma:
                    st.session_state.answer = auto_final_sigma(st.session_state.answer)
        # Consonants row 1
        cr1 = st.columns(len(CONSONANTS_ROW1))
        for i, c in enumerate(CONSONANTS_ROW1):
            if cr1[i].button(c, key=f"c1_{c}"):
                st.session_state.answer += c
                if st.session_state.auto_final_sigma:
                    st.session_state.answer = auto_final_sigma(st.session_state.answer)
        # Consonants row 2
        cr2 = st.columns(len(CONSONANTS_ROW2))
        for i, c in enumerate(CONSONANTS_ROW2):
            if cr2[i].button(c, key=f"c2_{c}"):
                st.session_state.answer += c
                if st.session_state.auto_final_sigma:
                    st.session_state.answer = auto_final_sigma(st.session_state.answer)

        cclr1, cclr2, cclr3 = st.columns(3)
        if cclr1.button("Leer"):
            st.session_state.answer += " "
        if cclr2.button("← Backspace"):
            st.session_state.answer = st.session_state.answer[:-1]
        if cclr3.button("CLR Löschen"):
            st.session_state.answer = ""

        st.text_input("Deine Eingabe:", value=st.session_state.answer, key="answer_echo")

        col_ok, col_next = st.columns(2)
        if col_ok.button("Prüfen", disabled=st.session_state.await_next):
            if is_correct(st.session_state.answer, e["greek"]):
                st.session_state.score += 1
                st.session_state.feedback = "✅ Richtig!"
            else:
                st.session_state.feedback = f"❌ Falsch. Richtig: {e['greek']}"
            st.session_state.await_next = True

        col_next.button("Weiter", on_click=next_round, disabled=not st.session_state.await_next)

        st.info(st.session_state.feedback or "Schreibe die griechische Zahl und klicke **Prüfen**.")

with st.expander("Hilfe & Dateiformate"):
    st.markdown("""
**CSV** braucht die Spalten: `roman, arabic, latin, greek`  
Mehrere korrekte griechische Formen trennst du mit `/` (z. B. `πεντε/πέντε`).  
Die Auswertung ignoriert Diakritika und behandelt `σ` und `ς` als gleich.

**JSON**-Beispiel:
```json
[
  {"roman":"XI","arabic":11,"latin":"undecim","greek":"ενδεκα"},
  {"roman":"LII","arabic":52,"latin":"quinquaginta duo","greek":"πεντηκοντα δυο"}
]
```
""")
