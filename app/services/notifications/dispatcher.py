import logging

logger = logging.getLogger("vts.notifications")

class BaseDispatcher:
    """
    Abstract interface for downstream delivery integration providers (Email, SMS, WebSockets, WhatsApp).
    """
    name: str = "BaseDispatcher"

    def send(self, title: str, message: str, severity: str, details: dict):
        raise NotImplementedError("Dispatchers must override send().")


class ConsoleDispatcher(BaseDispatcher):
    """
    Logs triggered notification alerts to standard server logs.
    """
    name = "Console"

    def send(self, title: str, message: str, severity: str, details: dict):
        logger.info(f"[DISPATCH -> {self.name}] [{severity.upper()}] {title} - {message}")


class EmailDispatcher(BaseDispatcher):
    name = "Email"

    def send(self, title: str, message: str, severity: str, details: dict):
        # Future SMTP delivery integration point
        logger.debug(f"[DISPATCH -> {self.name} (Extensible)] Email placeholder triggered for '{title}'.")


class SMSDispatcher(BaseDispatcher):
    name = "SMS"

    def send(self, title: str, message: str, severity: str, details: dict):
        # Future SMS Gateway (Twilio, Plivo) integration point
        logger.debug(f"[DISPATCH -> {self.name} (Extensible)] SMS placeholder triggered for '{title}'.")


class WhatsAppDispatcher(BaseDispatcher):
    name = "WhatsApp"

    def send(self, title: str, message: str, severity: str, details: dict):
        # Future Meta Business API integration point
        logger.debug(f"[DISPATCH -> {self.name} (Extensible)] WhatsApp placeholder triggered for '{title}'.")


class WebSocketDispatcher(BaseDispatcher):
    name = "WebSocket"

    def send(self, title: str, message: str, severity: str, details: dict):
        import asyncio
        from app.services.websocket_manager import ws_manager
        payload = {
            "title": title,
            "message": message,
            "severity": severity,
            "details": details
        }
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # Schedule async broadcast in running loop safely
                loop.create_task(ws_manager.broadcast("notifications", payload))
        except RuntimeError:
            pass
