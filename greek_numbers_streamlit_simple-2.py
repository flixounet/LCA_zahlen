# -*- coding: utf-8 -*-
# Greek–Latin Numbers Trainer (Streamlit) — simple Greek keyboard (no diacritics)
# Run:
#   pip install streamlit
#   streamlit run greek_numbers_streamlit_simple.py
#
# Fixed: use on_click callbacks; single text_input bound to key="answer"

import unicodedata, json, csv, io, random
import streamlit as st

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

def strip_accents(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("ς","σ")
    return s.lower().strip()

def is_correct(user, solutions):
    u = strip_accents(user)
    for part in solutions.split("/"):
        if strip_accents(part) == u:
            return True
    return False

def auto_final_sigma(text):
    out = []
    for i, ch in enumerate(text):
        if ch == "σ":
            nx = text[i+1] if i+1 < len(text) else ""
            out.append("ς" if (nx=="" or nx.isspace() or nx in ",.;:!?)»”'’") else "σ")
        else:
            out.append(ch)
    return "".join(out)

def load_csv_bytes(b):
    reader = csv.DictReader(io.StringIO(b.decode("utf-8-sig")))
    rows = []
    for row in reader:
        rows.append({"roman":row["roman"].strip(),"arabic":int(row["arabic"]),"latin":row["latin"].strip(),"greek":row["greek"].strip()})
    return rows

def load_json_bytes(b):
    data = json.loads(b.decode("utf-8"))
    return [{"roman":str(x["roman"]).strip(),"arabic":int(x["arabic"]),"latin":str(x["latin"]).strip(),"greek":str(x["greek"]).strip()} for x in data]

def merge_entries(base, extra):
    seen = {(e["roman"], e["arabic"]) for e in base}
    out = list(base); added=0
    for e in extra:
        k=(e["roman"],e["arabic"])
        if k not in seen:
            out.append(e); seen.add(k); added+=1
    return out, added

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

# Callbacks
def kb_add_char(ch):
    st.session_state.answer = st.session_state.get("answer","") + ch
    if st.session_state.auto_final_sigma:
        st.session_state.answer = auto_final_sigma(st.session_state.answer)
def kb_space(): kb_add_char(" ")
def kb_backspace(): st.session_state.answer = st.session_state.get("answer","")[:-1]
def kb_clear(): st.session_state.answer = ""
def start_quiz():
    st.session_state.started=True; st.session_state.round_i=0; st.session_state.score=0
    st.session_state.feedback=""; st.session_state.await_next=False
    st.session_state.answer=""; st.session_state.current=None; st.session_state.options=[]
def reset_all():
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()

# Sidebar
st.sidebar.title("Einstellungen")
label = st.sidebar.radio("Modus", ["Multiple Choice","Schreibmodus"], index=1)
st.session_state.mode = "MC" if label=="Multiple Choice" else "WRITE"
st.session_state.rounds = st.sidebar.slider("Anzahl Fragen", 5, 100, st.session_state.rounds)
st.session_state.auto_final_sigma = st.sidebar.checkbox("σ → ς am Wortende", value=st.session_state.auto_final_sigma)

st.sidebar.markdown("### Datensätze laden (CSV oder JSON)")
uploads = st.sidebar.file_uploader("Dateien wählen", type=["csv","json"], accept_multiple_files=True)
if uploads:
    new=[]; errors=[]
    for up in uploads:
        try:
            buf=up.read()
            new+= (load_csv_bytes(buf) if up.name.lower().endswith(".csv") else load_json_bytes(buf))
        except Exception as e:
            errors.append(f"{up.name}: {e}")
    if errors: st.sidebar.warning("Fehler:\n" + "\n".join(errors))
    if new:
        st.session_state.pool, added = merge_entries(st.session_state.pool, new)
        st.sidebar.success(f"{len(new)} Zeilen gelesen, {added} neu. Gesamt: {len(st.session_state.pool)}")
st.sidebar.download_button("CSV-Vorlage", data=("roman,arabic,latin,greek\nI,1,unus,εις/μια/εν\nIV,4,quattuor,τεσσαρες/τεσσαρα\nX,10,decem,δεκα\n").encode("utf-8"), file_name="greek_numbers_template.csv", mime="text/csv")

cA,cB = st.sidebar.columns(2)
cA.button("Start", use_container_width=True, on_click=start_quiz)
cB.button("Reset", use_container_width=True, on_click=reset_all)

st.title("Greek–Latin Numbers Trainer — einfache griechische Tastatur")

def pick_new():
    st.session_state.current = random.choice(st.session_state.pool)
    st.session_state.answer=""; st.session_state.feedback=""; st.session_state.await_next=False
    if st.session_state.mode=="MC":
        correct = st.session_state.current["greek"]
        opts={correct}
        while len(opts) < min(4, len(st.session_state.pool)):
            opts.add(random.choice(st.session_state.pool)["greek"])
        st.session_state.options = random.sample(list(opts), k=len(opts))

def next_round():
    st.session_state.round_i += 1
    if st.session_state.round_i > st.session_state.rounds:
        st.success(f"Fertig! Ergebnis: {st.session_state.score}/{st.session_state.rounds}")
        st.session_state.started=False; return
    pick_new()

if not st.session_state.started:
    st.info("Wähle links den Modus und klicke **Start**. Lade zusätzliche CSV/JSON-Dateien bei Bedarf.")
else:
    if st.session_state.current is None:
        next_round()
    e = st.session_state.current

    st.subheader(f"Runde {st.session_state.round_i}/{st.session_state.rounds}   •   Punkte: {st.session_state.score}")
    st.markdown(f"**Frage:** `{e['roman']}` (= {e['arabic']})  &nbsp;&nbsp;|&nbsp;&nbsp; **Latein:** *{e['latin']}*")

    if st.session_state.mode=="MC":
        cols = st.columns(2); labels=["A","B","C","D"]
        for i,opt in enumerate(st.session_state.options):
            def choose(opt=opt, e=e):
                if strip_accents(opt)==strip_accents(e["greek"]):
                    st.session_state.score += 1; st.session_state.feedback="✅ Richtig!"
                else:
                    st.session_state.feedback = f"❌ Falsch. Richtig: {e['greek']}"
                st.session_state.await_next=True
            cols[i%2].button(f"{labels[i] if i<len(labels) else i+1}: {opt}", key=f"mc_{i}", use_container_width=True, disabled=st.session_state.await_next, on_click=choose)
        st.info(st.session_state.feedback or "Wähle die richtige griechische Zahl.")
        st.button("Weiter", on_click=next_round, disabled=not st.session_state.await_next)
    else:
        st.text_input("Antwort (Altgriechisch – ohne Diakritika nötig):", key="answer")
        st.markdown("**Einfache griechische Bildschirmtastatur**")
        cv = st.columns(len(VOWELS))
        for i,v in enumerate(VOWELS): cv[i].button(v, key=f"v_{v}", on_click=kb_add_char, args=(v,))
        cr1 = st.columns(len(CONSONANTS_ROW1))
        for i,c in enumerate(CONSONANTS_ROW1): cr1[i].button(c, key=f"c1_{c}", on_click=kb_add_char, args=(c,))
        cr2 = st.columns(len(CONSONANTS_ROW2))
        for i,c in enumerate(CONSONANTS_ROW2): cr2[i].button(c, key=f"c2_{c}", on_click=kb_add_char, args=(c,))
        cc1,cc2,cc3 = st.columns(3)
        cc1.button("Leer", on_click=kb_space); cc2.button("← Backspace", on_click=kb_backspace); cc3.button("CLR Löschen", on_click=kb_clear)
        def do_check(e=e):
            if is_correct(st.session_state.get("answer",""), e["greek"]):
                st.session_state.score += 1; st.session_state.feedback="✅ Richtig!"
            else:
                st.session_state.feedback=f"❌ Falsch. Richtig: {e['greek']}"
            st.session_state.await_next=True
        c_ok,c_next = st.columns(2)
        c_ok.button("Prüfen", disabled=st.session_state.await_next, on_click=do_check)
        c_next.button("Weiter", on_click=next_round, disabled=not st.session_state.await_next)
        st.info(st.session_state.feedback or "Schreibe die griechische Zahl und klicke **Prüfen**.")
