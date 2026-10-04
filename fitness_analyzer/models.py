from statistics import mean


# Store the participant's normal measurements.
class ReferenceMeasurements:
    def __init__(self, heart_rate, skin_response, temperature):
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature

    @property
    def heart_rate(self):
        return self._heart_rate

    @heart_rate.setter
    def heart_rate(self, value):
        if not 30 <= value <= 150:
            raise ValueError("baseline heart rate must be between 30 and 150")
        self._heart_rate = value

    def values(self):
        return {
            "heart_rate": self.heart_rate,
            "skin_response": self.skin_response,
            "temperature": self.temperature,
        }


# Store a participant and their reference measurements.
class Participant:
    def __init__(self, participant_id, name, reference):
        self.participant_id = participant_id
        self.name = name
        self.reference = reference


# Store one valid sensor reading.
class Observation:
    def __init__(self, data):
        self.__dict__.update(data)


# Calculate average, minimum and maximum values.
def summary(readings):
    result = {}
    fields = ("heart_rate", "skin_response", "temperature", "activity_level", "signal_quality")

    for field in fields:
        values = [getattr(reading, field) for reading in readings]
        result[field] = {
            "average": round(mean(values), 2),
            "minimum": min(values),
            "maximum": max(values),
        }

    return result


# Check if heart rate and activity decrease at the end.
def recovery(readings):
    if len(readings) < 4:
        return False

    size = max(1, len(readings) // 3)
    before = readings[-2 * size:-size]
    end = readings[-size:]
    heart_rate_drop = mean(reading.heart_rate for reading in before) 
    - mean(reading.heart_rate for reading in end)

    activity_drop = mean(reading.activity_level for reading in before) 
    - mean(reading.activity_level for reading in end)
    return heart_rate_drop >= 8 and activity_drop >= 0.15


# Classify the session.
def classify(data, difference, is_recovering):
    if is_recovering:
        return "recovering", "heart rate and activity decreased at the end"
    if data["activity_level"]["average"] < 0.20 and difference["heart_rate"] < 15:
        return "resting", "low activity and heart rate close to baseline"
    if data["activity_level"]["average"] >= 0.65 or difference["heart_rate"] >= 55:
        return "high activity", "high activity or large heart-rate increase"
    return "moderate activity", "activity exceeds the resting range"


# Store one participant and all readings in one session.
class FitnessSession:
    MIN_READINGS = 3

    def __init__(self, session_id, participant):
        self.session_id = session_id
        self.participant = participant
        self.observations = []

    def add(self, observation):
        self.observations.append(observation)

    def analyse(self):
        observations = sorted(self.observations, key=lambda observation: observation.timestamp)
        result = {
            "session_id": self.session_id,
            "participant_id": self.participant.participant_id,
            "participant_name": self.participant.name,
            "usable_observations": len(observations),
        }

        if len(observations) < self.MIN_READINGS:
            result["classification"] = "insufficient data"
            result["reason"] = "fewer than 3 usable observations"
            result["recovery_detected"] = False
            result["summary"] = {}
            result["reference_difference"] = {}
            return result

        data = summary(observations)
        difference = {}
        for field, baseline in self.participant.reference.values().items():
            difference[field] = round(data[field]["average"] - baseline, 2)

        is_recovering = recovery(observations)
        label, reason = classify(data, difference, is_recovering)
        result["classification"] = label
        result["reason"] = reason
        result["recovery_detected"] = is_recovering
        result["summary"] = data
        result["reference_difference"] = difference
        return result
