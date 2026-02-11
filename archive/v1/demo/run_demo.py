#!/usr/bin/env python3
"""
Demo Runner for Parametric Insurance
Simulates end-to-end flow with realistic timing
"""
import sys
import os
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.fabric_client import FabricClient
from shared.eventgrid_client import EventGridClient
from shared.models import (
    OutageEvent, Location, OutageStatus, WeatherData,
    Policy, create_event_id
)
from shared.config import validate_config

# Demo scenarios
SCENARIOS = {
    "storm_seattle": {
        "name": "Seattle Thunderstorm Outage",
        "description": "Severe thunderstorm causes 3-hour power outage affecting downtown businesses",
        "location": {
            "city": "Seattle",
            "state": "WA",
            "zip_code": "98101",
            "latitude": 47.6097,
            "longitude": -122.3425
        },
        "outage": {
            "utility_name": "Seattle City Light",
            "affected_customers": 8420,
            "duration_minutes": 187,
            "cause": "storm_damage"
        },
        "weather": {
            "temperature_f": 42,
            "wind_speed_mph": 48,
            "wind_gust_mph": 62,
            "conditions": "Thunderstorms",
            "severe_weather_alert": True,
            "alert_type": "Severe Thunderstorm Warning",
            "lightning_strikes": 47
        },
        "expected_claims": 2  # BI-001, BI-002
    },
    
    "sf_earthquake": {
        "name": "San Francisco Minor Earthquake",
        "description": "4.2 magnitude earthquake causes brief power disruption",
        "location": {
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94111",
            "latitude": 37.7935,
            "longitude": -122.3989
        },
        "outage": {
            "utility_name": "PG&E",
            "affected_customers": 15234,
            "duration_minutes": 45,
            "cause": "earthquake"
        },
        "weather": {
            "temperature_f": 58,
            "wind_speed_mph": 12,
            "conditions": "Clear",
            "severe_weather_alert": False
        },
        "expected_claims": 1  # BI-007 (30 min threshold)
    },
    
    "ny_hurricane": {
        "name": "New York Hurricane Remnants",
        "description": "Hurricane remnants cause widespread 6-hour outage",
        "location": {
            "city": "New York",
            "state": "NY",
            "zip_code": "10022",
            "latitude": 40.7614,
            "longitude": -73.9776
        },
        "outage": {
            "utility_name": "Con Edison",
            "affected_customers": 42380,
            "duration_minutes": 358,
            "cause": "hurricane"
        },
        "weather": {
            "temperature_f": 68,
            "wind_speed_mph": 72,
            "wind_gust_mph": 95,
            "conditions": "Heavy Rain and Wind",
            "severe_weather_alert": True,
            "alert_type": "Hurricane Warning",
            "precipitation_inches": 4.2
        },
        "expected_claims": 2  # BI-010, BI-011
    }
}


