Installation du projet :
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

Pour tout lancer avec docker :
docker compose up -d

pour tout lancer, sauf le serveur fastapi :
docker compose up -d postgres minio prometheus grafana
et dcp de l'autre côté on fait : python main.py
