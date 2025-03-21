from loan import Loan, DbManager
from loan_crm import LoanCRM
import pandas as pd
import numpy as np
import datetime as dt
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.legends import Legend 
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import LineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.units import inch, cm
import matplotlib.pyplot as plt
import io
from PIL import Image as PILImage

_original_getSampleStyleSheet = getSampleStyleSheet

def _extended_getSampleStyleSheet():
    """Versione estesa di getSampleStyleSheet che include sempre lo stile Subtitle"""
    styles = _original_getSampleStyleSheet()
    if 'Subtitle' not in styles:
        styles.add(ParagraphStyle(
            name='Subtitle',
            fontName='Helvetica-Bold',
            fontSize=14,
            spaceAfter=10
        ))
    return styles

getSampleStyleSheet = _extended_getSampleStyleSheet

class LoanReport:
    """
    Classe per generare report avanzati sulla gestione dei prestiti.
    
    Funzionalità implementate (a parte la dashboard):
      - Report di sintesi del portafoglio (KPI, totali, medie)
      - Report comparativo tra prestiti
      - Report dettagliato di ammortamento per un prestito specifico
      - Report di pricing probabilistico (Monte Carlo)
      - Report aggregato delle performance del CRM (clienti, interazioni, assegnazioni)
      - Esportazione dei report in CSV e PDF
      - Report avanzato di segmentazione clienti (reddito, credito, clustering)
      - Report predittivo sul trend dei tassi Euribor (medie mobili)
    """
    
    def __init__(self, db_manager: DbManager, loan_crm: LoanCRM = None):
        self.db_manager = db_manager
        self.loan_crm = loan_crm

    def load_all_loans(self):
        """Carica tutti i prestiti dal database e li restituisce come lista di oggetti Loan."""
        success = Loan.load_all_loans(self.db_manager)
        if not success:
            raise Exception("Errore nel caricamento dei prestiti dal database.")
        return Loan.loans

    def generate_portfolio_summary(self):
        """
        Genera un report di sintesi del portafoglio di prestiti.
        
        Restituisce un dizionario contenente:
         - Numero totale di prestiti
         - Importo totale erogato
         - Media del tasso iniziale
         - Media del TAEG (periodico e annualizzato)
         - Interesse totale cumulato previsto
        """
        loans = self.load_all_loans()
        if not loans:
            return "Nessun prestito trovato."
            
        total_loans = len(loans)
        total_amount = sum(loan.loan_amount for loan in loans)
        avg_initial_rate = np.mean([loan.initial_rate for loan in loans])
        
        # Assicura che il TAEG sia calcolato per ogni prestito
        for loan in loans:
            if not loan.taeg:
                loan.calculate_taeg()
        avg_taeg_periodic = np.mean([loan.taeg.get('periodic', 0) for loan in loans])
        avg_taeg_annualized = np.mean([loan.taeg.get('annualized', 0) for loan in loans])
        total_interest = sum(loan.table["Interest"].cumsum().iloc[-1] for loan in loans)
        
        summary = {
            "Total Loans": total_loans,
            "Total Loan Amount": total_amount,
            "Average Initial Rate": avg_initial_rate,
            "Average TAEG Periodic (%)": avg_taeg_periodic,
            "Average TAEG Annualized (%)": avg_taeg_annualized,
            "Total Interest to be Paid": total_interest
        }
        return summary

    def generate_comparative_report(self, loans: list = None):
        """
        Genera un report comparativo tra prestiti.
        
        Se la lista non viene fornita, utilizza tutti i prestiti caricati.
        Restituisce una stringa formattata con i dettagli comparativi.
        """
        if loans is None:
            loans = self.load_all_loans()
        if len(loans) < 2:
            return "Occorrono almeno due prestiti per il confronto."
            
        report = Loan.compare_loans(loans)
        return report

    def generate_amortization_report(self, loan_id: str):
        """
        Genera il piano di ammortamento per il prestito specificato.
        
        Parametri:
          loan_id: identificativo del prestito
          
        Restituisce un DataFrame con la tabella di ammortamento.
        """
        loans = self.load_all_loans()
        loan = next((l for l in loans if l.loan_id == loan_id), None)
        if loan is None:
            raise ValueError(f"Prestito con ID {loan_id} non trovato.")
        # Ricalcola e restituisce la tabella di ammortamento
        amort_table = loan.loan_table()
        return amort_table

    def generate_probabilistic_pricing_report(self, loan_id: str, **kwargs):
        """
        Genera un report di pricing probabilistico per il prestito specificato.
        
        Parametri addizionali possono essere passati via kwargs e verranno
        propagati al metodo calculate_probabilistic_pricing del prestito.
        
        Restituisce tipicamente un oggetto (DataFrame o Pandas Styler) con i risultati.
        """
        loans = self.load_all_loans()
        loan = next((l for l in loans if l.loan_id == loan_id), None)
        if loan is None:
            raise ValueError(f"Prestito con ID {loan_id} non trovato.")
        report = loan.calculate_probabilistic_pricing(**kwargs)
        return report
    
    def generate_client_segmentation_report(self):
        """
        Genera un report di segmentazione dei clienti basato su parametri rilevanti.
        
        Include:
        - Segmentazione per fasce di reddito
        - Segmentazione per area geografica
        - Segmentazione per credit score
        - Clustering automatico basato su parametri multipli
        
        Restituisce un dizionario con i risultati della segmentazione.
        """
        if self.loan_crm is None:
            raise Exception("Modulo CRM non disponibile per la segmentazione.")
            
        clients = self.loan_crm.list_clients()
        if not clients:
            return {"error": "Nessun cliente trovato"}
            
        # Recupero dati dettagliati dei clienti
        client_details = []
        for client in clients:
            client_id = client.get("client_id")
            details = self.loan_crm.get_client_details(client_id)  # Assumo esista questo metodo
            if details:
                client_details.append(details)
        
        # Converto in DataFrame per facilitare l'analisi
        df_clients = pd.DataFrame(client_details)
        
        # 1. Segmentazione per fasce di reddito
        income_segments = {
            'Basso': (0, 30000),
            'Medio': (30000, 70000),
            'Alto': (70000, float('inf'))
        }
        
        income_distribution = {}
        for segment, (min_val, max_val) in income_segments.items():
            count = len(df_clients[(df_clients['income'] >= min_val) & (df_clients['income'] < max_val)])
            income_distribution[segment] = count
        
        # 2. Segmentazione per area geografica
        geo_distribution = df_clients['region'].value_counts().to_dict()
        
        # 3. Segmentazione per credit score
        credit_segments = {
            'Rischio alto': (300, 580),
            'Rischio medio': (580, 670),
            'Buono': (670, 740),
            'Eccellente': (740, 850)
        }
        
        credit_distribution = {}
        for segment, (min_val, max_val) in credit_segments.items():
            count = len(df_clients[(df_clients['credit_score'] >= min_val) & (df_clients['credit_score'] < max_val)])
            credit_distribution[segment] = count
        
        # 4. Clustering automatico con K-means
        from sklearn.cluster import KMeans
        import warnings
        from sklearn.metrics import silhouette_score
        from sklearn.preprocessing import StandardScaler
        
        # Selezione feature per clustering
        features = ['income', 'age', 'credit_score', 'loan_count', 'total_debt']
        feature_cols = [col for col in features if col in df_clients.columns]
        
        if feature_cols:
            # Normalizzazione dei dati
            X = df_clients[feature_cols].fillna(0)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            

            # Trova il numero ottimale di cluster
            # Imposta range di possibili cluster da valutare
            max_clusters = min(10, len(df_clients) - 1)  # Evita più cluster che dati
            range_clusters = range(2, max_clusters + 1)

            # Vettori per memorizzare metriche di valutazione
            wcss = []  # Within-Cluster Sum of Square
            silhouette_scores = []  # Coefficiente di silhouette

            # Calcola WCSS e silhouette per ogni k
            for k in range_clusters:
                # K-means
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(X_scaled)
                wcss.append(kmeans.inertia_)
                
                # Silhouette score (ignora warning per k=n o k=1)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    silhouette_scores.append(silhouette_score(X_scaled, kmeans.labels_))

            # Metodo del gomito (cerca dove la pendenza cambia significativamente)
            if len(wcss) > 2:
                diffs = np.diff(wcss)
                diffs_of_diffs = np.diff(diffs)
                elbow_k = np.argmax(diffs_of_diffs) + 2  # +2 per compensare i due np.diff
            else:
                elbow_k = 2

            # Miglior valore secondo silhouette (massimo valore)
            if silhouette_scores:
                silhouette_k = range_clusters[np.argmax(silhouette_scores)]
            else:
                silhouette_k = 2
                
            # Determina n_clusters finale (media ponderata dei due metodi)
            n_clusters = int(np.ceil((elbow_k + silhouette_k) / 2))

            # Garantisce limiti ragionevoli per n_clusters
            n_clusters = max(2, min(n_clusters, len(df_clients) // 5))  # Min 2, max 1/5 dei dati

            # Applica K-means
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            df_clients['cluster'] = kmeans.fit_predict(X_scaled)
            
            # Analisi dei cluster
            cluster_profiles = {}
            for i in range(n_clusters):
                cluster_data = df_clients[df_clients['cluster'] == i]
                cluster_profiles[f'Cluster {i+1}'] = {
                    'count': len(cluster_data),
                    'avg_income': cluster_data['income'].mean() if 'income' in df_clients else 'N/A',
                    'avg_age': cluster_data['age'].mean() if 'age' in df_clients else 'N/A',
                    'avg_credit_score': cluster_data['credit_score'].mean() if 'credit_score' in df_clients else 'N/A'
                }
        else:
            cluster_profiles = {'error': 'Dati insufficienti per clustering'}
        
        # Combina i risultati
        segmentation_report = {
            'income_segments': income_distribution,
            'geographical_segments': geo_distribution,
            'credit_score_segments': credit_distribution,
            'cluster_profiles': cluster_profiles,
        }
        
        return segmentation_report

    def generate_crm_performance_report(self):
        """
        Genera un report aggregato relativo al modulo CRM.
        
        Include:
          - Numero totale di clienti
          - Media delle interazioni per cliente
          - Media dei prestiti assegnati per cliente
        
        Restituisce un dizionario con queste metriche.
        """
        if self.loan_crm is None:
            raise Exception("Modulo CRM non disponibile per il report.")
            
        clients = self.loan_crm.list_clients()
        total_clients = len(clients)
        interactions_count = []
        loans_count = []
        for client in clients:
            client_id = client.get("client_id")
            interactions = self.loan_crm.get_interactions(client_id)
            interactions_count.append(len(interactions))
            client_loans = self.loan_crm.get_client_loans(client_id)
            loans_count.append(len(client_loans))
            
        avg_interactions = np.mean(interactions_count) if interactions_count else 0
        avg_loans = np.mean(loans_count) if loans_count else 0
        
        crm_report = {
            "Total Clients": total_clients,
            "Average Interactions per Client": avg_interactions,
            "Average Loans per Client": avg_loans
        }
        return crm_report

    def generate_enhanced_crm_report(self):
        """
        Genera un report CRM completo che include sia le performance che la segmentazione.
        """
        try:
            performance_report = self.generate_crm_performance_report()
            segmentation_report = self.generate_client_segmentation_report()
            
            enhanced_report = {
                'performance_metrics': performance_report,
                'client_segmentation': segmentation_report
            }
            
            return enhanced_report
        except Exception as e:
            return {"error": f"Errore nella generazione del report avanzato: {str(e)}"}

    def export_report_to_csv(self, report_df: pd.DataFrame, filepath: str):
        """
        Esporta un DataFrame (report) in un file CSV.
        
        Restituisce il percorso assoluto del file esportato.
        """
        report_df.to_csv(filepath, index=True)
        return os.path.abspath(filepath)
    
    def generate_forecasting_report(self, frequency: str = 'monthly', start: str = '1994-01-01', end: str = None):
        """
        Genera un report predittivo basato sui dati storici dell'Euribor.
        
        Utilizza la funzione get_euribor_series presente in Loan per scaricare i dati,
        ed aggiunge una colonna con la media mobile (window di 12 periodi) come previsione semplice.
        
        Parametri:
          frequency: frequenza dei dati (e.g., 'monthly', 'quarterly', ...)
          start: data di inizio (stringa)
          end: data di fine (se None, usa la data corrente)
        
        Restituisce un DataFrame con i dati storici e la previsione.
        """
        if end is None:
            end = dt.datetime.now().strftime('%Y-%m-%d')
        try:
            euribor_data = Loan.get_euribor_series(frequency, start, end)
        except Exception as e:
            raise ValueError(f"Errore nel recupero dei dati Euribor: {e}")
        
        # Ordina per data e calcola la media mobile
        euribor_data = euribor_data.sort_values("TIME_PERIOD")
        euribor_data["Moving_Avg"] = euribor_data["OBS_VALUE"].rolling(window=12, min_periods=1).mean()
        
        return euribor_data
    
    def export_to_pdf(self, report_data, report_type, filepath):
        """
        Esporta un report in formato PDF professionale.
        
        Parametri:
          report_data: I dati del report (DataFrame, dizionario, ecc.)
          report_type: Il tipo di report ('portfolio', 'comparative', 'amortization', ecc.)
          filepath: Il percorso del file dove salvare il PDF
          
        Restituisce il percorso assoluto del file esportato.
        """
        # Inizializziamo il documento PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Lista degli elementi da aggiungere al PDF
        elements = []
        
        # Stili di testo
        styles = getSampleStyleSheet()
        styles["Title"].fontSize = 16
        styles["Title"].alignment = 1
        styles["Title"].spaceAfter = 12

        styles["Subtitle"].fontSize = 14
        styles["Subtitle"].spaceAfter = 10

        styles["Normal"].fontSize = 10
        styles["Normal"].spaceAfter = 6

        # Aggiungi solo stili custom con nomi diversi se necessario
        styles.add(ParagraphStyle(
            name='CustomHeading',
            fontName='Helvetica-Bold',
            fontSize=15,
            alignment=1,
            spaceAfter=10
        ))

        
        # Aggiungi intestazione
        current_date = dt.datetime.now().strftime("%d/%m/%Y")
        elements.append(Paragraph(f"Report generato il {current_date}", styles["Normal"]))
        
        # Aggiungi logo (se disponibile)
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "assets/logo.png")
            if os.path.exists(logo_path):
                img = Image(logo_path, width=2*inch, height=1*inch)
                elements.append(img)
                elements.append(Spacer(1, 12))
        except Exception:
            pass  # Se non c'è logo, procedi senza
        
        # In base al tipo di report, formatta i dati in modo appropriato
        if report_type == "portfolio":
            self._format_portfolio_pdf(elements, report_data, styles)
        elif report_type == "comparative":
            self._format_comparative_pdf(elements, report_data, styles)
        elif report_type == "amortization":
            self._format_amortization_pdf(elements, report_data, styles)
        elif report_type == "probabilistic":
            self._format_probabilistic_pdf(elements, report_data, styles)
        elif report_type == "client_segmentation":
            self._format_segmentation_pdf(elements, report_data, styles)
        elif report_type == "crm_performance":
            self._format_crm_pdf(elements, report_data, styles)
        elif report_type == "euribor_forecast":
            self._format_forecast_pdf(elements, report_data, styles)
        else:
            elements.append(Paragraph("Tipo di report non supportato", styles["Normal"]))
        
        # Aggiungi piè di pagina
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Documento confidenziale - Solo per uso interno", styles["Normal"]))
        
        # Costruisci il documento
        doc.build(elements)
        return os.path.abspath(filepath)
    
    def _format_portfolio_pdf(self, elements, data, styles):
        """Formatta un report di sintesi del portafoglio per PDF."""
        elements.append(Paragraph("REPORT DI SINTESI DEL PORTAFOGLIO PRESTITI", styles["Title"]))
        elements.append(Spacer(1, 12))
        
        # Descrizione
        elements.append(Paragraph(
            "Questo report fornisce una panoramica complessiva del portafoglio prestiti, "
            "includendo metriche chiave per supportare decisioni strategiche.", 
            styles["Normal"]
        ))
        elements.append(Spacer(1, 12))
        
        # Tabella dei KPI principali
        table_data = [["Metrica", "Valore"]]
        for key, value in data.items():
            formatted_value = f"{value:,.2f}" if isinstance(value, (int, float)) else str(value)
            # Modifica le etichette per renderle più leggibili
            readable_key = key.replace("_", " ").title()
            table_data.append([readable_key, formatted_value])
            
        table = Table(table_data, colWidths=[250, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Aggiungi un grafico
        # Creiamo un grafico a torta per la distribuzione del capitale
        if "Total Loan Amount" in data and "Total Interest to be Paid" in data:
            self._add_chart_to_pdf(elements, {
                "Principal": data["Total Loan Amount"],
                "Interest": data["Total Interest to be Paid"]
            }, "Distribuzione Capitale e Interessi", chart_type="pie", styles=styles)
        
        # Aggiungi raccomandazioni
        elements.append(Paragraph("Raccomandazioni", styles["Subtitle"]))
        elements.append(Paragraph(
            "Sulla base dell'analisi del portafoglio, si raccomanda di:",
            styles["Normal"]
        ))
        
        # Genera raccomandazioni dinamiche basate sui dati
        recommendations = []
        if data.get("Average TAEG Annualized (%)", 0) > 5:
            recommendations.append("Valutare opportunità di rifinanziamento per i prestiti con TAEG elevato")
        if data.get("Total Loans", 0) > 10:
            recommendations.append("Considerare la diversificazione del portafoglio")
        if data.get("Average Initial Rate", 0) < 3:
            recommendations.append("Monitorare l'andamento dei tassi per potenziali aumenti")
        
        # Se non ci sono raccomandazioni specifiche, aggiungi un punto generico
        if not recommendations:
            recommendations.append("Continuare il monitoraggio regolare del portafoglio")
        
        # Aggiungi le raccomandazioni al documento
        for i, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(f"{i}. {rec}", styles["Normal"]))
    
    def _format_comparative_pdf(self, elements, data, styles):
        """Formatta un report comparativo tra prestiti per PDF."""
        elements.append(Paragraph("REPORT COMPARATIVO TRA PRESTITI", styles["Title"]))
        elements.append(Spacer(1, 12))
        
        if isinstance(data, str):
            # Se i dati sono una stringa, probabilmente è un messaggio di errore
            elements.append(Paragraph(data, styles["Normal"]))
            return
        
        elements.append(Paragraph(
            "Questo report confronta i dettagli di diversi prestiti per facilitare "
            "l'analisi comparativa e supportare le decisioni di gestione del portafoglio.", 
            styles["Normal"]
        ))
        elements.append(Spacer(1, 12))
        
        if isinstance(data, dict):
            # Se i dati sono già in formato dizionario
            for section, section_data in data.items():
                elements.append(Paragraph(section, styles["Subtitle"]))
                if isinstance(section_data, dict):
                    table_data = [["Parametro", "Valore"]]
                    for key, value in section_data.items():
                        table_data.append([key, str(value)])
                    table = Table(table_data, colWidths=[250, 150])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                    ]))
                    elements.append(table)
                else:
                    elements.append(Paragraph(str(section_data), styles["Normal"]))
                elements.append(Spacer(1, 12))
        elif isinstance(data, pd.DataFrame):
            # Se è un DataFrame, visualizzalo come tabella
            table_data = [data.columns.tolist()]
            for _, row in data.iterrows():
                table_data.append([str(x) for x in row.tolist()])
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph(str(data), styles["Normal"]))
            
    def _format_amortization_pdf(self, elements, data, styles):
        """Formatta un piano di ammortamento per PDF."""
        elements.append(Paragraph("PIANO DI AMMORTAMENTO", styles["Title"]))
        elements.append(Spacer(1, 12))
        
        if not isinstance(data, pd.DataFrame):
            elements.append(Paragraph("Dati di ammortamento non validi", styles["Normal"]))
            return
            
        elements.append(Paragraph(
            "Questo report mostra il piano di ammortamento dettagliato del prestito, "
            "includendo pagamenti periodici, interessi e capitale residuo.", 
            styles["Normal"]
        ))
        elements.append(Spacer(1, 12))
        
        # Aggiungi i dettagli del prestito
        loan_details = [
            f"Importo prestito: {data['Initial Debt'].iloc[0]:,.2f}",   
            f"Durata: {len(data)} rate",
            f"Rata: {data['Payment'].iloc[0]:,.2f}"
        ]
        for detail in loan_details:
            elements.append(Paragraph(detail, styles["Normal"]))
        elements.append(Spacer(1, 12))
        
        # Prepara la tabella di ammortamento (potrebbe essere necessario paginarla se troppo grande)
        max_rows_per_page = 20
        if len(data) > max_rows_per_page:
            # Utilizzare paginazione per tabelle grandi
            for start_idx in range(0, len(data), max_rows_per_page):
                if start_idx > 0:
                    elements.append(PageBreak())
                    elements.append(Paragraph("PIANO DI AMMORTAMENTO (continua)", styles["Title"]))
                    elements.append(Spacer(1, 12))
                
                end_idx = min(start_idx + max_rows_per_page, len(data))
                chunk = data.iloc[start_idx:end_idx]
                
                # Formatta tabella per questa pagina
                self._add_amortization_table(elements, chunk)
        else:
            # Se i dati sono pochi, mostrali tutti in una pagina
            self._add_amortization_table(elements, data)
                
        # Aggiungi un grafico dell'andamento del capitale residuo vs interessi pagati
        if len(data) > 1:
            self._add_chart_to_pdf(
                elements, 
                {
                    "Capitale residuo": data["Balance"].values,
                    "Interessi cumulati": data["Interest"].cumsum().values
                },
                "Andamento Capitale Residuo e Interessi",
                chart_type="line", styles=styles
            )
            
    def _add_amortization_table(self, elements, data):
        """Aggiunge una tabella di ammortamento al PDF."""
        # Seleziona solo le colonne principali per il report con mapping corretto
        display_cols = ["Initial Debt", "Payment", "Principal", "Interest", "Balance"]
        display_cols = [col for col in display_cols if col in data.columns]
        
        # Prepara intestazioni tradotte
        header_map = {
            "Initial Debt": "Debito Iniziale", 
            "Payment": "Rata", 
            "Principal": "Capitale", 
            "Interest": "Interessi", 
            "Balance": "Residuo"
        }
            # Crea tabella
        table_data = [[header_map.get(col, col) for col in display_cols]]
        
        # Aggiungi righe con formattazione
        for _, row in data.iterrows():
            table_row = []
            for col in display_cols:
                value = row[col]
                if isinstance(value, (int, float)):
                    if col == "Period":
                        formatted_value = f"{int(value)}"
                    else:
                        formatted_value = f"{value:,.2f}"
                else:
                    formatted_value = str(value)
                table_row.append(formatted_value)
            table_data.append(table_row)
                
        # Crea e formatta tabella
        col_widths = [60] + [90] * (len(display_cols) - 1)  # Larghezza colonne
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Allinea a destra i valori numerici
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # Riduce dimensione font per far stare più dati
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 12))
    
    def _format_probabilistic_pdf(self, elements, data, styles):
        """Formatta un report di pricing probabilistico per PDF."""
        elements.append(Paragraph("REPORT DI PRICING PROBABILISTICO", styles["Title"]))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(
            "Questo report mostra l'analisi probabilistica del prestito basata su simulazioni "
            "Monte Carlo, evidenziando i potenziali scenari di tasso e il loro impatto.", 
            styles["Normal"]
        ))
        elements.append(Spacer(1, 12))
        
        # Estrai e visualizza i risultati principali
        if isinstance(data, pd.DataFrame):
            # Statistiche di riepilogo
            elements.append(Paragraph("Statistiche di Simulazione", styles["Subtitle"]))
            
            summary_data = [
                ["Metrica", "Valore"],
                ["Media", f"{data.mean().mean():.2f}"],
                ["Mediana", f"{data.median().mean():.2f}"],
                ["Min", f"{data.min().min():.2f}"],
                ["Max", f"{data.max().max():.2f}"],
                ["Deviazione Standard", f"{data.std().mean():.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[200, 150])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 20))
            
            # Se il DataFrame è troppo grande, mostrane solo un campione
            if len(data.columns) > 8 or len(data) > 20:
                elements.append(Paragraph("Campione dei Risultati di Simulazione", styles["Subtitle"]))
                sample_data = data.iloc[:10, :5]  # Primi 10 righe, 5 colonne
            else:
                elements.append(Paragraph("Risultati di Simulazione", styles["Subtitle"]))
                sample_data = data
                
            # Visualizza i dati campione come tabella
            table_data = [[""] + [str(col) for col in sample_data.columns]]
            for idx, row in sample_data.iterrows():
                table_data.append([str(idx)] + [f"{val:.2f}" if isinstance(val, (int, float)) else str(val) 
                                                for val in row.values])
                
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),  # Riduce dimensione font
            ]))
            elements.append(table)
            
            # Aggiungi un istogramma della distribuzione
            if len(data) > 1:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("Distribuzione dei Risultati", styles["Subtitle"]))
                
                # Salva il grafico in un buffer di memoria
                buffer = io.BytesIO()
                plt.figure(figsize=(8, 4))
                data_array = data.values.flatten()
                plt.hist(data_array, bins=30, alpha=0.7, color='blue')
                plt.title("Distribuzione dei Valori di Pricing")
                plt.xlabel("Valore")
                plt.ylabel("Frequenza")
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=100)
                plt.close()
                
                # Aggiungi l'immagine al report
                buffer.seek(0)
                img = PILImage.open(buffer)
                imgdata = io.BytesIO()
                img.save(imgdata, format='png')
                imgdata.seek(0)
                image = Image(imgdata, width=450, height=225)
                elements.append(image)
        else:
            elements.append(Paragraph(str(data), styles["Normal"]))
    
    def _format_segmentation_pdf(self, elements, data, styles):
        """Formatta un report di segmentazione dei clienti per PDF."""
        elements.append(Paragraph("REPORT DI SEGMENTAZIONE CLIENTI", styles["Title"]))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(
            "Questo report presenta l'analisi di segmentazione dei clienti, "
            "evidenziando i diversi gruppi identificati e le loro caratteristiche chiave.", 
            styles["Normal"]
        ))
        elements.append(Spacer(1, 12))
        
        if not isinstance(data, dict):
            elements.append(Paragraph("Dati di segmentazione non validi", styles["Normal"]))
            return
        
        # Sezione per fasce di reddito
        if "income_segments" in data:
            elements.append(Paragraph("Segmentazione per Fasce di Reddito", styles["Subtitle"]))
            income_data = data["income_segments"]
            if income_data and isinstance(income_data, dict):
                table_data = [["Fascia di Reddito", "Numero Clienti"]]
                for segment, count in income_data.items():
                    table_data.append([segment, str(count)])
                
                table = Table(table_data, colWidths=[250, 150])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 12))
                
                # Aggiungi grafico a torta
                self._add_chart_to_pdf(elements, income_data, 
                                     "Distribuzione Clienti per Fascia di Reddito", 
                                     chart_type="pie", styles=styles)
                
        # Sezione per aree geografiche
        if "geographical_segments" in data:
            elements.append(Paragraph("Segmentazione Geografica", styles["Subtitle"]))
            geo_data = data["geographical_segments"]
            if geo_data and isinstance(geo_data, dict):
                table_data = [["Regione", "Numero Clienti"]]
                for region, count in geo_data.items():
                    table_data.append([region, str(count)])
                
                table = Table(table_data, colWidths=[250, 150])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 12))
                
                # Aggiungi grafico a barre per le regioni
                if len(geo_data) > 0:
                    self._add_chart_to_pdf(elements, geo_data, 
                                         "Distribuzione Geografica dei Clienti", 
                                         chart_type="bar", styles=styles)
        
        # Sezione per credit score
        if "credit_score_segments" in data:
            elements.append(Paragraph("Segmentazione per Credit Score", styles["Subtitle"]))
            credit_data = data["credit_score_segments"]
            if credit_data and isinstance(credit_data, dict):
                table_data = [["Fascia Credit Score", "Numero Clienti"]]
                for segment, count in credit_data.items():
                    table_data.append([segment, str(count)])
                
                table = Table(table_data, colWidths=[250, 150])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 12))
                
                # Aggiungi grafico 
                self._add_chart_to_pdf(elements, credit_data, 
                                     "Distribuzione per Credit Score", 
                                     chart_type="pie", styles=styles)
        
        # Sezione per cluster
        if "cluster_profiles" in data:
            elements.append(Paragraph("Profili di Cluster", styles["Subtitle"]))
            cluster_data = data["cluster_profiles"]
            if cluster_data and isinstance(cluster_data, dict) and "error" not in cluster_data:
                # Prepara tabella con profili di cluster
                table_data = [["Cluster", "Numerosità", "Reddito Medio", "Età Media", "Credit Score Medio"]]
                
                for cluster_name, profile in cluster_data.items():
                    if isinstance(profile, dict):
                        row = [
                            cluster_name,
                            str(profile.get('count', 'N/A')),
                            f"{profile.get('avg_income', 'N/A'):,.2f}" if profile.get('avg_income') != 'N/A' else 'N/A',
                            f"{profile.get('avg_age', 'N/A'):.1f}" if profile.get('avg_age') != 'N/A' else 'N/A',
                            f"{profile.get('avg_credit_score', 'N/A'):.1f}" if profile.get('avg_credit_score') != 'N/A' else 'N/A'
                        ]
                        table_data.append(row)
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Allineamento numeri a destra
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # Dimensione del testo
                ]))
                elements.append(table)
                elements.append(Spacer(1, 20))
                
                # Aggiungi una sezione di analisi del clustering
                elements.append(Paragraph("Analisi dei Cluster di Clienti", styles["Subtitle"]))
                
                # Descrizione dei cluster individuati
                elements.append(Paragraph(
                    "Di seguito è riportata un'interpretazione dei cluster identificati in base alle loro caratteristiche distintive:",
                    styles["Normal"]
                ))
                elements.append(Spacer(1, 10))
                
                # Genera descrizioni qualitative dei cluster
                cluster_descriptions = self._generate_cluster_descriptions(cluster_data)
                for cluster_name, description in cluster_descriptions.items():
                    elements.append(Paragraph(f"<b>{cluster_name}:</b> {description}", styles["Normal"]))
                elements.append(Spacer(1, 15))
                
                # Aggiungi raccomandazioni per ciascun segmento
                elements.append(Paragraph("Raccomandazioni Strategiche", styles["Subtitle"]))
                elements.append(Paragraph(
                    "In base all'analisi dei segmenti di clientela, si suggeriscono le seguenti strategie:",
                    styles["Normal"]
                ))
                elements.append(Spacer(1, 10))
                
                # Lista di raccomandazioni
                recommendations = self._generate_segmentation_recommendations(data)
                for i, rec in enumerate(recommendations, 1):
                    elements.append(Paragraph(f"{i}. {rec}", styles["Normal"]))
            else:
                elements.append(Paragraph("Dati di clustering non disponibili o insufficienti", styles["Normal"]))
        
        # Aggiungi una sezione di sintesi conclusiva
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Sintesi e Conclusioni", styles["Subtitle"]))
        
        # Genera automaticamente una sintesi 
        if "income_segments" in data and "credit_score_segments" in data:
            # Identificazione del segmento di reddito principale
            main_income = max(data["income_segments"].items(), key=lambda x: x[1])[0]
            # Identificazione del segmento di credit score principale
            main_credit = max(data["credit_score_segments"].items(), key=lambda x: x[1])[0]
            
            elements.append(Paragraph(
                f"La base clienti è principalmente caratterizzata da clienti con reddito {main_income.lower()} "
                f"e credit score nella fascia '{main_credit.lower()}'. L'analisi di segmentazione evidenzia "
                f"opportunità per strategie mirate di marketing, gestione del rischio e sviluppo prodotti.",
                styles["Normal"]
            ))
        else:
            elements.append(Paragraph(
                "L'analisi di segmentazione fornisce una visione dettagliata della clientela, "
                "utile per lo sviluppo di strategie personalizzate di marketing e gestione del rischio.",
                styles["Normal"]
            ))
    
    def _generate_cluster_descriptions(self, cluster_data):
        """Genera descrizioni qualitative dei cluster di clienti."""
        descriptions = {}
        
        for cluster_name, profile in cluster_data.items():
            if not isinstance(profile, dict):
                continue
                
            # Valori di riferimento per comparazioni qualitative
            avg_income = profile.get('avg_income')
            avg_age = profile.get('avg_age')
            avg_credit_score = profile.get('avg_credit_score') 
            count = profile.get('count', 0)
            
            description = "Segmento di clienti"
            
            # Descrizione dimensione
            if count > 100:
                description += " numeroso"
            elif count < 20:
                description += " di nicchia"
            
            # Descrizione per età
            if avg_age != 'N/A' and isinstance(avg_age, (int, float)):
                if avg_age < 30:
                    description += " giovani"
                elif avg_age > 60:
                    description += " senior"
                else:
                    description += " di età media"
            
            # Descrizione per reddito
            if avg_income != 'N/A' and isinstance(avg_income, (int, float)):
                if avg_income > 70000:
                    description += " ad alto reddito"
                elif avg_income < 30000:
                    description += " a basso reddito"
                else:
                    description += " a reddito medio"
            
            # Descrizione per credit score
            if avg_credit_score != 'N/A' and isinstance(avg_credit_score, (int, float)):
                if avg_credit_score > 720:
                    description += " con eccellente affidabilità creditizia"
                elif avg_credit_score < 600:
                    description += " con profilo di rischio elevato"
            
            descriptions[cluster_name] = description.strip() + "."
            
        return descriptions
        
    def _generate_segmentation_recommendations(self, data):
        """Genera raccomandazioni strategiche basate sui dati di segmentazione."""
        recommendations = []
        
        # Raccomandazioni basate sulle fasce di reddito
        if "income_segments" in data and isinstance(data["income_segments"], dict):
            income_data = data["income_segments"]
            high_income_count = income_data.get('Alto', 0)
            low_income_count = income_data.get('Basso', 0)
            
            if high_income_count > low_income_count:
                recommendations.append("Sviluppare prodotti premium con tassi competitivi per attrarre il segmento alto-spendente.")
            elif low_income_count > 0:
                recommendations.append("Creare pacchetti di prestito accessibili con protezioni aggiuntive per i clienti a basso reddito.")
        
        # Raccomandazioni basate sul credit score
        if "credit_score_segments" in data and isinstance(data["credit_score_segments"], dict):
            credit_data = data["credit_score_segments"]
            high_risk = credit_data.get('Rischio alto', 0)
            excellent = credit_data.get('Eccellente', 0)
            
            if high_risk > 0:
                recommendations.append("Implementare strategie di mitigazione del rischio per i clienti con basso credit score, come programmi di educazione finanziaria.")
            if excellent > 0:
                recommendations.append("Offrire vantaggi esclusivi e tassi preferenziali ai clienti con eccellente storico creditizio.")
        
        # Raccomandazioni basate sulla distribuzione geografica
        if "geographical_segments" in data and isinstance(data["geographical_segments"], dict):
            geo_data = data["geographical_segments"]
            if len(geo_data) > 3:  # Se ci sono diverse regioni
                recommendations.append("Personalizzare le offerte in base alle specificità regionali, considerando le differenze economiche locali.")
                
        # Aggiungi raccomandazioni generali se non ci sono abbastanza dati specifici
        if len(recommendations) < 2:
            recommendations.append("Sviluppare una strategia di marketing personalizzata per ciascun segmento di clientela identificato.")
            recommendations.append("Monitorare l'evoluzione dei segmenti nel tempo per adattare proattivamente le strategie di prodotto.")
        
        return recommendations
    
    def _format_crm_pdf(self, elements, data, styles):
        """Formatta un report sulle performance del CRM per PDF."""
        elements.append(Paragraph("REPORT SULLE PERFORMANCE DEL CRM", styles["Title"]))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(
            "Questo report analizza le performance del sistema CRM, includendo metriche "
            "relative ai clienti, alle interazioni e alla conversione in prestiti.", 
            styles["Normal"]
        ))
        elements.append(Spacer(1, 12))
        
        if not isinstance(data, dict):
            elements.append(Paragraph("Dati CRM non validi", styles["Normal"]))
            return
        
        # Mostra metriche principali
        elements.append(Paragraph("Metriche Principali", styles["Subtitle"]))
        table_data = [["Metrica", "Valore"]]
        
        for key, value in data.items():
            formatted_key = key.replace("_", " ").title()
            if isinstance(value, (int, float)):
                formatted_value = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
            else:
                formatted_value = str(value)
            table_data.append([formatted_key, formatted_value])
        
        table = Table(table_data, colWidths=[250, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Aggiungi un grafico per visualizzare le metriche
        if "Total Clients" in data and "Average Interactions per Client" in data and "Average Loans per Client" in data:
            chart_data = {
                "Clienti": data["Total Clients"],
                "Interazioni per cliente": data["Average Interactions per Client"] * data["Total Clients"],
                "Prestiti per cliente": data["Average Loans per Client"] * data["Total Clients"]
            }
            self._add_chart_to_pdf(elements, chart_data, "Distribuzione Attività CRM", chart_type="bar", styles=styles)
        
        # Aggiungi analisi e raccomandazioni
        elements.append(Paragraph("Analisi delle Performance", styles["Subtitle"]))
        
        avg_interactions = data.get("Average Interactions per Client", 0)
        avg_loans = data.get("Average Loans per Client", 0)
        
        # Calcola il tasso di conversione
        if avg_interactions > 0:
            conversion_rate = (avg_loans / avg_interactions) * 100
            elements.append(Paragraph(
                f"Il tasso di conversione da interazione a prestito è del {conversion_rate:.2f}%, "
                f"con una media di {avg_interactions:.2f} interazioni per cliente e {avg_loans:.2f} prestiti per cliente.",
                styles["Normal"]
            ))
        else:
            elements.append(Paragraph(
                "Non sono disponibili dati sufficienti per calcolare il tasso di conversione.",
                styles["Normal"]
            ))
        
        elements.append(Spacer(1, 12))
        
        # Aggiungi raccomandazioni per migliorare le performance
        elements.append(Paragraph("Raccomandazioni", styles["Subtitle"]))
        
        recommendations = []
        if avg_interactions < 3:
            recommendations.append("Aumentare la frequenza di contatto con i clienti, implementando campagne di follow-up automatizzate.")
        if avg_loans < 1:
            recommendations.append("Rivedere le strategie di cross-selling per migliorare il tasso di conversione.")
        
        # Aggiungi sempre almeno una raccomandazione
        if not recommendations:
            recommendations.append("Mantenere l'attuale strategia CRM, che mostra risultati positivi.")
            recommendations.append("Considerare l'implementazione di un programma di fidelizzazione per premiare i clienti più attivi.")
        
        for i, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(f"{i}. {rec}", styles["Normal"]))
    
    def _format_forecast_pdf(self, elements, data, styles):
        """Formatta un report di previsione dell'Euribor per PDF."""
        elements.append(Paragraph("REPORT DI PREVISIONE DELL'EURIBOR", styles["Title"]))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph(
            "Questo report analizza l'andamento storico dei tassi Euribor e fornisce "
            "una previsione basata su tecniche di analisi delle serie temporali.", 
            styles["Normal"]
        ))
        elements.append(Spacer(1, 12))
        
        if not isinstance(data, pd.DataFrame):
            elements.append(Paragraph("Dati di previsione non validi", styles["Normal"]))
            return
        
        # Statistiche descrittive
        elements.append(Paragraph("Statistiche dei Tassi Euribor", styles["Subtitle"]))
        
        latest_period = data["TIME_PERIOD"].max()
        latest_value = data.loc[data["TIME_PERIOD"] == latest_period, "OBS_VALUE"].values[0]
        avg_value = data["OBS_VALUE"].mean()
        min_value = data["OBS_VALUE"].min()
        max_value = data["OBS_VALUE"].max()
        
        stats_data = [
            ["Statistica", "Valore"],
            ["Ultimo valore osservato", f"{latest_value:.3f}%"],
            ["Media storica", f"{avg_value:.3f}%"],
            ["Valore minimo", f"{min_value:.3f}%"],
            ["Valore massimo", f"{max_value:.3f}%"],
            ["Periodo di osservazione", f"{data['TIME_PERIOD'].min()} - {latest_period}"]
        ]
        
        stats_table = Table(stats_data, colWidths=[250, 150])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Grafico dell'andamento storico e della previsione
        elements.append(Paragraph("Andamento Storico e Previsione", styles["Subtitle"]))
        
        # Crea grafico con matplotlib
        buffer = io.BytesIO()
        plt.figure(figsize=(10, 6))
        
        # Ordina per data per garantire un grafico corretto
        data_sorted = data.sort_values("TIME_PERIOD")
        
        # Converti le date in formato datetime
        data_sorted["TIME_PERIOD"] = pd.to_datetime(data_sorted["TIME_PERIOD"])
        
        # Traccia i valori osservati
        plt.plot(data_sorted["TIME_PERIOD"], data_sorted["OBS_VALUE"], 
                 label="Valori osservati", color="blue", linewidth=2)
        
        # Traccia la media mobile (previsione)
        if "Moving_Avg" in data_sorted.columns:
            plt.plot(data_sorted["TIME_PERIOD"], data_sorted["Moving_Avg"], 
                     label="Media Mobile (previsione)", color="red", linewidth=2, linestyle="--")
        
        plt.title("Andamento Euribor e Previsione")
        plt.xlabel("Periodo")
        plt.ylabel("Tasso (%)")
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(buffer, format="png", dpi=150)
        plt.close()
        
        # Aggiungi il grafico al PDF
        buffer.seek(0)
        img = PILImage.open(buffer)
        imgdata = io.BytesIO()
        img.save(imgdata, format="png")
        imgdata.seek(0)
        image = Image(imgdata, width=450, height=270)
        elements.append(image)
        
        # Tabella dei valori recenti e previsti
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Valori Recenti e Previsione", styles["Subtitle"]))
        
        # Mostra solo gli ultimi 6 mesi e le previsioni future
        recent_data = data_sorted.tail(6)
        
        table_data = [["Periodo", "Valore Osservato", "Valore Previsto (Media Mobile)"]]
        
        for _, row in recent_data.iterrows():
            period = row["TIME_PERIOD"].strftime("%b %Y") if isinstance(row["TIME_PERIOD"], pd.Timestamp) else str(row["TIME_PERIOD"])
            obs_value = f"{row['OBS_VALUE']:.3f}%" if pd.notnull(row["OBS_VALUE"]) else "N/A"
            mov_avg = f"{row['Moving_Avg']:.3f}%" if pd.notnull(row.get("Moving_Avg")) else "N/A"
            
            table_data.append([period, obs_value, mov_avg])
        
        recent_table = Table(table_data)
        recent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]))
        elements.append(recent_table)
        
        # Analisi e implicazioni
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Analisi e Implicazioni", styles["Subtitle"]))
        
        # Calcola la tendenza recente (ultimi 3 mesi)
        recent = data_sorted.tail(3)["OBS_VALUE"].values
        if len(recent) >= 2:
            trend = recent[-1] - recent[0]
            trend_text = "in aumento" if trend > 0 else "in diminuzione" if trend < 0 else "stabile"
            
            elements.append(Paragraph(
                f"L'analisi mostra una tendenza {trend_text} dei tassi Euribor negli ultimi 3 mesi "
                f"(variazione di {abs(trend):.3f}%). Questo andamento suggerisce che ",
                styles["Normal"]
            ))
            
            # Aggiungi considerazioni sulle implicazioni
            if trend > 0.5:
                elements.append(Paragraph(
                    "L'aumento significativo dei tassi potrebbe impattare negativamente sul costo dei prestiti "
                    "a tasso variabile. Si consiglia di valutare strategie di copertura del rischio tasso "
                    "o di proporre ai clienti la conversione a tasso fisso.",
                    styles["Normal"]
                ))
            elif trend < -0.5:
                elements.append(Paragraph(
                    "La diminuzione significativa dei tassi rappresenta un'opportunità per "
                    "il rifinanziamento di prestiti esistenti e per proporre nuovi prodotti a condizioni vantaggiose.",
                    styles["Normal"]
                ))
            else:
                elements.append(Paragraph(
                    "La relativa stabilità dei tassi suggerisce un periodo di bassa volatilità, "
                    "favorevole per una pianificazione più accurata e per l'aggiornamento dei modelli di pricing.",
                    styles["Normal"]
                ))
        else:
            elements.append(Paragraph(
                "Non sono disponibili dati sufficienti per analizzare la tendenza recente.",
                styles["Normal"]
            ))
    
    def _add_chart_to_pdf(self, elements, data, title, chart_type="pie", styles=None):
        """
        Aggiunge un grafico al documento PDF.
        
        Parametri:
          elements: lista degli elementi PDF a cui aggiungere il grafico
          data: dati da visualizzare (dict per pie/bar, dict con array per line)
          title: titolo del grafico
          chart_type: tipo di grafico ('pie', 'bar', 'line')
        """

        if styles is None:
            styles = getSampleStyleSheet()
            if "Subtitle" not in styles:
                styles.add(ParagraphStyle(name='Subtitle', 
                                        fontName='Helvetica-Bold',
                                        fontSize=14,
                                        spaceAfter=10))
 
        if not data:
            return
        
        if chart_type == "pie" and isinstance(data, dict):
            # Crea un grafico a torta usando reportlab
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 100
            pie.y = 25
            pie.width = 180
            pie.height = 180
            pie.data = list(data.values())
            pie.labels = [str(k) for k in data.keys()]
            pie.slices.strokeWidth = 0.5
            
            # Assegna colori diversi alle fette
            colors = [colors.blue, colors.green, colors.red, colors.yellow, 
                      colors.orange, colors.purple, colors.pink, colors.brown]
            for i, _ in enumerate(data):
                pie.slices[i].fillColor = colors[i % len(colors)]
            
            drawing.add(pie)
            
            # Aggiungi una legenda
            drawing.add(Legend(),
                pie.x + pie.width + 10,
                pie.y,
                pie.labels)
            
            elements.append(Paragraph(title, styles["Subtitle"]))
            elements.append(drawing)
            elements.append(Spacer(1, 10))
            
        elif chart_type == "bar" and isinstance(data, dict):
            # Usa matplotlib per un grafico a barre più sofisticato
            buffer = io.BytesIO()
            plt.figure(figsize=(8, 4))
            
            # Ordina i dati per valore decrescente
            sorted_data = {k: v for k, v in sorted(data.items(), key=lambda item: item[1], reverse=True)}
            
            plt.bar(sorted_data.keys(), sorted_data.values(), color='skyblue')
            plt.title(title)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plt.savefig(buffer, format='png', dpi=100)
            plt.close()
            
            buffer.seek(0)
            img = PILImage.open(buffer)
            imgdata = io.BytesIO()
            img.save(imgdata, format='png')
            imgdata.seek(0)
            image = Image(imgdata, width=450, height=225)
            
            elements.append(Paragraph(title, styles["Subtitle"]))
            elements.append(image)
            elements.append(Spacer(1, 10))
            
        elif chart_type == "line" and isinstance(data, dict):
            # Usa matplotlib per un grafico a linee
            buffer = io.BytesIO()
            plt.figure(figsize=(8, 4))
            
            # Supporta sia dict di valori singoli che dict di array
            has_arrays = any(isinstance(v, (list, tuple, np.ndarray)) for v in data.values())
            
            if has_arrays:
                # Se abbiamo array, traccia ogni serie
                x = range(len(next(iter(data.values()))))
                for label, values in data.items():
                    plt.plot(x, values, label=label)
                plt.legend()
            else:
                # Se abbiamo valori singoli, traccia una linea
                plt.plot(list(data.keys()), list(data.values()))
                
            plt.title(title)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            plt.savefig(buffer, format='png', dpi=100)
            plt.close()
            
            buffer.seek(0)
            img = PILImage.open(buffer)
            imgdata = io.BytesIO()
            img.save(imgdata, format='png')
            imgdata.seek(0)
            image = Image(imgdata, width=450, height=225)
            
            elements.append(Paragraph(title, styles["Subtitle"]))
            elements.append(image)
            elements.append(Spacer(1, 10))
