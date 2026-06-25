"""
fleet_analyzer.py
=================
Pure-Python analytics layer over the raw fleet API payload.

No API calls, no LLM — receives the dict returned by
combined_report_fleet() and exposes focused query methods.

All public methods return plain dicts / lists that are safe
to JSON-serialize and pass to the response generator.
"""

from collections import Counter, defaultdict
from typing import Optional

from app.utils.logger import logger


# =========================================================
# STATUS CODE MAPPING
# vStatus values from the API
# =========================================================

VSTATUS_MAP = {
    1: "moving",
    2: "idle",
    3: "stopped",
    4: "out_network",
    0: "disconnected",
}

VSTATUS_REVERSE = {v: k for k, v in VSTATUS_MAP.items()}


# =========================================================
# FLEET ANALYZER
# =========================================================

class FleetAnalyzer:

    def __init__(self, fleet_data: dict, vid_to_np: dict = None):
        self.vid_to_np = vid_to_np or {}
        last_records = fleet_data.get("lastRecords") or {}

        self.live_records: list[dict]  = last_records.get("data") or []
        self.overall_count: dict       = last_records.get("overAllCount") or {}

        alerts_section                 = fleet_data.get("alerts") or {}
        self.alerts: list[dict]        = alerts_section.get("results") or []
        self.alerts_total: int         = alerts_section.get("total", 0)

        op = fleet_data.get("operationSummary") or {}
        self.op_rows: list[dict]       = op.get("dataRows") or []
        self.op_totals: dict           = op.get("summary") or {}

        self.vn_to_np = {}
        self.vid_to_driver = {}
        self.np_to_driver = {}
        
        # O(1) Inverted Index for Fleet Status
        self.status_index = {
            "moving": [],
            "idle": [],
            "stopped": [],
            "out_network": [],
            "disconnected": []
        }
        
        for r in self.live_records:
            vn = r.get("vehicleName")
            np = r.get("numberPlate")
            if vn and np:
                self.vn_to_np[vn] = np
                
            vid = r.get("ID")
            driver = r.get("driverName")
            if vid is not None and driver:
                self.vid_to_driver[vid] = driver
            if np and driver:
                self.np_to_driver[np] = driver

            # Calculate and index status
            raw_speed = r.get("speed")
            raw_ign = r.get("ignitionOn")
            v_status = r.get("vStatus")
            
            def is_invalid(val):
                if val is None: return True
                if isinstance(val, str) and val.strip().lower() in ("", "na", "null", "nan"): return True
                return False
                
            valid_metrics = not is_invalid(raw_speed) and not is_invalid(raw_ign)
            speed = 0.0
            ignition = 0
            
            if valid_metrics:
                try:
                    speed = float(raw_speed)
                except (ValueError, TypeError):
                    valid_metrics = False
                    
                if raw_ign in (1, "1", True, "true", "True"):
                    ignition = 1
                elif raw_ign in (0, "0", False, "false", "False"):
                    ignition = 0
                else:
                    try:
                        ignition = int(float(raw_ign))
                    except (ValueError, TypeError):
                        valid_metrics = False
            
            assigned_status = None
            if valid_metrics and speed > 0.0 and ignition == 1:
                assigned_status = "moving"
            elif valid_metrics and ignition == 1 and speed == 0.0:
                assigned_status = "idle"
            elif valid_metrics and ignition == 0 and speed == 0.0:
                assigned_status = "stopped"
            elif v_status == 4:
                assigned_status = "out_network"
            elif v_status == 0:
                assigned_status = "disconnected"
                
            if assigned_status:
                self.status_index[assigned_status].append({
                    "vehicleName": r.get("vehicleName"),
                    "numberPlate": r.get("numberPlate"),
                    "driverName":  _clean_driver(r.get("driverName")),
                    "speed":       speed,
                    "lastUpdated": r.get("lastUpdatedTime"),
                })

        logger.info(
            f"[FLEET ANALYZER] live={len(self.live_records)} "
            f"alerts={len(self.alerts)} op_rows={len(self.op_rows)}"
        )

    # =================================================================
    # SECTION A — Live / Realtime  (lastRecords.data)
    # Use for: current speed, status listing, fleet overview now
    # =================================================================

    def fleet_overview(self) -> dict:
        """Overall fleet snapshot counts — total/moving/idle/stopped/etc."""
        counts = {
            "total": len(self.live_records),
            "moving": len(self.status_index["moving"]),
            "idle": len(self.status_index["idle"]),
            "stopped": len(self.status_index["stopped"]),
            "out_network": len(self.status_index["out_network"]),
            "disconnected": len(self.status_index["disconnected"])
        }
        
        # Fallback to API if we have no live records (edge case)
        if counts["total"] == 0:
            return {
                "total":        self.overall_count.get("total", 0),
                "moving":       self.overall_count.get("moving", 0),
                "idle":         self.overall_count.get("idle", 0),
                "stopped":      self.overall_count.get("stopped", 0),
                "out_network":  self.overall_count.get("outNetwork", 0),
                "disconnected": self.overall_count.get("disconnected", 0),
            }
            
        return counts

    def find_vehicles_by_status(self, status: str) -> list[dict]:
        """List all vehicles matching a live status by checking the inverted index."""
        status = status.lower()
        return self.status_index.get(status, [])

    def fastest_vehicle_now(self) -> dict:
        """Which vehicle has the highest live speed right now?"""
        candidates = [
            r for r in self.live_records
            if isinstance(r.get("speed"), (int, float))
        ]
        if not candidates:
            return {}
        top = max(candidates, key=lambda r: r["speed"])
        return _live_row_summary(top)

    def get_live_metrics_for_fleet(self, metrics: list[str]) -> list[dict]:
        """Extract requested metrics for all vehicles from live_records."""
        result = []
        
        # Mapping from normalized metric names to live_records field names
        metric_map = {
            "speed": ["speed"],
            "fuel_level": ["fuelLevel"],
            "battery": ["batteryLevel"],
            "ignition": ["ignitionOn"],
            "engine_status": ["EngineStatus"],
            "location": ["lat", "lon", "Location"],
            "odometer_reading": ["odometerCurrentReading"],
            "remote_immobilization": ["RemoteImmobilaztion", "RemoteImmobilaztionEnabled"],
            "seatbelt": ["seatBelt", "SeatbeltEnabledIo"],
            "door_open": ["doorOpen"],
            "weight": ["Weight"],
            "engine_temperature": ["engineTemperature"],
            "engine_rpm": ["engineRpm"],
            "mileage": ["mileage"],
            "gsm_signal": ["GSMSignal"],
            "satellites": ["satellites"],
            "camera_status": ["CameraStatus"],
            "camera_imei": ["CameraIMEI"],
            "wasl": ["WaslIdentityNumber"],
            "driver_name": ["driverName"],
            "driver": ["driverName"]
        }
        
        fields_to_extract = []
        for m in metrics:
            fields_to_extract.extend(metric_map.get(m, [m]))
                
        for r in self.live_records:
            vehicle_data = {
                "vehicleName": r.get("vehicleName"),
                "numberPlate": r.get("numberPlate"),
                "driverName": _clean_driver(r.get("driverName")),
                "lastUpdated": r.get("lastUpdatedTime"),
            }
            for field in fields_to_extract:
                vehicle_data[field] = r.get(field)
                    
            result.append(vehicle_data)
                
        return result

    # =================================================================
    # SECTION B — Operation Summary  (operationSummary.dataRows)
    # Use for: distance, idle time, moving time, max speed over a range
    # One row per vehicle per day for date-range queries.
    # =================================================================

    def aggregate_by_vehicle(self, metric: str) -> dict[str, dict]:
        """
        Groups multi-day operationSummary rows by vehicleName,
        accumulating totals and tracking the per-vehicle max.

        Returns a dict keyed by vehicleName:
            {
                "vehicleName": str,
                "driverName":  str,
                "total":       float,
                "max":         float,
                "days":        int
            }
        """
        agg: dict[str, dict] = defaultdict(lambda: {
            "vehicleName": "",
            "driverName": "",
            "groupName": "",
            "total": 0.0,
            "max": -1.0,
            "min": float('inf'),
            "max_date": None,
            "min_date": None,
            "days": 0
        })

        for row in self.op_rows:
            if not row or not isinstance(row, dict):
                continue
                
            vn  = row.get("vehicleName") or ""
            vid = row.get("VehicleID")
            # Try VehicleID map first, then numberPlate, then fallback to vehicleName map
            np  = self.vid_to_np.get(vid) or row.get("numberPlate") or self.vn_to_np.get(vn, vn)
            # Use driver from op_rows if present, otherwise map from live_records
            dn  = row.get("driverName") or self.vid_to_driver.get(vid) or ""
            gn  = row.get("groupName") or ""
            raw = row.get(metric)
            row_date = row.get("Date") or row.get("ReportDate") or row.get("DateString")

            try:
                val = float(raw) if raw is not None else 0.0
            except (TypeError, ValueError):
                val = 0.0

            agg[vn]["vehicleName"] = vn
            agg[vn]["numberPlate"] = np
            agg[vn]["driverName"]  = dn or agg[vn]["driverName"]
            agg[vn]["groupName"]   = gn or agg[vn]["groupName"]
            agg[vn]["total"]      += val
            
            if agg[vn]["max"] < 0 or val > agg[vn]["max"]:
                agg[vn]["max"] = val
                agg[vn]["max_date"] = row_date

            if agg[vn]["min"] == float('inf') or val < agg[vn]["min"]:
                agg[vn]["min"] = val
                agg[vn]["min_date"] = row_date

            agg[vn]["days"]       += 1

        # Fix infinity for vehicles with no rows (though loop prevents that)
        for vn in agg:
            if agg[vn]["min"] == float('inf'):
                agg[vn]["min"] = 0.0

        return dict(agg)

    def top_vehicle_by_metric(
        self,
        metric: str,
        aggregation: str = "maximum",   # "maximum" | "minimum" | "total"
        min_activity: bool = True       # skip zero-activity rows
    ) -> dict:
        """
        Finds the single vehicle that ranks highest/lowest for a metric
        across the requested date range.

        metric       → operationSummary field name, e.g. "maxSpeed",
                       "distance", "idleTime", "movingTime"
        aggregation  → "maximum" (default) or "minimum"
        """
        agg = self.aggregate_by_vehicle(metric)

        if not agg:
            return {}

        rows = list(agg.values())

        if min_activity:
            rows = [r for r in rows if r["total"] > 0 or r["max"] > 0]

        if not rows:
            return {}

        sort_key = "max" if metric == "maxSpeed" else "total"

        if aggregation == "maximum":
            top = max(rows, key=lambda r: r[sort_key])
            date_key = "max_date"
        else:
            top = min(rows, key=lambda r: r[sort_key])
            date_key = "min_date"

        return {
            "vehicleName": top["vehicleName"],
            "numberPlate": top.get("numberPlate", top["vehicleName"]),
            "driverName":  top["driverName"],
            "groupName":   top["groupName"],
            "value":       top[sort_key],
            "date":        top.get(date_key),
            "metric":      metric,
            "days_tracked": top["days"],
        }

    def rank_vehicles_by_metric(
        self,
        metric: str,
        top_n: int = 10,
        descending: bool = True
    ) -> list[dict]:
        """Returns top-N ranked vehicles for a given metric."""
        agg = self.aggregate_by_vehicle(metric)
        sort_key = "max" if metric == "maxSpeed" else "total"

        rows = sorted(
            agg.values(),
            key=lambda r: r[sort_key],
            reverse=descending
        )[:top_n]

        return [
            {
                "rank":        i + 1,
                "vehicleName": r["vehicleName"],
                "numberPlate": r.get("numberPlate", r["vehicleName"]),
                "driverName":  r["driverName"],
                "value":       r[sort_key],
            }
            for i, r in enumerate(rows)
        ]

    def fleet_operation_totals(self) -> dict:
        """Aggregate totals for the whole fleet in the date range."""
        return self.op_totals

    # =================================================================
    # SECTION C — Alerts  (alerts.results)
    # Use for: overspeed, seatbelt, idling, afterhours, etc.
    # =================================================================

    def filter_alerts_by_type(self, alert_type: Optional[str]) -> list[dict]:
        """Returns alerts matching an alert type keyword (case-insensitive)."""
        if not alert_type:
            return self.alerts

        at_lower = alert_type.lower().replace("_", "").replace("-", "")
        return [
            a for a in self.alerts
            if at_lower in (a.get("AlertName") or "").lower().replace("_", "")
        ]

    def find_highest_speed_from_alerts(
        self, alert_type: str = "overspeed"
    ) -> dict:
        """
        Which driver/vehicle hit the highest recorded speed
        within the overspeed alerts?
        """
        speed_alerts = [
            a for a in self.filter_alerts_by_type(alert_type)
            if isinstance(a.get("OrginalValue"), (int, float))
        ]
        if not speed_alerts:
            return {}

        top = max(speed_alerts, key=lambda a: a["OrginalValue"])
        vn = top.get("VehicleName")
        np = top.get("NumberPlate") or self.vn_to_np.get(vn, vn)
        
        return {
            "vehicleName": vn,
            "numberPlate": np,
            "driverName":  top.get("DriverName"),
            "speed":       top.get("OrginalValue"),
            "limit":       top.get("Limit"),
            "date":        top.get("Date"),
            "duration":    top.get("Duration"),
            "location":    top.get("Location"),
        }

    def most_alerts_driver(
        self, alert_type: Optional[str] = None
    ) -> dict:
        """Which driver triggered the most alerts (of a given type)?"""
        filtered = self.filter_alerts_by_type(alert_type)
        
        counts = defaultdict(int)
        vehicles = {}
        groups = {}
        driver_distributions = defaultdict(lambda: defaultdict(int))
        
        for a in filtered:
            raw_driver = a.get("DriverName")
            if not raw_driver:
                continue
            
            driver = _clean_driver(raw_driver)
            if driver == "Unassigned":
                continue
                
            counts[driver] += 1
            vn = a.get("VehicleName")
            np = a.get("NumberPlate") or self.vn_to_np.get(vn, vn)
            gn = a.get("GroupName")
            if np:
                vehicles[driver] = np
            if gn and str(gn).strip() not in ("", "None", "Unknown"):
                groups[driver] = gn
                
            alert_name = a.get("AlertName", "Unknown")
            driver_distributions[driver][alert_name] += 1
                
        if not counts:
            return {}
            
        driver, count = max(counts.items(), key=lambda x: x[1])
        return {
            "driverName":  driver,
            "numberPlate": vehicles.get(driver, "Unknown Vehicle"),
            "groupName":   groups.get(driver, "Unknown"),
            "alertCount":  count,
            "alertType":   alert_type or "all",
            "alertDistribution": dict(driver_distributions[driver])
        }

    def most_alerts_vehicle(
        self, alert_type: Optional[str] = None
    ) -> dict:
        """Which vehicle had the most alerts (of a given type)?"""
        filtered = self.filter_alerts_by_type(alert_type)
        
        counts = defaultdict(int)
        drivers = {}
        groups = {}
        vehicle_distributions = defaultdict(lambda: defaultdict(int))
        
        for a in filtered:
            vn = a.get("VehicleName")
            np = a.get("NumberPlate") or self.vn_to_np.get(vn, vn)
            if not np:
                continue
                
            counts[np] += 1
            
            gn = a.get("GroupName")
            if gn and str(gn).strip() not in ("", "None", "Unknown"):
                groups[np] = gn
                
            # Keep the latest or any driver name found for this vehicle in alerts
            raw_driver = a.get("DriverName")
            if raw_driver:
                drivers[np] = _clean_driver(raw_driver)
                
            alert_name = a.get("AlertName", "Unknown")
            vehicle_distributions[np][alert_name] += 1
                
        if not counts:
            return {}
            
        vehicle_np, count = max(counts.items(), key=lambda x: x[1])
        return {
            "numberPlate": vehicle_np,
            "driverName":  drivers.get(vehicle_np),
            "groupName":   groups.get(vehicle_np, "Unknown"),
            "alertCount":  count,
            "alertType":   alert_type or "all",
            "alertDistribution": dict(vehicle_distributions[vehicle_np])
        }

    def least_alerts_vehicle(
        self, alert_type: Optional[str] = None
    ) -> dict:
        """Which vehicle had the least alerts (of a given type)?"""
        filtered = self.filter_alerts_by_type(alert_type)
        
        counts = defaultdict(int)
        drivers = {}
        groups = {}
        vehicle_distributions = defaultdict(lambda: defaultdict(int))
        
        for r in self.live_records:
            np = r.get("numberPlate") or self.vn_to_np.get(r.get("vehicle", ""), None)
            if np:
                counts[np] = 0
                drivers[np] = _clean_driver(r.get("driverName"))
                groups[np] = r.get("groupName", "Unknown")

        for a in filtered:
            vn = a.get("VehicleName")
            np = a.get("NumberPlate") or self.vn_to_np.get(vn, vn)
            if not np:
                continue
                
            counts[np] += 1
            
            gn = a.get("GroupName")
            if gn and str(gn).strip() not in ("", "None", "Unknown"):
                groups[np] = gn
                
            raw_driver = a.get("DriverName")
            if raw_driver:
                drivers[np] = _clean_driver(raw_driver)
                
            alert_name = a.get("AlertName", "Unknown")
            vehicle_distributions[np][alert_name] += 1
                
        if not counts:
            return {}
            
        vehicle_np, count = min(counts.items(), key=lambda x: x[1])
        return {
            "numberPlate": vehicle_np,
            "driverName":  drivers.get(vehicle_np),
            "groupName":   groups.get(vehicle_np, "Unknown"),
            "alertCount":  count,
            "alertType":   alert_type or "all",
            "alertDistribution": dict(vehicle_distributions[vehicle_np])
        }
    def rank_vehicles_by_alerts(
        self, alert_type: Optional[str] = None, top_n: int = 10
    ) -> list[dict]:
        """Rank vehicles by the number of alerts (optionally filtered by type)."""
        filtered = self.filter_alerts_by_type(alert_type)
        
        counts = defaultdict(int)
        drivers = {}
        groups = {}
        vehicle_distributions = defaultdict(lambda: defaultdict(int))
        
        for a in filtered:
            vn = a.get("VehicleName")
            np = a.get("NumberPlate") or self.vn_to_np.get(vn, vn)
            if not np:
                continue
                
            counts[np] += 1
            
            gn = a.get("GroupName")
            if gn and str(gn).strip() not in ("", "None", "Unknown"):
                groups[np] = gn
                
            raw_driver = a.get("DriverName")
            if raw_driver:
                drivers[np] = _clean_driver(raw_driver)
                
            alert_name = a.get("AlertName", "Unknown")
            vehicle_distributions[np][alert_name] += 1

        rows = sorted(
            counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return [
            {
                "rank":        i + 1,
                "numberPlate": np,
                "driverName":  drivers.get(np) or self.np_to_driver.get(np, "Unknown"),
                "groupName":   groups.get(np, "Unknown"),
                "value":       count,
                "alertDistribution": dict(vehicle_distributions[np])
            }
            for i, (np, count) in enumerate(rows)
        ]
    def most_alerts_group(
        self, alert_type: Optional[str] = None
    ) -> dict:
        """Which group had the most alerts (of a given type)?"""
        filtered = self.filter_alerts_by_type(alert_type)
        
        counts = defaultdict(int)
        group_distributions = defaultdict(lambda: defaultdict(int))
        
        for a in filtered:
            gn = a.get("GroupName")
            if not gn or str(gn).strip() in ("", "None", "Unknown"):
                continue
                
            counts[gn] += 1
            alert_name = a.get("AlertName", "Unknown")
            group_distributions[gn][alert_name] += 1
                
        if not counts:
            return {}
            
        group_name, count = max(counts.items(), key=lambda x: x[1])
        return {
            "groupName":   group_name,
            "alertCount":  count,
            "alertType":   alert_type or "all",
            "alertDistribution": dict(group_distributions[group_name])
        }

    def alert_count_by_type(self) -> dict:
        """Distribution of all alert types across the fleet."""
        counts: dict[str, int] = Counter(
            a.get("AlertName", "Unknown") for a in self.alerts
        )
        return dict(counts)

    def alert_count_summary(self, alert_type: Optional[str] = None) -> dict:
        """Total count of alerts (optionally filtered by type)."""
        filtered = self.filter_alerts_by_type(alert_type)
        return {
            "alertType":  alert_type or "all",
            "totalAlerts": len(filtered),
        }

    def list_alerts_summary(
        self, alert_type: Optional[str] = None, limit: int = 20
    ) -> list[dict]:
        """Condensed list of alert events for display."""
        filtered = self.filter_alerts_by_type(alert_type)
        result = []
        for a in filtered[:limit]:
            vn = a.get("VehicleName")
            np = a.get("NumberPlate") or self.vn_to_np.get(vn, vn)
            driver_val = _clean_driver(a.get("DriverName")) if a.get("DriverName") else None
            result.append({
                "vehicleName": vn,
                "numberPlate": np,
                "driverName":  driver_val,
                "alertName":   a.get("AlertName"),
                "value":       a.get("CurrentValue") or a.get("OrginalValue"),
                "limit":       a.get("Limit"),
                "duration":    a.get("Duration"),
                "date":        a.get("Date"),
            })
        return result


# =========================================================

    def vehicles_with_alerts(self, alert_type=None):
        """
        Returns one entry per unique vehicle that triggered alerts of the
        given type, sorted by alert count descending.

        Used for queries like 'which vehicles had overspeed today' where
        the user wants a vehicle list, not individual event details.
        """
        filtered = self.filter_alerts_by_type(alert_type)

        counts = {}
        drivers = {}
        groups = {}

        for a in filtered:
            vn = a.get("VehicleName")
            np = a.get("NumberPlate") or self.vn_to_np.get(vn, vn)
            if not np:
                continue

            counts[np] = counts.get(np, 0) + 1

            raw_driver = a.get("DriverName")
            if raw_driver:
                drivers[np] = _clean_driver(raw_driver)

            gn = a.get("GroupName")
            if gn and str(gn).strip() not in ("", "None", "Unknown"):
                groups[np] = gn

        return [
            {
                "numberPlate": np,
                "driverName":  drivers.get(np, "Unassigned"),
                "groupName":   groups.get(np, ""),
                "alertCount":  count,
            }
            for np, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]

# PRIVATE HELPERS
# =========================================================

def _clean_driver(name: Optional[str]) -> str:
    if not name:
        return "Unassigned"
    return " ".join(name.split())


def _live_row_summary(r: dict) -> dict:
    return {
        "vehicleName": r.get("vehicleName"),
        "numberPlate": r.get("numberPlate"),
        "driverName":  _clean_driver(r.get("driverName")),
        "speed":       r.get("speed"),
        "status":      VSTATUS_MAP.get(r.get("vStatus"), "unknown"),
        "lastUpdated": r.get("lastUpdatedTime"),
    }
