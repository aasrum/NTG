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
            # Vi henter ut teksten linje for linje
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            # Regex for å finne linjer som ser ut som en startende utøver
            # Ser etter: Startnr (tall) + Navn + Klubb + Tid (XX:XX:XX)
            # Dette er en generell pattern som må justeres hvis PDF-formatet endrer seg drastisk
            for line in lines:
                # Sjekk om linjen inneholder "NTG" før vi bruker tid på å parse den
                if "NTG" in line:
                    # Enkel logikk: Vi antar at linjen slutter med tid (00:00:00) og starter med startnummer
                    # Eksempel linje: "113 Edvard Strømsæther Nesodden IF / NTG-G 11:56:30"
                    
                    # Regex for å fange opp strukturen
                    match = re.search(r'^(\d+)\s+(.+?)\s+(.+?)\s+(\d{2}:\d{2}:\d{2})$', line)
                    
                    if match:
                        startnr, navn, klubb, tid = match.groups()
                        
                        # Dobbeltsjekk at det faktisk er en NTG-utøver i klubbnavnet (for sikkerhets skyld)
                        if "NTG" in klubb or "NTG" in navn: # Noen ganger havner klubb i navnefeltet ved feilparsing
                            
                            # Prøv å finne årsklasse basert på startnummer eller kontekst hvis mulig
                            # Siden årsklasse ofte står i en overskrift over tabellen, er det vanskelig å fange per linje.
                            # Vi setter den som "Ukjent/Se startnr" eller lar bruker fylle ut, 
                            # men for enkelhets skyld i denne koden utelater vi den eller setter den generisk.
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
