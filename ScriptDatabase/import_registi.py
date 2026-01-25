import sys
import csv
from pathlib import Path

# Configurazione percorsi
current_dir = Path(__file__).parent
project_root = current_dir.parent
CSV_PATH = project_root / 'data' / 'registi.csv'

sys.path.append(str(project_root))

from flask import Flask
from database import db, Regista

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(project_root / 'instance' / 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def importa_registi():
    app = create_app()
    
    with app.app_context():
        try:
            if not CSV_PATH.exists():
                print(f"[ERRORE] File non trovato: {CSV_PATH}")
                return

            print("\n[INFO] Inizio importazione registi...")
            
            
            with open(CSV_PATH, 'r', encoding='utf-8-sig') as file:
                
                dialect = csv.Sniffer().sniff(file.read(1024))
                file.seek(0)
                csv_reader = csv.DictReader(file, dialect=dialect)
                
                
                print("Intestazioni rilevate:", csv_reader.fieldnames)
                
                # Normalizza nomi colonne
                normalized_headers = [header.strip().lower().replace(' ', '_') for header in csv_reader.fieldnames]
                id_header = next((h for h in normalized_headers if 'id' in h), None)
                name_header = next((h for h in normalized_headers if 'nome' in h or 'name' in h), None)

                if not id_header or not name_header:
                    print("[ERRORE] Struttura CSV non valida. Assicurati di avere colonne per ID e Nome")
                    print("Esempio atteso: regista_id,nome_regista")
                    return
                
                total = 0
                successi = 0
                errori = 0

                for riga in csv_reader:
                    total += 1
                    try:
                        
                        regista_id = int(riga[id_header].strip())
                        nome = riga[name_header].strip()

                       
                        if db.session.get(Regista, regista_id):
                            print(f"[WARN] Regista ID {regista_id} già esistente, salto")
                            errori += 1
                            continue

                        # Crea nuovo regista
                        db.session.add(Regista(
                            id_regista=regista_id,
                            nome=nome
                        ))
                        successi += 1

                        # Commit ogni 50 record
                        if successi % 50 == 0:
                            db.session.commit()

                    except ValueError as e:
                        print(f"[ERRORE] Riga {total}: {str(e)}")
                        errori += 1
                    except Exception as e:
                        print(f"[ERRORE] Riga {total}: {str(e)}")
                        errori += 1

                # Commit finale
                db.session.commit()
                print("\n[RIEPILOGO]")
                print(f"Righe processate: {total}")
                print(f"Registi importati: {successi}")
                print(f"Errori: {errori}")

        except Exception as e:
            db.session.rollback()
            print(f"\n[ERRORE CRITICO] {str(e)}")

if __name__ == "__main__":
    importa_registi()