from enum import Enum
class BookingState(Enum):
    PENDING="PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
class SeatStatus(Enum):
    AVAILABLE="AVAILABLE"
    BOOKED="BOOKED"
