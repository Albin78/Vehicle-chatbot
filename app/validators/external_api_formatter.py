import re

def data_formatter(result: dict):
    
    if isinstance(result, dict):
        vehicle = result.get("data", {})
        if not vehicle:
            return "Sorry, I couldn't fetch vehicle details."

        return f"""
    Vehicle Details:

    • Company Name: {vehicle.get( "CompanyName")}
    • Model: {vehicle.get("modelName")}
    • Make: {vehicle.get("makeName")}
    • Type: {vehicle.get("typeName")}
    • Number Plate: {vehicle.get("NumberPlate")}
    • Mobile: {vehicle.get("Mobile")}
    • Active Profiles: {vehicle.get("ActiveProfile")}
    • Country Code: {vehicle.get("CountryCode")}
    • Plate Number: {vehicle.get("PlateNumber")}
    • SIMcard number: {vehicle.get("SimcardNumber")}
    • Manufacture Serial Number: {vehicle.get("ManufactureSerialNo")}
"""
    

def extract_imei_from_query(query: str):
    match = re.search(r"\b\d{15}\b", query)
    return match.group() if match else None