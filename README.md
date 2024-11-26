# Subdomain Takeover App

## Toolchain
1. Inserimento domini da analizzare nel database personale MongoDB
2. Recupero sotto domini attraverso il tool Subfinder (https://github.com/projectdiscovery/subfinder)
3. Analisi vulnerabilità "subdomains takeover" tramite il tool Nuclei (https://github.com/projectdiscovery/nuclei)
4. Salvataggio informazioni su database MongoDB

### Configurazione Subfinder
Subfinder, utilizzato per il recupero dei sottodomini, utilizza di base dei dataset gratuiti, tra cui crtsh per la Certificate Transparency. E' possibile aggiungere API di alcuni servizi aggiuntivi per rendere la ricerca più completa ed efficente nel file provider-config.yaml. 

### Nuclei
Nuclei, utilizzato come già detto per rilevare sottodomini vulnerabili al "subdomains takeover", utilizza i template presenti in "nuclei-templates/http/takeovers" e i template "dns/azure-takeover-detection.yaml" e "dns/elasticbeanstalk-takeover.yaml. 

### Configurazione MongoDB
Per poter utilizzare MongoDB, è necessario aggiungere Username, Password e Mongo_URI nel file docker-compose.yml, precisamente nei campi "MONGO_INITDB_ROOT_USERNAME", "MONGO_INITDB_ROOT_PASSWORD" e "MONGO_URI" per impostare correttamente le variabili d'ambiente. E' inoltre necessario modificare, sempre in questo file, le voci "DATABASE_NAME" e "COLLECTION_NAME" con i rispettivi nomi di database e collection.

### Docker
L'applicazione è completamente containerizzata, il che significa che è possibile eseguirla con Docker. Di seguito le istruzioni per configurare e avviare il progetto.

#### Requisiti
- Docker
- Docker Desktop

#### Configurazione e avvio 
1. Clonare il repository nell'ambiente locale

```bash
git clone https://github.com/matteo-coni/subdomain_takeover.git
cd repository
```

2. Seguire passaggi sopra citati per configurare le variabili d'ambiente per MongoDB

3. Eseguire il comando per avviare il container dell'applicazione e il database MongoDB:

```bash
docker-compose up --build
```

#### Stop e pulizia
Per fermare i container in esecuzione:
```bash
docker-compose down
```

Per rimuovere i container:
```bash
docker-compose down -v
```
