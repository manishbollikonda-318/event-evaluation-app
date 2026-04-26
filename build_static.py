import json
import os

def build():
    app_path = "app.py"
    index_tpl_path = "index.html"
    output_path = "index.html"

    if not os.path.exists(app_path):
        print(f"Error: {app_path} not found")
        return

    with open(app_path, "r") as f:
        app_code = f.read()

    with open(index_tpl_path, "r") as f:
        html = f.read()

    # Find the placeholder and replace it with the escaped app code
    # We use JSON stringify style to handle escaping
    placeholder = '# ... [WE WILL INJECT THE CONTENT OF APP.PY HERE] ...'
    
    # Simple replacement with backtick preservation
    escaped_code = app_code.replace("`", "\\`").replace("${", "\\${")
    
    final_html = html.replace(placeholder, escaped_code)

    with open(output_path, "w") as f:
        f.write(final_html)

    print("✅ BEAST MODE: index.html updated with latest app.py logic.")
    print("🚀 Ready for Netlify deployment.")

if __name__ == "__main__":
    build()
