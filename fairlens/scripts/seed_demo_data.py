import json
import uuid

def seed_demo_data():
    print("Seeding demo datasets for Hackathon presentation...")
    demo_dataset = {
        "dataset_id": str(uuid.uuid4()),
        "name": "Credit Scoring Demo",
        "records": 1000,
        "protected_attributes_expected": ["age", "gender"]
    }
    
    # In a real scenario, this would push to Firestore and GCS
    print(f"Created demo dataset: {json.dumps(demo_dataset, indent=2)}")
    print("Done seeding.")

if __name__ == "__main__":
    seed_demo_data()
