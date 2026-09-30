from pydantic import BaseModel

from apps.intelligence.correlation.situation import CAUSAL_TRANSITIONS, Situation


class Forecast(BaseModel):
    predicted_concept: str
    probability: float
    reasons: list[str]


class SituationForecast(BaseModel):
    situation_id: str
    current_status: str
    predictions: list[Forecast]


def generate_forecast(situation: Situation) -> SituationForecast:
    """
    Project the future trajectory of an evolving situation.
    
    This analyzes the latest Incident DNA in the situation and uses 
    the causal knowledge base to predict what is likely to happen next.
    """
    
    if not situation.incidents:
        raise ValueError("Cannot forecast a situation with no incidents.")
        
    # Get all concepts currently active in the situation (so we don't predict them again)
    active_concepts = set()
    for incident in situation.incidents:
        for concept in incident.core_concepts:
            active_concepts.add(concept.concept)
            
    # The latest incident DNA is the most relevant for short-term forecasting
    latest_incident = sorted(situation.incidents, key=lambda i: i.start_time)[-1]
    
    predictions_map = {}
    
    # Check what typically follows the concepts active in the latest incident
    for core_concept in latest_incident.core_concepts:
        concept = core_concept.concept
        weight = core_concept.weight
        
        # Look for this concept acting as a cause in our transitions
        for (cause, effect), score in CAUSAL_TRANSITIONS.items():
            if cause == concept and effect not in active_concepts:
                
                # Base probability of transition multiplied by current severity/weight
                prob = score * weight
                
                if effect not in predictions_map:
                    predictions_map[effect] = {
                        "probability": prob,
                        "reasons": [
                            f"Current incident shows strong presence of '{cause}' (weight {weight:.2f}), "
                            f"which has a historical transition probability of {score:.2f} to '{effect}'."
                        ]
                    }
                else:
                    # Combine probabilities if multiple active concepts lead to the same effect
                    existing_prob = predictions_map[effect]["probability"]
                    # P(A or B) = P(A) + P(B) - P(A)*P(B)
                    combined_prob = existing_prob + prob - (existing_prob * prob)
                    
                    predictions_map[effect]["probability"] = combined_prob
                    predictions_map[effect]["reasons"].append(
                        f"Additionally, the presence of '{cause}' corroborates this prediction."
                    )
                    
    # Format the predictions
    forecasts = []
    for effect, data in predictions_map.items():
        if data["probability"] >= 0.10:  # Threshold for reporting
            forecasts.append(
                Forecast(
                    predicted_concept=effect,
                    probability=round(data["probability"], 4),
                    reasons=data["reasons"],
                )
            )
            
    # Sort by highest probability
    forecasts.sort(key=lambda f: f.probability, reverse=True)
    
    # Current status summary
    status = f"Evolving situation spanning {len(situation.incidents)} incidents. "
    status += f"Latest phase driven by: {', '.join([c.concept for c in latest_incident.core_concepts[:2]])}."
    
    return SituationForecast(
        situation_id=situation.situation_id,
        current_status=status,
        predictions=forecasts,
    )
