# view_employees.py
from app.db.database import SessionLocal
from app.models.employees import Employee

def view_employees():
    db = SessionLocal()
    try:
        employees = db.query(Employee).all()
        if not employees:
            print("No employees found.")
        else:
            for emp in employees:
                print(f"employee_number={emp.employee_number}, name={emp.name}, role={emp.role}")
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    view_employees()
