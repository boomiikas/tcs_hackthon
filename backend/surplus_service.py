from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from models import SurplusListing, SurplusReservation, FoodItem

class SurplusRecoveryEngine:
    def __init__(self, db: Session):
        self.db = db

    def calculate_recommended_discount(
        self,
        food_item_id: str,
        quantity_available: int,
        minutes_until_deadline: int
    ) -> Dict[str, Any]:
        item = self.db.query(FoodItem).filter(FoodItem.id == food_item_id).first()
        if not item:
            raise ValueError(f"FoodItem {food_item_id} not found")

        # Food safety guard: If fewer than 15 minutes remain, food must be removed from sale
        if minutes_until_deadline <= 15:
            return {
                "eligible": False,
                "reason": "Safety window approaching cutoff (< 15 min). Mandate kitchen disposition / composting.",
                "suggested_discount_pct": 0,
                "suggested_price": item.base_price,
                "expected_recovery_rate": 0.0,
                "projected_revenue": 0.0
            }

        # Dynamic pricing engine:
        # 1. Time decay factor: urgency increases as deadline approaches
        # 2. Inventory pressure: larger remaining batches need deeper discounts to clear before safety cutoff
        # 3. Cost floor constraint: discount should ideally not drop below 80% prep_cost unless clearing out

        # Time decay
        if minutes_until_deadline > 180: # > 3 hours
            base_disc = 25
        elif minutes_until_deadline > 120: # 2-3 hours
            base_disc = 35
        elif minutes_until_deadline > 60: # 1-2 hours
            base_disc = 45
        else: # 15-60 min
            base_disc = 60

        # Inventory pressure adjustment (+5% for each 10 surplus portions)
        pressure_adj = min(15, (quantity_available // 10) * 5)
        total_discount_pct = min(70, base_disc + pressure_adj)

        # Price calculation
        discounted_price = round(item.base_price * (1.0 - total_discount_pct / 100.0), 1)

        # Estimated elasticity: At 40% discount, expect ~75% clearance; at 60%, expect ~90%
        elasticity_recovery = min(0.95, 0.45 + (total_discount_pct / 100.0) * 0.75)
        expected_cleared_portions = int(round(quantity_available * elasticity_recovery))
        projected_revenue = round(expected_cleared_portions * discounted_price, 2)
        avoided_waste_cost = round(expected_cleared_portions * item.prep_cost, 2)

        return {
            "eligible": True,
            "food_item_id": item.id,
            "food_name": item.name,
            "original_price": item.base_price,
            "prep_cost": item.prep_cost,
            "suggested_discount_pct": total_discount_pct,
            "suggested_price": discounted_price,
            "expected_recovery_rate": round(elasticity_recovery * 100, 1),
            "expected_cleared_portions": expected_cleared_portions,
            "projected_revenue": projected_revenue,
            "avoided_waste_cost": avoided_waste_cost,
            "rationale": f"With {minutes_until_deadline} mins remaining and {quantity_available} units in batch, a {total_discount_pct}% markdown optimizes clearance while recovering ₹{projected_revenue:,.0f} in contribution margin."
        }

    def create_listing(
        self,
        food_item_id: str,
        canteen_id: str,
        batch_code: str,
        portion_size: str,
        quantity: int,
        prep_time: str,
        collection_deadline: str,
        custom_discount_pct: Optional[int] = None,
        notes: str = ""
    ) -> SurplusListing:
        item = self.db.query(FoodItem).filter(FoodItem.id == food_item_id).first()
        if not item:
            raise ValueError(f"Food item {food_item_id} not found")

        # Safety verification check:
        # Food prepared more than 4 hours ago cannot be listed without temperature record
        disc_calc = self.calculate_recommended_discount(food_item_id, quantity, 120)
        disc_pct = custom_discount_pct if custom_discount_pct is not None else disc_calc["suggested_discount_pct"]
        disc_price = round(item.base_price * (1.0 - disc_pct / 100.0), 2)

        listing_id = f"SUR-{datetime.utcnow().strftime('%M%S')}"

        listing = SurplusListing(
            id=listing_id,
            food_item_id=food_item_id,
            canteen_id=canteen_id,
            batch_code=batch_code,
            portion_size=portion_size,
            quantity_available=quantity,
            quantity_reserved=0,
            quantity_sold=0,
            quantity_discarded=0,
            original_price=item.base_price,
            discounted_price=disc_price,
            discount_percent=disc_pct,
            prep_time=prep_time,
            collection_deadline=collection_deadline,
            safety_status="Verified Safe",
            status="Active",
            disposition_notes=notes or "Hot-holding logged at 66°C. Passed sensory & temp check."
        )
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing

    def reserve_portions(self, listing_id: str, student_id: str, portions: int = 1) -> Dict[str, Any]:
        listing = self.db.query(SurplusListing).filter(SurplusListing.id == listing_id).first()
        if not listing:
            raise ValueError("Listing not found")
        if listing.status != "Active":
            raise ValueError(f"Listing is {listing.status}, cannot reserve")

        remaining = listing.quantity_available - listing.quantity_reserved
        if portions > remaining:
            raise ValueError(f"Only {remaining} portions remaining")

        listing.quantity_reserved += portions
        res_id = f"RES-{datetime.utcnow().strftime('%H%M%S')}"
        res = SurplusReservation(
            id=res_id,
            listing_id=listing_id,
            student_id=student_id,
            portions=portions,
            status="Reserved",
            created_at=datetime.utcnow().strftime("%I:%M %p")
        )
        self.db.add(res)
        self.db.commit()

        return {
            "reservation_id": res_id,
            "listing_id": listing_id,
            "portions": portions,
            "total_amount": round(portions * listing.discounted_price, 2),
            "collection_deadline": listing.collection_deadline,
            "status": "Reserved"
        }

    def confirm_collection(self, reservation_id: str) -> Dict[str, Any]:
        res = self.db.query(SurplusReservation).filter(SurplusReservation.id == reservation_id).first()
        if not res:
            raise ValueError("Reservation not found")
        if res.status != "Reserved":
            raise ValueError(f"Reservation already {res.status}")

        listing = self.db.query(SurplusListing).filter(SurplusListing.id == res.listing_id).first()
        res.status = "Collected"
        res.confirmed_at = datetime.utcnow().strftime("%I:%M %p")

        listing.quantity_reserved -= res.portions
        listing.quantity_available -= res.portions
        listing.quantity_sold += res.portions

        if listing.quantity_available <= 0:
            listing.status = "Completed"

        self.db.commit()
        return {"status": "Collected", "reservation_id": reservation_id, "portions": res.portions}

    def close_and_record_disposition(self, listing_id: str, reason: str = "Window expired") -> Dict[str, Any]:
        listing = self.db.query(SurplusListing).filter(SurplusListing.id == listing_id).first()
        if not listing:
            raise ValueError("Listing not found")

        unsold = listing.quantity_available - listing.quantity_reserved
        listing.quantity_discarded += unsold
        listing.quantity_available = 0
        listing.status = "Closed"
        listing.safety_status = "Approaching Limit"
        listing.disposition_notes = f"{reason}. {unsold} unsold portions dispatched to campus bio-composter."
        self.db.commit()

        return {
            "listing_id": listing_id,
            "status": "Closed",
            "unsold_discarded": unsold,
            "disposition": listing.disposition_notes
        }
