"""
Plotting module for visualizing comparison results.
"""

import matplotlib.pyplot as plt
from typing import Tuple


class Plotter:
    """Generate bar charts for performance comparison."""
    
    @staticmethod
    def plot_comparison(baseline_success: float, proposed_success: float,
                       baseline_delay: float, proposed_delay: float,
                       output_file: str = "comparison_results.png"):
        """
        Generate two bar charts comparing baseline and proposed schedulers.
        
        Args:
            baseline_success: Baseline success rate (%)
            proposed_success: Proposed success rate (%)
            baseline_delay: Baseline average delay (seconds)
            proposed_delay: Proposed average delay (seconds)
            output_file: Output filename for the plot
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Success Rate Comparison
        categories = ['Baseline', 'Proposed']
        success_rates = [baseline_success, proposed_success]
        colors = ['#3498db', '#2ecc71']
        
        bars1 = ax1.bar(categories, success_rates, color=colors, alpha=0.8, edgecolor='black')
        ax1.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
        ax1.set_title('Task Success Rate Comparison', fontsize=14, fontweight='bold')
        ax1.set_ylim(0, 100)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Average Delay Comparison
        delays = [baseline_delay, proposed_delay]
        bars2 = ax2.bar(categories, delays, color=colors, alpha=0.8, edgecolor='black')
        ax2.set_ylabel('Average Delay (seconds)', fontsize=12, fontweight='bold')
        ax2.set_title('Average Delay Comparison', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add value labels on bars
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}s',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✓ Comparison charts saved to: {output_file}")
        plt.show()
    
    @staticmethod
    def plot_metrics_only(baseline_success: float, proposed_success: float,
                         baseline_delay: float, proposed_delay: float):
        """
        Plot comparison charts (wrapper for plot_comparison).
        
        Args:
            baseline_success: Baseline success rate (%)
            proposed_success: Proposed success rate (%)
            baseline_delay: Baseline average delay (seconds)
            proposed_delay: Proposed average delay (seconds)
        """
        Plotter.plot_comparison(baseline_success, proposed_success,
                               baseline_delay, proposed_delay)

