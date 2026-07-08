from datetime import date, timedelta
from typing import List
from sqlalchemy import select, and_, func
from app.services.reports.base import BaseReportBuilder, ReportContext
from app.models.vehicle_daily_summary import VehicleDailySummary
from app.models.driver_daily_summary import DriverDailySummary
from app.models.fleet_daily_summary import FleetDailySummary
from app.models.maintenance_summary import MaintenanceSummary
from app.models.event import Event
from app.models.vehicle import Vehicle
from app.models.driver import Driver

class DailyFleetReportBuilder(BaseReportBuilder):
    name = "DailyFleet"
    title = "Daily Fleet Report"

    def build(self, context: ReportContext) -> dict:
        db = context.db
        summaries = db.query(FleetDailySummary).filter(
            FleetDailySummary.date >= context.start_date,
            FleetDailySummary.date <= context.end_date
        ).order_by(FleetDailySummary.date.asc()).all()

        total_dist = 0.0
        total_fuel = 0.0
        total_engine = 0.0
        total_driving = 0.0
        total_idle = 0.0
        max_speed = 0.0
        active_veh_max = 0

        details = []
        for s in summaries:
            total_dist += s.total_distance_km
            total_fuel += s.total_fuel_consumed_l
            total_engine += s.total_engine_hours
            total_driving += s.total_driving_hours
            total_idle += s.total_idle_hours
            max_speed = max(max_speed, s.fleet_max_speed)
            active_veh_max = max(active_veh_max, s.active_vehicles)

            details.append({
                "date": str(s.date),
                "distance_km": s.total_distance_km,
                "fuel_liters": s.total_fuel_consumed_l,
                "engine_hours": s.total_engine_hours,
                "active_vehicles": s.active_vehicles,
            })

        avg_fuel_economy = (total_dist / total_fuel) if total_fuel > 0 else 0.0
        idle_pct = (total_idle / total_engine * 100.0) if total_engine > 0 else 0.0

        recommendations = []
        if idle_pct > 20.0:
            recommendations.append("Fleet idling exceeds 20% of engine runtimes. Implement anti-idling driver coaching.")
        else:
            recommendations.append("Idling ratio is within normal parameters.")
        if avg_fuel_economy > 0.0 and avg_fuel_economy < 8.0:
            recommendations.append("Average economy is low. Advise checking tyre pressures across active assets.")

        return {
            "metadata": {
                "builder": self.name,
                "generated_at": str(date.today()),
            },
            "report_title": self.title,
            "filters": {
                "start_date": str(context.start_date),
                "end_date": str(context.end_date),
            },
            "summary_section": {
                "period": f"{context.start_date} to {context.end_date}",
                "records_found": len(summaries),
            },
            "kpi_section": [
                {"name": "Total Distance", "value": f"{total_dist:.1f} km"},
                {"name": "Fuel Consumed", "value": f"{total_fuel:.1f} L"},
                {"name": "Engine Runtime", "value": f"{total_engine:.1f} hrs"},
                {"name": "Active Assets", "value": str(active_veh_max)},
                {"name": "Avg Fuel Economy", "value": f"{avg_fuel_economy:.2f} km/L"},
                {"name": "Idling Ratio", "value": f"{idle_pct:.1f}%"},
            ],
            "charts_data": {
                "distance_trend": [{"date": d["date"], "value": d["distance_km"]} for d in details],
                "fuel_trend": [{"date": d["date"], "value": d["fuel_liters"]} for d in details],
            },
            "detailed_table": details,
            "recommendations": recommendations,
        }


