import json
import time
import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from pathlib import Path

@dataclass
class ReservoirAdjustment:
    timestamp: float
    ph_before: float
    ph_after: float
    ec_before: float
    ec_after: float
    ph_up_runtime: float
    ph_down_runtime: float
    fert_a_runtime: float
    fert_b_runtime: float
    volume_liters: float = 100.0  # Default to 100L if not specified

class ReservoirLogger:
    INITIAL_PH_CHANGE_RATE = 0.1  # Very conservative: 0.001 pH change per second
    INITIAL_EC_CHANGE_RATE = 0.1    # 2 EC points per second
    MIN_ADJUSTMENT_TIME = 1.0       # Minimum time to run motors
    MAX_ADJUSTMENT_TIME = 10.0      # Maximum time to run motors
    SAFETY_MARGIN = 0.2             # 20% safety margin
    DEFAULT_VOLUME = 100.0          # Default volume in liters
    
    def __init__(self, log_file: str = "reservoir_history.json"):
        self.log_file = Path(log_file)
        self.adjustments: List[ReservoirAdjustment] = []
        self.load_history()
        
        # Calibration parameters with conservative initial values
        self.ph_buffer_capacity = self.INITIAL_PH_CHANGE_RATE
        self.ec_response_factor = self.INITIAL_EC_CHANGE_RATE
        self._volume_liters = None  # Make volume optional
    
    @property
    def volume_liters(self) -> float:
        """Get the current volume, returning default if not set"""
        return self._volume_liters if self._volume_liters is not None else self.DEFAULT_VOLUME
    
    @volume_liters.setter
    def volume_liters(self, value: Optional[float]):
        """Set the current volume, allowing None to use default"""
        self._volume_liters = value if value is not None else None
    
    def load_history(self):
        """Load historical adjustment data from JSON file"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.adjustments = [ReservoirAdjustment(**adj) for adj in data]
                print(f"Loaded {len(self.adjustments)} historical adjustments")
            except Exception as e:
                print(f"Error loading history: {e}")
                self.adjustments = []
        else:
            print("No history file found - starting with conservative initial values")
            self.adjustments = []
    
    def save_history(self):
        """Save adjustment history to JSON file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump([vars(adj) for adj in self.adjustments], f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def log_adjustment(self, adjustment: ReservoirAdjustment):
        """Log a new adjustment and update calibration"""
        self.adjustments.append(adjustment)
        self.save_history()
        self.update_calibration()
    
    def calculate_ph_buffer_capacity(self) -> float:
        """Calculate pH buffer capacity based on historical data"""
        if len(self.adjustments) < 5:
            return self.INITIAL_PH_CHANGE_RATE
        
        recent_adjustments = self.adjustments[-20:]  # Use last 20 adjustments
        
        # Calculate pH change per second of motor runtime
        ph_changes = []
        for adj in recent_adjustments:
            total_runtime = adj.ph_up_runtime + adj.ph_down_runtime
            if total_runtime > 0:
                ph_change = abs(adj.ph_after - adj.ph_before)
                change_per_second = ph_change / total_runtime
                ph_changes.append(change_per_second)
        
        if not ph_changes:
            return self.INITIAL_PH_CHANGE_RATE
        
        # Use median to avoid outliers, but ensure it's not too aggressive
        calculated_rate = np.median(ph_changes)
        return min(calculated_rate, self.INITIAL_PH_CHANGE_RATE * 10)
    
    def calculate_ec_response(self) -> float:
        """Calculate EC response factor based on historical data"""
        if len(self.adjustments) < 5:
            return self.INITIAL_EC_CHANGE_RATE
        
        recent_adjustments = self.adjustments[-20:]
        
        # Calculate EC change per second of fertilizer runtime
        ec_changes = []
        for adj in recent_adjustments:
            total_runtime = adj.fert_a_runtime + adj.fert_b_runtime
            if total_runtime > 0:
                ec_change = adj.ec_after - adj.ec_before
                change_per_second = ec_change / total_runtime
                ec_changes.append(change_per_second)
        
        if not ec_changes:
            return self.INITIAL_EC_CHANGE_RATE
        
        calculated_rate = np.median(ec_changes)
        return min(calculated_rate, self.INITIAL_EC_CHANGE_RATE * 5)
    
    def update_calibration(self):
        """Update calibration factors based on historical data"""
        self.ph_buffer_capacity = self.calculate_ph_buffer_capacity()
        self.ec_response_factor = self.calculate_ec_response()
    
    def get_recommended_runtime(self, 
                              current_ph: float, 
                              target_ph: float, 
                              current_ec: float, 
                              target_ec: float) -> Dict[str, float]:
        """
        Calculate recommended motor runtime based on current calibration
        
        Returns:
            Dict with recommended runtime for each motor in seconds
        """
        recommendations = {
            'ph_up': 0.0,
            'ph_down': 0.0,
            'fert_a': 0.0,
            'fert_b': 0.0
        }
        
        # pH adjustment - extra cautious approach
        ph_diff = target_ph - current_ph
        if abs(ph_diff) > 0.1:  # Only adjust if difference is significant
            # For pH, start very conservatively if no history
            if len(self.adjustments) < 5:
                print("Warning: No historical data - using very conservative pH adjustment")
                # Limit initial pH adjustments to small steps
                ph_diff = max(min(ph_diff, 0.2), -0.2)
            
            # Consider buffer capacity and volume
            volume_factor = 100 / self.volume_liters
            required_time = abs(ph_diff) / (self.ph_buffer_capacity * volume_factor)
            
            # Apply safety margin
            required_time *= self.SAFETY_MARGIN
            
            # Enforce minimum and maximum runtime
            required_time = max(self.MIN_ADJUSTMENT_TIME, 
                              min(required_time, self.MAX_ADJUSTMENT_TIME))
            
            if ph_diff > 0:
                recommendations['ph_up'] = required_time
            else:
                recommendations['ph_down'] = required_time
        
        # EC adjustment
        ec_diff = target_ec - current_ec
        if abs(ec_diff) > 50:  # Only adjust if difference is significant
            # For EC, also be conservative without history
            if len(self.adjustments) < 5:
                print("Warning: No historical data - using conservative EC adjustment")
                # Limit initial EC adjustments
                ec_diff = max(min(ec_diff, 200), -200)
            
            # Consider response factor and volume
            volume_factor = 100 / self.volume_liters
            required_time = abs(ec_diff) / (self.ec_response_factor * volume_factor)
            
            # Apply safety margin
            required_time *= self.SAFETY_MARGIN
            
            # Enforce minimum and maximum runtime
            required_time = max(self.MIN_ADJUSTMENT_TIME, 
                              min(required_time, self.MAX_ADJUSTMENT_TIME))
            
            if ec_diff > 0:
                # Split between part A and B
                recommendations['fert_a'] = required_time / 2
                recommendations['fert_b'] = required_time / 2
        
        return recommendations
    
    def get_statistics(self) -> Dict:
        """Get statistical information about adjustments"""
        if not self.adjustments:
            return {
                'total_adjustments': 0,
                'current_ph_buffer_capacity': self.INITIAL_PH_CHANGE_RATE,
                'current_ec_response_factor': self.INITIAL_EC_CHANGE_RATE,
                'average_ph_change': 0.0,
                'average_ec_change': 0.0,
                'last_24h_adjustments': 0,
                'data_confidence': 'low' if len(self.adjustments) < 5 else 'medium' if len(self.adjustments) < 20 else 'high'
            }
        
        stats = {
            'total_adjustments': len(self.adjustments),
            'current_ph_buffer_capacity': self.ph_buffer_capacity,
            'current_ec_response_factor': self.ec_response_factor,
            'average_ph_change': 0.0,
            'average_ec_change': 0.0,
            'last_24h_adjustments': 0,
            'data_confidence': 'low' if len(self.adjustments) < 5 else 'medium' if len(self.adjustments) < 20 else 'high'
        }
        
        # Calculate 24h statistics
        now = time.time()
        last_24h = [adj for adj in self.adjustments 
                   if now - adj.timestamp < 24 * 3600]
        
        if last_24h:
            stats['last_24h_adjustments'] = len(last_24h)
            stats['average_ph_change'] = np.mean([abs(adj.ph_after - adj.ph_before) 
                                                for adj in last_24h])
            stats['average_ec_change'] = np.mean([abs(adj.ec_after - adj.ec_before) 
                                                for adj in last_24h])
        
        return stats 