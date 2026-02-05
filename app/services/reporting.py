import json
from typing import Dict, Any
from datetime import datetime

def generate_crime_report(session_id: str, data: Dict[str, Any]) -> str:
    """
    STUB: PDF generation is disabled for Render deployment.
    Returns a dummy path.
    """
    # Simply log the data to a JSON file for now
    report_data = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    
    filename = f"report_{session_id}.json"
    with open(filename, "w") as f:
        json.dump(report_data, f, indent=2)
        
    return filename

def generate_ncrp_report(session_id: str, data: Dict[str, Any]) -> str:
    """
    STUB: NCRP Report generation is disabled for Render deployment.
    """
    return generate_crime_report(session_id, data)
