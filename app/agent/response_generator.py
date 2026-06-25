from app.llm.ollama_client import OllamaClient
from app.response_generator.formatt_router import build_user_message
from app.utils.logger import logger


llm = OllamaClient()


def generate_response(result, intent):

    logger.debug(f"Result passed into the response generation: {result}")
    logger.debug(f"ResponseGenerator intent: {intent}")

    if not result:
        return "No data found."

    if "error" in result:
        return result["error"]

    base_message = build_user_message(
        result=result,
        intent=intent
    )


    query_str = getattr(intent, "query", "") or ""

    if result.get("type") == "summary":
        prompt = (
            "You are a professional fleet management chatbot. Your task: rewrite the telemetry INPUT below into a highly professional, beautifully structured daily summary report.\n"
            "\n"
            "STRUCTURE RULES:\n"
            "1. Start with a brief, professional introductory sentence stating the vehicle ID, type, group, and the exact date range (time period) covered by the summary.\n"
            "2. Present the daily breakdown reports as clean, professional, and easy-to-read single-line bullet points (one for each day). Do not write sub-bullet points. Each bullet point must be formatted in Markdown on a single line in this format:\n"
            "   * **[Date]**: [Distance] km traveled, max speed [Max Speed] km/h, moving [Moving Time], idle [Idle Time], stopped [Stop Time]\n"
            "3. Conclude with a single, highly professional final sentence highlighting overall stats or key performance metrics (such as total distance, average speed, highest speed, or engine hours).\n"
            "\n"
            "CONTRACT:\n"
            "- OUTPUT contains only facts present in INPUT — nothing added, nothing omitted.\n"
            "- Do not add any introductory header, extra commentary, notes, parenthetical explanations, or conversational filler under any circumstances. For example, never output '(Note: ...)' or any explanation of formatting changes.\n"
            "- Strictly output ONLY the final report itself and absolutely nothing else.\n"
            "- Use clean Markdown bullet points.\n"
            "- DRIVER RULE: If the driver is 'null', 'NA', 'None', 'Unknown', or 'Unassigned', state that 'driver details are not currently available' rather than 'Driver NA', 'Driver null', or 'Driver Unknown'.\n"
            "- VEHICLE IDENTIFIERS: Never split a vehicle's identifier into a separate 'ID' and 'Name'. Treat the entire identifier as a single immutable string. Do NOT invent vehicle identifiers.\n"
            "\n"
            "<example>\n"
            "INPUT: Vehicle ABC-123 of type Truck belongs to group Alpha Fleet. For the period Oct 01 to Oct 02. Total distance traveled was 150 km. Total moving time was 03:00:00. Total idle time was 00:30:00. Total stop time was 44:30:00. Highest speed recorded was 80 km/h on Oct 02. Average daily maximum speed across 2 days was 77.5 km/h. On Oct 01, distance traveled was 50 km, maximum speed reached 75 km/h, moving time was 01:00:00, idle time was 00:10:00, and stop time was 22:50:00. On Oct 02, distance traveled was 100 km, maximum speed reached 80 km/h, moving time was 02:00:00, idle time was 00:20:00, and stop time was 21:40:00.\n"
            "OUTPUT: Vehicle ABC-123 (Truck), belonging to group Alpha Fleet, is summarized as follows for the period Oct 01 to Oct 02:\n"
            "\n"
            "* **Oct 01**: 50.0 km traveled, max speed 75 km/h, moving 01:00:00, idle 00:10:00, stopped 22:50:00\n"
            "* **Oct 02**: 100.0 km traveled, max speed 80 km/h, moving 02:00:00, idle 00:20:00, stopped 21:40:00\n"
            "\n"
            "Total distance covered was 150.0 km over the period, with a highest speed of 80 km/h on Oct 02.\n"
            "</example>\n"
            "\n"
            f"USER_QUERY: {query_str}\n"
            f"INPUT: {base_message}\n"
            "OUTPUT:"
        )
    elif result.get("type") == "realtime_status":
        prompt = (
            "You are a professional fleet management chatbot. Your task: rewrite the comprehensive realtime status telemetry INPUT below into a highly professional, minimal, and beautifully structured status report.\n"
            "\n"
            "STRUCTURE RULES:\n"
            "1. Start with a brief, professional introductory sentence stating the vehicle ID, type, current status (stopped with engine off / stationary but ignition is on / moving at speed), and the assigned group.\n"
            "2. Present the detailed status parameters as four clean, easy-to-read single-line bullet points exactly in this format:\n"
            "   * **Specifications**: Manufactured by [Make], [Model] model, classified as [tanker/can], with odometer reading of [Odometer Reading], IMEI for device [IMEI], and Camera IMEI [Camera IMEI]\n"
            "   * **Connectivity & Power**: [GSM signal status with value], and battery voltage is [Battery voltage]\n"
            "   * **Fuel & Tanks**: Fuel level is [Fuel level] of [Fuel capacity] capacity, and tanker fuel level is [Tanker fuel level] of [Tanker capacity] capacity\n"
            "   * **Safety & Security**: Ignition is [Ignition status], seatbelt is [Seatbelt status], remote immobilization is [Immobilization status], and [Camera status]\n"
            "3. Conclude with a single, highly professional final sentence exactly in this format: Driver assigned is [Driver name]. Last updated: [Last updated timestamp]. Location map: [Location Map Link]\n"
            "\n"
            "CONTRACT:\n"
            "- OUTPUT contains only facts present in INPUT — nothing added, nothing omitted.\n"
            "- Do not add any introductory header, extra commentary, notes, parenthetical explanations, or conversational filler under any circumstances. For example, never output '(Note: ...)' or any explanation of formatting changes.\n"
            "- Strictly output ONLY the final report itself and absolutely nothing else.\n"
            "- Use clean Markdown bullet points.\n"
            "- For descriptive fields (camera, seatbelt, ignition, door, immobilization, tanker_status, gsm_signal), preserve the exact descriptive phrase from INPUT.\n"
            "- DRIVER RULE: If the driver is 'null', 'NA', 'None', 'Unknown', or 'Unassigned', output 'driver details are not currently available' instead of 'driver is NA', 'driver is null', or 'driver assigned is Unknown'.\n"
            "- VEHICLE IDENTIFIERS: Never split a vehicle's identifier into a separate 'ID' and 'Name'. Treat the entire identifier as a single immutable string. Do NOT invent vehicle identifiers.\n"
            "\n"
            "<example>\n"
            "INPUT: Vehicle 1832 RXB is currently stopped with the engine off. Fuel level is 0.0%. Vehicle has a fuel capacity of 400 L. The tanker has a fuel capacity of 8000 L. Tanker fuel level is 0.0%. Battery voltage is 13.5 V. Vehicle 1832 RXB is classified as a can. Vehicle type is Pick Up. Manufacturer is Isuzu and model is DOUBLE CABIN 2022. Vehicle is a can and belongs to Flames Hydraulic Co, Info, Others, Test Group. Driver assigned is Vipin. The ignition is off. The seatbelt is equipped but not fastened. Vehicle supports remote immobilization and is not currently remotely immobilized. Vehicle 1832 RXB has a good GSM signal with value of 5. Location map: https://www.google.com/maps?q=26.4325149,50.1023883. Last updated May 26, 2026 06:55 AM UTC. Camera IMEI is 940076337414. IMEI is 868963040937609. Odometer reading is 12345.6 km. camera is equipped with 1 camera channel.\n"
            "OUTPUT: Vehicle 1832 RXB (Pick Up, Isuzu DOUBLE CABIN 2022) is currently stopped with the engine off and belongs to Flames Hydraulic Co, Info, Others, Test Group.\n"
            "\n"
            "* **Specifications**: Manufactured by Isuzu, DOUBLE CABIN 2022 model, classified as can, with odometer reading of 12345.6 km, IMEI 868963040937609, and Camera IMEI 940076337414\n"
            "* **Connectivity & Power**: GSM signal is good with value of 5, and battery voltage is 13.5 V\n"
            "* **Fuel & Tanks**: Fuel level is 0.0% of 400 L capacity, and tanker fuel level is 0.0% of 8000 L capacity\n"
            "* **Safety & Security**: Ignition is off, seatbelt is equipped but not fastened, remote immobilization is supported (not currently immobilized), and camera is equipped with 1 camera channel\n"
            "\n"
            "Driver assigned is Vipin. Last updated: May 26, 2026 06:55 AM UTC. Location map: https://www.google.com/maps?q=26.4325149,50.1023883\n"
            "</example>\n"
            "\n"
            f"USER_QUERY: {query_str}\n"
            f"INPUT: {base_message}\n"
            "OUTPUT:"
        )
    elif result.get("type") == "fleet_analytics":
        prompt = (
            "You are a professional fleet management chatbot. Your task is to rewrite the fleet analytics INPUT below into a natural, friendly, and highly professional OUTPUT response.\n"
            "\n"
            "CRITICAL CONTRACT:\n"
            "1. EXACT FACTS ONLY: You MUST ONLY use the exact facts, vehicles, numbers, and data points provided in the INPUT. Do NOT omit important context (like the specific status being queried). NEVER fabricate, invent, or add fake vehicles, fake drivers, or fake dates.\n"
            "2. NO FILLER: Do not add introductory headers (e.g., 'Here is the data:'), extra commentary, conversational filler, or 'Note:' sections.\n"
            "3. PRESERVE LISTS: If the INPUT contains a list of vehicles, preserve them as a clean bulleted list. IMPORTANT: If the USER_QUERY asks to filter by a specific group, status, or condition (e.g., 'in the Others group', 'without a camera'), you MUST filter the INPUT list to ONLY include vehicles that match the user's criteria.\n"
            "4. NO QUOTES: Do not add quotation marks around vehicle names, group names, driver names, metrics, or statuses.\n"
            "5. DRIVERS & ENTITIES: Treat driver names and group names as single immutable entities. If driver details are explicitly present in the INPUT and the driver is 'null', 'NA', 'None', 'Unknown', or 'Unassigned', output 'driver details are not currently available'. If drivers are NOT mentioned in the INPUT, DO NOT mention drivers at all in your OUTPUT.\n"
            "6. VEHICLE IDENTIFIERS: Never split a vehicle's identifier into a separate 'ID' and 'Name'. Treat the entire identifier as a single immutable string. Do NOT invent vehicle identifiers.\n"
            "7. DIRECT ANSWER: Ensure your response directly and explicitly answers the core question asked in the USER_QUERY. Do not bury the answer in a generic summary.\n"
            "8. DATE RANGE: Always explicitly mention the exact date range in your response if it is provided in the INPUT (e.g., 'between [Start Date] and [End Date]'). Do NOT invent or copy dates from these instructions; use ONLY the dates provided in the INPUT.\n"
            "\n"
            "Strictly output ONLY the polished response and absolutely nothing else.\n"
            "\n"
            f"USER_QUERY: {query_str}\n"
            f"INPUT: {base_message}\n"
            "OUTPUT:"
        )
    else:
        prompt = (
            "You are a professional fleet management chatbot. Your task: rewrite the telemetry INPUT below into a natural, friendly, and highly professional OUTPUT sentence.\n"
            "\n"
            "CRITICAL CONTRACT:\n"
            "1. NO HALLUCINATION: You MUST ONLY use the exact facts, vehicles, and data points provided in the INPUT. NEVER fabricate, invent, or add fake vehicles, fake drivers, or extra information.\n"
            "2. NO FILLER: Do not add any introductory header, extra commentary, notes, parenthetical explanations, or conversational filler under any circumstances. For example, never output '(Note: ...)' or any explanation of formatting changes.\n"
            "3. Strictly output ONLY the rewritten output itself and absolutely nothing else.\n"
            "4. Write in short, professional sentence style. No bullet points, no pipes, no labels unless it's a long list.\n"
            "5. NO PREAMBLE OR CONVERSATIONAL FILLER: NEVER use phrases like 'Since the INPUT indicates', 'Here is a rewritten version', or 'The output should reflect this'. Output ONLY the final data-driven sentence.\n"
            "- SPEED & MOVEMENT RULE:\n"
            "  * If Speed is exactly '0 km/h', interpret and describe it as being 'stationary' or 'stopped' (e.g. 'is currently stationary at 0 km/h' or 'is stopped at 0 km/h'). Never just print raw 0 km/h without describing it as stationary or stopped.\n"
            "  * If Speed is greater than '0 km/h', describe it as 'moving' (e.g. 'is currently moving at 45 km/h').\n"
            "- For descriptive fields (camera, seatbelt, ignition, door, immobilization, tanker_status, gsm_signal), preserve the exact descriptive phrase from INPUT.\n"
            "- DRIVER RULE: If driver details are explicitly present in the INPUT and the driver is 'null', 'NA', 'None', 'Unknown', or 'Unassigned', output 'driver details are not currently available' or 'does not have a driver assigned'. Do not mention drivers at all if they are not included in the INPUT.\n"
            "- VEHICLE IDENTIFIERS: Never split a vehicle's identifier into a separate 'ID' and 'Name'. Treat the entire identifier as a single immutable string. Do NOT invent vehicle identifiers.\n"
            "- LOCATION RULE: If the INPUT contains a Google Maps URL (e.g., 'current location: https://maps.google.com/?q=...' or 'Location map: https://...'), you MUST preserve and include the full URL exactly as given in the OUTPUT. NEVER convert a Maps URL into raw coordinates or plain text like 'located at lat, lon'. Always present it as a clickable link in the format: 'Vehicle [ID] is currently located at [Google Maps URL]'.\n"
            "7. DIRECT ANSWER: Ensure your response directly and explicitly answers the core question asked in the USER_QUERY using the facts from the INPUT. For example, if the user asks 'on which day', highlight that day clearly. If the user asks for a specific metric, highlight it prominently.\n"
            "8. DATE RANGE: Always explicitly mention the exact date range in your response if it is provided in the INPUT (e.g., 'between [Start Date] and [End Date]'). Do NOT invent or copy dates from these instructions; use ONLY the dates provided in the INPUT.\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 6667 DKB, current location: https://maps.google.com/?q=26.40407,50.1034383.\n"
            "OUTPUT: Vehicle 6667 DKB is currently located at https://maps.google.com/?q=26.40407,50.1034383\n"
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 4671 JRB, driver name data is unavailable.\n"
            "OUTPUT: Vehicle 4671 JRB does not have a driver assigned.\n"
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 1832 RXB, vehicle is a can.\n"
            "OUTPUT: Vehicle 1832 RXB is classified as a can.\n"
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 1832 RXB, vehicle is a tanker.\n"
            "OUTPUT: Vehicle 1832 RXB is a tanker.\n"
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 1832 RXB, GSM signal is good with value of 5.\n"
            "OUTPUT: Vehicle 1832 RXB has a good GSM signal with value of 5.\n"
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 1832 RXB, device has no GSM signal with value of 0.\n"
            "OUTPUT: Vehicle 1832 RXB has no GSM signal (value of 0).\n"
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 1832RXB, Speed is 0 km/h. Fuel capacity is 400 L."
            "OUTPUT: Vehicle 1832RXB is currently stationary at 0 km/h with a fuel capacity of 400 L."
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 1832RXB, Speed is 0 km/h."
            "OUTPUT: Vehicle 1832RXB is currently stationary (stopped at 0 km/h)."
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 1832RXB, Speed is 65 km/h."
            "OUTPUT: Vehicle 1832RXB is currently moving at 65 km/h."
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 1832 RXB, camera is equipped with 1 camera channel."
            "OUTPUT: Vehicle 1832 RXB has a camera equipped with 1 channel."
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 5001 ABC, camera is not equipped."
            "\n"
            "OUTPUT: Vehicle 5001 ABC does not have a camera equipped."
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 1832 RXB, vehicle supports remote immobilization"
            " and is currently not remotely immobilized."
            "OUTPUT: Vehicle 1832 RXB supports remote immobilization and is not currently immobilized."
            "</example>\n"
            "\n"
            "<example>\n"
            "INPUT: For vehicle 1832 RXB, ignition is on. seatbelt is equipped but not fastened."
            "OUTPUT: Vehicle 1832 RXB has the ignition on. The seatbelt is equipped but not fastened."
            "</example>\n"
            "\n"
            "Now rewrite only this INPUT considering the USER_QUERY:\n"
            f"USER_QUERY: {query_str}\n"
            f"INPUT: {base_message}\n"
            "OUTPUT:"
        )

    response = llm.generate(prompt).strip()

    # Strip LLM hallucinated preambles
    import re
    response = re.sub(r'^(Here is|Based on|I can help|Sure|Yes|The output).*?:\s*\n*', '', response, flags=re.IGNORECASE)
    response = re.sub(r'^\*\*(.*?)\*\*\n*', '', response)

    if result.get("type") == "summary":
        query_str = getattr(intent, "query", "") or ""
        query_lower = query_str.lower()

        is_today_requested = "today" in query_lower or "today's" in query_lower
        is_default_range = getattr(intent, "summary_time_range_default", False)

        logger.info(f"Python conditions for summary note: query='{query_str}', is_today_requested={is_today_requested}, is_default_range={is_default_range}")

        if is_default_range or is_today_requested:
            note = "\n\n*Note: Today's summary data is currently unavailable. Fleet telemetry updates are processed daily at midnight during the data migration process.*"
            response += note
        else:
            logger.info("Skipping summary unavailability note because it was not defaulted or today's summary.")

    if result.get("backoff_applied"):
        orig_f, orig_t = result.get("backoff_original_range", (None, None))
        used_f, used_t = result.get("backoff_used_range", (None, None))
        
        def format_d(d):
            if not d: return ""
            try:
                from datetime import datetime
                return datetime.strptime(d, "%Y-%m-%d").strftime("%b %d, %Y")
            except Exception:
                return d
                
        orig_f_fmt = format_d(orig_f)
        orig_t_fmt = format_d(orig_t)
        used_f_fmt = format_d(used_f)
        used_t_fmt = format_d(used_t)
        
        if orig_f == orig_t:
            orig_str = f"on {orig_t_fmt}"
        else:
            orig_str = f"for the period from {orig_f_fmt} to {orig_t_fmt}"
            
        note = f"\n\n*Note: No alerts were found {orig_str}. To provide useful context, the system has dynamically backed off to show alerts found in the past period from {used_f_fmt} to {used_t_fmt}.*"
        response += note

    if result.get("time_range_altered_to_week") and result.get("type") in ["summary", "summary_metric"]:
        note = "\n\n*Note: As today's operation summary data may not be fully available yet, the system has backed off to show data from the past week.*"
        response += note

    return response