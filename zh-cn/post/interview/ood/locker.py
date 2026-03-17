class Slot:
    def __init__(self, slot_id, l, w, h):
        self.id = slot_id
        self.volume = l * w * h
        self.dims = sorted([l, w, h])
        self.used = False

    def can_fit(self, package):
        p = sorted(package)
        return all(a <= b for a, b in zip(p, self.dims))


class Locker:
    def __init__(self, slots):
        self.slots = sorted(slots, key=lambda x: x.volume)

    def get_slot(self, package):
        for slot in self.slots:
            if not slot.used and slot.can_fit(package):
                slot.used = True
                return slot.id
        return -1