class VehicleReportBuilder(BaseReportBuilder):
    name = "VehiclePerformance"
    title = "Vehicle Performance Report"

    def build(self, context: ReportContext) -> dict:
        db = context.db
        if not context.vehicle_id:
            raise ValueError("vehicle_id parameter is required for Vehicle Performance Report.")

        veh = db.query(Vehicle).filter_by(id=context.vehicle_id).first()
        veh_name = veh.vehicle_name if veh else f"Vehicle #{context.vehicle_id}"

        summaries = db.query(VehicleDailySummary).filter(
            VehicleDailySummary.vehicle_id == context.vehicle_id,
            VehicleDailySummary.date >= context.start_date,
            VehicleDailySummary.date <= context.end_date
        ).order_by(VehicleDailySummary.date.asc()).all()

        total_dist = 0.0
        total_fuel = 0.0
        total_engine = 0.0
        total_driving = 0.0
        total_idle = 0.0
        max_speed = 0.0

        details = []
        for s in summaries:
            total_dist += s.distance_gps_km
            total_fuel += s.fuel_consumed_liters
            total_engine += s.engine_runtime_hours
            total_driving += s.driving_hours
            total_idle += s.idle_hours
            max_speed = max(max_speed, s.max_speed)

            details.append({
                "date": str(s.date),
                "distance_km": s.distance_gps_km,
                "fuel_liters": s.fuel_consumed_liters,
                "engine_hours": s.engine_runtime_hours,
                "max_speed_kmh": s.max_speed,
            })

        avg_economy = (total_dist / total_fuel) if total_fuel > 0 else 0.0
        idle_pct = (total_idle / total_engine * 100.0) if total_engine > 0 else 0.0

        recommendations = []
        if avg_economy > 0.0 and avg_economy < 10.0:
            recommendations.append(f"Fuel economy ({avg_economy:.1f} km/L) is below target. Inspect filters and spark plugs.")
        if max_speed > 105.0:
            recommendations.append("Speed limit violations recorded. Advise driver on safety limits.")

        return {
            "metadata": {
                "builder": self.name,
                "vehicle_id": context.vehicle_id,
                "vehicle_name": veh_name,
            },
            "report_title": f"{self.title} - {veh_name}",
            "filters": {
                "start_date": str(context.start_date),
                "end_date": str(context.end_date),
            },
            "summary_section": {
                "vehicle": veh_name,
                "days_tracked": len(summaries),
            },
            "kpi_section": [
                {"name": "Distance Driven", "value": f"{total_dist:.1f} km"},
                {"name": "Fuel Burned", "value": f"{total_fuel:.1f} L"},
                {"name": "Engine Runtime", "value": f"{total_engine:.1f} hrs"},
                {"name": "Avg Speed Economy", "value": f"{avg_economy:.2f} km/L"},
                {"name": "Peak Speed", "value": f"{max_speed:.1f} km/h"},
                {"name": "Idling Percentage", "value": f"{idle_pct:.1f}%"},
            ],
            "charts_data": {
                "distance_trend": [{"date": d["date"], "value": d["distance_km"]} for d in details],
            },
            "detailed_table": details,
            "recommendations": recommendations,
        }


