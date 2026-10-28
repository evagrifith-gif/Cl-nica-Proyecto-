
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

import pacientes_ext as pex
import medicos as med
import agenda_medica as agenda
import antecedentes as ant
import signos_vitales as sv
import consultas as cons
import usuarios as usr
import respaldo as resp
from citas import eliminar_cita

FUENTE = ("Segoe UI", 10)
TITULO = ("Segoe UI", 13, "bold")


# ---------------------------------------------------------------- utilidades
def _lbl(parent, texto, **kw):
    return tk.Label(parent, text=texto, font=FUENTE, bg="white", fg="#475569", **kw)


def crear_tabla(parent, columnas, altura=8):
    """Crea un Treeview con barra de desplazamiento y lo empaqueta."""
    cont = tk.Frame(parent, bg="white")
    cont.pack(fill="both", expand=True, pady=(8, 0))
    sb = ttk.Scrollbar(cont, orient="vertical")
    sb.pack(side="right", fill="y")
    tabla = ttk.Treeview(cont, columns=[c[0] for c in columnas], show="headings",
                         height=altura, yscrollcommand=sb.set)
    sb.config(command=tabla.yview)
    for cid, texto, ancho in columnas:
        tabla.heading(cid, text=texto, anchor="w")
        tabla.column(cid, width=ancho, anchor="w", stretch=True)
    tabla.pack(fill="both", expand=True)
    return tabla


def llenar(tabla, filas):
    for item in tabla.get_children():
        tabla.delete(item)
    for fila in filas:
        tabla.insert("", "end", values=tuple("" if v is None else v for v in fila))


def _id_seleccionado(tabla, mensaje):
    sel = tabla.selection()
    if not sel:
        messagebox.showwarning("Atención", mensaje)
        return None
    return int(tabla.item(sel[0], "values")[0])


def _desactivar_botones(widget, texto_clave):
    for w in widget.winfo_children():
        if isinstance(w, ttk.Button) and texto_clave in str(w.cget("text")):
            w.state(["disabled"])
        _desactivar_botones(w, texto_clave)


