"""
Mobility Data Processor - processes real vehicular mobility datasets.
Supports Porto Taxi, TAPASCologne, and similar trajectory-based datasets.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from src.fog_node import FogNode


class MobilityProcessor:
    """Processes real mobility datasets to extract fog node characteristics."""
    
    @staticmethod
    def load_porto_dataset(csv_file: str) -> pd.DataFrame:
        """
        Load Porto Taxi or similar trajectory dataset.
        
        Expected columns: vehicle_id, timestamp, latitude, longitude, distance, duration
        Or: vehicle_id, timestamp, speed
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            DataFrame with mobility data
        """
        try:
            df = pd.read_csv(csv_file)
            print(f"✓ Loaded {len(df)} records from {csv_file}")
            return df
        except Exception as e:
            print(f"Error loading dataset: {e}")
            raise
    
    @staticmethod
    def compute_speed_from_trajectory(df: pd.DataFrame, 
                                     distance_col: str = 'distance',
                                     duration_col: str = 'duration') -> pd.Series:
        """
        Compute speed from distance and duration.
        
        Args:
            df: DataFrame with trajectory data
            distance_col: Column name for distance
            duration_col: Column name for duration
            
        Returns:
            Series with computed speeds
        """
        if distance_col in df.columns and duration_col in df.columns:
            # Avoid division by zero
            df['speed'] = df[distance_col] / (df[duration_col] + 0.001)  # Add small epsilon
            return df['speed']
        elif 'speed' in df.columns:
            return df['speed']
        else:
            raise ValueError(f"Need either 'speed' column or '{distance_col}' and '{duration_col}' columns")
    
    @staticmethod
    def compute_trust_from_mobility_pattern(speeds: pd.Series, 
                                           vehicle_id: Optional[str] = None) -> float:
        """
        Compute trust score from mobility pattern (speed consistency).
        
        Trust is based on:
        - Speed consistency (lower variance = higher trust)
        - Average speed (moderate speeds = higher trust)
        
        Args:
            speeds: Series of speed values for a vehicle
            vehicle_id: Optional vehicle identifier for logging
            
        Returns:
            Trust score between 0 and 1
        """
        if len(speeds) == 0:
            return 0.5  # Default trust
        
        avg_speed = speeds.mean()
        speed_std = speeds.std()
        speed_cv = speed_std / (avg_speed + 0.001)  # Coefficient of variation
        
        # Trust based on speed consistency (lower CV = higher trust)
        consistency_score = max(0.0, 1.0 - min(1.0, speed_cv))
        
        # Trust based on speed range (moderate speeds preferred)
        if avg_speed < 30:
            speed_score = 0.6  # Too slow
        elif avg_speed < 60:
            speed_score = 0.9  # Optimal
        elif avg_speed < 90:
            speed_score = 0.7  # Fast but acceptable
        elif avg_speed < 120:
            speed_score = 0.4  # Very fast, less reliable
        else:
            speed_score = 0.2  # Too fast, unreliable
        
        # Combined trust: 60% consistency, 40% speed range
        trust = 0.6 * consistency_score + 0.4 * speed_score
        
        return max(0.0, min(1.0, trust))
    
    @staticmethod
    def compute_success_failure_from_speed(speeds: pd.Series, 
                                          speed_threshold: float = 90.0) -> tuple:
        """
        Estimate success/failure counts from speed patterns.
        Vehicles with more consistent, moderate speeds have higher success rates.
        
        Args:
            speeds: Series of speed values
            speed_threshold: Speed above which tasks are more likely to fail
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        if len(speeds) == 0:
            return (10, 2)  # Default
        
        avg_speed = speeds.mean()
        high_speed_ratio = (speeds > speed_threshold).sum() / len(speeds)
        
        # Base success rate
        if avg_speed < 60:
            base_success_rate = 0.85
        elif avg_speed < 90:
            base_success_rate = 0.75
        else:
            base_success_rate = 0.50
        
        # Adjust for high-speed ratio
        success_rate = base_success_rate * (1 - high_speed_ratio * 0.3)
        success_rate = max(0.3, min(0.95, success_rate))
        
        # Generate counts (normalize to reasonable range)
        total_samples = max(10, min(50, len(speeds) // 10))
        success_count = int(total_samples * success_rate)
        failure_count = total_samples - success_count
        
        return (success_count, failure_count)
    
    @staticmethod
    def process_mobility_dataset(csv_file: str,
                                vehicle_id_col: str = 'vehicle_id',
                                speed_col: Optional[str] = None,
                                distance_col: Optional[str] = 'distance',
                                duration_col: Optional[str] = 'duration',
                                timestamp_col: Optional[str] = 'timestamp') -> List[FogNode]:
        """
        Process a mobility dataset and create FogNode objects.
        
        Supports multiple formats:
        1. Simple format: vehicle_id, speed
        2. Trajectory format: vehicle_id, distance, duration (speed computed)
        3. Full format: vehicle_id, timestamp, distance, duration, etc.
        
        Args:
            csv_file: Path to CSV file
            vehicle_id_col: Column name for vehicle identifier
            speed_col: Column name for speed (if available)
            distance_col: Column name for distance (if computing speed)
            duration_col: Column name for duration (if computing speed)
            timestamp_col: Column name for timestamp (optional)
            
        Returns:
            List of FogNode objects
        """
        # Load dataset
        df = MobilityProcessor.load_porto_dataset(csv_file)
        
        # Compute speed if needed
        if speed_col and speed_col in df.columns:
            speeds = df[speed_col]
        elif distance_col in df.columns and duration_col in df.columns:
            speeds = MobilityProcessor.compute_speed_from_trajectory(df, distance_col, duration_col)
        else:
            raise ValueError("Need either 'speed' column or 'distance' and 'duration' columns")
        
        # Group by vehicle
        if vehicle_id_col not in df.columns:
            # If no vehicle_id, treat entire dataset as one vehicle
            vehicle_groups = {1: df}
        else:
            vehicle_groups = {vid: group for vid, group in df.groupby(vehicle_id_col)}
        
        nodes = []
        for vehicle_id, vehicle_df in vehicle_groups.items():
            vehicle_speeds = speeds.loc[vehicle_df.index] if vehicle_id_col in df.columns else speeds
            
            # Compute average speed for this vehicle
            avg_speed = vehicle_speeds.mean()
            
            # Compute trust from mobility pattern
            trust_value = MobilityProcessor.compute_trust_from_mobility_pattern(vehicle_speeds, str(vehicle_id))
            
            # Estimate success/failure from speed pattern
            success, failure = MobilityProcessor.compute_success_failure_from_speed(vehicle_speeds)
            
            # Create fog node
            node = FogNode(
                node_id=int(vehicle_id) if isinstance(vehicle_id, (int, float)) else len(nodes) + 1,
                speed=float(avg_speed),
                success=int(success),
                failure=int(failure)
            )
            
            # Override trust with computed value (more accurate)
            node.trust = trust_value
            node.initial_trust = trust_value
            node._update_scores()
            
            nodes.append(node)
        
        print(f"✓ Processed {len(nodes)} vehicles from mobility dataset")
        return nodes
    
    @staticmethod
    def create_sample_porto_format_dataset(output_file: str = "porto_mobility_sample.csv", 
                                          num_vehicles: int = 5,
                                          records_per_vehicle: int = 100):
        """
        Create a sample dataset in Porto format for testing.
        
        Args:
            output_file: Output CSV filename
            num_vehicles: Number of vehicles to simulate
            records_per_vehicle: Number of trajectory records per vehicle
        """
        records = []
        
        for vehicle_id in range(1, num_vehicles + 1):
            # Different speed profiles for different vehicles
            if vehicle_id == 1:
                base_speed = 45  # Moderate, consistent
                speed_variance = 5
            elif vehicle_id == 2:
                base_speed = 65  # Fast but consistent
                speed_variance = 8
            elif vehicle_id == 3:
                base_speed = 95  # Very fast, less consistent
                speed_variance = 15
            elif vehicle_id == 4:
                base_speed = 35  # Slow, very consistent
                speed_variance = 3
            else:
                base_speed = 75  # Moderate-fast
                speed_variance = 10
            
            for record_id in range(records_per_vehicle):
                # Simulate trajectory point
                speed = max(10, np.random.normal(base_speed, speed_variance))
                distance = speed * np.random.uniform(0.5, 2.0)  # Distance in km
                duration = distance / (speed + 0.001)  # Duration in hours (normalized)
                timestamp = 1000 + record_id * 60  # Simulated timestamps
                
                records.append({
                    'vehicle_id': vehicle_id,
                    'timestamp': timestamp,
                    'latitude': 41.15 + np.random.uniform(-0.1, 0.1),
                    'longitude': -8.61 + np.random.uniform(-0.1, 0.1),
                    'distance': round(distance, 3),
                    'duration': round(duration, 4),
                    'speed': round(speed, 2)
                })
        
        df = pd.DataFrame(records)
        df.to_csv(output_file, index=False)
        print(f"✓ Created sample Porto-format dataset: {output_file}")
        print(f"  Vehicles: {num_vehicles}, Records: {len(records)}")
        return output_file