class DemoRunner:
    """Runs demo scenarios with realistic timing"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.fabric_client = None
        self.eventgrid_client = None
    
    def log(self, message: str, level: str = "INFO"):
        """Print log message"""
        if self.verbose:
            timestamp = datetime.utcnow().strftime("%H:%M:%S")
            colors = {
                "INFO": "\033[94m",
                "SUCCESS": "\033[92m",
                "WARNING": "\033[93m",
                "ERROR": "\033[91m",
                "RESET": "\033[0m"
            }
            color = colors.get(level, colors["INFO"])
            reset = colors["RESET"]
            print(f"{color}[{timestamp}] {level}: {message}{reset}")
    
    def initialize_clients(self):
        """Initialize Fabric and Event Grid clients"""
        self.log("Initializing clients...")
        try:
            validate_config()
            self.fabric_client = FabricClient()
            self.eventgrid_client = EventGridClient()
            self.log("Clients initialized successfully", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to initialize clients: {e}", "ERROR")
            return False
    
    def create_simulated_outage(
        self,
        scenario: Dict[str, Any]
    ) -> OutageEvent:
        """Create simulated outage event"""
        self.log(f"Creating outage event: {scenario['name']}")
        
        location = Location(**scenario['location'])
        
        # Create outage event
        outage_start = datetime.utcnow() - timedelta(
            minutes=scenario['outage']['duration_minutes']
        )
        
        outage = OutageEvent(
            event_id=create_event_id(
                scenario['outage']['utility_name'],
                outage_start
            ),
            utility_name=scenario['outage']['utility_name'],
            location=location,
            affected_customers=scenario['outage']['affected_customers'],
            outage_start=outage_start,
            outage_end=datetime.utcnow(),
            duration_minutes=scenario['outage']['duration_minutes'],
            status=OutageStatus.RESOLVED,
            cause=scenario['outage']['cause'],
            reported_cause=scenario['outage']['cause'],
            data_source="demo_simulation"
        )
        
        # Save to Fabric
        self.fabric_client.insert_outage_event(outage)
        self.log(f"Outage event created: {outage.event_id}", "SUCCESS")
        
        return outage
    
    def create_simulated_weather(
        self,
        scenario: Dict[str, Any],
        outage: OutageEvent
    ):
        """Create simulated weather data"""
        if 'weather' not in scenario:
            return
        
        self.log("Creating weather data...")
        
        weather = WeatherData(
            location=outage.location,
            timestamp=outage.outage_start,
            **scenario['weather']
        )
        
        self.fabric_client.insert_weather_data(weather)
        self.log(f"Weather data created (Severity: {weather.severity_score()})", "SUCCESS")
    
    def run_scenario(self, scenario_name: str):
        """Run a complete demo scenario"""
        if scenario_name not in SCENARIOS:
            self.log(f"Unknown scenario: {scenario_name}", "ERROR")
            self.log(f"Available scenarios: {', '.join(SCENARIOS.keys())}")
            return False
        
        scenario = SCENARIOS[scenario_name]
        
        print("\n" + "="*80)
        print(f"DEMO SCENARIO: {scenario['name']}")
        print("="*80)
        print(f"{scenario['description']}\n")
        print(f"Location: {scenario['location']['city']}, {scenario['location']['state']}")
        print(f"Utility: {scenario['outage']['utility_name']}")
        print(f"Duration: {scenario['outage']['duration_minutes']} minutes")
        print(f"Affected: {scenario['outage']['affected_customers']:,} customers")
        print(f"Expected Claims: {scenario['expected_claims']}")
        print("="*80 + "\n")
        
        # Initialize
        if not self.initialize_clients():
            return False
        
        try:
            # Step 1: Create outage event
            self.log("STEP 1: Creating outage event in Fabric")
            outage = self.create_simulated_outage(scenario)
            time.sleep(2)
            
            # Step 2: Create weather data
            self.log("STEP 2: Creating weather data in Fabric")
            self.create_simulated_weather(scenario, outage)
            time.sleep(2)
            
            # Step 3: Find affected policies
            self.log("STEP 3: Finding affected policies")
            affected_policies = self.fabric_client.get_policies_in_zip(
                scenario['location']['zip_code']
            )
            self.log(f"Found {len(affected_policies)} policies in {scenario['location']['zip_code']}")
            
            for policy in affected_policies:
                self.log(f"  - {policy['business_name']} (Threshold: {policy['threshold_minutes']} min)")
            
            time.sleep(2)
            
            # Step 4: Publish outage detected event
            self.log("STEP 4: Publishing 'outage.detected' event to Event Grid")
            policy_ids = [p['policy_id'] for p in affected_policies]
            
            success = self.eventgrid_client.publish_outage_detected(
                outage_event=outage,
                affected_policies=policy_ids
            )
            
            if success:
                self.log("Event published successfully", "SUCCESS")
            else:
                self.log("Failed to publish event", "ERROR")
                return False
            
            time.sleep(3)
            
            # Step 5: Monitor for threshold evaluations
            self.log("STEP 5: Azure Functions processing events...")
            self.log("  → ThresholdEvaluator function triggered")
            self.log("  → AI Agent validating claims")
            self.log("  → Calculating payouts")
            
            # Give time for async processing
            for i in range(5, 0, -1):
                self.log(f"  Waiting for processing... {i}s")
                time.sleep(1)
            
            # Step 6: Check for created claims
            self.log("STEP 6: Checking for created claims")
            time.sleep(2)
            
            total_payout = 0
            for policy in affected_policies:
                claims = self.fabric_client.get_policy_claims(
                    policy['policy_id'],
                    days=1
                )
                
                if claims:
                    for claim in claims:
                        self.log(
                            f"  ✓ Claim {claim['claim_id']}: "
                            f"{claim['status']} - ${claim.get('payout_amount', 0):.2f}",
                            "SUCCESS"
                        )
                        total_payout += claim.get('payout_amount', 0) or 0
            
            # Summary
            print("\n" + "="*80)
            print("DEMO COMPLETE")
            print("="*80)
            print(f"Total Claims Processed: {len(claims) if claims else 0}")
            print(f"Total Payout Amount: ${total_payout:,.2f}")
            print("="*80 + "\n")
            
            self.log("Demo scenario completed successfully!", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Error running scenario: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Parametric Insurance Demo Scenarios"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        choices=list(SCENARIOS.keys()),
        default="storm_seattle",
        help="Demo scenario to run"
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available scenarios"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    
    args = parser.parse_args()
    
    if args.list_scenarios:
        print("\nAvailable Demo Scenarios:")
        print("="*80)
        for name, scenario in SCENARIOS.items():
            print(f"\n{name}:")
            print(f"  {scenario['name']}")
            print(f"  {scenario['description']}")
            print(f"  Location: {scenario['location']['city']}, {scenario['location']['state']}")
            print(f"  Expected Claims: {scenario['expected_claims']}")
        print("\n" + "="*80)
        return
    
    # Run scenario
    runner = DemoRunner(verbose=not args.quiet)
    success = runner.run_scenario(args.scenario)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
