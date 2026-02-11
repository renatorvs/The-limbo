from app.core.database import SessionLocal
# from app.modules.backbone.models import CostCenter

def seed():
    db = SessionLocal()
    print("Seeding database...")
    # Create initial data
    # cost_center = CostCenter(name="Engineering", budget=500000)
    # db.add(cost_center)
    # db.commit()
    db.close()
    print("Database seeded.")

if __name__ == "__main__":
    seed()
