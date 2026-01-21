import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="Startliste Fix", layout="wide") # Bruker bredere layout
st.title("🎿 Startliste Konverterer (Alle + NTG)")

col1, col2 = st.columns([1, 2])
with col1:
    uploaded_file = st.file_uploader("Last opp PDF startliste", type="pdf")

def extract_all_data(file):
    extracted_rows = []
    
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            # layout=True er viktig for å skille kolonner
            text = page.extract_text(layout=True)
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                # Vi splitter linjen der det er 2 eller flere mellomrom
                parts = re.split(r'\s{2,}', line.strip())
                
                # Vi ser etter linjer som har minst 3 deler: Startnr ... Klubb ... Tid
                if len(parts) >= 3:
                    startnr = parts[0]
                    tid = parts[-1]
                    
                    # Enkel validering: Startnr må være tall, Tid må ha kolon
                    if startnr.isdigit() and ":" in tid:
                        
                        # LOGIKK FOR Å SKILLE NAVN OG KLUBB:
                        # Vi antar at "Tid" er siste element.
                        # Vi antar at "Klubb" er elementet FØR tiden (nest sist).
                        # Vi antar at "Navn" er alt mellom Startnr og Klubb.
                        
                        # Hent ut delene
                        klubb_del = parts[-2]
                        # Slå sammen alle deler mellom startnr (indeks 0) og klubb (indeks -2) til navn
                        navn_del = " ".join(parts[1:-2])
                        
                        # Hvis navn ble tomt (f.eks. hvis listen bare har [Nr, NavnOgKlubb, Tid]),
                        # må vi gjøre en justering. Men med layout=True er de oftest adskilt.
                        if not navn_del: 
                            # Fallback: Kanskje del 1 inneholder både navn og klubb?
                            # Vi lar det stå slik for nå, da layout=True oftest løser dette.
                            navn_del = parts[1] 
                            if len(parts) == 3: # Hvis vi bare har 3 deler totalt
                                klubb_del = "" # Klarte ikke skille ut klubb

                        row = {
                            "Startnummer": int(startnr), # Lagrer som tall for sortering
                            "Navn": navn_del.strip(),
                            "Klubb/Team": klubb_del.strip(),
                            "Starttid": tid
                        }
                        extracted_rows.append(row)

    return extracted_rows

if uploaded_file:
    with st.spinner('Leser hele startlisten...'):
        all_data = extract_all_data(uploaded_file)
        
        if all_data:
            # 1. LAG FULL LISTE
            df_all = pd.DataFrame(all_data)
            df_all = df_all.sort_values(by='Starttid')
            
            # Legg til rangering/rekkefølge
            df_all.insert(0, 'Nr.', range(1, 1 + len(df_all)))

            # 2. LAG NTG-FILTERT LISTE
            # Vi filtrerer der Klubb/Team inneholder "NTG" (case insensitive)
            df_ntg = df_all[df_all['Klubb/Team'].str.contains("NTG", case=False, na=False)].copy()
            # Renummerer NTG-listen fra 1
            df_ntg['Nr.'] = range(1, 1 + len(df_ntg))
            
            # --- VISNING ---
            
            st.success(f"Fant totalt {len(df_all)} startende ({len(df_ntg)} fra NTG).")
            
            tab1, tab2 = st.tabs(["Hele Startlisten", "Kun NTG"])
            
            with tab1:
                st.dataframe(df_all, hide_index=True, use_container_width=True)
                csv_all = df_all.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Last ned HELE listen (.csv)",
                    data=csv_all,
                    file_name="Hele_Startlisten.csv",
                    mime="text/csv",
                )
                
            with tab2:
                st.dataframe(df_ntg, hide_index=True, use_container_width=True)
                csv_ntg = df_ntg.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Last ned kun NTG (.csv)",
                    data=csv_ntg,
                    file_name="NTG_utovere.csv",
                    mime="text/csv",
                )
                
        else:
            st.warning("Fant ingen lesbare rader. Sjekk PDF-formatet.")
