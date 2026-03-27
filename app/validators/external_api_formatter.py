import re
from typing import Any
from app.utils.logger import logger


def data_formatter(result: dict[str, Any]):

    if isinstance(result, dict):
        logger.info(f"\n\n Vehicle Details from data formatter: {result}")
    
        if not result:
            return "Sorry, I couldn't fetch vehicle details."

        return f"""
    Vehicle Details:

    • Vehicle type: {result.get("Vehicletype")}
    • Group ID : {result.get("GroupID")}
    • Group Name: {result.get("GroupName")}
    • Plate Number: {result.get("NumberPlate")}
    • IMEI number: {result.get("IMEI")}
"""
    
    else:
        return "Result is not instance of list"
    

def extract_imei_from_query(query: str):
    match = re.search(r"\b\d{15}\b", query)
    return match.group() if match else None



# {'ID': 117, 'Name': '102', 'DepartmentID': None,
#   'TypeID': 11, 'IMEI': '868963040927576', 
#   'NumberPlate': '4672 J R B', 'VIN': None, 
#   'GroupID': 34, 'CreatedDate': '2022-05-26T00:00:00.000Z', 
#   'Status': '1', 'GroupName': 'Sales Team, Sales Team 2024', 
#   'Vehicletype': 'Truck', 'lastUpdatedTime': '2026-03-16T07:36:29.000Z', 
#   'TankerEquipmentNumber': None}