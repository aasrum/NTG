import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="Startliste Fix", layout="wide")
st.title("🎿 Startliste Konverterer (Med Klasse)")

col1, col2 = st.columns([1, 2])
with col1:
    uploaded_file = st.file_uploader("Last opp PDF startliste", type="pdf")

def extract_data_with_class(file):
    extracted_rows = []
    current_class = "Ukjent" # Variabel for å huske hvilken klasse vi leser nå
    
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                stripped_line = line.strip()
                
                # --- 1. SJEKK OM LINJEN ER EN KLASSE-OVERSKRIFT ---
                # Logikk: Inneholder "km" og "fri" eller "klassisk" eller "år", men starter IKKE med et tall (startnr)
                # Eksempel: "J 15 år 5 km, fri"
                if "km" in stripped_line and not stripped_line[0].isdigit():
                    # Vi bruker regex for å finne alt FØR distansen (tallet før 'km')
                    # Vi ser etter mønsteret: (Noe tekst) (mellomrom) (tall) km
                    match_header = re.search(r'^(.*?)\s\d+(\s?km)', stripped_line)
                    if match_header:
                        # Henter ut gruppe 1 (teksten før distansen)
                        raw_class = match_header.group(1).strip()
                        # Fjerner eventuelle komma på slutten
                        if raw_class.endswith(","):
                            raw_class = raw_class[:-1]
                        
                        current_class = raw_class
                        # Vi hopper videre til neste linje siden dette ikke er en utøver
                        continue

                # --- 2. SJEKK OM LINJEN ER EN UTØVER ---
                parts = re.split(r'\s{2,}', stripped_line)
                
                if len(parts) >= 3:
                    startnr = parts[0]
                    tid = parts[-1]
                    
                    if startnr.isdigit() and ":" in tid:
                        klubb_del = parts[-2]
                        navn_del = " ".join(parts[1:-2])
                        
                        if not navn_del: 
                            navn_del = parts[1] 
                            if len(parts) == 3: 
                                klubb_del = "" 

                        row = {
                            "Startnummer": int(startnr),
                            "Navn": navn_del.strip(),
                            "Klubb/Team": klubb_del.strip(),
                            "Klasse": current_class,     # Legger til klassen vi fant sist
                            "Starttid_Sortering": tid    # Beholder tid kun for å kunne sortere listen riktig
                        }
                        extracted_rows.append(row)

    return extracted_rows

if uploaded_file:
    with st.spinner('Leser PDF og henter klasser...'):
        all_data = extract_data_with_class(uploaded_file)
        
        if all_data:
            # Lag DataFrame
            df = pd.DataFrame(all_data)
            
            # Sorter listen basert på starttid (som vi midlertidig har med)
            df = df.sort_values(by='Starttid_Sortering')
            
            # Legg til "Wave" (nummerering) helt først
            df.insert(0, 'Wave', range(1, 1 + len(df)))
            
            # Fjern sorterings-kolonnen for tid, siden du ikke ville ha den i sluttresultatet
            df = df.drop(columns=['Starttid_Sortering'])

            # --- VISNING OG FILTRERING ---
            
            # Filtrer ut NTG
            df_ntg = df[df['Klubb/Team'].str.contains("NTG", case=False, na=False)].copy()
            # Reset Wave-nummerering for NTG-listen slik at den starter på 1
            df_ntg['Wave'] = range(1, 1 + len(df_ntg))
            
            st.success(f"Behandlet ferdig! Fant {len(df)} utøvere.")
            
            tab1, tab2 = st.tabs(["Hele Startlisten", "Kun NTG"])
            
            with tab1:
                st.dataframe(df, hide_index=True, use_container_width=True)
                csv_all = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Last ned HELE listen (.csv)", csv_all, "Hele_Startlisten.csv", "text/csv")
                
            with tab2:
                st.dataframe(df_ntg, hide_index=True, use_container_width=True)
                csv_ntg = df_ntg.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Last ned kun NTG (.csv)", csv_ntg, "NTG_liste.csv", "text/csv")
                
        else:
            st.warning("Fant ingen data. Sjekk PDF-en.")
