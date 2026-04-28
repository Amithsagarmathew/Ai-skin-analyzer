import os
import re

# Define the base path for templates
templates_path = r'c:\projects\LCC\Skin Care\project\app\templates'

# List of files to process (main user-facing pages)
files_to_process = [
    'index.html',
    'analysis.html',
    'routines.html',
    'progress.html',
    'scan_history.html',
    'scan_detail.html',
    'profile.html',
    'single-product.html',
    'cart.html',
    'order_success.html',
    'contact.html',
]

# Pattern to match the header section
pattern = re.compile(
    r'<!--=== Header ===-->.*?<!--=== End Header ===-->\s*',
    re.DOTALL
)

def remove_header_from_file(filepath):
    """Remove header section from a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if header exists
        if 'header-area two' in content:
            # Remove the header section
            new_content = pattern.sub('', content)
            
            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✓ Removed header from: {os.path.basename(filepath)}")
            return True
        else:
            print(f"- No header found in: {os.path.basename(filepath)}")
            return False
    except FileNotFoundError:
        print(f"✗ File not found: {os.path.basename(filepath)}")
        return False
    except Exception as e:
        print(f"✗ Error processing {os.path.basename(filepath)}: {str(e)}")
        return False

# Process all files
print("Removing header sections from templates...\n")
processed = 0
removed = 0

for filename in files_to_process:
    filepath = os.path.join(templates_path, filename)
    if remove_header_from_file(filepath):
        removed += 1
    processed += 1

print(f"\n{'='*50}")
print(f"Processed: {processed} files")
print(f"Headers removed: {removed}")
print(f"{'='*50}")
