import os
import sys
import stripe

# Add current dir to path to find backend module
sys.path.append(os.getcwd())

from backend.app.core.config import settings
from backend.app.worker.tasks import process_stripe_webhook

def recovery():
    stripe.api_key = settings.STRIPE_SECRET_KEY.get_secret_value()
    
    event_ids = [
        "evt_1T1QdHGxn2zz5Kew8Dw7O6MW",
        "evt_1T1QdHGxn2zz5Kew5tETzh8K",
        "evt_1T1QdHGxn2zz5Kew04YNJaAq"
    ]
    
    for eid in event_ids:
        print(f"--- Recovering {eid} ---")
        try:
            event = stripe.Event.retrieve(eid)
            # process_stripe_webhook internal logic will handle its own loop
            result = process_stripe_webhook(event.to_dict(), correlation_id="manual_recovery")
            print(f"Result for {eid}: {result}")
        except Exception as e:
            print(f"Failed to recover {eid}: {e}")

if __name__ == "__main__":
    recovery()
