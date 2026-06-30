import subprocess

with open("tmp/list_output.log", "w", encoding="utf-8") as f:
    result = subprocess.run(
        ["python", "tmp/list_models.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    f.write(result.stdout)
print("Done writing model list to tmp/list_output.log")
