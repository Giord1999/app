import numpy as np
import numpy_financial as npf
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import seaborn as sns
import uuid
import psycopg2
from psycopg2 import pool
from scipy import stats
from scipy.stats import norm
from scipy.optimize import brentq
import random
from ecbdata import ecbdata
from datetime import datetime 
import numba as nb
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import os
from tqdm import tqdm
import threading

#TODO: IMPELMENTARE SISTEMA CHECK DI PAGAMENTI

class DbManager:
    def __init__(self, dbname, user, password, host='localhost', port='5432', min_connections=1, max_connections=1000000000000000000000000000000000000000000000000000000000000000000000000000000000):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool = None
        self._init_pool()
 
    def _init_pool(self):
        """Initialize the connection pool"""
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                self.min_connections,
                self.max_connections,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            print(f"DEBUG: Connection pool initialized for DB {self.dbname} on {self.host}:{self.port}")
        except Exception as e:
            print(f"ERROR: Could not initialize connection pool: {str(e)}")
            raise

    def get_connection(self):
        """Get a connection from the pool"""
        if self._pool is None:
            self._init_pool()
        try:
            return self._pool.getconn()
        except Exception as e:
            print(f"ERROR: Failed to get connection from pool: {str(e)}")
            # Try to re-initialize the pool and get connection again
            self._init_pool()
            return self._pool.getconn()

    def release_connection(self, conn):
        """Return a connection to the pool"""
        if self._pool is not None and conn is not None:
            self._pool.putconn(conn)

    def connect(self):
        """Legacy method for backward compatibility"""
        print(f"DEBUG: Getting connection from pool for DB {self.dbname} via connect() method")
        return self.get_connection()

    def execute_db_query(self, query, parameters=()):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, parameters)
            conn.commit()
            result = cursor  # Save the cursor for result access
            return cursor
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Query execution error: {str(e)}")
            raise
        finally:
            if cursor:
                # Don't close the cursor here as it's being returned
                # The caller is responsible for processing the cursor results
                pass
            if conn:
                self.release_connection(conn)

    def create_db(self):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
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
            ''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS additional_costs(
                loan_id UUID REFERENCES loans(loan_id),
                description VARCHAR(255) NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                PRIMARY KEY (loan_id, description)
            )
            ''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS periodic_expenses(
                loan_id UUID REFERENCES loans(loan_id),
                description VARCHAR(255) NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                PRIMARY KEY (loan_id, description)
            )
            ''')

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
            ''')
            
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Database creation error: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)

    def save_loan(self, loan):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
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

            # Save additional costs (one-time costs)
            cursor.execute("DELETE FROM additional_costs WHERE loan_id = %s", (loan.loan_id,))
            for desc, amount in loan.additional_costs.items():
                cursor.execute("""
                    INSERT INTO additional_costs (loan_id, description, amount)
                    VALUES (%s, %s, %s)
                """, (loan.loan_id, desc, float(amount)))

            # Save periodic expenses (recurring costs)
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
            if conn:
                conn.rollback()
            print(f"Error saving loan: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)

    def delete_loan(self, loan_id):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Delete related records first
            tables = [
                "amortization_schedule",
                "periodic_expenses",
                "additional_costs",
                "client_loans"  # Make sure this table exists or handle errors appropriately
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"DELETE FROM {table} WHERE loan_id = %s", (loan_id,))
                except psycopg2.Error as e:
                    # Log and continue if table doesn't exist
                    if "does not exist" in str(e):
                        print(f"Warning: Table {table} does not exist. Continuing...")
                    else:
                        raise
            
            # Then delete from the main loans table
            cursor.execute("DELETE FROM loans WHERE loan_id = %s", (loan_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error deleting loan: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)

    def update_loan(self, loan):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = '''
            UPDATE loans SET
                initial_rate = %s, initial_term = %s, loan_amount = %s, amortization_type = %s, 
                frequency = %s, rate_type = %s, use_euribor = %s, update_frequency = %s, 
                downpayment_percent = %s, start_date = %s, active = %s
            WHERE loan_id = %s
            '''
            parameters = (
                float(loan.initial_rate), int(loan.initial_term), float(loan.loan_amount), loan.amortization_type, 
                loan.frequency, loan.rate_type, loan.use_euribor, loan.update_frequency, 
                float(loan.downpayment_percent), loan.start.date(), loan.active, loan.loan_id
            )
            cursor.execute(query, parameters)
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error updating loan: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)

    def check_connection(self):
        """Verifica che la connessione al database sia attiva"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)

    def load_all_loans_from_db(self):
        """Carica tutti i prestiti senza filtrarli per active=True."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT loan_id, initial_rate, initial_term, loan_amount, 
                amortization_type, frequency, rate_type, use_euribor,
                update_frequency, downpayment_percent, start_date, active
            FROM loans 
            ORDER BY start_date DESC
            """
            cursor.execute(query)
            loans = cursor.fetchall()
            print(f"DEBUG: Prestiti trovati nel DB: {len(loans)}")
            return loans
            
        except Exception as e:
            print(f"Error loading loans: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)

    def load_additional_costs(self, loan_id):
        """Load additional costs for a loan"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT description, amount FROM additional_costs WHERE loan_id = %s"
            cursor.execute(query, (loan_id,))
            return {row[0]: row[1] for row in cursor.fetchall()}
            
        except Exception as e:
            print(f"Error loading additional costs: {str(e)}")
            return {}
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)

    def load_periodic_expenses(self, loan_id):
        """Load periodic expenses for a loan"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT description, amount FROM periodic_expenses WHERE loan_id = %s"
            cursor.execute(query, (loan_id,))
            return {row[0]: row[1] for row in cursor.fetchall()}
            
        except Exception as e:
            print(f"Error loading periodic expenses: {str(e)}")
            return {}
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)
                
    def close_all_connections(self):
        """Close all connections in the pool"""
        if self._pool is not None:
            self._pool.closeall()
            print("All database connections closed")

# JIT-compiled function for calculating default probability
@nb.jit(nopython=True)
def _calculate_default_probability(loan_life, initial_default, default_decay, final_default, recovery_rate):
    # Pre-allocate array with sufficient size
    default_probability_values = np.zeros(loan_life + 2)
    current_default = initial_default
    idx = 0
    
    # Match original logic exactly
    for i in range(1, loan_life + 3):
        if i == 1:
            default_probability_values[idx] = current_default
            idx += 1
        elif i < loan_life:
            current_default *= default_decay
            default_probability_values[idx] = current_default
            idx += 1
        elif i == loan_life:
            default_probability_values[idx] = final_default
            idx += 1
        elif i == loan_life + 1:
            default_probability_values[idx] = 0
            idx += 1
        else:  # i == loan_life + 2
            default_probability_values[idx] = recovery_rate
            idx += 1
    
    return default_probability_values[:idx]  # Return only the filled portion

# JIT-compiled function for calculating adjusted cashflow
@nb.jit(nopython=True)
def _calculate_adjusted_cashflow(default_probs, cashflows, loan_amount, period_rate, recovery_rate):
    n = len(default_probs)
    adjusted_flows = np.zeros(n)
    
    for i in range(n):
        default_prob = default_probs[i]
        cf = cashflows[i] if i < len(cashflows) else 0.0
        
        if i == 0:  # First flow
            interest_portion = period_rate * loan_amount
            adj_interest = interest_portion * (1.0 - default_prob)
            adjusted_flows[i] = -loan_amount + adj_interest
        elif abs(default_prob - recovery_rate) < 1e-10 and abs(cf - loan_amount) < 1e-10:
            adj_cf = (period_rate * loan_amount) * (1.0 - default_prob)
            adjusted_flows[i] = adj_cf
        elif abs(default_prob - recovery_rate) < 1e-10:
            adjusted_flows[i] = recovery_rate * loan_amount
        elif abs(default_prob) < 1e-10 and abs(cf) < 1e-10:
            adjusted_flows[i] = 0.0
        else:
            adjusted_flows[i] = cf * (1.0 - default_prob)
    
    return adjusted_flows

# JIT-compiled function to generate multiple payment streams efficiently
@nb.jit(nopython=True)
def _generate_payment_streams(loan_amount, rates, terms, amortization_type, periods_per_year):
    """Generate payment streams for all combinations of rates and terms"""
    result = {}
    
    for rate in rates:
        for term in terms:
            periods = term * periods_per_year
            period_rate = rate / periods_per_year
            
            if amortization_type == "French":
                # French amortization (constant payment)
                payment = abs(loan_amount * period_rate / (1 - (1 + period_rate)**(-periods)))
                payments = np.full(periods, payment)
            else:  # Italian
                # Italian amortization (constant principal)
                principal = loan_amount / periods
                payments = np.zeros(periods)
                remaining = loan_amount
                for i in range(periods):
                    interest = remaining * period_rate
                    payments[i] = principal + interest
                    remaining -= principal
                    
            key = (rate, term)
            result[key] = payments
            
    return result

@nb.jit(nopython=True, parallel=True)
def _process_simulation_batch(
    loan_amount, interest_rates_array, loan_lives_array, default_probabilities_array, 
    payment_streams_keys, payment_streams_values, 
    num_iterations, initial_default, default_decay, final_default, recovery_rate, 
    periods_per_year, batch_start, batch_end
):
    """JIT-compiled function to process a batch of simulations"""
    # Pre-allocate result arrays
    rate_count = len(interest_rates_array)
    life_count = len(loan_lives_array)
    prob_count = len(default_probabilities_array)
    
    local_sum = np.zeros((rate_count, life_count, prob_count))
    local_count = np.zeros((rate_count, life_count, prob_count), dtype=np.int32)
    
    for i in range(batch_start, batch_end):
        # Fast index calculation
        iter_idx = i % num_iterations
        param_idx = i // num_iterations
        
        rate_idx = param_idx % rate_count
        param_idx //= rate_count
        prob_idx = param_idx % prob_count
        life_idx = param_idx // prob_count
        
        if life_idx >= life_count:
            continue
            
        rate = interest_rates_array[rate_idx]
        default_prob = default_probabilities_array[prob_idx]
        life = loan_lives_array[life_idx]
        
        # Find the right payment stream in the flattened arrays
        payment_idx = -1
        for j in range(len(payment_streams_keys)):
            if (abs(payment_streams_keys[j][0] - rate) < 1e-10 and 
                payment_streams_keys[j][1] == life):
                payment_idx = j
                break
                
        if payment_idx == -1:
            continue
            
        cashflows = payment_streams_values[payment_idx]
        
        # Calculate probabilities and adjusted cashflows
        probs = _calculate_default_probability(
            life, default_prob, default_decay, final_default, recovery_rate
        )
        
        adj_flows = _calculate_adjusted_cashflow(
            probs, cashflows, loan_amount, rate/periods_per_year, recovery_rate
        )
        
        # Calculate IRR
        try:
            # Simple IRR calculation for nopython mode
            irr = _calculate_simple_irr(adj_flows, 0.05, 100)
            if not np.isnan(irr) and abs(irr) < 1.0:  # Valid IRR
                local_sum[rate_idx, life_idx, prob_idx] += irr
                local_count[rate_idx, life_idx, prob_idx] += 1
        except:
            pass
            
    return local_sum, local_count

@nb.jit(nopython=True)
def _calculate_simple_irr(cashflows, guess=0.1, max_iterations=100):
    """Simple IRR implementation compatible with Numba nopython mode"""
    rate = guess
    
    for _ in range(max_iterations):
        npv = 0.0
        der = 0.0
        
        for i in range(len(cashflows)):
            npv += cashflows[i] / (1 + rate) ** i
            der += -i * cashflows[i] / (1 + rate) ** (i + 1)
            
        if abs(npv) < 1e-6:
            return rate
            
        if abs(der) < 1e-10:
            break
            
        rate = rate - npv / der
        
        if rate <= -1.0:
            return np.nan
            
    return rate if -1.0 < rate < 100.0 else np.nan

@nb.jit(nopython=True)
def _flatten_payment_streams(rates, terms, payment_dict):
    """Convert dictionary to arrays for numba compatibility"""
    keys = []
    values = []
    
    for r in rates:
        for t in terms:
            key = (r, t)
            if key in payment_dict:
                keys.append(key)
                values.append(payment_dict[key])
                
    return keys, values

# Funzioni JIT compilate per l'efficienza computazionale
@nb.jit(nopython=True)
def _mc_simulate_loan_lifetime(
    principal, period_rate, monthly_payment, periods, 
    amortization_type_code, extra_payment_prob, extra_payment_amount,
    late_payment_prob, seed=None
):
    """Simula un singolo scenario di durata del mutuo"""
    if seed is not None:
        np.random.seed(seed)
    
    balance = principal
    n_payments = 0
    
    # Per ammortamento italiano (ammortization_type_code=1)
    principal_payment = principal / periods if amortization_type_code == 1 else 0
    
    while balance > 0:
        n_payments += 1
        
        # Calcolo interessi
        interest_payment = balance * period_rate
        
        # Calcolo quota capitale in base al tipo di ammortamento
        if amortization_type_code == 0:  # French
            principal_payment = monthly_payment - interest_payment
        else:  # Italian (la quota capitale è costante)
            pass  # principal_payment già calcolato
            
        # Pagamento standard
        principal_payment_applied = min(balance, principal_payment)
        balance -= principal_payment_applied
        
        # Possibile pagamento extra
        if np.random.random() < extra_payment_prob:
            extra_payment = min(balance, extra_payment_amount)
            balance -= extra_payment
            
        # Possibile ritardo pagamento (aggiunge interessi extra)
        if np.random.random() < late_payment_prob:
            balance += balance * period_rate
    
    return n_payments

@nb.jit(nopython=True)
def _mc_run_simulations(
    principal, period_rate, monthly_payment, periods,
    amortization_type_code, extra_payment_prob, extra_payment_amount,
    late_payment_prob, n_simulations, seed=None
):
    """Esegue multiple simulazioni Monte Carlo"""
    results = np.zeros(n_simulations)
    
    for i in range(n_simulations):
        sim_seed = None if seed is None else seed + i
        results[i] = _mc_simulate_loan_lifetime(
            principal, period_rate, monthly_payment, periods,
            amortization_type_code, extra_payment_prob, extra_payment_amount,
            late_payment_prob, sim_seed
        )
    
    return results

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
        self.start = dt.datetime.fromisoformat(start)
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
        if self.db_manager is None:
            # Attempt to get a db_manager from the main application
            # This is a fallback mechanism
            from loan_app import app_instance
            if hasattr(app_instance, 'db_manager'):
                self.db_manager = app_instance.db_manager
                print("Recovered db_manager from application instance")
                
        if self.db_manager:
            try:
                self.db_manager.update_loan(self)
            except Exception as e:
                print(f"Database update error: {str(e)}")
                # You may want to show a message box here
        else:
            print("Error: No database manager associated with Loan!")



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
                                    default_probabilities: list = None,
                                    progress_callback=None) -> pd.DataFrame:
        """
        Calculate probabilistic loan pricing using Monte Carlo simulation.
        Optimized for extremely large numbers of iterations (100k+) with near-compiled performance.
        """
        # Input validation and conversion to numpy arrays - same as before
        if loan_lives is None:
            loan_lives = [5, 10, 20]
        if interest_rates is None:
            interest_rates = np.arange(0.3, 0.41, 0.05)
        if default_probabilities is None:
            default_probabilities = [0.1, 0.2, 0.3]

        # Convert inputs to Numpy arrays with explicit data types for performance
        loan_lives_array = np.array(loan_lives, dtype=np.int32)
        interest_rates_array = np.array(interest_rates, dtype=np.float64)
        default_probabilities_array = np.array(default_probabilities, dtype=np.float64)
        
        # Determine frequency multiplier
        frequency_map = {'monthly': 12, 'quarterly': 4, 'semi-annual': 2, 'annual': 1}
        periods_per_year = frequency_map[self.frequency]
        
        # Pre-calculate all payment streams once
        payment_streams = _generate_payment_streams(
            self.loan_amount, 
            interest_rates_array,
            loan_lives_array,
            self.amortization_type, 
            periods_per_year
        )
        
        # Convert payment streams to numba-compatible flat arrays
        payment_keys, payment_values = _flatten_payment_streams(
            interest_rates_array, 
            loan_lives_array, 
            payment_streams
        )
        
        # Calculate the total number of simulations
        rate_count = len(interest_rates_array)
        life_count = len(loan_lives_array)
        prob_count = len(default_probabilities_array)
        total_parameter_combinations = rate_count * prob_count * life_count
        total_calculations = num_iterations * total_parameter_combinations
        
        # Prepare final aggregation arrays
        sum_irr = np.zeros((rate_count, life_count, prob_count))
        count_irr = np.zeros((rate_count, life_count, prob_count), dtype=np.int32)
        
        # Configure parallel processing optimally
        cpu_count = max(1, os.cpu_count() - 1) 
        max_workers = min(16, cpu_count)
        
        # Optimize batch size - larger batches for better numba performance
        batch_size = min(10000, max(2000, total_calculations // (max_workers * 5)))
        
        # Thread-safe progress tracking
        progress_lock = threading.Lock()
        progress_counter = [0]
        
        def run_batch(batch_idx, start_iter, end_iter):
            local_sum, local_count = _process_simulation_batch(
                float(self.loan_amount),
                interest_rates_array, 
                loan_lives_array, 
                default_probabilities_array,
                payment_keys,
                payment_values,
                num_iterations,
                initial_default,
                default_decay,
                final_default,
                recovery_rate,
                periods_per_year,
                start_iter,
                end_iter
            )
            
            # Update progress with minimal locking
            with progress_lock:
                progress_counter[0] += 1
                current = progress_counter[0]
                total_batches = (total_calculations + batch_size - 1) // batch_size
                
                if progress_callback and (current % 5 == 0 or current == total_batches):
                    percent = (current / total_batches) * 100
                    progress_callback(current, total_batches, percent)
                    
            return local_sum, local_count
        
        # Execute calculations in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in range(0, total_calculations, batch_size):
                futures.append(executor.submit(
                    run_batch,
                    i // batch_size,
                    i,
                    min(i + batch_size, total_calculations)
                ))
            
            # Combine results as they complete
            for future in concurrent.futures.as_completed(futures):
                batch_sum, batch_count = future.result()
                sum_irr += batch_sum
                count_irr += batch_count
        
        # Calculate means - using numpy's vectorized operations
        with np.errstate(divide='ignore', invalid='ignore'):
            mean_irr = np.divide(sum_irr, count_irr, out=np.zeros_like(sum_irr), where=count_irr!=0)
        
        # Rest of the function for DataFrame creation remains the same
        results = []
        for r_idx, rate in enumerate(interest_rates_array):
            for l_idx, life in enumerate(loan_lives_array):
                for p_idx, prob in enumerate(default_probabilities_array):
                    if count_irr[r_idx, l_idx, p_idx] > 0:
                        results.append({
                            'Interest Rate': f"{rate:.2%}",
                            'Loan Life': life,
                            'Initial Default Probability': f"{prob:.2%}",
                            'IRR': mean_irr[r_idx, l_idx, p_idx],
                            'Sample Size': count_irr[r_idx, l_idx, p_idx]
                        })
        
        if not results:
            raise ValueError("No valid IRR calculations could be completed")
        
        df = pd.DataFrame(results)
        std_dev = np.nanstd(mean_irr)
        df['IRR'] = df['IRR'] - std_dev
        
        pivot = pd.pivot_table(
            df,
            values='IRR', 
            index=['Interest Rate', 'Loan Life'],
            columns='Initial Default Probability',
            fill_value=0
        )
        
        styled = pivot.style.background_gradient(cmap=sns.color_palette("RdYlGn", as_cmap=True))
        styled = styled.format("{:.2%}")
        
        return styled
    
    def simulate_loan_lifetime(
        self, 
        n_simulations=1000,
        extra_payment_prob=0.05,
        extra_payment_amount=500,
        late_payment_prob=0.01,
        seed=None,
        plot_results=True,
        scenarios=None
    ):
        """
        Simula la durata del prestito utilizzando il metodo Monte Carlo.
        
        Parameters:
        -----------
        n_simulations : int
            Numero di simulazioni da eseguire
        extra_payment_prob : float
            Probabilità di effettuare un pagamento extra (0-1)
        extra_payment_amount : float
            Importo del pagamento extra
        late_payment_prob : float
            Probabilità di un pagamento in ritardo (0-1)
        seed : int, optional
            Seme per la generazione casuale
        plot_results : bool
            Se True, visualizza grafici dei risultati
        scenarios : list of dict, optional
            Lista di scenari da simulare, dove ogni scenario è un dizionario con
            parametri differenti (es. diverse probabilità di pagamento extra)
            
        Returns:
        --------
        dict
            Risultati delle simulazioni, incluse statistiche e distribuzioni
        """
        # Converti il tipo di ammortamento in codice numerico per numba
        amortization_type_code = 0 if self.amortization_type == "French" else 1
        
        # Prepara risultati
        results = {}
        
        # Caso singolo scenario
        if scenarios is None:
            # Esegui simulazioni
            loan_lifetime_periods = _mc_run_simulations(
                self.loan_amount,
                self.rate,  # Il tasso è già convertito in periodicità corretta
                self.pmt,
                self.periods,
                amortization_type_code,
                extra_payment_prob,
                extra_payment_amount,
                late_payment_prob,
                n_simulations,
                seed
            )
            
            # Converti periodi in anni in base alla frequenza
            frequency_factor = {
                'monthly': 12,
                'quarterly': 4,
                'semi-annual': 2,
                'annual': 1
            }.get(self.frequency, 12)
            
            loan_lifetime_years = loan_lifetime_periods / frequency_factor
            
            # Calcola statistiche
            mean = np.mean(loan_lifetime_years)
            std = np.std(loan_lifetime_years)
            
            results['base_scenario'] = {
                'lifetime_periods': loan_lifetime_periods,
                'lifetime_years': loan_lifetime_years,
                'stats': {
                    'mean_years': mean,
                    'median_years': np.median(loan_lifetime_years),
                    'std_years': std,
                    'min_years': np.min(loan_lifetime_years),
                    'max_years': np.max(loan_lifetime_years),
                    'empirical_68': [mean - std, mean + std],
                    'empirical_95': [mean - 2*std, mean + 2*std],
                    'empirical_99.7': [mean - 3*std, mean + 3*std],
                }
            }
            
            if plot_results:
                plt.figure(figsize=(10, 6))
                plt.hist(loan_lifetime_years, bins='auto', alpha=0.7, color='b', edgecolor='black')
                plt.title('Distribuzione della durata del prestito')
                plt.xlabel('Anni')
                plt.ylabel('Frequenza')
                plt.axvline(mean, color='r', linestyle='--', label=f'Media: {mean:.2f} anni')
                plt.axvline(mean - std, color='g', linestyle=':', label=f'68% ({mean-std:.2f}, {mean+std:.2f})')
                plt.axvline(mean + std, color='g', linestyle=':')
                plt.legend()
                plt.show()
                
        # Caso multi-scenario
        else:
            for i, scenario in enumerate(scenarios):
                # Estrai parametri dallo scenario o usa default
                ep_prob = scenario.get('extra_payment_prob', extra_payment_prob)
                ep_amount = scenario.get('extra_payment_amount', extra_payment_amount)
                lp_prob = scenario.get('late_payment_prob', late_payment_prob)
                scenario_name = scenario.get('name', f"Scenario {i+1}")
                
                # Esegui simulazioni per questo scenario
                loan_lifetime_periods = _mc_run_simulations(
                    self.loan_amount,
                    self.rate,
                    self.pmt,
                    self.periods,
                    amortization_type_code,
                    ep_prob,
                    ep_amount,
                    lp_prob,
                    n_simulations,
                    seed
                )
                
                # Converti periodi in anni
                frequency_factor = {
                    'monthly': 12, 'quarterly': 4, 
                    'semi-annual': 2, 'annual': 1
                }.get(self.frequency, 12)
                
                loan_lifetime_years = loan_lifetime_periods / frequency_factor
                
                # Calcola statistiche
                mean = np.mean(loan_lifetime_years)
                std = np.std(loan_lifetime_years)
                
                results[scenario_name] = {
                    'parameters': {
                        'extra_payment_prob': ep_prob,
                        'extra_payment_amount': ep_amount,
                        'late_payment_prob': lp_prob,
                    },
                    'lifetime_periods': loan_lifetime_periods,
                    'lifetime_years': loan_lifetime_years,
                    'stats': {
                        'mean_years': mean,
                        'median_years': np.median(loan_lifetime_years),
                        'std_years': std,
                        'min_years': np.min(loan_lifetime_years),
                        'max_years': np.max(loan_lifetime_years),
                        'empirical_68': [mean - std, mean + std],
                        'empirical_95': [mean - 2*std, mean + 2*std],
                        'empirical_99.7': [mean - 3*std, mean + 3*std],
                    }
                }
            
            if plot_results:
                plt.figure(figsize=(12, 7))
                for name, data in results.items():
                    plt.hist(data['lifetime_years'], bins='auto', alpha=0.5, label=name)
                plt.title('Confronto degli scenari di durata del prestito')
                plt.xlabel('Anni')
                plt.ylabel('Frequenza')
                plt.legend()
                plt.show()
                
                # Visualizza anche un grafico di confronto dei valori medi
                means = [data['stats']['mean_years'] for data in results.values()]
                plt.figure(figsize=(10, 6))
                plt.bar(results.keys(), means)
                plt.title('Durata media per scenario')
                plt.xlabel('Scenario')
                plt.ylabel('Durata media (anni)')
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.show()
        
        return results

    @classmethod
    def clear_loans(cls):
        """Pulisce la lista dei prestiti in memoria"""
        cls.loans = []
        

    @classmethod 
    def load_all_loans(cls, db_manager):
        """Carica tutti i prestiti dal database nella lista loans usando threadpooling"""
        cls.clear_loans()  # Pulisce la lista esistente
        
        try:
            # Carica i dati dal database
            loans_data = db_manager.load_all_loans_from_db()
            
            # Utilizzo di thread per caricare i prestiti in parallelo
            with ThreadPoolExecutor(max_workers=min(10, len(loans_data))) as executor:
                future_to_loan = {executor.submit(cls._load_single_loan, db_manager, loan_data): loan_data[0] 
                                for loan_data in loans_data}
                
                for future in concurrent.futures.as_completed(future_to_loan):
                    loan_id = future_to_loan[future]
                    try:
                        loan = future.result()
                        if loan:
                            cls.loans.append(loan)
                    except Exception as e:
                        print(f"Error loading loan {loan_id}: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"Error loading loans: {str(e)}")
            return False

    @classmethod
    def load_single_loan(cls, db_manager, loan_data):
        """Carica un singolo prestito dal database - utilizzato per threading"""
        try:
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
            
            return loan
            
        except Exception as e:
            print(f"Error loading loan {loan_data[0]}: {str(e)}")
            return None
