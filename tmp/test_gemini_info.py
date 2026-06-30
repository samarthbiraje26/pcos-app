import subprocess

with open("tmp/gemini_output.log", "w", encoding="utf-8") as f:
    result = subprocess.run(
        ["python", "tmp/test_gemini.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    f.write(result.stdout)
print("Done writing results to tmp/gemini_output.log")