class ModulosExtra:
    def __init__(self, app, usuario, al_cerrar_sesion):
        self.app = app
        self.root = app.root
        self.nb = app.notebook
        self.usuario = usuario
        self.rol = usuario["rol"]
        self.al_cerrar_sesion = al_cerrar_sesion
        self._refrescadores = {}
        self._combos_pacientes = []

        self._aplicar_permisos_base()
        self._barra_estado()

        constructores = [
            ("ficha", " Ficha Completa ", self._tab_ficha),
            ("medicos", " Médicos ", self._tab_medicos),
            ("cita_medico", " Cita con Médico ", self._tab_cita_medico),
            ("historia", " Historia Clínica ", self._tab_historia),
            ("usuarios", " Usuarios ", self._tab_usuarios),
            ("respaldo", " Respaldo ", self._tab_respaldo),
        ]
        for permiso, texto, constructor in constructores:
            if usr.tiene_permiso(self.rol, permiso):
                frame = tk.Frame(self.nb, bg="white")
                self.nb.add(frame, text=texto)
                constructor(frame)

        self.nb.bind("<<NotebookTabChanged>>", self._al_cambiar_tab, add="+")
        self._seleccionar_primera_visible()

    # ------------------------------------------------------------ permisos
    def _aplicar_permisos_base(self):
        a = self.app
        mapa = {
            "base_registro": a.tab_reg_paciente,
            "base_expedientes": a.tab_ver_pacientes,
            "base_cita": a.tab_agendar_cita,
            "base_agenda": a.tab_ver_citas,
        }
        for permiso, frame in mapa.items():
            if not usr.tiene_permiso(self.rol, permiso):
                self.nb.hide(frame)
        if not usr.tiene_permiso(self.rol, "eliminar_paciente"):
            _desactivar_botones(a.tab_ver_pacientes, "Eliminar")
        if not usr.tiene_permiso(self.rol, "cancelar_cita"):
            _desactivar_botones(a.tab_ver_citas, "Cancelar")

    def _seleccionar_primera_visible(self):
        for t in self.nb.tabs():
            if self.nb.tab(t, "state") != "hidden":
                self.nb.select(t)
                return

    def _barra_estado(self):
        barra = tk.Frame(self.root, bg="#E2E8F0")
        barra.pack(side="bottom", fill="x", before=self.nb)
        tk.Label(barra, text=f"👤 {self.usuario['nombre']}  ·  Rol: {self.rol}", font=("Segoe UI", 9, "bold"),
                 bg="#E2E8F0", fg="#1E293B").pack(side="left", padx=15, pady=6)
        ttk.Button(barra, text="Cerrar sesión", style="Secondary.TButton",
                   command=self.al_cerrar_sesion).pack(side="right", padx=15, pady=4)

    def _al_cambiar_tab(self, event):
        try:
            frame = self.nb.nametowidget(self.nb.select())
        except KeyError:
            return
        refrescar = self._refrescadores.get(frame)
        if refrescar:
            refrescar()

    # ------------------------------------------------------------ combos
    def _combo_pacientes(self, parent, ancho=42):
        combo = ttk.Combobox(parent, width=ancho, font=FUENTE)
        combo.bind("<KeyRelease>", lambda e, c=combo: self._filtrar_combo(c))
        self._combos_pacientes.append(combo)
        self._cargar_combo_pacientes(combo)
        return combo

    def _cargar_combo_pacientes(self, combo, filtro=""):
        combo["values"] = [f"{f[0]} - {f[2]}" for f in pex.buscar_pacientes(filtro)]

    def _filtrar_combo(self, combo):
        texto = combo.get().strip()
        if " - " not in texto:
            self._cargar_combo_pacientes(combo, texto)

    def _refrescar_combos_pacientes(self):
        for c in self._combos_pacientes:
            self._cargar_combo_pacientes(c)

    @staticmethod
    def _id_combo(combo):
        try:
            return int(combo.get().strip().split(" - ", 1)[0])
        except ValueError:
            return None

    @staticmethod
    def _cargar_combo_medicos(combo, especialidad=None):
        combo["values"] = [f"{m[0]} - {m[1]} ({m[2]})" for m in med.listar_medicos(especialidad)]

    def _error(self, e):
        if isinstance(e, ValueError):
            messagebox.showwarning("Atención", str(e))
        else:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")

    # =================================================== FICHA COMPLETA
    def _tab_ficha(self, tab):
        cont = tk.Frame(tab, bg="white", padx=15, pady=10)
        cont.pack(fill="both", expand=True)
        tk.Label(cont, text="Ficha completa del paciente", font=TITULO, bg="white", fg="#0F172A").pack(anchor="w")

        form = tk.Frame(cont, bg="white")
        form.pack(fill="x", pady=6)
        izq = [("Nombre completo:", "nombre"), ("Teléfono:", "telefono"), ("Historial / Alergias:", "historial")]
        der = [("DPI (13 dígitos):", "dpi"), ("Fecha nac. (AAAA-MM-DD):", "fecha_nac"), ("Dirección:", "direccion"),
               ("Contacto de emergencia:", "contacto"), ("Tel. de emergencia:", "tel_contacto")]
        self.ficha = {}
        for col, lista in ((0, izq), (2, der)):
            for i, (texto, clave) in enumerate(lista):
                _lbl(form, texto).grid(row=i, column=col, sticky="w", pady=3)
                e = ttk.Entry(form, width=30, font=FUENTE)
                e.grid(row=i, column=col + 1, sticky="w", padx=(8, 25), pady=3)
                self.ficha[clave] = e

        self.var_ficha_info = tk.StringVar(value="Paciente nuevo")
        tk.Label(cont, textvariable=self.var_ficha_info, font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#1E3A8A").pack(anchor="w")

        botones = tk.Frame(cont, bg="white")
        botones.pack(fill="x", pady=6)
        ttk.Button(botones, text="Guardar como nuevo", style="Primary.TButton",
                   command=self._ficha_guardar_nuevo).pack(side="left")
        ttk.Button(botones, text="Actualizar seleccionado", style="Secondary.TButton",
                   command=self._ficha_actualizar).pack(side="left", padx=6)
        ttk.Button(botones, text="Limpiar", style="Secondary.TButton",
                   command=self._ficha_limpiar).pack(side="left")

        busq = tk.Frame(cont, bg="white")
        busq.pack(fill="x", pady=(8, 0))
        _lbl(busq, "🔍 Buscar por nombre, DPI o código (PAC-0001):").pack(side="left")
        self.ficha_buscar = ttk.Entry(busq, width=28)
        self.ficha_buscar.pack(side="left", padx=6)
        self.ficha_buscar.bind("<KeyRelease>", lambda e: self._ficha_cargar_tabla())

        self.tabla_ficha = crear_tabla(cont, [
            ("id", "ID", 50), ("codigo", "Código", 90), ("nombre", "Nombre", 230),
            ("dpi", "DPI", 130), ("fecha", "Fecha nac.", 90), ("edad", "Edad", 50), ("telefono", "Teléfono", 100),
        ], altura=7)
        self.tabla_ficha.bind("<<TreeviewSelect>>", self._ficha_seleccionar)
        self._ficha_id = None
        self._refrescadores[tab] = self._ficha_cargar_tabla
        self._ficha_cargar_tabla()

    def _ficha_valores(self):
        return {k: e.get().strip() for k, e in self.ficha.items()}

    def _ficha_limpiar(self):
        for e in self.ficha.values():
            e.delete(0, tk.END)
        self._ficha_id = None
        self.var_ficha_info.set("Paciente nuevo")

    def _ficha_cargar_tabla(self):
        llenar(self.tabla_ficha, pex.buscar_pacientes(self.ficha_buscar.get()))

    def _ficha_seleccionar(self, event=None):
        pid = None
        sel = self.tabla_ficha.selection()
        if sel:
            pid = int(self.tabla_ficha.item(sel[0], "values")[0])
        d = pex.obtener_paciente(pid) if pid is not None else None
        if not d:
            return
        for clave, entry in self.ficha.items():
            entry.delete(0, tk.END)
            entry.insert(0, d[clave])
        self._ficha_id = pid
        edad = f"{d['edad']} años" if d["edad"] != "" else "sin fecha de nacimiento"
        self.var_ficha_info.set(f"Editando {d['codigo']}  ·  Edad: {edad}")

    def _ficha_guardar_nuevo(self):
        v = self._ficha_valores()
        try:
            pid = pex.registrar_paciente_completo(v["nombre"], v["telefono"], v["historial"], v["dpi"],
                                                  v["fecha_nac"], v["direccion"], v["contacto"], v["tel_contacto"])
        except Exception as e:
            self._error(e)
            return
        messagebox.showinfo("Éxito", f"Paciente registrado con el código {pex.codigo_paciente(pid)}.")
        self._ficha_limpiar()
        self._ficha_cargar_tabla()
        self._refrescar_combos_pacientes()
        self.app.cargar_pacientes_tabla()

    def _ficha_actualizar(self):
        if self._ficha_id is None:
            messagebox.showwarning("Atención", "Seleccione un paciente de la lista para actualizarlo.")
            return
        v = self._ficha_valores()
        try:
            pex.actualizar_paciente_completo(self._ficha_id, v["nombre"], v["telefono"], v["historial"], v["dpi"],
                                             v["fecha_nac"], v["direccion"], v["contacto"], v["tel_contacto"])
        except Exception as e:
            self._error(e)
            return
        messagebox.showinfo("Éxito", "Datos del paciente actualizados.")
        self._ficha_cargar_tabla()
        self._refrescar_combos_pacientes()
        self.app.cargar_pacientes_tabla()
        self.app.cargar_citas_tabla()

    # =================================================== MÉDICOS
    def _tab_medicos(self, tab):
        cont = tk.Frame(tab, bg="white", padx=15, pady=10)
        cont.pack(fill="both", expand=True)
        tk.Label(cont, text="Registro de médicos", font=TITULO, bg="white", fg="#0F172A").pack(anchor="w")
        form = tk.Frame(cont, bg="white")
        form.pack(fill="x", pady=8)

        _lbl(form, "Nombre completo:").grid(row=0, column=0, sticky="w", pady=4)
        self.med_nombre = ttk.Entry(form, width=32, font=FUENTE)
        self.med_nombre.grid(row=0, column=1, padx=(8, 25), pady=4)
        _lbl(form, "Especialidad:").grid(row=0, column=2, sticky="w")
        self.med_esp = ttk.Combobox(form, values=med.ESPECIALIDADES, width=28, font=FUENTE, state="readonly")
        self.med_esp.grid(row=0, column=3, padx=8)
        _lbl(form, "No. de colegiado:").grid(row=1, column=0, sticky="w", pady=4)
        self.med_colegiado = ttk.Entry(form, width=32, font=FUENTE)
        self.med_colegiado.grid(row=1, column=1, padx=(8, 25), pady=4)
        _lbl(form, "Teléfono:").grid(row=1, column=2, sticky="w")
        self.med_tel = ttk.Entry(form, width=30, font=FUENTE)
        self.med_tel.grid(row=1, column=3, padx=8)

        botones = tk.Frame(cont, bg="white")
        botones.pack(fill="x")
        ttk.Button(botones, text="Registrar médico", style="Primary.TButton",
                   command=self._med_guardar).pack(side="left")
        ttk.Button(botones, text="🗑 Eliminar seleccionado", style="Danger.TButton",
                   command=self._med_eliminar).pack(side="right")

        self.tabla_med = crear_tabla(cont, [
            ("id", "ID", 50), ("nombre", "Nombre", 260), ("esp", "Especialidad", 200),
            ("col", "Colegiado", 120), ("tel", "Teléfono", 120),
        ], altura=12)
        self._refrescadores[tab] = self._med_cargar
        self._med_cargar()

    def _med_cargar(self):
        llenar(self.tabla_med, med.listar_medicos())

    def _med_guardar(self):
        try:
            med.registrar_medico(self.med_nombre.get(), self.med_esp.get(),
                                 self.med_colegiado.get(), self.med_tel.get())
        except Exception as e:
            self._error(e)
            return
        for e in (self.med_nombre, self.med_colegiado, self.med_tel):
            e.delete(0, tk.END)
        self.med_esp.set("")
        self._med_cargar()
        messagebox.showinfo("Éxito", "Médico registrado correctamente.")

    def _med_eliminar(self):
        mid = _id_seleccionado(self.tabla_med, "Seleccione un médico de la lista.")
        if mid is None:
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar al médico seleccionado?"):
            return
        try:
            med.eliminar_medico(mid)
        except Exception as e:
            self._error(e)
            return
        self._med_cargar()

    # =================================================== CITA CON MÉDICO
    def _tab_cita_medico(self, tab):
        cont = tk.Frame(tab, bg="white", padx=15, pady=10)
        cont.pack(fill="both", expand=True)
        tk.Label(cont, text="Programar cita con médico", font=TITULO, bg="white", fg="#0F172A").pack(anchor="w")
        form = tk.Frame(cont, bg="white")
        form.pack(fill="x", pady=8)

        _lbl(form, "Paciente:").grid(row=0, column=0, sticky="w", pady=4)
        self.cm_paciente = self._combo_pacientes(form)
        self.cm_paciente.grid(row=0, column=1, padx=(8, 25), pady=4, sticky="w")
        _lbl(form, "Especialidad:").grid(row=0, column=2, sticky="w")
        self.cm_esp = ttk.Combobox(form, values=["Todas"] + med.ESPECIALIDADES, state="readonly", width=26, font=FUENTE)
        self.cm_esp.set("Todas")
        self.cm_esp.grid(row=0, column=3, padx=8, sticky="w")
        self.cm_esp.bind("<<ComboboxSelected>>", lambda e: self._cm_filtrar_medicos())

        _lbl(form, "Médico:").grid(row=1, column=0, sticky="w", pady=4)
        self.cm_medico = ttk.Combobox(form, width=42, state="readonly", font=FUENTE)
        self.cm_medico.grid(row=1, column=1, padx=(8, 25), pady=4, sticky="w")
        _lbl(form, "Fecha (AAAA-MM-DD):").grid(row=1, column=2, sticky="w")
        self.cm_fecha = ttk.Entry(form, width=14, font=FUENTE)
        self.cm_fecha.grid(row=1, column=3, padx=8, sticky="w")

        _lbl(form, "Motivo:").grid(row=2, column=0, sticky="w", pady=4)
        self.cm_motivo = ttk.Entry(form, width=45, font=FUENTE)
        self.cm_motivo.grid(row=2, column=1, padx=(8, 25), pady=4, sticky="w")
        _lbl(form, "Hora (HH:MM):").grid(row=2, column=2, sticky="w")
        self.cm_hora = ttk.Entry(form, width=14, font=FUENTE)
        self.cm_hora.grid(row=2, column=3, padx=8, sticky="w")

        botones = tk.Frame(cont, bg="white")
        botones.pack(fill="x")
        ttk.Button(botones, text="Agendar cita", style="Primary.TButton",
                   command=self._cm_agendar).pack(side="left")
        ttk.Button(botones, text="🔄 Actualizar", style="Secondary.TButton",
                   command=self._cm_cargar).pack(side="left", padx=6)
        btn_cancelar = ttk.Button(botones, text="🗑 Cancelar cita", style="Danger.TButton",
                                  command=self._cm_cancelar)
        btn_cancelar.pack(side="right")
        if not usr.tiene_permiso(self.rol, "cancelar_cita"):
            btn_cancelar.state(["disabled"])

        self.tabla_cm = crear_tabla(cont, [
            ("id", "Cita #", 55), ("paciente", "Paciente", 170), ("medico", "Médico", 160),
            ("esp", "Especialidad", 130), ("fecha", "Fecha y hora", 120), ("motivo", "Motivo", 180),
            ("estado", "Estado", 80),
        ], altura=8)
        self._refrescadores[tab] = self._cm_refrescar
        self._cm_filtrar_medicos()
        self._cm_cargar()

    def _cm_refrescar(self):
        self._refrescar_combos_pacientes()
        self._cm_filtrar_medicos()
        self._cm_cargar()

    def _cm_filtrar_medicos(self):
        self.cm_medico.set("")
        self._cargar_combo_medicos(self.cm_medico, self.cm_esp.get())

    def _cm_cargar(self):
        llenar(self.tabla_cm, agenda.listar_agenda_detallada())

    def _cm_agendar(self):
        pid = self._id_combo(self.cm_paciente)
        mid = self._id_combo(self.cm_medico)
        if pid is None or mid is None:
            messagebox.showwarning("Atención", "Seleccione el paciente y el médico de las listas.")
            return
        fecha_hora = f"{self.cm_fecha.get().strip()} {self.cm_hora.get().strip()}"
        try:
            agenda.agendar_cita_con_medico(pid, mid, fecha_hora, self.cm_motivo.get())
        except Exception as e:
            self._error(e)
            return
        messagebox.showinfo("Éxito", "Cita agendada correctamente.")
        for e in (self.cm_fecha, self.cm_hora, self.cm_motivo):
            e.delete(0, tk.END)
        self._cm_cargar()
        self.app.cargar_citas_tabla()

    def _cm_cancelar(self):
        cid = _id_seleccionado(self.tabla_cm, "Seleccione una cita de la lista para cancelar.")
        if cid is None:
            return
        if agenda.estado_cita(cid) == "Atendida":
            messagebox.showwarning("Atención", "No se puede cancelar una cita que ya fue atendida.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Cancelar la cita #{cid}?"):
            return
        try:
            eliminar_cita(cid)
        except Exception as e:
            self._error(e)
            return
        self._cm_cargar()
        self.app.cargar_citas_tabla()

    # =================================================== HISTORIA CLÍNICA
    def _tab_historia(self, tab):
        cont = tk.Frame(tab, bg="white", padx=15, pady=10)
        cont.pack(fill="both", expand=True)
        self.hc_id = None

        top = tk.Frame(cont, bg="white")
        top.pack(fill="x")
        _lbl(top, "Paciente:").pack(side="left")
        self.hc_combo = self._combo_pacientes(top, 48)
        self.hc_combo.pack(side="left", padx=6)
        ttk.Button(top, text="Abrir historia", style="Primary.TButton",
                   command=self._hc_abrir).pack(side="left", padx=6)

        self.var_hc_resumen = tk.StringVar(value="Seleccione un paciente (escriba parte del nombre, DPI o código) y presione 'Abrir historia'.")
        tk.Label(cont, textvariable=self.var_hc_resumen, font=("Segoe UI", 10, "bold"), bg="white",
                 fg="#1E3A8A", wraplength=1050, justify="left").pack(anchor="w", pady=6)

        self.hc_nb = ttk.Notebook(cont)
        self.hc_nb.pack(fill="both", expand=True)
        t_ant = tk.Frame(self.hc_nb, bg="white", padx=10, pady=8)
        t_sv = tk.Frame(self.hc_nb, bg="white", padx=10, pady=8)
        t_con = tk.Frame(self.hc_nb, bg="white", padx=10, pady=8)
        self.hc_nb.add(t_ant, text=" Antecedentes ")
        self.hc_nb.add(t_sv, text=" Signos vitales e IMC ")
        self.hc_nb.add(t_con, text=" Consulta médica ")
        self._hc_antecedentes(t_ant)
        self._hc_signos(t_sv)
        self._hc_consultas(t_con)
        self._refrescadores[tab] = self._hc_refrescar

    def _hc_refrescar(self):
        self._refrescar_combos_pacientes()
        self._cargar_combo_medicos(self.con_medico)

    def _hc_requiere_paciente(self):
        if self.hc_id is None:
            messagebox.showwarning("Atención", "Primero seleccione un paciente y presione 'Abrir historia'.")
        return self.hc_id

    def _hc_abrir(self):
        pid = self._id_combo(self.hc_combo)
        d = pex.obtener_paciente(pid) if pid is not None else None
        if not d:
            messagebox.showwarning("Atención", "Seleccione un paciente válido de la lista.")
            return
        self.hc_id = pid
        edad = f"{d['edad']} años" if d["edad"] != "" else "edad no registrada"
        self.var_hc_resumen.set(
            f"{d['codigo']}  ·  {d['nombre']}  ·  {edad}  ·  DPI: {d['dpi'] or '—'}  ·  "
            f"Alergias/historial: {d['historial'] or '—'}")
        self._ant_cargar()
        self._sv_cargar()
        self._con_cargar()
        self._con_cargar_citas()
        self._cargar_combo_medicos(self.con_medico)

    # ---- antecedentes
    def _hc_antecedentes(self, parent):
        fila = tk.Frame(parent, bg="white")
        fila.pack(fill="x")
        _lbl(fila, "Tipo:").pack(side="left")
        self.ant_tipo = ttk.Combobox(fila, values=ant.TIPOS, state="readonly", width=20, font=FUENTE)
        self.ant_tipo.set(ant.TIPOS[0])
        self.ant_tipo.pack(side="left", padx=6)
        _lbl(fila, "Descripción:").pack(side="left")
        self.ant_desc = ttk.Entry(fila, width=50, font=FUENTE)
        self.ant_desc.pack(side="left", padx=6)
        ttk.Button(fila, text="Agregar", style="Primary.TButton", command=self._ant_agregar).pack(side="left")
        ttk.Button(fila, text="🗑 Eliminar", style="Danger.TButton", command=self._ant_eliminar).pack(side="right")
        self.tabla_ant = crear_tabla(parent, [
            ("id", "ID", 50), ("tipo", "Tipo", 160), ("desc", "Descripción", 520), ("fecha", "Registrado", 130),
        ], altura=8)

    def _ant_cargar(self):
        llenar(self.tabla_ant, ant.listar_antecedentes(self.hc_id))

    def _ant_agregar(self):
        pid = self._hc_requiere_paciente()
        if pid is None:
            return
        try:
            ant.agregar_antecedente(pid, self.ant_tipo.get(), self.ant_desc.get())
        except Exception as e:
            self._error(e)
            return
        self.ant_desc.delete(0, tk.END)
        self._ant_cargar()

    def _ant_eliminar(self):
        aid = _id_seleccionado(self.tabla_ant, "Seleccione un antecedente de la lista.")
        if aid is not None and messagebox.askyesno("Confirmar", "¿Eliminar este antecedente?"):
            ant.eliminar_antecedente(aid)
            self._ant_cargar()

    # ---- signos vitales
    def _hc_signos(self, parent):
        form = tk.Frame(parent, bg="white")
        form.pack(fill="x")
        campos = [("Peso (kg):", "peso"), ("Talla (cm):", "talla"), ("Presión (120/80):", "presion"),
                  ("Frec. cardíaca (lpm):", "fc"), ("Temperatura (°C):", "temp"), ("Saturación O₂ (%):", "sat")]
        self.sv_e = {}
        for i, (texto, clave) in enumerate(campos):
            fila, col = divmod(i, 3)
            _lbl(form, texto).grid(row=fila, column=col * 2, sticky="w", pady=4)
            e = ttk.Entry(form, width=12, font=FUENTE)
            e.grid(row=fila, column=col * 2 + 1, padx=(6, 22), pady=4, sticky="w")
            self.sv_e[clave] = e
        self.sv_e["peso"].bind("<KeyRelease>", lambda e: self._sv_imc_vivo())
        self.sv_e["talla"].bind("<KeyRelease>", lambda e: self._sv_imc_vivo())

        fila = tk.Frame(parent, bg="white")
        fila.pack(fill="x", pady=4)
        self.var_imc = tk.StringVar(value="IMC: —")
        tk.Label(fila, textvariable=self.var_imc, font=("Segoe UI", 11, "bold"), bg="white", fg="#047857").pack(side="left")
        ttk.Button(fila, text="Registrar signos", style="Primary.TButton", command=self._sv_guardar).pack(side="left", padx=15)
        ttk.Button(fila, text="🗑 Eliminar", style="Danger.TButton", command=self._sv_eliminar).pack(side="right")
        self.tabla_sv = crear_tabla(parent, [
            ("id", "ID", 40), ("fecha", "Fecha", 110), ("peso", "Peso", 55), ("talla", "Talla", 55),
            ("imc", "IMC", 55), ("clas", "Clasificación", 90), ("pa", "Presión", 70),
            ("fc", "FC", 45), ("temp", "Temp.", 55), ("sat", "SatO₂", 55),
        ], altura=6)

    def _sv_imc_vivo(self):
        try:
            imc = sv.calcular_imc(float(self.sv_e["peso"].get().replace(",", ".")),
                                  float(self.sv_e["talla"].get().replace(",", ".")))
        except ValueError:
            imc = None
        self.var_imc.set(f"IMC: {imc} ({sv.clasificar_imc(imc)})" if imc else "IMC: —")

    def _sv_cargar(self):
        llenar(self.tabla_sv, sv.listar_signos(self.hc_id))

    def _sv_guardar(self):
        pid = self._hc_requiere_paciente()
        if pid is None:
            return
        v = {k: e.get() for k, e in self.sv_e.items()}
        try:
            sv.registrar_signos(pid, v["peso"], v["talla"], v["presion"], v["fc"], v["temp"], v["sat"])
        except Exception as e:
            self._error(e)
            return
        for e in self.sv_e.values():
            e.delete(0, tk.END)
        self.var_imc.set("IMC: —")
        self._sv_cargar()

    def _sv_eliminar(self):
        rid = _id_seleccionado(self.tabla_sv, "Seleccione un registro de la lista.")
        if rid is not None and messagebox.askyesno("Confirmar", "¿Eliminar este registro de signos vitales?"):
            sv.eliminar_signos(rid)
            self._sv_cargar()

    # ---- consulta médica
    def _hc_consultas(self, parent):
        izq = tk.Frame(parent, bg="white")
        izq.pack(side="left", fill="y", padx=(0, 15))
        der = tk.Frame(parent, bg="white")
        der.pack(side="left", fill="both", expand=True)

        _lbl(izq, "Cita (opcional):").grid(row=0, column=0, sticky="w", pady=3)
        self.con_cita = ttk.Combobox(izq, width=36, state="readonly", font=FUENTE)
        self.con_cita.grid(row=0, column=1, pady=3, padx=6)
        _lbl(izq, "Médico:").grid(row=1, column=0, sticky="w", pady=3)
        self.con_medico = ttk.Combobox(izq, width=36, state="readonly", font=FUENTE)
        self.con_medico.grid(row=1, column=1, pady=3, padx=6)
        _lbl(izq, "Diagnóstico:").grid(row=2, column=0, sticky="w", pady=3)
        self.con_diag = ttk.Entry(izq, width=38, font=FUENTE)
        self.con_diag.grid(row=2, column=1, pady=3, padx=6)
        _lbl(izq, "Tratamiento:").grid(row=3, column=0, sticky="w", pady=3)
        self.con_trat = ttk.Entry(izq, width=38, font=FUENTE)
        self.con_trat.grid(row=3, column=1, pady=3, padx=6)
        _lbl(izq, "Receta:").grid(row=4, column=0, sticky="nw", pady=3)
        self.con_receta = tk.Text(izq, width=38, height=4, font=FUENTE, relief="solid", borderwidth=1)
        self.con_receta.grid(row=4, column=1, pady=3, padx=6)
        _lbl(izq, "Observaciones:").grid(row=5, column=0, sticky="w", pady=3)
        self.con_obs = ttk.Entry(izq, width=38, font=FUENTE)
        self.con_obs.grid(row=5, column=1, pady=3, padx=6)
        ttk.Button(izq, text="Guardar consulta", style="Primary.TButton",
                   command=self._con_guardar).grid(row=6, column=1, sticky="w", padx=6, pady=8)

        self.tabla_con = crear_tabla(der, [
            ("id", "ID", 40), ("fecha", "Fecha", 110), ("medico", "Médico", 150), ("diag", "Diagnóstico", 200),
        ], altura=5)
        self.tabla_con.bind("<<TreeviewSelect>>", self._con_detalle)
        barra = tk.Frame(der, bg="white")
        barra.pack(fill="x", pady=(6, 0))
        ttk.Button(barra, text="Exportar receta (.txt)", style="Secondary.TButton",
                   command=self._con_exportar).pack(side="left")
        self.con_texto = tk.Text(der, height=7, font=("Consolas", 9), relief="solid", borderwidth=1, state="disabled")
        self.con_texto.pack(fill="both", expand=True, pady=(6, 0))
        self._con_citas_ids = {}

    def _con_cargar(self):
        llenar(self.tabla_con, cons.listar_consultas(self.hc_id))
        self._con_mostrar_texto("")

    def _con_cargar_citas(self):
        self._con_citas_ids = {}
        valores = ["(Sin cita)"]
        for cid, fecha, motivo in agenda.citas_pendientes_paciente(self.hc_id):
            etiqueta = f"#{cid} · {fecha} · {motivo}"
            self._con_citas_ids[etiqueta] = cid
            valores.append(etiqueta)
        self.con_cita["values"] = valores
        self.con_cita.set("(Sin cita)")

    def _con_mostrar_texto(self, texto):
        self.con_texto.config(state="normal")
        self.con_texto.delete("1.0", tk.END)
        self.con_texto.insert("1.0", texto)
        self.con_texto.config(state="disabled")

    def _con_detalle(self, event=None):
        sel = self.tabla_con.selection()
        if sel:
            self._con_mostrar_texto(cons.generar_receta_texto(int(self.tabla_con.item(sel[0], "values")[0])))

    def _con_guardar(self):
        pid = self._hc_requiere_paciente()
        if pid is None:
            return
        mid = self._id_combo(self.con_medico)
        if mid is None:
            messagebox.showwarning("Atención", "Seleccione el médico que atiende la consulta.")
            return
        cita_id = self._con_citas_ids.get(self.con_cita.get())
        try:
            cons.registrar_consulta(pid, mid, self.con_diag.get(), self.con_trat.get(),
                                    self.con_receta.get("1.0", tk.END), self.con_obs.get(), cita_id)
        except Exception as e:
            self._error(e)
            return
        messagebox.showinfo("Éxito", "Consulta registrada correctamente.")
        self.con_diag.delete(0, tk.END)
        self.con_trat.delete(0, tk.END)
        self.con_obs.delete(0, tk.END)
        self.con_receta.delete("1.0", tk.END)
        self._con_cargar()
        self._con_cargar_citas()
        self.app.cargar_citas_tabla()

    def _con_exportar(self):
        cid = _id_seleccionado(self.tabla_con, "Seleccione una consulta de la lista.")
        if cid is None:
            return
        ruta = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"receta_{cid}.txt",
                                            filetypes=[("Texto", "*.txt")])
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(cons.generar_receta_texto(cid))
            messagebox.showinfo("Éxito", "Receta exportada correctamente.")

    # =================================================== USUARIOS
    def _tab_usuarios(self, tab):
        cont = tk.Frame(tab, bg="white", padx=15, pady=10)
        cont.pack(fill="both", expand=True)
        tk.Label(cont, text="Usuarios y permisos", font=TITULO, bg="white", fg="#0F172A").pack(anchor="w")
        form = tk.Frame(cont, bg="white")
        form.pack(fill="x", pady=8)

        _lbl(form, "Usuario:").grid(row=0, column=0, sticky="w", pady=4)
        self.us_usuario = ttk.Entry(form, width=22, font=FUENTE)
        self.us_usuario.grid(row=0, column=1, padx=(8, 25))
        _lbl(form, "Nombre completo:").grid(row=0, column=2, sticky="w")
        self.us_nombre = ttk.Entry(form, width=32, font=FUENTE)
        self.us_nombre.grid(row=0, column=3, padx=8)
        _lbl(form, "Rol:").grid(row=1, column=0, sticky="w", pady=4)
        self.us_rol = ttk.Combobox(form, values=usr.ROLES, state="readonly", width=20, font=FUENTE)
        self.us_rol.grid(row=1, column=1, padx=(8, 25))
        _lbl(form, "Contraseña (mín. 6):").grid(row=1, column=2, sticky="w")
        self.us_pass = ttk.Entry(form, width=30, font=FUENTE, show="•")
        self.us_pass.grid(row=1, column=3, padx=8)

        botones = tk.Frame(cont, bg="white")
        botones.pack(fill="x")
        ttk.Button(botones, text="Crear usuario", style="Primary.TButton", command=self._us_crear).pack(side="left")
        ttk.Button(botones, text="Cambiar contraseña", style="Secondary.TButton",
                   command=self._us_cambiar_pass).pack(side="left", padx=6)
        ttk.Button(botones, text="🗑 Eliminar", style="Danger.TButton", command=self._us_eliminar).pack(side="right")

        self.tabla_us = crear_tabla(cont, [
            ("id", "ID", 50), ("usuario", "Usuario", 150), ("nombre", "Nombre", 260),
            ("rol", "Rol", 140), ("estado", "Estado", 90),
        ], altura=10)
        self._refrescadores[tab] = self._us_cargar
        self._us_cargar()

    def _us_cargar(self):
        llenar(self.tabla_us, usr.listar_usuarios())

    def _us_crear(self):
        try:
            usr.crear_usuario(self.us_usuario.get(), self.us_nombre.get(), self.us_rol.get(), self.us_pass.get())
        except Exception as e:
            self._error(e)
            return
        for e in (self.us_usuario, self.us_nombre, self.us_pass):
            e.delete(0, tk.END)
        self.us_rol.set("")
        self._us_cargar()
        messagebox.showinfo("Éxito", "Usuario creado correctamente.")

    def _us_cambiar_pass(self):
        uid = _id_seleccionado(self.tabla_us, "Seleccione un usuario de la lista.")
        if uid is None:
            return
        nueva = simpledialog.askstring("Cambiar contraseña", "Nueva contraseña (mínimo 6 caracteres):",
                                       show="•", parent=self.root)
        if nueva is None:
            return
        try:
            usr.cambiar_password(uid, nueva)
        except Exception as e:
            self._error(e)
            return
        messagebox.showinfo("Éxito", "Contraseña actualizada.")

    def _us_eliminar(self):
        uid = _id_seleccionado(self.tabla_us, "Seleccione un usuario de la lista.")
        if uid is None or not messagebox.askyesno("Confirmar", "¿Eliminar al usuario seleccionado?"):
            return
        try:
            usr.eliminar_usuario(uid, self.usuario["id"])
        except Exception as e:
            self._error(e)
            return
        self._us_cargar()

    # =================================================== RESPALDO
    def _tab_respaldo(self, tab):
        cont = tk.Frame(tab, bg="white", padx=15, pady=10)
        cont.pack(fill="both", expand=True)
        tk.Label(cont, text="Respaldo de datos", font=TITULO, bg="white", fg="#0F172A").pack(anchor="w")
        tk.Label(cont, text=("Se guarda una copia completa de clinica.db (pacientes, citas, médicos, historia clínica y usuarios).\n"
                             f"Carpeta predeterminada: '{resp.CARPETA_RESPALDOS}' junto al programa."),
                 font=FUENTE, bg="white", fg="#475569", justify="left").pack(anchor="w", pady=6)
        botones = tk.Frame(cont, bg="white")
        botones.pack(fill="x")
        ttk.Button(botones, text="Crear respaldo ahora", style="Primary.TButton",
                   command=self._rs_crear).pack(side="left")
        ttk.Button(botones, text="Crear en otra carpeta…", style="Secondary.TButton",
                   command=lambda: self._rs_crear(True)).pack(side="left", padx=6)
        ttk.Button(botones, text="Restaurar desde archivo…", style="Danger.TButton",
                   command=self._rs_restaurar).pack(side="right")
        self.tabla_rs = crear_tabla(cont, [("archivo", "Archivo", 420), ("tam", "Tamaño", 100), ("fecha", "Fecha", 150)],
                                    altura=12)
        self._refrescadores[tab] = self._rs_cargar
        self._rs_cargar()

    def _rs_cargar(self):
        llenar(self.tabla_rs, resp.listar_respaldos())

    def _rs_crear(self, elegir_carpeta=False):
        carpeta = resp.CARPETA_RESPALDOS
        if elegir_carpeta:
            carpeta = filedialog.askdirectory(title="Seleccione la carpeta de destino")
            if not carpeta:
                return
        try:
            ruta = resp.crear_respaldo(carpeta)
        except Exception as e:
            self._error(e)
            return
        self._rs_cargar()
        messagebox.showinfo("Respaldo creado", f"Copia guardada en:\n{os.path.abspath(ruta)}")

    def _rs_restaurar(self):
        ruta = filedialog.askopenfilename(title="Seleccione el respaldo a restaurar",
                                          initialdir=resp.CARPETA_RESPALDOS if os.path.isdir(resp.CARPETA_RESPALDOS) else ".",
                                          filetypes=[("Base de datos SQLite", "*.db")])
        if not ruta:
            return
        if not messagebox.askyesno("Confirmar restauración",
                                   "Se reemplazarán TODOS los datos actuales por los del respaldo.\n"
                                   "Antes se guardará una copia del estado actual.\n\n¿Desea continuar?"):
            return
        try:
            previa = resp.restaurar_respaldo(ruta)
        except Exception as e:
            self._error(e)
            return
        messagebox.showinfo("Restauración completa",
                            f"Datos restaurados.\nCopia previa guardada en:\n{os.path.abspath(previa)}\n\n"
                            "Por seguridad se cerrará la sesión; vuelva a iniciar sesión.")
        self.al_cerrar_sesion()