class DriverReportBuilder(BaseReportBuilder):
    name = "DriverPerformance"
    title = "Driver Performance Report"

    def build(self, context: ReportContext) -> dict:
        db = context.db
        if not context.driver_id:
            raise ValueError("driver_id parameter is required for Driver Performance Report.")

        drv = db.query(Driver).filter_by(id=context.driver_id).first()
        drv_name = drv.driver_name if drv else f"Driver #{context.driver_id}"

        summaries = db.query(DriverDailySummary).filter(
            DriverDailySummary.driver_id == context.driver_id,
            DriverDailySummary.date >= context.start_date,
            DriverDailySummary.date <= context.end_date
        ).order_by(DriverDailySummary.date.asc()).all()

        total_dist = 0.0
        total_fuel = 0.0
        total_overspeed = 0
        total_harsh_brake = 0
        total_harsh_accel = 0
        total_sharp_turn = 0
        avg_safety = 0.0
        avg_eco = 0.0

        details = []
        for s in summaries:
            total_dist += s.distance_driven_km
            total_fuel += s.fuel_used_l
            total_overspeed += s.overspeed_count
            total_harsh_brake += s.harsh_braking_count
            total_harsh_accel += s.harsh_acceleration_count
            total_sharp_turn += s.sharp_turn_count
            avg_safety += s.safety_score
            avg_eco += s.eco_score

            details.append({
                "date": str(s.date),
                "distance_km": s.distance_driven_km,
                "safety_score": s.safety_score,
                "eco_score": s.eco_score,
                "harsh_brakes": s.harsh_braking_count,
            })

        count = len(summaries)
        avg_safety = (avg_safety / count) if count > 0 else 100.0
        avg_eco = (avg_eco / count) if count > 0 else 100.0

        recommendations = []
        if avg_safety < 85.0:
            recommendations.append("Safety Score is below 85. Focus driver training on overspeed and harsh braking mitigations.")
        else:
            recommendations.append("Safety performance is exemplary. Keep up the high standard!")

        return {
            "metadata": {
                "builder": self.name,
                "driver_id": context.driver_id,
                "driver_name": drv_name,
            },
            "report_title": f"{self.title} - {drv_name}",
            "filters": {
                "start_date": str(context.start_date),
                "end_date": str(context.end_date),
            },
            "summary_section": {
                "driver": drv_name,
                "days_worked": count,
            },
            "kpi_section": [
                {"name": "Avg Safety Score", "value": f"{avg_safety:.1f} / 100"},
                {"name": "Avg Eco Score", "value": f"{avg_eco:.1f} / 100"},
                {"name": "Distance Driven", "value": f"{total_dist:.1f} km"},
                {"name": "Overspeeds", "value": str(total_overspeed)},
                {"name": "Harsh Braking", "value": str(total_harsh_brake)},
                {"name": "Harsh Accel", "value": str(total_harsh_accel)},
            ],
            "charts_data": {
                "score_trend": [{"date": d["date"], "safety": d["safety_score"], "eco": d["eco_score"]} for d in details],
            },
            "detailed_table": details,
            "recommendations": recommendations,
        }


class MaintenanceReportBuilder(BaseReportBuilder):
    name = "Maintenance"
    title = "Maintenance Report"

    def build(self, context: ReportContext) -> dict:
        db = context.db
        query = db.query(MaintenanceSummary)
        if context.vehicle_id:
            query = query.filter(MaintenanceSummary.vehicle_id == context.vehicle_id)
        
        summaries = query.filter(
            MaintenanceSummary.date >= context.start_date,
            MaintenanceSummary.date <= context.end_date
        ).order_by(MaintenanceSummary.date.desc()).all()

        details = []
        due_service_cnt = 0
        avg_oil_life = 0.0

        for s in summaries:
            avg_oil_life += s.oil_life_pct
            if s.remaining_service_distance_km < 1000.0:
                due_service_cnt += 1

            details.append({
                "vehicle_id": s.vehicle_id,
                "date": str(s.date),
                "remaining_service_distance_km": s.remaining_service_distance_km,
                "oil_life_pct": s.oil_life_pct,
                "brake_wear_pct": s.brake_wear_pct,
                "tyre_health_pct": s.tyre_health_pct,
                "battery_health_pct": s.battery_health_pct,
            })

        count = len(summaries)
        avg_oil_life = (avg_oil_life / count) if count > 0 else 100.0

        recommendations = []
        if due_service_cnt > 0:
            recommendations.append(f"{due_service_cnt} vehicles require immediate maintenance service booking.")
        else:
            recommendations.append("All vehicles are within safe operational service limits.")

        return {
            "metadata": {
                "builder": self.name,
                "vehicle_id": context.vehicle_id,
            },
            "report_title": self.title,
            "filters": {
                "start_date": str(context.start_date),
                "end_date": str(context.end_date),
            },
            "summary_section": {
                "records_evaluated": count,
                "service_due_count": due_service_cnt,
            },
            "kpi_section": [
                {"name": "Vehicles Service Due", "value": str(due_service_cnt)},
                {"name": "Avg Oil Life", "value": f"{avg_oil_life:.1f}%"},
            ],
            "charts_data": {
                "oil_life_summary": [{"vehicle_id": d["vehicle_id"], "oil_life": d["oil_life_pct"]} for d in details[:10]],
            },
            "detailed_table": details,
            "recommendations": recommendations,
        }


