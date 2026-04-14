from typing import Any


def format_operation_summary(result: dict[str, Any]) -> str:

    if not result:
        return "No operation data available."

    summary = result.get("summary", {})
    rows = result.get("dataRows", [])

    if not summary:
        return "Operation summary not available."

    # -----------------------------
    # SUMMARY BLOCK
    # -----------------------------
    response = f"""
Operation Summary:

• Total Distance: {summary.get("totalDistance", "N/A")} km
• Total Moving Time: {summary.get("totalMovingTime", "N/A")}
• Total Idle Time: {summary.get("totalIdleTime", "N/A")}
• Total Stop Time: {summary.get("totalStopTime", "N/A")}
• Engine Hours: {summary.get("totalEngineHours", "N/A")}
"""

    # -----------------------------
    # OPTIONAL: DAILY BREAKDOWN
    # -----------------------------
    if rows:
        response += "\nDaily Breakdown:\n"

        for row in rows[:5]:  # limit to avoid long responses
            response += f"""
• {row.get("Date")}:
  - Distance: {row.get("distance")} km
  - Moving: {row.get("movingTimeFormated")}
  - Idle: {row.get("idleTimeFormated")}
  - Stop: {row.get("stopTimeFormated")}
"""

        if len(rows) > 5:
            response += "\n...and more days."

    return response.strip()


# {'ID': 117, 'Name': '102', 'DepartmentID': None,
#   'TypeID': 11, 'IMEI': '868963040927576', 
#   'NumberPlate': '4672 J R B', 'VIN': None, 
#   'GroupID': 34, 'CreatedDate': '2022-05-26T00:00:00.000Z', 
#   'Status': '1', 'GroupName': 'Sales Team, Sales Team 2024', 
#   'Vehicletype': 'Truck', 'lastUpdatedTime': '2026-03-16T07:36:29.000Z', 
#   'TankerEquipmentNumber': None}