import os
import re

backend_path = r"C:\Users\HP\Documents\Proyecto\SI2_Examen_1\backend\app\routers"
routes = []

for root, dirs, files in os.walk(backend_path):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                prefix = ""
                # Find APIRouter prefix
                content = f.read()
                prefix_match = re.search(r'APIRouter\([^)]*prefix=["\']([^"\']+)["\']', content)
                if prefix_match:
                    prefix = prefix_match.group(1)
                
                # Find all decorators
                decorators = re.findall(r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content)
                for method, route in decorators:
                    full_route = (prefix + route).replace('//', '/')
                    routes.append((file, method.upper(), full_route))

print("Found endpoints:")
for f, m, r in sorted(routes):
    print(f"- {m} {r} (in {f})")
