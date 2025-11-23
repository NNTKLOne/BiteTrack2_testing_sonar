import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os

def load_metrics(json_file='metrics.json'):
    """Load metrics from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def plot_metrics_comparison(results, output_file='metrics_comparison.png'):
    """Create a comparison chart of all metrics for all classes"""
    
    # Collect all class data
    all_classes = []
    all_metrics = {
        'WMC': [],
        'CBO': [],
        'RFC': [],
        'DIT': [],
        'NOC': [],
        'Cohesion': [],
        'Coupling': []
    }
    
    for file_path, file_data in results.items():
        for class_name, metrics in file_data['classes'].items():
            all_classes.append(f"{Path(file_path).stem}::{class_name}")
            for metric_name in all_metrics.keys():
                all_metrics[metric_name].append(metrics[metric_name])
    
    if not all_classes:
        print("Nerasta klasių vizualizacijai!")
        return
    
    # Create subplots
    fig, axes = plt.subplots(3, 3, figsize=(16, 12))
    fig.suptitle('Objektinio Programavimo Metrikos - Palyginimas', fontsize=16, fontweight='bold')
    
    metrics_info = [
        ('WMC', 'Weighted Methods per Class', 20),
        ('CBO', 'Coupling Between Objects', 5),
        ('RFC', 'Response For a Class', 25),
        ('DIT', 'Depth of Inheritance Tree', 3),
        ('NOC', 'Number of Children', 5),
        ('Cohesion', 'Sankabumo Metrika', 0.7),
        ('Coupling', 'Priklausomybės', 5)
    ]
    
    for idx, (metric, title, threshold) in enumerate(metrics_info):
        ax = axes[idx // 3, idx % 3]
        values = all_metrics[metric]
        
        # Create bar chart
        colors = ['green' if v <= threshold else 'orange' if v <= threshold * 1.5 else 'red' 
                  for v in values]
        
        if metric == 'Cohesion':  # Higher is better for cohesion
            colors = ['green' if v >= threshold else 'orange' if v >= threshold * 0.7 else 'red' 
                      for v in values]
        
        bars = ax.bar(range(len(all_classes)), values, color=colors, alpha=0.7, edgecolor='black')
        
        # Add threshold line
        ax.axhline(y=threshold, color='blue', linestyle='--', linewidth=2, label=f'Norma: {threshold}')
        
        ax.set_title(f'{metric}: {title}', fontweight='bold')
        ax.set_xlabel('Klasės')
        ax.set_ylabel('Vertė')
        ax.set_xticks(range(len(all_classes)))
        ax.set_xticklabels(all_classes, rotation=45, ha='right', fontsize=8)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontsize=8)
    
    # Remove extra subplot
    fig.delaxes(axes[2, 2])
    
    # Add legend in the empty space
    legend_ax = axes[2, 2]
    legend_ax.axis('off')
    legend_text = """
    Spalvų reikšmės:
    🟢 Žalia - Gera vertė
    🟠 Oranžinė - Vidutinė vertė
    🔴 Raudona - Bloga vertė (reikia refaktoringo)
    
    Normos:
    WMC < 20 | CBO < 5 | RFC < 25
    DIT < 3 | NOC < 5 | Coupling < 5
    Cohesion > 0.7
    """
    legend_ax.text(0.1, 0.5, legend_text, fontsize=10, verticalalignment='center',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Grafikas išsaugotas: {output_file}")
    plt.close()

def plot_cohesion_coupling_scatter(results, output_file='cohesion_coupling.png'):
    """Create scatter plot of Cohesion vs Coupling"""
    
    class_names = []
    cohesion_values = []
    coupling_values = []
    
    for file_path, file_data in results.items():
        for class_name, metrics in file_data['classes'].items():
            class_names.append(f"{Path(file_path).stem}::{class_name}")
            cohesion_values.append(metrics['Cohesion'])
            coupling_values.append(metrics['Coupling'])
    
    if not class_names:
        print("Nerasta klasių vizualizacijai!")
        return
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create scatter plot
    scatter = ax.scatter(coupling_values, cohesion_values, s=200, alpha=0.6, 
                        c=range(len(class_names)), cmap='viridis', edgecolors='black', linewidth=2)
    
    # Add labels for each point
    for i, name in enumerate(class_names):
        ax.annotate(name, (coupling_values[i], cohesion_values[i]), 
                   fontsize=9, ha='right', va='bottom')
    
    # Add quadrant lines
    ax.axhline(y=0.7, color='red', linestyle='--', linewidth=2, label='Cohesion norma (0.7)')
    ax.axvline(x=5, color='blue', linestyle='--', linewidth=2, label='Coupling norma (5)')
    
    # Add quadrant labels
    ax.text(2.5, 0.85, 'IDEALUS\n(Aukštas cohesion,\nŽemas coupling)', 
           ha='center', fontsize=11, fontweight='bold', 
           bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    ax.text(10, 0.85, 'SUSIETAS\n(Aukštas cohesion,\nAukštas coupling)', 
           ha='center', fontsize=11, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    ax.text(2.5, 0.2, 'LAISVAS\n(Žemas cohesion,\nŽemas coupling)', 
           ha='center', fontsize=11, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    ax.text(10, 0.2, 'BLOGAI\n(Žemas cohesion,\nAukštas coupling)', 
           ha='center', fontsize=11, fontweight='bold',
           bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
    
    ax.set_xlabel('Coupling (Priklausomybės)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cohesion (Sankabumas)', fontsize=12, fontweight='bold')
    ax.set_title('Cohesion vs Coupling Analizė', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Cohesion/Coupling grafikas išsaugotas: {output_file}")
    plt.close()

def plot_radar_chart(results, output_file='metrics_radar.png'):
    """Create radar chart for each class"""
    
    for file_path, file_data in results.items():
        if not file_data['classes']:
            continue
            
        for class_name, metrics in file_data['classes'].items():
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
            
            # Normalize metrics to 0-1 scale
            categories = ['WMC\n(norm: 20)', 'CBO\n(norm: 5)', 'RFC\n(norm: 25)', 
                         'DIT\n(norm: 3)', 'NOC\n(norm: 5)', 'Cohesion\n(norm: 0.7)', 
                         'Coupling\n(norm: 5)']
            
            # Normalize values (lower is better except for Cohesion)
            normalized_values = [
                min(metrics['WMC'] / 40, 1),  # WMC normalized by 40
                min(metrics['CBO'] / 10, 1),  # CBO normalized by 10
                min(metrics['RFC'] / 50, 1),  # RFC normalized by 50
                min(metrics['DIT'] / 6, 1),   # DIT normalized by 6
                min(metrics['NOC'] / 10, 1),  # NOC normalized by 10
                metrics['Cohesion'],          # Already 0-1
                min(metrics['Coupling'] / 10, 1)  # Coupling normalized by 10
            ]
            
            # For cohesion, invert since higher is better
            # normalized_values[5] = 1 - normalized_values[5]  # Uncomment if you want consistent "lower is better"
            
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            normalized_values += normalized_values[:1]  # Complete the circle
            angles += angles[:1]
            
            ax.plot(angles, normalized_values, 'o-', linewidth=2, color='blue')
            ax.fill(angles, normalized_values, alpha=0.25, color='blue')
            
            # Add threshold circle
            threshold = [0.5] * (len(categories) + 1)
            ax.plot(angles, threshold, '--', linewidth=2, color='red', alpha=0.5, label='Vidutinė norma')
            
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontsize=10)
            ax.set_ylim(0, 1)
            ax.set_title(f'Metrikos Radaras: {class_name}', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.legend(loc='upper right')
            ax.grid(True)
            
            filename = f"radar_{Path(file_path).stem}_{class_name}.png"
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"✓ Radaro grafikas išsaugotas: {filename}")
            plt.close()

def generate_summary_stats(results):
    """Generate summary statistics"""
    print("\n" + "="*80)
    print("SANTRAUKA")
    print("="*80)
    
    total_classes = 0
    total_files = len(results)
    
    avg_metrics = {
        'WMC': [],
        'CBO': [],
        'RFC': [],
        'DIT': [],
        'NOC': [],
        'Cohesion': [],
        'Coupling': []
    }
    
    for file_path, file_data in results.items():
        total_classes += len(file_data['classes'])
        for class_name, metrics in file_data['classes'].items():
            for metric_name in avg_metrics.keys():
                avg_metrics[metric_name].append(metrics[metric_name])
    
    print(f"\nIšanalizuota failų: {total_files}")
    print(f"Rasta klasių: {total_classes}")
    
    if total_classes > 0:
        print("\nVIDURKIAI:")
        for metric_name, values in avg_metrics.items():
            avg = np.mean(values)
            print(f"  {metric_name}: {avg:.2f}")

if __name__ == "__main__":
    import sys
    
    json_file = 'metrics.json'
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"Klaida: Nerastas failas {json_file}")
        print("Pirmiausia paleiskite: python metrics_analyzer.py <failai>")
        sys.exit(1)
    
    print("Generuojamos vizualizacijos...\n")
    
    results = load_metrics(json_file)
    
    plot_metrics_comparison(results, 'metrics_comparison.png')
    plot_cohesion_coupling_scatter(results, 'cohesion_coupling.png')
    plot_radar_chart(results, 'metrics_radar.png')
    generate_summary_stats(results)
    
    print("\n✓ Visos vizualizacijos sugeneruotos!")
    print("\nSugeneruoti failai:")
    print("  - metrics_comparison.png - Visų metrikų palyginimas")
    print("  - cohesion_coupling.png - Cohesion vs Coupling analizė")
    print("  - radar_*.png - Radaro grafikai kiekvienai klasei")