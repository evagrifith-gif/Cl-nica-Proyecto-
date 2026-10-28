
import tkinter as tk
from tkinter import messagebox

from migracion import preparar_base_de_datos
from login import mostrar_login
from gui import AppClinica
from gui_extra import ModulosExtra
import usuarios as usr


def main():
    preparar_base_de_datos()
    while True:
        usuario = mostrar_login()
        if usuario is None:
            break

        estado = {"cerrar_sesion": False}
        root = tk.Tk()
        app = AppClinica(root)
        root.geometry("1150x720")
        root.minsize(1000, 650)

        def cerrar_sesion():
            estado["cerrar_sesion"] = True
            root.destroy()

        ModulosExtra(app, usuario, cerrar_sesion)

        if usr.usa_password_inicial(usuario):
            root.after(500, lambda: messagebox.showwarning(
                "Seguridad",
                "Está usando la contraseña inicial del administrador.\n"
                "Cámbiela en la pestaña 'Usuarios' (botón 'Cambiar contraseña').",
                parent=root))

        root.mainloop()
        if not estado["cerrar_sesion"]:
            break


if __name__ == "__main__":
    main()