class HealthReportBuilder(BaseReportBuilder):
    name = "FleetHealth"
    title = "Fleet Health Report"

    def build(self, context: ReportContext) -> dict:
        db = context.db
        summaries = db.query(MaintenanceSummary).filter(
            MaintenanceSummary.date == context.date
        ).all()

        total_health = 0.0
        critical_count = 0
        warning_count = 0

        details = []
        for s in summaries:
            total_health += s.overall_vehicle_health_score
            if s.overall_vehicle_health_score < 70.0:
                critical_count += 1
            elif s.overall_vehicle_health_score < 85.0:
                warning_count += 1

            details.append({
                "vehicle_id": s.vehicle_id,
                "overall_health_score": s.overall_vehicle_health_score,
                "engine_health_index": s.engine_health_index,
                "battery_health_pct": s.battery_health_pct,
                "cooling_system_health": s.cooling_system_health,
            })

        count = len(summaries)
        avg_health = (total_health / count) if count > 0 else 100.0

        recommendations = []
        if critical_count > 0:
            recommendations.append(f"Detected {critical_count} vehicles with overall health below 70%. Schedule garage inspections.")
        else:
            recommendations.append("Fleet health index is within the optimal green band.")

        return {
            "metadata": {
                "builder": self.name,
                "date": str(context.date),
            },
            "report_title": self.title,
            "filters": {
                "date": str(context.date),
            },
            "summary_section": {
                "active_assets_evaluated": count,
                "critical_assets": critical_count,
            },
            "kpi_section": [
                {"name": "Fleet Health Index", "value": f"{avg_health:.1f}%"},
                {"name": "Critical Assets", "value": str(critical_count)},
                {"name": "Warning Assets", "value": str(warning_count)},
            ],
            "charts_data": {
                "health_distribution": [
                    {"name": "Healthy (>85)", "value": count - critical_count - warning_count},
                    {"name": "Warning (70-85)", "value": warning_count},
                    {"name": "Critical (<70)", "value": critical_count},
                ]
            },
            "detailed_table": details,
            "recommendations": recommendations,
        }


