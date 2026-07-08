from app.services.notifications.base import BaseNotificationRule, NotificationContext
from app.services.notifications.dispatcher import (
    BaseDispatcher,
    ConsoleDispatcher,
    EmailDispatcher,
    SMSDispatcher,
    WhatsAppDispatcher,
    WebSocketDispatcher,
)
from app.services.notifications.manager import NotificationManager
from app.services.notifications.rules import (
    OverspeedRule,
    LowFuelRule,
    LowBatteryRule,
    EngineOverheatRule,
    GPSLostRule,
    PowerFailureRule,
    VehicleOfflineRule,
    MaintenanceDueRule,
    RefuelingCompletedRule,
)

def get_notification_manager() -> NotificationManager:
    """
    Factory function instantiating a NotificationManager pre-registered with all
    rules and extensible mock dispatchers.
    """
    manager = NotificationManager()
    
    # Register rules
    manager.register_rule(OverspeedRule())
    manager.register_rule(LowFuelRule())
    manager.register_rule(LowBatteryRule())
    manager.register_rule(EngineOverheatRule())
    manager.register_rule(GPSLostRule())
    manager.register_rule(PowerFailureRule())
    manager.register_rule(VehicleOfflineRule())
    manager.register_rule(MaintenanceDueRule())
    manager.register_rule(RefuelingCompletedRule())
    
    # Register dispatchers
    manager.register_dispatcher(ConsoleDispatcher())
    manager.register_dispatcher(EmailDispatcher())
    manager.register_dispatcher(SMSDispatcher())
    manager.register_dispatcher(WhatsAppDispatcher())
    manager.register_dispatcher(WebSocketDispatcher())
    
    return manager

__all__ = [
    "BaseNotificationRule",
    "NotificationContext",
    "BaseDispatcher",
    "NotificationManager",
    "get_notification_manager",
]
