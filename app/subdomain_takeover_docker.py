import os
import json
import subprocess
import pymongo
import time
from datetime import datetime, timedelta
from pymongo import MongoClient

# Configurazione del database MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")  # impostare questa variabile d'ambiente
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

def connect_db():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    return db[COLLECTION_NAME]

# --- FUNZIONE PER AGGIUNGERE DOMINI DA FILE ---
def add_domains_from_file(collection, file_path):
    
    if not os.path.exists(file_path):
        print(f"[ERRORE] Il file {file_path} non esiste.")
        return

    with open(file_path, "r") as file:
        domains = [line.strip() for line in file.readlines() if line.strip()]

    for domain in domains:
        result = collection.update_one(
            {"domain": domain},
            {"$setOnInsert": {"retrieve_date": None, "subdomains": []}},
            upsert=True
        )
        if result.upserted_id:
            print(f"[INFO] Dominio aggiunto: {domain}")
        else:
            print(f"[INFO] Dominio già presente: {domain}")

# --- FUNZIONI PER SUBFINDER ---
def fetch_domains_for_subfinder(collection):
    # recupero domini da analizzare se retrieve_date è null, non esiste o è precedente ad un mese
    one_month_ago = datetime.now() - timedelta(days=30)

    # Filtra i domini da MongoDB
    domains = collection.find({ "$or": [
        {"retrieve_date": {"$exists": False}},  
        {"retrieve_date": None},               
        {"retrieve_date": {"$lt": one_month_ago}} 
        ]
    })
    #domains = collection.find() #questo se vogliamo prenderli tutti
    return [d['domain'] for d in domains]

def save_subdomain_results(collection, domain, subdomains):
    
    for subdomain in subdomains:
        # Aggiorna la data di retrieve e aggiunge il sottodominio solo se non esiste già con addToSet
        collection.update_one(
            {"domain": domain},
            {
                "$set": {"retrieve_date": datetime.now()},
                "$addToSet": {"subdomains": {"name": subdomain, "vulnerable": False, "last_vulnerability_check": datetime(1970, 1, 1)}}
            },
            upsert=True
        )


def update_retrieve_date(collection, domain):
    # Aggiorna la data di retrieve del dominio dopo aver eseguito Subfinder
    collection.update_one(
        {"domain": domain},
        {"$set": {"retrieve_date": datetime.now()}}
    )

def run_subfinder(target_domain):
    subdomains_file = f"{target_domain}_subdom.txt"
    try:
        subprocess.run(
            ["subfinder", "-d", target_domain, "-o", subdomains_file],
            check=True
        )
        print(f"[INFO] Sottodomini trovati per {target_domain}: salvati in {subdomains_file}")
    except subprocess.CalledProcessError:
        print(f"[ERRORE] Nessun sottodominio trovato per {target_domain} con Subfinder.")
        return None
    return subdomains_file

# --- FUNZIONI PER NUCLEI ---
def update_vulnerability_status(collection, domain, subdomain, is_vulnerable):
    
    update_result = collection.update_one(
        {"domain": domain, "subdomains.name": subdomain},
        {"$set": {
            "subdomains.$.vulnerable": is_vulnerable, 
            "subdomains.$.last_vulnerability_check": datetime.now()
        }}
    )
    if update_result.modified_count > 0:
        print(f"[INFO] Aggiornato {subdomain} in {domain} con vulnerabilità: {is_vulnerable}")
    else:
        print(f"[ERRORE] Impossibile aggiornare {subdomain} in {domain}")

def run_nuclei(subdomains_file, collection, domain, subdomains):
    output_file = "output_nuclei.json"
    try:
        result = subprocess.run(
            [
                "nuclei", "-l", subdomains_file,
                "-t", "http/takeovers/",
                "-t", "dns/azure-takeover-detection.yaml",
                "-t", "dns/elasticbeanstalk-takeover.yaml",
                "-o", output_file,
                "-jsonl"
            ],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"prova")

        found_vulnerabilities = set()
        with open(output_file, "r") as f:
            for line in f:
                data = json.loads(line)
                if "host" in data:
                    found_vulnerabilities.add(data["host"])

        for subdomain in subdomains:
            is_vulnerable = subdomain in found_vulnerabilities
            update_vulnerability_status(collection, domain, subdomain, is_vulnerable)
        
        print(f"[INFO] Risultati di Nuclei salvati in {output_file}")
    except subprocess.CalledProcessError:
        print(f"[ERRORE] Errore durante l'esecuzione di Nuclei su {subdomains_file}")

# --- MAIN FUNCTION ---
def main():
    collection = connect_db()

    # Aggiunge domini da file (personalizzabile)
    file_path = "data/domains.txt"  # Specifica filepath
    add_domains_from_file(collection, file_path)

    # Analisi con Subfinder e Nuclei
    domains_for_subfinder = fetch_domains_for_subfinder(collection)
    for domain in domains_for_subfinder:
        # Trova sottodomini con Subfinder
        subdomains_file = run_subfinder(domain)
        if subdomains_file and os.path.getsize(subdomains_file) > 0:
            with open(subdomains_file, "r") as f:
                subdomains = [line.strip() for line in f.readlines()]
            
            # Salva i sottodomini nel database
            save_subdomain_results(collection, domain, subdomains)
            update_retrieve_date(collection, domain)

            # Verifica le vulnerabilità dei sottodomini trovati
            run_nuclei(subdomains_file, collection, domain, subdomains)
            
            # Rimuove il file temporaneo dei sottodomini
            os.remove(subdomains_file)
        else:
            print(f"[ERRORE] Nessun sottodominio trovato per {domain} con Subfinder.")
            update_retrieve_date(collection, domain)

    print("[INFO] Operazione completata.")



if __name__ == "__main__":
    main()
    

