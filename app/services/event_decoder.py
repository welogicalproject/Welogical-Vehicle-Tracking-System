import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.models.device_config import DeviceConfig
from app.models.device_command import DeviceCommand
from app.schemas.vts import VTSPacket

logger = logging.getLogger(__name__)

# Core mapping of VTS Protocol v2.2 transaction identifiers (txn)
TXN_EVENT_MAPPING = {
    "A": ("Vehicle Moving", "Vehicle in normal motion periodic transmission", "Info"),
    "B": ("Overspeed", "Vehicle detected moving at higher speed than set limit periodic transmission", "Critical"),
    "C": ("Speed Normal", "Vehicle speed returned below the configured threshold limit", "Info"),
    "D": ("Speed Limit Exceeded", "Vehicle speed limit exceeded event alert", "Critical"),
    "E": ("Vehicle Stopped", "Vehicle is at halt or not moving periodic transmission", "Info"),
    "F": ("Motion Start", "Vehicle motion start event detected", "Info"),
    "G": ("Motion Stop", "Vehicle motion stop event detected (speed goes to 0)", "Info"),
    "J": ("Ignition Changed", "Vehicle ignition state transition detected", "Warning"),
    "K": ("Device Open", "Device enclosure casing/box open tamper event detected", "Warning"),
    "L": ("Power Changed", "External mains power connected or disconnected transit event", "Warning"),
    "M": ("Harsh Turn", "Vehicle experience a sharp harsh turn event", "Info"),
    "N": ("SOS", "SOS emergency alarm button pressed on tracking hardware", "Critical"),
    "O": ("Digital Input Changed", "Digital input GPIO pin logic level transition detected", "Info"),
    "P": ("Over Acceleration", "Vehicle acceleration rate exceeded safe thresholds", "Critical"),
    "Q": ("Parameter Changed", "Device configuration setting parameter modification acknowledged", "Info"),
    "R": ("Parameter Query", "Diagnostic query for parameter request processed", "Info"),
    "S": ("Harsh Brake", "Vehicle experienced a deceleration force exceeding threshold limits", "Critical"),
    "T": ("Immobilizer Event", "Immobilizer active state transition occurred", "Info"),
    "U": ("GPS Status Event", "GPS satellite tracking or fix status transition occurred", "Info"),
    "V": ("Temperature Alert", "Analog temperature sensor threshold limit violation occurred", "Warning"),
    "W": ("New ID Detected", "New identification tag scanned (RFID, Fingerprint, or iButton)", "Info"),
    "X": ("Geofence Event", "Vehicle entered or exited geofence boundary coordinate limits", "Warning"),
    "Y": ("Trip Event", "Trip activation state button trigger event occurred", "Info"),
    "Z": ("Firmware Update Event", "FOTA firmware override or upgrade process started", "Info"),
}


async def trigger_system_event(
    db: AsyncSession,
    vehicle_id: int,
    txn: str,
    event_type: str,
    description: str,
    severity: str,
    msgid: Optional[int] = None
) -> Optional[Event]:
    """
    Decoupled utility to persist an event with duplicate event protection.
    Uniqueness tuple: (vehicle_id, txn, msgid)
    """
    if msgid is not None:
        # Check for duplicate event
        stmt = select(Event).where(
            Event.vehicle_id == vehicle_id,
            Event.txn == txn,
            Event.msgid == msgid
        )
        res = await db.execute(stmt)
        if res.scalars().first() is not None:
            logger.warning(
                f"[EventDecoder] Duplicate event skipped: vehicle={vehicle_id}, txn={txn}, msgid={msgid}"
            )
            return None

    db_event = Event(
        vehicle_id=vehicle_id,
        txn=txn,
        event_type=event_type,
        description=description,
        severity=severity,
        msgid=msgid
    )
    db.add(db_event)
    await db.flush()
    logger.info(
        f"[EventDecoder] Logged event: vehicle={vehicle_id}, type={event_type}, severity={severity}"
    )
    return db_event


