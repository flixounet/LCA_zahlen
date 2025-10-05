# -*- coding: utf-8 -*-
# Latin–Greek Numbers Quiz (Streamlit) — ohne IPA
# Features:
# - Moduswahl: Multiple Choice oder Schreibmodus
# - Polytonische Bildschirmtastatur (Atemzeichen, Akzente, Iota-subscriptum, Trema)
# - Akzenttoleranter Vergleich + optional σ→ς am Wortende
#
# Start:
#   pip install streamlit
#   streamlit run greek_numbers_streamlit.py

import unicodedata
import random
import streamlit as st

# -------------------- Daten --------------------
ENTRIES = [
    {"roman":"I","arabic":1,"latin":"unus, a, um","greek":"εἷς/μία/ἕν"},
    {"roman":"II","arabic":2,"latin":"duo, duae, duo","greek":"δύο"},
    {"roman":"III","arabic":3,"latin":"tres, tres, tria","greek":"τρεῖς/τρία"},
    {"roman":"IV","arabic":4,"latin":"quattuor","greek":"τέσσαρες/τέσσαρα"},
    {"roman":"V","arabic":5,"latin":"quinque","greek":"πέντε"},
    {"roman":"VI","arabic":6,"latin":"sex","greek":"ἕξ"},
    {"roman":"VII","arabic":7,"latin":"septem","greek":"ἑπτά"},
    {"roman":"VIII","arabic":8,"latin":"octo","greek":"ὀκτώ"},
    {"roman":"IX","arabic":9,"latin":"novem","greek":"ἐννέα"},
    {"roman":"X","arabic":10,"latin":"decem","greek":"δέκα"},
    {"roman":"XX","arabic":20,"latin":"viginti","greek":"εἴκοσι"},
    {"roman":"XXX","arabic":30,"latin":"triginta","greek":"τριάκοντα"},
    {"roman":"XL","arabic":40,"latin":"quadraginta","greek":"τεσσεράκοντα"},
    {"roman":"L","arabic":50,"latin":"quinquaginta","greek":"πεντήκοντα"},
    {"roman":"LX","arabic":60,"latin":"sexaginta","greek":"ἑξήκοντα"},
    {"roman":"LXX","arabic":70,"latin":"septuaginta","greek":"ἑβδομήκοντα"},
    {"roman":"LXXX","arabic":80,"latin":"octoginta","greek":"ὀγδοήκοντα"},
    {"roman":"XC","arabic":90,"latin":"nonaginta","greek":"ἐνενήκοντα"},
    {"roman":"C","arabic":100,"latin":"centum","greek":"ἑκατόν"},
    {"roman":"D","arabic":500,"latin":"quingenti, ae, a","greek":"πεντακόσιοι/πεντακόσιαι/πεντακόσια"},
    {"roman":"M","arabic":1000,"latin":"mille","greek":"χίλιοι/χίλιαι/χίλια"},
]

VOWELS = "αεηιουω"
CONSONANTS_ROW1 = "βγδζθκλμνξπρσ"
CONSONANTS_ROW2 = "τυφχψς"

# -------------------- Hilfsfunktionen --------------------
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
            next_ch = text[i+1] if i+1 < len(text) else ""
            if next_ch == "" or next_ch.isspace() or next_ch in ",.;:!?)»”'’":
                out.append("ς")
            else:
                out.append("σ")
        else:
            out.append(ch)
    return "".join(out)

# -------------------- Polytonic Composer --------------------
COMPOSE = {}
def add(v, breath, acc, iota, diaer, ch):
    COMPOSE[(v, breath, acc, iota, diaer)] = ch

