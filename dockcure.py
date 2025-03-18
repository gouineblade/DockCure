import docker
import json
import subprocess
import tkinter as tk
from tkinter import ttk

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Python GUI")

        # Première section : champ de recherche, boutons et tableau
        self.frame_top = tk.Frame(self.root)
        self.frame_top.pack(fill=tk.BOTH, padx=10, pady=10)

        # Search Field
        self.search_label = tk.Label(self.frame_top, text="Search:")
        self.search_label.grid(row=0, column=0, padx=5, pady=5)
        self.search_field = tk.Entry(self.frame_top)
        self.search_field.grid(row=0, column=1, padx=5, pady=5)

        # Boutons "Run" et "Fix"
        self.run_button = tk.Button(self.frame_top, text="Run", command=self.run_action)
        self.run_button.grid(row=0, column=2, padx=5, pady=5)
        self.fix_button = tk.Button(self.frame_top, text="Fix", command=self.fix_action)
        self.fix_button.grid(row=0, column=3, padx=5, pady=5)

        # Tableau avec les entêtes
        self.table_frame = tk.Frame(self.frame_top)
        self.table_frame.grid(row=1, column=0, columnspan=4, pady=10)

        # Colonnes de la table avec la nouvelle colonne "Select"
        self.columns = ("Select", "Package", "Version", "Fixable Version", "CVE", "Security", "Action")
        self.treeview = ttk.Treeview(self.table_frame, columns=self.columns, show="headings")

        # Définir les entêtes
        for col in self.columns:
            self.treeview.heading(col, text=col)

        self.treeview.pack(fill=tk.BOTH, expand=True)

        # Deuxième section : Logs (zone de texte non modifiable)
        self.frame_bottom = tk.Frame(self.root)
        self.frame_bottom.pack(fill=tk.BOTH, padx=10, pady=10)

        self.log_label = tk.Label(self.frame_bottom, text="Logs:")
        self.log_label.pack(pady=5)

        self.log_text = tk.Text(self.frame_bottom, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Pour stocker l'état des cases à cocher
        self.checkbox_states = {}

    def show_logs(self, log_message):
        """Afficher les logs dans la zone de texte"""
        self.log_text.config(state=tk.NORMAL)  # Rendre la zone de texte modifiable temporairement
        self.log_text.insert(tk.END, log_message + "\n")
        self.log_text.yview(tk.END)
        self.log_text.config(state=tk.DISABLED)  # Rendre la zone de texte non modifiable à nouveau

    def run_action(self):
        """Exécute la commande système avec l'input du champ de recherche"""
        search_text = self.search_field.get()
        if search_text:
            self.show_logs(f"Running the action with search text: {search_text}...")
            command = f"grype {search_text} -o json"
            try:
                result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                json_output = result.stdout.decode('utf-8')
                self.process_grype_output(json_output)
            except subprocess.CalledProcessError as e:
                self.show_logs(f"Error executing grype: {e.stderr.decode('utf-8')}")
        else:
            self.show_logs("❌ Please enter a search term.")

    def fix_action(self):
        """Action de correction - à personnaliser"""
        self.show_logs("Fixing the issue...")

    def process_grype_output(self, json_output):
        """Traite les résultats JSON de grype et les affiche dans la table"""
        try:
            results = json.loads(json_output)
            if 'matches' in results:
                for match in results['matches']:
                    package = match.get('artifact', {}).get('name', 'N/A')
                    version = match.get('artifact', {}).get('version', 'N/A')
                    fixable_version = match.get('fixed_by', 'N/A')
                    cve = ", ".join([cve['id'] for cve in match.get('vulnerabilities', [])])
                    security = ", ".join([sec['severity'] for sec in match.get('vulnerabilities', [])])

                    # Ajouter une ligne à la table avec une case à cocher
                    self.add_row_to_table(package, version, fixable_version, cve, security)
            else:
                self.show_logs("No matches found.")
        except json.JSONDecodeError:
            self.show_logs("Error parsing the grype output.")

    def add_row_to_table(self, package, version, fixable_version, cve, security):
        """Ajoute une ligne à la table avec une case à cocher"""
        # Créer une case à cocher
        checkbox_var = tk.BooleanVar()  # Variable pour gérer l'état de la case
        checkbox = tk.Checkbutton(self.treeview, variable=checkbox_var)

        # Ajouter la ligne avec case à cocher dans la Treeview
        item_id = self.treeview.insert("", tk.END, values=("☐", package, version, fixable_version, cve, security, "Action"))
        
        # Ajouter l'état de la case dans le dictionnaire
        self.checkbox_states[item_id] = checkbox_var

        # Placer la case à cocher dans la première colonne
        self.treeview.item(item_id, values=("☐", package, version, fixable_version, cve, security, "Action"))

        # Lier l'événement pour appliquer des actions quand la case est cochée
        checkbox_var.trace_add("write", lambda *args: self.apply_changes(item_id))

    def apply_changes(self, item_id):
        """Appliquer des changements si la case à cocher est activée"""
        checkbox_var = self.checkbox_states[item_id]
        if checkbox_var.get():
            self.show_logs(f"Changes applied for {self.treeview.item(item_id)['values'][1]}")  # Afficher le nom du package
        else:
            self.show_logs(f"Changes removed for {self.treeview.item(item_id)['values'][1]}")

# Créer la fenêtre principale et démarrer l'application
root = tk.Tk()
app = App(root)
root.mainloop()
