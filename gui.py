import tkinter as tk
from tkinter import ttk, messagebox
from pacientes import registrar_paciente, listar_pacientes
from citas import agendar_cita, listar_citas

class AppClinica:
    def __init__(self, root):
        self.root = root
        self.root.title("Clínica Integral Sanity")
        self.root.geometry("820x620")
        self.root.configure(bg="#F4F6F9")

        # Configurar estilos de Tkinter
        self.setup_styles()

        # Encabezado principal
        header_frame = tk.Frame(self.root, bg="#1E3A8A", height=70)
        header_frame.pack(fill="x", side="top")
        
        titulo_app = tk.Label(
            header_frame, 
            text="🏥 Clínica Integral Sanity", 
            font=("Segoe UI", 18, "bold"), 
            bg="#1E3A8A", 
            fg="white"
        )
        titulo_app.pack(padx=20, pady=18, side="left")

        # Contenedor principal de pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)

        # Declaración de frames para pestañas
        self.tab_reg_paciente = tk.Frame(self.notebook, bg="white")
        self.tab_ver_pacientes = tk.Frame(self.notebook, bg="white")
        self.tab_agendar_cita = tk.Frame(self.notebook, bg="white")
        self.tab_ver_citas = tk.Frame(self.notebook, bg="white")

        self.notebook.add(self.tab_reg_paciente, text=" Registrar Paciente ")
        self.notebook.add(self.tab_ver_pacientes, text=" Expedientes ")
        self.notebook.add(self.tab_agendar_cita, text=" Agendar Cita ")
        self.notebook.add(self.tab_ver_citas, text=" Agenda Médica ")

        # Evento para recargar datos automáticamente al cambiar de pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self.al_cambiar_pestana)

        # Crear vistas
        self.crear_vista_registro_paciente()
        self.crear_vista_lista_pacientes()
        self.crear_vista_agendar_cita()
        self.crear_vista_lista_citas()

        # Cargar datos iniciales
        self.cargar_pacientes_tabla()
        self.cargar_citas_tabla()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook", background="#F4F6F9", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[15, 8], background="#E2E8F0", foreground="#334155")
        style.map("TNotebook.Tab", background=[("selected", "white")], foreground=[("selected", "#1E3A8A")])

        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background="#2563EB", foreground="white", borderwidth=0, padding=8)
        style.map("Primary.TButton", background=[("active", "#1D4ED8")])

        style.configure("Secondary.TButton", font=("Segoe UI", 9, "bold"), background="#E2E8F0", foreground="#0F172A", padding=6)

        style.configure("Treeview", font=("Segoe UI", 10), rowheight=28, background="white", fieldbackground="white", borderwidth=1)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#E2E8F0", foreground="#1E293B")
        style.map("Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", "#1E3A8A")])

    def al_cambiar_pestana(self, event):
        tab_actual = self.notebook.index(self.notebook.select())
        if tab_actual == 1:
            self.cargar_pacientes_tabla()
        elif tab_actual == 3:
            self.cargar_citas_tabla()

    # --- PESTAÑA 1: REGISTRO DE PACIENTES ---
    def crear_vista_registro_paciente(self):
        card = tk.Frame(self.tab_reg_paciente, bg="white", padx=30, pady=30)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Nuevo Paciente", font=("Segoe UI", 14, "bold"), bg="white", fg="#0F172A").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        fields = [("Nombre Completo:", "ent_nombre"), ("Teléfono:", "ent_telefono"), ("Historial / Alergias:", "ent_historial")]
        for i, (label_text, attr_name) in enumerate(fields, start=1):
            tk.Label(card, text=label_text, font=("Segoe UI", 10), bg="white", fg="#475569").grid(row=i, column=0, sticky="w", pady=10)
            entry = ttk.Entry(card, width=35, font=("Segoe UI", 10))
            entry.grid(row=i, column=1, sticky="w", padx=15, pady=10)
            setattr(self, attr_name, entry)

        btn = ttk.Button(card, text="Guardar Registro", style="Primary.TButton", command=self.guardar_paciente)
        btn.grid(row=4, column=1, sticky="w", padx=15, pady=25)

    def guardar_paciente(self):
        nombre = self.ent_nombre.get().strip()
        telefono = self.ent_telefono.get().strip()
        historial = self.ent_historial.get().strip()

        if not nombre:
            messagebox.showwarning("Atención", "Ingrese el nombre del paciente.")
            return

        registrar_paciente(nombre, telefono, historial)
        messagebox.showinfo("Éxito", f"Paciente '{nombre}' registrado correctamente.")
        
        # Limpiar campos
        self.ent_nombre.delete(0, tk.END)
        self.ent_telefono.delete(0, tk.END)
        self.ent_historial.delete(0, tk.END)
        
        # Refrescar tabla de expediente e ir automáticamente a ver el resultado
        self.cargar_pacientes_tabla()

    # --- PESTAÑA 2: EXPEDIENTES (TABLA PACIENTES) ---
    def crear_vista_lista_pacientes(self):
        frame = tk.Frame(self.tab_ver_pacientes, bg="white", padx=15, pady=15)
        frame.pack(fill="both", expand=True)

        # Barra superior con botón
        top_bar = tk.Frame(frame, bg="white")
        top_bar.pack(fill="x", pady=(0, 10))
        
        btn_refresh = ttk.Button(top_bar, text="🔄 Actualizar Lista", style="Secondary.TButton", command=self.cargar_pacientes_tabla)
        btn_refresh.pack(side="right")

        # Contenedor para tabla y scrollbar
        table_container = tk.Frame(frame, bg="white")
        table_container.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_container, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        cols = ("id", "nombre", "telefono", "historial")
        self.tabla_pacientes = ttk.Treeview(
            table_container, 
            columns=cols, 
            show="headings", 
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tabla_pacientes.yview)

        headers = [("id", "ID", 50), ("nombre", "Nombre Paciente", 220), ("telefono", "Teléfono", 120), ("historial", "Historial / Alergias", 300)]
        for col_id, text, width in headers:
            self.tabla_pacientes.heading(col_id, text=text, anchor="w")
            self.tabla_pacientes.column(col_id, width=width, anchor="w", stretch=True)

        self.tabla_pacientes.pack(fill="both", expand=True)

    def cargar_pacientes_tabla(self):
        # 1. Limpiar completamente los registros visuales anteriores
        for item in self.tabla_pacientes.get_children():
            self.tabla_pacientes.delete(item)

        # 2. Obtener datos actualizados desde la base de datos
        pacientes = listar_pacientes()

        # 3. Insertar filas una por una
        if pacientes:
            for p in pacientes:
                # Asegura que cada valor se pase convertido explícitamente a string
                row_values = tuple(str(val) if val is not None else "" for val in p)
                self.tabla_pacientes.insert("", "end", values=row_values)
        
        # 4. Forzar refresco del componente en pantalla
        self.tabla_pacientes.update_idletasks()

    # --- PESTAÑA 3: AGENDAR CITA ---
    def crear_vista_agendar_cita(self):
        card = tk.Frame(self.tab_agendar_cita, bg="white", padx=30, pady=30)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Programar Consulta", font=("Segoe UI", 14, "bold"), bg="white", fg="#0F172A").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        fields = [("ID Paciente:", "ent_cita_paciente_id"), ("Fecha y Hora (AAAA-MM-DD HH:MM):", "ent_cita_fecha"), ("Motivo de Consulta:", "ent_cita_motivo")]
        for i, (label_text, attr_name) in enumerate(fields, start=1):
            tk.Label(card, text=label_text, font=("Segoe UI", 10), bg="white", fg="#475569").grid(row=i, column=0, sticky="w", pady=10)
            entry = ttk.Entry(card, width=35, font=("Segoe UI", 10))
            entry.grid(row=i, column=1, sticky="w", padx=15, pady=10)
            setattr(self, attr_name, entry)

        btn = ttk.Button(card, text="Agendar Cita", style="Primary.TButton", command=self.guardar_cita)
        btn.grid(row=4, column=1, sticky="w", padx=15, pady=25)

    def guardar_cita(self):
        p_id = self.ent_cita_paciente_id.get().strip()
        fecha = self.ent_cita_fecha.get().strip()
        motivo = self.ent_cita_motivo.get().strip()

        if not p_id or not fecha or not motivo:
            messagebox.showwarning("Atención", "Complete todos los campos para agendar.")
            return

        try:
            agendar_cita(int(p_id), fecha, motivo)
            messagebox.showinfo("Éxito", "Cita agendada correctamente.")
            self.ent_cita_paciente_id.delete(0, tk.END)
            self.ent_cita_fecha.delete(0, tk.END)
            self.ent_cita_motivo.delete(0, tk.END)
            self.cargar_citas_tabla()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agendar la cita: {e}")

    # --- PESTAÑA 4: AGENDA MÉDICA (TABLA CITAS) ---
    def crear_vista_lista_citas(self):
        frame = tk.Frame(self.tab_ver_citas, bg="white", padx=15, pady=15)
        frame.pack(fill="both", expand=True)

        top_bar = tk.Frame(frame, bg="white")
        top_bar.pack(fill="x", pady=(0, 10))
        
        btn_refresh = ttk.Button(top_bar, text="🔄 Actualizar Agenda", style="Secondary.TButton", command=self.cargar_citas_tabla)
        btn_refresh.pack(side="right")

        table_container = tk.Frame(frame, bg="white")
        table_container.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_container, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        cols = ("id", "paciente", "fecha", "motivo")
        self.tabla_citas = ttk.Treeview(
            table_container, 
            columns=cols, 
            show="headings", 
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tabla_citas.yview)

        headers = [("id", "Cita #", 60), ("paciente", "Paciente", 220), ("fecha", "Fecha y Hora", 150), ("motivo", "Motivo de Consulta", 260)]
        for col_id, text, width in headers:
            self.tabla_citas.heading(col_id, text=text, anchor="w")
            self.tabla_citas.column(col_id, width=width, anchor="w", stretch=True)

        self.tabla_citas.pack(fill="both", expand=True)

    def cargar_citas_tabla(self):
        for item in self.tabla_citas.get_children():
            self.tabla_citas.delete(item)

        citas = listar_citas()
        if citas:
            for c in citas:
                row_values = tuple(str(val) if val is not None else "" for val in c)
                self.tabla_citas.insert("", "end", values=row_values)
                
        self.tabla_citas.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppClinica(root)
    root.mainloop()