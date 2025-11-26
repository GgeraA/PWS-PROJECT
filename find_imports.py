import os
import re

def find_all_imports():
    imports = set()
    
    for root, dirs, files in os.walk('.'):
        # Excluir venv y otros directorios no deseados
        if 'venv' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Encontrar imports
                        import_lines = re.findall(r'^(?:import|from)\s+(\S+)', content, re.MULTILINE)
                        
                        for imp in import_lines:
                            # Limpiar el import
                            clean_imp = imp.split('.')[0].split(' ')[0]
                            if clean_imp and not clean_imp.startswith('_'):
                                imports.add(clean_imp)
                                
                except Exception as e:
                    print(f"Error leyendo {filepath}: {e}")
    
    return sorted(imports)

if __name__ == '__main__':
    all_imports = find_all_imports()
    print("📦 Librerías importadas en tu proyecto:")
    for imp in all_imports:
        print(f"  - {imp}")