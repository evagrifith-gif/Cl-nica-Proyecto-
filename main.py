from pacientes import registrar_paciente, listar_pacientes
from citas import agendar_cita, listar_citas

def menu():
    while True:
        print("\n==================================")
        print("  SISTEMA DE CLINICA MEDICA v1.0  ")
        print("==================================")
        print("1. Registrar Paciente")
        print("2. Ver Lista de Pacientes")
        print("3. Agendar Cita Medica")
        print("4. Ver Citas Agendadas")
        print("5. Salir")
        
        opcion = input("Seleccione una opción (1-5): ")
        
        if opcion == "1":
            nombre = input("Nombre completo del paciente: ")
            telefono = input("Teléfono: ")
            historial = input("Historial / Alergias: ")
            registrar_paciente(nombre, telefono, historial)
            
        elif opcion == "2":
            pacientes = listar_pacientes()
            print("\n--- LISTADO DE PACIENTES ---")
            if not pacientes:
                print("No hay pacientes registrados aún.")
            for p in pacientes:
                print(f"ID: {p[0]} | Nombre: {p[1]} | Tel: {p[2]} | Historial: {p[3]}")
                
        elif opcion == "3":
            pacientes = listar_pacientes()
            if not pacientes:
                print("\n⚠️ Debe registrar al menos un paciente antes de agendar una cita.")
                continue
                
            print("\n--- PACIENTES DISPONIBLES ---")
            for p in pacientes:
                print(f"ID: {p[0]} | Nombre: {p[1]}")
                
            try:
                paciente_id = int(input("\nIngrese el ID del paciente para la cita: "))
                fecha = input("Fecha y hora de la cita (Ej: 2026-10-15 10:00): ")
                motivo = input("Motivo de consulta: ")
                agendar_cita(paciente_id, fecha, motivo)
            except ValueError:
                print("\n❌ El ID del paciente debe ser un número entero válido.")
                
        elif opcion == "4":
            citas = listar_citas()
            print("\n--- AGENDA DE CITAS ---")
            if not citas:
                print("No hay citas programadas.")
            for c in citas:
                print(f"Cita #{c[0]} | Paciente: {c[1]} | Fecha: {c[2]} | Motivo: {c[3]}")
                
        elif opcion == "5":
            print("\nSaliendo del sistema...")
            break
        else:
            print("\nOpción no válida. Intente de nuevo.")

if __name__ == "__main__":
    menu()