async def decode_and_save_event(
    db: AsyncSession,
    vehicle_id: int,
    packet: VTSPacket
) -> Optional[Event]:
    """
    Ingests a raw VTSPacket, decodes its main transaction status, compares metrics against configurations,
    resolves version mismatches, and persists any triggered events to database.
    """
    txn = packet.info.txn
    msgid = packet.info.msgid
    
    # 1. Decode main transaction packet code
    mapping = TXN_EVENT_MAPPING.get(txn)
    if mapping:
        event_type, description, severity = mapping
        # Handle specialized descriptions based on values
        if txn == "J" and packet.io:
            ign_state = "ON" if packet.io.ign == 1 else "OFF"
            description = f"Vehicle ignition turned {ign_state}"
        elif txn == "L" and packet.pwr:
            pwr_state = "connected" if packet.pwr.main == 1 else "disconnected"
            description = f"External mains supply power {pwr_state}"
            
        await trigger_system_event(
            db,
            vehicle_id=vehicle_id,
            txn=txn,
            event_type=event_type,
            description=description,
            severity=severity,
            msgid=msgid
        )
    else:
        logger.warning(f"[EventDecoder] Unknown transaction reason code '{txn}' in packet from vehicle {vehicle_id}")

    # 2. Check configuration thresholds and version overrides
    try:
        config_stmt = select(DeviceConfig).where(DeviceConfig.vehicle_id == vehicle_id)
        config_res = await db.execute(config_stmt)
        config = config_res.scalars().first()
        
        if config:
            # Firmware Mismatch Alert
            if config.firmware_version and packet.dbg and packet.dbg.ver:
                device_fw = packet.dbg.ver[0] if len(packet.dbg.ver) > 0 else None
                if device_fw and device_fw != config.firmware_version:
                    await trigger_system_event(
                        db,
                        vehicle_id=vehicle_id,
                        txn="Q",
                        event_type="Firmware Mismatch",
                        description=f"Device firmware {device_fw} does not match configured target {config.firmware_version}",
                        severity="Warning",
                        msgid=msgid
                    )

            # Hardware Mismatch Alert
            if config.hardware_version and packet.dbg and packet.dbg.ver:
                device_hw = packet.dbg.ver[1] if len(packet.dbg.ver) > 1 else None
                if device_hw and device_hw != config.hardware_version:
                    await trigger_system_event(
                        db,
                        vehicle_id=vehicle_id,
                        txn="Q",
                        event_type="Hardware Mismatch",
                        description=f"Device hardware {device_hw} does not match configured target {config.hardware_version}",
                        severity="Warning",
                        msgid=msgid
                    )

            # Speed Limit Violation (Overspeeding Alert)
            if config.speed_limit is not None and packet.gps.speed > config.speed_limit:
                # Avoid generating duplicate overspeed alert if packet is already B or D
                if txn not in ("B", "D"):
                    await trigger_system_event(
                        db,
                        vehicle_id=vehicle_id,
                        txn="D",
                        event_type="Overspeed Alert",
                        description=f"Vehicle speed {packet.gps.speed} km/h exceeded configured limit of {config.speed_limit} km/h",
                        severity="Critical",
                        msgid=msgid
                    )
    except Exception as e:
        logger.error(f"[EventDecoder] Error running configuration mismatch checks for vehicle {vehicle_id}: {str(e)}", exc_info=True)

    return None


async def handle_command_execution(db: AsyncSession, command: DeviceCommand) -> None:
    """
    Hook executed when a command shifts state to EXECUTED. Synchronizes configuration
    and registers respective event records.
    """
    vehicle_id = command.vehicle_id
    name = command.command_name.upper()
    val = command.command_value
    
    # 1. Update config if PRD or ESS
    if name in ("PRD", "ESS"):
        try:
            cfg_stmt = select(DeviceConfig).where(DeviceConfig.vehicle_id == vehicle_id)
            cfg_res = await db.execute(cfg_stmt)
            config = cfg_res.scalars().first()
            if not config:
                config = DeviceConfig(vehicle_id=vehicle_id)
                db.add(config)
                
            if name == "PRD":
                config.reporting_interval = int(val) if val else None
            elif name == "ESS":
                config.speed_limit = float(val) if val else None
            
            await db.flush()
        except Exception as e:
            logger.error(f"[EventDecoder] Failed to update device config on command execution: {str(e)}", exc_info=True)

    # 2. Trigger events based on command execution
    if name == "STOPV":
        await trigger_system_event(
            db,
            vehicle_id=vehicle_id,
            txn="T",
            event_type="Immobilizer Event",
            description="Immobilizer active state transition: starter/fuel cut command executed successfully",
            severity="Critical"
        )
    elif name == "STARTV":
        await trigger_system_event(
            db,
            vehicle_id=vehicle_id,
            txn="T",
            event_type="Immobilizer Event",
            description="Immobilizer active state transition: starter/fuel restored command executed successfully",
            severity="Info"
        )
    elif name in ("PRD", "ESS"):
        await trigger_system_event(
            db,
            vehicle_id=vehicle_id,
            txn="Q",
            event_type="Parameter Changed",
            description=f"Device parameter configured: {name} updated to {val}",
            severity="Info"
        )
    elif name == "REBOOT":
        await trigger_system_event(
            db,
            vehicle_id=vehicle_id,
            txn="Q",
            event_type="Parameter Changed",
            description="Device system reboot command executed successfully",
            severity="Info"
        )
    elif name == "RESET":
        await trigger_system_event(
            db,
            vehicle_id=vehicle_id,
            txn="Q",
            event_type="Parameter Changed",
            description="Device factory default reset command executed successfully",
            severity="Warning"
        )
