"""Role-scoped visualization service for rendering charts and structured reports.

POST /visualize
{
  "chart_type": "bar",
  "title": "Attendance by Department",
  "labels": ["BSIT", "BSCS", "BSECE"],
  "data": [120, 150, 80],
  "options": { "label": "Students Present" }
}
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="MCP Visualization Service")

class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    SVG = "svg"
    HTML = "html"

class VisualizationRequest(BaseModel):
    chart_type: ChartType
    title: str
    labels: Optional[List[str]] = None
    data: Optional[Union[List[float], List[int], List[Dict[str, Any]]]] = None
    source: Optional[str] = Field(None, description="Raw SVG string or HTML snippet")
    options: Dict[str, Any] = Field(default_factory=dict)
    
    # Context for audit/policy
    role: Optional[str] = None
    school_id: Optional[int] = None

@app.post("/visualize")
def visualize(body: VisualizationRequest) -> Dict[str, Any]:
    """Process data into a structured visualization payload for the Frontend."""
    
    # We essentially wrap the input into a standard "Aura Visual" format
    # that the Frontend's AuraVisualization.vue component understands.
    
    response = {
        "__aura_visual__": True,
        "type": body.chart_type,
        "title": body.title,
        "payload": {
            "labels": body.labels or [],
            "datasets": [
                {
                    "label": body.options.get("label", body.title),
                    "data": body.data or [],
                    "backgroundColor": body.options.get("colors") or _get_default_colors(body.chart_type),
                }
            ]
        },
        "options": body.options
    }
    
    if body.chart_type in [ChartType.SVG, ChartType.HTML]:
        if not body.source:
            raise HTTPException(status_code=400, detail=f"source is required for {body.chart_type}")
        response["source"] = body.source
        
    return response

def _get_default_colors(chart_type: ChartType) -> List[str]:
    # Aura Design System matched colors
    colors = [
        "rgba(255, 107, 107, 0.8)",  # Soft Red
        "rgba(78, 205, 196, 0.8)",   # Teal
        "rgba(255, 201, 101, 0.8)",  # Mustard
        "rgba(0, 150, 136, 0.8)",    # Emerald
        "rgba(106, 76, 147, 0.8)",   # Purple
        "rgba(255, 159, 64, 0.8)",   # Orange
    ]
    if chart_type in [ChartType.PIE, ChartType.DOUGHNUT]:
        return colors
    return [colors[1]] # Primary teal for bars/lines
