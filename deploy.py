import os
import shutil
import zipfile
import subprocess

def main():
    print("Creating Lambda deployment package...")

    #Clean up
    if os.path.exists("lambda-package"):
        shutil.rmtree("lambda-package")
    if os.path.exists("lambda-deployment.zip"):
        os.remove("lambda-deployment.zip")
    

    os.makedirs("lambda-package")

    print("Installing dependencies for Lambda runtime...")

    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{os.getcwd()}:/var/task",
            "--platform",
            "linux/amd64",
            "--entrypoint",
            "",
            "public.ecr.aws/lambda/python:3.12",
            "/bin/sh",
            "-c",
            "pip install --target /var/task/lambda-package -r /var/task/requirements.txt --only-binary=:all: \
                --no-binary=google-search-results,pybars4,pymeta3,pypika,simplegeneric,testresources,wikipedia --upgrade",  
        ],
        check=True,
    )

    print("Copying application files...")
    for file in ["server.py", "lambda_handler.py","tools.py","resumeevaluator.py"]:
        if os.path.exists(file):
            shutil.copy2(file, "lambda-package/")
    
    print("Creating zip file...")
    with zipfile.ZipFile("lambda-deployment.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("lambda-package"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "lambda-package")
                zipf.write(file_path, arcname)
    
    size_mb = os.path.getsize("lambda-deployment.zip") / (1024 * 1024)
    print(f"✓ Created lambda-deployment.zip ({size_mb:.2f} MB)")



if __name__ == "__main__":
    main()