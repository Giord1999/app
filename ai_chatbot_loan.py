import json
import difflib
import os
from loan import Loan, DbManager

#TODO: fare in modo che il chatbot sia un vero e proprio agente. Esempio: quando creo/modifico un prestito io devo poter fare in modo di crearlo direttamente in chat dicendogli tutte le cose che sono necessarie direttamente nella chat.

class Chatbot:
    def __init__(self, intents_file):
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
            "plot_graph"
        }
        
        # Aggiungiamo una mappatura degli intent che non richiedono un prestito selezionato
        self.non_loan_specific_intents = {
            "create_loan",
            "display_loans",
            "compare_loans",
            "consolidate_loans",
            "greeting"
        }
        # Istanza del gestore del database (modificare i parametri in base al proprio ambiente)
        self.db_manager = DbManager(dbname="loanmanager", user="user", password="password")


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

if __name__ == "__main__":
    # Assumiamo che il file intents.json si trovi nella stessa directory
    chatbot = Chatbot("intents.json")
    chatbot.start_conversation()
