from database import engine, Base
import models

# Drop all tables
models.Base.metadata.drop_all(bind=engine)
print("All tables dropped.")
