import json
import difflib
import os
from loan import Loan, DbManager
from loan_crm import LoanCRM

class Chatbot:
    def __init__(self, intents_file, db_manager=None):
        self.intents = self.load_intents(intents_file)
        self.db_manager = db_manager
        # Converti il percorso in assoluto se è relativo
        if not os.path.isabs(intents_file):
            intents_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), intents_file)
        self.intents = self.load_intents(intents_file)
        # Aggiungiamo una mappatura degli intent che richiedono un prestito selezionato
        self.loan_specific_intents = {
            "update_loan", 
            "amortization_schedule",
            "euribor_rates",
            "calculate_taeg",
            "pricing_analysis",
            "plot_graph",
            "assign_loan_to_client",
            "assign_loan_to_corporation"
        }
        
        # Aggiungiamo una mappatura degli intent che non richiedono un prestito selezionato
        self.non_loan_specific_intents = {
            "create_loan",
            "display_loans",
            "compare_loans",
            "consolidate_loans",
            "greeting",
            "goodbye",
            "thanks",
            "add_client",
            "update_client",
            "delete_client",
            "get_client",
            "list_clients",
            "record_client_interaction",
            "get_client_interactions",
            "get_client_loans",
            "get_client_details",
            "add_corporation",
            "update_corporation",
            "delete_corporation",
            "get_corporation",
            "list_corporations",
            "record_corporation_interaction",
            "get_corporation_interactions",
            "get_corporation_loans",
            "get_corporation_details"
        }
        # Istanza del gestore del database (modificare i parametri in base al proprio ambiente)
        self.db_manager = db_manager

        self.crm = LoanCRM(db_manager=self.db_manager)

        # Mapping degli intent ai rispettivi handler
        self.intent_methods = {
            "greeting": self.handle_greeting,
            "goodbye": self.handle_goodbye,
            "thanks": self.handle_thanks,
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
            "display_loans": self.handle_display_loans,
            "plot_graph": self.handle_plot_graph,
            
            # Gestione clienti privati
            "add_client": self.handle_add_client,
            "update_client": self.handle_update_client,
            "delete_client": self.handle_delete_client,
            "get_client": self.handle_get_client,
            "list_clients": self.handle_list_clients,
            "assign_loan_to_client": self.handle_assign_loan_to_client,
            "record_client_interaction": self.handle_record_client_interaction,
            "get_client_interactions": self.handle_get_client_interactions,
            "get_client_loans": self.handle_get_client_loans,
            "get_client_details": self.handle_get_client_details,
            
            # Gestione aziende
            "add_corporation": self.handle_add_corporation,
            "update_corporation": self.handle_update_corporation,
            "delete_corporation": self.handle_delete_corporation,
            "get_corporation": self.handle_get_corporation,
            "list_corporations": self.handle_list_corporations,
            "assign_loan_to_corporation": self.handle_assign_loan_to_corporation,
            "record_corporation_interaction": self.handle_record_corporation_interaction,
            "get_corporation_interactions": self.handle_get_corporation_interactions,
            "get_corporation_loans": self.handle_get_corporation_loans,
            "get_corporation_details": self.handle_get_corporation_details
        }

    def validate_context(self, intent, selected_loan=None):
        """
        Valida il contesto dell'operazione.
        
        Args:
            intent (str): L'intent da validare
            selected_loan: Il prestito attualmente selezionato (se presente)
            
        Returns:
            tuple: (bool, str) - (validità, messaggio di errore se non valido)
        """
        if self.needs_selected_loan(intent):
            if not selected_loan:
                return False, (
                    "You need to select a loan first. "
                    "Would you like to see available loans? "
                    "Just say 'show loans' or 'display loans' and I'll help you select one."
                )
        return True, ""
    
    def needs_selected_loan(self, intent):
        """
        Verifica se l'intent richiede un prestito selezionato.
        
        Args:
            intent (str): L'intent da verificare
            
        Returns:
            bool: True se l'intent richiede un prestito selezionato, False altrimenti
        """
        return intent in self.loan_specific_intents
    
    def load_intents(self, file_path):
        """Carica il file degli intent."""
        with open(file_path, "r") as f:
            data = json.load(f)
        return data.get("intents", [])
    
    def get_intent(self, message):
        """
        Determina l'intento in base al messaggio dell'utente utilizzando fuzzy matching.
        Confronta il messaggio con ciascuno dei pattern definiti negli intent e seleziona l'intento
        corrispondente con il punteggio di similarità maggiore (se superiore ad una soglia).
        """
        message_lower = message.lower()
        best_match = None
        best_ratio = 0.0
        for intent in self.intents:
            for pattern in intent["patterns"]:
                ratio = difflib.SequenceMatcher(None, message_lower, pattern.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = intent["tag"]
                    
        # Soglia di similarità (0.6 può essere modificata in base alle esigenze)
        if best_ratio >= 0.6:
            return best_match
        return "unknown"
        
    def get_action(self, intent, selected_loan=None):
        """
        Restituisce l'azione corrispondente all'intent specificato, 
        verificando prima il contesto.
        
        Args:
            intent (str): L'intent identificato
            selected_loan: Il prestito attualmente selezionato (se presente)
            
        Returns:
            function: Il metodo di gestione o None se non valido
        """
        # Verifica il contesto
        is_valid, error_message = self.validate_context(intent, selected_loan)
        if not is_valid:
            print(f"Chatbot: {error_message}")
            return None
            
        # Se l'intent è valido, restituisci il metodo corrispondente
        if intent in self.intent_methods:
            return self.intent_methods[intent]
            
        return None
        
    def operator_confirmation(self, prompt):
        """Richiede all'operatore umano di confermare l'azione."""
        confirmation = input(prompt + " (Operatore: si/no): ")
        return confirmation.lower() == "si"
    
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

# Add these methods to the Chatbot class

    def handle_greeting(self):
        """Handles greeting intents."""
        print("Chatbot: Ciao! Sono il tuo assistente per la gestione di prestiti, clienti e aziende.")
        print("Chatbot: Come posso aiutarti oggi?")

    def handle_goodbye(self):
        """Handles goodbye intents."""
        print("Chatbot: Grazie per aver utilizzato il nostro servizio. Arrivederci!")

    def handle_thanks(self):
        """Handles thank you intents."""
        print("Chatbot: Prego! È un piacere poterti aiutare. C'è altro che posso fare per te?")

    def handle_plot_graph(self):
        """Handles plotting graph requests."""
        print("Chatbot: Creiamo un grafico per il tuo prestito.")
        loan_id = input("Inserisci l'ID del prestito: ")
        loan = next((l for l in Loan.loans if l.loan_id == loan_id), None)
        if loan:
            try:
                loan.plot_balances()
                print("Chatbot: Grafico creato con successo.")
            except Exception as e:
                print(f"Chatbot: Errore nella creazione del grafico: {e}")
        else:
            print("Chatbot: Prestito non trovato.")

    def handle_create_loan(self):
        """Gestisce la creazione di un nuovo prestito, richiedendo conferma all'operatore."""
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
            
            # Riepilogo dati raccolti
            summary = (
                f"Tasso: {rate}\n"
                f"Durata: {term}\n"
                f"Importo: {loan_amount}\n"
                f"Tipo di ammortamento: {amortization_type}\n"
                f"Frequenza: {frequency}\n"
                f"Tipo di tasso: {rate_type}\n"
                f"Uso Euribor: {use_euribor}\n"
                f"Frequenza aggiornamento: {update_frequency}\n"
                f"Acconto: {downpayment_percent}"
            )
            print("Chatbot: Riepilogo del prestito:")
            print(summary)
            if not self.operator_confirmation("Operatore, confermi la creazione del prestito con i dati sopra?"):
                print("Chatbot: Creazione del prestito annullata.")
                return
            
            # Creazione del prestito (che verrà salvato successivamente nel db se confermato)
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
        """Gestisce il salvataggio del prestito corrente nel database, previa conferma dell'operatore."""
        print("Chatbot: Salvataggio del prestito in corso...")
        if Loan.loans:
            loan = Loan.loans[-1]
            print("Chatbot: Dati del prestito da salvare:")
            print(loan)  # Si assume che Loan implementi un __str__ appropriato
            if not self.operator_confirmation("Operatore, confermi il salvataggio del prestito corrente?"):
                print("Chatbot: Salvataggio annullato.")
                return
            try:
                loan.save_to_db()
                print("Chatbot: Prestito salvato con successo.")
            except Exception as e:
                print(f"Chatbot: Errore nel salvataggio del prestito: {e}")
        else:
            print("Chatbot: Nessun prestito trovato da salvare.")
    
    def handle_delete_loan(self):
        """Gestisce l'eliminazione di un prestito, richiedendo conferma all'operatore."""
        print("Chatbot: Eliminazione di un prestito.")
        loan_id = input("Inserisci l'ID del prestito da eliminare: ")
        if not self.operator_confirmation(f"Operatore, confermi l'eliminazione del prestito con ID {loan_id}?"):
            print("Chatbot: Eliminazione annullata.")
            return
        try:
            result = Loan.delete_loan(loan_id)
            if result:
                print("Chatbot: Prestito eliminato con successo.")
            else:
                print("Chatbot: Errore durante l'eliminazione del prestito.")
        except Exception as e:
            print(f"Chatbot: Errore: {e}")
    
    def handle_update_loan(self):
        """Gestisce l'aggiornamento di un prestito esistente, previa conferma dell'operatore."""
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
                
                summary = (
                    f"Nuovo tasso: {new_rate}\n"
                    f"Nuova durata: {new_term}\n"
                    f"Nuovo importo: {new_loan_amount}\n"
                    f"Nuovo tipo di ammortamento: {new_amortization_type}\n"
                    f"Nuova frequenza: {new_frequency}\n"
                    f"Nuova percentuale di acconto: {new_downpayment_percent}"
                )
                print("Chatbot: Riepilogo aggiornamento prestito:")
                print(summary)
                if not self.operator_confirmation("Operatore, confermi l'aggiornamento del prestito?"):
                    print("Chatbot: Aggiornamento annullato.")
                    return
                
                loan.edit_loan(new_rate, new_term, new_loan_amount, new_amortization_type, new_frequency, new_downpayment_percent)
                print("Chatbot: Prestito aggiornato con successo.")
            except Exception as e:
                print(f"Chatbot: Errore durante l'aggiornamento: {e}")
        else:
            print("Chatbot: Prestito non trovato.")
    
    def handle_amortization_schedule(self):
        """Visualizza il piano di ammortamento e, opzionalmente, il grafico relativo."""
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
        """Consolida più prestiti in uno solo, previa conferma dell'operatore."""
        print("Chatbot: Consolidamento dei prestiti.")
        loan_ids = input("Inserisci gli ID dei prestiti da consolidare, separati da una virgola: ")
        loan_ids = [lid.strip() for lid in loan_ids.split(",")]
        selected_loans = [l for l in Loan.loans if l.loan_id in loan_ids]
        if len(selected_loans) < 2:
            print("Chatbot: Sono necessari almeno due prestiti per il consolidamento.")
            return
        frequency = input("Inserisci la frequenza dei pagamenti per il prestito consolidato (mensile, trimestrale, semestrale, annuale): ")
        
        print("Chatbot: Riepilogo consolidamento prestiti:")
        print("Prestiti selezionati: " + ", ".join(loan_ids))
        print("Frequenza: " + frequency)
        if not self.operator_confirmation("Operatore, confermi il consolidamento dei prestiti?"):
            print("Chatbot: Consolidamento annullato.")
            return
        
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

    # GESTIONE CLIENTI

    def handle_add_client(self):
        """Gestisce l'aggiunta di un nuovo cliente."""
        print("Chatbot: Registrazione di un nuovo cliente.")
        try:
            client_data = {
                "first_name": input("Nome: "),
                "last_name": input("Cognome: "),
                "birth_date": input("Data di nascita (YYYY-MM-DD): "),
                "address": input("Indirizzo: "),
                "city": input("Città: "),
                "state": input("Provincia/Stato: "),
                "zip_code": input("CAP: "),
                "country": input("Paese: "),
                "phone": input("Telefono: "),
                "email": input("Email: "),
                "occupation": input("Occupazione: "),
                "employer": input("Datore di lavoro: ")
            }
            
            # Gestione dati numerici
            income = input("Reddito annuale: ")
            if income:
                client_data["income"] = float(income)
                
            credit_score = input("Punteggio di credito (se disponibile): ")
            if credit_score:
                client_data["credit_score"] = int(credit_score)
            
            # Riepilogo dati cliente
            print("\nChatbot: Riepilogo dati cliente:")
            for key, value in client_data.items():
                print(f"{key}: {value}")
                
            if not self.operator_confirmation("Operatore, confermi la registrazione del cliente?"):
                print("Chatbot: Registrazione cliente annullata.")
                return
                
            client_id = self.crm.add_client(client_data)
            print(f"Chatbot: Cliente registrato con successo! ID cliente: {client_id}")
            
        except Exception as e:
            print(f"Chatbot: Errore nella registrazione del cliente: {e}")
    
    def handle_update_client(self):
        """Gestisce l'aggiornamento dei dati di un cliente."""
        print("Chatbot: Aggiornamento dati cliente.")
        try:
            client_id = input("Inserisci l'ID del cliente da aggiornare: ")
            
            # Verifica esistenza cliente
            client = self.crm.get_client(client_id)
            if not client:
                print("Chatbot: Cliente non trovato.")
                return
                
            print("Chatbot: Inserisci i nuovi dati (lascia vuoto per mantenere i valori attuali)")
            
            updated_data = {}
            fields = [
                ("first_name", "Nome"),
                ("last_name", "Cognome"),
                ("birth_date", "Data di nascita (YYYY-MM-DD)"),
                ("address", "Indirizzo"),
                ("city", "Città"),
                ("state", "Provincia/Stato"),
                ("zip_code", "CAP"),
                ("country", "Paese"),
                ("phone", "Telefono"),
                ("email", "Email"),
                ("occupation", "Occupazione"),
                ("employer", "Datore di lavoro")
            ]
            
            for field_key, field_name in fields:
                value = input(f"{field_name} [{client.get(field_key, '')}]: ")
                if value:
                    updated_data[field_key] = value
            
            # Gestione dati numerici
            income = input(f"Reddito annuale [{client.get('income', '')}]: ")
            if income:
                updated_data["income"] = float(income)
                
            credit_score = input(f"Punteggio di credito [{client.get('credit_score', '')}]: ")
            if credit_score:
                updated_data["credit_score"] = int(credit_score)
            
            if not updated_data:
                print("Chatbot: Nessuna modifica effettuata.")
                return
                
            # Riepilogo modifiche
            print("\nChatbot: Riepilogo modifiche:")
            for key, value in updated_data.items():
                print(f"{key}: {value}")
                
            if not self.operator_confirmation("Operatore, confermi l'aggiornamento del cliente?"):
                print("Chatbot: Aggiornamento cliente annullato.")
                return
                
            self.crm.update_client(client_id, updated_data)
            print("Chatbot: Dati cliente aggiornati con successo!")
            
        except Exception as e:
            print(f"Chatbot: Errore nell'aggiornamento del cliente: {e}")
    
    def handle_delete_client(self):
        """Gestisce l'eliminazione di un cliente."""
        print("Chatbot: Eliminazione cliente.")
        try:
            client_id = input("Inserisci l'ID del cliente da eliminare: ")
            
            # Verifica esistenza cliente
            client = self.crm.get_client(client_id)
            if not client:
                print("Chatbot: Cliente non trovato.")
                return
                
            print(f"Chatbot: Stai per eliminare il cliente {client.get('first_name')} {client.get('last_name')}.")
            print("ATTENZIONE: Questa operazione eliminerà anche tutte le interazioni e le associazioni ai prestiti.")
                
            if not self.operator_confirmation("Operatore, confermi l'eliminazione del cliente?"):
                print("Chatbot: Eliminazione cliente annullata.")
                return
                
            self.crm.delete_client(client_id)
            print("Chatbot: Cliente eliminato con successo!")
            
        except Exception as e:
            print(f"Chatbot: Errore nell'eliminazione del cliente: {e}")
    
    def handle_get_client(self):
        """Visualizza i dettagli di un cliente specifico."""
        print("Chatbot: Visualizzazione dettagli cliente.")
        try:
            client_id = input("Inserisci l'ID del cliente: ")
            client = self.crm.get_client(client_id)
            
            if not client:
                print("Chatbot: Cliente non trovato.")
                return
                
            print("\nChatbot: Dettagli cliente:")
            for key, value in client.items():
                if key != "documents":  # Escludiamo i documenti per semplicità
                    print(f"{key}: {value}")
            
        except Exception as e:
            print(f"Chatbot: Errore nel recupero dei dettagli del cliente: {e}")
    
    def handle_list_clients(self):
        """Visualizza l'elenco di tutti i clienti."""
        print("Chatbot: Elenco di tutti i clienti registrati.")
        try:
            clients = self.crm.list_clients()
            
            if not clients:
                print("Chatbot: Nessun cliente registrato.")
                return
                
            print(f"Chatbot: Trovati {len(clients)} clienti:")
            for i, client in enumerate(clients, 1):
                print(f"{i}. ID: {client.get('client_id')} - {client.get('first_name')} {client.get('last_name')} - {client.get('email')}")
            
        except Exception as e:
            print(f"Chatbot: Errore nel recupero dell'elenco clienti: {e}")
    
    def handle_assign_loan_to_client(self):
        """Assegna un prestito a un cliente."""
        print("Chatbot: Assegnazione di un prestito a un cliente.")
        try:
            client_id = input("Inserisci l'ID del cliente: ")
            
            # Verifica esistenza cliente
            client = self.crm.get_client(client_id)
            if not client:
                print("Chatbot: Cliente non trovato.")
                return
                
            loan_id = input("Inserisci l'ID del prestito da assegnare: ")
            loan = next((l for l in Loan.loans if l.loan_id == loan_id), None)
            
            if not loan:
                print("Chatbot: Prestito non trovato.")
                return
                
            print(f"Chatbot: Assegnazione del prestito {loan_id} al cliente {client.get('first_name')} {client.get('last_name')}.")
                
            if not self.operator_confirmation("Operatore, confermi l'assegnazione?"):
                print("Chatbot: Assegnazione prestito annullata.")
                return
                
            self.crm.assign_loan_to_client(client_id, loan_id)
            print("Chatbot: Prestito assegnato al cliente con successo!")
            
        except Exception as e:
            print(f"Chatbot: Errore nell'assegnazione del prestito: {e}")
    
    def handle_record_client_interaction(self):
        """Registra un'interazione con un cliente."""
        print("Chatbot: Registrazione interazione con cliente.")
        try:
            client_id = input("Inserisci l'ID del cliente: ")
            
            # Verifica esistenza cliente
            client = self.crm.get_client(client_id)
            if not client:
                print("Chatbot: Cliente non trovato.")
                return
                
            print(f"Chatbot: Registrazione interazione per {client.get('first_name')} {client.get('last_name')}.")
            
            interaction_type = input("Tipo di interazione (telefono, email, incontro, altro): ")
            notes = input("Note sull'interazione: ")
            
            if not self.operator_confirmation("Operatore, confermi la registrazione dell'interazione?"):
                print("Chatbot: Registrazione interazione annullata.")
                return
                
            interaction_id = self.crm.record_interaction(client_id, interaction_type, notes)
            print(f"Chatbot: Interazione registrata con successo! ID interazione: {interaction_id}")
            
        except Exception as e:
            print(f"Chatbot: Errore nella registrazione dell'interazione: {e}")
    
    def handle_get_client_interactions(self):
        """Visualizza le interazioni di un cliente."""
        print("Chatbot: Visualizzazione interazioni cliente.")
        try:
            client_id = input("Inserisci l'ID del cliente: ")
            
            # Verifica esistenza cliente
            client = self.crm.get_client(client_id)
            if not client:
                print("Chatbot: Cliente non trovato.")
                return
                
            interactions = self.crm.get_interactions(client_id)
            
            if not interactions:
                print(f"Chatbot: Nessuna interazione registrata per {client.get('first_name')} {client.get('last_name')}.")
                return
                
            print(f"Chatbot: Interazioni di {client.get('first_name')} {client.get('last_name')}:")
            for i, interaction in enumerate(interactions, 1):
                print(f"{i}. Data: {interaction.get('interaction_date')}")
                print(f"   Tipo: {interaction.get('interaction_type')}")
                print(f"   Note: {interaction.get('notes')}")
                print()
            
        except Exception as e:
            print(f"Chatbot: Errore nel recupero delle interazioni: {e}")
    
    def handle_get_client_loans(self):
        """Visualizza i prestiti di un cliente."""
        print("Chatbot: Visualizzazione prestiti cliente.")
        try:
            client_id = input("Inserisci l'ID del cliente: ")
            
            # Verifica esistenza cliente
            client = self.crm.get_client(client_id)
            if not client:
                print("Chatbot: Cliente non trovato.")
                return
                
            loans = self.crm.get_client_loans(client_id)
            
            if not loans:
                print(f"Chatbot: Nessun prestito associato a {client.get('first_name')} {client.get('last_name')}.")
                return
                
            print(f"Chatbot: Prestiti di {client.get('first_name')} {client.get('last_name')}:")
            for i, loan in enumerate(loans, 1):
                print(f"{i}. ID: {loan.get('loan_id')}")
                print(f"   Importo: {loan.get('loan_amount')}")
                print(f"   Tasso: {loan.get('rate')}")
                print(f"   Durata: {loan.get('term')} anni")
                print()
            
        except Exception as e:
            print(f"Chatbot: Errore nel recupero dei prestiti: {e}")
    
    def handle_get_client_details(self):
        """Visualizza il profilo completo di un cliente."""
        print("Chatbot: Visualizzazione profilo completo cliente.")
        try:
            client_id = input("Inserisci l'ID del cliente: ")
            
            client_details = self.crm.get_client_details(client_id)
            
            if not client_details:
                print("Chatbot: Cliente non trovato.")
                return
                
            print("\nChatbot: PROFILO COMPLETO CLIENTE")
            print("=" * 50)
            print(f"Nome: {client_details.get('first_name')} {client_details.get('last_name')}")
            print(f"Email: {client_details.get('email')}")
            print(f"Telefono: {client_details.get('phone')}")
            print(f"Indirizzo: {client_details.get('address')}, {client_details.get('city')}, {client_details.get('state')}")
            print(f"Età: {client_details.get('age', 'N/D')} anni")
            print(f"Occupazione: {client_details.get('occupation')} presso {client_details.get('employer')}")
            print(f"Reddito: {client_details.get('income')}")
            print(f"Credit score: {client_details.get('credit_score')}")
            
            print("\nRIEPILOGO PRESTITI")
            print("-" * 50)
            print(f"Numero totale prestiti: {client_details.get('loan_count')}")
            print(f"Debito totale: {client_details.get('total_debt')}")
            
            if client_details.get('loans'):
                print("\nDettaglio prestiti:")
                for i, loan in enumerate(client_details.get('loans'), 1):
                    print(f"{i}. ID: {loan.get('loan_id')}")
                    print(f"   Importo: {loan.get('loan_amount')}")
                    print(f"   Tasso: {loan.get('rate')}")
                    print(f"   Durata: {loan.get('term')} anni")
            
            print("\nSTORICO INTERAZIONI")
            print("-" * 50)
            print(f"Numero totale interazioni: {client_details.get('interaction_count')}")
            
            if client_details.get('interactions'):
                print("\nUltime interazioni:")
                for i, interaction in enumerate(client_details.get('interactions')[:5], 1):
                    print(f"{i}. Data: {interaction.get('interaction_date')}")
                    print(f"   Tipo: {interaction.get('interaction_type')}")
                    print(f"   Note: {interaction.get('notes')}")
            
        except Exception as e:
            print(f"Chatbot: Errore nel recupero del profilo cliente: {e}")
    
    # GESTIONE AZIENDE
    
    def handle_add_corporation(self):
        """Gestisce l'aggiunta di una nuova azienda."""
        print("Chatbot: Registrazione di una nuova azienda.")
        try:
            corporation_data = {
                "company_name": input("Ragione sociale: "),
                "business_type": input("Tipo di attività: "),
                "incorporation_date": input("Data di costituzione (YYYY-MM-DD): "),
                "registration_number": input("Numero di registrazione: "),
                "tax_id": input("Partita IVA/Codice fiscale: "),
                "industry": input("Settore: "),
                "headquarters_address": input("Indirizzo sede: "),
                "city": input("Città: "),
                "state": input("Provincia/Stato: "),
                "zip_code": input("CAP: "),
                "country": input("Paese: "),
                "phone": input("Telefono: "),
                "email": input("Email: "),
                "website": input("Sito web: "),
                "primary_contact_name": input("Nome referente principale: "),
                "primary_contact_role": input("Ruolo referente principale: ")
            }
            
            # Gestione dati numerici
            annual_revenue = input("Fatturato annuale: ")
            if annual_revenue:
                corporation_data["annual_revenue"] = float(annual_revenue)
                
            employees = input("Numero di dipendenti: ")
            if employees:
                corporation_data["number_of_employees"] = int(employees)
            
            # Riepilogo dati azienda
            print("\nChatbot: Riepilogo dati azienda:")
            for key, value in corporation_data.items():
                print(f"{key}: {value}")
                
            if not self.operator_confirmation("Operatore, confermi la registrazione dell'azienda?"):
                print("Chatbot: Registrazione azienda annullata.")
                return
                
            corporation_id = self.crm.add_corporation(corporation_data)
            print(f"Chatbot: Azienda registrata con successo! ID azienda: {corporation_id}")
            
        except Exception as e:
            print(f"Chatbot: Errore nella registrazione dell'azienda: {e}")
    
    def handle_update_corporation(self):
        """Gestisce l'aggiornamento dei dati di un'azienda."""
        print("Chatbot: Aggiornamento dati azienda.")
        try:
            corporation_id = input("Inserisci l'ID dell'azienda da aggiornare: ")
            
            # Verifica esistenza azienda
            corporation = self.crm.get_corporation(corporation_id)
            if not corporation:
                print("Chatbot: Azienda non trovata.")
                return
                
            print("Chatbot: Inserisci i nuovi dati (lascia vuoto per mantenere i valori attuali)")
            
            updated_data = {}
            fields = [
                ("company_name", "Ragione sociale"),
                ("business_type", "Tipo di attività"),
                ("incorporation_date", "Data di costituzione (YYYY-MM-DD)"),
                ("registration_number", "Numero di registrazione"),
                ("tax_id", "Partita IVA/Codice fiscale"),
                ("industry", "Settore"),
                ("headquarters_address", "Indirizzo sede"),
                ("city", "Città"),
                ("state", "Provincia/Stato"),
                ("zip_code", "CAP"),
                ("country", "Paese"),
                ("phone", "Telefono"),
                ("email", "Email"),
                ("website", "Sito web"),
                ("primary_contact_name", "Nome referente principale"),
                ("primary_contact_role", "Ruolo referente principale")
            ]
            
            for field_key, field_name in fields:
                value = input(f"{field_name} [{corporation.get(field_key, '')}]: ")
                if value:
                    updated_data[field_key] = value
            
            # Gestione dati numerici
            annual_revenue = input(f"Fatturato annuale [{corporation.get('annual_revenue', '')}]: ")
            if annual_revenue:
                updated_data["annual_revenue"] = float(annual_revenue)
                
            employees = input(f"Numero di dipendenti [{corporation.get('number_of_employees', '')}]: ")
            if employees:
                updated_data["number_of_employees"] = int(employees)
            
            if not updated_data:
                print("Chatbot: Nessuna modifica effettuata.")
                return
                
            # Riepilogo modifiche
            print("\nChatbot: Riepilogo modifiche:")
            for key, value in updated_data.items():
                print(f"{key}: {value}")
                
            if not self.operator_confirmation("Operatore, confermi l'aggiornamento dell'azienda?"):
                print("Chatbot: Aggiornamento azienda annullato.")
                return
                
            self.crm.update_corporation(corporation_id, updated_data)
            print("Chatbot: Dati azienda aggiornati con successo!")
            
        except Exception as e:
            print(f"Chatbot: Errore nell'aggiornamento dell'azienda: {e}")
    
    def handle_delete_corporation(self):
        """Gestisce l'eliminazione di un'azienda."""
        print("Chatbot: Eliminazione azienda.")
        try:
            corporation_id = input("Inserisci l'ID dell'azienda da eliminare: ")
            
            # Verifica esistenza azienda
            corporation = self.crm.get_corporation(corporation_id)
            if not corporation:
                print("Chatbot: Azienda non trovata.")
                return
                
            print(f"Chatbot: Stai per eliminare l'azienda {corporation.get('company_name')}.")
            print("ATTENZIONE: Questa operazione eliminerà anche tutte le interazioni e le associazioni ai prestiti.")
                
            if not self.operator_confirmation("Operatore, confermi l'eliminazione dell'azienda?"):
                print("Chatbot: Eliminazione azienda annullata.")
                return
                
            self.crm.delete_corporation(corporation_id)
            print("Chatbot: Azienda eliminata con successo!")
            
        except Exception as e:
            print(f"Chatbot: Errore nell'eliminazione dell'azienda: {e}")
    
    def handle_get_corporation(self):
        """Visualizza i dettagli di un'azienda specifica."""
        print("Chatbot: Visualizzazione dettagli azienda.")
        try:
            corporation_id = input("Inserisci l'ID dell'azienda: ")
            corporation = self.crm.get_corporation(corporation_id)
            
            if not corporation:
                print("Chatbot: Azienda non trovata.")
                return
                
            print("\nChatbot: Dettagli azienda:")
            for key, value in corporation.items():
                if key != "documents":  # Escludiamo i documenti per semplicità
                    print(f"{key}: {value}")
            
        except Exception as e:
            print(f"Chatbot: Errore nel recupero dei dettagli dell'azienda: {e}")
    
    def handle_list_corporations(self):
        """Visualizza l'elenco di tutte le aziende."""
        print("Chatbot: Elenco di tutte le aziende registrate.")
        try:
            corporations = self.crm.list_corporations()
            
            if not corporations:
                print("Chatbot: Nessuna azienda registrata.")
                return
                
            print(f"Chatbot: Trovate {len(corporations)} aziende:")
            for i, corporation in enumerate(corporations, 1):
                print(f"{i}. ID: {corporation.get('corporation_id')} - {corporation.get('company_name')} - {corporation.get('industry')}")
            
        except Exception as e:
            print(f"Chatbot: Errore nel recupero dell'elenco aziende: {e}")
    
    def handle_assign_loan_to_corporation(self):
        """Assegna un prestito a un'azienda."""
        print("Chatbot: Assegnazione di un prestito a un'azienda.")
        try:
            corporation_id = input("Inserisci l'ID dell'azienda: ")
            
            # Verifica esistenza azienda
            corporation = self.crm.get_corporation(corporation_id)
            if not corporation:
                print("Chatbot: Azienda non trovata.")
                return
                
            loan_id = input("Inserisci l'ID del prestito da assegnare: ")
            loan = next((l for l in Loan.loans if l.loan_id == loan_id), None)
            
            if not loan:
                print("Chatbot: Prestito non trovato.")
                return
                
            print(f"Chatbot: Assegnazione del prestito {loan_id} all'azienda {corporation.get('company_name')}.")
                
            if not self.operator_confirmation("Operatore, confermi l'assegnazione?"):
                print("Chatbot: Assegnazione prestito annullata.")
                return
                
            self.crm.assign_loan_to_corporation(corporation_id, loan_id)
            print("Chatbot: Prestito assegnato all'azienda con successo!")
            
        except Exception as e:
            print(f"Chatbot: Errore nell'assegnazione del prestito: {e}")
    
    def handle_record_corporation_interaction(self):
        """Registra un'interazione con un'azienda."""
        print("Chatbot: Registrazione interazione con azienda.")
        try:
            corporation_id = input("Inserisci l'ID dell'azienda: ")
            
            # Verifica esistenza azienda
            corporation = self.crm.get_corporation(corporation_id)
            if not corporation:
                print("Chatbot: Azienda non trovata.")
                return
                
            print(f"Chatbot: Registrazione interazione per {corporation.get('company_name')}.")
            
            interaction_type = input("Tipo di interazione (telefono, email, incontro, altro): ")
            notes = input("Note sull'interazione: ")
            
            if not self.operator_confirmation("Operatore, confermi la registrazione dell'interazione?"):
                print("Chatbot: Registrazione interazione annullata.")
                return
                
            interaction_id = self.crm.record_corporation_interaction(corporation_id, interaction_type, notes)
            print(f"Chatbot: Interazione registrata con successo! ID interazione: {interaction_id}")
            
        except Exception as e:
            print(f"Chatbot: Errore nella registrazione dell'interazione: {e}")
    
    def handle_get_corporation_interactions(self):
        """Visualizza le interazioni di un'azienda."""
        print("Chatbot: Visualizzazione interazioni azienda.")
        try:
            corporation_id = input("Inserisci l'ID dell'azienda: ")
            
            # Verifica esistenza azienda
            corporation = self.crm.get_corporation(corporation_id)
            if not corporation:
                print("Chatbot: Azienda non trovata.")
                return
                
            interactions = self.crm.get_corporation_interactions(corporation_id)
            
            if not interactions:
                print(f"Chatbot: Nessuna interazione registrata per {corporation.get('company_name')}.")
                return
                
            print(f"Chatbot: Interazioni di {corporation.get('company_name')}:")
            for i, interaction in enumerate(interactions, 1):
                print(f"{i}. Data: {interaction.get('interaction_date')}")
                print(f"   Tipo: {interaction.get('interaction_type')}")
                print(f"   Note: {interaction.get('notes')}")
                print()
            
        except Exception as e:
            print(f"Chatbot: Errore nel recupero delle interazioni: {e}")
    
    def handle_get_corporation_loans(self):
        """Visualizza i prestiti di un'azienda."""
        print("Chatbot: Visualizzazione prestiti azienda.")
        try:
            corporation_id = input("Inserisci l'ID dell'azienda: ")
            
            # Verifica esistenza azienda
            corporation = self.crm.get_corporation(corporation_id)
            if not corporation:
                print("Chatbot: Azienda non trovata.")
                return
                
            loans = self.crm.get_corporation_loans(corporation_id)
            
            if not loans:
                print(f"Chatbot: Nessun prestito associato a {corporation.get('company_name')}.")
                return
                
            print(f"Chatbot: Prestiti di {corporation.get('company_name')}:")
            for i, loan in enumerate(loans, 1):
                print(f"{i}. ID: {loan.get('loan_id')}")
                print(f"   Importo: {loan.get('loan_amount')}")
                print(f"   Tasso: {loan.get('rate')}")
                print(f"   Durata: {loan.get('term')} anni")
                print()
            
        except Exception as e:
            print(f"Chatbot: Errore nel recupero dei prestiti: {e}")
    
    def handle_get_corporation_details(self):
        """Visualizza il profilo completo di un'azienda."""
        print("Chatbot: Visualizzazione profilo completo azienda.")
        try:
            corporation_id = input("Inserisci l'ID dell'azienda: ")
            
            corporation_details = self.crm.get_corporation_details(corporation_id)
            
            if not corporation_details:
                print("Chatbot: Azienda non trovata.")
                return
                
            print("\nChatbot: PROFILO COMPLETO AZIENDA")
            print("=" * 50)
            print(f"Ragione sociale: {corporation_details.get('company_name')}")
            print(f"Settore: {corporation_details.get('industry')}")
            print(f"Tipo: {corporation_details.get('business_type')}")
            print(f"P.IVA/CF: {corporation_details.get('tax_id')}")
            print(f"Età azienda: {corporation_details.get('company_age_years', 'N/D')} anni")
            print(f"Indirizzo: {corporation_details.get('headquarters_address')}, {corporation_details.get('city')}")
            print(f"Contatti: {corporation_details.get('email')} - {corporation_details.get('phone')}")
            print(f"Sito web: {corporation_details.get('website')}")
            print(f"Referente: {corporation_details.get('primary_contact_name')} ({corporation_details.get('primary_contact_role')})")
            print(f"Dipendenti: {corporation_details.get('number_of_employees')}")
            print(f"Fatturato: {corporation_details.get('annual_revenue')}")
            
            print("\nRIEPILOGO PRESTITI")
            print("-" * 50)
            print(f"Numero totale prestiti: {corporation_details.get('loan_count')}")
            print(f"Debito totale: {corporation_details.get('total_debt')}")
            
            if corporation_details.get('loans'):
                print("\nDettaglio prestiti:")
                for i, loan in enumerate(corporation_details.get('loans'), 1):
                    print(f"{i}. ID: {loan.get('loan_id')}")
                    print(f"   Importo: {loan.get('loan_amount')}")
                    print(f"   Tasso: {loan.get('rate')}")
                    print(f"   Durata: {loan.get('term')} anni")
            
            print("\nSTORICO INTERAZIONI")
            print("-" * 50)
            print(f"Numero totale interazioni: {corporation_details.get('interaction_count')}")
            
            if corporation_details.get('interactions'):
                print("\nUltime interazioni:")
                for i, interaction in enumerate(corporation_details.get('interactions')[:5], 1):
                    print(f"{i}. Data: {interaction.get('interaction_date')}")
                    print(f"   Tipo: {interaction.get('interaction_type')}")
                    print(f"   Note: {interaction.get('notes')}")
            
        except Exception as e:
            print(f"Chatbot: Errore nel recupero del profilo azienda: {e}")

if __name__ == "__main__":
    # Assumiamo che il file intents.json si trovi nella stessa directory
    chatbot = Chatbot("intents.json")
    chatbot.start_conversation()
