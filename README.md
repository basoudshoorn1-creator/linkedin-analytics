# LBSP LinkedIn Analytics Dashboard

Streamlit dashboard voor Leiden Bio Science Park LinkedIn analytics.  
Upload je LinkedIn XLS export en het dashboard herberekent automatisch.

---

## Lokaal draaien

```bash
# 1. Installeer dependencies
pip install -r requirements.txt

# 2. Start de app
streamlit run app.py
```

De app opent automatisch op http://localhost:8501

---

## Deployen op Streamlit Cloud (gratis, publieke URL)

1. Maak een gratis account op [github.com](https://github.com) als je die nog niet hebt
2. Maak een nieuwe repository aan: `lbsp-dashboard` (mag private zijn)
3. Push deze twee bestanden erin:
   - `app.py`
   - `requirements.txt`
4. Ga naar [share.streamlit.io](https://share.streamlit.io)
5. Log in met je GitHub account
6. Klik **New app** → kies je repo → branch `main` → main file `app.py`
7. Klik **Deploy** — na ~1 minuut heb je een publieke URL

De URL ziet er zo uit:  
`https://jouwgithubuser-lbsp-dashboard-app-xxxxx.streamlit.app`

Die URL kun je gewoon delen met Esther of anderen.

---

## Data updaten

1. Download nieuwe LinkedIn export via:  
   **LinkedIn Page → Analytics → Export** (rechtsboven)
2. Open de app
3. Klik **Browse files** en upload het nieuwe .xls bestand
4. Klaar — alles herberekent automatisch

---

## LinkedIn export downloaden

Ga naar je LinkedIn Organisatiepagina:
- **Analytics → Content** → Export → "Alle bijdragen"
- **Analytics → Updates** → Export → "Statistieken"

Beide sheets zitten in één .xls bestand.

---

## Nieuwe strategie datum aanpassen

In de sidebar kun je instellen vanaf welke maand de nieuwe strategie is gestart.  
Posts vóór die datum = baseline (blauw), erna = nieuwe strategie (oranje).
