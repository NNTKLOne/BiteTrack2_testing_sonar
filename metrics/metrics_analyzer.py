import ast
import os
from pathlib import Path
from collections import defaultdict
import json

class MetricsAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path):
        self.file_path = file_path
        self.classes = {}
        self.current_class = None
        self.imports = set()
        self.functions = []
        
    def visit_ClassDef(self, node):
        class_name = node.name
        self.current_class = class_name
        
        self.classes[class_name] = {
            'methods': [],
            'method_names': set(),
            'base_classes': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
            'attributes': set(),
            'method_calls': defaultdict(set),
            'external_calls': set(),
            'lines': len(node.body)
        }
        
        self.generic_visit(node)
        self.current_class = None
        
    def visit_FunctionDef(self, node):
        if self.current_class:
            self.classes[self.current_class]['methods'].append(node.name)
            self.classes[self.current_class]['method_names'].add(node.name)
            
            # Calculate cyclomatic complexity for the method
            complexity = self._calculate_complexity(node)
            self.classes[self.current_class][f'{node.name}_complexity'] = complexity
        else:
            self.functions.append(node.name)
        
        self.generic_visit(node)
    
    def visit_Call(self, node):
        if self.current_class:
            # External constructor call (e.g., ScreenManager())
            if isinstance(node.func, ast.Name):
                self.classes[self.current_class]['external_calls'].add(node.func.id)

            # Existing logic for attribute calls (e.g., sm.add_widget)
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == 'self':
                        self.classes[self.current_class]['method_calls']['internal'].add(node.func.attr)
                    else:
                        self.classes[self.current_class]['external_calls'].add(f"{node.func.value.id}.{node.func.attr}")
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        if self.current_class and isinstance(node.value, ast.Name) and node.value.id == 'self':
            self.classes[self.current_class]['attributes'].add(node.attr)
        self.generic_visit(node)
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)
    
    def _calculate_complexity(self, node):
        """Calculate cyclomatic complexity (simplified)"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

def calculate_wmc(class_info):
    """Weighted Methods per Class - sum of complexities of all methods"""
    wmc = 0
    for method in class_info['methods']:
        complexity_key = f'{method}_complexity'
        wmc += class_info.get(complexity_key, 1)
    return wmc

def calculate_dit(class_name, all_classes, inheritance_tree, depth=0):
    """Depth of Inheritance Tree"""
    if depth > 100:  # Prevent infinite recursion
        return 0
    
    if class_name not in all_classes:
        return depth
    
    base_classes = all_classes[class_name].get('base_classes', [])
    if not base_classes or base_classes == ['object']:
        return depth
    
    max_depth = depth
    for base in base_classes:
        if base in all_classes:
            max_depth = max(max_depth, calculate_dit(base, all_classes, inheritance_tree, depth + 1))
    
    return max_depth

def calculate_noc(class_name, all_classes):
    """Number of Children"""
    children = 0
    for cls, info in all_classes.items():
        if class_name in info.get('base_classes', []):
            children += 1
    return children

def calculate_lcom(class_info):
    """Lack of Cohesion of Methods - simplified version"""
    methods = class_info['methods']
    attributes = class_info['attributes']
    
    if len(methods) <= 1 or len(attributes) == 0:
        return 0
    
    # Count methods that don't share attributes
    non_sharing_pairs = 0
    sharing_pairs = 0
    
    # This is a simplified LCOM calculation
    # In reality, you'd need to track which methods use which attributes
    method_attr_usage = defaultdict(set)
    
    # For simplification, we'll estimate based on method calls
    for method in methods:
        if method in class_info['method_calls']['internal']:
            sharing_pairs += 1
    
    total_pairs = (len(methods) * (len(methods) - 1)) / 2
    if total_pairs == 0:
        return 0
    
    lcom = max(0, 1 - (sharing_pairs / total_pairs))
    return round(lcom, 2)

def analyze_files(files):
    """Analyze all files and calculate metrics"""
    all_classes = {}
    file_metrics = {}
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
            
            analyzer = MetricsAnalyzer(file_path)
            analyzer.visit(tree)
            
            file_metrics[file_path] = {
                'classes': analyzer.classes,
                'imports': analyzer.imports,
                'functions': analyzer.functions
            }
            
            # Add to all_classes with file context
            for class_name, class_info in analyzer.classes.items():
                all_classes[f"{file_path}::{class_name}"] = class_info
                all_classes[class_name] = class_info  # Also store without file prefix
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    # Calculate metrics for each class
    results = {}
    
    for file_path, metrics in file_metrics.items():
        file_results = {}
        
        for class_name, class_info in metrics['classes'].items():
            # WMC - Weighted Methods per Class
            wmc = calculate_wmc(class_info)
            
            # CBO - Coupling Between Objects
            cbo = len(set(call.split('.')[0] for call in class_info['external_calls']))
            
            # RFC - Response For a Class
            internal_calls = class_info['method_calls']['internal']
            external_calls = class_info['external_calls']
            all_distinct_calls = internal_calls.union(external_calls)
            rfc = len(class_info['methods']) + len(all_distinct_calls)
            # DIT - Depth of Inheritance Tree
            dit = calculate_dit(class_name, all_classes, {})
            
            # NOC - Number of Children
            noc = calculate_noc(class_name, all_classes)
            
            # LCOM - Lack of Cohesion of Methods (Cohesion metric)
            lcom = calculate_lcom(class_info)
            cohesion = 1 - lcom  # Convert to cohesion (higher is better)
            
            # Coupling (based on external dependencies)
            coupling = cbo
            
            file_results[class_name] = {
                'WMC': wmc,
                'CBO': cbo,
                'RFC': rfc,
                'DIT': dit,
                'NOC': noc,
                'Cohesion': round(cohesion, 2),
                'Coupling': coupling,
                'LCOM': lcom,
                'num_methods': len(class_info['methods']),
                'num_attributes': len(class_info['attributes'])
            }
        
        # File-level coupling
        file_coupling = len(metrics['imports'])
        
        results[file_path] = {
            'classes': file_results,
            'file_coupling': file_coupling,
            'num_functions': len(metrics['functions'])
        }
    
    return results

def generate_report(results, output_file='metrics_report.txt'):
    """Generate a text report"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("OBJEKTINIO PROGRAMAVIMO METRIKOS - ATASKAITA\n")
        f.write("=" * 80 + "\n\n")
        
        for file_path, file_data in results.items():
            f.write(f"\n{'=' * 80}\n")
            f.write(f"Failas: {os.path.basename(file_path)}\n")
            f.write(f"{'=' * 80}\n")
            f.write(f"Failo Coupling (importų skaičius): {file_data['file_coupling']}\n")
            f.write(f"Funkcijų skaičius: {file_data['num_functions']}\n\n")
            
            if not file_data['classes']:
                f.write("  Nerasta klasių šiame faile.\n\n")
                continue
            
            for class_name, metrics in file_data['classes'].items():
                f.write(f"\nKlasė: {class_name}\n")
                f.write("-" * 80 + "\n")
                
                f.write(f"  WMC (Weighted Methods per Class): {metrics['WMC']}\n")
                f.write(f"    → Metodų sudėtingumo suma: {metrics['WMC']}\n")
                f.write(f"    → Metodų skaičius: {metrics['num_methods']}\n")
                if metrics['WMC'] > 50:
                    f.write(f"    ⚠️  Aukšta vertė! Klasė gali būti per sudėtinga.\n")
                elif metrics['WMC'] > 20:
                    f.write(f"    ⚠️  Vidutinė vertė. Galima apsvarstyti refaktoringą.\n")
                else:
                    f.write(f"    ✓ Gera vertė.\n")
                
                f.write(f"\n  CBO (Coupling Between Objects): {metrics['CBO']}\n")
                f.write(f"    → Priklausomybių nuo kitų objektų skaičius: {metrics['CBO']}\n")
                if metrics['CBO'] > 10:
                    f.write(f"    ⚠️  Aukštas coupling! Klasė labai priklauso nuo kitų.\n")
                elif metrics['CBO'] > 5:
                    f.write(f"    ⚠️  Vidutinis coupling.\n")
                else:
                    f.write(f"    ✓ Žemas coupling - gera.\n")
                
                f.write(f"\n  RFC (Response For a Class): {metrics['RFC']}\n")
                f.write(f"    → Metodų + išorinių kvietimų suma: {metrics['RFC']}\n")
                if metrics['RFC'] > 50:
                    f.write(f"    ⚠️  Aukšta vertė! Klasė gali būti per sudėtinga testuoti.\n")
                elif metrics['RFC'] > 25:
                    f.write(f"    ⚠️  Vidutinė vertė.\n")
                else:
                    f.write(f"    ✓ Gera vertė.\n")
                
                f.write(f"\n  DIT (Depth of Inheritance Tree): {metrics['DIT']}\n")
                f.write(f"    → Paveldėjimo medžio gylis: {metrics['DIT']}\n")
                if metrics['DIT'] > 5:
                    f.write(f"    ⚠️  Per gilus paveldėjimas! Gali būti sunku suprasti.\n")
                elif metrics['DIT'] > 3:
                    f.write(f"    ⚠️  Vidutinis gylis.\n")
                else:
                    f.write(f"    ✓ Normalus gylis.\n")
                
                f.write(f"\n  NOC (Number of Children): {metrics['NOC']}\n")
                f.write(f"    → Vaikinių klasių skaičius: {metrics['NOC']}\n")
                if metrics['NOC'] > 10:
                    f.write(f"    ⚠️  Daug vaikų! Gali reikėti persvarstyti dizainą.\n")
                elif metrics['NOC'] > 5:
                    f.write(f"    ⚠️  Vidutiniškai daug vaikų.\n")
                else:
                    f.write(f"    ✓ Normalus skaičius.\n")
                
                f.write(f"\n  COHESION (Sankabumo metrika): {metrics['Cohesion']}\n")
                f.write(f"    → Kiek metodai dirba su bendrais duomenimis: {metrics['Cohesion']}\n")
                if metrics['Cohesion'] > 0.7:
                    f.write(f"    ✓ Aukštas cohesion! Klasė gerai suorganizuota.\n")
                elif metrics['Cohesion'] > 0.4:
                    f.write(f"    ⚠️  Vidutinis cohesion. Galima pagerinti.\n")
                else:
                    f.write(f"    ⚠️  Žemas cohesion! Klasė gali turėti per daug atsakomybių.\n")
                
                f.write(f"\n  COUPLING (Priklausomybės): {metrics['Coupling']}\n")
                f.write(f"    → Išorinių priklausomybių skaičius: {metrics['Coupling']}\n")
                if metrics['Coupling'] > 10:
                    f.write(f"    ⚠️  Aukštas coupling! Per daug priklausomybių.\n")
                elif metrics['Coupling'] > 5:
                    f.write(f"    ⚠️  Vidutinis coupling.\n")
                else:
                    f.write(f"    ✓ Žemas coupling - gera!\n")
                
                f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("BENDROS REKOMENDACIJOS\n")
        f.write("=" * 80 + "\n\n")
        f.write("WMC: Mažesnė vertė geriau (<20). Didelė vertė rodo sudėtingą klasę.\n")
        f.write("CBO: Mažesnis coupling geriau (<5). Didelis CBO rodo daug priklausomybių.\n")
        f.write("RFC: Mažesnė vertė geriau (<25). Didelė vertė apsunkina testavimą.\n")
        f.write("DIT: Optimalus 2-4. Per gilus paveldėjimas apsunkina supratimą.\n")
        f.write("NOC: Mažiau vaikų geriau (<5). Daug vaikų gali reikėti redesign.\n")
        f.write("Cohesion: Aukštesnis geriau (>0.7). Rodo, kad klasė turi aiškią atsakomybę.\n")
        f.write("Coupling: Žemesnis geriau (<5). Mažiau priklausomybių - lengviau palaikyti.\n\n")
    
    print(f"✓ Ataskaita išsaugota: {output_file}")

def generate_json_report(results, output_file='metrics.json'):
    """Generate JSON report for visualization"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✓ JSON duomenys išsaugoti: {output_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Naudojimas: python metrics_analyzer.py <file1.py> <file2.py> ...")
        sys.exit(1)
    
    files = sys.argv[1:]
    print(f"Analizuojama {len(files)} failų...\n")
    
    results = analyze_files(files)
    generate_report(results, 'metrics_report.txt')
    generate_json_report(results, 'metrics.json')
    
    print("\n✓ Analizė baigta!")
    print("  - Žiūrėkite metrics_report.txt detaliai ataskaitai")
    print("  - metrics.json naudokite vizualizacijai")