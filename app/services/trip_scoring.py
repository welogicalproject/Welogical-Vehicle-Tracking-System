import logging
from app.config import settings

logger = logging.getLogger(__name__)

def calculate_driving_score(
    overspeed_events_count: int,
    long_idle_events_count: int,
    harsh_braking_count: int = 0,
    harsh_acceleration_count: int = 0
) -> int:
    """
    Calculate driving score based on driving violations and idle metrics.
    Configured settings drive all penalty values.
    """
    score = settings.DRIVING_SCORE_START

    # Penalties
    overspeed_penalty = overspeed_events_count * settings.DRIVING_SCORE_OVERSPEED_PENALTY
    idle_penalty = long_idle_events_count * settings.DRIVING_SCORE_IDLE_PENALTY
    
    # Future placeholder penalties (harsh braking and harsh acceleration are out of scope for Phase 2B, but we support them)
    harsh_braking_penalty = harsh_braking_count * 5
    harsh_acceleration_penalty = harsh_acceleration_count * 5

    total_penalty = overspeed_penalty + idle_penalty + harsh_braking_penalty + harsh_acceleration_penalty
    score -= total_penalty

    # Bound the score
    final_score = max(settings.DRIVING_SCORE_MIN, min(settings.DRIVING_SCORE_START, score))
    
    logger.debug(
        f"Driving Score Calculation: start={settings.DRIVING_SCORE_START}, "
        f"overspeed_events={overspeed_events_count} (penalty={overspeed_penalty}), "
        f"long_idle_events={long_idle_events_count} (penalty={idle_penalty}), "
        f"final_score={final_score}"
    )
    return int(final_score)
