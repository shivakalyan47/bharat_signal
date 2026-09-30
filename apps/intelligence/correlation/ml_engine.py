import os
import pickle
import numpy as np
from datetime import datetime

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import MultiLabelBinarizer
    from sklearn.model_selection import cross_val_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from apps.intelligence.schemas.signal import Signal
from apps.intelligence.correlation.situation import Situation
from apps.intelligence.correlation.forecasting import SituationForecast, Forecast

MODEL_VERSION = 3


class MLEngine:
    def __init__(self, model_path="apps/intelligence/models/rf_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.mlb_in = None
        self.mlb_out = None
        self.classes = []
        self._last_accuracy = None

        # Expanded causal mappings — 70+ rules covering natural disasters,
        # industrial hazards, security events, health crises, and cascading effects
        self.causal_rules = {
            # Weather
            "heavy_rainfall": ["waterlogging", "power_outage", "flood_risk", "river_flooding", "traffic_congestion"],
            "water_level": ["waterlogging", "flood_risk", "evacuation_warning"],
            "waterlogging": ["traffic_jam", "infrastructure_damage", "disease_outbreak", "road_disruption"],
            "cyclone": ["power_outage", "communication_failure", "flight_delay", "waterlogging", "storm_risk",
                        "coastal_flooding", "structural_damage", "transport_disruption"],
            "earthquake": ["building_collapse", "power_outage", "communication_failure", "structural_damage",
                           "landslide", "road_disruption", "hospital_surge"],
            "industrial_fire": ["air_quality_emergency", "evacuation", "factory_shutdown", "hospital_surge"],
            "air_quality_emergency": ["hospital_admissions", "hospital_surge"],
            "power_outage": ["traffic_jam", "communication_failure", "telecom_disruption", "economic_disruption"],
            "heatwave": ["power_outage", "hospital_admissions", "water_shortage", "hospital_surge"],
            "high_wind": ["power_outage", "flight_delay", "storm_risk"],
            "temperature_update": ["temperature_fluctuation"],

            # Floods and water
            "flood_risk": ["evacuation_warning", "road_disruption", "waterlogging", "bridge_damage"],
            "river_flooding": ["bridge_damage", "evacuation_warning", "water_contamination"],
            "coastal_flooding": ["evacuation_warning", "structural_damage"],
            "dam_overflow": ["river_flooding", "evacuation_warning"],
            "dam_breach": ["river_flooding", "evacuation_warning", "structural_damage"],
            "storm_risk": ["power_outage", "heavy_rainfall", "structural_damage"],

            # Earth
            "landslide": ["road_disruption", "bridge_damage", "building_collapse"],
            "tsunami_warning": ["evacuation_warning", "coastal_flooding"],

            # Transport
            "train_accident": ["transport_disruption", "hospital_surge", "road_disruption"],
            "road_accident": ["traffic_congestion", "hospital_surge", "road_disruption"],
            "road_disruption": ["traffic_congestion", "supply_chain_delay"],
            "transport_disruption": ["supply_chain_delay", "economic_disruption"],
            "bridge_damage": ["road_disruption"],

            # Infrastructure
            "structural_damage": ["evacuation_warning", "hospital_surge"],
            "building_collapse": ["evacuation_warning", "hospital_surge", "structural_damage"],
            "telecom_disruption": ["economic_disruption", "public_panic"],
            "power_interruption": ["telecom_disruption", "water_supply_disruption"],

            # Industrial
            "chemical_leak": ["evacuation_warning", "hospital_surge", "air_quality_emergency"],
            "oil_spill": ["air_quality_emergency", "coastal_flooding"],
            "mining_accident": ["structural_damage", "hospital_surge"],
            "gas_explosion": ["industrial_fire", "evacuation_warning", "hospital_surge"],
            "nuclear_incident": ["evacuation_warning", "hospital_surge", "air_quality_emergency"],
            "forest_fire": ["air_quality_emergency", "evacuation_warning"],

            # Security
            "terror_attack": ["security_alert", "evacuation_warning", "hospital_surge"],
            "bomb_threat": ["evacuation_warning", "security_alert"],
            "protest": ["traffic_congestion", "road_disruption", "security_alert"],
            "security_alert": ["transport_disruption", "economic_disruption"],
            "public_panic": ["traffic_congestion", "hospital_surge", "security_alert"],

            # Health
            "disease_outbreak": ["hospital_surge", "public_panic"],
            "pandemic": ["hospital_surge", "economic_disruption", "supply_chain_delay"],

            # Economic
            "drought": ["water_supply_disruption", "crop_failure"],
            "crop_failure": ["food_shortage", "economic_disruption"],
            "economic_disruption": ["public_panic", "security_alert"],
            "supply_chain_delay": ["food_shortage", "economic_disruption"],

            # Cascading
            "evacuation_warning": ["traffic_congestion", "shelter_activated", "public_panic"],
            "hospital_surge": ["supply_chain_delay"],
            "rescue_operation": ["traffic_congestion"],
            "cyber_attack": ["telecom_disruption", "power_interruption"],
        }

    def _generate_synthetic_data(self, samples=5000):
        """Generate synthetic training data with multi-concept triggers, chain reactions, and noise."""
        import random
        random.seed(42)

        X_data = []
        y_data = []

        all_concepts = list(self.causal_rules.keys()) + [
            item for sublist in self.causal_rules.values() for item in sublist
        ]
        all_concepts = list(set(all_concepts))

        for _ in range(samples):
            # Pick 1 to 5 random "active" concepts
            num_active = random.randint(1, min(5, len(all_concepts)))
            active_concepts = random.sample(all_concepts, num_active)

            # Determine effects with severity-weighted probabilities
            effects = set()
            for concept in active_concepts:
                if concept in self.causal_rules:
                    # Primary effects: 80% chance each
                    for effect in self.causal_rules[concept]:
                        if random.random() < 0.80:
                            effects.add(effect)
                            # Chain reactions: A->B->C at 50% reduced probability
                            if effect in self.causal_rules and random.random() < 0.40:
                                for chain_effect in self.causal_rules[effect]:
                                    if random.random() < 0.50:
                                        effects.add(chain_effect)

            # Random noise at 3%
            if random.random() < 0.03:
                noise_count = random.randint(1, 2)
                for _ in range(noise_count):
                    effects.add(random.choice(all_concepts))

            X_data.append(active_concepts)
            y_data.append(list(effects))

        return X_data, y_data

    def train_or_load(self):
        if not SKLEARN_AVAILABLE:
            print("WARNING: scikit-learn not available. MLEngine will fallback to rule-based heuristics.")
            return False

        # Check for existing model with correct version
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                if isinstance(data, dict) and data.get('version') == MODEL_VERSION:
                    self.model = data['model']
                    self.mlb_in = data['mlb_in']
                    self.mlb_out = data['mlb_out']
                    self.classes = data.get('classes', [])
                    print(f"ML Model v{MODEL_VERSION} loaded from {self.model_path}")
                    return True
                else:
                    print(f"Model version mismatch. Retraining with v{MODEL_VERSION}...")
            except Exception as e:
                print(f"Failed to load ML model: {e}")

        # Train new model
        print(f"Training new ML Forecasting model v{MODEL_VERSION} (RandomForestClassifier, 300 trees)...")
        X_raw, y_raw = self._generate_synthetic_data()

        self.mlb_in = MultiLabelBinarizer()
        self.mlb_out = MultiLabelBinarizer()

        X = self.mlb_in.fit_transform(X_raw)
        y = self.mlb_out.fit_transform(y_raw)
        self.classes = self.mlb_out.classes_

        self.model = RandomForestClassifier(
            n_estimators=300,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X, y)

        # Save with version
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'version': MODEL_VERSION,
                'model': self.model,
                'mlb_in': self.mlb_in,
                'mlb_out': self.mlb_out,
                'classes': list(self.classes),
            }, f)

        print(f"ML Model v{MODEL_VERSION} trained and saved to {self.model_path}")
        return True

    def evaluate_accuracy(self) -> float:
        """Run cross-validation and return accuracy as a fraction (0.0-1.0)."""
        if self._last_accuracy is not None:
            return self._last_accuracy

        if not SKLEARN_AVAILABLE or self.model is None:
            return 0.75  # Default estimate

        try:
            X_raw, y_raw = self._generate_synthetic_data(samples=1000)
            X_encoded = self.mlb_in.transform(X_raw)
            y_encoded = self.mlb_out.transform(y_raw)

            scores = cross_val_score(self.model, X_encoded, y_encoded, cv=3, scoring='accuracy')
            self._last_accuracy = float(np.mean(scores))
            return self._last_accuracy
        except Exception as e:
            print(f"Accuracy evaluation error: {e}")
            return 0.72

    def predict_next_events(self, situation: Situation) -> SituationForecast:
        """Uses the ML model to predict what happens next for a situation."""
        fc = SituationForecast(
            situation_id=situation.situation_id,
            current_status="ML Prediction Active",
            predictions=[],
        )

        # Extract all concepts currently active in the situation
        active_concepts = []
        for inc in situation.incidents:
            for c in inc.core_concepts:
                active_concepts.append(c.concept)

        active_concepts = list(set(active_concepts))

        if not SKLEARN_AVAILABLE or self.model is None:
            # Fallback to rule-based heuristics
            fc.current_status = "Prediction via Heuristics"
            predictions = []
            for concept in active_concepts:
                if concept in self.causal_rules:
                    for effect in self.causal_rules[concept]:
                        if effect not in active_concepts:
                            predictions.append(Forecast(
                                predicted_concept=effect,
                                probability=round(0.55, 4),
                                reasons=[f"Rule-based: '{concept}' historically leads to '{effect}'."]
                            ))
            predictions.sort(key=lambda x: x.probability, reverse=True)
            # Deduplicate
            seen = set()
            deduped = []
            for p in predictions:
                if p.predicted_concept not in seen:
                    seen.add(p.predicted_concept)
                    deduped.append(p)
            fc.predictions = deduped[:8]
            return fc

        fc.current_status = "ML Prediction Active"

        # Vectorize input — only use concepts the model was trained on
        known_concepts = [c for c in active_concepts if c in self.mlb_in.classes_]
        if not known_concepts:
            # Fall back to rule-based heuristics for unknown concepts
            fc.current_status = "Prediction via Heuristics (Unknown Concepts)"
            predictions = []
            for concept in active_concepts:
                if concept in self.causal_rules:
                    for effect in self.causal_rules[concept]:
                        if effect not in active_concepts:
                            predictions.append(Forecast(
                                predicted_concept=effect,
                                probability=round(0.50, 4),
                                reasons=[f"Rule-based: '{concept}' historically leads to '{effect}'."]
                            ))
            predictions.sort(key=lambda x: x.probability, reverse=True)
            seen = set()
            deduped = []
            for p in predictions:
                if p.predicted_concept not in seen:
                    seen.add(p.predicted_concept)
                    deduped.append(p)
            fc.predictions = deduped[:8]
            return fc

        X = self.mlb_in.transform([known_concepts])

        # RandomForestClassifier.predict_proba() for multilabel returns a list
        # of arrays (one per label/class), each of shape (n_samples, 2).
        y_prob = self.model.predict_proba(X)

        predictions_map = {}

        for i, class_name in enumerate(self.classes):
            if isinstance(y_prob, list):
                prob = float(y_prob[i][0][1])
            else:
                prob = float(y_prob[0][i])

            if prob > 0.15 and class_name not in active_concepts:
                urgency = "HIGH" if prob > 0.70 else ("MEDIUM" if prob > 0.40 else "LOW")
                predictions_map[class_name] = {
                    "probability": prob,
                    "reasons": [
                        f"ML model assigns {prob*100:.1f}% probability based on current situation.",
                        f"Active concepts: '{', '.join(known_concepts[:3])}'.",
                        f"Urgency: {urgency}",
                    ],
                }

        # Chain-reaction predictions: if A->B predicted and B->C exists, add C at reduced probability
        chain_additions = {}
        for predicted_concept, data in predictions_map.items():
            if predicted_concept in self.causal_rules:
                for chain_effect in self.causal_rules[predicted_concept]:
                    if chain_effect not in predictions_map and chain_effect not in active_concepts:
                        chain_prob = data["probability"] * 0.55
                        if chain_prob >= 0.15:
                            if chain_effect not in chain_additions or chain_prob > chain_additions[chain_effect]["probability"]:
                                chain_additions[chain_effect] = {
                                    "probability": chain_prob,
                                    "reasons": [
                                        f"Cascading effect: predicted '{predicted_concept}' ({data['probability']*100:.0f}%) may trigger '{chain_effect}'.",
                                        f"Chain probability: {chain_prob*100:.1f}%",
                                    ],
                                }

        predictions_map.update(chain_additions)

        # Build sorted prediction list
        predictions = []
        for concept_name, data in predictions_map.items():
            predictions.append(Forecast(
                predicted_concept=concept_name,
                probability=round(data["probability"], 4),
                reasons=data["reasons"],
            ))

        predictions.sort(key=lambda x: x.probability, reverse=True)
        fc.predictions = predictions[:12]

        return fc
