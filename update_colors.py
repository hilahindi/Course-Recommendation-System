import os
import re

dir_path = "client/src"

replacements = {
    r'text-white/(\d+)': lambda m: f"text-gray-{900 - int(m.group(1))*3}",
    r'text-white': 'text-gray-800',
    r'bg-black/(\d+)': lambda m: f"bg-white/{int(m.group(1))*2}",
    r'bg-white/(\d+)': lambda m: f"bg-gray-100", # simplify
    r'border-white/(\d+)': lambda m: f"border-gray-200",
    
    r'from-blue-400': 'from-emerald-500',
    r'to-purple-500': 'to-teal-500',
    r'to-purple-400': 'to-teal-500',
    r'via-blue-400': 'via-emerald-400',
    
    r'bg-blue-600': 'bg-emerald-600',
    r'hover:bg-blue-500': 'hover:bg-emerald-500',
    r'text-blue-400': 'text-emerald-600',
    r'text-blue-300': 'text-emerald-700',
    r'border-blue-400': 'border-emerald-400',
    r'shadow-blue-500': 'shadow-emerald-500',
    
    r'bg-purple-600': 'bg-teal-600',
    r'hover:bg-purple-500': 'hover:bg-teal-500',
    r'text-purple-400': 'text-teal-600',
    r'text-purple-300': 'text-teal-700',
    r'border-purple-400': 'border-teal-400',
    r'shadow-purple-500': 'shadow-teal-500',

    r'bg-blue-900/30': 'bg-emerald-100/50',
    r'bg-blue-900/20': 'bg-emerald-50/50',
    r'bg-blue-900/10': 'bg-emerald-50/30',
    
    # Custom text-gray replacements for the heuristic
    r'text-gray-720': 'text-gray-500',
    r'text-gray-690': 'text-gray-600',
    r'text-gray-660': 'text-gray-600',
    r'text-gray-630': 'text-gray-700',
    r'text-gray-600': 'text-gray-500',
    r'text-gray-750': 'text-gray-400',
    r'text-gray-780': 'text-gray-400',
    r'text-gray-810': 'text-gray-400',
    r'text-gray-840': 'text-gray-400',
    r'text-gray-870': 'text-gray-300',
}

for root, _, files in os.walk(dir_path):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                if callable(new):
                    new_content = re.sub(old, new, new_content)
                else:
                    new_content = re.sub(old, new, new_content)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

print("Colors updated!")
