# popola_generi.py
from pathlib import Path
import sys


# Configurazione percorsi
current_dir = Path(__file__).parent
project_root = current_dir.parent

sys.path.append(str(project_root))


from database import db, Genere
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(project_root / 'instance' / 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def popola_generi():
    with app.app_context():
        generi_predefiniti = [
            'Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi',
            'Thriller', 'Animation', 'Fantasy', 'Documentary', 'Western',
            'Children', 'Film-Noir', 'Mystery', 'Crime', 'War',
            'Adventure', 'Musical', 'IMAX'
        ]

        try:
            nuovi_generi = 0
            for nome_genere in generi_predefiniti:
                # Verifica se il genere esiste già
                if not Genere.query.filter_by(nome=nome_genere).first():
                    db.session.add(Genere(nome=nome_genere))
                    nuovi_generi += 1
                    print(f'Creato genere: {nome_genere}')
            
            db.session.commit()
            print(f"Popolamento completato. {nuovi_generi} nuovi generi aggiunti.")

        except Exception as e:
            db.session.rollback()
            print(f"Errore durante il popolamento: {str(e)}")

if __name__ == '__main__':
    popola_generi()