# α
add("α", "smooth", None, False, False, "ἀ")
add("α", "rough",  None, False, False, "ἁ")
add("α", "smooth", "acute", False, False, "ἄ")
add("α", "rough",  "acute", False, False, "ἅ")
add("α", "smooth", "grave", False, False, "ἂ")
add("α", "rough",  "grave", False, False, "ἃ")
add("α", "smooth", "circ",  False, False, "ἆ")
add("α", "rough",  "circ",  False, False, "ἇ")
add("α", "smooth", None, True,  False, "ᾳ")
add("α", "smooth", "acute", True, False, "ᾴ")
add("α", "smooth", "grave", True, False, "ᾲ")
add("α", "smooth", "circ",  True, False, "ᾷ")
add("α", "rough",  None, True,  False, "ᾁ")
add("α", "rough",  "acute", True, False, "ᾅ")
add("α", "rough",  "grave", True, False, "ᾃ")
add("α", "rough",  "circ",  True, False, "ᾇ")
# ε
add("ε", "smooth", None, False, False, "ἐ")
add("ε", "rough",  None, False, False, "ἑ")
add("ε", "smooth", "acute", False, False, "ἔ")
add("ε", "rough",  "acute", False, False, "ἕ")
add("ε", "smooth", "grave", False, False, "ἒ")
add("ε", "rough",  "grave", False, False, "ἓ")
# η
add("η", "smooth", None, False, False, "ἠ")
add("η", "rough",  None, False, False, "ἡ")
add("η", "smooth", "acute", False, False, "ἤ")
add("η", "rough",  "acute", False, False, "ἥ")
add("η", "smooth", "grave", False, False, "ἢ")
add("η", "rough",  "grave", False, False, "ἣ")
add("η", "smooth", "circ",  False, False, "ἦ")
add("η", "rough",  "circ",  False, False, "ἧ")
add("η", "smooth", None, True,  False, "ῃ")
add("η", "smooth", "acute", True, False, "ῄ")
add("η", "smooth", "grave", True, False, "ῂ")
add("η", "smooth", "circ",  True, False, "ῇ")
add("η", "rough",  None, True,  False, "ᾐ")
add("η", "rough",  "acute", True, False, "ᾔ")
add("η", "rough",  "grave", True, False, "ᾒ")
add("η", "rough",  "circ",  True, False, "ᾖ")
# ι
add("ι", "smooth", None, False, False, "ἰ")
add("ι", "rough",  None, False, False, "ἱ")
add("ι", "smooth", "acute", False, False, "ἴ")
add("ι", "rough",  "acute", False, False, "ἵ")
add("ι", "smooth", "grave", False, False, "ἲ")
add("ι", "rough",  "grave", False, False, "ἳ")
add("ι", "smooth", "circ",  False, False, "ἶ")
add("ι", "rough",  "circ",  False, False, "ἷ")
# Trema-Sonderfälle
COMPOSE[("ι", None, None, False, True)] = "ϊ"
COMPOSE[("ι", None, "acute", False, True)] = "ΐ"
# ο
add("ο", "smooth", None, False, False, "ὀ")
add("ο", "rough",  None, False, False, "ὁ")
add("ο", "smooth", "acute", False, False, "ὄ")
add("ο", "rough",  "acute", False, False, "ὅ")
add("ο", "smooth", "grave", False, False, "ὂ")
add("ο", "rough",  "grave", False, False, "ὃ")
# υ
add("υ", "smooth", None, False, False, "ὐ")
add("υ", "rough",  None, False, False, "ὑ")
add("υ", "smooth", "acute", False, False, "ὔ")
add("υ", "rough",  "acute", False, False, "ὕ")
add("υ", "smooth", "grave", False, False, "ὒ")
add("υ", "rough",  "grave", False, False, "ὓ")
add("υ", "smooth", "circ",  False, False, "ὖ")
add("υ", "rough",  "circ",  False, False, "ὗ")
COMPOSE[("υ", None, None, False, True)] = "ϋ"
COMPOSE[("υ", None, "acute", False, True)] = "ΰ"
# ω
add("ω", "smooth", None, False, False, "ὠ")
add("ω", "rough",  None, False, False, "ὡ")
add("ω", "smooth", "acute", False, False, "ὤ")
add("ω", "rough",  "acute", False, False, "ὥ")
add("ω", "smooth", "grave", False, False, "ὢ")
add("ω", "rough",  "grave", False, False, "ὣ")
add("ω", "smooth", "circ",  False, False, "ὦ")
add("ω", "rough",  "circ",  False, False, "ὧ")
add("ω", "smooth", None, True,  False, "ῳ")
add("ω", "smooth", "acute", True, False, "ῴ")
add("ω", "smooth", "grave", True, False, "ῲ")
add("ω", "smooth", "circ",  True, False, "ῷ")
add("ω", "rough",  None, True,  False, "ᾠ")
add("ω", "rough",  "acute", True, False, "ᾤ")
add("ω", "rough",  "grave", True, False, "ᾢ")
add("ω", "rough",  "circ",  True, False, "ᾦ")

# -------------------- State --------------------
def init_state():
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
    st.session_state.setdefault("breath", None)
    st.session_state.setdefault("accent", None)
    st.session_state.setdefault("iota", False)
    st.session_state.setdefault("diaer", False)

init_state()

# -------------------- Sidebar --------------------
st.sidebar.title("Einstellungen")
mode_label = st.sidebar.radio("Modus", ["Multiple Choice", "Schreibmodus"], index=1)
st.session_state.mode = "MC" if mode_label == "Multiple Choice" else "WRITE"
st.session_state.rounds = st.sidebar.slider("Anzahl Fragen", 5, 50, st.session_state.rounds)
st.session_state.auto_final_sigma = st.sidebar.checkbox("σ → ς am Wortende", value=st.session_state.auto_final_sigma)

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

st.title("Latin–Greek Numbers Quiz (Streamlit) — ohne IPA")
st.caption("Im Schreibmodus auf der polytonischen Bildschirmtastatur Altgriechisch eingeben (Atemzeichen, Akzent, Iota‑subscriptum, Trema).")

