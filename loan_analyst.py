import numpy as np
import numpy_financial as npf
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import psycopg2
from scipy import stats
from scipy.optimize import brentq
import random
from ecbdata import ecbdata
from datetime import datetime 



class DbManager:
    def __init__(self, dbname, user, password, host='localhost', port='5432'):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
 
    def connect(self):
        print(f"DEBUG: Connessione a DB {self.dbname} su {self.host}:{self.port} con utente {self.user}")  # <-- Stampa dettagli
        return psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )


    def execute_db_query(self, query, parameters=()):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, parameters)
            conn.commit()
            return cursor

    def create_db(self):
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''CREATE TABLE IF NOT EXISTS loans(
                    loan_id UUID PRIMARY KEY,
                    initial_rate DECIMAL(8,6) NOT NULL,
                    initial_term INTEGER NOT NULL,
                    loan_amount DECIMAL(15,2) NOT NULL,
                    amortization_type VARCHAR(20) NOT NULL CHECK (amortization_type IN ('French', 'Italian')),
                    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('monthly', 'quarterly', 'semi-annual', 'annual')),
                    rate_type VARCHAR(10) NOT NULL CHECK (rate_type IN ('fixed', 'variable')),
                    use_euribor BOOLEAN DEFAULT FALSE,
                    update_frequency VARCHAR(20) CHECK (update_frequency IN ('monthly', 'quarterly', 'semi-annual', 'annual')),
                    downpayment_percent DECIMAL(5,2) DEFAULT 0,
                    start_date DATE NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
                ''');

                cursor.execute('''CREATE TABLE IF NOT EXISTS additional_costs(
                    loan_id UUID REFERENCES loans(loan_id),
                    description VARCHAR(255) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    PRIMARY KEY (loan_id, description)
                )
                ''');

                cursor.execute('''CREATE TABLE IF NOT EXISTS periodic_expenses(
                    loan_id UUID REFERENCES loans(loan_id),
                    description VARCHAR(255) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    PRIMARY KEY (loan_id, description)
                )
                ''');

                cursor.execute(''' CREATE TABLE IF NOT EXISTS amortization_schedule(
                    payment_id UUID PRIMARY KEY,
                    loan_id UUID REFERENCES loans(loan_id),
                    payment_date DATE NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    interest DECIMAL(15,2) NOT NULL,
                    principal DECIMAL(15,2) NOT NULL,
                    balance DECIMAL(15,2) NOT NULL
                )
                ''')

                 # Creazione degli indici
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_amortization_loan_id ON amortization_schedule(loan_id);
                CREATE INDEX IF NOT EXISTS idx_additional_costs_loan_id ON additional_costs(loan_id);
                CREATE INDEX IF NOT EXISTS idx_periodic_expenses_loan_id ON periodic_expenses(loan_id);
                ''');

    def save_loan(self, loan):
        with self.connect() as conn:
            try:
                cursor = conn.cursor()
                
                # Convert numpy values to Python native types
                initial_rate = float(loan.initial_rate)
                initial_term = int(loan.initial_term)
                loan_amount = float(loan.loan_amount)
                downpayment_percent = float(loan.downpayment_percent)
                
                # Check if loan exists
                check_query = "SELECT COUNT(*) FROM loans WHERE loan_id = %s"
                cursor.execute(check_query, (loan.loan_id,))
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    update_query = '''
                    UPDATE loans SET 
                        initial_rate = %s, initial_term = %s, loan_amount = %s, 
                        amortization_type = %s, frequency = %s, rate_type = %s,
                        use_euribor = %s, update_frequency = %s, downpayment_percent = %s,
                        start_date = %s, active = %s
                    WHERE loan_id = %s
                    '''
                    cursor.execute(update_query, (
                        initial_rate, initial_term, loan_amount,
                        loan.amortization_type, loan.frequency, loan.rate_type,
                        loan.use_euribor, loan.update_frequency, downpayment_percent,
                        loan.start.date(), loan.active, loan.loan_id
                    ))
                else:
                    insert_query = '''
                    INSERT INTO loans (
                        loan_id, initial_rate, initial_term, loan_amount, 
                        amortization_type, frequency, rate_type, use_euribor,
                        update_frequency, downpayment_percent, start_date, active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    '''
                    cursor.execute(insert_query, (
                        loan.loan_id, initial_rate, initial_term, loan_amount,
                        loan.amortization_type, loan.frequency, loan.rate_type,
                        loan.use_euribor, loan.update_frequency, downpayment_percent,
                        loan.start.date(), loan.active
                    ))

                # Save additional costs (one-time costs) - moved outside if/else
                cursor.execute("DELETE FROM additional_costs WHERE loan_id = %s", (loan.loan_id,))
                for desc, amount in loan.additional_costs.items():
                    cursor.execute("""
                        INSERT INTO additional_costs (loan_id, description, amount)
                        VALUES (%s, %s, %s)
                    """, (loan.loan_id, desc, float(amount)))

                # Save periodic expenses (recurring costs) - moved outside if/else
                cursor.execute("DELETE FROM periodic_expenses WHERE loan_id = %s", (loan.loan_id,))
                for desc, amount in loan.periodic_expenses.items():
                    cursor.execute("""
                        INSERT INTO periodic_expenses (loan_id, description, amount)
                        VALUES (%s, %s, %s)
                    """, (loan.loan_id, desc, float(amount)))
                    
                # Save amortization table
                cursor.execute("DELETE FROM amortization_schedule WHERE loan_id = %s", (loan.loan_id,))
                for index, row in loan.table.iterrows():
                    cursor.execute("""
                        INSERT INTO amortization_schedule (
                            payment_id, loan_id, payment_date, 
                            amount, interest, principal, balance
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()), loan.loan_id, index.date(),
                        float(row['Payment']), float(row['Interest']), 
                        float(row['Principal']), float(row['Balance'])
                    ))

                conn.commit()
                return True

            except Exception as e:
                conn.rollback()
                print(f"Error saving loan: {str(e)}")
                raise

    def delete_loan(self, loan_id):
        try:
            # Elimina prima tutti i record correlati dalle tabelle dipendenti
            tables = [
                "amortization_schedule",  # Aggiunti questi due
                "periodic_expenses",      # che mancavano
                "additional_costs",
                "client_loans"            # Anche questa per sicurezza
            ]
            
            for table in tables:
                delete_related_query = f"DELETE FROM {table} WHERE loan_id = %s"
                self.execute_db_query(delete_related_query, (loan_id,))
            
            # Poi elimina il prestito dalla tabella principale
            delete_loan_query = "DELETE FROM loans WHERE loan_id = %s"
            self.execute_db_query(delete_loan_query, (loan_id,))
            
            return True
        except Exception as e:
            print(f"Error deleting loan: {e}")
            return False

    def update_loan(self, loan):
        query = '''
        UPDATE loans SET
            initial_rate = %s, initial_term = %s, loan_amount = %s, amortization_type = %s, 
            frequency = %s, rate_type = %s, use_euribor = %s, update_frequency = %s, 
            downpayment_percent = %s, start_date = %s, active = %s
        WHERE loan_id = %s
        '''
        parameters = (
            loan.initial_rate, loan.initial_term, loan.loan_amount, loan.amortization_type, 
            loan.frequency, loan.rate_type, loan.use_euribor, loan.update_frequency, 
            loan.downpayment_percent, loan.start.date(), loan.active, loan.loan_id
        )
        self.execute_db_query(query, parameters)


    def check_connection(self):
        """Verifica che la connessione al database sia attiva"""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            return False

    def load_all_loans_from_db(self):
        """Carica tutti i prestiti senza filtrarli per active=True."""
        query = """
        SELECT loan_id, initial_rate, initial_term, loan_amount, 
            amortization_type, frequency, rate_type, use_euribor,
            update_frequency, downpayment_percent, start_date, active
        FROM loans 
        ORDER BY start_date DESC
        """
        cursor = self.execute_db_query(query)
        loans = cursor.fetchall()
        print(f"DEBUG: Prestiti trovati nel DB: {loans}")  # <-- Controlla se i dati esistono
        return loans


    def load_additional_costs(self, loan_id):
        """Load additional costs for a loan"""
        query = "SELECT description, amount FROM additional_costs WHERE loan_id = %s"
        cursor = self.execute_db_query(query, (loan_id,))
        return {row[0]: row[1] for row in cursor.fetchall()}

    def load_periodic_expenses(self, loan_id):
        """Load periodic expenses for a loan"""
        query = "SELECT description, amount FROM periodic_expenses WHERE loan_id = %s"
        cursor = self.execute_db_query(query, (loan_id,))
        return {row[0]: row[1] for row in cursor.fetchall()}


class Loan:
    loans = []

    def __init__(self, db_manager, rate, term, loan_amount, amortization_type, frequency, rate_type='fixed', use_euribor=False, update_frequency='monthly', downpayment_percent=0, additional_costs=None, periodic_expenses=None, start=dt.date.today().isoformat(), loan_id=None, should_save=True, euribor_spread=0.0):
        self.loan_id = loan_id or str(uuid.uuid4())
        self.initial_rate = rate
        self.initial_term = term
        self.loan_amount = loan_amount
        self.downpayment_percent = downpayment_percent
        self.downpayment = self.loan_amount * (self.downpayment_percent / 100)
        self.loan_amount -= self.downpayment
        self.start = dt.datetime.fromisoformat(start).replace(day=1)
        self.frequency = frequency
        self.rate_type = rate_type
        self.use_euribor = use_euribor
        if self.rate_type == 'variable' and self.use_euribor:
            start_date = '1994-01-01'
            end_date = dt.datetime.now().strftime('%Y-%m-%d')
            euribor_data = Loan.get_euribor_series(frequency, start_date, end_date)
            if not euribor_data.empty:
                rate = euribor_data['OBS_VALUE'].iloc[-1]
            else:
                print("WARN: Nessun dato Euribor disponibile. Utilizzo il tasso inserito.")
        self.initial_rate = rate

        self.update_frequency = update_frequency
        self.euribor_spread = euribor_spread 
        self.periods = self.calculate_periods()
        self.rate = self.calculate_rate()
        self.pmt = abs(npf.pmt(self.rate, self.periods, self.loan_amount))
        self.pmt_str = f"€ {self.pmt:,.2f}"
        self.amortization_type = amortization_type
        self.additional_costs = additional_costs or {}
        self.periodic_expenses = periodic_expenses or {}
        self.taeg = {}
        self.table = self.loan_table()
        self.active = False
        self.db_manager = db_manager 

        # Add to loans list
        if self not in Loan.loans:
            Loan.loans.append(self)
            
        # Save to database only if should_save is True
        if should_save:
            self.save_to_db()


    def save_to_db(self):
        """Save loan to database"""
        if not self.db_manager:
            raise Exception("No database manager configured")
            
        try:
            # Ensure all numpy values are converted to Python native types
            self.initial_rate = float(self.initial_rate)
            self.initial_term = int(self.initial_term)
            self.loan_amount = float(self.loan_amount)
            self.downpayment_percent = float(self.downpayment_percent)
            
            self.db_manager.save_loan(self)
                        # Ensure costs dictionaries exist
            if not hasattr(self, 'additional_costs') or self.additional_costs is None:
                self.additional_costs = {}
            if not hasattr(self, 'periodic_expenses') or self.periodic_expenses is None:
                self.periodic_expenses = {}
            return True
        except Exception as e:
            print(f"Error saving loan to database: {str(e)}")
            raise

    def delete_from_db(self):
        """Elimina il prestito dal database e dalla memoria."""
        try:
            if self.db_manager:
                # First delete related records
                tables = [
                    "amortization_schedule",
                    "additional_costs",
                    "periodic_expenses"
                ]
                
                for table in tables:
                    query = f"DELETE FROM {table} WHERE loan_id = %s"
                    self.db_manager.execute_db_query(query, (self.loan_id,))

                # Then delete the loan itself
                if self.db_manager.delete_loan(self.loan_id):
                    if self in Loan.loans:
                        Loan.loans.remove(self)
                    return True
                else:
                    raise Exception("Failed to delete loan from database")
            else:
                raise Exception("No database manager associated with this loan")
                
        except Exception as e:
            print(f"Error deleting loan: {str(e)}")
            return False
    
    def update_db(self):
        """Aggiorna i dati del prestito nel database."""
        if self.db_manager:
            self.db_manager.update_loan(self)
        else:
            print("Errore: Nessun database manager associato a Loan!")



    def calculate_periods(self):
        if self.frequency == 'monthly':
            return self.initial_term * 12
        elif self.frequency == 'quarterly':
            return self.initial_term * 4
        elif self.frequency == 'semi-annual':
            return self.initial_term * 2
        elif self.frequency == 'annual':
            return self.initial_term
        else:
            raise ValueError("Unsupported frequency")


    def calculate_rate(self):
        if self.frequency == 'monthly':
            factor = 12
        elif self.frequency == 'quarterly':
            factor = 4
        elif self.frequency == 'semi-annual':
            factor = 2
        elif self.frequency == 'annual':
            factor = 1
        else:
            raise ValueError("Unsupported frequency")
        
        if self.rate_type == 'fixed':
            return self.initial_rate / factor
        elif self.rate_type == 'variable' and self.use_euribor:
            # Per i prestiti a tasso variabile, utilizziamo il tasso iniziale ma il piano 
            # di ammortamento completo sarà calcolato usando dati Euribor nel metodo loan_table()
            return self.initial_rate / factor
        else:
            raise ValueError("Unsupported rate type or Euribor configuration")

    # Mappa dei codici serie in base alla frequenza
    SERIES_CODES = {
        'monthly': 'FM.M.U2.EUR.RT.MM.EURIBOR1MD_.HSTA',
        'quarterly': 'FM.M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA',
        'semi-annual': 'FM.M.U2.EUR.RT.MM.EURIBOR6MD_.HSTA',
        'annual': 'FM.M.U2.EUR.RT.MM.EURIBOR1YD_.HSTA'
    }

    @staticmethod
    def format_date(date: pd.Timestamp, frequency: str) -> str:
        """
        Formattta la data secondo la frequenza richiesta.
        - monthly: 'YYYY-MM'
        - quarterly: 'YYYY-Qx'
        - semi-annual: 'YYYY-S1' oppure 'YYYY-S2'
        - annual: 'YYYY'
        """
        if frequency == 'monthly':
            return date.strftime('%Y-%m')
        elif frequency == 'quarterly':
            quarter = (date.month - 1) // 3 + 1
            return f"{date.year}-Q{quarter}"
        elif frequency == 'semi-annual':
            semi = 'S1' if date.month <= 6 else 'S2'
            return f"{date.year}-{semi}"
        elif frequency == 'annual':
            return date.strftime('%Y')
        else:
            raise ValueError("Frequenza non supportata")

    @staticmethod
    def get_euribor_series(frequency: str, start: str, end: str) -> pd.DataFrame:
        """
        Scarica la serie storica dell'Euribor in base alla frequenza.
        
        I formati di start e end vengono adattati:
        - monthly: 'YYYY-MM'
        - quarterly: 'YYYY-Qx'
        - semi-annual: 'YYYY-Sx'
        - annual: 'YYYY'
        
        Parametri:
        frequency: una stringa tra 'monthly', 'quarterly', 'semi-annual', 'annual'
        start: data iniziale (in un formato riconoscibile, ad es. '1994-01-01')
        end: data finale (in un formato riconoscibile)
        
        Ritorna un DataFrame con le colonne 'TIME_PERIOD' e 'OBS_VALUE' (i tassi in formato decimale).
        """
        series_code = Loan.SERIES_CODES.get(frequency)
        if series_code is None:
            raise ValueError("Frequenza non supportata. Scegli tra: monthly, quarterly, semi-annual, annual.")
        
        # Converti le date in pd.Timestamp e formatta in base alla frequenza
        start_ts = pd.to_datetime(start)
        end_ts = pd.to_datetime(end)
        start_str = Loan.format_date(start_ts, frequency)
        end_str = Loan.format_date(end_ts, frequency)
        
        # Scarica i dati utilizzando ecbdata
        data = ecbdata.get_series(series_code, start=start_str, end=end_str)
        data = data[['TIME_PERIOD', 'OBS_VALUE']]
        data['OBS_VALUE'] = data['OBS_VALUE'] / 100  # conversione in formato decimale
        data['TIME_PERIOD'] = pd.to_datetime(data['TIME_PERIOD'])
        return data

    @staticmethod
    def fit_best_distribution(data: pd.Series):
        """
        Adatta diverse distribuzioni (Normale, Lognormale, Gamma, Beta, Cauchy, t) alla serie storica e ne sceglie la migliore
        in base al test KS.
        
        Parametri:
        data: Serie di tassi storici
        
        Ritorna:
        (best_dist, best_params): la distribuzione scelta e i relativi parametri stimati.
        """
        distributions = [stats.norm, stats.lognorm, stats.gamma, stats.beta, stats.cauchy, stats.t]
        best_dist = None
        best_params = None
        best_ks_stat = float('inf')
        
        for dist in distributions:
            try:
                params = dist.fit(data)
                ks_stat, _ = stats.kstest(data, dist.name, args=params)
                # Stampa di debug (opzionale)
                print(f"{dist.name}: ks_stat={ks_stat}")
                if ks_stat < best_ks_stat:
                    best_ks_stat = ks_stat
                    best_dist = dist
                    best_params = params
            except Exception as e:
                print(f"Errore nell'adattamento della distribuzione {dist.name}: {e}")
                continue
        return best_dist, best_params

    @staticmethod
    def generate_variable_rates_with_spread(initial_rate: float, periods: int, dist, params, 
                                        historical_median: float, spread: float = 0.0, seed: int = None):
        """
        Genera una sequenza di tassi variabili con l'aggiunta di uno spread.
        
        Parametri:
        initial_rate: il tasso euribor corrente (in formato decimale)
        periods: numero totale di periodi
        dist: la distribuzione statistica scelta
        params: i parametri della distribuzione
        historical_median: mediana dei tassi storici (da utilizzare in caso di tasso negativo)
        spread: spread da aggiungere al tasso Euribor (in decimale, es: 0.01 = 1%)
        seed: seme per la generazione casuale
        
        Ritorna:
        Una lista di tassi (float) di lunghezza 'periods' con spread applicato.
        """
        rng = np.random.default_rng(seed)
        base_rates = [initial_rate]
        for _ in range(periods - 1):
            new_rate = dist.rvs(*params, size=1, random_state=rng)[0]
            # Se il tasso generato è negativo, usa la mediana della serie storica
            if new_rate < 0:
                new_rate = historical_median
            base_rates.append(new_rate)
        
        # Applica lo spread a ogni tasso
        return [rate + spread for rate in base_rates]


    def loan_table(self):
        if self.frequency == 'monthly':
            periods = [self.start + relativedelta(months=x) for x in range(self.periods)]
        elif self.frequency == 'quarterly':
            periods = [self.start + relativedelta(months=3 * x) for x in range(self.periods)]
        elif self.frequency == 'semi-annual':
            periods = [self.start + relativedelta(months=6 * x) for x in range (self.periods)]
        elif self.frequency == 'annual':
            periods = [self.start + relativedelta(years=x) for x in range(self.periods)]
        else:
            raise ValueError("Unsupported frequency")
        
        if self.rate_type == 'fixed':
            if self.amortization_type == "French":
                interest = [npf.ipmt(self.rate, month, self.periods, -self.loan_amount)
                            for month in range(1, self.periods + 1)]
            
                principal = [npf.ppmt(self.rate, month, self.periods, -self.loan_amount)
                            for month in range(1, self.periods + 1)]
                
                balance = [self.loan_amount - sum(principal[:x]) for x in range(1, self.periods + 1)]

                table = pd.DataFrame({
                    'Initial Debt': [self.loan_amount] + balance[:-1],
                    'Payment': [self.pmt] * self.periods,
                    'Interest': interest,
                    'Principal': principal,
                    'Balance': balance
                }, index=pd.to_datetime(periods))

            elif self.amortization_type == "Italian":
                principal_payment = self.loan_amount / self.periods
                interest = [(self.loan_amount - principal_payment * x) * self.rate for x in range(self.periods)]
                principal = [principal_payment] * self.periods
                payment = [interest[x] + principal[x] for x in range(self.periods)]
                balance = [self.loan_amount - sum(principal[:x+1]) for x in range(self.periods)]

                table = pd.DataFrame({
                    'Initial Debt': [self.loan_amount] + balance[:-1],
                    'Payment': payment,
                    'Interest': interest,
                    'Principal': principal,
                    'Balance': balance
                }, index=pd.to_datetime(periods))

            else:
                raise ValueError("Unsupported amortization type")
            return table.round(2)
        

        elif self.rate_type == 'variable' and self.use_euribor:
                    start_date = '1994-01-01'  # Data iniziale per un dataset storico significativo
                    end_date = dt.datetime.now().strftime('%Y-%m-%d')
                    euribor_data = self.get_euribor_series(self.frequency, start_date, end_date)
                    
                    # Verifica disponibilità dati Euribor
                    if euribor_data.empty:
                        raise ValueError(f"Nessun dato Euribor disponibile per la frequenza {self.frequency}")
                    
                    # Calcola il tasso corrente e parametri statistici
                    current_euribor_rate = euribor_data['OBS_VALUE'].iloc[-1]
                    historical_median = euribor_data['OBS_VALUE'].median()
                    best_dist, best_params = self.fit_best_distribution(euribor_data['OBS_VALUE'])
                    
                    # Genera le date dei periodi in base alla frequenza
                    if self.frequency == 'monthly':
                        periods_dates = [self.start + relativedelta(months=x) for x in range(self.periods)]
                    elif self.frequency == 'quarterly':
                        periods_dates = [self.start + relativedelta(months=3 * x) for x in range(self.periods)]
                    elif self.frequency == 'semi-annual':
                        periods_dates = [self.start + relativedelta(months=6 * x) for x in range(self.periods)]
                    elif self.frequency == 'annual':
                        periods_dates = [self.start + relativedelta(years=x) for x in range(self.periods)]
                    else:
                        raise ValueError("Unsupported frequency")
                    
                    # Per la prima rata utilizziamo l'ultimo valore Euribor noto più lo spread
                    first_rate = current_euribor_rate + self.euribor_spread
                    
                    # Per le rate successive, generiamo i tassi in modo stocastico
                    if self.periods > 1:
                        # Genera tassi solo per i periodi successivi al primo
                        future_rates = self.generate_variable_rates_with_spread(
                            current_euribor_rate, self.periods - 1, best_dist, best_params,
                            historical_median, self.euribor_spread, seed=42)
                        
                        # Combina il primo tasso noto con i tassi generati per i periodi successivi
                        variable_rates = [first_rate] + future_rates
                    else:
                        # Se c'è un solo periodo, usiamo solo il tasso corrente
                        variable_rates = [first_rate]
                    
                    # Calcola il piano di ammortamento in base al tipo
                    if self.amortization_type == "French":
                        # Metodo Francese (a rata costante per ogni tasso)
                        initial_balance = [self.loan_amount]
                        final_balance = []
                        interest = []
                        principal = []
                        payment = []
                        
                        for i in range(self.periods):
                            period_rate = variable_rates[i]
                            remaining_periods = self.periods - i
                            
                            # Ricalcolo della rata in base al tasso corrente e al capitale residuo
                            period_payment = abs(npf.pmt(period_rate, remaining_periods, -initial_balance[i]))
                            
                            # Calcolo delle componenti della rata
                            period_interest = period_rate * initial_balance[i]
                            period_principal = period_payment - period_interest
                            period_final_balance = initial_balance[i] - period_principal
                            
                            # Gestione dell'ultimo periodo per assicurare che il saldo finale sia esattamente zero
                            if i == self.periods - 1:
                                # Aggiustiamo la quota capitale per far chiudere il piano a zero
                                period_principal = initial_balance[i]
                                period_payment = period_interest + period_principal
                                period_final_balance = 0
                            
                            # Accumulo dei valori
                            payment.append(period_payment)
                            interest.append(period_interest)
                            principal.append(period_principal)
                            final_balance.append(period_final_balance)
                            
                            # Prepara il saldo iniziale per il periodo successivo
                            if i < self.periods - 1:
                                initial_balance.append(period_final_balance)
                        
                    elif self.amortization_type == "Italian":
                        # Metodo Italiano (quota capitale costante)
                        # La quota capitale è costante per definizione
                        principal_payment = self.loan_amount / self.periods
                        initial_balance = [self.loan_amount]
                        final_balance = []
                        principal = []
                        interest = []
                        payment = []
                        
                        for i in range(self.periods):
                            # Calcolo interessi per questo periodo
                            period_interest = initial_balance[i] * variable_rates[i]
                            
                            # Gestione dell'ultimo periodo per assicurare che il saldo finale sia esattamente zero
                            if i == self.periods - 1:
                                period_principal = initial_balance[i]
                            else:
                                period_principal = principal_payment
                            
                            # Calcolo rata e saldo finale
                            period_payment = period_interest + period_principal
                            period_final_balance = initial_balance[i] - period_principal
                            
                            # Accumulo dei valori
                            interest.append(period_interest)
                            principal.append(period_principal)
                            payment.append(period_payment)
                            final_balance.append(period_final_balance)
                            
                            # Prepara il saldo iniziale per il periodo successivo
                            if i < self.periods - 1:
                                initial_balance.append(period_final_balance)
                    else:
                        raise ValueError("Unsupported amortization type")
                    
                    # Verifica che tutte le liste abbiano la stessa lunghezza
                    list_lengths = {
                        'initial_balance': len(initial_balance),
                        'payment': len(payment),
                        'interest': len(interest),
                        'principal': len(principal),
                        'final_balance': len(final_balance),
                        'periods_dates': len(periods_dates)
                    }
                    
                    if len(set(list_lengths.values())) != 1:
                        raise ValueError(f"Inconsistent list lengths in loan table calculation: {list_lengths}")
                    
                    # Creazione della tabella di ammortamento
                    table = pd.DataFrame({
                        'Initial Debt': initial_balance,
                        'Payment': payment,
                        'Interest': interest,
                        'Principal': principal,
                        'Balance': final_balance
                    }, index=pd.to_datetime(periods_dates))
                    
                    return table.round(2)
        else:
            raise ValueError("Unsupported rate type or Euribor configuration")


    def plot_balances(self):
        amort = self.loan_table()
        if self.amortization_type == "French":
            plt.title("French Amortization Interest and Balance")
        elif self.amortization_type == "Italian":
            plt.title("Italian Amortization Interest and Balance")
        else:
            plt.title("Unknown Amortization")
        plt.plot(amort.Balance, label='Balance (€)')
        plt.plot(amort.Interest.cumsum(), label='Interest Paid (€)')
        plt.grid(axis='y', alpha=.5)
        plt.legend(loc=8)
        plt.show()

    def summary(self):
        print("Summary")
        print("-" * 60)
        print(f'Downpayment: €{self.downpayment:,.2f} ({self.downpayment_percent}%)')
        if self.amortization_type == "French":
            print(f'Payment (French amortization): {self.pmt_str:>21}')
        elif self.amortization_type == "Italian":
            italian_payment = self.table['Payment'].iloc[0]
            print(f'Payment (Italian Amortization): €{italian_payment:,.2f}')
        print(f'{"Payoff Date:":19s} {self.table.index.date[-1]}')
        print(f'Interest Paid: €{self.table["Interest"].cumsum().iloc[-1]:,.2f}')

        print("-" * 60)

    def pay_early(self, extra_amt):
        """Calculate the new payoff date and periods reduction with an extra payment."""
        new_periods = npf.nper(self.rate, self.pmt + extra_amt, -self.loan_amount)
        reduced_periods = self.periods - new_periods
        
        # Calculate the new payoff date based on frequency
        if self.frequency == 'monthly':
            payoff_date = self.start + relativedelta(months=int(new_periods))
        elif self.frequency == 'quarterly':
            payoff_date = self.start + relativedelta(months=int(new_periods * 3))
        elif self.frequency == 'semi-annual':
            payoff_date = self.start + relativedelta(months=int(new_periods * 6))
        elif self.frequency == 'annual':
            payoff_date = self.start + relativedelta(years=int(new_periods))
        else:
            raise ValueError("Unsupported frequency")

        # Convert periods reduced to appropriate units (e.g., months, quarters, etc.)
        reduced_periods_in_frequency = self.periods - new_periods
        if self.frequency == 'quarterly':
            reduced_periods_in_frequency /= 3
        elif self.frequency == 'semi-annual':
            reduced_periods_in_frequency /= 6
        elif self.frequency == 'annual':
            reduced_periods_in_frequency /= 12

        new_years = new_periods / 12
        return (f'New payoff date: {payoff_date.date()}, '
                f'Periods reduced by: {int(reduced_periods_in_frequency)} {self.frequency} '
                f'({new_years:.2f} years)')

    def pay_faster(self, years_to_debt_free):
        """Calculate the required extra payment to retire the debt within the desired time frame."""
        desired_periods = years_to_debt_free * 12  # Defaulting to monthly periods
        
        # Adjust periods based on frequency
        if self.frequency == 'quarterly':
            desired_periods //= 3
        elif self.frequency == 'semi-annual':
            desired_periods //= 6
        elif self.frequency == 'annual':
            desired_periods //= 12

        extra_pmt = npf.pmt(self.rate, desired_periods, -self.loan_amount) - self.pmt
        new_periods = npf.nper(self.rate, self.pmt + extra_pmt, -self.loan_amount)
        
        # Convert new periods into appropriate units
        if self.frequency == 'quarterly':
            new_periods /= 3
        elif self.frequency == 'semi-annual':
            new_periods /= 6
        elif self.frequency == 'annual':
            new_periods /= 12

        new_years = new_periods / 12
        return (f'Extra payment required: €{extra_pmt:.2f}, '
                f'Total payment: €{self.pmt + extra_pmt:.2f}, '
                f'New term: {int(new_periods)} {self.frequency} ({new_years:.2f} years)')

    def edit_loan(self, new_rate, new_term, new_loan_amount, new_amortization_type, 
                new_frequency, new_downpayment_percent, new_rate_type='fixed', 
                new_use_euribor=False, new_update_frequency=None, new_euribor_spread=0.0):
        self.initial_rate = new_rate
        self.initial_term = new_term
        self.downpayment_percent = new_downpayment_percent
        self.downpayment = new_loan_amount * (self.downpayment_percent / 100)
        self.loan_amount = new_loan_amount - self.downpayment
        self.amortization_type = new_amortization_type
        self.frequency = new_frequency
        self.rate_type = new_rate_type
        self.use_euribor = new_use_euribor
        self.update_frequency = new_update_frequency
        self.euribor_spread = new_euribor_spread
        self.periods = self.calculate_periods()
        self.rate = self.calculate_rate()
        self.pmt = abs(npf.pmt(self.rate, self.periods, self.loan_amount))
        self.pmt_str = f"€ {self.pmt:,.2f}"
        self.table = self.loan_table()
        self.update_db()

    def calculate_taeg(self):

        """
        Calcola il TAEG periodico e annualizzato. Il TAEG è il tasso che uguaglia la somma attualizzata
        dei pagamenti periodici (rate lorde) all'importo erogato (prestito netto dopo le spese iniziali).
        """

        # Importo del prestito iniziale al netto delle spese iniziali
        loan_amount = float(self.loan_amount)
        initial_expenses = float(sum(self.additional_costs.values()))
        net_loan_amount = loan_amount - initial_expenses

        # Recupera le spese periodiche dall'attributo periodic_expenses
        total_periodic_expenses = float(sum(self.periodic_expenses.values())) if self.periodic_expenses else 0

        # Pagamento periodico lordo (inclusi eventuali costi periodici)
        gross_payment = float(self.pmt) + total_periodic_expenses

        # Durata del prestito in anni, tenendo conto della frequenza dei pagamenti
        if self.frequency == 'monthly':
            periods_in_years = np.array([(i + 1) / 12 for i in range(self.periods)])
            periods_per_year = 12
        elif self.frequency == 'quarterly':
            periods_in_years = np.array([(i + 1) / 4 for i in range(self.periods)])
            periods_per_year = 4
        elif self.frequency == 'semi-annual':
            periods_in_years = np.array([(i + 1) / 2 for i in range(self.periods)])
            periods_per_year = 2
        elif self.frequency == 'annual':
            periods_in_years = np.array([(i + 1) for i in range(self.periods)])
            periods_per_year = 1
        else:
            raise ValueError("Unsupported frequency")

        # Funzione da azzerare per calcolare il TAEG periodico
        def taeg_func(r): 
            return sum([gross_payment / (1 + r)**t for t in periods_in_years]) - net_loan_amount

        # Trova la radice dell'equazione per ottenere il TAEG periodico
        period_rate = brentq(taeg_func, 0, 1)

        # Calcola il TAEG annualizzato
        annualized_taeg = (1 + period_rate)**periods_per_year - 1

        # Converti i TAEG in percentuale
        period_taeg_percent = period_rate * 100
        annualized_taeg_percent = annualized_taeg * 100

        # Aggiorna gli attributi TAEG del prestito
        self.taeg_periodic = period_taeg_percent
        self.taeg_annualized = annualized_taeg_percent

        # Assegna entrambi i TAEG calcolati al dizionario
        self.taeg = {
            'periodic': period_taeg_percent,
            'annualized': annualized_taeg_percent
        }
        
        return f'TAEG Periodico: {period_taeg_percent:.4f}%, TAEG Annualizzato: {annualized_taeg_percent:.4f}%'


    @classmethod
    def compare_loans(cls, loans):
        if len(loans) < 2:
            return "Please set at least two loans for comparison."

        results = []
        
        for i, loan in enumerate(loans):
            if not loan.taeg:
                loan.calculate_taeg()

            if loan.amortization_type == "French":
                monthly_payment = loan.pmt
            elif loan.amortization_type == "Italian":
                monthly_payment = loan.table['Payment'].iloc[0]

            results.append(f"Loan {i + 1} - Monthly Payment: €{monthly_payment:,.2f}")
            results.append(f"Loan {i + 1} - TAEG Periodic: {loan.taeg['periodic']:.2f}%")
            results.append(f"Loan {i + 1} - TAEG Annualized: {loan.taeg['annualized']:.2f}%")
            results.append(f"Loan {i + 1} - Interest Paid: €{loan.table['Interest'].cumsum().iloc[-1]:,.2f}")
            results.append("-" * 60)
        
        # Identificare il prestito più conveniente per il mutuatario
        min_periodic_taeg_loan = min(loans, key=lambda loan: loan.taeg['periodic'])
        min_annualized_taeg_loan = min(loans, key=lambda loan: loan.taeg['annualized'])
        
        results.append(f"Most convenient loan for Borrower based on Periodic TAEG: Loan {loans.index(min_periodic_taeg_loan) + 1} (TAEG Periodic: {min_periodic_taeg_loan.taeg['periodic']:.2f}%)")
        results.append(f"Most convenient loan for Borrower based on Annualized TAEG: Loan {loans.index(min_annualized_taeg_loan) + 1} (TAEG Annualized: {min_annualized_taeg_loan.taeg['annualized']:.2f}%)")
        
        # Identificare il prestito più conveniente per il prestatore
        max_periodic_taeg_loan = max(loans, key=lambda loan: loan.taeg['periodic'])
        max_annualized_taeg_loan = max(loans, key=lambda loan: loan.taeg['annualized'])
        
        results.append(f"Most profitable loan for Lender based on Periodic TAEG: Loan {loans.index(max_periodic_taeg_loan) + 1} (TAEG Periodic: {max_periodic_taeg_loan.taeg['periodic']:.2f}%)")
        results.append(f"Most profitable loan for Lender based on Annualized TAEG: Loan {loans.index(max_annualized_taeg_loan) + 1} (TAEG Annualized: {max_annualized_taeg_loan.taeg['annualized']:.2f}%)")
        
        # Identificare il prestito di equilibrio
        equilibrium_loan = min(loans, key=lambda loan: abs(loan.taeg['periodic'] - loan.taeg['annualized']))
        
        results.append(f"\nOptimal Equilibrium Loan: Loan {loans.index(equilibrium_loan) + 1}")
        results.append(f"Optimal Loan TAEG: {equilibrium_loan.taeg['periodic']:.2f}% (Periodic), {equilibrium_loan.taeg['annualized']:.2f}% (Annualized)")
        
        results.append("-" * 60)
        return "\n".join(results)

    @classmethod
    def display_loans(cls):
        """
        Display all loans with their details for selection.
        """
        if not cls.loans:
            print("No loans available.")
            return

        for idx, loan in enumerate(cls.loans):
            print(f"{idx + 1}: Loan ID: {loan.loan_id}, Amount: €{loan.loan_amount:,.2f}, Rate: {loan.initial_rate * 100:.2f}%, Term: {loan.initial_term} years")


    @classmethod
    def delete_loan(cls, loan_id):
        """
        Delete a loan by ID from both database and memory.
        
        Args:
            loan_id: UUID of the loan to delete
        
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            # Find loan in memory list
            loan_to_delete = next((loan for loan in cls.loans if loan.loan_id == loan_id), None)
            
            if loan_to_delete is None:
                print(f"Loan with ID {loan_id} not found in memory")
                return False
                    
            # Use the instance method delete_from_db instead of calling db_manager.delete_loan directly
            if loan_to_delete.delete_from_db():
                # Il metodo delete_from_db già rimuove il prestito dalla lista loans
                # e gestisce tutte le tabelle correlate necessarie
                print(f"Successfully deleted loan {loan_id}")
                return True
            else:
                print(f"Failed to delete loan {loan_id}")
                return False
                
        except Exception as e:
            print(f"Error deleting loan: {str(e)}")
            return False

    @classmethod
    def delete_loan_with_confirmation(cls):
        """
        Select a loan to delete with user confirmation.
        """
        cls.display_loans()
        loan_idx = int(input("Enter the loan number you want to delete: ")) - 1
        if 0 <= loan_idx < len(cls.loans):
            loan = cls.loans[loan_idx]
            confirm = input(f"Are you sure you want to delete the loan with ID {loan.loan_id}? (yes/no): ").strip().lower()
            if confirm == 'yes':
                # Modifica qui: passa loan.loan_id invece di loan_idx
                cls.delete_loan(loan.loan_id)  # <-- Correzione
            else:
                print("Deletion cancelled.")
        else:
            print("Invalid loan number.")

    @classmethod
    def consolidate_loans(cls, selected_loans, frequency):
        if not selected_loans or len(selected_loans) < 2:
            raise ValueError("At least two loans must be selected for consolidation.")
            
                # Prendi il db_manager dal primo prestito selezionato
        db_manager = selected_loans[0].db_manager


        # Calcola il totale dell'importo del prestito
        total_amount = sum(loan.loan_amount for loan in selected_loans)

        def convert_to_frequency(loan, target_frequency):
            conversion_factors = {
                'monthly': 12,
                'quarterly': 4,
                'semi-annual': 2,
                'annual': 1
            }

            current_factor = conversion_factors[loan.frequency]
            target_factor = conversion_factors[target_frequency]

            target_rate = (1 + loan.initial_rate) ** (target_factor / current_factor) - 1
            target_payment = npf.pmt(target_rate, loan.periods * (current_factor / target_factor), loan.loan_amount)
            return target_rate, abs(target_payment)

        def convert_taeg_to_frequency(loan, target_frequency):
            conversion_factors = {
                'monthly': 12,
                'quarterly': 4,
                'semi-annual': 2,
                'annual': 1
            }

            current_factor = conversion_factors[loan.frequency]
            target_factor = conversion_factors[target_frequency]

            if 'periodic' in loan.taeg:
                target_taeg_periodic = (1 + loan.taeg['periodic'] / 100) ** (target_factor / current_factor) - 1
            else:
                target_taeg_periodic = loan.rate  # Fallback to the loan rate if TAEG is not available
            return target_taeg_periodic

        weighted_rate_sum = 0
        weighted_term_sum = 0
        amortization_types = {}
        weighted_payments_sum = 0
        weighted_taeg_sum = 0

        for loan in selected_loans:
            # Ensure TAEG is calculated for each loan
            if not loan.taeg:
                loan.calculate_taeg()

            target_rate, target_payment = convert_to_frequency(loan, frequency)
            target_taeg_periodic = convert_taeg_to_frequency(loan, frequency)

            weighted_rate_sum += target_rate * loan.loan_amount
            weighted_term_sum += loan.initial_term * loan.loan_amount
            weighted_payments_sum += target_payment * loan.loan_amount
            weighted_taeg_sum += target_taeg_periodic * loan.loan_amount
            amortization_types[loan.amortization_type] = amortization_types.get(loan.amortization_type, 0) + loan.loan_amount

        average_rate = weighted_rate_sum / total_amount
        average_term = weighted_term_sum / total_amount
        average_payment = weighted_payments_sum / total_amount
        average_taeg_periodic = weighted_taeg_sum / total_amount

        conversion_factors = {
            'monthly': 12,
            'quarterly': 4,
            'semi-annual': 2,
            'annual': 1
        }
        periods_per_year = conversion_factors[frequency]
        average_taeg_annualized = (1 + average_taeg_periodic) ** periods_per_year - 1

        amortization_type = max(amortization_types, key=amortization_types.get)

        consolidated_loan = cls(
            db_manager=db_manager,
            rate=average_rate,
            term=int(round(average_term, 2)),
            loan_amount=total_amount,
            amortization_type=amortization_type,
            frequency=frequency,
        )

        consolidated_loan.taeg = {
            'periodic': average_taeg_periodic * 100,
            'annualized': average_taeg_annualized * 100
        }

        consolidated_loan.save_to_db()

        return consolidated_loan

    def calculate_probabilistic_pricing(self, 
                                    initial_default: float = 0.2,
                                    default_decay: float = 0.9, 
                                    final_default: float = 0.4,
                                    recovery_rate: float = 0.4,
                                    num_iterations: int = 100,
                                    loan_lives: list = None,
                                    interest_rates: np.ndarray = None,
                                    default_probabilities: list = None) -> pd.DataFrame:
        """
        Calculate probabilistic loan pricing using Monte Carlo simulation.

        Parameters
        ----------
        initial_default : float, optional
            Initial default probability, default 0.2 (20%)
        default_decay : float, optional
            Default probability decay rate, default 0.9 (90%)
        final_default : float, optional
            Final default probability, default 0.4 (40%)
        recovery_rate : float, optional
            Recovery rate in case of default, default 0.4 (40%)
        num_iterations : int, optional
            Number of Monte Carlo iterations, default 100
        loan_lives : list, optional
            List of loan durations in years, default [5,10,20]
        interest_rates : array-like, optional
            Array of interest rates, default np.arange(0.3, 0.41, 0.05)
        default_probabilities : list, optional
            List of default probabilities, default [0.1, 0.2, 0.3]

        Returns
        -------
        pd.DataFrame
            Styled DataFrame with IRR calculations
        """
        # Input validation
        if loan_lives is None:
            loan_lives = [5, 10, 20]
        if interest_rates is None:
            interest_rates = np.arange(0.3, 0.41, 0.05)
        if default_probabilities is None:
            default_probabilities = [0.1, 0.2, 0.3]

        # Validate ranges
        if not all(0 < r < 1 for r in interest_rates):
            raise ValueError("Interest rates must be between 0 and 1")
        if not all(l > 0 for l in loan_lives):
            raise ValueError("Loan lives must be positive")
        if not all(0 <= p <= 1 for p in default_probabilities):
            raise ValueError("Default probabilities must be between 0 and 1")

        results = []
        
        # Convert amortization schedule DataFrame to cash flow list
        unadjusted_cashflows = self.table['Payment'].tolist()
        
        def calculate_default_probability(loan_life):
            default_probability_values = []
            current_default = initial_default
            
            for i in range(1, loan_life + 3):
                if i == 1:
                    default_probability_values.append(current_default)
                elif i < loan_life:
                    current_default *= default_decay
                    default_probability_values.append(current_default) 
                elif i == loan_life:
                    default_probability_values.append(final_default)
                elif i == loan_life + 1:
                    default_probability_values.append(0)
                else: # i == loan_life + 2
                    default_probability_values.append(recovery_rate)
            return default_probability_values

        def calculate_adjusted_cashflow(default_probs, cashflows):
            adjusted_flows = []
            
            for i, (default_prob, cf) in enumerate(zip(default_probs, cashflows)):
                if i == 0: # First flow
                    interest_portion = self.rate * self.loan_amount
                    adj_interest = interest_portion * (1 - default_prob)
                    adjusted_flows.append(-self.loan_amount + adj_interest)
                elif default_prob == recovery_rate and cf == self.loan_amount:
                    adj_cf = (self.rate * self.loan_amount) * (1 - default_prob)
                    adjusted_flows.append(adj_cf)
                elif default_prob == recovery_rate:
                    adjusted_flows.append(recovery_rate * self.loan_amount)
                elif default_prob == 0 and cf == 0:
                    adjusted_flows.append(0)
                else:
                    adjusted_flows.append(cf * (1 - default_prob))
                    
            return adjusted_flows

        # Execute iterations
        irr_values = []
        rate_values = []
        default_prob_values = [] 
        life_values = []

        for _ in range(num_iterations):
            for rate in interest_rates:
                for default_prob in default_probabilities:
                    for life in loan_lives:
                        try:
                            # Calculate default probabilities
                            probs = calculate_default_probability(life)
                            
                            # Calculate adjusted cash flows
                            adj_flows = calculate_adjusted_cashflow(probs, unadjusted_cashflows)
                            
                            # Calculate IRR
                            irr = npf.irr(adj_flows)
                            
                            irr_values.append(irr)
                            rate_values.append(rate)
                            default_prob_values.append(default_prob)
                            life_values.append(life)
                            
                            results.append({
                                'Interest Rate': f"{rate:.2%}",
                                'Loan Life': life,
                                'Initial Default Probability': f"{default_prob:.2%}",
                                'IRR': irr
                            })
                        except Exception as e:
                            print(f"IRR calculation failed for rate={rate}, prob={default_prob}, life={life}: {str(e)}")
                            continue

        # Create results DataFrame
        df = pd.DataFrame(results)
        
        # Calculate means and standard deviation
        avg_results = df.groupby(['Interest Rate', 'Loan Life', 'Initial Default Probability']).mean().reset_index()
        std_dev = np.std(irr_values)
        
        # Adjust IRR with standard deviation
        avg_results['IRR'] = avg_results['IRR'] - std_dev
        
        # Create pivot table with formatting
        pivot = pd.pivot_table(
            avg_results,
            values='IRR', 
            index=['Interest Rate', 'Loan Life'],
            columns='Initial Default Probability',
            fill_value=0
        )
        
        # Apply formatting
        styled = pivot.style.background_gradient(cmap=sns.color_palette("RdYlGn", as_cmap=True))
        styled = styled.format("{:.2%}")
        
        return styled



    @classmethod
    def clear_loans(cls):
        """Pulisce la lista dei prestiti in memoria"""
        cls.loans.clear()
        

    @classmethod 
    def load_all_loans(cls, db_manager):
        """Carica tutti i prestiti dal database nella lista loans"""
        cls.clear_loans()  # Pulisce la lista esistente
        
        try:
            # Carica i dati dal database
            loans_data = db_manager.load_all_loans_from_db()
            
            for loan_data in loans_data:
                try:
                    # Crea nuovo prestito con should_save=False per evitare il doppio salvataggio
                    loan = cls(
                        db_manager=db_manager,
                        rate=float(loan_data[1]),
                        term=int(loan_data[2]),
                        loan_amount=float(loan_data[3]),
                        amortization_type=loan_data[4],
                        frequency=loan_data[5],
                        rate_type=loan_data[6],
                        use_euribor=loan_data[7],
                        update_frequency=loan_data[8],
                        downpayment_percent=float(loan_data[9]),
                        start=loan_data[10].isoformat(),
                        loan_id=str(loan_data[0]),
                        should_save=False 
                    )
                    
                    # Carica i costi aggiuntivi e le spese periodiche
                    loan.additional_costs = db_manager.load_additional_costs(loan.loan_id)
                    loan.periodic_expenses = db_manager.load_periodic_expenses(loan.loan_id)
                    
                    # Ricalcola tabella e TAEG con i nuovi costi
                    loan.table = loan.loan_table()
                    loan.calculate_taeg()
                    
                    # Aggiungi alla lista dei prestiti
                    cls.loans.append(loan)
                    
                except Exception as e:
                    print(f"Error loading loan {loan_data[0]}: {str(e)}")
                    continue
                    
            return True
            
        except Exception as e:
            print(f"Error loading loans: {str(e)}")
            return False
