"""
Microsoft Foundry AI Agent: Claims Validator
Intelligent claim validation using multi-source correlation
"""
import os
import sys
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.models import AIValidationResult
from shared.config import foundry_config, policy_config


# In production, this would use the actual Microsoft Foundry SDK
# For now, we'll simulate with Azure OpenAI API
try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI SDK not available - using rule-based fallback")


class ClaimsValidatorAgent:
    """
    AI Agent for validating parametric insurance claims
    
    Uses multi-source data correlation and reasoning to:
    - Validate claim legitimacy
    - Assess weather severity
    - Detect fraud patterns
    - Calculate appropriate payouts
    """
    
    def __init__(self):
        """Initialize the agent with Foundry configuration"""
        self.endpoint = foundry_config.endpoint
        self.api_key = foundry_config.api_key
        self.model = foundry_config.model
        self.max_tokens = foundry_config.max_tokens
        self.temperature = foundry_config.temperature
        
        if OPENAI_AVAILABLE and self.endpoint and self.api_key:
            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version="2024-02-01"
            )
        else:
            self.client = None
    
    def _build_prompt(
        self,
        policy: Dict[str, Any],
        outage: Dict[str, Any],
        weather: Optional[Dict[str, Any]] = None,
        social_signals: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build the validation prompt for the AI agent"""
        
        prompt = f"""You are an expert parametric insurance claims validator specializing in business interruption claims caused by power outages.

Your task is to validate a claim and determine the appropriate payout based on objective data sources.

POLICY DETAILS:
- Policy ID: {policy['policy_id']}
- Business: {policy['business_name']}
- Location: {policy['zip_code']} (Lat: {policy.get('latitude')}, Lon: {policy.get('longitude')})
- Threshold: {policy['threshold_minutes']} minutes
- Hourly Rate: ${policy['hourly_rate']}/hour
- Maximum Payout: ${policy['max_payout']}

OUTAGE EVENT:
- Event ID: {outage['event_id']}
- Utility: {outage['utility_name']}
- Affected Customers: {outage['affected_customers']:,}
- Outage Start: {outage['outage_start']}
- Duration: {outage.get('duration_minutes', 'Unknown')} minutes
- Reported Cause: {outage.get('reported_cause', 'Unknown')}
- Status: {outage['status']}
"""
        
        if weather:
            prompt += f"""
WEATHER DATA:
- Temperature: {weather.get('temperature_f')}°F
- Wind Speed: {weather.get('wind_speed_mph')} mph
- Wind Gusts: {weather.get('wind_gust_mph')} mph
- Conditions: {weather.get('conditions')}
- Severe Weather Alert: {weather.get('severe_weather_alert', False)}
- Alert Type: {weather.get('alert_type')}
- Lightning Strikes: {weather.get('lightning_strikes')}
"""
        
        if social_signals and len(social_signals) > 0:
            prompt += f"""
SOCIAL MEDIA VERIFICATION:
- Twitter mentions: {len(social_signals)} posts about outage in area
- Sample posts: {json.dumps([s.get('text', '')[:100] for s in social_signals[:3]], indent=2)}
"""
        
        prompt += """
VALIDATION TASKS:

1. **Location Verification**: Confirm the business location is within the outage zone
2. **Duration Check**: Verify outage duration exceeds the policy threshold
3. **Cause Assessment**: Determine if this was an emergency outage (covered) vs planned maintenance (not covered)
4. **Weather Severity**: Assess weather as a contributing factor and determine severity multiplier:
   - Low severity (no alert, wind <25mph): 1.0x
   - Medium severity (wind 25-40mph): 1.1x
   - High severity (wind 40-55mph or weather alert): 1.2x
   - Severe (wind >55mph or severe weather alert): 1.5x

5. **Fraud Detection**: Check for fraud signals:
   - Unusual claim frequency (>5 claims in 30 days)
   - Inconsistent data (outage timing doesn't match weather)
   - Geographic mismatch
   - Duplicate claims

6. **Payout Calculation**:
   - Base payout = (duration - threshold) / 60 * hourly_rate
   - Adjusted payout = base_payout * severity_multiplier
   - Final payout = min(adjusted_payout, max_payout)

OUTPUT FORMAT (respond with valid JSON only):
{
    "decision": "approved" or "denied",
    "confidence_score": 0.0 to 1.0,
    "payout_amount": dollar amount,
    "reasoning": "detailed explanation of your decision",
    "evidence": [
        {"type": "duration", "value": "X minutes"},
        {"type": "weather", "value": "severity level"},
        {"type": "social_verification", "value": "X mentions found"}
    ],
    "fraud_signals": ["signal1", "signal2"] or [],
    "severity_assessment": "low" | "medium" | "high" | "severe",
    "weather_factor": multiplier value
}

Provide your analysis and decision now:
"""
        
        return prompt
    
    def _parse_agent_response(self, response_text: str) -> AIValidationResult:
        """Parse the agent's JSON response into AIValidationResult"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            data = json.loads(response_text.strip())
            
            return AIValidationResult(
                decision=data['decision'],
                confidence_score=float(data['confidence_score']),
                payout_amount=float(data['payout_amount']),
                reasoning=data['reasoning'],
                evidence=data.get('evidence', []),
                fraud_signals=data.get('fraud_signals', []),
                severity_assessment=data['severity_assessment'],
                weather_factor=float(data['weather_factor'])
            )
            
        except Exception as e:
            print(f"Error parsing agent response: {e}")
            print(f"Response text: {response_text}")
            raise
    
    def validate_claim(
        self,
        policy: Dict[str, Any],
        outage: Dict[str, Any],
        weather: Optional[Dict[str, Any]] = None,
        social_signals: Optional[List[Dict[str, Any]]] = None
    ) -> AIValidationResult:
        """
        Validate a claim using the AI agent
        
        Args:
            policy: Policy data
            outage: Outage event data
            weather: Weather data (optional)
            social_signals: Social media signals (optional)
            
        Returns:
            AIValidationResult with decision and reasoning
        """
        
        if not self.client:
            # Fallback to rule-based validation
            return self._rule_based_validation(policy, outage, weather)
        
        try:
            # Build prompt
            prompt = self._build_prompt(policy, outage, weather, social_signals)
            
            # Call AI model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert parametric insurance claims validator. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            result = self._parse_agent_response(response_text)
            
            print(f"AI Agent Decision: {result.decision}")
            print(f"Confidence: {result.confidence_score:.2f}")
            print(f"Payout: ${result.payout_amount:.2f}")
            print(f"Reasoning: {result.reasoning[:200]}...")
            
            return result
            
        except Exception as e:
            print(f"Error in AI agent validation: {e}")
            # Fallback to rule-based
            return self._rule_based_validation(policy, outage, weather)
    
    def _rule_based_validation(
        self,
        policy: Dict[str, Any],
        outage: Dict[str, Any],
        weather: Optional[Dict[str, Any]] = None
    ) -> AIValidationResult:
        """
        Rule-based validation fallback
        """
        # Calculate duration
        if outage.get('duration_minutes'):
            duration = outage['duration_minutes']
        else:
            outage_start = datetime.fromisoformat(str(outage['outage_start']).replace('Z', '+00:00'))
            duration = (datetime.utcnow() - outage_start).total_seconds() / 60
        
        threshold = policy['threshold_minutes']
        
        # Check threshold
        if duration <= threshold:
            return AIValidationResult(
                decision="deny",
                confidence_score=0.95,
                payout_amount=0.0,
                reasoning=f"Outage duration ({duration:.0f} min) does not exceed policy threshold ({threshold} min)",
                evidence=[
                    {"type": "duration", "value": f"{duration:.0f} minutes"},
                    {"type": "threshold", "value": f"{threshold} minutes"}
                ],
                fraud_signals=[],
                severity_assessment="low",
                weather_factor=1.0
            )
        
        # Calculate payout
        hours_over = (duration - threshold) / 60
        base_payout = hours_over * policy['hourly_rate']
        
        # Weather severity
        severity_multiplier = 1.0
        severity = "medium"
        
        if weather:
            if weather.get('severe_weather_alert'):
                severity_multiplier = 1.5
                severity = "severe"
            elif weather.get('wind_speed_mph', 0) > 40:
                severity_multiplier = 1.2
                severity = "high"
            elif weather.get('wind_speed_mph', 0) > 25:
                severity_multiplier = 1.1
                severity = "medium"
        
        final_payout = min(
            base_payout * severity_multiplier,
            policy['max_payout']
        )
        
        return AIValidationResult(
            decision="approve",
            confidence_score=0.85,
            payout_amount=final_payout,
            reasoning=f"Threshold exceeded by {hours_over:.1f} hours. Weather severity: {severity}. Applied {severity_multiplier}x multiplier.",
            evidence=[
                {"type": "duration", "value": f"{duration:.0f} minutes"},
                {"type": "hours_over_threshold", "value": f"{hours_over:.1f} hours"},
                {"type": "weather_severity", "value": severity},
                {"type": "base_payout", "value": f"${base_payout:.2f}"},
                {"type": "severity_multiplier", "value": f"{severity_multiplier}x"}
            ],
            fraud_signals=[],
            severity_assessment=severity,
            weather_factor=severity_multiplier
        )


# Global agent instance
_agent = None


def get_agent() -> ClaimsValidatorAgent:
    """Get or create the singleton agent instance"""
    global _agent
    if _agent is None:
        _agent = ClaimsValidatorAgent()
    return _agent


def validate_claim(
    policy: Dict[str, Any],
    outage: Dict[str, Any],
    weather: Optional[Dict[str, Any]] = None,
    social_signals: Optional[List[Dict[str, Any]]] = None
) -> AIValidationResult:
    """
    Convenience function to validate a claim
    
    Args:
        policy: Policy data
        outage: Outage event data
        weather: Weather data (optional)
        social_signals: Social media signals (optional)
        
    Returns:
        AIValidationResult
    """
    agent = get_agent()
    return agent.validate_claim(policy, outage, weather, social_signals)


# For testing
if __name__ == "__main__":
    # Test data
    test_policy = {
        "policy_id": "BI-001",
        "business_name": "Downtown Coffee Co",
        "zip_code": "98101",
        "latitude": 47.6062,
        "longitude": -122.3321,
        "threshold_minutes": 120,
        "hourly_rate": 500,
        "max_payout": 50000
    }
    
    test_outage = {
        "event_id": "OUT-SEATTLECITYLIGHT-20260209",
        "utility_name": "Seattle City Light",
        "affected_customers": 8420,
        "outage_start": "2026-02-09T14:23:00Z",
        "duration_minutes": 187,
        "status": "active",
        "reported_cause": "storm_damage"
    }
    
    test_weather = {
        "temperature_f": 42,
        "wind_speed_mph": 48,
        "wind_gust_mph": 62,
        "conditions": "Thunderstorms",
        "severe_weather_alert": True,
        "alert_type": "Severe Thunderstorm Warning",
        "lightning_strikes": 47
    }
    
    result = validate_claim(test_policy, test_outage, test_weather)
    
    print("\n" + "="*60)
    print("CLAIM VALIDATION RESULT")
    print("="*60)
    print(f"Decision: {result.decision.upper()}")
    print(f"Confidence: {result.confidence_score:.1%}")
    print(f"Payout Amount: ${result.payout_amount:,.2f}")
    print(f"Severity: {result.severity_assessment}")
    print(f"Weather Factor: {result.weather_factor}x")
    print(f"\nReasoning:\n{result.reasoning}")
    print("\nEvidence:")
    for evidence in result.evidence:
        print(f"  - {evidence['type']}: {evidence['value']}")
    if result.fraud_signals:
        print(f"\nFraud Signals: {', '.join(result.fraud_signals)}")
    print("="*60)