# -------------------- Helpers --------------------
def pick_new_question():
    st.session_state.current = random.choice(ENTRIES)
    st.session_state.answer = ""
    st.session_state.feedback = ""
    st.session_state.await_next = False
    if st.session_state.mode == "MC":
        correct = st.session_state.current["greek"]
        opts = {correct}
        while len(opts) < 4:
            opts.add(random.choice(ENTRIES)["greek"])
        st.session_state.options = random.sample(list(opts), k=4)

def next_round():
    st.session_state.round_i += 1
    if st.session_state.round_i > st.session_state.rounds:
        st.success(f"Fertig! Ergebnis: {st.session_state.score}/{st.session_state.rounds}")
        st.session_state.started = False
        return
    pick_new_question()

# -------------------- UI --------------------
if st.session_state.started:
    if st.session_state.current is None:
        next_round()
    e = st.session_state.current

    st.subheader(f"Runde {st.session_state.round_i}/{st.session_state.rounds}   •   Punkte: {st.session_state.score}")
    st.markdown(f"**Frage:** `{e['roman']}` (= {e['arabic']})  &nbsp;&nbsp;|&nbsp;&nbsp; **Latein:** *{e['latin']}*")

    if st.session_state.mode == "MC":
        cols = st.columns(2)
        for i, opt in enumerate(st.session_state.options):
            if cols[i%2].button(opt, key=f"mc_{i}", use_container_width=True, disabled=st.session_state.await_next):
                if opt == e["greek"]:
                    st.session_state.score += 1
                    st.session_state.feedback = "✅ Richtig!"
                else:
                    st.session_state.feedback = f"❌ Falsch. Richtig: {e['greek']}"
                st.session_state.await_next = True

        st.info(st.session_state.feedback or "Wähle die richtige griechische Zahl.")
        st.button("Weiter", on_click=next_round, disabled=not st.session_state.await_next)

    else:
        # Schreibmodus
        st.text_input("Antwort (Altgriechisch):", key="answer", value=st.session_state.answer)
        st.markdown("**Polytonische Tastatur** – zuerst Diakritika wählen, dann Vokal drücken.")

        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1:
            if st.button("᾿ glatt"): st.session_state.breath = "smooth"
        with c2:
            if st.button("῾ rauh"): st.session_state.breath = "rough"
        with c3:
            if st.button("kein Atem"): st.session_state.breath = None
        with c4:
            if st.button("´ akut"): st.session_state.accent = "acute"
        with c5:
            if st.button("` gravis"): st.session_state.accent = "grave"
        with c6:
            if st.button("῀ circumflex"): st.session_state.accent = "circ"
        with c7:
            if st.button("Reset"):
                st.session_state.breath = None; st.session_state.accent=None; st.session_state.iota=False; st.session_state.diaer=False

        c8, c9, c10 = st.columns(3)
        with c8:
            st.session_state.iota = st.toggle("Iota‑sub", value=st.session_state.iota)
        with c9:
            st.session_state.diaer = st.toggle("Trema", value=st.session_state.diaer)
        with c10:
            st.write("Aktiv:")
            active = []
            active.append("᾿" if st.session_state.breath == "smooth" else ("῾" if st.session_state.breath=="rough" else "—"))
            active.append({"acute":"´","grave":"`","circ":"῀"}.get(st.session_state.accent,"—"))
            active.append("ͺ" if st.session_state.iota else "—")
            active.append("¨" if st.session_state.diaer else "—")
            st.code(" ".join(active))

        # Vokale
        cv = st.columns(len(VOWELS))
        for i, v in enumerate(VOWELS):
            if cv[i].button(v, key=f"v_{v}"):
                ch = COMPOSE.get((v, st.session_state.breath, st.session_state.accent, st.session_state.iota, st.session_state.diaer))
                if ch is None and v in ("ι","υ") and st.session_state.diaer and st.session_state.accent in (None, "acute"):
                    ch = COMPOSE.get((v, None, st.session_state.accent or None, False, True))
                if ch is None:
                    ch = v
                st.session_state.answer += ch
                if st.session_state.auto_final_sigma:
                    st.session_state.answer = auto_final_sigma(st.session_state.answer)

        # Konsonanten
        cr1 = st.columns(len(CONSONANTS_ROW1))
        for i, c in enumerate(CONSONANTS_ROW1):
            if cr1[i].button(c, key=f"c1_{c}"):
                st.session_state.answer += c
                if st.session_state.auto_final_sigma:
                    st.session_state.answer = auto_final_sigma(st.session_state.answer)
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

        # Echo
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

else:
    st.info("Wähle links den Modus und klicke **Start**.")
    st.markdown("- **Multiple Choice**: eine von vier griechischen Antworten wählen.\n- **Schreibmodus**: Altgriechisch mit polytonischer Bildschirmtastatur eingeben.\n- Vergleich ist akzent‑tolerant; optionale automatische Umwandlung **σ→ς** am Wortende.")
