
import tkinter as tk
from tkinter import ttk, messagebox

import usuarios as usr

MAX_INTENTOS = 3


def mostrar_login():
    resultado = {"usuario": None}
    intentos = {"n": 0}

    root = tk.Tk()
    root.title("Iniciar sesión - Clínica Médica Serenidad")
    root.configure(bg="#F4F6F9")
    root.resizable(False, False)
    ancho, alto = 380, 380
    x = (root.winfo_screenwidth() - ancho) // 2
    y = (root.winfo_screenheight() - alto) // 2
    root.geometry(f"{ancho}x{alto}+{x}+{y}")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background="#2563EB",
                    foreground="white", borderwidth=0, padding=8)
    style.map("Primary.TButton", background=[("active", "#1D4ED8")])

    cab = tk.Frame(root, bg="#1E3A8A", height=70)
    cab.pack(fill="x")
    tk.Label(cab, text="🏥 Clínica Médica Serenidad", font=("Segoe UI", 14, "bold"),
             bg="#1E3A8A", fg="white").pack(pady=20)

    cuerpo = tk.Frame(root, bg="#F4F6F9", padx=40, pady=20)
    cuerpo.pack(fill="both", expand=True)

    tk.Label(cuerpo, text="Usuario:", font=("Segoe UI", 10), bg="#F4F6F9", fg="#475569").pack(anchor="w")
    ent_u = ttk.Entry(cuerpo, font=("Segoe UI", 11))
    ent_u.pack(fill="x", pady=(2, 12))
    tk.Label(cuerpo, text="Contraseña:", font=("Segoe UI", 10), bg="#F4F6F9", fg="#475569").pack(anchor="w")
    ent_p = ttk.Entry(cuerpo, font=("Segoe UI", 11), show="•")
    ent_p.pack(fill="x", pady=(2, 8))

    var_error = tk.StringVar()
    tk.Label(cuerpo, textvariable=var_error, font=("Segoe UI", 9), bg="#F4F6F9", fg="#DC2626").pack(anchor="w")

    def entrar(event=None):
        usuario = usr.autenticar(ent_u.get(), ent_p.get())
        if usuario:
            resultado["usuario"] = usuario
            root.destroy()
            return
        intentos["n"] += 1
        restantes = MAX_INTENTOS - intentos["n"]
        if restantes <= 0:
            messagebox.showerror("Acceso denegado", "Se agotaron los intentos. El programa se cerrará.")
            root.destroy()
            return
        var_error.set(f"Usuario o contraseña incorrectos. Intentos restantes: {restantes}")
        ent_p.delete(0, tk.END)
        ent_p.focus_set()

    ttk.Button(cuerpo, text="Ingresar", style="Primary.TButton", command=entrar).pack(fill="x", pady=(10, 0))
    root.bind("<Return>", entrar)
    ent_u.focus_set()
    root.mainloop()
    return resultado["usuario"]