class FuelReportBuilder(BaseReportBuilder):
    name = "FuelConsumption"
    title = "Fuel Consumption Report"

    def build(self, context: ReportContext) -> dict:
        db = context.db
        summaries = db.query(VehicleDailySummary).filter(
            VehicleDailySummary.date >= context.start_date,
            VehicleDailySummary.date <= context.end_date
        ).order_by(VehicleDailySummary.date.desc()).all()

        total_distance = 0.0
        total_fuel = 0.0

        details = []
        vehicle_fuel_map = {}

        for s in summaries:
            total_distance += s.distance_gps_km
            total_fuel += s.fuel_consumed_liters
            
            # Map totals per vehicle
            v_id = s.vehicle_id
            if v_id not in vehicle_fuel_map:
                vehicle_fuel_map[v_id] = {"distance": 0.0, "fuel": 0.0}
            vehicle_fuel_map[v_id]["distance"] += s.distance_gps_km
            vehicle_fuel_map[v_id]["fuel"] += s.fuel_consumed_liters

        for v_id, metrics in vehicle_fuel_map.items():
            economy = (metrics["distance"] / metrics["fuel"]) if metrics["fuel"] > 0 else 0.0
            details.append({
                "vehicle_id": v_id,
                "total_distance_km": metrics["distance"],
                "total_fuel_liters": metrics["fuel"],
                "average_economy_kpl": economy,
            })

        avg_fleet_economy = (total_distance / total_fuel) if total_fuel > 0 else 0.0

        recommendations = []
        low_economy_veh = [d["vehicle_id"] for d in details if d["average_economy_kpl"] > 0 and d["average_economy_kpl"] < 8.0]
        if low_economy_veh:
            recommendations.append(f"Vehicles {low_economy_veh} have fuel economy < 8 km/L. Schedule inspections for fuel line or engine efficiency losses.")
        else:
            recommendations.append("All assets exceed the baseline fuel economy standard.")

        return {
            "metadata": {
                "builder": self.name,
            },
            "report_title": self.title,
            "filters": {
                "start_date": str(context.start_date),
                "end_date": str(context.end_date),
            },
            "summary_section": {
                "total_distance_tracked": total_distance,
                "total_fuel_liters": total_fuel,
            },
            "kpi_section": [
                {"name": "Total Fuel Burned", "value": f"{total_fuel:.1f} L"},
                {"name": "Fleet Avg Economy", "value": f"{avg_fleet_economy:.2f} km/L"},
                {"name": "Total Distance", "value": f"{total_distance:.1f} km"},
            ],
            "charts_data": {
                "fuel_burn_ranking": [{"vehicle_id": d["vehicle_id"], "fuel_liters": d["total_fuel_liters"]} for d in details[:10]],
            },
            "detailed_table": details,
            "recommendations": recommendations,
        }


class EventReportBuilder(BaseReportBuilder):
    name = "EventSummary"
    title = "Event Summary Report"

    def build(self, context: ReportContext) -> dict:
        db = context.db
        query = db.query(Event)
        if context.vehicle_id:
            query = query.filter(Event.vehicle_id == context.vehicle_id)

        # Filters dates
        start_dt = datetime_combine_min(context.start_date)
        end_dt = datetime_combine_max(context.end_date)
        
        events = query.filter(
            Event.created_at >= start_dt,
            Event.created_at <= end_dt
        ).order_by(Event.created_at.desc()).all()

        critical_count = 0
        warning_count = 0
        info_count = 0
        details = []

        for e in events:
            if e.severity == "Critical":
                critical_count += 1
            elif e.severity == "Warning":
                warning_count += 1
            else:
                info_count += 1

            details.append({
                "event_id": e.id,
                "vehicle_id": e.vehicle_id,
                "event_type": e.event_type,
                "severity": e.severity,
                "description": e.description,
                "created_at": str(e.created_at),
            })

        recommendations = []
        if critical_count > 5:
            recommendations.append("High volume of Critical events recorded. Action compliance logs.")
        else:
            recommendations.append("System alerts volume is within normal parameters.")

        return {
            "metadata": {
                "builder": self.name,
                "vehicle_id": context.vehicle_id,
            },
            "report_title": self.title,
            "filters": {
                "start_date": str(context.start_date),
                "end_date": str(context.end_date),
            },
            "summary_section": {
                "total_events_found": len(events),
                "critical_alerts": critical_count,
            },
            "kpi_section": [
                {"name": "Total Ingested Events", "value": str(len(events))},
                {"name": "Critical Alerts", "value": str(critical_count)},
                {"name": "Warning Alerts", "value": str(warning_count)},
                {"name": "Information Events", "value": str(info_count)},
            ],
            "charts_data": {
                "event_severity_ratio": [
                    {"name": "Critical", "value": critical_count},
                    {"name": "Warning", "value": warning_count},
                    {"name": "Info", "value": info_count},
                ]
            },
            "detailed_table": details[:100], # Limit response payload for performance
            "recommendations": recommendations,
        }

# Helpers
def datetime_combine_min(d: date):
    from datetime import datetime, time
    return datetime.combine(d, time.min)

def datetime_combine_max(d: date):
    from datetime import datetime, time
    return datetime.combine(d, time.max)
