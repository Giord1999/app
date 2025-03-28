import uuid
import json
from datetime import datetime
from loan import DbManager, Loan

class LoanCRM:
    """
    Classe per gestire il CRM dei clienti legati ai prestiti.
    Implementa le operazioni per creare e aggiornare i clienti,
    associare un cliente a un prestito e registrare le interazioni.
    """
    def __init__(self, db_manager: DbManager):
        self.db_manager = db_manager

        #Individual client tables initialization
        self._create_clients_table()
        self._create_client_loans_table()
        self._create_client_interactions_table()

        #Corporate tables initialization
        self._create_corporations_table()
        self._create_corporation_loans_table()
        self._create_corporation_interactions_table()


    def _create_clients_table(self):
        """
        Crea la tabella 'clients' per memorizzare i dati anagrafici e finanziari dei clienti.
        """
        query = """
        CREATE TABLE IF NOT EXISTS clients (
            client_id UUID PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            birth_date DATE,
            address TEXT,
            city VARCHAR(100),
            state VARCHAR(100),
            zip_code VARCHAR(20),
            country VARCHAR(100),
            phone VARCHAR(50),
            email VARCHAR(100),
            occupation VARCHAR(100),
            employer VARCHAR(100),
            income DECIMAL(15,2),
            credit_score INTEGER,
            documents JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_clients_name ON clients (first_name, last_name);
        CREATE INDEX IF NOT EXISTS idx_clients_email ON clients (email);
        CREATE INDEX IF NOT EXISTS idx_clients_occupation ON clients (occupation);
        CREATE INDEX IF NOT EXISTS idx_clients_employer ON clients (employer);
        CREATE INDEX IF NOT EXISTS idx_clients_income ON clients (income);
        CREATE INDEX IF NOT EXISTS idx_clients_credit_score ON clients (credit_score);
        """
        self.db_manager.execute_db_query(query)

    def _create_client_loans_table(self):
        """
        Crea la tabella 'client_loans' per memorizzare l'associazione tra clienti e prestiti.
        """
        query = """
        CREATE TABLE IF NOT EXISTS client_loans (
            client_id UUID REFERENCES clients(client_id),
            loan_id UUID REFERENCES loans(loan_id),
            assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (client_id, loan_id)
        )
        """
        self.db_manager.execute_db_query(query)

    def _create_client_interactions_table(self):
        """
        Crea la tabella 'client_interactions' per registrare le interazioni con i clienti.
        """
        query = """
        CREATE TABLE IF NOT EXISTS client_interactions (
            interaction_id UUID PRIMARY KEY,
            client_id UUID REFERENCES clients(client_id),
            interaction_type VARCHAR(50),
            notes TEXT,
            interaction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_client_interactions_client_id ON client_interactions (client_id);
        CREATE INDEX IF NOT EXISTS idx_client_interactions_interaction_type ON client_interactions (interaction_type);
        CREATE INDEX IF NOT EXISTS idx_client_interactions_interaction_date ON client_interactions (interaction_date);
        """
        self.db_manager.execute_db_query(query)

    def add_client(self, client_data: dict) -> str:
        """
        Aggiunge un nuovo cliente.
        
        Args:
            client_data (dict): Dizionario contenente i dati del cliente (es. first_name, last_name, email, ecc.).
        
        Returns:
            str: Il client_id generato o passato.
        """
        client_id = client_data.get("client_id") or str(uuid.uuid4())
        query = """
        INSERT INTO clients (
            client_id, first_name, last_name, birth_date, address, city, state, zip_code, country, phone, email,
            occupation, employer, income, credit_score, documents
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        parameters = (
            client_id,
            client_data.get("first_name"),
            client_data.get("last_name"),
            client_data.get("birth_date"),
            client_data.get("address"),
            client_data.get("city"),
            client_data.get("state"),
            client_data.get("zip_code"),
            client_data.get("country"),
            client_data.get("phone"),
            client_data.get("email"),
            client_data.get("occupation"),
            client_data.get("employer"),
            client_data.get("income"),
            client_data.get("credit_score"),
            json.dumps(client_data.get("documents")) if client_data.get("documents") else None
        )
        self.db_manager.execute_db_query(query, parameters)
        return client_id

    def update_client(self, client_id: str, updated_data: dict) -> bool:
        """
        Aggiorna i dati di un cliente.
        
        Args:
            client_id (str): L'ID del cliente.
            updated_data (dict): Dizionario con i campi da aggiornare.
        
        Returns:
            bool: True se l'aggiornamento va a buon fine.
        """
        set_clauses = []
        params = []
        for key, value in updated_data.items():
            # Se aggiorniamo documenti, convertiamoli in JSON
            if key == "documents" and value is not None:
                value = json.dumps(value)
            set_clauses.append(f"{key} = %s")
            params.append(value)
        # Aggiorna automaticamente il timestamp
        set_clauses.append("updated_at = %s")
        params.append(datetime.utcnow())
        query = f"UPDATE clients SET {', '.join(set_clauses)} WHERE client_id = %s"
        params.append(client_id)
        self.db_manager.execute_db_query(query, tuple(params))
        return True

    def delete_client(self, client_id: str) -> bool:
        """
        Elimina un cliente e le sue associazioni/interazioni.
        
        Args:
            client_id (str): L'ID del cliente.
        
        Returns:
            bool: True se l'eliminazione va a buon fine.
        """
        # Elimina prima le interazioni e le associazioni, poi il record cliente
        self.db_manager.execute_db_query("DELETE FROM client_interactions WHERE client_id = %s", (client_id,))
        self.db_manager.execute_db_query("DELETE FROM client_loans WHERE client_id = %s", (client_id,))
        self.db_manager.execute_db_query("DELETE FROM clients WHERE client_id = %s", (client_id,))
        return True

    def get_client(self, client_id: str) -> dict:
        """
        Recupera i dati di un cliente.
        
        Args:
            client_id (str): L'ID del cliente.
        
        Returns:
            dict: Un dizionario con i dati del cliente (vuoto se non trovato).
        """
        query = "SELECT * FROM clients WHERE client_id = %s"
        cursor = self.db_manager.execute_db_query(query, (client_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            client = dict(zip(columns, row))
            if client.get("documents"):
                client["documents"] = json.loads(client["documents"])
            return client
        return {}

    def list_clients(self) -> list:
        """
        Restituisce la lista di tutti i clienti.
        
        Returns:
            list: Lista di dizionari contenenti i dati dei clienti.
        """
        query = "SELECT * FROM clients ORDER BY created_at DESC"
        cursor = self.db_manager.execute_db_query(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        clients = []
        for row in rows:
            client = dict(zip(columns, row))
            if client.get("documents"):
                client["documents"] = json.loads(client["documents"])
            clients.append(client)
        return clients

    def assign_loan_to_client(self, client_id: str, loan_id: str) -> bool:
        """
        Associa un prestito a un cliente.
        
        Args:
            client_id (str): L'ID del cliente.
            loan_id (str): L'ID del prestito.
        
        Returns:
            bool: True se l'associazione viene registrata correttamente.
        """
        query = "INSERT INTO client_loans (client_id, loan_id) VALUES (%s, %s)"
        self.db_manager.execute_db_query(query, (client_id, loan_id))
        return True

    def record_interaction(self, client_id: str, interaction_type: str, notes: str) -> str:
        """
        Registra un'interazione (es. contatto telefonico, email, appuntamento) per un cliente.
        
        Args:
            client_id (str): L'ID del cliente.
            interaction_type (str): Il tipo di interazione (es. "telefono", "email", "incontro").
            notes (str): Note o dettagli sull'interazione.
        
        Returns:
            str: L'ID dell'interazione registrata.
        """
        interaction_id = str(uuid.uuid4())
        query = """
        INSERT INTO client_interactions (interaction_id, client_id, interaction_type, notes)
        VALUES (%s, %s, %s, %s)
        """
        self.db_manager.execute_db_query(query, (interaction_id, client_id, interaction_type, notes))
        return interaction_id

    def get_interactions(self, client_id: str) -> list:
        """
        Recupera tutte le interazioni registrate per un dato cliente.
        
        Args:
            client_id (str): L'ID del cliente.
        
        Returns:
            list: Lista di dizionari contenenti i dati delle interazioni.
        """
        query = "SELECT * FROM client_interactions WHERE client_id = %s ORDER BY interaction_date DESC"
        cursor = self.db_manager.execute_db_query(query, (client_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        interactions = [dict(zip(columns, row)) for row in rows]
        return interactions

    def get_client_loans(self, client_id: str) -> list:
        """
        Recupera tutti i prestiti associati a un cliente.
        
        Args:
            client_id (str): L'ID del cliente.
        
        Returns:
            list: Lista di prestiti associati al cliente.
        """
        query = """
        SELECT l.* 
        FROM client_loans cl
        JOIN loans l ON cl.loan_id = l.loan_id
        WHERE cl.client_id = %s
        """
        cursor = self.db_manager.execute_db_query(query, (client_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        loans = [dict(zip(columns, row)) for row in rows]
        return loans

    def get_client_details(self, client_id: str) -> dict:
        """
        Recupera i dati dettagliati di un cliente, includendo prestiti e interazioni.
        
        Args:
            client_id (str): L'ID del cliente.
        
        Returns:
            dict: Un dizionario con i dati dettagliati del cliente.
        """
        # Get basic client data
        client_data = self.get_client(client_id)
        if not client_data:
            return {}
        
        # Get client's loans
        client_data['loans'] = self.get_client_loans(client_id)
        
        # Get client's interactions
        client_data['interactions'] = self.get_interactions(client_id)
        
        # Calculate additional metrics
        client_data['loan_count'] = len(client_data['loans'])
        client_data['total_debt'] = sum(loan.get('loan_amount', 0) for loan in client_data['loans'])
        client_data['interaction_count'] = len(client_data['interactions'])
        
        # Calculate age if birth_date is available
        if 'birth_date' in client_data and client_data['birth_date']:
            try:
                birth_date = datetime.strptime(str(client_data['birth_date']), '%Y-%m-%d')
                today = datetime.now()
                client_data['age'] = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            except:
                client_data['age'] = None
        else:
            client_data['age'] = None
        
        # Add region from city/state for geographical segmentation
        client_data['region'] = client_data.get('state') or client_data.get('city') or 'Unknown'
        
        return client_data
    
    def _create_corporations_table(self):
        """
        Crea la tabella 'corporations' per memorizzare i dati delle aziende.
        """
        query = """
        CREATE TABLE IF NOT EXISTS corporations (
            corporation_id UUID PRIMARY KEY,
            company_name VARCHAR(200) NOT NULL,
            business_type VARCHAR(100),
            incorporation_date DATE,
            registration_number VARCHAR(100),
            tax_id VARCHAR(100),
            industry VARCHAR(100),
            annual_revenue DECIMAL(20,2),
            number_of_employees INTEGER,
            headquarters_address TEXT,
            city VARCHAR(100),
            state VARCHAR(100),
            zip_code VARCHAR(20),
            country VARCHAR(100),
            phone VARCHAR(50),
            email VARCHAR(100),
            website VARCHAR(200),
            primary_contact_name VARCHAR(200),
            primary_contact_role VARCHAR(100),
            documents JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_corporations_name ON corporations (company_name);
        CREATE INDEX IF NOT EXISTS idx_corporations_industry ON corporations (industry);
        CREATE INDEX IF NOT EXISTS idx_corporations_revenue ON corporations (annual_revenue);
        CREATE INDEX IF NOT EXISTS idx_corporations_employees ON corporations (number_of_employees);
        """
        self.db_manager.execute_db_query(query)

    def _create_corporation_loans_table(self):
        """
        Crea la tabella 'corporation_loans' per associare aziende e prestiti.
        """
        query = """
        CREATE TABLE IF NOT EXISTS corporation_loans (
            corporation_id UUID REFERENCES corporations(corporation_id),
            loan_id UUID REFERENCES loans(loan_id),
            assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (corporation_id, loan_id)
        )
        """
        self.db_manager.execute_db_query(query)

    def _create_corporation_interactions_table(self):
        """
        Crea la tabella 'corporation_interactions' per registrare le interazioni con le aziende.
        """
        query = """
        CREATE TABLE IF NOT EXISTS corporation_interactions (
            interaction_id UUID PRIMARY KEY,
            corporation_id UUID REFERENCES corporations(corporation_id),
            interaction_type VARCHAR(50),
            notes TEXT,
            interaction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_corporation_interactions_corporation_id 
            ON corporation_interactions (corporation_id);
        CREATE INDEX IF NOT EXISTS idx_corporation_interactions_interaction_type 
            ON corporation_interactions (interaction_type);
        CREATE INDEX IF NOT EXISTS idx_corporation_interactions_interaction_date 
            ON corporation_interactions (interaction_date);
        """
        self.db_manager.execute_db_query(query)

    def add_corporation(self, corporation_data: dict) -> str:
        """
        Aggiunge una nuova azienda.
        
        Args:
            corporation_data (dict): Dizionario contenente i dati dell'azienda.
        
        Returns:
            str: Il corporation_id generato o passato.
        """
        corporation_id = corporation_data.get("corporation_id") or str(uuid.uuid4())
        query = """
        INSERT INTO corporations (
            corporation_id, company_name, business_type, incorporation_date, 
            registration_number, tax_id, industry, annual_revenue, number_of_employees,
            headquarters_address, city, state, zip_code, country, phone, email,
            website, primary_contact_name, primary_contact_role, documents
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        parameters = (
            corporation_id,
            corporation_data.get("company_name"),
            corporation_data.get("business_type"),
            corporation_data.get("incorporation_date"),
            corporation_data.get("registration_number"),
            corporation_data.get("tax_id"),
            corporation_data.get("industry"),
            corporation_data.get("annual_revenue"),
            corporation_data.get("number_of_employees"),
            corporation_data.get("headquarters_address"),
            corporation_data.get("city"),
            corporation_data.get("state"),
            corporation_data.get("zip_code"),
            corporation_data.get("country"),
            corporation_data.get("phone"),
            corporation_data.get("email"),
            corporation_data.get("website"),
            corporation_data.get("primary_contact_name"),
            corporation_data.get("primary_contact_role"),
            json.dumps(corporation_data.get("documents")) if corporation_data.get("documents") else None
        )
        self.db_manager.execute_db_query(query, parameters)
        return corporation_id

    def update_corporation(self, corporation_id: str, updated_data: dict) -> bool:
        """
        Aggiorna i dati di un'azienda.
        
        Args:
            corporation_id (str): L'ID dell'azienda.
            updated_data (dict): Dizionario con i campi da aggiornare.
        
        Returns:
            bool: True se l'aggiornamento va a buon fine.
        """
        set_clauses = []
        params = []
        for key, value in updated_data.items():
            if key == "documents" and value is not None:
                value = json.dumps(value)
            set_clauses.append(f"{key} = %s")
            params.append(value)
        set_clauses.append("updated_at = %s")
        params.append(datetime.utcnow())
        query = f"UPDATE corporations SET {', '.join(set_clauses)} WHERE corporation_id = %s"
        params.append(corporation_id)
        self.db_manager.execute_db_query(query, tuple(params))
        return True

    def delete_corporation(self, corporation_id: str) -> bool:
        """
        Elimina un'azienda e le sue associazioni/interazioni.
        
        Args:
            corporation_id (str): L'ID dell'azienda.
        
        Returns:
            bool: True se l'eliminazione va a buon fine.
        """
        self.db_manager.execute_db_query("DELETE FROM corporation_interactions WHERE corporation_id = %s", (corporation_id,))
        self.db_manager.execute_db_query("DELETE FROM corporation_loans WHERE corporation_id = %s", (corporation_id,))
        self.db_manager.execute_db_query("DELETE FROM corporations WHERE corporation_id = %s", (corporation_id,))
        return True

    def get_corporation(self, corporation_id: str) -> dict:
        """
        Recupera i dati di un'azienda.
        
        Args:
            corporation_id (str): L'ID dell'azienda.
        
        Returns:
            dict: Un dizionario con i dati dell'azienda (vuoto se non trovata).
        """
        query = "SELECT * FROM corporations WHERE corporation_id = %s"
        cursor = self.db_manager.execute_db_query(query, (corporation_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            corporation = dict(zip(columns, row))
            if corporation.get("documents"):
                corporation["documents"] = json.loads(corporation["documents"])
            return corporation
        return {}

    def list_corporations(self) -> list:
        """
        Restituisce la lista di tutte le aziende.
        
        Returns:
            list: Lista di dizionari contenenti i dati delle aziende.
        """
        query = "SELECT * FROM corporations ORDER BY created_at DESC"
        cursor = self.db_manager.execute_db_query(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        corporations = []
        for row in rows:
            corporation = dict(zip(columns, row))
            if corporation.get("documents"):
                corporation["documents"] = json.loads(corporation["documents"])
            corporations.append(corporation)
        return corporations

    def assign_loan_to_corporation(self, corporation_id: str, loan_id: str) -> bool:
        """
        Associa un prestito a un'azienda.
        
        Args:
            corporation_id (str): L'ID dell'azienda.
            loan_id (str): L'ID del prestito.
        
        Returns:
            bool: True se l'associazione viene registrata correttamente.
        """
        query = "INSERT INTO corporation_loans (corporation_id, loan_id) VALUES (%s, %s)"
        self.db_manager.execute_db_query(query, (corporation_id, loan_id))
        return True

    def record_corporation_interaction(self, corporation_id: str, interaction_type: str, notes: str) -> str:
        """
        Registra un'interazione per un'azienda.
        
        Args:
            corporation_id (str): L'ID dell'azienda.
            interaction_type (str): Il tipo di interazione (es. "telefono", "email", "incontro").
            notes (str): Note o dettagli sull'interazione.
        
        Returns:
            str: L'ID dell'interazione registrata.
        """
        interaction_id = str(uuid.uuid4())
        query = """
        INSERT INTO corporation_interactions (interaction_id, corporation_id, interaction_type, notes)
        VALUES (%s, %s, %s, %s)
        """
        self.db_manager.execute_db_query(query, (interaction_id, corporation_id, interaction_type, notes))
        return interaction_id

    def get_corporation_interactions(self, corporation_id: str) -> list:
        """
        Recupera tutte le interazioni registrate per una data azienda.
        
        Args:
            corporation_id (str): L'ID dell'azienda.
        
        Returns:
            list: Lista di dizionari contenenti i dati delle interazioni.
        """
        query = "SELECT * FROM corporation_interactions WHERE corporation_id = %s ORDER BY interaction_date DESC"
        cursor = self.db_manager.execute_db_query(query, (corporation_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        interactions = [dict(zip(columns, row)) for row in rows]
        return interactions

    def get_corporation_loans(self, corporation_id: str) -> list:
        """
        Recupera tutti i prestiti associati a un'azienda.
        
        Args:
            corporation_id (str): L'ID dell'azienda.
        
        Returns:
            list: Lista di prestiti associati all'azienda.
        """
        query = """
        SELECT l.* 
        FROM corporation_loans cl
        JOIN loans l ON cl.loan_id = l.loan_id
        WHERE cl.corporation_id = %s
        """
        cursor = self.db_manager.execute_db_query(query, (corporation_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        loans = [dict(zip(columns, row)) for row in rows]
        return loans

    def get_corporation_details(self, corporation_id: str) -> dict:
        """
        Recupera i dati dettagliati di un'azienda, includendo prestiti e interazioni.
        
        Args:
            corporation_id (str): L'ID dell'azienda.
        
        Returns:
            dict: Un dizionario con i dati dettagliati dell'azienda.
        """
        # Get basic corporation data
        corporation_data = self.get_corporation(corporation_id)
        if not corporation_data:
            return {}
        
        # Get corporation's loans
        corporation_data['loans'] = self.get_corporation_loans(corporation_id)
        
        # Get corporation's interactions
        corporation_data['interactions'] = self.get_corporation_interactions(corporation_id)
        
        # Calculate additional metrics
        corporation_data['loan_count'] = len(corporation_data['loans'])
        corporation_data['total_debt'] = sum(loan.get('loan_amount', 0) for loan in corporation_data['loans'])
        corporation_data['interaction_count'] = len(corporation_data['interactions'])
        
        # Calculate company age if incorporation_date is available
        if 'incorporation_date' in corporation_data and corporation_data['incorporation_date']:
            try:
                incorporation_date = datetime.strptime(str(corporation_data['incorporation_date']), '%Y-%m-%d')
                today = datetime.now()
                corporation_data['company_age_years'] = today.year - incorporation_date.year
            except:
                corporation_data['company_age_years'] = None
        else:
            corporation_data['company_age_years'] = None
        
        return corporation_data
