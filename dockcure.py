import docker
import json
import subprocess

import tkinter as tk
from tkinter import ttk

# Fonction pour afficher les logs
def show_logs(log_message):
    log_text.insert(tk.END, log_message + "\n")
    log_text.yview(tk.END)

# Fonction pour exécuter l'action "Run"
def run_action():
    show_logs("Running the action...")

# Fonction pour exécuter l'action "Fix"
def fix_action():
    show_logs("Fixing the issue...")

# Créer la fenêtre principale
root = tk.Tk()
root.title("Python GUI")

# Première section : champ de recherche, boutons et tableau
frame_top = tk.Frame(root)
frame_top.pack(fill=tk.BOTH, padx=10, pady=10)

# Search Field
search_label = tk.Label(frame_top, text="Search:")
search_label.grid(row=0, column=0, padx=5, pady=5)
search_field = tk.Entry(frame_top)
search_field.grid(row=0, column=1, padx=5, pady=5)

# Boutons "Run" et "Fix"
run_button = tk.Button(frame_top, text="Run", command=run_action)
run_button.grid(row=0, column=2, padx=5, pady=5)
fix_button = tk.Button(frame_top, text="Fix", command=fix_action)
fix_button.grid(row=0, column=3, padx=5, pady=5)

# Tableau avec les entêtes
table_frame = tk.Frame(frame_top)
table_frame.grid(row=1, column=0, columnspan=4, pady=10)

# Colonnes de la table
columns = ("", "Package", "Version", "Fixable Version", "CVE", "Security", "Action")
treeview = ttk.Treeview(table_frame, columns=columns, show="headings")

# Définir les entêtes
for col in columns:
    treeview.heading(col, text=col)

treeview.pack(fill=tk.BOTH, expand=True)

# Deuxième section : Logs (zone de texte non modifiable)
frame_bottom = tk.Frame(root)
frame_bottom.pack(fill=tk.BOTH, padx=10, pady=10)

log_label = tk.Label(frame_bottom, text="Logs:")
log_label.pack(pady=5)

log_text = tk.Text(frame_bottom, height=10, wrap=tk.WORD, state=tk.DISABLED)
log_text.pack(fill=tk.BOTH, expand=True)

# Lancer l'interface
root.mainloop()


# if __name__ == "__main__":
#     exit