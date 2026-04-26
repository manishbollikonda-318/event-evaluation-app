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

    # We need a fallback or a way to restore index.html if it's empty
    # For now, if index.html is empty, we will write a fresh template
    
    template = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Event Evaluation — Beast Mode</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.39.0/build/stlite.css" />
    <style>
        body { background: #020617; }
        #stlite-loader {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: radial-gradient(circle at top left, #0f172a 0%, #020617 100%);
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            z-index: 10000; color: white; font-family: 'Inter', sans-serif;
        }
        .spinner {
            width: 50px; height: 50px; border: 3px solid rgba(255,255,255,0.1);
            border-top: 3px solid #3b82f6; border-radius: 50%;
            animation: spin 1s linear infinite; margin-bottom: 20px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .beast-logo { font-size: 2rem; font-weight: 800; letter-spacing: -0.05em; margin-bottom: 10px; background: linear-gradient(to right, #60a5fa, #2563eb); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
  </head>
  <body>
    <div id="stlite-loader">
        <div class="beast-logo">BEAST MODE</div>
        <div class="spinner"></div>
        <p>Igniting Core Engine...</p>
    </div>
    <div id="root"></div>
    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.39.0/build/stlite.js"></script>
    <script>
      const observer = new MutationObserver((mutations) => {
        if (document.querySelector(".stApp")) {
          document.getElementById("stlite-loader").style.display = "none";
          observer.disconnect();
        }
      });
      observer.observe(document.body, { childList: true, subtree: true });

      stlite.mount({
        requirements: ["pandas", "plotly"],
        entrypoint: "app.py",
        files: {
          "app.py": `# ... [WE WILL INJECT THE CONTENT OF APP.PY HERE] ...`
        }
      });
    </script>
  </body>
</html>"""

    # Simple replacement with backtick preservation
    escaped_code = app_code.replace("`", "\\`").replace("${", "\\${")
    
    placeholder = '# ... [WE WILL INJECT THE CONTENT OF APP.PY HERE] ...'
    final_html = template.replace(placeholder, escaped_code)

    with open(output_path, "w") as f:
        f.write(final_html)

    print("✅ BEAST MODE: index.html restored and updated with latest app.py logic.")
    print("🚀 Ready for Netlify deployment.")

if __name__ == "__main__":
    build()
