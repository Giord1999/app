import json
from loan import Loan, DbManager

class Chatbot:
    def __init__(self, intents_file):
        self.intents = self.load_intents(intents_file)
        # Mappa degli intent verso i metodi di gestione
        self.intent_methods = {
            "create_loan": self.handle_create_loan,
            "save_loan": self.handle_save_loan,
            "delete_loan": self.handle_delete_loan,
            "update_loan": self.handle_update_loan,
            "amortization_schedule": self.handle_amortization_schedule,
            "euribor_rates": self.handle_euribor_rates,
            "consolidate_loans": self.handle_consolidate_loans,
            "calculate_taeg": self.handle_calculate_taeg,
            "pricing_analysis": self.handle_pricing_analysis,
            "compare_loans": self.handle_compare_loans,
            "display_loans": self.handle_display_loans
        }
        # Crea un'istanza del gestore del database (modifica i parametri in base al tuo ambiente)
        self.db_manager = DbManager(dbname="loanmanager", user="user", password="password")
    
    def load_intents(self, file_path):
        """Carica il file degli intent."""
        with open(file_path, "r") as f:
            data = json.load(f)
        return data.get("intents", [])
    
    def get_intent(self, message):
        """Determina l'intento in base al messaggio dell'utente."""
        message_lower = message.lower()
        for intent in self.intents:
            for pattern in intent["patterns"]:
                if pattern.lower() in message_lower:
                    return intent["tag"]
        return "unknown"
    
    def start_conversation(self):
        """Avvia la conversazione in modalità loop."""
        print("Benvenuto in LoanManager GPT, il chatbot per la gestione dei prestiti! (digita 'exit' per terminare)")
        while True:
            user_input = input("Utente: ")
            if user_input.lower() == "exit":
                print("Chatbot: Arrivederci!")
                break
            intent = self.get_intent(user_input)
            if intent in self.intent_methods:
                self.intent_methods[intent]()
            else:
                print("Chatbot: Mi dispiace, non ho capito la richiesta.")
    
    def handle_create_loan(self):
        """Gestisce la creazione di un nuovo prestito."""
        print("Chatbot: Iniziamo la creazione del prestito.")
        try:
            rate = float(input("Inserisci il tasso di interesse (in decimale, es. 0.05 per 5%): "))
            term = int(input("Inserisci la durata del prestito (anni): "))
            loan_amount = float(input("Inserisci l'importo del prestito: "))
            amortization_type = input("Inserisci il tipo di ammortamento (Francese/Italiano): ")
            frequency = input("Inserisci la frequenza dei pagamenti (mensile, trimestrale, semestrale, annuale): ")
            rate_type = input("Inserisci il tipo di tasso (fisso/variabile): ")
            use_euribor = False
            update_frequency = "mensile"
            if rate_type.lower() == "variabile":
                euribor_choice = input("Vuoi usare il tasso Euribor? (si/no): ")
                if euribor_choice.lower() == "si":
                    use_euribor = True
                    update_frequency = input("Inserisci la frequenza di aggiornamento dell'Euribor (mensile, trimestrale, semestrale, annuale): ")
            downpayment_percent = float(input("Inserisci la percentuale di acconto (0 se nessuno): "))
            
            # Crea il prestito (verrà salvato automaticamente in db grazie alla logica interna)
            loan = Loan(
                db_manager=self.db_manager,
                rate=rate,
                term=term,
                loan_amount=loan_amount,
                amortization_type=amortization_type,
                frequency=frequency,
                rate_type=rate_type,
                use_euribor=use_euribor,
                update_frequency=update_frequency,
                downpayment_percent=downpayment_percent
            )
            print(f"Chatbot: Prestito creato con successo. ID: {loan.loan_id}")
        except Exception as e:
            print(f"Chatbot: Errore nella creazione del prestito: {e}")
    
    def handle_save_loan(self):
        """Gestisce il salvataggio del prestito corrente nel database."""
        print("Chatbot: Salvataggio del prestito in corso...")
        # Utilizza l'ultimo prestito creato (presente nella lista Loan.loans)
        if Loan.loans:
            loan = Loan.loans[-1]
            try:
                loan.save_to_db()
                print("Chatbot: Prestito salvato con successo.")
            except Exception as e:
                print(f"Chatbot: Errore nel salvataggio del prestito: {e}")
        else:
            print("Chatbot: Nessun prestito trovato da salvare.")
    
    def handle_delete_loan(self):
        """Gestisce l'eliminazione di un prestito."""
        print("Chatbot: Eliminazione di un prestito.")
        loan_id = input("Inserisci l'ID del prestito da eliminare: ")
        try:
            result = Loan.delete_loan(loan_id)
            if result:
                print("Chatbot: Prestito eliminato con successo.")
            else:
                print("Chatbot: Errore durante l'eliminazione del prestito.")
        except Exception as e:
            print(f"Chatbot: Errore: {e}")
    
    def handle_update_loan(self):
        """Gestisce l'aggiornamento dei dati di un prestito esistente."""
        print("Chatbot: Aggiornamento del prestito.")
        loan_id = input("Inserisci l'ID del prestito da aggiornare: ")
        loan = next((l for l in Loan.loans if l.loan_id == loan_id), None)
        if loan:
            try:
                new_rate = float(input("Inserisci il nuovo tasso di interesse: "))
                new_term = int(input("Inserisci la nuova durata (anni): "))
                new_loan_amount = float(input("Inserisci il nuovo importo del prestito: "))
                new_amortization_type = input("Inserisci il nuovo tipo di ammortamento (Francese/Italiano): ")
                new_frequency = input("Inserisci la nuova frequenza dei pagamenti (mensile, trimestrale, semestrale, annuale): ")
                new_downpayment_percent = float(input("Inserisci la nuova percentuale di acconto: "))
                loan.edit_loan(new_rate, new_term, new_loan_amount, new_amortization_type, new_frequency, new_downpayment_percent)
                print("Chatbot: Prestito aggiornato con successo.")
            except Exception as e:
                print(f"Chatbot: Errore durante l'aggiornamento: {e}")
        else:
            print("Chatbot: Prestito non trovato.")
    
    def handle_amortization_schedule(self):
        """Mostra il piano di ammortamento e, opzionalmente, il grafico relativo."""
        print("Chatbot: Visualizzazione del piano di ammortamento.")
        loan_id = input("Inserisci l'ID del prestito: ")
        loan = next((l for l in Loan.loans if l.loan_id == loan_id), None)
        if loan:
            try:
                table = loan.loan_table()
                print("Chatbot: Ecco il piano di ammortamento:")
                print(table)
                plot_choice = input("Vuoi visualizzare il grafico del saldo e degli interessi? (si/no): ")
                if plot_choice.lower() == "si":
                    loan.plot_balances()
            except Exception as e:
                print(f"Chatbot: Errore nella visualizzazione del piano: {e}")
        else:
            print("Chatbot: Prestito non trovato.")
    
    def handle_euribor_rates(self):
        """Recupera ed espone i tassi Euribor aggiornati per il prestito."""
        print("Chatbot: Recupero dei tassi Euribor per il prestito.")
        loan_id = input("Inserisci l'ID del prestito: ")
        loan = next((l for l in Loan.loans if l.loan_id == loan_id), None)
        if loan:
            if loan.rate_type.lower() == "variabile" and loan.use_euribor:
                try:
                    rates = loan.get_euribor_rates_api()
                    print("Chatbot: Tassi Euribor aggiornati:")
                    for key, value in rates.items():
                        print(f"{key}: {value}")
                except Exception as e:
                    print(f"Chatbot: Errore nel recupero dei tassi Euribor: {e}")
            else:
                print("Chatbot: Il prestito non utilizza il tasso variabile Euribor.")
        else:
            print("Chatbot: Prestito non trovato.")
    
    def handle_consolidate_loans(self):
        """Consolida più prestiti in uno solo."""
        print("Chatbot: Consolidamento dei prestiti.")
        loan_ids = input("Inserisci gli ID dei prestiti da consolidare, separati da una virgola: ")
        loan_ids = [lid.strip() for lid in loan_ids.split(",")]
        selected_loans = [l for l in Loan.loans if l.loan_id in loan_ids]
        if len(selected_loans) < 2:
            print("Chatbot: Sono necessari almeno due prestiti per il consolidamento.")
            return
        frequency = input("Inserisci la frequenza dei pagamenti per il prestito consolidato (mensile, trimestrale, semestrale, annuale): ")
        try:
            consolidated_loan = Loan.consolidate_loans(selected_loans, frequency)
            print(f"Chatbot: Prestito consolidato creato con ID: {consolidated_loan.loan_id}")
        except Exception as e:
            print(f"Chatbot: Errore nel consolidamento dei prestiti: {e}")
    
    def handle_calculate_taeg(self):
        """Calcola e mostra il TAEG del prestito."""
        print("Chatbot: Calcolo del TAEG per il prestito.")
        loan_id = input("Inserisci l'ID del prestito: ")
        loan = next((l for l in Loan.loans if l.loan_id == loan_id), None)
        if loan:
            try:
                taeg_info = loan.calculate_taeg()
                print("Chatbot:", taeg_info)
            except Exception as e:
                print(f"Chatbot: Errore nel calcolo del TAEG: {e}")
        else:
            print("Chatbot: Prestito non trovato.")
    
    def handle_pricing_analysis(self):
        """Esegue l'analisi di pricing probabilistico con simulazione Monte Carlo."""
        print("Chatbot: Esecuzione dell'analisi di pricing probabilistico (Monte Carlo).")
        loan_id = input("Inserisci l'ID del prestito: ")
        loan = next((l for l in Loan.loans if l.loan_id == loan_id), None)
        if loan:
            try:
                analysis = loan.calculate_probabilistic_pricing()
                print("Chatbot: Risultati dell'analisi di pricing:")
                # Se analysis è un DataFrame "styled", stampiamo i dati sottostanti
                print(analysis.data)
            except Exception as e:
                print(f"Chatbot: Errore nell'analisi di pricing: {e}")
        else:
            print("Chatbot: Prestito non trovato.")
    
    def handle_compare_loans(self):
        """Confronta due o più prestiti fornendo dettagli come TAEG e interessi totali."""
        print("Chatbot: Confronto tra prestiti.")
        loan_ids = input("Inserisci gli ID dei prestiti da confrontare, separati da una virgola: ")
        loan_ids = [lid.strip() for lid in loan_ids.split(",")]
        selected_loans = [l for l in Loan.loans if l.loan_id in loan_ids]
        if len(selected_loans) < 2:
            print("Chatbot: Sono necessari almeno due prestiti per il confronto.")
            return
        try:
            comparison = Loan.compare_loans(selected_loans)
            print("Chatbot: Confronto dei prestiti:")
            print(comparison)
        except Exception as e:
            print(f"Chatbot: Errore nel confronto dei prestiti: {e}")
    
    def handle_display_loans(self):
        """Visualizza tutti i prestiti attualmente salvati."""
        print("Chatbot: Visualizzazione di tutti i prestiti salvati.")
        try:
            Loan.display_loans()
        except Exception as e:
            print(f"Chatbot: Errore nella visualizzazione dei prestiti: {e}")

if __name__ == "__main__":
    # Assumiamo che il file intents.json si trovi nella stessa directory
    chatbot = Chatbot("intents.json")
    chatbot.start_conversation()
