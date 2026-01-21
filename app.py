import streamlit as st
import pdfplumber
import pandas as pd
import re

# Tittel på siden
st.set_page_config(page_title="Startliste PDF til CSV", layout="centered")
st.title("🎿 Startliste Konverterer")
st.write("Last opp startlisten (PDF), så henter jeg ut NTG-utøverne og lager en CSV.")

# Filopplaster
uploaded_file = st.file_uploader("Last opp PDF her", type="pdf")

def extract_data_from_pdf(file):
    extracted_rows = []
    
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                # Vi sjekker først om linjen kan inneholde en NTG-utøver
                if "NTG" in line:
                    
                    # LOGIKK-ENDRING:
                    # I stedet for regex som gjetter, splitter vi linjen der det er 
                    # 2 eller flere mellomrom. Dette skiller kolonnene mye tryggere.
                    parts = re.split(r'\s{2,}', line.strip())
                    
                    # En typisk rad skal da bli seende slik ut i 'parts':
                    # ['113', 'Edvard Pålssønn Strømsæther', 'Nesodden IF / NTG-G', '11:56:30']
                    # Noen ganger kan det være flere deler, så vi må være litt fleksible.
                    
                    if len(parts) >= 3:
                        # Vi antar at siste felt er TID og første felt er STARTNUMMER
                        tid = parts[-1]
                        startnr = parts[0]
                        
                        # Dobbeltsjekk at det ser riktig ut (startnr er tall, tid har kolon)
                        if startnr.isdigit() and ":" in tid:
                            
                            # Klubben er vanligvis nest siste felt
                            klubb = parts[-2]
                            
                            # Navnet er alt som ligger mellom startnr og klubb
                            # (Vi slår sammen med mellomrom i tilfelle navnet ble delt opp)
                            navn = " ".join(parts[1:-2])
                            
                            # Sjekk at det faktisk er NTG-utøveren vi fant
                            if "NTG" in klubb or "NTG" in navn:
                                row = {
                                    "Navn": navn.strip(),
                                    "Startnummer": startnr,
                                    "Klubb/Team": klubb.strip(),
                                    "Starttid": tid
                                }
                                extracted_rows.append(row)

    return extracted_rows

if uploaded_file is not None:
    with st.spinner('Leser PDF...'):
        try:
            data = extract_data_from_pdf(uploaded_file)
            
            if data:
                # Lag DataFrame
                df = pd.DataFrame(data)
                
                # Sorter etter Starttid
                df = df.sort_values(by='Starttid')
                
                # Legg til nummerering (Nr. 1, 2, 3...)
                df.insert(0, 'Nr.', range(1, 1 + len(df)))
                
                # Vis tabellen på skjermen
                st.success(f"Fant {len(df)} utøvere fra NTG!")
                st.dataframe(df, hide_index=True)
                
                # Konverter til CSV for nedlasting
                csv = df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Last ned CSV-fil",
                    data=csv,
                    file_name="NTG_utovere.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Fant ingen utøvere med 'NTG' i klubbnavnet på linjer som kunne leses. Sjekk om PDF-en er et bilde eller tekst.")
                
        except Exception as e:
            st.error(f"En feil oppstod: {e}")
