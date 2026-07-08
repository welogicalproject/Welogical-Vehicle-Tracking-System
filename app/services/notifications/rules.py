from app.services.notifications.base import BaseNotificationRule, NotificationContext

class OverspeedRule(BaseNotificationRule):
    name = "Overspeed"
    event_type = "Overspeed"
    severity = "Warning"

    def create_notification_payload(self, context: NotificationContext) -> dict:
        return {
            "title": "Overspeeding Alert",
            "message": f"Vehicle ID {context.event.vehicle_id} exceeded speed limits: {context.event.description}"
        }

class LowFuelRule(BaseNotificationRule):
    name = "LowFuel"
    event_type = "Low Fuel"
    severity = "Warning"

    def create_notification_payload(self, context: NotificationContext) -> dict:
        return {
            "title": "Low Fuel Alert",
            "message": f"Vehicle ID {context.event.vehicle_id} fuel reserves are low: {context.event.description}"
        }

class LowBatteryRule(BaseNotificationRule):
    name = "LowBattery"
    event_type = "Low Battery"
    severity = "Warning"

    def create_notification_payload(self, context: NotificationContext) -> dict:
        return {
            "title": "Low Battery Alert",
            "message": f"Vehicle ID {context.event.vehicle_id} voltage dropped below threshold: {context.event.description}"
        }

class EngineOverheatRule(BaseNotificationRule):
    name = "EngineOverheat"
    event_type = "Engine Over Temperature"
    severity = "Critical"

    def create_notification_payload(self, context: NotificationContext) -> dict:
        return {
            "title": "Engine Overheating Alert",
            "message": f"CRITICAL: Vehicle ID {context.event.vehicle_id} cooling coolant temperature reached dangerous levels: {context.event.description}"
        }

class GPSLostRule(BaseNotificationRule):
    name = "GPSLost"
    event_type = "GPS Lost"
    severity = "Warning"

    def create_notification_payload(self, context: NotificationContext) -> dict:
        return {
            "title": "GPS Fix Lost",
            "message": f"Vehicle ID {context.event.vehicle_id} has lost satellite telemetry fix."
        }

class PowerFailureRule(BaseNotificationRule):
    name = "PowerFailure"
    event_type = "Power Failure"
    severity = "Critical"

    def create_notification_payload(self, context: NotificationContext) -> dict:
        return {
            "title": "Power Failure Alert",
            "message": f"CRITICAL: External battery mains disconnected on Vehicle ID {context.event.vehicle_id}."
        }

class VehicleOfflineRule(BaseNotificationRule):
    name = "VehicleOffline"
    event_type = "Vehicle Offline"
    severity = "Warning"

    def create_notification_payload(self, context: NotificationContext) -> dict:
        return {
            "title": "Asset Offline Alert",
            "message": f"Vehicle ID {context.event.vehicle_id} has been offline for over 30 minutes."
        }

class MaintenanceDueRule(BaseNotificationRule):
    name = "MaintenanceDue"
    event_type = "Maintenance Due"
    severity = "Warning"

    def create_notification_payload(self, context: NotificationContext) -> dict:
        return {
            "title": "Maintenance Reminder",
            "message": f"Odometer milestone crossed on Vehicle ID {context.event.vehicle_id}. Routine service recommended."
        }

class RefuelingCompletedRule(BaseNotificationRule):
    name = "RefuelingCompleted"
    event_type = "Refueling Completed"
    severity = "Info"

    def create_notification_payload(self, context: NotificationContext) -> dict:
        return {
            "title": "Refueling Complete",
            "message": f"Vehicle ID {context.event.vehicle_id} refueling sequence concluded successfully."
        }
