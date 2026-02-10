"""
PRESTO Integration Module
Power Reliability Event Simulation Tool (PRESTO) for Parametric Insurance Demo

PRESTO simulates realistic power outages based on:
- Historical outage patterns
- Weather conditions
- Grid infrastructure
- Time of day/year patterns
- Geographic distribution
"""
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import math


@dataclass
class OutageSimulationConfig:
    """Configuration for outage simulation"""
    base_outage_rate: float = 0.05  # 5% chance per region per day
    weather_multiplier: float = 3.0  # 3x more likely during severe weather
    peak_hours: tuple = (16, 20)  # 4 PM - 8 PM most vulnerable
    seasonal_variance: float = 1.5  # 50% more outages in summer/winter
    min_duration_minutes: int = 15
    max_duration_minutes: int = 480  # 8 hours
    min_customers_affected: int = 100
    max_customers_affected: int = 50000


class PRESTO:
    """
    Power Reliability Event Simulation Tool
    Generates realistic power outage scenarios for testing
    """
    
    def __init__(self, config: Optional[OutageSimulationConfig] = None):
        self.config = config or OutageSimulationConfig()
        
        # US utility companies by region
        self.utilities = {
            "Pacific Northwest": [
                "Seattle City Light",
                "Portland General Electric",
                "Puget Sound Energy",
                "Tacoma Power"
            ],
            "California": [
                "Pacific Gas & Electric (PG&E)",
                "Southern California Edison",
                "San Diego Gas & Electric",
                "Los Angeles Department of Water and Power"
            ],
            "Southwest": [
                "Arizona Public Service",
                "Salt River Project",
                "NV Energy",
                "El Paso Electric"
            ],
            "Mountain": [
                "Xcel Energy",
                "Black Hills Energy",
                "Rocky Mountain Power"
            ],
            "Midwest": [
                "ComEd",
                "DTE Energy",
                "Duke Energy Ohio",
                "Consumers Energy"
            ],
            "South": [
                "Georgia Power",
                "Duke Energy Carolinas",
                "Florida Power & Light",
                "Entergy"
            ],
            "Texas": [
                "Oncor Electric Delivery",
                "CenterPoint Energy",
                "AEP Texas",
                "Texas-New Mexico Power"
            ],
            "Northeast": [
                "Con Edison",
                "National Grid",
                "PSEG",
                "Eversource Energy"
            ],
            "Mid-Atlantic": [
                "PECO",
                "BGE",
                "Pepco",
                "Dominion Energy"
            ]
        }
        
        # Major cities with coordinates and typical utility
        self.cities = [
            {"name": "Seattle", "state": "WA", "zip": "98101", "lat": 47.6062, "lon": -122.3321, "region": "Pacific Northwest"},
            {"name": "Portland", "state": "OR", "zip": "97201", "lat": 45.5152, "lon": -122.6784, "region": "Pacific Northwest"},
            {"name": "San Francisco", "state": "CA", "zip": "94111", "lat": 37.7935, "lon": -122.3989, "region": "California"},
            {"name": "Los Angeles", "state": "CA", "zip": "90012", "lat": 34.0522, "lon": -118.2437, "region": "California"},
            {"name": "San Diego", "state": "CA", "zip": "92101", "lat": 32.7157, "lon": -117.1611, "region": "California"},
            {"name": "Phoenix", "state": "AZ", "zip": "85001", "lat": 33.4484, "lon": -112.0740, "region": "Southwest"},
            {"name": "Las Vegas", "state": "NV", "zip": "89101", "lat": 36.1699, "lon": -115.1398, "region": "Southwest"},
            {"name": "Denver", "state": "CO", "zip": "80202", "lat": 39.7392, "lon": -104.9903, "region": "Mountain"},
            {"name": "Chicago", "state": "IL", "zip": "60601", "lat": 41.8781, "lon": -87.6298, "region": "Midwest"},
            {"name": "Detroit", "state": "MI", "zip": "48226", "lat": 42.3314, "lon": -83.0458, "region": "Midwest"},
            {"name": "Atlanta", "state": "GA", "zip": "30303", "lat": 33.7490, "lon": -84.3880, "region": "South"},
            {"name": "Miami", "state": "FL", "zip": "33101", "lat": 25.7617, "lon": -80.1918, "region": "South"},
            {"name": "Houston", "state": "TX", "zip": "77002", "lat": 29.7604, "lon": -95.3698, "region": "Texas"},
            {"name": "Dallas", "state": "TX", "zip": "75201", "lat": 32.7767, "lon": -96.7970, "region": "Texas"},
            {"name": "Austin", "state": "TX", "zip": "78701", "lat": 30.2672, "lon": -97.7431, "region": "Texas"},
            {"name": "New York", "state": "NY", "zip": "10022", "lat": 40.7614, "lon": -73.9776, "region": "Northeast"},
            {"name": "Boston", "state": "MA", "zip": "02101", "lat": 42.3601, "lon": -71.0589, "region": "Northeast"},
            {"name": "Philadelphia", "state": "PA", "zip": "19103", "lat": 39.9526, "lon": -75.1652, "region": "Mid-Atlantic"},
            {"name": "Washington", "state": "DC", "zip": "20001", "lat": 38.9072, "lon": -77.0369, "region": "Mid-Atlantic"}
        ]
        
        # Outage causes with probability weights
        self.outage_causes = {
            "storm_damage": 0.35,
            "equipment_failure": 0.25,
            "tree_contact": 0.15,
            "vehicle_accident": 0.08,
            "animal_contact": 0.07,
            "planned_maintenance": 0.05,
            "earthquake": 0.02,
            "heat_overload": 0.02,
            "unknown": 0.01
        }
    
    def generate_outage(
        self,
        location: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        weather_severity: str = "normal"
    ) -> Dict[str, Any]:
        """
        Generate a single realistic outage event
        
        Args:
            location: Specific location dict, or random if None
            timestamp: Outage start time, or current time if None
            weather_severity: "normal", "moderate", "severe", "extreme"
        
        Returns:
            Dictionary with outage details
        """
        # Select location
        if location is None:
            location = random.choice(self.cities)
        
        # Select utility for region
        utilities_in_region = self.utilities.get(location["region"], ["Local Utility"])
        utility_name = random.choice(utilities_in_region)
        
        # Determine timestamp
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Calculate duration based on cause and severity
        duration = self._calculate_duration(weather_severity)
        
        # Calculate affected customers based on time and location
        affected_customers = self._calculate_affected_customers(
            timestamp, 
            weather_severity,
            location
        )
        
        # Select cause
        cause = self._select_cause(weather_severity)
        
        # Generate event ID
        event_id = f"PRESTO-{location['state']}-{timestamp.strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        
        return {
            "event_id": event_id,
            "utility_name": utility_name,
            "location": location,
            "zip_code": location["zip"],
            "latitude": location["lat"],
            "longitude": location["lon"],
            "city": location["name"],
            "state": location["state"],
            "affected_customers": affected_customers,
            "outage_start": timestamp,
            "outage_end": timestamp + timedelta(minutes=duration),
            "duration_minutes": duration,
            "cause": cause,
            "reported_cause": cause,
            "status": "resolved",
            "data_source": "PRESTO",
            "simulation_params": {
                "weather_severity": weather_severity,
                "peak_hour": self._is_peak_hour(timestamp),
                "seasonal_factor": self._get_seasonal_factor(timestamp)
            }
        }
    
    def generate_outage_scenario(
        self,
        scenario_type: str = "normal_day"
    ) -> List[Dict[str, Any]]:
        """
        Generate a complete outage scenario with multiple events
        
        Args:
            scenario_type: Type of scenario
                - "normal_day": Typical day, 2-5 outages
                - "severe_weather": Storm event, 10-20 outages
                - "heat_wave": Summer heat stress, 5-15 outages
                - "winter_storm": Ice/snow event, 15-30 outages
                - "equipment_failure": Cascading failures, 3-8 outages
        
        Returns:
            List of outage events
        """
        scenarios = {
            "normal_day": {
                "count": (2, 5),
                "weather": "normal",
                "time_spread_hours": 24,
                "geographic_spread": "random"
            },
            "severe_weather": {
                "count": (10, 20),
                "weather": "severe",
                "time_spread_hours": 6,
                "geographic_spread": "clustered"
            },
            "heat_wave": {
                "count": (5, 15),
                "weather": "moderate",
                "time_spread_hours": 8,
                "geographic_spread": "regional"
            },
            "winter_storm": {
                "count": (15, 30),
                "weather": "extreme",
                "time_spread_hours": 12,
                "geographic_spread": "regional"
            },
            "equipment_failure": {
                "count": (3, 8),
                "weather": "normal",
                "time_spread_hours": 4,
                "geographic_spread": "clustered"
            }
        }
        
        config = scenarios.get(scenario_type, scenarios["normal_day"])
        
        # Generate outages
        outages = []
        num_outages = random.randint(*config["count"])
        base_time = datetime.utcnow()
        
        # Select locations based on geographic spread
        if config["geographic_spread"] == "random":
            locations = [random.choice(self.cities) for _ in range(num_outages)]
        elif config["geographic_spread"] == "clustered":
            # Pick one city and add nearby variations
            base_city = random.choice(self.cities)
            locations = [base_city] * num_outages
        else:  # regional
            # Pick one region
            region = random.choice(list(self.utilities.keys()))
            region_cities = [c for c in self.cities if c["region"] == region]
            locations = [random.choice(region_cities) for _ in range(num_outages)]
        
        # Generate each outage
        for i, location in enumerate(locations):
            # Spread outages over time
            time_offset = random.randint(0, config["time_spread_hours"] * 60)
            outage_time = base_time + timedelta(minutes=time_offset)
            
            outage = self.generate_outage(
                location=location,
                timestamp=outage_time,
                weather_severity=config["weather"]
            )
            
            outages.append(outage)
        
        return outages
    
    def _calculate_duration(self, weather_severity: str) -> int:
        """Calculate outage duration based on severity"""
        base_duration = random.randint(
            self.config.min_duration_minutes,
            self.config.max_duration_minutes
        )
        
        severity_multipliers = {
            "normal": 0.5,
            "moderate": 1.0,
            "severe": 1.5,
            "extreme": 2.0
        }
        
        multiplier = severity_multipliers.get(weather_severity, 1.0)
        duration = int(base_duration * multiplier)
        
        # Add some randomness (log-normal distribution)
        duration = int(duration * random.lognormvariate(0, 0.3))
        
        return max(
            self.config.min_duration_minutes,
            min(duration, self.config.max_duration_minutes)
        )
    
    def _calculate_affected_customers(
        self,
        timestamp: datetime,
        weather_severity: str,
        location: Dict[str, Any]
    ) -> int:
        """Calculate number of affected customers"""
        base_customers = random.randint(
            self.config.min_customers_affected,
            self.config.max_customers_affected
        )
        
        # Peak hour adjustment
        if self._is_peak_hour(timestamp):
            base_customers = int(base_customers * 1.3)
        
        # Weather severity adjustment
        severity_multipliers = {
            "normal": 0.3,
            "moderate": 0.7,
            "severe": 1.2,
            "extreme": 2.0
        }
        multiplier = severity_multipliers.get(weather_severity, 1.0)
        
        customers = int(base_customers * multiplier)
        
        # Add log-normal variation
        customers = int(customers * random.lognormvariate(0, 0.5))
        
        return max(
            self.config.min_customers_affected,
            min(customers, self.config.max_customers_affected)
        )
    
    def _select_cause(self, weather_severity: str) -> str:
        """Select outage cause based on weather severity"""
        if weather_severity in ["severe", "extreme"]:
            # Weather-related causes more likely
            weather_causes = {
                "storm_damage": 0.60,
                "tree_contact": 0.20,
                "equipment_failure": 0.15,
                "unknown": 0.05
            }
            causes = weather_causes
        else:
            causes = self.outage_causes
        
        # Weighted random selection
        rand = random.random()
        cumulative = 0
        for cause, probability in causes.items():
            cumulative += probability
            if rand <= cumulative:
                return cause
        
        return "unknown"
    
    def _is_peak_hour(self, timestamp: datetime) -> bool:
        """Check if timestamp is during peak hours"""
        hour = timestamp.hour
        return self.config.peak_hours[0] <= hour <= self.config.peak_hours[1]
    
    def _get_seasonal_factor(self, timestamp: datetime) -> float:
        """Get seasonal adjustment factor"""
        month = timestamp.month
        
        # Higher outage rates in summer (AC load) and winter (heating)
        if month in [6, 7, 8, 12, 1, 2]:
            return self.config.seasonal_variance
        return 1.0
    
    def generate_continuous_simulation(
        self,
        duration_days: int = 30,
        outages_per_day: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate continuous outage simulation over multiple days
        
        Args:
            duration_days: Number of days to simulate
            outages_per_day: Average outages per day
        
        Returns:
            List of outage events over time period
        """
        outages = []
        start_date = datetime.utcnow() - timedelta(days=duration_days)
        
        for day in range(duration_days):
            # Vary number of outages per day
            num_outages = max(1, int(random.gauss(outages_per_day, 2)))
            
            for _ in range(num_outages):
                # Random time during the day
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                outage_time = start_date + timedelta(
                    days=day,
                    hours=hour,
                    minutes=minute
                )
                
                # Random weather severity (mostly normal)
                weather = random.choices(
                    ["normal", "moderate", "severe", "extreme"],
                    weights=[0.70, 0.20, 0.08, 0.02]
                )[0]
                
                outage = self.generate_outage(
                    timestamp=outage_time,
                    weather_severity=weather
                )
                
                outages.append(outage)
        
        # Sort by time
        outages.sort(key=lambda x: x["outage_start"])
        
        return outages


# Convenience functions
def generate_realistic_outage(**kwargs) -> Dict[str, Any]:
    """Quick function to generate a single realistic outage"""
    presto = PRESTO()
    return presto.generate_outage(**kwargs)


def generate_scenario(scenario_type: str = "normal_day") -> List[Dict[str, Any]]:
    """Quick function to generate a scenario"""
    presto = PRESTO()
    return presto.generate_outage_scenario(scenario_type)


def generate_historical_data(days: int = 30) -> List[Dict[str, Any]]:
    """Quick function to generate historical outage data"""
    presto = PRESTO()
    return presto.generate_continuous_simulation(duration_days=days)


# Example usage and testing
if __name__ == "__main__":
    presto = PRESTO()
    
    print("="*70)
    print("PRESTO - Power Reliability Event Simulation Tool")
    print("="*70)
    print()
    
    # Example 1: Single outage
    print("Example 1: Single realistic outage")
    print("-"*70)
    outage = presto.generate_outage(weather_severity="severe")
    print(json.dumps(outage, indent=2, default=str))
    print()
    
    # Example 2: Severe weather scenario
    print("Example 2: Severe weather scenario")
    print("-"*70)
    scenario = presto.generate_outage_scenario("severe_weather")
    print(f"Generated {len(scenario)} outages")
    for i, outage in enumerate(scenario[:3], 1):
        print(f"{i}. {outage['utility_name']} - {outage['city']}, {outage['state']}")
        print(f"   {outage['affected_customers']:,} customers, {outage['duration_minutes']} minutes")
    print()
    
    # Example 3: Historical simulation
    print("Example 3: 7-day historical simulation")
    print("-"*70)
    historical = presto.generate_continuous_simulation(duration_days=7, outages_per_day=5)
    print(f"Generated {len(historical)} outages over 7 days")
    print(f"Average per day: {len(historical) / 7:.1f}")
    print()
    
    # Statistics
    total_customers = sum(o['affected_customers'] for o in historical)
    avg_duration = sum(o['duration_minutes'] for o in historical) / len(historical)
    print(f"Total customers affected: {total_customers:,}")
    print(f"Average outage duration: {avg_duration:.1f} minutes")
