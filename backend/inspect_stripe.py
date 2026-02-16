import os
import sys
import stripe
import json

# Add current dir to path to find backend module
sys.path.append(os.getcwd())

from backend.app.core.config import settings

def inspect():
    stripe.api_key = settings.STRIPE_SECRET_KEY.get_secret_value()
    
    eid = "evt_1T1QdHGxn2zz5Kew04YNJaAq"
    try:
        event = stripe.Event.retrieve(eid)
        data = event.data.object
        # Print as JSON
        print(json.dumps(data.to_dict(), indent=2))
            
    except Exception as e:
        print(f"Failed to inspect {eid}: {e}")

if __name__ == "__main__":
    inspect()
